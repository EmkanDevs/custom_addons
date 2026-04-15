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
        {"fieldname": "employee",            "label": _("Employee No"),          "fieldtype": "Link",     "options": "Employee",        "width": 130},
        {"fieldname": "employee_name",        "label": _("Employee Name"),        "fieldtype": "Data",                                   "width": 180},
        {"fieldname": "department",           "label": _("Department"),           "fieldtype": "Link",     "options": "Department",      "width": 150},
        {"fieldname": "project_name",         "label": _("Project Name"),         "fieldtype": "Data",                                   "width": 180},
        {"fieldname": "designation",          "label": _("Designation"),          "fieldtype": "Link",     "options": "Designation",     "width": 150},
        {"fieldname": "branch",               "label": _("Branch"),               "fieldtype": "Link",     "options": "Branch",          "width": 130},
        {"fieldname": "employment_type",      "label": _("Employment Type"),      "fieldtype": "Link",     "options": "Employment Type", "width": 140},
        {"fieldname": "working_hours",        "label": _("Working Hours"),        "fieldtype": "Float",                                  "width": 130},
        {"fieldname": "working_hour_rate",    "label": _("Working Hour Rate"),    "fieldtype": "Currency",                               "width": 150},
        {"fieldname": "ot_hours",             "label": _("OT Hours"),             "fieldtype": "Float",                                  "width": 110},
        {"fieldname": "ot_rate",              "label": _("OT Hours Rate"),        "fieldtype": "Currency",                               "width": 130},
        {"fieldname": "working_hour_amount",  "label": _("Working Hour Amount"),  "fieldtype": "Currency",                               "width": 170},
        {"fieldname": "ot_hour_amount",       "label": _("OT Hour Amount"),       "fieldtype": "Currency",                               "width": 150},
    ]


def get_data(filters):
    conditions, values = build_conditions(filters)
    having_clause = build_having_clause(filters, values)

    rows = frappe.db.sql(
        f"""
        SELECT
            ts.employee                                    AS employee,
            ts.employee_name                               AS employee_name,
            IFNULL(ts.department, emp.department)          AS department,
            GROUP_CONCAT(DISTINCT tsd.project ORDER BY tsd.project SEPARATOR ', ')  AS project_name,
            emp.designation                                AS designation,
            emp.branch                                     AS branch,
            emp.employment_type                            AS employment_type,

            SUM(IFNULL(tsd.working_hours, 0))              AS working_hours,
            MAX(IFNULL(tsd.working_hour_rate_, 0))         AS working_hour_rate,
            SUM(IFNULL(tsd.ot_hrs, 0))                     AS ot_hours,
            MAX(IFNULL(tsd.ot_hours_rate_, 0))             AS ot_rate

        FROM
            `tabTimesheet` ts
        LEFT JOIN
            `tabEmployee` emp ON emp.name = ts.employee
        LEFT JOIN
            `tabTimesheet Detail` tsd ON tsd.parent = ts.name
        WHERE
            {conditions}
        GROUP BY
            ts.employee,
            ts.employee_name,
            IFNULL(ts.department, emp.department),
            emp.designation,
            emp.branch,
            emp.employment_type
        {having_clause}
        ORDER BY
            ts.employee ASC
        """,
        values,
        as_dict=True,
    )

    result = []
    for row in rows:
        wh  = row.working_hours     or 0
        whr = row.working_hour_rate or 0
        oth = row.ot_hours          or 0
        otr = row.ot_rate           or 0

        row["working_hour_amount"] = wh  * whr
        row["ot_hour_amount"]      = oth * otr
        result.append(row)

    return result


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

    for key, col in {"employee": "ts.employee", "department": "ts.department"}.items():
        if filters.get(key):
            conditions.append(f"{col} = %({key})s")
            values[key] = filters[key]

    for key, col in {
        "branch":          "emp.branch",
        "employment_type": "emp.employment_type",
        "designation":     "emp.designation",
    }.items():
        if filters.get(key):
            conditions.append(f"{col} = %({key})s")
            values[key] = filters[key]

    if filters.get("project"):
        conditions.append(
            "EXISTS ("
            "  SELECT 1 FROM `tabTimesheet Detail` tsd2"
            "  WHERE tsd2.parent = ts.name AND tsd2.project = %(project)s"
            ")"
        )
        values["project"] = filters["project"]

    return " AND ".join(conditions), values


def build_having_clause(filters, values):
    """
    Builds the HAVING clause to filter based on aggregated sums 
    of Working Hours + OT Hours.
    """
    having_conditions = []

    if filters.get("total_hours_gt"):
        having_conditions.append("(SUM(IFNULL(tsd.working_hours, 0)) + SUM(IFNULL(tsd.ot_hrs, 0))) > %(total_hours_gt)s")
        values["total_hours_gt"] = flt(filters.get("total_hours_gt"))

    if filters.get("total_hours_lt"):
        having_conditions.append("(SUM(IFNULL(tsd.working_hours, 0)) + SUM(IFNULL(tsd.ot_hrs, 0))) < %(total_hours_lt)s")
        values["total_hours_lt"] = flt(filters.get("total_hours_lt"))

    if having_conditions:
        return "HAVING " + " AND ".join(having_conditions)
    
    return ""