import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": "Job Opening",
			"fieldname": "job_opening",
			"fieldtype": "Link",
			"options": "Job Opening",
			"width": 160,
		},
		{
			"label": "Job Title",
			"fieldname": "job_title",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": "Designation",
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 140,
		},
		{
			"label": "Department",
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 140,
		},
		{
			"label": "Company",
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 140,
		},
		{
			"label": "Status",
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": "Published",
			"fieldname": "publish",
			"fieldtype": "Check",
			"width": 80,
		},
		{
			"label": "Posted On",
			"fieldname": "posted_on",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": "Closes On",
			"fieldname": "closes_on",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": "Planned Vacancies",
			"fieldname": "planned_vacancies",
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
	if filters.get("publish") is not None and str(filters.get("publish")).strip() != "":
		query_filters["publish"] = int(filters["publish"])
	if filters.get("from_date"):
		query_filters["posted_on"] = [">=", filters["from_date"]]
	if filters.get("to_date"):
		if "posted_on" in query_filters:
			query_filters["posted_on"] = ["between", [filters["from_date"], filters["to_date"]]]
		else:
			query_filters["posted_on"] = ["<=", filters["to_date"]]

	fields = [
		"name",
		"job_title",
		"designation",
		"department",
		"company",
		"status",
		"publish",
		"posted_on",
		"closes_on",
		"planned_vacancies",
	]

	openings = frappe.get_list(
		"Job Opening",
		filters=query_filters,
		fields=fields,
		order_by="posted_on desc",
	)

	data = []
	for row in openings:
		data.append({
			"job_opening": row.name,
			"job_title": row.job_title or row.name,
			"designation": row.designation,
			"department": row.department,
			"company": row.company,
			"status": row.status,
			"publish": int(row.publish or 0),
			"posted_on": row.posted_on,
			"closes_on": row.closes_on,
			"planned_vacancies": int(row.planned_vacancies or 0),
		})

	return data
