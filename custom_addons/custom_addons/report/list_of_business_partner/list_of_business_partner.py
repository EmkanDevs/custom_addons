# Copyright (c) 2026, Finbyz Tech Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)
	report_summary = get_report_summary(data)
	return columns, data, None, chart, report_summary


def get_columns():
	return [
		{
			"label": _("#"),
			"fieldname": "idx",
			"fieldtype": "Int",
			"width": 50,
		},
		{
			"label": _("BP Type"),
			"fieldname": "bp_type",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("BP Code"),
			"fieldname": "bp_code",
			"fieldtype": "Dynamic Link",
			"options": "bp_doctype",
			"width": 130,
		},
		{
			"label": _("BP Name"),
			"fieldname": "bp_name",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Foreign Name"),
			"fieldname": "foreign_name",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Federal Tax ID"),
			"fieldname": "tax_id",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("CRN"),
			"fieldname": "crn",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Group Code"),
			"fieldname": "group_code",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Payment Terms Code"),
			"fieldname": "payment_terms",
			"fieldtype": "Link",
			"options": "Payment Terms Template",
			"width": 160,
		},
		{
			"label": _("Active"),
			"fieldname": "active",
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"label": _("Account Balance"),
			"fieldname": "account_balance",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"label": _("Accounts Receivable/Payable"),
			"fieldname": "account_name",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Control Acct."),
			"fieldname": "control_account",
			"fieldtype": "Data",
			"width": 120,
		},
	]


def get_data(filters):
	data = []
	bp_type = filters.get("bp_type")

	if not bp_type or bp_type == "Customer":
		data.extend(get_customers(filters))

	if not bp_type or bp_type == "Supplier":
		data.extend(get_suppliers(filters))

	data.sort(key=lambda row: (row["bp_type"], (row["bp_name"] or "").lower()))

	for i, row in enumerate(data, start=1):
		row["idx"] = i

	return data


def get_customers(filters):
	conditions, values = [], {}

	conditions.append("c.custom_is_business_partner_ = 1")

	if filters.get("party"):
		conditions.append("c.name = %(party)s")
		values["party"] = filters.get("party")

	if filters.get("tax_id"):
		conditions.append("(c.tax_id like %(tax_id)s or c.custom_cr like %(tax_id)s)")
		values["tax_id"] = "%{0}%".format(filters.get("tax_id"))

	if filters.get("group_code"):
		conditions.append("c.customer_group = %(group_code)s")
		values["group_code"] = filters.get("group_code")

	if filters.get("payment_terms"):
		conditions.append("c.payment_terms = %(payment_terms)s")
		values["payment_terms"] = filters.get("payment_terms")

	if filters.get("active") == "Yes":
		conditions.append("c.disabled = 0")
	elif filters.get("active") == "No":
		conditions.append("c.disabled = 1")

	company = filters.get("company")

	rows = frappe.db.sql(
		"""
		select
			c.name as bp_code,
			c.customer_name as bp_name,
			c.customer_name_in_arabic as foreign_name,
			c.tax_id as tax_id,
			c.custom_cr as customer_cr,
			c.customer_group as group_code,
			c.payment_terms as payment_terms,
			c.disabled as disabled
		from `tabCustomer` c
		where {conditions}
		order by c.customer_name
		""".format(conditions=" and ".join(conditions)),
		values,
		as_dict=True,
	)

	receivable_accounts = get_party_accounts("Customer", company)
	default_receivable = get_default_account("Customer", company)
	balances = get_gl_balances("Customer", company)

	data = []
	for row in rows:
		account = receivable_accounts.get(row["bp_code"]) or default_receivable

		if filters.get("account") and account != filters.get("account"):
			continue

		account_name, control_account = split_account(account)

		data.append(
			{
				"bp_type": "Customer",
				"bp_doctype": "Customer",
				"bp_code": row["bp_code"],
				"bp_name": row["bp_name"],
				"foreign_name": row["foreign_name"],
				"tax_id": row["tax_id"] or row["customer_cr"],
				"crn": None,
				"group_code": row["group_code"],
				"account_name": account_name,
				"control_account": control_account,
				"payment_terms": row["payment_terms"],
				"active": "No" if row["disabled"] else "Yes",
				"account_balance": balances.get(row["bp_code"], 0),
			}
		)

	return data


def get_suppliers(filters):
	conditions, values = [], {}

	conditions.append("s.custom_is_business_partner_ = 1")

	if filters.get("party"):
		conditions.append("s.name = %(party)s")
		values["party"] = filters.get("party")

	if filters.get("tax_id"):
		conditions.append("s.tax_id like %(tax_id)s")
		values["tax_id"] = "%{0}%".format(filters.get("tax_id"))

	if filters.get("group_code"):
		conditions.append("s.supplier_group = %(group_code)s")
		values["group_code"] = filters.get("group_code")

	if filters.get("payment_terms"):
		conditions.append("s.payment_terms = %(payment_terms)s")
		values["payment_terms"] = filters.get("payment_terms")

	if filters.get("active") == "Yes":
		conditions.append("s.disabled = 0")
	elif filters.get("active") == "No":
		conditions.append("s.disabled = 1")

	company = filters.get("company")

	rows = frappe.db.sql(
		"""
		select
			s.name as bp_code,
			s.supplier_name as bp_name,
			s.supplier_name_in_arabic as foreign_name,
			s.tax_id as tax_id,
			s.supplier_group as group_code,
			s.payment_terms as payment_terms,
			s.disabled as disabled
		from `tabSupplier` s
		where {conditions}
		order by s.supplier_name
		""".format(conditions=" and ".join(conditions)),
		values,
		as_dict=True,
	)

	payable_accounts = get_party_accounts("Supplier", company)
	default_payable = get_default_account("Supplier", company)
	balances = get_gl_balances("Supplier", company)

	data = []
	for row in rows:
		account = payable_accounts.get(row["bp_code"]) or default_payable

		if filters.get("account") and account != filters.get("account"):
			continue

		account_name, control_account = split_account(account)

		data.append(
			{
				"bp_type": "Supplier",
				"bp_doctype": "Supplier",
				"bp_code": row["bp_code"],
				"bp_name": row["bp_name"],
				"foreign_name": row["foreign_name"],
				"tax_id": row["tax_id"],
				"crn": None,
				"group_code": row["group_code"],
				"account_name": account_name,
				"control_account": control_account,
				"payment_terms": row["payment_terms"],
				"active": "No" if row["disabled"] else "Yes",
				"account_balance": balances.get(row["bp_code"], 0),
			}
		)

	return data


