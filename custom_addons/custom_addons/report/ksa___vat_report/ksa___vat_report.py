import frappe
from frappe.utils import flt, getdate


def execute(filters=None):
    filters = frappe._dict(filters or {})
    validate_filters(filters)

    columns = get_columns()
    data = get_data(filters)

    for idx, row in enumerate(data, start=1):
        row["sr_no"] = idx

    return columns, data


def validate_filters(filters):
    if not filters.get("from_date"):
        frappe.throw("From Date is required.")

    if not filters.get("to_date"):
        frappe.throw("To Date is required.")

    if filters.from_date > filters.to_date:
        frappe.throw("From Date cannot be greater than To Date.")


def get_columns():
    return [
        {"label": "Type", "fieldname": "type", "fieldtype": "Data", "width": 140},
        {"label": "Invoice Number", "fieldname": "invoice_number", "fieldtype": "Dynamic Link", "options": "doctype", "width": 150},
        {"label": "Year", "fieldname": "year", "fieldtype": "Int", "width": 80},
        {"label": "Quarter Name", "fieldname": "quarter_name", "fieldtype": "Data", "width": 100},
        {"label": "Month Number", "fieldname": "month_number", "fieldtype": "Int", "width": 100},
        {"label": "Month Name", "fieldname": "month_name", "fieldtype": "Data", "width": 120},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": "Customer/Supplier", "fieldname": "customer_supplier", "fieldtype": "Data", "width": 180},
        {"label": "Tax Account", "fieldname": "tax_account", "fieldtype": "Link", "options": "Account", "width": 200},
        {"label": "Root Type", "fieldname": "root_type", "fieldtype": "Data", "width": 100},
        {"label": "Source", "fieldname": "source", "fieldtype": "Data", "width": 130},
        {"label": "Tax ID (TRN)", "fieldname": "tax_id", "fieldtype": "Data", "width": 130},
        {"label": "Tax Template", "fieldname": "tax_template", "fieldtype": "Data", "width": 180},
        {"label": "Taxable Amount", "fieldname": "taxable_amount", "fieldtype": "Currency", "width": 140},
        {"label": "VAT Amount", "fieldname": "vat_amount", "fieldtype": "Currency", "width": 140},
        {"label": "Total Amount", "fieldname": "total_amount", "fieldtype": "Currency", "width": 140},
        {"label": "Document Type", "fieldname": "doctype", "fieldtype": "Data", "hidden": 1},
    ]


def get_data(filters):
    tax_account_map = get_tax_accounts(filters)
    if not tax_account_map:
        return []

    grouped_gl = get_grouped_gl_entries(filters, tax_account_map)
    if not grouped_gl:
        return []

    meta_maps = get_voucher_metadata_maps(grouped_gl)
    return build_report_rows(grouped_gl, tax_account_map, meta_maps, filters)


def get_tax_accounts(filters):
    acc_filters = {"account_type": ["in", ["Tax", "Charge"]]}
    if filters.get("root_type"):
        acc_filters["root_type"] = filters.get("root_type")

    tax_accounts = frappe.get_list(
        "Account",
        filters=acc_filters,
        fields=["name", "root_type"],
        limit_page_length=0,
    )
    return {acc.name: acc.root_type for acc in tax_accounts}


def get_grouped_gl_entries(filters, tax_account_map):
    gl_filters = {
        "is_cancelled": 0,
        "account": ["in", list(tax_account_map.keys())],
        "posting_date": ["between", [filters.from_date, filters.to_date]],
    }
    if filters.get("source"):
        gl_filters["voucher_type"] = filters.get("source")

    gl_entries = frappe.get_list(
        "GL Entry",
        filters=gl_filters,
        fields=[
            "voucher_type",
            "voucher_no",
            "account",
            "posting_date",
            "debit",
            "credit",
            "party",
        ],
        order_by="posting_date asc",
        limit_page_length=0,
    )

    grouped_gl = {}
    for entry in gl_entries:
        key = (entry.voucher_type, entry.voucher_no, entry.account, entry.posting_date)
        if key not in grouped_gl:
            grouped_gl[key] = {
                "voucher_type": entry.voucher_type,
                "voucher_no": entry.voucher_no,
                "account": entry.account,
                "posting_date": getdate(entry.posting_date),
                "party": entry.party,
                "net_vat": 0.0,
            }
        grouped_gl[key]["net_vat"] += flt(entry.debit) - flt(entry.credit)

    return grouped_gl


