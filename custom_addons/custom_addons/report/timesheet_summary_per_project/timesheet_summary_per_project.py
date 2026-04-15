# # Copyright (c) 2026, Administrator and contributors
# # For license information, please see license.txt

# import frappe
# from frappe import _


# def execute(filters=None):
# 	filters = filters or {}
# 	columns = get_columns()
# 	data = get_data(filters)
# 	return columns, data


# def get_columns():
# 	return [
# 		{"fieldname": "project",             "label": _("Project"),              "fieldtype": "Link",     "options": "Project",         "width": 160},
# 		{"fieldname": "project_name",        "label": _("Project Name"),         "fieldtype": "Data",                                   "width": 220},
# 		{"fieldname": "department",          "label": _("Department"),           "fieldtype": "Link",     "options": "Department",      "width": 150},
# 		{"fieldname": "branch",              "label": _("Branch"),               "fieldtype": "Link",     "options": "Branch",          "width": 130},
# 		{"fieldname": "employment_type",     "label": _("Employment Type"),      "fieldtype": "Link",     "options": "Employment Type", "width": 140},
# 		{"fieldname": "working_hours",       "label": _("Working Hours"),        "fieldtype": "Float",                                  "width": 130},
# 		{"fieldname": "ot_hours",            "label": _("OT Hours"),             "fieldtype": "Float",                                  "width": 110},
# 		{"fieldname": "working_hour_amount", "label": _("Working Hour Amount"),  "fieldtype": "Currency",                               "width": 170},
# 		{"fieldname": "ot_hour_amount",      "label": _("OT Hour Amount"),       "fieldtype": "Currency",                               "width": 150},
# 	]


# def get_data(filters):
# 	conditions, values = build_conditions(filters)

# 	rows = frappe.db.sql(
# 		f"""
# 		SELECT
# 			tsd.project                                              AS project,
# 			proj.project_name                                        AS project_name,
# 			IFNULL(ts.department, emp.department)                    AS department,
# 			emp.branch                                               AS branch,
# 			emp.employment_type                                      AS employment_type,

# 			SUM(IFNULL(tsd.working_hours, 0))                        AS working_hours,
# 			SUM(IFNULL(tsd.ot_hrs, 0))                               AS ot_hours,

# 			SUM(
# 				IFNULL(tsd.working_hours, 0) * IFNULL(tsd.working_hour_rate_, 0)
# 			)                                                        AS working_hour_amount,
# 			SUM(
# 				IFNULL(tsd.ot_hrs, 0) * IFNULL(tsd.ot_hours_rate_, 0)
# 			)                                                        AS ot_hour_amount

# 		FROM
# 			`tabTimesheet` ts
# 		LEFT JOIN
# 			`tabEmployee` emp ON emp.name = ts.employee
# 		INNER JOIN
# 			`tabTimesheet Detail` tsd ON tsd.parent = ts.name
# 		LEFT JOIN
# 			`tabProject` proj ON proj.name = tsd.project
# 		WHERE
# 			{conditions}
# 		GROUP BY
# 			tsd.project,
# 			proj.project_name,
# 			IFNULL(ts.department, emp.department),
# 			emp.branch,
# 			emp.employment_type
# 		ORDER BY
# 			tsd.project ASC,
# 			IFNULL(ts.department, emp.department) ASC
# 		""",
# 		values,
# 		as_dict=True,
# 	)

# 	return rows


# def build_conditions(filters):
# 	conditions = ["ts.docstatus != 2"]
# 	values = {}

# 	if filters.get("from_date"):
# 		conditions.append("ts.end_date >= %(from_date)s")
# 		values["from_date"] = filters["from_date"]

# 	if filters.get("to_date"):
# 		conditions.append("ts.start_date <= %(to_date)s")
# 		values["to_date"] = filters["to_date"]

# 	if filters.get("status"):
# 		status_map = {"Draft": 0, "Submitted": 1, "Cancelled": 2}
# 		if filters["status"] in status_map:
# 			conditions.append("ts.docstatus = %(docstatus)s")
# 			values["docstatus"] = status_map[filters["status"]]
# 		elif filters["status"] == "Payslip":
# 			conditions.append("ts.status = 'Payslip'")

# 	if filters.get("project"):
# 		conditions.append("tsd.project = %(project)s")
# 		values["project"] = filters["project"]

# 	if filters.get("department"):
# 		conditions.append("IFNULL(ts.department, emp.department) = %(department)s")
# 		values["department"] = filters["department"]

# 	for key, col in {
# 		"branch":          "emp.branch",
# 		"employment_type": "emp.employment_type",
# 	}.items():
# 		if filters.get(key):
# 			conditions.append(f"{col} = %({key})s")
# 			values[key] = filters[key]

# 	return " AND ".join(conditions), values


import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	report_summary = get_report_summary(data)
	return columns, data, None, None, report_summary


