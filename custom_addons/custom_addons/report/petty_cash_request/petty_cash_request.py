# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data

def get_columns():
    return [
        {"label": "Petty Cash Request", "fieldname": "name", "fieldtype": "Link", "options": "Petty Cash Request", "width": 180},
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
        {"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 200},
        {"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 150},
        {"label": "Required Amount", "fieldname": "required_amount", "fieldtype": "Currency", "width": 150},
        {"label": "Received Amount", "fieldname": "received_amount", "fieldtype": "Currency", "width": 150},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": "Date Required On", "fieldname": "date_required_on", "fieldtype": "Date", "width": 120},
        {"label": "Priority", "fieldname": "priority", "fieldtype": "Data", "width": 100}
    ]

def get_data(filters):
    conditions = ""
    if filters.get("project"):
        conditions += " AND project = %(project)s"
    if filters.get("name"):
        conditions += " AND name = %(name)s"

    return frappe.db.sql(f"""
        SELECT
            name,
            employee,
            employee_name,
            company,
            project,
            required_amount,
            received_amount,
            status,
            date_required_on,
            priority
        FROM
            `tabPetty Cash Request`
        WHERE
            docstatus < 2 {conditions}
        ORDER BY
            creation DESC
    """, filters, as_dict=True)
