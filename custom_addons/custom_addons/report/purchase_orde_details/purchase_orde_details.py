import frappe
from collections import defaultdict


def execute(filters=None):
    """Main function to generate the tree report"""
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    """Define the report columns - Including RFQ and Bid Tabulation"""
    columns = [
        # Document Reference
        {"label": "Document Type", "fieldname": "document_type", "fieldtype": "Data", "width": 150},
        {"label": "Document Name", "fieldname": "document_name", "fieldtype": "Dynamic Link", "options": "document_type", "width": 180},
        
        # Material Request Information
        {"label": "Material Request", "fieldname": "material_request", "fieldtype": "Link", "options": "Material Request", "width": 180},
        {"label": "Assigned To","fieldname": "assigned_to","fieldtype": "Data","width": 180,},
        {"label": "MR Status", "fieldname": "mr_status", "fieldtype": "Data", "width": 100},
        {"label": "MR Workflow State", "fieldname": "mr_workflow_state", "fieldtype": "Data", "width": 130},
        
        # Request for Quotation Information
        {"label": "Request for Quotation", "fieldname": "request_for_quotation", "fieldtype": "Link", "options": "Request for Quotation", "width": 180},
        {"label": "RFQ Status", "fieldname": "rfq_status", "fieldtype": "Data", "width": 100},
        {"label": "RFQ Workflow State", "fieldname": "rfq_workflow_state", "fieldtype": "Data", "width": 130},
        
        # Bid Tabulation / Supplier Quotation Information
        {"label": "Bid Tabulation", "fieldname": "bid_tabulation", "fieldtype": "Link", "options": "Bid Tabulation Discussion", "width": 180},
        {"label": "BT Status", "fieldname": "bt_status", "fieldtype": "Data", "width": 100},
        {"label": "Supplier Quotation", "fieldname": "supplier_quotation", "fieldtype": "Link", "options": "Supplier Quotation", "width": 180},
        {"label": "SQ Status", "fieldname": "sq_status", "fieldtype": "Data", "width": 100},
        
        # Purchase Order Information
        {"label": "Purchase Order", "fieldname": "purchase_order", "fieldtype": "Link", "options": "Purchase Order", "width": 180},
        {"label": "PO Status", "fieldname": "po_status", "fieldtype": "Data", "width": 100},
        {"label": "PO Workflow State", "fieldname": "po_workflow_state", "fieldtype": "Data", "width": 130},
        {"label": "PO Approval Date", "fieldname": "po_approval_date", "fieldtype": "Data", "width": 140},
        {"label": "PO Transaction Date", "fieldname": "po_transaction_date", "fieldtype": "Date", "width": 130},
        
        # Purchase Receipt
        {"label": "Purchase Receipt", "fieldname": "purchase_receipt", "fieldtype": "Link", "options": "Purchase Receipt", "width": 180},
        {"label": "PR Status", "fieldname": "pr_status", "fieldtype": "Data", "width": 100},
        {"label": "PR Workflow State", "fieldname": "pr_workflow_state", "fieldtype": "Data", "width": 130},
        
        # Purchase Invoice
        {"label": "Purchase Invoice", "fieldname": "purchase_invoice", "fieldtype": "Link", "options": "Purchase Invoice", "width": 180},
        {"label": "PI Status", "fieldname": "pi_status", "fieldtype": "Data", "width": 100},
        {"label": "PI Workflow State", "fieldname": "pi_workflow_state", "fieldtype": "Data", "width": 130},
        
        # Payment Request
        {"label": "Payment Request", "fieldname": "payment_request", "fieldtype": "Link", "options": "Payment Request", "width": 180},
        {"label": "PayReq Status", "fieldname": "payreq_status", "fieldtype": "Data", "width": 100},
        {"label": "PayReq Workflow State", "fieldname": "payreq_workflow_state", "fieldtype": "Data", "width": 130},
        
        # Payment Entry
        {"label": "Payment Entry", "fieldname": "payment_entry", "fieldtype": "Link", "options": "Payment Entry", "width": 180},
        {"label": "PE Status", "fieldname": "pe_status", "fieldtype": "Data", "width": 100},
        {"label": "PE Workflow State", "fieldname": "pe_workflow_state", "fieldtype": "Data", "width": 130},
        
        # Purchase Order Item Information
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 130},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 150},
        {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 130},
        {"label": "Quantity", "fieldname": "qty", "fieldtype": "Float", "width": 90},
        {"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 130},
        {"label": "Schedule Date", "fieldname": "schedule_date", "fieldtype": "Date", "width": 120},
        
        # Technical fields for tree structure
        {"label": "Indent", "fieldname": "indent", "fieldtype": "Int", "width": 50, "hidden": 1},
        {"label": "Parent Document", "fieldname": "parent_document", "fieldtype": "Data", "width": 180, "hidden": 1},
    ]
    
    return columns


