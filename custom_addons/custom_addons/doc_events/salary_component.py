# File: custom_addons/custom_addons/doc_events/salary_component.py
#
# Doc event for Salary Component.
# On validate: if the type changed, moves component rows between
# earnings/deductions in every Draft Salary Slip using raw SQL.

import frappe
from frappe.utils import flt


def validate(doc, method=None):
    """
    Fires on every Salary Component save (before DB write).
    Checks if the Type field changed. If yes, moves the component
    row from the old child table to the new one in all Draft Salary Slips.
    """
    # Fetch the currently saved type from DB (before this save)
    saved_type = frappe.db.get_value("Salary Component", doc.name, "type")

    # New doc or type unchanged — nothing to do
    if not saved_type or saved_type == doc.type:
        return

    old_type  = saved_type
    new_type  = doc.type
    old_table = "earnings"   if old_type == "Earning" else "deductions"
    new_table = "earnings"   if new_type == "Earning" else "deductions"

    _move_component_in_draft_slips(doc.name, old_table, new_table)


# ═════════════════════════════════════════════════════════════════════════════
def _move_component_in_draft_slips(component_name, old_table, new_table):
    """
    Moves a salary component row from old_table → new_table
    in every Draft Salary Slip (docstatus = 0) using raw SQL.

    Steps:
        1. Find all Draft Salary Slip names that have this component
           in the OLD table.
        2. Update the parentfield of those rows to the NEW table.
        3. Recalculate gross_pay, total_deduction, net_pay for each slip.
    """

    # ── Step 1: Find affected Draft Salary Slips ──────────────────────────
    affected = frappe.db.sql("""
        SELECT
            sd.name      AS detail_name,
            sd.parent    AS slip_name,
            sd.amount    AS amount
        FROM
            `tabSalary Detail` sd
        INNER JOIN
            `tabSalary Slip` ss ON ss.name = sd.parent
        WHERE
            sd.salary_component = %(component)s
            AND sd.parenttype   = 'Salary Slip'
            AND sd.parentfield  = %(old_table)s
            AND ss.docstatus    = 0
    """, {
        "component" : component_name,
        "old_table" : old_table,
    }, as_dict=True)

    if not affected:
        frappe.msgprint(
            f"No Draft Salary Slips found with <b>{component_name}</b> "
            f"in the <b>{old_table}</b> table. Nothing updated.",
            indicator="blue",
            alert=True,
        )
        return

    slip_names = list({r.slip_name for r in affected})

    # ── Step 2: Move rows — update parentfield in one SQL call ────────────
    frappe.db.sql("""
        UPDATE `tabSalary Detail`
        SET    parentfield = %(new_table)s
        WHERE
            salary_component = %(component)s
            AND parenttype   = 'Salary Slip'
            AND parentfield  = %(old_table)s
            AND parent IN %(slips)s
    """, {
        "new_table" : new_table,
        "component" : component_name,
        "old_table" : old_table,
        "slips"     : slip_names,
    })

    # ── Step 3: Recalculate totals for every affected slip ────────────────
    for slip_name in slip_names:

        # Sum all earnings for this slip
        gross_pay = frappe.db.sql("""
            SELECT COALESCE(SUM(amount), 0)
            FROM   `tabSalary Detail`
            WHERE  parent     = %(slip)s
            AND    parenttype = 'Salary Slip'
            AND    parentfield = 'earnings'
        """, {"slip": slip_name})[0][0]

        # Sum all deductions for this slip
        total_deduction = frappe.db.sql("""
            SELECT COALESCE(SUM(amount), 0)
            FROM   `tabSalary Detail`
            WHERE  parent      = %(slip)s
            AND    parenttype  = 'Salary Slip'
            AND    parentfield = 'deductions'
        """, {"slip": slip_name})[0][0]

        net_pay = flt(gross_pay) - flt(total_deduction)

        # Update the Salary Slip totals
        frappe.db.sql("""
            UPDATE `tabSalary Slip`
            SET
                gross_pay       = %(gross_pay)s,
                total_deduction = %(total_deduction)s,
                net_pay         = %(net_pay)s,
                modified        = NOW(),
                modified_by     = %(user)s
            WHERE
                name      = %(slip)s
                AND docstatus = 0
        """, {
            "gross_pay"      : flt(gross_pay),
            "total_deduction": flt(total_deduction),
            "net_pay"        : net_pay,
            "slip"           : slip_name,
            "user"           : frappe.session.user,
        })

    frappe.db.commit()

    frappe.msgprint(
        f"Salary Component <b>{component_name}</b> moved from "
        f"<b>{old_table}</b> to <b>{new_table}</b> in "
        f"<b>{len(slip_names)}</b> Draft Salary Slip(s):<br>"
        f"<small>{'<br>'.join(slip_names)}</small>",
        title="Draft Salary Slips Updated",
        indicator="green",
    )