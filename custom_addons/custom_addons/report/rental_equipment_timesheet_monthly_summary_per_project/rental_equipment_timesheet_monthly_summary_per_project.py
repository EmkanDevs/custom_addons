# Copyright (c) 2026, Administrator and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from collections import defaultdict


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data    = get_data(filters)
	return columns, data


# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------
def get_columns():
	return [
		{
			"label":     _("Project"),
			"fieldname": "project",
			"fieldtype": "Link",
			"options":   "Project",
			"width":     160,
		},
		{
			"label":     _("Project Name"),
			"fieldname": "project_name",
			"fieldtype": "Data",
			"width":     220,
		},
		{
			"label":     _("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options":   "Supplier",
			"width":     160,
		},
		{
			"label":     _("Supplier Name"),
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"width":     200,
		},
		{
			"label":     _("Month"),
			"fieldname": "month",
			"fieldtype": "Data",
			"width":     110,
		},
		{
			"label":     _("Total Hours"),
			"fieldname": "total_hours",
			"fieldtype": "Float",
			"precision": 2,
			"width":     130,
		},
		{
			"label":     _("Total Amount"),
			"fieldname": "total_amount",
			"fieldtype": "Currency",
			"width":     150,
		},
	]


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def get_data(filters):
	conditions, values = get_conditions(filters)

	# ------------------------------------------------------------------
	# Step 1 – Query at equipment level so we have item_code per row.
	# Group by project + supplier + month + item_code.
	# This ensures we get the correct hours per equipment type.
	# ------------------------------------------------------------------
	query = """
		SELECT
			IFNULL(ret.project_id, '(No Project)')                AS project,
			IFNULL(proj.project_name, '')                         AS project_name,
			IFNULL(ret.supplier_name, '')                         AS supplier,
			IFNULL(sup.supplier_name, '')                         AS supplier_name,
			DATE_FORMAT(MIN(ret.date), '%%b-%%Y')                 AS month,
			YEAR(ret.date)                                        AS year_num,
			MONTH(ret.date)                                       AS month_num,
			IFNULL(eam.item, '')                                  AS item_code,
			SUM(IFNULL(ret.hours, 0))                             AS total_hours
		FROM
			`tabRental Equipment Timesheet` ret
		LEFT JOIN `tabProject`                    proj ON proj.name = ret.project_id
		LEFT JOIN `tabSupplier`                   sup  ON sup.name  = ret.supplier_name
		LEFT JOIN `tabEquipment Asset Management` eam  ON eam.name  = ret.door_no_or_plate_no
		WHERE
			1=1
			{conditions}
		GROUP BY
			ret.project_id,
			ret.supplier_name,
			YEAR(ret.date),
			MONTH(ret.date),
			eam.item
		ORDER BY
			ret.project_id     ASC,
			YEAR(ret.date)     ASC,
			MONTH(ret.date)    ASC,
			ret.supplier_name  ASC
	""".format(conditions=conditions)

	equipment_rows = frappe.db.sql(query, values, as_dict=True)

	if not equipment_rows:
		return []

	# ------------------------------------------------------------------
	# Step 2 – For each equipment row get the rate from Blanket Order,
	# calculate amount, then aggregate by (project, supplier, month).
	#
	# For each item_code:
	#   - Get all Blanket Order rates for that item
	#   - Calculate average rate across all Blanket Orders
	#   - total_amount = avg_rate × total_hours (per equipment type)
	#
	# Then aggregate by (project, supplier, month):
	#   - Sum all hours from different equipment types
	#   - Sum all amounts from different equipment types
	# ------------------------------------------------------------------
	_rate_cache = {}  # item_code → avg_rate (avoid repeated DB hits)

	# Dictionary to aggregate by (project, supplier, month)
	monthly = {}

	for row in equipment_rows:
		item_code = row.item_code or ""

		# Get or calculate average rate for this item_code
		if item_code not in _rate_cache:
			_rate_cache[item_code] = get_average_rate_for_item(item_code)

		avg_rate     = _rate_cache[item_code]
		row_amount   = flt(avg_rate) * flt(row.total_hours)

		# Key for aggregating by project, supplier, and month
		key = (row.project, row.supplier, row.year_num, row.month_num)

		if key not in monthly:
			monthly[key] = {
				"project":      row.project,
				"project_name": row.project_name,
				"supplier":     row.supplier,
				"supplier_name":row.supplier_name,
				"month":        row.month,
				"year_num":     row.year_num,
				"month_num":    row.month_num,
				"total_hours":  0.0,
				"total_amount": 0.0,
			}

		monthly[key]["total_hours"]  += flt(row.total_hours)
		monthly[key]["total_amount"] += row_amount

	# ------------------------------------------------------------------
	# Step 3 – Build the final list, rounding values for display.
	# ------------------------------------------------------------------
	data = []
	for record in monthly.values():
		data.append({
			"project":      record["project"],
			"project_name": record["project_name"],
			"supplier":     record["supplier"],
			"supplier_name":record["supplier_name"],
			"month":        record["month"],
			"total_hours":  flt(record["total_hours"], 2),
			"total_amount": flt(record["total_amount"], 2),
		})

	return data


# ---------------------------------------------------------------------------
# Blanket Order rate lookup - returns average rate for an item
# ---------------------------------------------------------------------------
def get_average_rate_for_item(item_code):
	"""
	Fetch all rates from submitted Blanket Orders for the given item_code.
	Returns the average rate across all Blanket Orders.
	
	If the same equipment item appears multiple times (multiple Blanket Orders),
	this calculates the average rate across all of them.
	
	Returns:
		float: Average rate, or 0.0 if no Blanket Orders found
	"""
	if not item_code:
		return 0.0

	try:
		rows = frappe.db.sql(
			"""
			SELECT boi.rate
			FROM   `tabBlanket Order Item` boi
			JOIN   `tabBlanket Order`      bo  ON bo.name = boi.parent
			WHERE  bo.docstatus  = 1
			AND    boi.item_code = %(item_code)s
			""",
			{"item_code": item_code},
			as_list=True,
		)

		# Extract all rates from the result
		rates = [r[0] for r in rows if r[0]]

		if not rates:
			return 0.0

		# Calculate and return average rate
		avg_rate = sum(rates) / len(rates)
		return avg_rate

	except Exception as e:
		frappe.log_error(f"get_average_rate_for_item error: {e}", "Rental Equipment Report")
		return 0.0


# ---------------------------------------------------------------------------
# Filters → SQL conditions  (all named placeholders)
# ---------------------------------------------------------------------------
def get_conditions(filters):
	conditions = []
	values     = {}

	if filters.get("project"):
		conditions.append("AND ret.project_id = %(project)s")
		values["project"] = filters["project"]

	if filters.get("supplier"):
		conditions.append("AND ret.supplier_name = %(supplier)s")
		values["supplier"] = filters["supplier"]

	if filters.get("month"):
		month_num = [
			"January", "February", "March", "April", "May", "June",
			"July", "August", "September", "October", "November", "December",
		].index(filters["month"]) + 1
		conditions.append("AND MONTH(ret.date) = %(month_num)s")
		values["month_num"] = month_num

	if filters.get("year"):
		conditions.append("AND YEAR(ret.date) = %(year)s")
		values["year"] = filters["year"]

	if filters.get("state"):
		# Map state to docstatus
		state_map = {
			"Draft": 0,
			"Submitted": 1,
			"Cancelled": 2
		}
		if filters["state"] in state_map:
			conditions.append("AND ret.docstatus = %(docstatus)s")
			values["docstatus"] = state_map[filters["state"]]

	return " ".join(conditions), values