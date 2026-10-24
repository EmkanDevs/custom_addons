import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": "Job Offer",
			"fieldname": "job_offer",
			"fieldtype": "Link",
			"options": "Job Offer",
			"width": 150,
		},
		{
			"label": "Applicant",
			"fieldname": "job_applicant",
			"fieldtype": "Link",
			"options": "Job Applicant",
			"width": 150,
		},
		{
			"label": "Applicant Name",
			"fieldname": "applicant_name",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": "Designation",
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
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
			"label": "Offer Date",
			"fieldname": "offer_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": "Offer Status",
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": "Onboarding",
			"fieldname": "onboarding",
			"fieldtype": "Link",
			"options": "Employee Onboarding",
			"width": 150,
		},
		{
			"label": "Onboarding Status",
			"fieldname": "boarding_status",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": "Joining Date",
			"fieldname": "date_of_joining",
			"fieldtype": "Date",
			"width": 110,
		},
	]


def get_data(filters=None):
	filters = filters or {}
	query_filters = {}

	if filters.get("company"):
		query_filters["company"] = filters["company"]
	if filters.get("designation"):
		query_filters["designation"] = filters["designation"]
	if filters.get("status"):
		query_filters["status"] = filters["status"]
	if filters.get("from_date"):
		query_filters["offer_date"] = [">=", filters["from_date"]]
	if filters.get("to_date"):
		if "offer_date" in query_filters:
			query_filters["offer_date"] = ["between", [filters["from_date"], filters["to_date"]]]
		else:
			query_filters["offer_date"] = ["<=", filters["to_date"]]

	fields = [
		"name",
		"job_applicant",
		"applicant_name",
		"designation",
		"company",
		"offer_date",
		"status",
	]

	offers = frappe.get_list(
		"Job Offer",
		filters=query_filters,
		fields=fields,
		order_by="offer_date desc",
	)

	if not offers:
		return []

	applicant_ids = [o.job_applicant for o in offers if o.job_applicant]
	onboarding_map = {}
	if applicant_ids:
		onboardings = frappe.get_list(
			"Employee Onboarding",
			filters={"job_applicant": ["in", applicant_ids]},
			fields=["name", "job_applicant", "boarding_status", "date_of_joining"],
		)
		for onb in onboardings:
			onboarding_map[onb.job_applicant] = onb

	data = []
	for o in offers:
		onb = onboarding_map.get(o.job_applicant, {})
		data.append({
			"job_offer": o.name,
			"job_applicant": o.job_applicant,
			"applicant_name": o.applicant_name or "",
			"designation": o.designation,
			"company": o.company,
			"offer_date": o.offer_date,
			"status": o.status,
			"onboarding": onb.get("name") or "",
			"boarding_status": onb.get("boarding_status") or "",
			"date_of_joining": onb.get("date_of_joining") or "",
		})

	return data
