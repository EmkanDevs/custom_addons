import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": "Staffing Plan",
			"fieldname": "staffing_plan",
			"fieldtype": "Link",
			"options": "Staffing Plan",
			"width": 150,
		},
		{
			"label": "Company",
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 140,
		},
		{
			"label": "Department",
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 150,
		},
		{
			"label": "Designation",
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 150,
		},
		{
			"label": "Planned Vacancies",
			"fieldname": "vacancies",
			"fieldtype": "Int",
			"width": 130,
		},
		{
			"label": "Current Count",
			"fieldname": "current_count",
			"fieldtype": "Int",
			"width": 120,
		},
		{
			"label": "Current Openings",
			"fieldname": "current_openings",
			"fieldtype": "Int",
			"width": 130,
		},
		{
			"label": "Variance",
			"fieldname": "variance",
			"fieldtype": "Int",
			"width": 110,
		},
		{
			"label": "From Date",
			"fieldname": "from_date",
			"fieldtype": "Date",
			"width": 100,
		},
		{
			"label": "To Date",
			"fieldname": "to_date",
			"fieldtype": "Date",
			"width": 100,
		},
	]


def get_data(filters=None):
	filters = filters or {}
	plan_filters = {"docstatus": 1}

	if filters.get("company"):
		plan_filters["company"] = filters["company"]
	if filters.get("department"):
		plan_filters["department"] = filters["department"]
	if filters.get("from_date"):
		plan_filters["to_date"] = [">=", filters["from_date"]]
	if filters.get("to_date"):
		plan_filters["from_date"] = ["<=", filters["to_date"]]

	plans = frappe.get_list(
		"Staffing Plan",
		filters=plan_filters,
		fields=["name", "company", "department", "from_date", "to_date"],
		order_by="department asc",
	)

	if not plans:
		return []

	plan_names = [p.name for p in plans]
	plan_map = {p.name: p for p in plans}

	detail_filters = {"parent": ["in", plan_names]}
	if filters.get("designation"):
		detail_filters["designation"] = filters["designation"]

	details = frappe.get_list(
		"Staffing Plan Detail",
		parent_doctype="Staffing Plan",
		filters=detail_filters,
		fields=["parent", "designation", "vacancies", "current_count", "current_openings"],
		order_by="designation asc",
	)

	data = []
	for d in details:
		parent_plan = plan_map.get(d.parent, {})
		vacancies = int(d.vacancies or 0)
		current_count = int(d.current_count or 0)
		current_openings = int(d.current_openings or 0)
		variance = vacancies - current_openings

		data.append({
			"staffing_plan": d.parent,
			"company": parent_plan.get("company"),
			"department": parent_plan.get("department"),
			"designation": d.designation,
			"vacancies": vacancies,
			"current_count": current_count,
			"current_openings": current_openings,
			"variance": variance,
			"from_date": parent_plan.get("from_date"),
			"to_date": parent_plan.get("to_date"),
		})

	return data