def get_party_accounts(party_type, company=None):
	"""Return {party_name: account} from the Party Account child table,
	optionally restricted to a single company."""
	conditions = {"parenttype": party_type}
	if company:
		conditions["company"] = company

	rows = frappe.get_all(
		"Party Account",
		filters=conditions,
		fields=["parent", "account", "company"],
	)

	accounts = {}
	for row in rows:
		# if multiple companies exist and none specified, first one wins
		accounts.setdefault(row["parent"], row["account"])

	return accounts


def get_default_account(party_type, company=None):
	"""Fallback to the company's default receivable/payable account."""
	if not company:
		company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
			"Global Defaults", "default_company"
		)

	if not company:
		return None

	fieldname = "default_receivable_account" if party_type == "Customer" else "default_payable_account"
	return frappe.db.get_value("Company", company, fieldname)


def split_account(account):
	"""Account is stored as 'CODE - Name - Abbr' (e.g. '2131101 - Accounts
	Payables Goods - CPC'). Return (name_part, code_part) to populate the
	'Accounts Receivable/Payable' and 'Control Acct.' columns respectively.

	account_number is not reliably set on every Account record, so the
	numeric code is parsed directly from the account string itself first,
	falling back to account_number. If neither exists, Control Acct. is
	left blank rather than repeating the account name."""
	if not account:
		return None, None

	parts = [p.strip() for p in account.split(" - ")]

	if len(parts) >= 2 and parts[0].replace(".", "").isdigit():
		# "2131101 - Accounts Payables Goods - CPC" -> code, name
		code, name = parts[0], parts[1]
	else:
		# no code prefix in the account name itself; fall back to the
		# account_number field, leave Control Acct. blank if that's empty too
		code = frappe.db.get_value("Account", account, "account_number")
		name = parts[0] if parts else account

	return name, code


def get_gl_balances(party_type, company=None):
	"""Net outstanding balance per party from GL Entry, restricted to the
	receivable/payable account type so advances/other ledgers don't bleed in."""
	conditions = {
		"party_type": party_type,
		"is_cancelled": 0,
	}
	if company:
		conditions["company"] = company

	rows = frappe.get_all(
		"GL Entry",
		filters=conditions,
		group_by="party",
		fields=["party", "sum(debit - credit) as balance"],
	)

	return {row["party"]: row["balance"] for row in rows}


def get_chart(data):
	"""Donut chart: Customer vs Supplier count, same style as the
	AR/AP report's aging legend at the top of the report."""
	customer_count = sum(1 for row in data if row["bp_type"] == "Customer")
	supplier_count = sum(1 for row in data if row["bp_type"] == "Supplier")

	return {
		"data": {
			"labels": [_("Customers"), _("Suppliers")],
			"datasets": [{"name": _("Business Partners"), "values": [customer_count, supplier_count]}],
		},
		"type": "donut",
		"colors": ["#5e64ff", "#ff5858"],
	}


def get_report_summary(data):
	"""Number-card style summary shown above the table, same slot the
	AR/AP reports use for their 0-30 / 31-60 / etc totals.

	account_balance is stored as (debit - credit) for both Customer and
	Supplier rows (same sign convention as the table column), so Payable
	is negated here to show as a positive outstanding amount."""
	customers = [row for row in data if row["bp_type"] == "Customer"]
	suppliers = [row for row in data if row["bp_type"] == "Supplier"]

	total_receivable = sum(row["account_balance"] or 0 for row in customers)
	total_payable = -sum(row["account_balance"] or 0 for row in suppliers)
	net_position = total_receivable - total_payable

	return [
		{
			"value": len(data),
			"label": _("Total Business Partners"),
			"datatype": "Int",
			"indicator": "blue",
		},
		{
			"value": len(customers),
			"label": _("Total Customers"),
			"datatype": "Int",
			"indicator": "blue",
		},
		{
			"value": len(suppliers),
			"label": _("Total Suppliers"),
			"datatype": "Int",
			"indicator": "orange",
		},
		{
			"value": total_receivable,
			"label": _("Total Receivable"),
			"datatype": "Currency",
			"indicator": "green",
		},
		{
			"value": total_payable,
			"label": _("Total Payable"),
			"datatype": "Currency",
			"indicator": "red",
		},
		{
			"value": net_position,
			"label": _("Net Position"),
			"datatype": "Currency",
			"indicator": "green" if net_position >= 0 else "red",
		},
	]