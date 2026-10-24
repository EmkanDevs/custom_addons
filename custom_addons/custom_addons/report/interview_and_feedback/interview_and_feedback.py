import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": "Interview",
			"fieldname": "interview",
			"fieldtype": "Link",
			"options": "Interview",
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
			"label": "Designation",
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 140,
		},
		{
			"label": "Round",
			"fieldname": "interview_round",
			"fieldtype": "Link",
			"options": "Interview Round",
			"width": 130,
		},
		{
			"label": "Scheduled On",
			"fieldname": "scheduled_on",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": "Interview Status",
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": "Interviewer",
			"fieldname": "interviewer",
			"fieldtype": "Link",
			"options": "User",
			"width": 140,
		},
		{
			"label": "Rating",
			"fieldname": "average_rating",
			"fieldtype": "Float",
			"width": 80,
		},
		{
			"label": "Feedback Result",
			"fieldname": "result",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": "Feedback Submitted",
			"fieldname": "feedback_submitted",
			"fieldtype": "Check",
			"width": 130,
		},
	]


def get_data(filters=None):
	filters = filters or {}
	query_filters = {}

	if filters.get("designation"):
		query_filters["designation"] = filters["designation"]
	if filters.get("interview_round"):
		query_filters["interview_round"] = filters["interview_round"]
	if filters.get("status"):
		query_filters["status"] = filters["status"]
	if filters.get("from_date"):
		query_filters["scheduled_on"] = [">=", filters["from_date"]]
	if filters.get("to_date"):
		if "scheduled_on" in query_filters:
			query_filters["scheduled_on"] = ["between", [filters["from_date"], filters["to_date"]]]
		else:
			query_filters["scheduled_on"] = ["<=", filters["to_date"]]

	fields = [
		"name",
		"job_applicant",
		"designation",
		"interview_round",
		"scheduled_on",
		"status",
	]

	interviews = frappe.get_list(
		"Interview",
		filters=query_filters,
		fields=fields,
		order_by="scheduled_on desc",
	)

	if not interviews:
		return []

	interview_names = [i.name for i in interviews]

	feedback_filters = {"interview": ["in", interview_names]}
	if filters.get("interviewer"):
		feedback_filters["interviewer"] = filters["interviewer"]

	feedbacks = frappe.get_list(
		"Interview Feedback",
		filters=feedback_filters,
		fields=["name", "interview", "interviewer", "average_rating", "result", "docstatus"],
		order_by="creation desc",
	)

	feedback_map = {}
	for fb in feedbacks:
		if fb.interview not in feedback_map:
			feedback_map[fb.interview] = []
		feedback_map[fb.interview].append(fb)

	data = []
	for i in interviews:
		fbs = feedback_map.get(i.name, [])
		if fbs:
			for fb in fbs:
				data.append({
					"interview": i.name,
					"job_applicant": i.job_applicant,
					"designation": i.designation,
					"interview_round": i.interview_round,
					"scheduled_on": i.scheduled_on,
					"status": i.status,
					"interviewer": fb.interviewer,
					"average_rating": fb.average_rating,
					"result": fb.result,
					"feedback_submitted": 1 if fb.docstatus == 1 else 0,
				})
		else:
			if not filters.get("interviewer"):
				data.append({
					"interview": i.name,
					"job_applicant": i.job_applicant,
					"designation": i.designation,
					"interview_round": i.interview_round,
					"scheduled_on": i.scheduled_on,
					"status": i.status,
					"interviewer": "",
					"average_rating": None,
					"result": "",
					"feedback_submitted": 0,
				})

	return data
