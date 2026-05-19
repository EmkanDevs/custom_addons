import frappe
import json
from frappe.utils import flt


@frappe.whitelist()
def get_data(filters=None):

	if isinstance(filters, str):
		filters = json.loads(filters)

	filters = frappe._dict(filters)

	return {
		"employee_timesheet": get_employee_timesheet(filters),
		"equipment_timesheet": get_equipment_timesheet(filters),
		"purchase_order": get_purchase_order(filters),
		"expense_claim": get_expense_claim(filters),
		"purchase_invoice": get_purchase_invoice(filters)
	}


def get_conditions(filters):

	conditions = ""

	if filters.project:
		conditions += f" AND project = '{filters.project}' "

	if filters.supplier:
		conditions += f" AND supplier = '{filters.supplier}' "

	if filters.branch:
		conditions += f" AND branch = '{filters.branch}' "

	return conditions


def get_employee_timesheet(filters):

    conditions = ""

    if filters.project:
        conditions += " AND tsd.project = %(project)s "

    if filters.branch:
        conditions += " AND emp.branch = %(branch)s "

    query = f"""
        SELECT

            IFNULL(tsd.project, '') AS project,

            IFNULL(proj.project_name, '') AS project_name,

            IFNULL(
                IFNULL(ts.department, emp.department),
                ''
            ) AS department,

            IFNULL(emp.branch, '') AS branch,

            CASE
                WHEN MAX(ts.stand_by) = 1
                THEN 'Yes'
                ELSE 'No'
            END AS stand_by,

            DATE_FORMAT(tsd.from_time, '%%b-%%Y') AS month_year,

            SUM(
                IFNULL(tsd.working_hours, 0)
                *
                IFNULL(tsd.working_hour_rate_, 0)
            ) AS working_amount,

            SUM(
                IFNULL(tsd.ot_hrs, 0)
                *
                IFNULL(tsd.ot_hours_rate_, 0)
            ) AS ot_amount

        FROM `tabTimesheet Detail` tsd

        INNER JOIN `tabTimesheet` ts
            ON ts.name = tsd.parent

        LEFT JOIN `tabEmployee` emp
            ON emp.name = ts.employee

        LEFT JOIN `tabProject` proj
            ON proj.name = tsd.project

        WHERE
            ts.docstatus = 1
            AND DATE(tsd.from_time) BETWEEN %(from_date)s AND %(to_date)s
            AND IFNULL(tsd.project, '') != ''
            {conditions}

        GROUP BY
            tsd.project,
            proj.project_name,
            IFNULL(ts.department, emp.department),
            emp.branch,
            YEAR(tsd.from_time),
            MONTH(tsd.from_time)

        ORDER BY
            YEAR(tsd.from_time),
            MONTH(tsd.from_time)
    """

    data = frappe.db.sql(query, filters, as_dict=1)

    if not data:
        return []

    # ---------------------------------------------------------
    # Grand Totals
    # ---------------------------------------------------------

    total_working_amount = 0.0
    total_ot_amount = 0.0

    for row in data:

        total_working_amount += flt(
            row.get("working_amount")
        )

        total_ot_amount += flt(
            row.get("ot_amount")
        )

    # ---------------------------------------------------------
    # Total Row
    # ---------------------------------------------------------

    data.append({
        "project": "",
        "project_name": "<b>Grand Total</b>",
        "department": "",
        "branch": "",
        "stand_by": "",
        "month_year": "",
        "working_amount": flt(total_working_amount, 2),
        "ot_amount": flt(total_ot_amount, 2),
        "is_total_row": 1,
    })

    return data




