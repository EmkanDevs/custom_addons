# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe


def execute(filters):
    filters_for_data = (filters or {}).copy()

    columns = [
        {"label": "Workflow Status", "fieldname": "workflow_status", "fieldtype": "Data", "width": 120},
        {"label": "Expense Claim Amount", "fieldname": "expense_claim_amount", "fieldtype": "Currency", "width": 180},
        {"label": "Purchase Receipt Amount", "fieldname": "purchase_receipt_amount", "fieldtype": "Currency", "width": 180},
        {"label": "Total Taxes and Charges", "fieldname": "total_taxes_charges", "fieldtype": "Currency", "width": 180},
        {"label": "TOTAL Un-Settled Amount", "fieldname": "unsettled_amount", "fieldtype": "Currency", "width": 200},
        {"label": "Settled Petty Cash", "fieldname": "settled_petty_cash", "fieldtype": "Currency", "width": 200},
        {"label": "Net Amount", "fieldname": "net_amount", "fieldtype": "Currency", "width": 200},
    ]

    data = get_grouped_data(filters_for_data)
    summary = get_summary(filters or {})

    fieldnames = []
    seen = {}
    for i, col in enumerate(columns):
        fname = col.get("fieldname") or f"col_{i}"
        if fname in seen:
            seen[fname] += 1
            new_fname = f"{fname}_{seen[fname]}"
            col["fieldname"] = new_fname
            fieldnames.append(new_fname)
        else:
            seen[fname] = 0
            fieldnames.append(fname)

    mapped_data = []
    for row in data:
        row_dict = {}
        for idx, fname in enumerate(fieldnames):
            row_dict[fname] = row[idx] if idx < len(row) else None
        mapped_data.append(row_dict)

    return columns, mapped_data, None, None, summary



def save_data(status, filters, data, filters_purchase_receipt):
    filters_q = (filters or {}).copy()
    filters_q["docstatus"] = status

    expense_claim = frappe.db.get_values("Expense Claim", filters=filters_q, fieldname=["grand_total"], as_dict=True)
    if filters_purchase_receipt:
        fpr = (filters_purchase_receipt or {}).copy()
        fpr["docstatus"] = status
        purchase_receipt = frappe.db.get_values("Purchase Receipt", filters=fpr, fieldname=["grand_total"], as_dict=True)
    else:
        purchase_receipt = frappe.db.get_values("Purchase Receipt", filters=filters_q, fieldname=["grand_total"], as_dict=True)

    data[status][1] = expense_claim[0].get("grand_total", 0) if expense_claim else 0
    data[status][2] = purchase_receipt[0].get("grand_total", 0) if purchase_receipt else 0
    return data


def get_data(data, filters, filters_purchase_receipt):
    for status in [0, 1, 2]:
        data = save_data(status, filters, data, filters_purchase_receipt)

    for idx in range(len(data)):
        data[idx][4] = (data[idx][1] or 0) + (data[idx][2] or 0)

    return data


def get_grouped_data(filters):
    data = [
        ["Draft", 0, 0, 0, 0, 0, 0],
        ["Approved", 0, 0, 0, 0, 0, 0],
        ["Cancelled", 0, 0, 0, 0, 0, 0]
    ]

    f = (filters or {}).copy()

    if f.get("department") and f.get("employee"):
        petty_cash_requests = frappe.db.get_values("Petty Cash Request", filters=f, fieldname=["employee_id"], as_dict=True)
        f.pop("department", None)
        filters_purchase_receipt = f.copy()
        filters_purchase_receipt.pop("employee", None)
        filters_purchase_receipt["custom_petty_cash_holder"] = f.get("employee")
        data = get_data(data, f, filters_purchase_receipt)

    elif f.get("department"):
        department = f.get("department")
        petty_cash_requests = frappe.db.get_values("Petty Cash Request", filters={"department": department},
                                                  fieldname=["employee_id"], as_dict=True)
        for employee in petty_cash_requests:
            filters_purchase_receipt = f.copy()
            filters_purchase_receipt["custom_petty_cash_holder"] = employee.get("employee_id")
            data = get_data(data, f, filters_purchase_receipt)

    elif f.get("employee"):
        filters_purchase_receipt = f.copy()
        filters_purchase_receipt.pop("employee", None)
        filters_purchase_receipt["custom_petty_cash_holder"] = f.get("employee")
        data = get_data(data, f, filters_purchase_receipt)

    else:
        data = get_data(data, f, None)

    if f.get("project"):
        settled_result = frappe.db.sql("""
            SELECT SUM(balances) AS total_settled
            FROM `tabPetty Cash Settled`
            WHERE project = %(project)s
        """, {"project": f.get("project")}, as_dict=True)

        settled_sum = (
            settled_result[0].get("total_settled")
            if settled_result and settled_result[0].get("total_settled")
            else 0
        )

        data[1][5] = settled_sum  
        data[1][6] = (data[1][4] or 0) - settled_sum

    return data


def get_summary(filters):
    # Get all requests for the project
    conditions = ""
    if filters.get("project"):
        conditions += " AND project = %(project)s"
    requests = frappe.db.sql(f"""
        SELECT received_amount
        FROM `tabPetty Cash Request`
        WHERE docstatus = 1 {conditions}
    """, filters, as_dict=True)
    total_received = sum(r["received_amount"] or 0 for r in requests)
    project_name = frappe.db.get_value("Project", filters.get("project"), "project_name")
    return [
        {
            "label": "TOTAL Received Amount",
            "value": total_received,
            "indicator": "Green",
            "datatype":"Currency"
        },
        {
            "label": "Project Name",
            "value": project_name,
            "indicator": "Red",
            "datatype":"Data",
        }
    ]
