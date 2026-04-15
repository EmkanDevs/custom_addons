# # Copyright (c) 2026, Administrator and contributors
# # For license information, please see license.txt

# import frappe
# from frappe import _


# def execute(filters=None):
# 	if not filters:
# 		filters = {}

# 	columns = get_columns()
# 	data    = get_data(filters)
# 	return columns, data


# # ---------------------------------------------------------------------------
# # Columns
# # ---------------------------------------------------------------------------
# def get_columns():
# 	return [
# 		{"label": _("Project"),              "fieldname": "project",             "fieldtype": "Link",     "options": "Project",         "width": 160},
# 		{"label": _("Department"),           "fieldname": "department",          "fieldtype": "Link",     "options": "Department",      "width": 140},
# 		{"label": _("Branch"),               "fieldname": "branch",              "fieldtype": "Link",     "options": "Branch",          "width": 130},
# 		{"label": _("Employment Type"),      "fieldname": "employment_type",     "fieldtype": "Link",     "options": "Employment Type", "width": 140},
# 		{"label": _("Month"),                "fieldname": "month",               "fieldtype": "Data",                                   "width": 110},
# 		{"label": _("Working Hours"),        "fieldname": "working_hours",       "fieldtype": "Float",    "precision": 2,               "width": 130},
# 		{"label": _("OT Hours"),             "fieldname": "ot_hours",            "fieldtype": "Float",    "precision": 2,               "width": 110},
# 		{"label": _("Working Hour Amount"),  "fieldname": "working_hour_amount", "fieldtype": "Currency",                               "width": 170},
# 		{"label": _("OT Hour Amount"),       "fieldname": "ot_hour_amount",      "fieldtype": "Currency",                               "width": 150},
# 	]


# # ---------------------------------------------------------------------------
# # Data
# # ---------------------------------------------------------------------------
# def get_data(filters):
# 	conditions, values = get_conditions(filters)

# 	query = """
# 		SELECT
# 			IFNULL(tsd.project, '(No Project)')                              AS project,
# 			IFNULL(IFNULL(ts.department, emp.department), '')                AS department,
# 			IFNULL(emp.branch, '')                                           AS branch,
# 			IFNULL(emp.employment_type, '')                                  AS employment_type,
# 			DATE_FORMAT(ts.start_date, '%%b-%%Y')                            AS month,
# 			MONTH(ts.start_date)                                             AS month_num,
# 			YEAR(ts.start_date)                                              AS year_num,

# 			SUM(IFNULL(tsd.working_hours, 0))                                AS working_hours,
# 			SUM(IFNULL(tsd.ot_hrs, 0))                                       AS ot_hours,

# 			SUM(IFNULL(tsd.working_hours, 0) * IFNULL(tsd.working_hour_rate_, 0))
# 			                                                                 AS working_hour_amount,
# 			SUM(IFNULL(tsd.ot_hrs, 0) * IFNULL(tsd.ot_hours_rate_, 0))
# 			                                                                 AS ot_hour_amount
# 		FROM
# 			`tabTimesheet Detail` tsd
# 		INNER JOIN `tabTimesheet` ts
# 			ON ts.name = tsd.parent
# 		LEFT JOIN `tabEmployee` emp
# 			ON emp.name = ts.employee
# 		WHERE
# 			ts.docstatus != 2
# 			{conditions}
# 		GROUP BY
# 			tsd.project,
# 			IFNULL(ts.department, emp.department),
# 			emp.branch,
# 			emp.employment_type,
# 			YEAR(ts.start_date),
# 			MONTH(ts.start_date)
# 		ORDER BY
# 			tsd.project ASC,
# 			IFNULL(ts.department, emp.department) ASC,
# 			YEAR(ts.start_date) ASC,
# 			MONTH(ts.start_date) ASC
# 	""".format(conditions=conditions)

# 	data = frappe.db.sql(query, values, as_dict=True)
# 	return add_group_totals(data)


# # ---------------------------------------------------------------------------
# # Filters → SQL conditions
# # ---------------------------------------------------------------------------
# def get_conditions(filters):
# 	conditions = []
# 	values = {}

# 	if filters.get("month"):
# 		month_num = [
# 			"January", "February", "March", "April", "May", "June",
# 			"July", "August", "September", "October", "November", "December"
# 		].index(filters["month"]) + 1
# 		conditions.append("AND MONTH(ts.start_date) = %(month_num)s")
# 		values["month_num"] = month_num

