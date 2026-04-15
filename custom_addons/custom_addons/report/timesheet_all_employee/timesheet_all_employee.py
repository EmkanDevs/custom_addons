# # Copyright (c) 2026, Administrator and contributors
# # For license information, please see license.txt

# import frappe
# from frappe import _
# from frappe.utils import flt


# def execute(filters=None):
#     filters = filters or {}
#     columns = get_columns()
#     data = get_data(filters)
#     return columns, data


# def get_columns():
#     return [
#         {"fieldname": "date",                "label": _("Date"),                 "fieldtype": "Date",                                   "width": 110},
#         {"fieldname": "employee",            "label": _("Employee No"),          "fieldtype": "Link",     "options": "Employee",        "width": 130},
#         {"fieldname": "employee_name",        "label": _("Employee Name"),        "fieldtype": "Data",                                   "width": 180},
#         {"fieldname": "department",           "label": _("Department"),           "fieldtype": "Link",     "options": "Department",      "width": 150},
#         {"fieldname": "project_name",         "label": _("Project Name"),         "fieldtype": "Data",                                   "width": 180},
#         {"fieldname": "working_hours",        "label": _("Working Hours"),        "fieldtype": "Float",                                  "width": 120},
#         {"fieldname": "ot_hours",             "label": _("OT Hours"),             "fieldtype": "Float",                                  "width": 100},
#         {"fieldname": "working_hour_amount",  "label": _("Working Hour Amount"),  "fieldtype": "Currency",                               "width": 160},
#         {"fieldname": "ot_hour_amount",       "label": _("OT Hour Amount"),       "fieldtype": "Currency",                               "width": 140},
#     ]


# def get_data(filters):
#     conditions, values = build_conditions(filters)
#     having_clause = build_having_clause(filters, values)

#     rows = frappe.db.sql(
#         f"""
#         SELECT
#             tsd.from_time                                  AS date,
#             emp.name                                       AS employee,
#             emp.employee_name                              AS employee_name,
#             emp.department                                 AS department,
#             GROUP_CONCAT(DISTINCT tsd.project ORDER BY tsd.project SEPARATOR ', ')  AS project_name,
            
#             SUM(IFNULL(tsd.working_hours, 0))              AS working_hours,
#             MAX(IFNULL(tsd.working_hour_rate_, 0))         AS working_hour_rate,
#             SUM(IFNULL(tsd.ot_hrs, 0))                     AS ot_hours,
#             MAX(IFNULL(tsd.ot_hours_rate_, 0))             AS ot_rate

#         FROM
#             `tabEmployee` emp
#         LEFT JOIN
#             `tabTimesheet` ts ON ts.employee = emp.name AND ts.docstatus != 2
#         LEFT JOIN
#             `tabTimesheet Detail` tsd ON tsd.parent = ts.name
#             {" AND " + conditions if conditions else ""}
#         WHERE
#             emp.status = 'Active'
#         GROUP BY
#             tsd.from_time,
#             emp.name,
#             emp.employee_name,
#             emp.department
#         {having_clause}
#         ORDER BY
#             tsd.from_time DESC, emp.name ASC
#         """,
#         values,
#         as_dict=True,
#     )

#     result = []
#     for row in rows:
#         wh  = flt(row.working_hours)
#         whr = flt(row.working_hour_rate)
#         oth = flt(row.ot_hours)
#         otr = flt(row.ot_rate)

#         row["working_hour_amount"] = wh  * whr
#         row["ot_hour_amount"]      = oth * otr
#         result.append(row)

#     return result


# def build_conditions(filters):
#     conditions = []
#     values = {}

#     # Specific Date Filter
#     if filters.get("specific_date"):
#         conditions.append("DATE(tsd.from_time) = %(specific_date)s")
#         values["specific_date"] = filters["specific_date"]

#     # Date Range Filters
#     if filters.get("from_date"):
#         conditions.append("tsd.from_time >= %(from_date)s")
#         values["from_date"] = filters["from_date"]