def get_equipment_timesheet(filters):

	conditions, values = get_conditions_for_timesheet(filters)

	# Merge from_date / to_date into values
	values["from_date"] = filters.from_date
	values["to_date"]   = filters.to_date

	query = """
		SELECT
			IFNULL(ret.project_id, '(No Project)')   AS project,
			IFNULL(proj.project_name, '')             AS project_name,
			IFNULL(ret.supplier_name, '')             AS supplier,
			IFNULL(sup.supplier_name, '')             AS supplier_name,
			DATE_FORMAT(MIN(ret.date), '%%b-%%Y')     AS month_year,
			YEAR(ret.date)                            AS year_num,
			MONTH(ret.date)                           AS month_num,
			IFNULL(eam.item, '')                      AS item_code,
			SUM(IFNULL(ret.hours, 0))                 AS total_hours

		FROM `tabRental Equipment Timesheet` ret

		LEFT JOIN `tabProject`                    proj ON proj.name = ret.project_id
		LEFT JOIN `tabSupplier`                   sup  ON sup.name  = ret.supplier_name
		LEFT JOIN `tabEquipment Asset Management` eam  ON eam.name  = ret.door_no_or_plate_no

		WHERE
			ret.date BETWEEN %(from_date)s AND %(to_date)s
			{conditions}

		GROUP BY
			ret.project_id,
			ret.supplier_name,
			YEAR(ret.date),
			MONTH(ret.date),
			eam.item

		ORDER BY
			ret.project_id    ASC,
			YEAR(ret.date)    ASC,
			MONTH(ret.date)   ASC,
			ret.supplier_name ASC
	""".format(conditions=conditions)

	rows = frappe.db.sql(query, values, as_dict=1)

	if not rows:
		return []

	rate_cache = {}
	monthly    = {}

	for row in rows:

		item_code = row.item_code or ""

		if item_code not in rate_cache:
			rate_cache[item_code] = get_average_rate_for_item(item_code)

		avg_rate   = rate_cache[item_code]
		row_amount = flt(avg_rate) * flt(row.total_hours)

		key = (row.project, row.supplier, row.year_num, row.month_num)

		if key not in monthly:
			monthly[key] = {
				"project":       row.project,
				"project_name":  row.project_name,
				"supplier":      row.supplier,
				"supplier_name": row.supplier_name,
				"month_year":    row.month_year,
				"total_hours":   0.0,
				"total_amount":  0.0,
			}

		monthly[key]["total_hours"]  += flt(row.total_hours)
		monthly[key]["total_amount"] += flt(row_amount)

	data = []

	# Grand Totals
	grand_total_hours = 0.0
	grand_total_amount = 0.0

	for d in monthly.values():

		total_hours = flt(d.get("total_hours"), 2)
		total_amount = flt(d.get("total_amount"), 2)

		grand_total_hours += total_hours
		grand_total_amount += total_amount

		data.append({
			"project":       d.get("project") or "",
			"project_name":  d.get("project_name") or "",
			"supplier":      d.get("supplier") or "",
			"supplier_name": d.get("supplier_name") or "",
			"month_year":    d.get("month_year") or "",
			"total_hours":   total_hours,
			"total_amount":  total_amount,
		})

	# Add Total Row
	data.append({
		"project":       "",
		"project_name":  "<b>Grand Total</b>",
		"supplier":      "",
		"supplier_name": "",
		"month_year":    "",
		"total_hours":   flt(grand_total_hours, 2),
		"total_amount":  flt(grand_total_amount, 2),
		"is_total_row":  1,
	})

	return data


def get_conditions_for_timesheet(filters):
	"""
	Build SQL conditions and named-placeholder values dict
	from the filters object — mirrors get_conditions() in the
	reference report but scoped to the timesheet helper.
	"""
	conditions = []
	values     = {}

	# docstatus  --------------------------------------------------------
	if filters.get("state"):
		state_map = {"Draft": 0, "Submitted": 1, "Cancelled": 2}
		if filters["state"] in state_map:
			conditions.append("AND ret.docstatus = %(docstatus)s")
			values["docstatus"] = state_map[filters["state"]]
	# No state filter → no docstatus restriction (show all)

	# project  ----------------------------------------------------------
	if filters.get("project"):
		conditions.append("AND ret.project_id = %(project)s")
		values["project"] = filters["project"]

	# supplier  ---------------------------------------------------------
	if filters.get("supplier"):
		conditions.append("AND ret.supplier_name = %(supplier)s")
		values["supplier"] = filters["supplier"]

	# month  ------------------------------------------------------------
	if filters.get("month"):
		month_num = [
			"January","February","March","April","May","June",
			"July","August","September","October","November","December",
		].index(filters["month"]) + 1
		conditions.append("AND MONTH(ret.date) = %(month_num)s")
		values["month_num"] = month_num

	# year  -------------------------------------------------------------
	if filters.get("year"):
		conditions.append("AND YEAR(ret.date) = %(year)s")
		values["year"] = filters["year"]

	return " ".join(conditions), values

def get_average_rate_for_item(item_code):

	if not item_code:
		return 0.0

	rows = frappe.db.sql("""
		SELECT boi.rate

		FROM `tabBlanket Order Item` boi

		INNER JOIN `tabBlanket Order` bo
			ON bo.name = boi.parent

		WHERE
			bo.docstatus = 1
			AND boi.item_code = %(item_code)s
	""", {
		"item_code": item_code
	}, as_list=1)

	rates = [r[0] for r in rows if r[0]]

	if not rates:
		return 0.0

	return sum(rates) / len(rates)