# 	if filters.get("year"):
# 		conditions.append("AND YEAR(ts.start_date) = %(year)s")
# 		values["year"] = filters["year"]

# 	if filters.get("project"):
# 		conditions.append("AND tsd.project = %(project)s")
# 		values["project"] = filters["project"]

# 	if filters.get("department"):
# 		conditions.append("AND IFNULL(ts.department, emp.department) = %(department)s")
# 		values["department"] = filters["department"]

# 	if filters.get("branch"):
# 		conditions.append("AND emp.branch = %(branch)s")
# 		values["branch"] = filters["branch"]

# 	if filters.get("employment_type"):
# 		conditions.append("AND emp.employment_type = %(employment_type)s")
# 		values["employment_type"] = filters["employment_type"]

# 	if filters.get("state"):
# 		conditions.append("AND ts.status = %(state)s")
# 		values["state"] = filters["state"]

# 	return " ".join(conditions), values


# # ---------------------------------------------------------------------------
# # Group subtotals – bold Total row per project
# # ---------------------------------------------------------------------------
# def add_group_totals(data):
# 	if not data:
# 		return data

# 	result        = []
# 	current_proj  = None
# 	group_rows    = []

# 	def flush_group(rows):
# 		result.extend(rows)
# 		if len(rows) > 1:
# 			result.append({
# 				"project":             rows[0].get("project"),
# 				"department":          "",
# 				"branch":              "",
# 				"employment_type":     "",
# 				"month":               _("Total"),
# 				"working_hours":       sum(r.get("working_hours")       or 0 for r in rows),
# 				"ot_hours":            sum(r.get("ot_hours")            or 0 for r in rows),
# 				"working_hour_amount": sum(r.get("working_hour_amount") or 0 for r in rows),
# 				"ot_hour_amount":      sum(r.get("ot_hour_amount")      or 0 for r in rows),
# 				"bold": 1,
# 			})

# 	for row in data:
# 		if row["project"] != current_proj:
# 			if group_rows:
# 				flush_group(group_rows)
# 			current_proj = row["project"]
# 			group_rows   = []
# 		group_rows.append(row)

# 	if group_rows:
# 		flush_group(group_rows)

# 	return result



import frappe
from frappe import _


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
		{"label": _("Project"),              "fieldname": "project",             "fieldtype": "Link",     "options": "Project",         "width": 160},
		{"fieldname": "project_name",        "label": _("Project Name"),         "fieldtype": "Data",                                   "width": 220},
		{"label": _("Department"),           "fieldname": "department",          "fieldtype": "Link",     "options": "Department",      "width": 140},
		{"label": _("Branch"),               "fieldname": "branch",              "fieldtype": "Link",     "options": "Branch",          "width": 130},
		{"label": _("Employment Type"),      "fieldname": "employment_type",     "fieldtype": "Link",     "options": "Employment Type", "width": 140},
		{"label": _("Month"),                "fieldname": "month",               "fieldtype": "Data",                                   "width": 110},
		{"label": _("Working Hours"),        "fieldname": "working_hours",       "fieldtype": "Float",    "precision": 2,               "width": 130},
		{"label": _("OT Hours"),             "fieldname": "ot_hours",            "fieldtype": "Float",    "precision": 2,               "width": 110},
		{"label": _("Working Hour Amount"),  "fieldname": "working_hour_amount", "fieldtype": "Currency",                               "width": 170},
		{"label": _("OT Hour Amount"),       "fieldname": "ot_hour_amount",      "fieldtype": "Currency",                               "width": 150},
	]


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def get_data(filters):
	conditions, values = get_conditions(filters)

	query = """
		SELECT
			IFNULL(tsd.project, '(No Project)')                              AS project,
			proj.project_name                                                AS project_name,
			IFNULL(IFNULL(ts.department, emp.department), '')                AS department,
			IFNULL(emp.branch, '')                                           AS branch,
			IFNULL(emp.employment_type, '')                                  AS employment_type,
			DATE_FORMAT(ts.start_date, '%%b-%%Y')                            AS month,
			MONTH(ts.start_date)                                             AS month_num,
			YEAR(ts.start_date)                                              AS year_num,

			SUM(IFNULL(tsd.working_hours, 0))                                AS working_hours,
			SUM(IFNULL(tsd.ot_hrs, 0))                                       AS ot_hours,

			SUM(IFNULL(tsd.working_hours, 0) * IFNULL(tsd.working_hour_rate_, 0))
			                                                                 AS working_hour_amount,
			SUM(IFNULL(tsd.ot_hrs, 0) * IFNULL(tsd.ot_hours_rate_, 0))
			                                                                 AS ot_hour_amount
		FROM
			`tabTimesheet Detail` tsd
		INNER JOIN `tabTimesheet` ts
			ON ts.name = tsd.parent
		LEFT JOIN `tabEmployee` emp
			ON emp.name = ts.employee
		LEFT JOIN
			`tabProject` proj ON proj.name = tsd.project
		WHERE
			ts.docstatus != 2
			{conditions}
		GROUP BY
			tsd.project,
			proj.project_name,
			IFNULL(ts.department, emp.department),
			emp.branch,
			emp.employment_type,
			YEAR(ts.start_date),
			MONTH(ts.start_date)
		ORDER BY
			tsd.project ASC,
			IFNULL(ts.department, emp.department) ASC,
			YEAR(ts.start_date) ASC,
			MONTH(ts.start_date) ASC
	""".format(conditions=conditions)

	data = frappe.db.sql(query, values, as_dict=True)
	# return add_group_totals(data)
	return data