#     if filters.get("to_date"):
#         conditions.append("tsd.from_time <= %(to_date)s")
#         values["to_date"] = filters["to_date"]

#     if filters.get("status"):
#         status_map = {"Draft": 0, "Submitted": 1, "Cancelled": 2}
#         if filters["status"] in status_map:
#             conditions.append("ts.docstatus = %(docstatus)s")
#             values["docstatus"] = status_map[filters["status"]]

#     for key in ["employee", "department", "branch", "employment_type", "designation"]:
#         if filters.get(key):
#             conditions.append(f"emp.{key} = %({key})s")
#             values[key] = filters[key]

#     return " AND ".join(conditions), values


# def build_having_clause(filters, values):
#     having_conditions = []

#     if filters.get("show_zero_working_hours"):
#         having_conditions.append("(SUM(IFNULL(tsd.working_hours, 0)) + SUM(IFNULL(tsd.ot_hrs, 0))) = 0")
#     else:
#         if filters.get("total_hours_gt"):
#             having_conditions.append("(SUM(IFNULL(tsd.working_hours, 0)) + SUM(IFNULL(tsd.ot_hrs, 0))) > %(total_hours_gt)s")
#             values["total_hours_gt"] = flt(filters.get("total_hours_gt"))
#         if filters.get("total_hours_lt"):
#             having_conditions.append("(SUM(IFNULL(tsd.working_hours, 0)) + SUM(IFNULL(tsd.ot_hrs, 0))) < %(total_hours_lt)s")
#             values["total_hours_lt"] = flt(filters.get("total_hours_lt"))

#     if having_conditions:
#         return "HAVING " + " AND ".join(having_conditions)
    
#     return ""




# Copyright (c) 2026, Administrator and contributors
# For license information, please see license.txt

# Copyright (c) 2026, Administrator and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"fieldname": "date",                "label": _("Date"),                 "fieldtype": "Date",                                   "width": 110},
        {"fieldname": "employee_code",        "label": _("Employee No"),          "fieldtype": "Data",                                  "width": 130},
        {"fieldname": "employee_name",        "label": _("Employee Name"),        "fieldtype": "Data",                                   "width": 180},
        {"fieldname": "department",           "label": _("Department"),           "fieldtype": "Link",     "options": "Department",      "width": 150},
        {"fieldname": "designation",          "label": _("Designation"),          "fieldtype": "Link",     "options": "Designation",     "width": 150},
        {"fieldname": "project_name",         "label": _("Project Name"),         "fieldtype": "Data",                                   "width": 180},
        {"fieldname": "working_hours",        "label": _("Working Hours"),        "fieldtype": "Float",                                  "width": 120},
        {"fieldname": "ot_hours",             "label": _("OT Hours"),             "fieldtype": "Float",                                  "width": 100},
        {"fieldname": "working_hour_amount",  "label": _("Working Hour Amount"),  "fieldtype": "Currency",                               "width": 160},
        {"fieldname": "ot_hour_amount",       "label": _("OT Hour Amount"),       "fieldtype": "Currency",                               "width": 140},
    ]


