# Copyright (c) 2026, Finbyz and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    filters = filters or {}

    columns = [
        {
            "label": "Purchase Order",
            "fieldname": "purchase_order",
            "fieldtype": "Link",
            "options": "Purchase Order",
            "width": 150,
        },
        {
            "label": "PO Date",
            "fieldname": "po_date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": "Supplier Code",
            "fieldname": "supplier_code",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 150,
        },
        {
            "label": "Supplier Name",
            "fieldname": "supplier_name",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": "Project Code",
            "fieldname": "project_code",
            "fieldtype": "Link",
            "options": "Project",
            "width": 150,
        },
        {
            "label": "Purchase Order Amount",
            "fieldname": "purchase_order_amount",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": "Purchase Order Status",
            "fieldname": "purchase_order_status",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": "Purchase Receipt",
            "fieldname": "purchase_receipt",
            "fieldtype": "Link",
            "options": "Purchase Receipt",
            "width": 150,
        },
        {
            "label": "PR Date",
            "fieldname": "pr_date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": "Purchase Receipt Amount",
            "fieldname": "purchase_receipt_amount",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": "Purchase Receipt Status",
            "fieldname": "purchase_receipt_status",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": "No. of Invoices",
            "fieldname": "no_of_invoices",
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "label": "Purchase Invoices Amount",
            "fieldname": "purchase_invoices_amount",
            "fieldtype": "Currency",
            "width": 160,
        },
        {
            "label": "Pending Amount",
            "fieldname": "pending_amount",
            "fieldtype": "Currency",
            "width": 140,
        },
    ]

    conditions = [
        "po.docstatus = 1",
        "po.transaction_date BETWEEN %(from_date)s AND %(to_date)s",
    ]

    if filters.get("purchase_order"):
        conditions.append("po.name = %(purchase_order)s")

    if filters.get("purchase_receipt"):
        conditions.append("pr.name = %(purchase_receipt)s")

    if filters.get("purchase_invoice"):
        conditions.append("pi.name = %(purchase_invoice)s")

    if filters.get("supplier"):
        conditions.append("po.supplier = %(supplier)s")

    if filters.get("project"):
        conditions.append("po.project = %(project)s")

    query = f"""
        SELECT
            po.name AS purchase_order,
            po.transaction_date AS po_date,
            po.supplier AS supplier_code,
            po.supplier_name AS supplier_name,
            po.project AS project_code,
            po.total AS purchase_order_amount,
            po.status AS purchase_order_status,

            GROUP_CONCAT(DISTINCT pr.name) AS purchase_receipt,
            MIN(pr.posting_date) AS pr_date,
            COALESCE(SUM(DISTINCT pr.total), 0) AS purchase_receipt_amount,

            GROUP_CONCAT(DISTINCT pr.status) AS purchase_receipt_status,

            COUNT(DISTINCT pi.name) AS no_of_invoices,
            COALESCE(SUM(DISTINCT pi.total), 0) AS purchase_invoices_amount,

            po.total - COALESCE(SUM(DISTINCT pi.total), 0)
                AS pending_amount

        FROM `tabPurchase Order` po

        LEFT JOIN `tabPurchase Receipt Item` pri
            ON pri.purchase_order = po.name

        LEFT JOIN `tabPurchase Receipt` pr
            ON pr.name = pri.parent
            AND pr.docstatus = 1

        LEFT JOIN `tabPurchase Invoice Item` pii
            ON pii.purchase_order = po.name

        LEFT JOIN `tabPurchase Invoice` pi
            ON pi.name = pii.parent
            AND pi.docstatus = 1

        WHERE {" AND ".join(conditions)}

        GROUP BY po.name

        ORDER BY po.transaction_date DESC
    """

    data = frappe.db.sql(
        query,
        {
            "from_date": filters.get("from_date"),
            "to_date": filters.get("to_date"),
            "purchase_order": filters.get("purchase_order"),
            "purchase_receipt": filters.get("purchase_receipt"),
            "purchase_invoice": filters.get("purchase_invoice"),
            "supplier": filters.get("supplier"),
            "project": filters.get("project"),
        },
        as_dict=True,
    )

    return columns, data