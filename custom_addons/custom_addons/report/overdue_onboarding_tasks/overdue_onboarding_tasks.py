import frappe
from frappe.utils import date_diff, getdate, nowdate


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": "Onboarding",
			"fieldname": "onboarding",
			"fieldtype": "Link",
			"options": "Employee Onboarding",
			"width": 150,
		},
		{
			"label": "Employee Name",
			"fieldname": "employee_name",
			"fieldtype": "Data",
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
			"width": 140,
		},
		{
			"label": "Task / Activity",
			"fieldname": "activity_name",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": "Task",
			"fieldname": "task",
			"fieldtype": "Link",
			"options": "Task",
			"width": 140,
		},
		{
			"label": "Task Status",
			"fieldname": "task_status",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": "Assigned User",
			"fieldname": "user",
			"fieldtype": "Link",
			"options": "User",
			"width": 140,
		},
		{
			"label": "Expected End Date",
			"fieldname": "exp_end_date",
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"label": "Joining Date",
			"fieldname": "date_of_joining",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": "Overdue (Days)",
			"fieldname": "overdue_days",
			"fieldtype": "Int",
			"width": 120,
		},
	]


def get_data(filters=None):
	filters = filters or {}
	onb_filters = {"boarding_status": ["in", ["Pending", "In Process"]]}

	if filters.get("company"):
		onb_filters["company"] = filters["company"]
	if filters.get("department"):
		onb_filters["department"] = filters["department"]

	fields = [
		"name",
		"employee_name",
		"company",
		"department",
		"boarding_status",
		"date_of_joining",
	]

	onboardings = frappe.get_list(
		"Employee Onboarding",
		filters=onb_filters,
		fields=fields,
		order_by="creation desc",
	)

	if not onboardings:
		return []

	onb_names = [o.name for o in onboardings]
	onb_map = {o.name: o for o in onboardings}

	act_filters = {"parent": ["in", onb_names]}
	if filters.get("user"):
		act_filters["user"] = filters["user"]

	activities = frappe.get_list(
		"Employee Boarding Activity",
		parent_doctype="Employee Onboarding",
		filters=act_filters,
		fields=["parent", "activity_name", "task", "user"],
	)

	task_names = [a.task for a in activities if a.task]
	task_map = {}
	if task_names:
		tasks = frappe.get_list(
			"Task",
			filters={"name": ["in", task_names]},
			fields=["name", "status", "exp_end_date"],
		)
		for t in tasks:
			task_map[t.name] = t

	today = nowdate()
	data = []

	for a in activities:
		onb = onb_map.get(a.parent, {})
		task_obj = task_map.get(a.task, {})
		task_status = task_obj.get("status") or "Open"

		if task_status in ["Completed", "Cancelled"]:
			continue

		if filters.get("task_status") and task_status != filters.get("task_status"):
			continue

		exp_end = task_obj.get("exp_end_date")
		joining = onb.get("date_of_joining")

		due_date = exp_end or joining
		if not due_date:
			continue

		due_date_str = str(due_date)
		if due_date_str >= today:
			continue

		overdue_days = date_diff(today, getdate(due_date))

		data.append({
			"onboarding": a.parent,
			"employee_name": onb.get("employee_name") or "",
			"company": onb.get("company") or "",
			"department": onb.get("department") or "",
			"activity_name": a.activity_name or "",
			"task": a.task or "",
			"task_status": task_status,
			"user": a.user or "",
			"exp_end_date": exp_end or "",
			"date_of_joining": joining or "",
			"overdue_days": overdue_days,
		})

	data.sort(key=lambda x: x["overdue_days"], reverse=True)
	return data
