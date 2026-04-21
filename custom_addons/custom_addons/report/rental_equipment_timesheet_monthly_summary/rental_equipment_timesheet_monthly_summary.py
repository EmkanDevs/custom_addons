# Copyright (c) 2024, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": _("Project"),
            "fieldname": "project",
            "fieldtype": "Link",
            "options": "Project",
            "width": 130,
        },
        {
            "label": _("Project Name"),
            "fieldname": "project_name",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": _("Supplier"),
            "fieldname": "supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 130,
        },
        {
            "label": _("Supplier Name"),
            "fieldname": "supplier_name",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": _("Door No or Plate No"),
            "fieldname": "door_no_or_plate_no",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Equipment Name"),
            "fieldname": "equipment_name",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": _("Status"),
            "fieldname": "timesheet_status",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Total Hours"),
            "fieldname": "total_hours",
            "fieldtype": "Float",
            "precision": 2,
            "width": 120,
        },
        {
            "label": _("Rate"),
            "fieldname": "rate",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Total Amount"),
            "fieldname": "total_amount",
            "fieldtype": "Currency",
            "width": 150,
        },
    ]


def get_filters_conditions(filters):
    """Build WHERE conditions and values dict from report filters."""
    conditions = []
    values = {}

    if filters.get("project"):
        conditions.append("ret.project_id = %(project)s")
        values["project"] = filters["project"]

    if filters.get("supplier"):
        conditions.append("ret.supplier_name = %(supplier)s")
        values["supplier"] = filters["supplier"]

    if filters.get("door_no_or_plate_no"):
        conditions.append("ret.door_no_or_plate_no = %(door_no_or_plate_no)s")
        values["door_no_or_plate_no"] = filters["door_no_or_plate_no"]

    if filters.get("from_date"):
        conditions.append("ret.date >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("ret.date <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "AND " + where_clause

    return where_clause, values


def get_data(filters):
    where_clause, values = get_filters_conditions(filters)

    # -----------------------------------------------------------------
    # Step 1 – Aggregate Rental Equipment Timesheet records
    # Group by (project, supplier, door/plate, equipment) so every row
    # represents one equipment per supplier per project for the period.
    # -----------------------------------------------------------------
    timesheet_rows = frappe.db.sql(
        f"""
        SELECT
            ret.project_id                          AS project,
            COALESCE(p.project_name, ret.project_id) AS project_name,
            ret.supplier_name                       AS supplier,
            COALESCE(s.supplier_name, ret.supplier_name) AS supplier_name,
            ret.door_no_or_plate_no,
            ret.equipment_name,
            COALESCE(eam.item, '')                  AS item_code,
            CASE ret.docstatus
                WHEN 0 THEN 'Draft'
                WHEN 1 THEN 'Submitted'
                WHEN 2 THEN 'Cancelled'
                ELSE 'Unknown'
            END                                     AS timesheet_status,
            SUM(ret.hours)                          AS total_hours
        FROM
            `tabRental Equipment Timesheet` ret
            LEFT JOIN `tabProject` p
                ON p.name = ret.project_id
            LEFT JOIN `tabSupplier` s
                ON s.name = ret.supplier_name
            LEFT JOIN `tabEquipment Asset Management` eam
                ON eam.name = ret.door_no_or_plate_no
        WHERE
            ret.docstatus < 2
            {where_clause}
        GROUP BY
            ret.project_id,
            ret.supplier_name,
            ret.door_no_or_plate_no,
            ret.equipment_name,
            eam.item,
            ret.docstatus
        ORDER BY
            ret.project_id,
            ret.supplier_name,
            ret.equipment_name
        """,
        values,
        as_dict=True,
    )

    if not timesheet_rows:
        return []

    # -----------------------------------------------------------------
    # Step 2 – For each equipment group, get the item code from
    # Equipment Asset Management (via door_no_or_plate_no), then fetch
    # all Blanket Order rates for that supplier + item.
    # Average the rates if multiple Blanket Orders exist, then:
    #   Total Amount = avg_rate × total_hours
    # -----------------------------------------------------------------
    data = []

    for row in timesheet_rows:
        bo_rates = get_blanket_order_rates(item_code=row.item_code)

        avg_rate = sum(bo_rates) / len(bo_rates) if bo_rates else 0.0
        total_amount = flt(avg_rate) * flt(row.total_hours)

        data.append(
            {
                "project": row.project,
                "project_name": row.project_name,
                "supplier": row.supplier,
                "supplier_name": row.supplier_name,
                "door_no_or_plate_no": row.door_no_or_plate_no,
                "equipment_name": row.equipment_name,
                "timesheet_status": row.timesheet_status,
                "total_hours": flt(row.total_hours, 2),
                "rate": flt(avg_rate, 2),
                "total_amount": flt(total_amount, 2),
            }
        )

    return data


def get_blanket_order_rates(item_code):
    """
    Return all rates from submitted Blanket Orders for the given item_code.
    If multiple Blanket Orders exist, all rates are returned so the caller
    can average them.
    """
    if not item_code:
        return []

    try:
        rates = frappe.db.sql(
            """
            SELECT
                boi.rate
            FROM
                `tabBlanket Order Item` boi
                INNER JOIN `tabBlanket Order` bo
                    ON bo.name = boi.parent
            WHERE
                bo.docstatus = 1
                AND boi.item_code = %(item_code)s
            """,
            {
                "item_code": item_code,
            },
            as_list=True,
        )
        return [r[0] for r in rates if r[0]]
    except Exception:
        return []