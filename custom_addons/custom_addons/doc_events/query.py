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




@frappe.whitelist()
def bo_query_with_totals(doctype, txt, searchfield, start, page_len, filters):
	filters = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})

	conditions = {
		"docstatus": 1,
		"blanket_order_type": "Purchasing",
		"blanket_order_po_exemption": 1,
	}

	for key, value in filters.items():
		if value not in (None, "", []):
			conditions[key] = value

	if txt:
		conditions["name"] = ["like", f"%{txt}%"]

	return frappe.get_list(
		"Blanket Order",
		filters=conditions,
		fields=["name", "supplier", "from_date", "to_date", "blanket_order_type"],
		order_by="from_date desc",
		limit_start=cint(start),
		limit_page_length=cint(page_len),
		as_list=False,
	)


@frappe.whitelist()
def blanket_eligible_item_query(doctype, txt, searchfield, start, page_len, filters):
	filters = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})

	conditions = [
		"`tabItem`.disabled = 0",
		"`tabItem`.is_stock_item = 0",
		"`tabItem`.is_fixed_asset = 0",
		"`tabItem`.blanket_order_po_exemption = 1",
	]

	values = {"page_len": page_len, "start": start}

	if txt:
		conditions.append("(`tabItem`.name like %(txt)s or `tabItem`.item_name like %(txt)s)")
		values["txt"] = f"%{txt}%"

	condition_str = " and ".join(conditions)

	return frappe.db.sql(
		f"""
		select `tabItem`.name, `tabItem`.item_name
		from `tabItem`
		where {condition_str}
		order by `tabItem`.name
		limit %(page_len)s offset %(start)s
		""",
		values,
	)