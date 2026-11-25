import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        # ---- Material Request ----
        {
            "label": _("Material Request"),
            "fieldname": "mr_name",
            "fieldtype": "Link",
            "options": "Material Request",
            "width": 160,
        },
        {
            "label": _("Assigned To"),
            "fieldname": "assigned_to_names",
            "fieldtype": "Data",
            "width": 240,
        },
        {
            "label": _("Transaction Date"),
            "fieldname": "transaction_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": _("Required By"),
            "fieldname": "required_by",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": _("Set Warehouse"),
            "fieldname": "set_warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 160,
        },
        {
            "label": _("MR Workflow State"),
            "fieldname": "mr_workflow_state",
            "fieldtype": "Data",
            "width": 140,
        },

        # ---- Purchase Order ----
        {
            "label": _("Purchase Order"),
            "fieldname": "po_name",
            "fieldtype": "Link",
            "options": "Purchase Order",
            "width": 160,
        },
        {
            "label": _("PO Date"),
            "fieldname": "po_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": _("Project"),
            "fieldname": "project",
            "fieldtype": "Link",
            "options": "Project",
            "width": 140,
        },
        {
            "label": _("Project Name"),
            "fieldname": "project_name",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _("Supplier Code"),
            "fieldname": "supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 140,
        },
        {
            "label": _("Supplier Name"),
            "fieldname": "supplier_name",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": _("PO Workflow State"),
            "fieldname": "po_workflow_state",
            "fieldtype": "Data",
            "width": 140,
        },
    ]


def get_data(filters):
    conditions = []
    values = {}

    if filters.get("due_po"):
        conditions.append("""
            NOT EXISTS (
                SELECT 1
                FROM `tabPurchase Order Item` poi
                INNER JOIN `tabPurchase Order` po
                    ON po.name = poi.parent
                    AND po.docstatus = 1
                WHERE poi.material_request = mr.name
            )
        """)

    if filters.get("material_request"):
        conditions.append("mr.name = %(material_request)s")
        values["material_request"] = filters["material_request"]

    if filters.get("project"):
        conditions.append("""
            EXISTS (
                SELECT 1
                FROM `tabPurchase Order Item` poi
                INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
                WHERE poi.material_request = mr.name
                  AND po.project = %(project)s
            )
        """)
        values["project"] = filters["project"]

    if filters.get("purpose"):
        conditions.append("mr.material_request_type = %(purpose)s")
        values["purpose"] = filters["purpose"]

    if filters.get("from_date"):
        conditions.append("mr.transaction_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("mr.transaction_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    # ✅ CORRECT Assigned To filter (allocated_to)
    if filters.get("assigned_to"):
        conditions.append("""
            EXISTS (
                SELECT 1
                FROM `tabToDo` td
                WHERE td.reference_type = 'Material Request'
                  AND td.reference_name = mr.name
                  AND td.allocated_to = %(assigned_to)s
            )
        """)
        values["assigned_to"] = filters["assigned_to"]

    condition_str = " AND ".join(conditions)

    return frappe.db.sql(f"""
        SELECT
            mr.name AS mr_name,

            -- ✅ ACTUAL assigned users (not assigner)
            (
                SELECT GROUP_CONCAT(
                    DISTINCT u.full_name
                    ORDER BY u.full_name
                    SEPARATOR ', '
                )
                FROM `tabToDo` td
                INNER JOIN `tabUser` u
                    ON u.name = td.allocated_to
                WHERE td.reference_type = 'Material Request'
                  AND td.reference_name = mr.name
            ) AS assigned_to_names,

            mr.transaction_date,
            mr.schedule_date AS required_by,
            mr.set_warehouse,
            mr.workflow_state AS mr_workflow_state,

            -- Latest Purchase Order
            (
                SELECT po.name
                FROM `tabPurchase Order Item` poi
                INNER JOIN `tabPurchase Order` po
                    ON po.name = poi.parent
                    AND po.docstatus != 2
                WHERE poi.material_request = mr.name
                ORDER BY po.transaction_date DESC
                LIMIT 1
            ) AS po_name,

            (
                SELECT po.transaction_date
                FROM `tabPurchase Order Item` poi
                INNER JOIN `tabPurchase Order` po
                    ON po.name = poi.parent
                    AND po.docstatus != 2
                WHERE poi.material_request = mr.name
                ORDER BY po.transaction_date DESC
                LIMIT 1
            ) AS po_date,

            (
                SELECT po.project
                FROM `tabPurchase Order Item` poi
                INNER JOIN `tabPurchase Order` po
                    ON po.name = poi.parent
                    AND po.docstatus != 2
                WHERE poi.material_request = mr.name
                ORDER BY po.transaction_date DESC
                LIMIT 1
            ) AS project,

            (
                SELECT pr.project_name
                FROM `tabPurchase Order Item` poi
                INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
                INNER JOIN `tabProject` pr ON pr.name = po.project
                WHERE poi.material_request = mr.name
                ORDER BY po.transaction_date DESC
                LIMIT 1
            ) AS project_name,

            (
                SELECT po.supplier
                FROM `tabPurchase Order Item` poi
                INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
                WHERE poi.material_request = mr.name
                ORDER BY po.transaction_date DESC
                LIMIT 1
            ) AS supplier,

            (
                SELECT po.supplier_name
                FROM `tabPurchase Order Item` poi
                INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
                WHERE poi.material_request = mr.name
                ORDER BY po.transaction_date DESC
                LIMIT 1
            ) AS supplier_name,

            (
                SELECT po.workflow_state
                FROM `tabPurchase Order Item` poi
                INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
                WHERE poi.material_request = mr.name
                ORDER BY po.transaction_date DESC
                LIMIT 1
            ) AS po_workflow_state

        FROM `tabMaterial Request` mr

        WHERE
            mr.docstatus = 1
            {f"AND {condition_str}" if condition_str else ""}

        ORDER BY mr.transaction_date DESC
    """, values, as_dict=True)