def get_data(filters):
    """Fetches and organizes the report data in tree format using batched queries."""
    filters = filters or {}
    values = {}

    mr_purpose = filters.get("material_request_purpose", "Purchase")
    if mr_purpose:
        values["mr_purpose"] = mr_purpose

    project_is_list = isinstance(filters.get("project"), list)
    project_filter_sql = ""
    if filters.get("project"):
        if project_is_list:
            values["projects"] = tuple(filters["project"])
            project_filter_sql = " AND poi.project IN %(projects)s"
        else:
            values["project"] = filters["project"]
            project_filter_sql = " AND poi.project = %(project)s"

    date_filter_sql = ""
    if filters.get("from_date") and filters.get("to_date"):
        values["from_date"] = filters["from_date"]
        values["to_date"] = filters["to_date"]
        date_filter_sql = " AND po.transaction_date BETWEEN %(from_date)s AND %(to_date)s"

    bid_tabulation_exists = frappe.db.exists("DocType", "Bid Tabulation Discussion")
    rfq_has_workflow = frappe.db.sql(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'tabRequest for Quotation'
        AND COLUMN_NAME = 'workflow_state'
        """
    )[0][0] > 0

    parent_filter_exists_sql = ""
    if project_filter_sql or date_filter_sql:
        parent_filter_exists_sql = f"""
            AND EXISTS (
                SELECT 1
                FROM `tabMaterial Request Item` mri
                JOIN `tabPurchase Order Item` poi ON poi.material_request_item = mri.name
                JOIN `tabPurchase Order` po ON po.name = poi.parent
                WHERE mri.parent = mr.name
                {project_filter_sql}
                {date_filter_sql}
            )
        """

        # Assigned To Filter
    assigned_to = filters.get("assigned_to") or ""
    values["assigned_to"] = assigned_to

    parent_query = f"""
        SELECT
            'Material Request' AS document_type,
            mr.name AS document_name,
            mr.name AS material_request,
            mr.status AS mr_status,
            mr.workflow_state AS mr_workflow_state,
            (
                SELECT GROUP_CONCAT(td.allocated_to SEPARATOR ', ')
                FROM `tabToDo` td
                WHERE td.reference_type = 'Material Request'
                AND td.reference_name = mr.name
                AND td.status != 'Cancelled'
            ) AS assigned_to,
            0 AS indent,
            NULL AS parent_document
        FROM `tabMaterial Request` mr
        WHERE (%(mr_purpose)s = '' OR mr.material_request_type = %(mr_purpose)s)
        AND (
            %(assigned_to)s = ''
            OR EXISTS (
                SELECT 1
                FROM `tabToDo` td2
                WHERE td2.reference_type = 'Material Request'
                AND td2.reference_name = mr.name
                AND td2.status != 'Cancelled'
                AND td2.allocated_to = %(assigned_to)s
            )
        )
        {parent_filter_exists_sql}
        ORDER BY mr.creation DESC
    """

    parent_rows = frappe.db.sql(parent_query, values, as_dict=True)
    if not parent_rows:
        return []

    null_columns = [
        "request_for_quotation", "rfq_status", "rfq_workflow_state",
        "bid_tabulation", "bt_status",
        "supplier_quotation", "sq_status",
        "purchase_order", "po_status", "po_workflow_state", "po_approval_date", "po_transaction_date",
        "purchase_receipt", "pr_status", "pr_workflow_state",
        "purchase_invoice", "pi_status", "pi_workflow_state",
        "payment_request", "payreq_status", "payreq_workflow_state",
        "payment_entry", "pe_status", "pe_workflow_state",
        "item_code", "item_name", "item_group", "qty", "project", "schedule_date",
    ]

    mr_names = tuple(row["material_request"] for row in parent_rows)
    query_values = dict(values)
    query_values["mr_names"] = mr_names

    rfq_workflow_field = "rfq.workflow_state AS rfq_workflow_state," if rfq_has_workflow else "NULL AS rfq_workflow_state,"
    bt_rfq_fields = """
            bt_agg.bid_tabulation AS bid_tabulation,
            bt_agg.bt_status AS bt_status,
    """ if bid_tabulation_exists else """
            NULL AS bid_tabulation,
            NULL AS bt_status,
    """
    bt_rfq_join = """
        LEFT JOIN (
            SELECT
                bt.request_for_quotation,
                GROUP_CONCAT(DISTINCT bt.name SEPARATOR ', ') AS bid_tabulation,
                GROUP_CONCAT(DISTINCT CASE
                    WHEN bt.docstatus = 0 THEN 'Draft'
                    WHEN bt.docstatus = 1 THEN 'Submitted'
                    WHEN bt.docstatus = 2 THEN 'Cancelled'
                    ELSE 'Unknown'
                END SEPARATOR ', ') AS bt_status
            FROM `tabBid Tabulation Discussion` bt
            GROUP BY bt.request_for_quotation
        ) bt_agg ON bt_agg.request_for_quotation = rfq.name
    """ if bid_tabulation_exists else ""

    rfq_query = f"""
        SELECT
            rfqi.material_request AS material_request,
            rfq.name AS request_for_quotation,
            rfq.status AS rfq_status,
            {rfq_workflow_field}
            {bt_rfq_fields}
            sq_agg.supplier_quotation AS supplier_quotation,
            sq_agg.sq_status AS sq_status
        FROM `tabRequest for Quotation` rfq
        JOIN `tabRequest for Quotation Item` rfqi ON rfqi.parent = rfq.name
        LEFT JOIN (
            SELECT
                sqi.request_for_quotation,
                GROUP_CONCAT(DISTINCT sq.name SEPARATOR ', ') AS supplier_quotation,
                GROUP_CONCAT(DISTINCT sq.status SEPARATOR ', ') AS sq_status
            FROM `tabSupplier Quotation Item` sqi
            JOIN `tabSupplier Quotation` sq ON sq.name = sqi.parent
            WHERE IFNULL(sqi.request_for_quotation, '') != ''
            GROUP BY sqi.request_for_quotation
        ) sq_agg ON sq_agg.request_for_quotation = rfq.name
        {bt_rfq_join}
        WHERE rfqi.material_request IN %(mr_names)s
        GROUP BY rfqi.material_request, rfq.name
        ORDER BY rfq.creation
    """
    rfq_rows = frappe.db.sql(rfq_query, query_values, as_dict=True)

    po_project_filter_sql = project_filter_sql
    po_date_filter_sql = date_filter_sql
    rfq_workflow_select = "rfq_mr_agg.rfq_workflow_state AS rfq_workflow_state," if rfq_has_workflow else "NULL AS rfq_workflow_state,"
    rfq_workflow_agg = """
                GROUP_CONCAT(DISTINCT rfq.workflow_state SEPARATOR ', ') AS rfq_workflow_state
    """ if rfq_has_workflow else """
                NULL AS rfq_workflow_state
    """
    bt_po_fields = """
            po.bid_tabulation AS bid_tabulation,
            CASE
                WHEN bt.docstatus = 0 THEN 'Draft'
                WHEN bt.docstatus = 1 THEN 'Submitted'
                WHEN bt.docstatus = 2 THEN 'Cancelled'
                WHEN bt.docstatus IS NULL THEN NULL
                ELSE 'Unknown'
            END AS bt_status,
    """ if bid_tabulation_exists else """
            NULL AS bid_tabulation,
            NULL AS bt_status,
    """
    bt_po_join = "LEFT JOIN `tabBid Tabulation Discussion` bt ON bt.name = po.bid_tabulation" if bid_tabulation_exists else ""

    def wf_agg(alias, doctype):
        # workflow_state only exists when the doctype has (or had) a Workflow
        if frappe.db.has_column(doctype, "workflow_state"):
            return f"GROUP_CONCAT(DISTINCT {alias}.workflow_state SEPARATOR ', ')"
        return "NULL"

    po_query = f"""
        SELECT
            map.material_request AS material_request,
            po.name AS purchase_order,
            po.status AS po_status,
            po.workflow_state AS po_workflow_state,
            sc_agg.po_approval_date AS po_approval_date,
            po.transaction_date AS po_transaction_date,
            {bt_po_fields}
            rfq_mr_agg.request_for_quotation AS request_for_quotation,
            rfq_mr_agg.rfq_status AS rfq_status,
            {rfq_workflow_select}
            sq_mr_agg.supplier_quotation AS supplier_quotation,
            sq_mr_agg.sq_status AS sq_status,
            pr_agg.purchase_receipt AS purchase_receipt,
            pr_agg.pr_status AS pr_status,
            pr_agg.pr_workflow_state AS pr_workflow_state,
            pi_agg.purchase_invoice AS purchase_invoice,
            pi_agg.pi_status AS pi_status,
            pi_agg.pi_workflow_state AS pi_workflow_state,
            payreq_agg.payment_request AS payment_request,
            payreq_agg.payreq_status AS payreq_status,
            payreq_agg.payreq_workflow_state AS payreq_workflow_state,
            pe_agg.payment_entry AS payment_entry,
            pe_agg.pe_status AS pe_status,
            pe_agg.pe_workflow_state AS pe_workflow_state
        FROM (
            SELECT DISTINCT
                mri.parent AS material_request,
                poi.parent AS purchase_order
            FROM `tabPurchase Order Item` poi
            JOIN `tabMaterial Request Item` mri ON mri.name = poi.material_request_item
            JOIN `tabPurchase Order` po ON po.name = poi.parent
            WHERE mri.parent IN %(mr_names)s
            {po_project_filter_sql}
            {po_date_filter_sql}
        ) map
        JOIN `tabPurchase Order` po ON po.name = map.purchase_order
        LEFT JOIN (
            SELECT
                rfqi.material_request,
                GROUP_CONCAT(DISTINCT rfq.name SEPARATOR ', ') AS request_for_quotation,
                GROUP_CONCAT(DISTINCT rfq.status SEPARATOR ', ') AS rfq_status,
                {rfq_workflow_agg}
            FROM `tabRequest for Quotation Item` rfqi
            JOIN `tabRequest for Quotation` rfq ON rfq.name = rfqi.parent
            WHERE rfqi.material_request IN %(mr_names)s
            GROUP BY rfqi.material_request
        ) rfq_mr_agg ON rfq_mr_agg.material_request = map.material_request
        LEFT JOIN (
            SELECT
                sqi.material_request,
                GROUP_CONCAT(DISTINCT sq.name SEPARATOR ', ') AS supplier_quotation,
                GROUP_CONCAT(DISTINCT sq.status SEPARATOR ', ') AS sq_status
            FROM `tabSupplier Quotation Item` sqi
            JOIN `tabSupplier Quotation` sq ON sq.name = sqi.parent
            WHERE sqi.material_request IN %(mr_names)s
            GROUP BY sqi.material_request
        ) sq_mr_agg ON sq_mr_agg.material_request = map.material_request
        LEFT JOIN (
            SELECT
                poi2.parent AS purchase_order,
                GROUP_CONCAT(DISTINCT pr.name SEPARATOR ', ') AS purchase_receipt,
                GROUP_CONCAT(DISTINCT pr.status SEPARATOR ', ') AS pr_status,
                {wf_agg('pr', 'Purchase Receipt')} AS pr_workflow_state
            FROM `tabPurchase Receipt Item` pri
            JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
            JOIN `tabPurchase Order Item` poi2 ON poi2.name = pri.purchase_order_item
            GROUP BY poi2.parent
        ) pr_agg ON pr_agg.purchase_order = po.name
        LEFT JOIN (
            SELECT
                pii.purchase_order,
                GROUP_CONCAT(DISTINCT pi.name SEPARATOR ', ') AS purchase_invoice,
                GROUP_CONCAT(DISTINCT pi.status SEPARATOR ', ') AS pi_status,
                {wf_agg('pi', 'Purchase Invoice')} AS pi_workflow_state
            FROM `tabPurchase Invoice Item` pii
            JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
            GROUP BY pii.purchase_order
        ) pi_agg ON pi_agg.purchase_order = po.name
        LEFT JOIN (
            SELECT
                pr.reference_name AS purchase_order,
                GROUP_CONCAT(DISTINCT pr.name SEPARATOR ', ') AS payment_request,
                GROUP_CONCAT(DISTINCT pr.status SEPARATOR ', ') AS payreq_status,
                {wf_agg('pr', 'Payment Request')} AS payreq_workflow_state
            FROM `tabPayment Request` pr
            GROUP BY pr.reference_name
        ) payreq_agg ON payreq_agg.purchase_order = po.name
        LEFT JOIN (
            SELECT
                per.reference_name AS purchase_order,
                GROUP_CONCAT(DISTINCT pe.name SEPARATOR ', ') AS payment_entry,
                GROUP_CONCAT(DISTINCT pe.status SEPARATOR ', ') AS pe_status,
                {wf_agg('pe', 'Payment Entry')} AS pe_workflow_state
            FROM `tabPayment Entry Reference` per
            JOIN `tabPayment Entry` pe ON pe.name = per.parent
            GROUP BY per.reference_name
        ) pe_agg ON pe_agg.purchase_order = po.name
        LEFT JOIN (
            SELECT
                sc.parent AS purchase_order,
                DATE_FORMAT(MIN(sc.modification_time), '%%d-%%m-%%Y %%H:%%i:%%s') AS po_approval_date
            FROM `tabState Change Items` sc
            WHERE sc.docstatus = 1
            AND sc.workflow_state = 'Approved'
            GROUP BY sc.parent
        ) sc_agg ON sc_agg.purchase_order = po.name
        {bt_po_join}
        ORDER BY po.creation
    """
    po_rows = frappe.db.sql(po_query, query_values, as_dict=True)

    po_names = tuple(sorted({row["purchase_order"] for row in po_rows if row.get("purchase_order")}))
    po_items = []
    if po_names:
        po_items = frappe.db.sql(
            """
            SELECT
                poi.parent AS purchase_order,
                poi.name AS document_name,
                poi.item_code,
                poi.item_name,
                i.item_group,
                poi.qty,
                IFNULL(CAST(poi.project AS CHAR), '') AS project,
                poi.schedule_date
            FROM `tabPurchase Order Item` poi
            LEFT JOIN `tabItem` i ON i.name = poi.item_code
            WHERE poi.parent IN %(po_names)s
            ORDER BY poi.parent, poi.idx
            """,
            {"po_names": po_names},
            as_dict=True,
        )

    rfq_by_mr = defaultdict(list)
    for rfq_row in rfq_rows:
        rfq_by_mr[rfq_row["material_request"]].append(rfq_row)

    po_by_mr = defaultdict(list)
    for po_row in po_rows:
        po_by_mr[po_row["material_request"]].append(po_row)

    po_items_by_po = defaultdict(list)
    for item in po_items:
        po_items_by_po[item["purchase_order"]].append(item)

    data = []

    for mr_row in parent_rows:
        for col in null_columns:
            mr_row[col] = None
        data.append(mr_row)

        for rfq_row in rfq_by_mr.get(mr_row["material_request"], []):
            row = {
                "document_type": "Request for Quotation",
                "document_name": rfq_row["request_for_quotation"],
                "material_request": mr_row["material_request"],
                "mr_status": mr_row["mr_status"],
                "mr_workflow_state": mr_row["mr_workflow_state"],
                "request_for_quotation": rfq_row["request_for_quotation"],
                "rfq_status": rfq_row["rfq_status"],
                "rfq_workflow_state": rfq_row["rfq_workflow_state"],
                "bid_tabulation": rfq_row["bid_tabulation"],
                "bt_status": rfq_row["bt_status"],
                "supplier_quotation": rfq_row["supplier_quotation"],
                "sq_status": rfq_row["sq_status"],
                "indent": 1,
                "parent_document": mr_row["material_request"],
            }
            for col in [
                "purchase_order", "po_status", "po_workflow_state", "po_approval_date", "po_transaction_date",
                "purchase_receipt", "pr_status", "pr_workflow_state",
                "purchase_invoice", "pi_status", "pi_workflow_state",
                "payment_request", "payreq_status", "payreq_workflow_state",
                "payment_entry", "pe_status", "pe_workflow_state",
                "item_code", "item_name", "item_group", "qty", "project", "schedule_date",
            ]:
                row[col] = None
            data.append(row)

        for po_row in po_by_mr.get(mr_row["material_request"], []):
            po_out = {
                "document_type": "Purchase Order",
                "document_name": po_row["purchase_order"],
                "material_request": mr_row["material_request"],
                "mr_status": mr_row["mr_status"],
                "mr_workflow_state": mr_row["mr_workflow_state"],
                "request_for_quotation": po_row["request_for_quotation"],
                "rfq_status": po_row["rfq_status"],
                "rfq_workflow_state": po_row["rfq_workflow_state"],
                "bid_tabulation": po_row["bid_tabulation"],
                "bt_status": po_row["bt_status"],
                "supplier_quotation": po_row["supplier_quotation"],
                "sq_status": po_row["sq_status"],
                "purchase_order": po_row["purchase_order"],
                "po_status": po_row["po_status"],
                "po_workflow_state": po_row["po_workflow_state"],
                "po_approval_date": po_row["po_approval_date"],
                "po_transaction_date": po_row["po_transaction_date"],
                "purchase_receipt": po_row["purchase_receipt"],
                "pr_status": po_row["pr_status"],
                "pr_workflow_state": po_row["pr_workflow_state"],
                "purchase_invoice": po_row["purchase_invoice"],
                "pi_status": po_row["pi_status"],
                "pi_workflow_state": po_row["pi_workflow_state"],
                "payment_request": po_row["payment_request"],
                "payreq_status": po_row["payreq_status"],
                "payreq_workflow_state": po_row["payreq_workflow_state"],
                "payment_entry": po_row["payment_entry"],
                "pe_status": po_row["pe_status"],
                "pe_workflow_state": po_row["pe_workflow_state"],
                "item_code": None,
                "item_name": None,
                "item_group": None,
                "qty": None,
                "project": None,
                "schedule_date": None,
                "indent": 1,
                "parent_document": mr_row["material_request"],
            }
            data.append(po_out)

            for item in po_items_by_po.get(po_row["purchase_order"], []):
                data.append(
                    {
                        "document_type": "Purchase Order Item",
                        "document_name": item["document_name"],
                        "material_request": mr_row["material_request"],
                        "mr_status": mr_row["mr_status"],
                        "mr_workflow_state": mr_row["mr_workflow_state"],
                        "request_for_quotation": po_row["request_for_quotation"],
                        "rfq_status": po_row["rfq_status"],
                        "rfq_workflow_state": po_row["rfq_workflow_state"],
                        "bid_tabulation": po_row["bid_tabulation"],
                        "bt_status": po_row["bt_status"],
                        "supplier_quotation": po_row["supplier_quotation"],
                        "sq_status": po_row["sq_status"],
                        "purchase_order": po_row["purchase_order"],
                        "po_status": po_row["po_status"],
                        "po_workflow_state": po_row["po_workflow_state"],
                        "po_approval_date": po_row["po_approval_date"],
                        "po_transaction_date": po_row["po_transaction_date"],
                        "purchase_receipt": po_row["purchase_receipt"],
                        "pr_status": po_row["pr_status"],
                        "pr_workflow_state": po_row["pr_workflow_state"],
                        "purchase_invoice": po_row["purchase_invoice"],
                        "pi_status": po_row["pi_status"],
                        "pi_workflow_state": po_row["pi_workflow_state"],
                        "payment_request": po_row["payment_request"],
                        "payreq_status": po_row["payreq_status"],
                        "payreq_workflow_state": po_row["payreq_workflow_state"],
                        "payment_entry": po_row["payment_entry"],
                        "pe_status": po_row["pe_status"],
                        "pe_workflow_state": po_row["pe_workflow_state"],
                        "item_code": item["item_code"],
                        "item_name": item["item_name"],
                        "item_group": item["item_group"],
                        "qty": item["qty"],
                        "project": item["project"],
                        "schedule_date": item["schedule_date"],
                        "indent": 2,
                        "parent_document": po_row["purchase_order"],
                    }
                )

    return data