def get_columns():
	return [
		{"fieldname": "project",             "label": _("Project"),              "fieldtype": "Link",     "options": "Project",         "width": 160},
		{"fieldname": "project_name",        "label": _("Project Name"),         "fieldtype": "Data",                                   "width": 220},
		{"fieldname": "department",          "label": _("Department"),           "fieldtype": "Link",     "options": "Department",      "width": 150},
		{"fieldname": "branch",              "label": _("Branch"),               "fieldtype": "Link",     "options": "Branch",          "width": 130},
		{"fieldname": "employment_type",     "label": _("Employment Type"),      "fieldtype": "Link",     "options": "Employment Type", "width": 140},
		{"fieldname": "working_hours",       "label": _("Working Hours"),        "fieldtype": "Float",                                  "width": 130},
		{"fieldname": "ot_hours",            "label": _("OT Hours"),             "fieldtype": "Float",                                  "width": 110},
		{"fieldname": "working_hour_amount", "label": _("Working Hour Amount"),  "fieldtype": "Currency",                               "width": 170},
		{"fieldname": "ot_hour_amount",      "label": _("OT Hour Amount"),       "fieldtype": "Currency",                               "width": 150},
	]


def get_report_summary(data):
	total_working_hours    = sum(row.get("working_hours",       0) or 0 for row in data)
	total_ot_hours         = sum(row.get("ot_hours",            0) or 0 for row in data)
	total_working_amount   = sum(row.get("working_hour_amount", 0) or 0 for row in data)
	total_ot_amount        = sum(row.get("ot_hour_amount",      0) or 0 for row in data)

	return [
		{
			"value":     total_working_hours,
			"label":     _("Total Working Hours"),
			"datatype":  "Float",
			"indicator": "Blue",
		},
		{
			"value":     total_ot_hours,
			"label":     _("Total OT Hours"),
			"datatype":  "Float",
			"indicator": "Orange",
		},
		{
			"value":     total_working_amount,
			"label":     _("Total Working Hour Amount"),
			"datatype":  "Currency",
			"indicator": "Green",
		},
		{
			"value":     total_ot_amount,
			"label":     _("Total OT Hour Amount"),
			"datatype":  "Currency",
			"indicator": "Purple",
		},
	]


def get_data(filters):
	conditions, values = build_conditions(filters)

	rows = frappe.db.sql(
		f"""
		SELECT
			tsd.project                                              AS project,
			proj.project_name                                        AS project_name,
			IFNULL(ts.department, emp.department)                    AS department,
			emp.branch                                               AS branch,
			emp.employment_type                                      AS employment_type,

			SUM(IFNULL(tsd.working_hours, 0))                        AS working_hours,
			SUM(IFNULL(tsd.ot_hrs, 0))                               AS ot_hours,

			SUM(
				IFNULL(tsd.working_hours, 0) * IFNULL(tsd.working_hour_rate_, 0)
			)                                                        AS working_hour_amount,
			SUM(
				IFNULL(tsd.ot_hrs, 0) * IFNULL(tsd.ot_hours_rate_, 0)
			)                                                        AS ot_hour_amount

		FROM
			`tabTimesheet` ts
		LEFT JOIN
			`tabEmployee` emp ON emp.name = ts.employee
		INNER JOIN
			`tabTimesheet Detail` tsd ON tsd.parent = ts.name
		LEFT JOIN
			`tabProject` proj ON proj.name = tsd.project
		WHERE
			{conditions}
		GROUP BY
			tsd.project,
			proj.project_name,
			IFNULL(ts.department, emp.department),
			emp.branch,
			emp.employment_type
		ORDER BY
			tsd.project ASC,
			IFNULL(ts.department, emp.department) ASC
		""",
		values,
		as_dict=True,
	)

	return rows


def build_conditions(filters):
	conditions = ["ts.docstatus != 2"]
	values = {}

	if filters.get("from_date"):
		conditions.append("ts.end_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("ts.start_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	if filters.get("status"):
		status_map = {"Draft": 0, "Submitted": 1, "Cancelled": 2}
		if filters["status"] in status_map:
			conditions.append("ts.docstatus = %(docstatus)s")
			values["docstatus"] = status_map[filters["status"]]
		elif filters["status"] == "Payslip":
			conditions.append("ts.status = 'Payslip'")

	if filters.get("project"):
		conditions.append("tsd.project = %(project)s")
		values["project"] = filters["project"]

	if filters.get("department"):
		conditions.append("IFNULL(ts.department, emp.department) = %(department)s")
		values["department"] = filters["department"]

	for key, col in {
		"branch":          "emp.branch",
		"employment_type": "emp.employment_type",
		"designation":     "emp.designation",
	}.items():
		if filters.get(key):
			conditions.append(f"{col} = %({key})s")
			values[key] = filters[key]

	return " AND ".join(conditions), values