def get_data(filters):
    join_conditions, where_conditions, values = build_conditions(filters)
    having_clause = build_having_clause(filters, values)

    join_sql  = ("AND " + join_conditions)  if join_conditions  else ""
    where_sql = ("AND " + where_conditions) if where_conditions else ""

    rows = frappe.db.sql(
        f"""
        SELECT
            tsd.from_time                                                            AS date,
            emp.employee                                                             AS employee_code,
            emp.employee_name                                                        AS employee_name,
            emp.department                                                           AS department,
            emp.designation                                                          AS designation,
            GROUP_CONCAT(DISTINCT tsd.project ORDER BY tsd.project SEPARATOR ', ')  AS project_name,

            SUM(IFNULL(tsd.working_hours, 0))              AS working_hours,
            MAX(IFNULL(tsd.working_hour_rate_, 0))         AS working_hour_rate,
            SUM(IFNULL(tsd.ot_hrs, 0))                     AS ot_hours,
            MAX(IFNULL(tsd.ot_hours_rate_, 0))             AS ot_rate

        FROM
            `tabEmployee` emp
        LEFT JOIN
            `tabTimesheet` ts  ON ts.employee = emp.name AND ts.docstatus != 2
        LEFT JOIN
            `tabTimesheet Detail` tsd ON tsd.parent = ts.name
            {join_sql}
        WHERE
            emp.status = 'Active'
            {where_sql}
        GROUP BY
            tsd.from_time,
            emp.name,
            emp.employee_name,
            emp.department,
            emp.designation
        {having_clause}
        ORDER BY
            tsd.from_time DESC, emp.name ASC
        """,
        values,
        as_dict=True,
    )

    result = []
    for row in rows:
        wh  = flt(row.working_hours)
        whr = flt(row.working_hour_rate)
        oth = flt(row.ot_hours)
        otr = flt(row.ot_rate)

        row["working_hour_amount"] = wh  * whr
        row["ot_hour_amount"]      = oth * otr
        result.append(row)

    return result


def build_conditions(filters):
    join_conds  = []
    where_conds = []
    values      = {}

    # Timesheet-detail level
    if filters.get("specific_date"):
        join_conds.append("DATE(tsd.from_time) = %(specific_date)s")
        values["specific_date"] = filters["specific_date"]

    if filters.get("from_date"):
        join_conds.append("tsd.from_time >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        join_conds.append("tsd.from_time <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    if filters.get("status"):
        status_map = {"Draft": 0, "Submitted": 1, "Cancelled": 2}
        if filters["status"] in status_map:
            join_conds.append("ts.docstatus = %(docstatus)s")
            values["docstatus"] = status_map[filters["status"]]

    # Multi-select fields — employee, department, designation
    multi_select_map = {
        "employee":    "emp.name",
        "department":  "emp.department",
        "designation": "emp.designation",
    }

    for field, col in multi_select_map.items():
        val = filters.get(field)

        # Normalize: could arrive as a string or a list
        if not val:
            continue

        if isinstance(val, str):
            val = [v.strip() for v in val.split("\n") if v.strip()]

        if not isinstance(val, (list, tuple)):
            val = [val]

        # Drop empty strings
        val = [v for v in val if v]

        if not val:
            continue

        if len(val) == 1:
            # Single value — use = to avoid single-element tuple edge cases
            where_conds.append(f"{col} = %({field})s")
            values[field] = val[0]
        else:
            where_conds.append(f"{col} IN %({field})s")
            values[field] = tuple(val)

    # Other single-value filters
    for key in ["branch", "employment_type"]:
        if filters.get(key):
            where_conds.append(f"emp.{key} = %({key})s")
            values[key] = filters[key]

    return (
        " AND ".join(join_conds),
        " AND ".join(where_conds),
        values,
    )


def build_having_clause(filters, values):
    having_conditions = []

    if filters.get("show_zero_working_hours"):
        having_conditions.append("(SUM(IFNULL(tsd.working_hours, 0)) + SUM(IFNULL(tsd.ot_hrs, 0))) = 0")
    else:
        if filters.get("total_hours_gt"):
            having_conditions.append("(SUM(IFNULL(tsd.working_hours, 0)) + SUM(IFNULL(tsd.ot_hrs, 0))) > %(total_hours_gt)s")
            values["total_hours_gt"] = flt(filters.get("total_hours_gt"))
        if filters.get("total_hours_lt"):
            having_conditions.append("(SUM(IFNULL(tsd.working_hours, 0)) + SUM(IFNULL(tsd.ot_hrs, 0))) < %(total_hours_lt)s")
            values["total_hours_lt"] = flt(filters.get("total_hours_lt"))

    if having_conditions:
        return "HAVING " + " AND ".join(having_conditions)

    return ""