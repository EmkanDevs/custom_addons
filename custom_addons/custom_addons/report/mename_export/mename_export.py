# Copyright (c) 2026, Administrator and contributors
# For license information, please see license.txt
import frappe


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": "Employee Code",
            "fieldname": "employee_code",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 130,
        },
        {
            "label": "Transaction Date",
            "fieldname": "transaction_date",
            "fieldtype": "Date",
            "width": 130,
        },
        {
            "label": "Transaction Period",
            "fieldname": "transaction_period",
            "fieldtype": "Float",
            "width": 140,
        },
        {
            "label": "Project Code",
            "fieldname": "project_code",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": "Activity",
            "fieldname": "activity",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": "Job Card",
            "fieldname": "job_card",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Notes",
            "fieldname": "notes",
            "fieldtype": "Data",
            "width": 250,
        },
    ]


def get_data(filters):
    conditions, values = get_conditions(filters)

    rows = frappe.db.sql(
        """
        SELECT
            ts.employee                     AS employee_code,
            ts.start_date                   AS transaction_date,
            tsd.hours                       AS transaction_period,
            IFNULL(p.project_code, '')      AS project_code,
            IFNULL(p.project_name, '')      AS activity,
            ''                              AS job_card,
            IFNULL(tsd.description, '')     AS notes
        FROM `tabTimesheet` ts
        INNER JOIN `tabTimesheet Detail` tsd ON tsd.parent = ts.name
        LEFT  JOIN `tabProject`          p   ON p.name = tsd.project
        WHERE ts.docstatus = 1
          {conditions}
        ORDER BY ts.employee, ts.start_date, tsd.idx
        """.format(conditions=conditions),
        values=values,
        as_dict=True,
    )

    return rows


def get_conditions(filters):
    conditions = []
    values = {}

    if filters.get("employee"):
        conditions.append("AND ts.employee = %(employee)s")
        values["employee"] = filters["employee"]

    if filters.get("project"):
        conditions.append("AND tsd.project = %(project)s")
        values["project"] = filters["project"]

    if filters.get("from_date"):
        conditions.append("AND ts.start_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("AND ts.start_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    return " ".join(conditions), values