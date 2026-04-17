# Copyright (c) 2026, Administrator and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 110},
        {"label": _("Project"), "fieldname": "project_id", "fieldtype": "Link", "options": "Project", "width": 250},
        {"label": _("Supplier Name"), "fieldname": "supplier_name", "fieldtype": "Link", "options": "Supplier", "width": 200},
        {"label": _("Door No or Plate No"), "fieldname": "door_no_or_plate_no", "fieldtype": "Link", "options": "Equipment Asset Management", "width": 160},
        {"label": _("Equipment Name"), "fieldname": "equipment_name", "fieldtype": "Data", "width": 250},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": _("Operator Nationality"), "fieldname": "operator_nationality", "fieldtype": "Data", "width": 180},
        {"label": _("Total Hours"), "fieldname": "hours", "fieldtype": "Float", "width": 100}
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    # We group by the main attributes to get the SUM of hours
    data = frappe.db.sql(f"""
        SELECT 
            date, project_id, supplier_name, door_no_or_plate_no, 
            equipment_name, docstatus, operator_nationality,
            SUM(hours) as hours
        FROM `tabRental Equipment Timesheet`
        WHERE {conditions}
        GROUP BY 
            date, project_id, supplier_name, door_no_or_plate_no, equipment_name
        HAVING hours >= %(total_hours_greater_than)s
    """, filters, as_dict=1)

    # Format docstatus to readable strings
    status_map = {0: "Draft", 1: "Submitted", 2: "Cancelled"}
    for row in data:
        row.status = status_map.get(row.docstatus, "Unknown")
        
    return data

def get_conditions(filters):
    conditions = "1=1"
    if filters.get("from_date"): conditions += " AND date >= %(from_date)s"
    if filters.get("to_date"): conditions += " AND date <= %(to_date)s"
    if filters.get("project"): conditions += " AND project_id = %(project)s"
    if filters.get("supplier"): conditions += " AND supplier_name = %(supplier)s"
    
    # Docstatus filter
    if filters.get("state"):
        state_map = {"Draft": 0, "Submitted": 1, "Cancelled": 2}
        filters["docstatus_val"] = state_map.get(filters.get("state"))
        conditions += " AND docstatus = %(docstatus_val)s"
        
    if not filters.get("total_hours_greater_than"):
        filters["total_hours_greater_than"] = 0
        
    return conditions