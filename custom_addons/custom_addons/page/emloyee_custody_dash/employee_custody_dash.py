import frappe
from frappe.utils import nowdate

@frappe.whitelist()
def get_it_assets(employee, active_only=0):
    condition = ""
    values = {"employee": employee}

    if int(active_only):
        condition += " AND (child.to_date IS NULL OR child.to_date >= %(today)s)"
        values["today"] = nowdate()

    data = frappe.db.sql(f"""
        SELECT
            iam.asset_local_code AS asset_id,
            iam.item,
            iam.item_name,
            iam.item_group,
            iam.manufacturer,
            child.from_date,
            child.to_date
        FROM `tabIT Asset Management` iam
        INNER JOIN `tabIT Asset Assigned User2` child
            ON child.parent = iam.name
        WHERE child.assigned_user = %(employee)s
        {condition}
        ORDER BY child.from_date DESC
    """, values, as_dict=True)

    return data


@frappe.whitelist()
def get_sim_cards(employee, active_only=0):
    condition = ""
    values = {"employee": employee}

    # ✅ Apply Active filter on status
    if int(active_only):
        condition += " AND sim.status = 'In Use'"

    data = frappe.db.sql(f"""
        SELECT
            sim.name AS sim_id,
            sim.service_no,
            sim.serial_number,
            sim.reason_of_purchase,
            sim.sim_provider,
            sim.status,
            child.from_date,
            child.to_date
        FROM `tabSIM Management` sim
        INNER JOIN `tabSIM Assigned User` child
            ON child.parent = sim.name
        WHERE child.assigned_user = %(employee)s
        {condition}
        ORDER BY child.from_date DESC
    """, values, as_dict=True)

    return data


@frappe.whitelist()
def get_vehicles(employee):
    data = frappe.db.sql("""
        SELECT
            v.name AS vehicle_id,
            v.tags,
            v.license_plate,
            v.door_number,
            v.vehicle_types,
            v.model_year
        FROM `tabVehicles` v
        WHERE v.driver = %s
        ORDER BY v.modified DESC
    """, (employee,), as_dict=True)

    return data


@frappe.whitelist()
def get_employee_custody(employee=None):
    condition = ""
    values = {}

    if employee:
        condition = "AND emp.name = %(employee)s"
        values["employee"] = employee

    data = frappe.db.sql(f"""
        SELECT
            emp.name AS employee,
            emp.employee_name,
            emp.department,
            
            /* Calculate final balance */
            IFNULL(adv.total_advance, 0) 
            - (IFNULL(exp.total_expense, 0) + IFNULL(pi.total_pi_amount, 0)) AS pending_amount,
            
            IFNULL(adv.total_advance, 0) AS total_advance,
            IFNULL(exp.total_expense, 0) AS total_expense_claim,
            IFNULL(pi.total_pi_amount, 0) AS total_purchase_invoice

        FROM `tabEmployee` emp

        /* 1. Sum Employee Advances */
        LEFT JOIN (
            SELECT employee, SUM(paid_amount) AS total_advance
            FROM `tabEmployee Advance`
            WHERE docstatus = 1
            GROUP BY employee
        ) adv ON adv.employee = emp.name

        /* 2. Sum Expense Claims */
        LEFT JOIN (
            SELECT employee, SUM(total_claimed_amount) AS total_expense
            FROM `tabExpense Claim`
            WHERE docstatus = 1
            GROUP BY employee
        ) exp ON exp.employee = emp.name

        /* 3. Sum Purchase Invoices linked to Employee */
        LEFT JOIN (
            SELECT employee, SUM(grand_total) AS total_pi_amount
            FROM `tabPurchase Invoice`
            WHERE docstatus = 1 AND employee IS NOT NULL AND employee != ''
            GROUP BY employee
        ) pi ON pi.employee = emp.name

        WHERE 
            (IFNULL(adv.total_advance, 0) 
            - (IFNULL(exp.total_expense, 0) + IFNULL(pi.total_pi_amount, 0))) != 0
            {condition}

        ORDER BY pending_amount DESC
    """, values, as_dict=True)

    return data

@frappe.whitelist()
def get_medical_insurance(employee):
    # Try employee_number first
    emp_number = frappe.db.get_value('Employee', employee, 'employee_number')

    if emp_number:
        data = frappe.db.sql("""
            SELECT
                mis.main_member_id AS employee,
                mis.main_member_id,
                mis.bupa_id,
                mis.employee_number,
                mis.member_name,
                mis.relationship,
                mis.main_membership_no,
                mis.member_cchi_status,
                mis.member_reject_reason
            FROM `tabMedical Insurance Sheet` mis
            WHERE mis.employee_number = %s
            ORDER BY mis.creation DESC
        """, (emp_number,), as_dict=True)
    else:
        # Fallback: match directly by main_member_id
        data = frappe.db.sql("""
            SELECT
                mis.main_member_id AS employee,
                mis.main_member_id,
                mis.bupa_id,
                mis.employee_number,
                mis.member_name,
                mis.relationship,
                mis.main_membership_no,
                mis.member_cchi_status,
                mis.member_reject_reason
            FROM `tabMedical Insurance Sheet` mis
            WHERE mis.main_member_id = %s
            ORDER BY mis.creation DESC
        """, (employee,), as_dict=True)

    return data


    

@frappe.whitelist()
def get_equipment_tools(employee, active_only=0):

    records = frappe.db.sql("""

        SELECT
            elr.custody_holder_id,
            elr.custody_holder_name,

            eli.item_code,
            eli.item_name,
            eli.item_group,
            eli.fixed_asset,
            eli.project,
            proj.project_name,
            eli.tag_number,
            eli.quantity,
            elr.transaction_type

        FROM `tabEquipment Log Register` elr

        INNER JOIN `tabEquipment Log Item` eli
            ON eli.parent = elr.name

        LEFT JOIN `tabProject` proj
            ON proj.name = eli.project

        WHERE elr.docstatus = 1
        AND elr.custody_holder_id = %(employee)s

        ORDER BY eli.item_code

    """, {
        "employee": employee
    }, as_dict=True)

    balance_map = {}

    for row in records:

        # =========================
        # ASSET
        # =========================

        if row.fixed_asset:

            key = (
                row.item_code,
                row.tag_number,
                row.project
            )

            if key not in balance_map:

                balance_map[key] = {
                    "item_code": row.item_code,
                    "item_name": row.item_name,
                    "item_group": row.item_group,
                    "stock_asset": "Asset",
                    "project": row.project,
                    "project_name": row.project_name,
                    "balance_qty": 0
                }

            if row.transaction_type == "Issue / Receiving":
                balance_map[key]["balance_qty"] += 1

            elif row.transaction_type == "Return":
                balance_map[key]["balance_qty"] -= 1

        # =========================
        # STOCK
        # =========================

        else:

            key = (
                row.item_code,
                row.project
            )

            if key not in balance_map:

                balance_map[key] = {
                    "item_code": row.item_code,
                    "item_name": row.item_name,
                    "item_group": row.item_group,
                    "stock_asset": "Stock",
                    "project": row.project,
                    "project_name": row.project_name,
                    "balance_qty": 0
                }

            qty = row.quantity or 0

            if row.transaction_type == "Issue / Receiving":
                balance_map[key]["balance_qty"] += qty

            elif row.transaction_type == "Return":
                balance_map[key]["balance_qty"] -= qty

    final_data = []

    for value in balance_map.values():

        # Active only = show balance > 0
        if int(active_only):

            if value["balance_qty"] > 0:
                final_data.append(value)

        else:
            final_data.append(value)

    return final_data