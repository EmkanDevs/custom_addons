# Copyright (c) 2026, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

from erpnext.accounts.report.trial_balance.trial_balance import execute as trial_balance_execute


def execute(filters=None):
	filters = frappe._dict(filters or {})
	_, data = trial_balance_execute(filters)
	if not data:
		return get_columns(), []

	accounts = {
		account.name: account
		for account in frappe.get_all(
			"Account",
			filters={"company": filters.company},
			fields=["name", "account_number", "account_name", "account_type"],
		)
	}
	for row in data:
		if not row:
			continue

		account = accounts.get(row.get("account"))
		if account:
			row.update(
				account_number=account.account_number,
				account_name=account.account_name,
				account_type=account.account_type,
			)

		row["opening"] = flt(row.get("opening_debit")) - flt(row.get("opening_credit"))
		row["balance"] = flt(row.get("closing_debit")) - flt(row.get("closing_credit"))

	return get_columns(), data


def get_columns():
	return [
		{
			"fieldname": "account_number",
			"label": _("Account No"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "account_name",
			"label": _("Account Name"),
			"fieldtype": "Data",
			"width": 320,
		},
		{
			"fieldname": "account_type",
			"label": _("Account Type"),
			"fieldtype": "Data",
			"width": 200,
		},
		*[
			{
				"fieldname": fieldname,
				"label": _(label),
				"fieldtype": "Currency",
				"options": "currency",
				"width": 150,
			}
			for fieldname, label in (
				("opening", "OP"),
				("debit", "Debit"),
				("credit", "Credit"),
				("balance", "Balance"),
			)
		],
	]
