import frappe
from frappe.utils import date_diff, getdate, nowdate


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": "Requisition",
			"fieldname": "requisition",
			"fieldtype": "Link",
			"options": "Job Requisition",
			"width": 160,
		},
		{
			"label": "Designation",
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 150,
		},
		{
			"label": "Department",
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 150,
		},
		{
			"label": "Company",
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 150,
		},
		{
			"label": "Requested By",
			"fieldname": "requested_by",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 150,
		},
		{
			"label": "Status",
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": "Requested Date",
			"fieldname": "requested_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": "Expected By",
			"fieldname": "expected_by",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": "Duration (Days)",
			"fieldname": "duration_days",
			"fieldtype": "Int",
			"width": 120,
		},
	]


def get_data(filters=None):
	filters = filters or {}
	query_filters = {}

	if filters.get("company"):
		query_filters["company"] = filters["company"]
	if filters.get("department"):
		query_filters["department"] = filters["department"]
	if filters.get("designation"):
		query_filters["designation"] = filters["designation"]
	if filters.get("status"):
		query_filters["status"] = filters["status"]
	if filters.get("from_date"):
		query_filters["creation"] = [">=", filters["from_date"]]
	if filters.get("to_date"):
		if "creation" in query_filters:
			query_filters["creation"] = ["between", [filters["from_date"], filters["to_date"]]]
		else:
			query_filters["creation"] = ["<=", filters["to_date"]]

	fields = [
		"name",
		"designation",
		"department",
		"company",
		"requested_by",
		"status",
		"creation",
		"expected_by",
		"modified",
	]

	requisitions = frappe.get_list(
		"Job Requisition",
		filters=query_filters,
		fields=fields,
		order_by="creation desc",
	)

	data = []
	today = nowdate()
	for row in requisitions:
		end_date = row.modified if row.status in ["Filled", "Rejected", "Cancelled"] else today
		start_date = getdate(row.creation)
		duration = date_diff(getdate(end_date), start_date) if start_date else 0

		data.append({
			"requisition": row.name,
			"designation": row.designation,
			"department": row.department,
			"company": row.company,
			"requested_by": row.requested_by,
			"status": row.status,
			"requested_date": start_date,
			"expected_by": row.expected_by,
			"duration_days": duration,
		})

	return data
