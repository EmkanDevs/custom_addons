import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        # Changed to Data type so it only shows the ID string, not the Link title
        {"label": _("Employee ID"), "fieldname": "employee", "fieldtype": "Data", "width": 120},
        {"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
        {"label": _("Transaction Date"), "fieldname": "transaction_date", "fieldtype": "Date", "width": 120},
        {"label": _("Transaction Period"), "fieldname": "transaction_period", "fieldtype": "Float", "width": 160},
        {"label": _("Project"), "fieldname": "activity", "fieldtype": "Link", "options": "Project", "width": 180},
        {"label": _("Notes"), "fieldname": "notes", "fieldtype": "Small Text", "width": 300}
    ]

def get_data(filters):
    conditions = []
    
    # Use parameters to prevent SQL injection
    values = {}
    
    if filters.get("from_date"):
        conditions.append("ts.start_date >= %(from_date)s")
        values["from_date"] = filters.get("from_date")
    if filters.get("to_date"):
        conditions.append("ts.start_date <= %(to_date)s")
        values["to_date"] = filters.get("to_date")
    if filters.get("employee"):
        conditions.append("ts.employee = %(employee)s")
        values["employee"] = filters.get("employee")
    if filters.get("project"):
        conditions.append("ts.parent_project = %(project)s")
        values["project"] = filters.get("project")

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else " WHERE 1=1 "
    
    query = f"""
        SELECT 
            ts.employee as employee,
            emp.employee_name as employee_name,
            ts.start_date as transaction_date,
            ts.total_hours as transaction_period,
            ts.parent_project as activity,
            tld.description as notes
        FROM 
            `tabTimesheet` ts
        LEFT JOIN
            `tabEmployee` emp ON ts.employee = emp.name
        LEFT JOIN
            `tabTimesheet Detail` tld ON tld.parent = ts.name
        {where_clause}
        AND ts.docstatus < 2
        ORDER BY ts.start_date DESC
    """
    
    # Pass values dict to the sql executor for safety
    data = frappe.db.sql(query, values, as_dict=True)
    return data