def get_purchase_order(filters):

	conditions = ""

	if filters.project:
		conditions += " AND po.project = %(project)s "

	if filters.supplier:
		conditions += " AND po.supplier = %(supplier)s "

	query = f"""
		SELECT

			IFNULL(po.project, '') AS project,

			IFNULL(proj.project_name, '') AS project_name,

			IFNULL(po.supplier, '') AS supplier,

			IFNULL(po.supplier_name, '') AS supplier_name,

			IFNULL(po.status, '') AS workflow_state,

			DATE_FORMAT(po.transaction_date, '%%b-%%Y') AS month_year,

			IFNULL(po.per_billed, 0) AS per_billed,

			IFNULL(po.per_received, 0) AS per_received,

			IFNULL(po.grand_total, 0) AS grand_total

		FROM `tabPurchase Order` po

		LEFT JOIN `tabProject` proj
			ON proj.name = po.project

		WHERE
			po.docstatus = 1
			AND po.transaction_date BETWEEN %(from_date)s AND %(to_date)s
			AND IFNULL(po.project, '') != ''
			{conditions}

		ORDER BY
			YEAR(po.transaction_date),
			MONTH(po.transaction_date),
			po.project ASC
	"""

	data = frappe.db.sql(query, filters, as_dict=1)

	if not data:
		return []

	# Calculate Grand Total
	total_grand_total = 0.0

	for row in data:
		total_grand_total += flt(row.get("grand_total"))

	# Append Total Row
	data.append({
		"project": "",
		"project_name": "<b>Grand Total</b>",
		"supplier": "",
		"supplier_name": "",
		"month_year": "",
		"per_billed": "",
		"per_received": "",
		"grand_total": flt(total_grand_total, 2),
		"is_total_row": 1,
	})

	return data


def get_expense_claim(filters):

	conditions = ""

	if filters.project:
		conditions += " AND ecd.project = %(project)s "

	query = f"""
		SELECT

			IFNULL(ecd.project, '') AS project,

			IFNULL(proj.project_name, '') AS project_name,

			IFNULL(ec.employee, '') AS employee,

			IFNULL(ec.employee_name, '') AS employee_name,

			DATE_FORMAT(ec.posting_date, '%%b-%%Y') AS month_year,

			SUM(IFNULL(ec.grand_total, 0)) AS total_amount

		FROM `tabExpense Claim` ec

		INNER JOIN `tabExpense Claim Detail` ecd
			ON ecd.parent = ec.name

		LEFT JOIN `tabProject` proj
			ON proj.name = ecd.project

		WHERE
			ec.docstatus = 1
			AND ec.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND IFNULL(ecd.project, '') != ''
			{conditions}

		GROUP BY
			ecd.project,
			ec.employee,
			YEAR(ec.posting_date),
			MONTH(ec.posting_date)

		ORDER BY
			YEAR(ec.posting_date),
			MONTH(ec.posting_date),
			ecd.project ASC
	"""

	data = frappe.db.sql(query, filters, as_dict=1)

	if not data:
		return []

	# Calculate Grand Total
	total_amount = 0.0

	for row in data:
		total_amount += flt(row.get("total_amount"))

	# Append Total Row
	data.append({
		"project": "",
		"project_name": "<b>Grand Total</b>",
		"employee": "",
		"employee_name": "",
		"month_year": "",
		"total_amount": flt(total_amount, 2),
		"is_total_row": 1,
	})

	return data


def get_purchase_invoice(filters):

	conditions = ""

	if filters.project:
		conditions += " AND pii.project = %(project)s "

	if filters.supplier:
		conditions += " AND pi.supplier = %(supplier)s "

	query = f"""
		SELECT

			IFNULL(pii.project, '') AS project,

			IFNULL(proj.project_name, '') AS project_name,

			IFNULL(pi.supplier, '') AS supplier,

			IFNULL(pi.supplier_name, '') AS supplier_name,

			IFNULL(pi.status, '') AS workflow_state,

			DATE_FORMAT(pi.posting_date, '%%b-%%Y') AS month_year,

			MAX(IFNULL(pi.grand_total, 0)) AS grand_total

		FROM `tabPurchase Invoice` pi

		INNER JOIN `tabPurchase Invoice Item` pii
			ON pii.parent = pi.name

		LEFT JOIN `tabProject` proj
			ON proj.name = pii.project

		WHERE
			pi.docstatus = 1
			AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND IFNULL(pii.project, '') != ''
			{conditions}

		GROUP BY
			pii.project,
			pi.supplier,
			YEAR(pi.posting_date),
			MONTH(pi.posting_date),
			pi.name

		ORDER BY
			YEAR(pi.posting_date),
			MONTH(pi.posting_date),
			pii.project ASC
	"""

	data = frappe.db.sql(query, filters, as_dict=1)

	if not data:
		return []

	# Calculate Grand Total
	total_grand_total = 0.0

	for row in data:
		total_grand_total += flt(row.get("grand_total"))

	# Append Total Row
	data.append({
		"project": "",
		"project_name": "<b>Grand Total</b>",
		"supplier": "",
		"supplier_name": "",
		"month_year": "",
		"grand_total": flt(total_grand_total, 2),
		"is_total_row": 1,
	})

	return data