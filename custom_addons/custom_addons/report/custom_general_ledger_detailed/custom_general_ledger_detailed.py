import frappe
from frappe import _

from erpnext.accounts.report.general_ledger.general_ledger import execute as standard_gl_execute


def execute(filters=None):
    if not filters:
        return [], []

    standard_columns, data = standard_gl_execute(filters)
    add_account_details(data)
    add_voucher_details(data)
    return get_columns(standard_columns), data


def get_columns(standard_columns):
    columns = list(standard_columns)
    custom_columns = [
        {"label": _("Reference Date"), "fieldname": "reference_date", "fieldtype": "Date", "width": 110},
        {"label": _("Supplier Invoice Date"), "fieldname": "bill_date", "fieldtype": "Date", "width": 140},
        {"label": _("Account Number"), "fieldname": "account_number", "fieldtype": "Data", "width": 120},
        {"label": _("Account Name"), "fieldname": "account_name", "fieldtype": "Data", "width": 140},
    ]
    account_index = next(i for i, column in enumerate(columns) if column.get("fieldname") == "account")
    columns[account_index:account_index] = custom_columns
    columns.append({"label": _("Reference Number"), "fieldname": "reference_no", "fieldtype": "Data", "width": 130})
    return columns


def add_account_details(data):
    accounts = {row.get("account") for row in data if row.get("voucher_no") and row.get("account")}
    if not accounts:
        return

    details = {
        account.name: account
        for account in frappe.get_all(
            "Account", filters={"name": ("in", list(accounts))}, fields=["name", "account_name", "account_number"]
        )
    }
    for row in data:
        if account := details.get(row.get("account")):
            row["account_name"] = account.account_name
            row["account_number"] = account.account_number


def add_voucher_details(data):
    vouchers = {"Purchase Invoice": set(), "Payment Entry": set(), "Journal Entry": set()}
    for row in data:
        if row.get("voucher_no") and row.get("voucher_type") in vouchers:
            vouchers[row["voucher_type"]].add(row["voucher_no"])

    invoice_details = get_voucher_map("Purchase Invoice", vouchers["Purchase Invoice"], ["bill_date"])
    payment_details = get_voucher_map(
        "Payment Entry", vouchers["Payment Entry"], ["reference_no", "reference_date"]
    )
    journal_details = get_voucher_map("Journal Entry", vouchers["Journal Entry"], ["cheque_no", "cheque_date"])

    for row in data:
        voucher_no = row.get("voucher_no")
        if row.get("voucher_type") == "Purchase Invoice" and voucher_no in invoice_details:
            row["bill_date"] = invoice_details[voucher_no].bill_date
        elif row.get("voucher_type") == "Payment Entry" and voucher_no in payment_details:
            row["reference_no"] = payment_details[voucher_no].reference_no
            row["reference_date"] = payment_details[voucher_no].reference_date
        elif row.get("voucher_type") == "Journal Entry" and voucher_no in journal_details:
            row["reference_no"] = journal_details[voucher_no].cheque_no
            row["reference_date"] = journal_details[voucher_no].cheque_date


def get_voucher_map(doctype, names, fields):
    if not names:
        return {}
    return {
        voucher.name: voucher
        for voucher in frappe.get_all(
            doctype, filters={"name": ("in", list(names))}, fields=["name", *fields]
        )
    }
