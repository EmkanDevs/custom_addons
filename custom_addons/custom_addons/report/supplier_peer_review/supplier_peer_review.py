# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import formatdate

def execute(filters=None):
    """Main function to generate the comprehensive report"""
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data

def get_columns():
    """Define all report columns"""
    return [
        # Material Request Fields
        {"label": "Material Request", "fieldname": "material_request", "fieldtype": "Link", "options": "Material Request", "width": 180},
        {"label": "MR Transaction Date", "fieldname": "mr_transaction_date", "fieldtype": "Date", "width": 130},
        {"label": "MR Workflow State", "fieldname": "mr_workflow_state", "fieldtype": "Data", "width": 150},
        {"label": "MR Status", "fieldname": "mr_status", "fieldtype": "Data", "width": 120},
        {"label": "MR Set Target Warehouse", "fieldname": "mr_set_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 150},
        {"label": "MR % Ordered", "fieldname": "mr_per_ordered", "fieldtype": "Percent", "width": 110},
        {"label": "MR % Received", "fieldname": "mr_per_received", "fieldtype": "Percent", "width": 110},
        
        # Supplier Quotation Fields
        {"label": "Supplier Quotation", "fieldname": "supplier_quotation", "fieldtype": "Link", "options": "Supplier Quotation", "width": 180},
        {"label": "SQ Supplier Name", "fieldname": "sq_supplier_name", "fieldtype": "Data", "width": 150},
        {"label": "SQ Date", "fieldname": "sq_date", "fieldtype": "Date", "width": 120},
        {"label": "SQ Total", "fieldname": "sq_total", "fieldtype": "Currency", "width": 130},
        {"label": "SQ Taxes and Charges", "fieldname": "sq_total_taxes_and_charges", "fieldtype": "Currency", "width": 130},
        {"label": "SQ Grand Total", "fieldname": "sq_grand_total", "fieldtype": "Currency", "width": 130},
        {"label": "SQ Status", "fieldname": "sq_status", "fieldtype": "Data", "width": 120},
        
        # Purchase Order Fields
        {"label": "Purchase Order", "fieldname": "purchase_order", "fieldtype": "Link", "options": "Purchase Order", "width": 180},
        {"label": "PO Supplier Name", "fieldname": "po_supplier_name", "fieldtype": "Data", "width": 150},
        {"label": "PO Supplier", "fieldname": "po_supplier", "fieldtype": "Link", "options": "Supplier", "width": 150},
        {"label": "PO Created By", "fieldname": "po_owner", "fieldtype": "Data", "width": 150},
        {"label": "PO Status", "fieldname": "po_status", "fieldtype": "Data", "width": 120},
        {"label": "PO Project", "fieldname": "po_project", "fieldtype": "Link", "options": "Project", "width": 150},
        {"label": "PO Project Name", "fieldname": "po_project_name", "fieldtype": "Data", "width": 180},
        {"label": "PO Created On", "fieldname": "po_creation_date", "fieldtype": "Data", "width": 150},
        {"label": "PO Total Taxes", "fieldname": "po_total_taxes", "fieldtype": "Currency", "width": 130},
        {"label": "PO Grand Total", "fieldname": "po_grand_total", "fieldtype": "Currency", "width": 130},
        {"label": "PO % Billed", "fieldname": "po_per_billed", "fieldtype": "Percent", "width": 110},
        {"label": "PO % Received", "fieldname": "po_per_received", "fieldtype": "Percent", "width": 110},
        {"label": "PO Workflow State", "fieldname": "po_workflow_state", "fieldtype": "Data", "width": 150},
        
        # Purchase Receipt Fields
        {"label": "Purchase Receipt", "fieldname": "purchase_receipt", "fieldtype": "Link", "options": "Purchase Receipt", "width": 180},
        {"label": "PR % Amount Billed", "fieldname": "pr_per_billed", "fieldtype": "Percent", "width": 130},
        {"label": "PR Is Petty Cash", "fieldname": "pr_is_petty_cash", "fieldtype": "Check", "width": 120},
        {"label": "PR Petty Cash Holder", "fieldname": "pr_petty_cash_holder", "fieldtype": "Data", "width": 150},
        {"label": "PR Petty Cash Employee", "fieldname": "pr_petty_cash_employee", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": "PR Date", "fieldname": "pr_date", "fieldtype": "Date", "width": 120},
        {"label": "PR Accepted Warehouse", "fieldname": "pr_accepted_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 150},
        {"label": "PR Workflow State", "fieldname": "pr_workflow_state", "fieldtype": "Data", "width": 150},
        {"label": "PR Supplier", "fieldname": "pr_party_name", "fieldtype": "Data", "width": 150},
        
        # Payment Request Fields
        {"label": "Payment Request", "fieldname": "payment_request", "fieldtype": "Link", "options": "Payment Request", "width": 180},
        {"label": "PRQ Transaction Date", "fieldname": "prq_transaction_date", "fieldtype": "Date", "width": 130},
        {"label": "PRQ Type", "fieldname": "prq_payment_type", "fieldtype": "Data", "width": 120},
        {"label": "PRQ Amount", "fieldname": "prq_amount", "fieldtype": "Currency", "width": 120},
        {"label": "PRQ Workflow State", "fieldname": "prq_workflow_state", "fieldtype": "Data", "width": 150},
        
        # Purchase Invoice Fields
        {"label": "Purchase Invoice", "fieldname": "purchase_invoice", "fieldtype": "Link", "options": "Purchase Invoice", "width": 180},
        {"label": "PI Grand Total", "fieldname": "pi_grand_total", "fieldtype": "Currency", "width": 130},
        {"label": "PI Workflow State", "fieldname": "pi_workflow_state", "fieldtype": "Data", "width": 150},
        {"label": "PI Date", "fieldname": "pi_date", "fieldtype": "Date", "width": 120},
        {"label": "PI Credit To", "fieldname": "pi_credit_to", "fieldtype": "Link", "options": "Account", "width": 150},
        {"label": "PI Supplier Warehouse", "fieldname": "pi_supplier_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 150},
        
        # Payment Entry Fields
        {"label": "Payment Entry", "fieldname": "payment_entry", "fieldtype": "Link", "options": "Payment Entry", "width": 180},
        {"label": "PE Posting Date", "fieldname": "pe_posting_date", "fieldtype": "Date", "width": 130},
        {"label": "PE Paid Amount", "fieldname": "pe_paid_amount", "fieldtype": "Currency", "width": 130},
        {"label": "PE Paid Amount After Tax", "fieldname": "pe_paid_amount_after_tax", "fieldtype": "Currency", "width": 150},
        {"label": "PE Mode of Payment", "fieldname": "pe_mode_of_payment", "fieldtype": "Data", "width": 150},
        {"label": "PE Workflow State", "fieldname": "pe_workflow_state", "fieldtype": "Data", "width": 150},
        
    ]

def get_data(filters):
    """Fetches and organizes the comprehensive report data with Material Request as parent"""
    conditions = []
    values = {}

    # Apply filters for Material Request
    if filters.get("id"):
        if isinstance(filters["id"], list):
            conditions.append("mr.name IN %(ids)s")
            values["ids"] = tuple(filters["id"])
        else:
            conditions.append("mr.name = %(id)s")
            values["id"] = filters["id"]

    if filters.get("project"):
        if isinstance(filters["project"], list):
            conditions.append("""EXISTS (
                SELECT 1 FROM `tabMaterial Request Item` mri 
                INNER JOIN `tabPurchase Order Item` poi ON poi.material_request = mr.name
                WHERE mri.parent = mr.name AND poi.project IN %(projects)s
            )""")
            values["projects"] = tuple(filters["project"])
        else:
            conditions.append("""EXISTS (
                SELECT 1 FROM `tabMaterial Request Item` mri 
                INNER JOIN `tabPurchase Order Item` poi ON poi.material_request = mr.name
                WHERE mri.parent = mr.name AND poi.project = %(project)s
            )""")
            values["project"] = filters["project"]
        
    if filters.get("from_date") and filters.get("to_date"):
        conditions.append("mr.transaction_date BETWEEN %(from_date)s AND %(to_date)s")
        values["from_date"] = filters["from_date"]
        values["to_date"] = filters["to_date"]

    condition_str = " AND ".join(conditions) if conditions else "1=1"

    # Main query to get all Material Requests as parent rows
    parent_query = f"""
        SELECT 
            mr.name AS material_request,
            mr.transaction_date AS mr_transaction_date,
            mr.workflow_state AS mr_workflow_state,
            mr.status AS mr_status,
            mr.set_warehouse AS mr_set_warehouse,
            mr.per_ordered AS mr_per_ordered,
            mr.per_received AS mr_per_received,
            NULL AS purchase_order,
            NULL AS po_supplier_name,
            NULL AS po_supplier,
            NULL AS po_owner,
            NULL AS po_status,
            NULL AS po_project,
            NULL AS po_project_name,
            NULL AS po_creation_date,
            NULL AS po_total_taxes,
            NULL AS po_grand_total,
            NULL AS po_per_billed,
            NULL AS po_per_received,
            NULL AS po_workflow_state,
            NULL AS item_code,
            NULL AS item_name,
            NULL AS qty,
            NULL AS schedule_date,
            0 AS indent
        FROM `tabMaterial Request` mr
        WHERE {condition_str}
        ORDER BY mr.creation DESC
    """
    
    parent_rows = frappe.db.sql(parent_query, values, as_dict=True)
    
    data = []
    for parent in parent_rows:
        mr_name = parent["material_request"]
        
        # Get all Purchase Orders linked to this Material Request
        po_conditions = "poi.material_request = %s"
        po_values = [mr_name]
        
        if filters.get("project"):
            if isinstance(filters["project"], list):
                po_conditions += " AND (poi.project IN %s OR poi.project IS NULL)"
                po_values.append(tuple(filters["project"]))
            else:
                po_conditions += " AND (poi.project = %s OR poi.project IS NULL)"
                po_values.append(filters["project"])
        
        # Get distinct Purchase Orders for this Material Request
        po_query = f"""
            SELECT DISTINCT
                po.name AS purchase_order,
                po.supplier_name AS po_supplier_name,
                po.supplier AS po_supplier,
                po.owner AS po_owner,
                po.status AS po_status,
                DATE_FORMAT(po.creation, '%%d-%%m-%%Y %%H:%%i:%%s') AS po_creation_date,
                po.total_taxes_and_charges AS po_total_taxes,
                po.grand_total AS po_grand_total,
                po.per_billed AS po_per_billed,
                po.per_received AS po_per_received,
                po.workflow_state AS po_workflow_state,
                NULL AS item_code,
                NULL AS item_name,
                NULL AS qty,
                NULL AS schedule_date,
                NULL AS po_project,
                NULL AS po_project_name,
                1 AS indent
            FROM `tabPurchase Order` po
            INNER JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
            WHERE {po_conditions}
            ORDER BY po.creation DESC
        """
        
        po_rows = frappe.db.sql(po_query, po_values, as_dict=True)
        
        # Get Supplier Quotations for this Material Request
        sq_query = """
            SELECT DISTINCT poi.supplier_quotation
            FROM `tabPurchase Order Item` poi
            WHERE poi.material_request = %s AND poi.supplier_quotation IS NOT NULL
            LIMIT 1
        """
        sq_result = frappe.db.sql(sq_query, mr_name, as_dict=True)
        if sq_result and sq_result[0].get("supplier_quotation"):
            sq_details = get_supplier_quotation_details(sq_result[0]["supplier_quotation"])
            parent.update(sq_details)
        
        if po_rows:
            # Add Material Request parent row
            data.append(parent)
            
            # Add Purchase Order child rows
            for po in po_rows:
                po_name = po["purchase_order"]
                
                # Get related documents for this PO
                related_docs = get_related_documents(po_name)
                po.update(related_docs)
                
                # Add Material Request info to PO row
                po["material_request"] = mr_name
                po["mr_transaction_date"] = parent["mr_transaction_date"]
                po["mr_workflow_state"] = parent["mr_workflow_state"]
                po["mr_status"] = parent["mr_status"]
                po["mr_set_warehouse"] = parent["mr_set_warehouse"]
                po["mr_per_ordered"] = parent["mr_per_ordered"]
                po["mr_per_received"] = parent["mr_per_received"]
                
                # Get items for this PO
                item_conditions = "poi.parent = %s AND poi.material_request = %s"
                item_values = [po_name, mr_name]
                
                if filters.get("project"):
                    if isinstance(filters["project"], list):
                        item_conditions += " AND (poi.project IN %s OR poi.project IS NULL)"
                        item_values.append(tuple(filters["project"]))
                    else:
                        item_conditions += " AND (poi.project = %s OR poi.project IS NULL)"
                        item_values.append(filters["project"])
                
                item_query = f"""
                    SELECT 
                        poi.item_code,
                        poi.item_name,
                        poi.qty,
                        poi.schedule_date,
                        IFNULL(CAST(poi.project AS CHAR), '') AS po_project,
                        (SELECT project_name FROM `tabProject` WHERE name = poi.project) AS po_project_name,
                        poi.supplier_quotation,
                        2 AS indent
                    FROM `tabPurchase Order Item` poi
                    WHERE {item_conditions}
                """
                
                item_rows = frappe.db.sql(item_query, item_values, as_dict=True)
                
                if item_rows:
                    # Add PO row
                    data.append(po)
                    
                    # Add item rows
                    for item in item_rows:
                        # Copy all parent data to item
                        item.update({
                            "material_request": mr_name,
                            "mr_transaction_date": parent["mr_transaction_date"],
                            "mr_workflow_state": parent["mr_workflow_state"],
                            "mr_status": parent["mr_status"],
                            "mr_set_warehouse": parent["mr_set_warehouse"],
                            "mr_per_ordered": parent["mr_per_ordered"],
                            "mr_per_received": parent["mr_per_received"],
                            "purchase_order": po_name,
                            "po_supplier_name": po["po_supplier_name"],
                            "po_supplier": po["po_supplier"],
                            "po_owner": po["po_owner"],
                            "po_status": po["po_status"],
                            "po_creation_date": po["po_creation_date"],
                            "po_total_taxes": po["po_total_taxes"],
                            "po_grand_total": po["po_grand_total"],
                            "po_per_billed": po["po_per_billed"],
                            "po_per_received": po["po_per_received"],
                            "po_workflow_state": po["po_workflow_state"]
                        })
                        
                        # Add related documents
                        item.update(related_docs)
                        
                        # Get Supplier Quotation details if available
                        if item.get("supplier_quotation"):
                            sq_details = get_supplier_quotation_details(item["supplier_quotation"])
                            item.update(sq_details)
                        
                        data.append(item)

    return data

def get_related_documents(po_name):
    """Get all related documents for a Purchase Order"""
    related = {}
    
    # Purchase Receipt
    pr_data = frappe.db.sql("""
        SELECT DISTINCT
            pr.name,
            pr.per_billed,
            pr.is_petty_cash,
            pr.custom_petty_cash_holder_name,
            pr.petty_cash_employee,
            pr.posting_date,
            pr.set_warehouse,
            pr.workflow_state,
            pr.supplier_name
        FROM `tabPurchase Receipt` pr
        INNER JOIN `tabPurchase Receipt Item` pri ON pri.parent = pr.name
        INNER JOIN `tabPurchase Order Item` poi ON pri.purchase_order_item = poi.name
        WHERE poi.parent = %s
        LIMIT 1
    """, po_name, as_dict=True)
    
    if pr_data:
        pr = pr_data[0]
        related["purchase_receipt"] = pr.name
        related["pr_per_billed"] = pr.per_billed
        related["pr_is_petty_cash"] = pr.is_petty_cash
        related["pr_petty_cash_holder"] = pr.custom_petty_cash_holder_name
        related["pr_petty_cash_employee"] = pr.petty_cash_employee
        related["pr_date"] = pr.posting_date
        related["pr_accepted_warehouse"] = pr.set_warehouse
        related["pr_workflow_state"] = pr.workflow_state
        related["pr_party_name"] = pr.supplier_name
    
    # Payment Request
    prq_data = frappe.db.sql("""
        SELECT 
            name,
            transaction_date,
            payment_request_type,
            grand_total,
            workflow_state
        FROM `tabPayment Request`
        WHERE reference_name = %s
        LIMIT 1
    """, po_name, as_dict=True)
    
    if prq_data:
        prq = prq_data[0]
        related["payment_request"] = prq.name
        related["prq_transaction_date"] = prq.transaction_date
        related["prq_payment_type"] = prq.payment_request_type
        related["prq_amount"] = prq.grand_total
        related["prq_workflow_state"] = prq.workflow_state
    
    # Purchase Invoice
    pi_data = frappe.db.sql("""
        SELECT DISTINCT
            pi.name,
            pi.grand_total,
            pi.workflow_state,
            pi.posting_date,
            pi.credit_to,
            pi.supplier_warehouse
        FROM `tabPurchase Invoice` pi
        INNER JOIN `tabPurchase Invoice Item` pii ON pii.parent = pi.name
        WHERE pii.purchase_order = %s
        LIMIT 1
    """, po_name, as_dict=True)
    
    if pi_data:
        pi = pi_data[0]
        related["purchase_invoice"] = pi.name
        related["pi_grand_total"] = pi.grand_total
        related["pi_workflow_state"] = pi.workflow_state
        related["pi_date"] = pi.posting_date
        related["pi_credit_to"] = pi.credit_to
        related["pi_supplier_warehouse"] = pi.supplier_warehouse
    
    # Payment Entry
    pe_data = frappe.db.sql("""
        SELECT 
            pe.name,
            pe.posting_date,
            pe.paid_amount,
            pe.paid_amount_after_tax,
            pe.mode_of_payment,
            pe.workflow_state
        FROM `tabPayment Entry` pe
        INNER JOIN `tabPayment Entry Reference` per ON per.parent = pe.name
        WHERE per.reference_name = %s
        LIMIT 1
    """, po_name, as_dict=True)
    
    if pe_data:
        pe = pe_data[0]
        related["payment_entry"] = pe.name
        related["pe_posting_date"] = pe.posting_date
        related["pe_paid_amount"] = pe.paid_amount
        related["pe_paid_amount_after_tax"] = pe.paid_amount_after_tax
        related["pe_mode_of_payment"] = pe.mode_of_payment
        related["pe_workflow_state"] = pe.workflow_state
    
    return related

def get_material_request_details(mr_name):
    """Get Material Request details"""
    mr_data = frappe.db.sql("""
        SELECT 
            name,
            transaction_date,
            workflow_state,
            status,
            set_warehouse,
            per_ordered,
            per_received
        FROM `tabMaterial Request`
        WHERE name = %s
    """, mr_name, as_dict=True)
    
    if mr_data:
        mr = mr_data[0]
        return {
            "material_request": mr.name,
            "mr_transaction_date": mr.transaction_date,
            "mr_workflow_state": mr.workflow_state,
            "mr_status": mr.status,
            "mr_set_warehouse": mr.set_warehouse,
            "mr_per_ordered": mr.per_ordered,
            "mr_per_received": mr.per_received
        }
    return {}

def get_supplier_quotation_details(sq_name):
    """Get Supplier Quotation details"""
    sq_data = frappe.db.sql("""
        SELECT 
            name,
            supplier_name,
            transaction_date,
            total,
            total_taxes_and_charges,
            grand_total,
            status
        FROM `tabSupplier Quotation`
        WHERE name = %s
    """, sq_name, as_dict=True)
    
    if sq_data:
        sq = sq_data[0]
        return {
            "supplier_quotation": sq.name,
            "sq_supplier_name": sq.supplier_name,
            "sq_date": sq.transaction_date,
            "sq_total": sq.total,
            "sq_total_taxes_and_charges": sq.total_taxes_and_charges,
            "sq_grand_total": sq.grand_total,
            "sq_status": sq.status
        }
    return {}