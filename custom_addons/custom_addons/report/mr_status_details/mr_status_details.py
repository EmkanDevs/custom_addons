# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    """Main function to generate the tree report"""
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data

def get_columns():
    """Define the report columns"""
    return [
        {"label": "Material Request", "fieldname": "material_request", "fieldtype": "Link", "options": "Material Request", "width": 250},
        {"label": "Created By", "fieldname": "owner", "fieldtype": "Data", "width": 150},
        {"label": "Workflow State", "fieldname": "workflow_state", "fieldtype": "Data", "width": 150},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120},
        {"label": "Transaction Date", "fieldname": "transaction_date", "fieldtype": "Date", "width": 150},
        {"label": "Purpose", "fieldname": "material_request_type", "fieldtype": "Select", "width": 150},
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 150},
        {"label": "Quantity", "fieldname": "qty", "fieldtype": "Float", "width": 100},
        {"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 150},
        {"label": "Schedule Date", "fieldname": "schedule_date", "fieldtype": "Date", "width": 120},
        {"label": "Indent", "fieldname": "indent", "fieldtype": "Int", "width": 50,"hidden":1},
        {"label": "Purchase Order", "fieldname": "purchase_order", "fieldtype": "Link", "options": "Purchase Order", "width": 250},
        {"label": "Request for Quotation", "fieldname": "request_for_quotation", "fieldtype": "Link", "options": "Request for Quotation", "width": 250},
        {"label": "Supplier Quotation", "fieldname": "supplier_quotation", "fieldtype": "Link", "options": "Supplier Quotation", "width": 250},
    ]

def get_data(filters):
    """Fetches and organizes the report data in a tree format"""
    conditions = []
    values = {}

    # Handle multiple Material Request IDs
    if filters.get("id"):
        if isinstance(filters["id"], list):
            conditions.append("name IN %(ids)s")
            values["ids"] = tuple(filters["id"])
        else:
            conditions.append("name = %(id)s")
            values["id"] = filters["id"]

    # Handle project filtering
    if filters.get("project"):
        # Modify the query to ensure proper project filtering
        project_conditions = []
        if isinstance(filters["project"], list):
            project_conditions.append("EXISTS (SELECT 1 FROM `tabMaterial Request Item` mri WHERE mri.parent = mr.name AND mri.project IN %(projects)s)")
            values["projects"] = tuple(filters["project"])
        else:
            project_conditions.append("EXISTS (SELECT 1 FROM `tabMaterial Request Item` mri WHERE mri.parent = mr.name AND mri.project = %(project)s)")
            values["project"] = filters["project"]
        
        conditions.extend(project_conditions)
        
    if filters.get("from_date") and filters.get("to_date"):
        conditions.append("""
            EXISTS (
                SELECT 1 
                FROM `tabMaterial Request Item` mri 
                WHERE mri.parent = mr.name
                AND mri.schedule_date BETWEEN %(from_date)s AND %(to_date)s
            )
        """)
        values["from_date"] = filters["from_date"]
        values["to_date"] = filters["to_date"]


    condition_str = " AND ".join(conditions) if conditions else "1=1"

    parent_query = f"""
        SELECT 
            mr.name AS material_request,
            mr.owner,
            mr.workflow_state,
            mr.status,
            mr.transaction_date,
            mr.material_request_type,
            NULL AS item_code,
            NULL AS item_name,
            NULL AS qty,
            NULL AS project,
            NULL AS schedule_date,
            NULL AS parent_material_request,
            0 AS indent,
            (SELECT GROUP_CONCAT(DISTINCT po.name SEPARATOR ', ')
            FROM `tabPurchase Order` po
            JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
            WHERE poi.material_request = mr.name) AS purchase_order,
            (SELECT GROUP_CONCAT(DISTINCT rfq.name SEPARATOR ', ')
            FROM `tabRequest for Quotation` rfq
            JOIN `tabRequest for Quotation Item` rfqi ON rfqi.parent = rfq.name
            WHERE rfqi.material_request = mr.name) AS request_for_quotation,
            (SELECT GROUP_CONCAT(DISTINCT sq.name SEPARATOR ', ')
            FROM `tabSupplier Quotation` sq
            JOIN `tabSupplier Quotation Item` sqi ON sqi.parent = sq.name
            WHERE sqi.request_for_quotation IN (
                SELECT rfq.name 
                FROM `tabRequest for Quotation` rfq
                JOIN `tabRequest for Quotation Item` rfqi ON rfqi.parent = rfq.name
                WHERE rfqi.material_request = mr.name
            )) AS supplier_quotation
        FROM `tabMaterial Request` mr
        WHERE {condition_str}
        ORDER BY mr.creation DESC
    """

    
    parent_rows = frappe.db.sql(parent_query, values, as_dict=True)
    
    data = []
    for parent in parent_rows:
        # Fetch Material Request Items (Child Rows)
        child_conditions = "mri.parent = %s"
        child_values = [parent["material_request"]]

        # Additional project filtering for child rows
        if filters.get("project"):
            if isinstance(filters["project"], list):
                child_conditions += " AND (mri.project IN %s OR mri.project IS NULL)"
                child_values.append(tuple(filters["project"]))
            else:
                child_conditions += " AND (mri.project = %s OR mri.project IS NULL)"
                child_values.append(filters["project"])

        child_query = f"""
            SELECT 
                NULL AS material_request,  
                NULL AS Owner,
                NULL AS workflow_state,
                NULL AS status,
                Null AS transaction_date,
                Null AS material_request_type,
                mri.item_code,
                mri.item_name,
                mri.qty,
                IFNULL(CAST(mri.project AS CHAR), '') AS project,
                mri.schedule_date,
                %s AS parent_material_request,
                1 AS indent  
            FROM `tabMaterial Request Item` AS mri
            WHERE {child_conditions}
        """
        
        child_values.insert(0, parent["material_request"])
        child_rows = frappe.db.sql(child_query, child_values, as_dict=True)
        
        # Only add parent and children if there are child rows
        if child_rows:
            data.append(parent)
            data.extend(child_rows)

    return data