def get_voucher_metadata_maps(grouped_gl):
    vouchers_by_type = {}
    for item in grouped_gl.values():
        vouchers_by_type.setdefault(item["voucher_type"], set()).add(item["voucher_no"])

    maps = {
        "Sales Invoice": {},
        "Purchase Invoice": {},
        "Payment Entry": {},
        "Journal Entry": {},
        "Expense Claim": {},
    }

    if vouchers_by_type.get("Sales Invoice"):
        for doc in frappe.get_list(
            "Sales Invoice",
            filters={"name": ["in", list(vouchers_by_type["Sales Invoice"])]},
            fields=[
                "name",
                "customer_name",
                "tax_id",
                "taxes_and_charges",
                "base_net_total",
                "base_grand_total",
                "is_return",
            ],
            limit_page_length=0,
        ):
            maps["Sales Invoice"][doc.name] = doc

    if vouchers_by_type.get("Purchase Invoice"):
        for doc in frappe.get_list(
            "Purchase Invoice",
            filters={"name": ["in", list(vouchers_by_type["Purchase Invoice"])]},
            fields=[
                "name",
                "supplier_name",
                "tax_id",
                "taxes_and_charges",
                "base_net_total",
                "base_grand_total",
                "is_return",
            ],
            limit_page_length=0,
        ):
            maps["Purchase Invoice"][doc.name] = doc

    if vouchers_by_type.get("Payment Entry"):
        for doc in frappe.get_list(
            "Payment Entry",
            filters={"name": ["in", list(vouchers_by_type["Payment Entry"])]},
            fields=["name", "party_name", "base_paid_amount", "base_received_amount"],
            limit_page_length=0,
        ):
            maps["Payment Entry"][doc.name] = doc

    if vouchers_by_type.get("Journal Entry"):
        for doc in frappe.get_list(
            "Journal Entry",
            filters={"name": ["in", list(vouchers_by_type["Journal Entry"])]},
            fields=["name", "pay_to_recd_from", "total_amount"],
            limit_page_length=0,
        ):
            maps["Journal Entry"][doc.name] = doc

    if vouchers_by_type.get("Expense Claim"):
        for doc in frappe.get_list(
            "Expense Claim",
            filters={"name": ["in", list(vouchers_by_type["Expense Claim"])]},
            fields=["name", "employee_name", "total_sanctioned_amount"],
            limit_page_length=0,
        ):
            maps["Expense Claim"][doc.name] = doc

    return maps


def build_report_rows(grouped_gl, tax_account_map, meta_maps, filters):
    data = []
    cs_filter = (filters.get("customer_supplier") or "").strip().lower()

    for item in grouped_gl.values():
        v_type = item["voucher_type"]
        v_no = item["voucher_no"]
        p_date = item["posting_date"]

        type_label = v_type
        if v_type == "Sales Invoice":
            type_label = "Output VAT (Sales)"
        elif v_type == "Purchase Invoice":
            type_label = "Input VAT (Purchases)"

        customer_supplier = item["party"]
        tax_id = None
        tax_template = None
        taxable_amount = 0.0
        total_amount = 0.0

        if v_type == "Sales Invoice":
            si = meta_maps["Sales Invoice"].get(v_no)
            if si:
                customer_supplier = si.customer_name or customer_supplier
                tax_id = si.tax_id
                tax_template = si.taxes_and_charges
                sign = 1 if si.is_return == 1 else -1
                taxable_amount = sign * abs(flt(si.base_net_total))
                total_amount = sign * abs(flt(si.base_grand_total))
        elif v_type == "Purchase Invoice":
            pi = meta_maps["Purchase Invoice"].get(v_no)
            if pi:
                customer_supplier = pi.supplier_name or customer_supplier
                tax_id = pi.tax_id
                tax_template = pi.taxes_and_charges
                sign = -1 if pi.is_return == 1 else 1
                taxable_amount = sign * abs(flt(pi.base_net_total))
                total_amount = sign * abs(flt(pi.base_grand_total))
        elif v_type == "Payment Entry":
            pe = meta_maps["Payment Entry"].get(v_no)
            if pe:
                customer_supplier = pe.party_name or customer_supplier
                taxable_amount = flt(pe.base_paid_amount) + flt(pe.base_received_amount)
                total_amount = taxable_amount
        elif v_type == "Journal Entry":
            je = meta_maps["Journal Entry"].get(v_no)
            if je:
                customer_supplier = je.pay_to_recd_from or customer_supplier
                taxable_amount = flt(je.total_amount)
                total_amount = taxable_amount
        elif v_type == "Expense Claim":
            ec = meta_maps["Expense Claim"].get(v_no)
            if ec:
                customer_supplier = ec.employee_name or customer_supplier
                taxable_amount = flt(ec.total_sanctioned_amount)
                total_amount = taxable_amount

        if cs_filter and not (customer_supplier and cs_filter in customer_supplier.lower()):
            continue

        data.append(
            {
                "type": type_label,
                "invoice_number": v_no,
                "year": p_date.year,
                "quarter_name": f"Q{(p_date.month - 1) // 3 + 1}",
                "month_number": p_date.month,
                "month_name": p_date.strftime("%B"),
                "date": p_date,
                "customer_supplier": customer_supplier,
                "tax_account": item["account"],
                "root_type": tax_account_map.get(item["account"]),
                "source": v_type,
                "tax_id": tax_id,
                "tax_template": tax_template,
                "taxable_amount": taxable_amount,
                "vat_amount": round(item["net_vat"], 2),
                "total_amount": total_amount,
                "doctype": v_type,
            }
        )

    data.sort(key=lambda x: (x["type"], x["year"], x["month_number"], x["date"]))
    return data
