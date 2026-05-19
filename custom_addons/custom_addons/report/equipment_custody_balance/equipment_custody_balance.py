import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": _("Employee Number"),
            "fieldname": "custody_holder_id",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150
        },
        {
            "label": _("Employee Full Name"),
            "fieldname": "custody_holder_name",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("Department"),
            "fieldname": "department",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Designation"),
            "fieldname": "designation",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Project"),
            "fieldname": "project",
            "fieldtype": "Link",
            "options": "Project",
            "width": 140
        },
        {
            "label": _("Item Code"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 140
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("Item Group"),
            "fieldname": "item_group",
            "fieldtype": "Data",
            "width": 140
        },
        {
            "label": _("Stock / Asset"),
            "fieldname": "stock_asset",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Tag Number"),
            "fieldname": "tag_number",
            "fieldtype": "Data",
            "width": 140
        },
        {
            "label": _("Balance Qty"),
            "fieldname": "balance_qty",
            "fieldtype": "Float",
            "width": 120
        }
    ]


def get_data(filters):

    conditions = ""

    if filters.get("custody_holder_id"):
        conditions += " AND elr.custody_holder_id = %(custody_holder_id)s"

    if filters.get("project"):
        conditions += " AND eli.project = %(project)s"

    if filters.get("transaction_type"):
        conditions += " AND elr.transaction_type = %(transaction_type)s"

    # ✅ Use COALESCE so whichever date field is filled gets checked
    date_conditions = ""
    if filters.get("from_date"):
        date_conditions += """
            AND COALESCE(elr.receiving_date, elr.return_date) >= %(from_date)s
        """

    if filters.get("to_date"):
        date_conditions += """
            AND COALESCE(elr.receiving_date, elr.return_date) <= %(to_date)s
        """

    records = frappe.db.sql(f"""
        SELECT
            elr.custody_holder_id,
            elr.custody_holder_name,
            emp.department,
            emp.designation,
            eli.project,
            eli.item_code,
            eli.item_name,
            eli.item_group,
            eli.fixed_asset,
            eli.tag_number,
            eli.quantity,
            elr.transaction_type

        FROM `tabEquipment Log Register` elr

        INNER JOIN `tabEquipment Log Item` eli
            ON eli.parent = elr.name

        LEFT JOIN `tabEmployee` emp
            ON emp.name = elr.custody_holder_id

        WHERE elr.docstatus = 1

        {conditions}
        {date_conditions}

        ORDER BY elr.custody_holder_id, eli.item_code, eli.tag_number

    """, filters, as_dict=1)

    balance_map = {}

    for row in records:

        if row.fixed_asset:
            # Each unique tag = separate physical asset
            key = (
                row.custody_holder_id,
                row.project,
                row.item_code,
                row.tag_number
            )

            if key not in balance_map:
                balance_map[key] = {
                    "custody_holder_id": row.custody_holder_id,
                    "custody_holder_name": row.custody_holder_name,
                    "department": row.department,
                    "designation": row.designation,
                    "project": row.project,
                    "item_code": row.item_code,
                    "item_name": row.item_name,
                    "item_group": row.item_group,
                    "stock_asset": "Asset",
                    "tag_number": row.tag_number,
                    "balance_qty": 0
                }

            if row.transaction_type == "Issue / Receiving":
                balance_map[key]["balance_qty"] += 1
            elif row.transaction_type == "Return":
                balance_map[key]["balance_qty"] -= 1

        else:
            # Stock: sum quantities
            key = (
                row.custody_holder_id,
                row.project,
                row.item_code
            )

            if key not in balance_map:
                balance_map[key] = {
                    "custody_holder_id": row.custody_holder_id,
                    "custody_holder_name": row.custody_holder_name,
                    "department": row.department,
                    "designation": row.designation,
                    "project": row.project,
                    "item_code": row.item_code,
                    "item_name": row.item_name,
                    "item_group": row.item_group,
                    "stock_asset": "Stock",
                    "tag_number": "",
                    "balance_qty": 0
                }

            if row.transaction_type == "Issue / Receiving":
                balance_map[key]["balance_qty"] += (row.quantity or 0)
            elif row.transaction_type == "Return":
                balance_map[key]["balance_qty"] -= (row.quantity or 0)

    final_data = []

    for value in balance_map.values():

        # Show only items currently with employee
        if filters.get("with_employee"):

            if value["balance_qty"] > 0:
                final_data.append(value)

        # Show all balances
        else:
            final_data.append(value)

    return final_data