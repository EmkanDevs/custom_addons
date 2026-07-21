import frappe
from frappe.utils import cint, fmt_money

@frappe.whitelist()
def po_query_with_totals(doctype, txt, searchfield, start, page_len, filters):
    if isinstance(filters, str):
        filters = frappe.parse_json(filters)
    filters = filters or {}

    # drop empty/unset filter rows coming from the "+ Add a Filter" UI
    filters = {
        k: v for k, v in filters.items()
        if not (isinstance(v, (list, tuple)) and (len(v) < 2 or v[-1] in (None, "", [])))
    }

    filters["docstatus"] = 1
    filters["company"] = frappe.defaults.get_user_default("Company")
    filters["status"] = ["not in", ["Closed", "Cancelled"]]
    filters["per_billed"] = ["<", 100]
    if txt:
        filters["name"] = ["like", f"%{txt}%"]

    data = frappe.get_list(
        "Purchase Order",
        filters=filters,
        fields=["name", "transaction_date", "supplier", "total", "grand_total", "status"],
        order_by="transaction_date desc",
        limit_start=cint(start),
        limit_page_length=cint(page_len),
    )

    for row in data:
        row["total"] = fmt_money(row["total"], precision=2)
        row["grand_total"] = fmt_money(row["grand_total"], precision=2)

    return data


@frappe.whitelist()
def pr_query_with_totals(doctype, txt, searchfield, start, page_len, filters):
    if isinstance(filters, str):
        filters = frappe.parse_json(filters)
    filters = filters or {}

    filters = {
        k: v for k, v in filters.items()
        if not (isinstance(v, (list, tuple)) and (len(v) < 2 or v[-1] in (None, "", [])))
    }

    filters["docstatus"] = 1
    filters["company"] = frappe.defaults.get_user_default("Company")
    filters["status"] = ["not in", ["Closed", "Cancelled"]]
    filters["per_billed"] = ["<", 100]
    if txt:
        filters["name"] = ["like", f"%{txt}%"]

    data = frappe.get_list(
        "Purchase Receipt",
        filters=filters,
        fields=["name", "posting_date", "supplier", "total", "grand_total", "status"],
        order_by="posting_date desc",
        limit_start=cint(start),
        limit_page_length=cint(page_len),
    )

    for row in data:
        row["total"] = fmt_money(row["total"], precision=2)
        row["grand_total"] = fmt_money(row["grand_total"], precision=2)

    return data