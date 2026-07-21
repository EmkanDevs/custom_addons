# Copyright (c) 2026, Finbyz and contributors
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
            "label": "Issue Stock Entry",
            "fieldname": "issue_stock_entry",
            "fieldtype": "Link",
            "options": "Stock Entry",
            "width": 180,
        },
        {
            "label": "Issue SE Date",
            "fieldname": "issue_posting_date",
            "fieldtype": "Date",
            "width": 120,
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
            "width": 200,
        },
        {
            "label": "Project",
            "fieldname": "project",
            "fieldtype": "Link",
            "options": "Project",
            "width": 150,
        },
        {
            "label": "Item Code",
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 150,
        },
        {
            "label": "Item Name",
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": "Issued Qty",
            "fieldname": "issued_qty",
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "label": "Return Request",
            "fieldname": "return_request",
            "fieldtype": "Link",
            "options": "Returned Material to Warehouse Request",
            "width": 180,
        },
        {
            "label": "Return Request Date",
            "fieldname": "return_request_date",
            "fieldtype": "Date",
            "width": 130,
        },
        {
            "label": "Reason of Return",
            "fieldname": "reason_of_return",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": "Target Warehouse",
            "fieldname": "default_target_warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 200,
        },
        {
            "label": "Returned Qty",
            "fieldname": "returned_qty",
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "label": "Return Stock Entry",
            "fieldname": "return_stock_entry",
            "fieldtype": "Link",
            "options": "Stock Entry",
            "width": 180,
        },
        {
            "label": "Receipt Date",
            "fieldname": "receipt_posting_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": "Receipt Reason",
            "fieldname": "receipt_reason_of_return",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": "Return Condition",
            "fieldname": "return_condition",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": "Balance Qty",
            "fieldname": "balance_qty",
            "fieldtype": "Float",
            "width": 120,
        },
    ]


def get_data(filters):
    conditions = ["rmwr.docstatus = 1"]
    values = {}

    if filters.get("project"):
        conditions.append("rmwr.project = %(project)s")
        values["project"] = filters.get("project")

    if filters.get("supplier"):
        conditions.append("se.custom_supplier_code = %(supplier)s")
        values["supplier"] = filters.get("supplier")

    if filters.get("item_code"):
        conditions.append("rmwri.item_code = %(item_code)s")
        values["item_code"] = filters.get("item_code")

    if filters.get("issue_stock_entry"):
        conditions.append("se.name = %(issue_stock_entry)s")
        values["issue_stock_entry"] = filters.get("issue_stock_entry")

    if filters.get("return_request"):
        conditions.append("rmwr.name = %(return_request)s")
        values["return_request"] = filters.get("return_request")

    if filters.get("return_stock_entry"):
        conditions.append("rse.name = %(return_stock_entry)s")
        values["return_stock_entry"] = filters.get("return_stock_entry")

    if filters.get("target_warehouse"):
        conditions.append(
            "rmwr.default_target_warehouse = %(target_warehouse)s"
        )
        values["target_warehouse"] = filters.get("target_warehouse")

    if filters.get("reason_of_return"):
        conditions.append(
            "rmwr.reason_of_return = %(reason_of_return)s"
        )
        values["reason_of_return"] = filters.get("reason_of_return")

    if filters.get("from_date"):
        conditions.append("rmwr.date >= %(from_date)s")
        values["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        conditions.append("rmwr.date <= %(to_date)s")
        values["to_date"] = filters.get("to_date")

    where_clause = " AND ".join(conditions)

    data = frappe.db.sql(
        f"""
        SELECT
            se.name AS issue_stock_entry,
            se.posting_date AS issue_posting_date,
            se.custom_supplier_code_ AS supplier_code,
            se.custom_suppliers_name_ AS supplier_name,

            rmwr.project,

            rmwri.item_code,
            rmwri.item_name,

            IFNULL((
                SELECT SUM(sed.qty)
                FROM `tabStock Entry Detail` sed
                WHERE sed.parent = se.name
                AND sed.item_code = rmwri.item_code
            ), 0) AS issued_qty,

            rmwr.name AS return_request,
            rmwr.date AS return_request_date,
            rmwr.reason_of_return,
            rmwr.default_target_warehouse,

            rmwri.quantity AS returned_qty,

            rse.name AS return_stock_entry,
            rse.posting_date AS receipt_posting_date,
            rse.custom_reason_of_return AS receipt_reason_of_return,
            rse.custom_return_condition AS return_condition,

            (
                IFNULL((
                    SELECT SUM(sed.qty)
                    FROM `tabStock Entry Detail` sed
                    WHERE sed.parent = se.name
                    AND sed.item_code = rmwri.item_code
                ), 0)
                - IFNULL(rmwri.quantity, 0)
            ) AS balance_qty

        FROM `tabReturned Material to Warehouse Request` rmwr

        INNER JOIN `tabReturned Material to Warehouse Items` rmwri
            ON rmwri.parent = rmwr.name

        LEFT JOIN `tabStock Entry` se
            ON se.name = rmwr.stock_entry_reference

        LEFT JOIN `tabStock Entry` rse
            ON rse.custom_return_material_ref_doc = rmwr.name

        WHERE {where_clause}

        ORDER BY rmwr.date DESC, rmwr.creation DESC
        """,
        values,
        as_dict=True,
    )
    return data