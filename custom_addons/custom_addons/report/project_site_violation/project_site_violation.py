import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    # Get filters
    project = filters.get("project")
    project_site_violation = filters.get("project_site_violation")
    violation_penalty_reason = filters.get("violation_penalty_reason")

    # Build dynamic conditions
    conditions = []
    if project:
        conditions.append(f"project = '{project}'")
    if project_site_violation:
        conditions.append(f"name = '{project_site_violation}'")
    if violation_penalty_reason:
        conditions.append(f"violation_penalty_reason = '{violation_penalty_reason}'")

    # Join conditions with AND
    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "AND " + where_clause

    # Fetch data
    data = frappe.db.sql(f"""
        SELECT
            name,
            area_permit_no,
            company,
            area_po_no,
            violation_penalty_reason,
            violation_penalty_reason_arabic,
            penalty_date,
            penalty_amount,
            objection_bcd,
            violation_description,
            issuing_authority,
            issuing_authority_arabic,
            project,
            project_name,
            project_manager,
            pm_contact_no,
            area_manager,
            location,
            area,
            penalty_status,
            objection_no,
            objection_status,
            objection_reason
        FROM `tabProject Site Violation`
        WHERE docstatus < 2 {where_clause}
        ORDER BY penalty_date DESC
    """, as_dict=True)

    # Columns remain unchanged
    columns = [
        {"label": "Violation ID", "fieldname": "name", "fieldtype": "Link", "options": "Project Site Violation"},
        {"label": "Area Permit No", "fieldname": "area_permit_no", "fieldtype": "Data"},
        {"label": "Company", "fieldname": "company", "fieldtype": "Data"},
        {"label": "Area PO No", "fieldname": "area_po_no", "fieldtype": "Data"},
        {"label": "Violation Penalty Reason", "fieldname": "violation_penalty_reason", "fieldtype": "Link","options":"Violation Penalty Reason"},
        {"label": "Violation Penalty Reason Arabic", "fieldname": "violation_penalty_reason_arabic", "fieldtype": "Data"},
        {"label": "Penalty Date", "fieldname": "penalty_date", "fieldtype": "Date"},
        {"label": "Penalty Amount", "fieldname": "penalty_amount", "fieldtype": "Currency"},
        {"label": "Objection BCD", "fieldname": "objection_bcd", "fieldtype": "Date"},
        {"label": "Violation Description", "fieldname": "violation_description", "fieldtype": "Data"},
        {"label": "Issuing Authority", "fieldname": "issuing_authority", "fieldtype": "Data"},
        {"label": "Issuing Authority Arabic", "fieldname": "issuing_authority_arabic", "fieldtype": "Data"},
        {"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project"},
        {"label": "Project Name", "fieldname": "project_name", "fieldtype": "Data"},
        {"label": "Project Manager", "fieldname": "project_manager", "fieldtype": "Data"},
        {"label": "PM Contact No", "fieldname": "pm_contact_no", "fieldtype": "Data"},
        {"label": "Area Manager", "fieldname": "area_manager", "fieldtype": "Data"},
        {"label": "Location", "fieldname": "location", "fieldtype": "Data"},
        {"label": "Area", "fieldname": "area", "fieldtype": "Data"},
        {"label": "Penalty Status", "fieldname": "penalty_status", "fieldtype": "Data"},
        {"label": "Objection No", "fieldname": "objection_no", "fieldtype": "Data"},
        {"label": "Objection Status", "fieldname": "objection_status", "fieldtype": "Data"},
        {"label": "Objection Reason", "fieldname": "objection_reason", "fieldtype": "Data"}
    ]

    return columns, data
