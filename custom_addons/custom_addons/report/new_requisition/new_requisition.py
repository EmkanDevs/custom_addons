# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {"label": "Requisition", "fieldname": "name", "fieldtype": "Link", "options": "New Requisition", "width": 180},
        {"label": "Requested On", "fieldname": "requested_on", "fieldtype": "Date", "width": 120},
        {"label": "Subject", "fieldname": "subject", "fieldtype": "Data", "width": 200},
        {"label": "Submitted By", "fieldname": "submitted_by", "fieldtype": "Data", "width": 220},
        {"label": "Request From", "fieldname": "request_from", "fieldtype": "Data", "width": 150},
        {"label": "Service Group", "fieldname": "service_group", "fieldtype": "Data", "width": 150},
        {"label": "Department Service", "fieldname": "department_service", "fieldtype": "Data", "width": 150},
        {"label": "Type of Transportation", "fieldname": "custom_type_of_transportation", "fieldtype": "Data", "width": 150},
        {"label": "City", "fieldname": "custom_city", "fieldtype": "Data", "width": 150},
        {"label": "From Date", "fieldname": "custom_from_date", "fieldtype": "Date", "width": 120},
        {"label": "To Date", "fieldname": "custom_to_date", "fieldtype": "Date", "width": 120},
        {"label": "Project", "fieldname": "for_project", "fieldtype": "Link", "options": "Project", "width": 150},
    ]


def get_data(filters):
    conditions = ""
    if filters.get("for_project"):
        conditions += " AND for_project = %(for_project)s"
    if filters.get("name"):
        conditions += " AND name = %(name)s"

    return frappe.db.sql(f"""
        SELECT
            name,
            requested_on,
            subject,
            submitted_by,
            request_from,
            service_group,
            department_service,
            custom_type_of_transportation,
            custom_city,
            custom_from_date,
            custom_to_date,
            for_project
        FROM
            `tabNew Requisition`
        WHERE
            docstatus < 2 {conditions}
        ORDER BY
            creation DESC
    """, filters, as_dict=True)