# ---------------------------------------------------------------------------
# Filters → SQL conditions
# ---------------------------------------------------------------------------
def get_conditions(filters):
	conditions = []
	values = {}

	if filters.get("month"):
		month_num = [
			"January", "February", "March", "April", "May", "June",
			"July", "August", "September", "October", "November", "December"
		].index(filters["month"]) + 1
		conditions.append("AND MONTH(ts.start_date) = %(month_num)s")
		values["month_num"] = month_num

	if filters.get("year"):
		conditions.append("AND YEAR(ts.start_date) = %(year)s")
		values["year"] = filters["year"]

	if filters.get("project"):
		conditions.append("AND tsd.project = %(project)s")
		values["project"] = filters["project"]

	if filters.get("department"):
		conditions.append("AND IFNULL(ts.department, emp.department) = %(department)s")
		values["department"] = filters["department"]

	if filters.get("branch"):
		conditions.append("AND emp.branch = %(branch)s")
		values["branch"] = filters["branch"]

	if filters.get("employment_type"):
		conditions.append("AND emp.employment_type = %(employment_type)s")
		values["employment_type"] = filters["employment_type"]

	if filters.get("state"):
		conditions.append("AND ts.status = %(state)s")
		values["state"] = filters["state"]

	return " ".join(conditions), values


# ---------------------------------------------------------------------------
# Group subtotals
# ---------------------------------------------------------------------------
# def add_group_totals(data):
# 	"""
# 	- Shows project name only on the FIRST row of each group (blank for rest).
# 	- Appends a bold subtotal row at the end of each group (when > 1 row).
# 	"""
# 	if not data:
# 		return data

# 	result       = []
# 	current_proj = None
# 	group_rows   = []

# 	def flush_group(rows):
# 		# Blank out the project on every row except the first
# 		for i, row in enumerate(rows):
# 			if i > 0:
# 				row["project"] = ""

# 		result.extend(rows)

# 		# Only add a Total row when the group has more than one detail row
# 		if len(rows) > 1:
# 			result.append({
# 				"project":             rows[0].get("_project_key"),   # bold label
# 				"department":          "",
# 				"branch":              "",
# 				"employment_type":     "",
# 				"month":               _("Total"),
# 				"working_hours":       sum(r.get("working_hours")       or 0 for r in rows),
# 				"ot_hours":            sum(r.get("ot_hours")            or 0 for r in rows),
# 				"working_hour_amount": sum(r.get("working_hour_amount") or 0 for r in rows),
# 				"ot_hour_amount":      sum(r.get("ot_hour_amount")      or 0 for r in rows),
# 				"bold": 1,
# 			})

# 	for row in data:
# 		proj_key = row["project"]  # original value before we blank it
# 		row["_project_key"] = proj_key  # stash for the total row label

# 		if proj_key != current_proj:
# 			if group_rows:
# 				flush_group(group_rows)
# 			current_proj = proj_key
# 			group_rows   = []

# 		group_rows.append(row)

# 	if group_rows:
# 		flush_group(group_rows)

	# return result