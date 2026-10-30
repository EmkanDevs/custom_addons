# Copyright (c) 2026, Incharge and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.accounts.doctype.journal_entry.journal_entry import (
	get_account_details_and_party_type as standard_get_account_details_and_party_type,
)

EMPLOYEE_ACCOUNT_NUMBERS = {"1158101", "1159000", "1159104", "1159102"}
EMPLOYEE_ACCOUNT_NAMES = {
	"petty cash (business advance)",
	"employee loans",
	"employee other deduction",
	"employee other deductions",
	"employee loans (e.o.s)",
	"employee loan (e.o.s)",
	"mega employee loan",
}


def is_employee_target_account(account):
	"""Check if an account matches any of the designated 4 employee accounts
	by account number or account name (regardless of company suffix).
	Designated accounts:
	  1158101 - Petty Cash (Business Advance)
	  1159000 - Employee Loans
	  1159104 - Employee Other Deduction (or MEGA Employee Loan)
	  1159102 - Employee Loans (E.O.S)
	"""
	if not account:
		return False

	account_str = str(account).strip()

	# 1. Match account number prefix / substring
	for num in EMPLOYEE_ACCOUNT_NUMBERS:
		if account_str.startswith(num) or num in account_str:
			return True

	# 2. Match target account names (case-insensitive)
	lower_name = account_str.lower()
	for name in EMPLOYEE_ACCOUNT_NAMES:
		if name in lower_name:
			return True

	# 3. Match against Account record fields in DB
	if getattr(frappe, "db", None):
		try:
			acc_data = frappe.get_cached_value(
				"Account", account_str, ["account_number", "account_name"], as_dict=True
			)
			if acc_data:
				if acc_data.get("account_number") in EMPLOYEE_ACCOUNT_NUMBERS:
					return True
				acc_name = (acc_data.get("account_name") or "").strip().lower()
				for name in EMPLOYEE_ACCOUNT_NAMES:
					if name in acc_name:
						return True
		except Exception:
			pass

	return False


@frappe.whitelist()
def get_account_details_and_party_type(
	account, date, company, debit=None, credit=None, exchange_rate=None
):
	"""Override for get_account_details_and_party_type.
	Returns party_type: 'Employee' when one of the target employee accounts is selected.
	"""
	res = standard_get_account_details_and_party_type(
		account=account,
		date=date,
		company=company,
		debit=debit,
		credit=credit,
		exchange_rate=exchange_rate,
	)

	if res is None:
		res = {}

	if is_employee_target_account(account):
		res["party_type"] = "Employee"

	return res


_orig_validate_account_party_type = None
_orig_journal_entry_validate_party = None


def patched_validate_account_party_type(self):
	"""Monkey-patch for validate_account_party_type in GL Entry & party module.
	Allows party_type = 'Employee' for the designated employee accounts during submission,
	preventing 'Party Type and Party can only be set for Receivable / Payable account' errors.
	"""
	if self.is_cancelled:
		return

	if self.party_type == "Employee" and is_employee_target_account(self.account):
		return

	if _orig_validate_account_party_type:
		return _orig_validate_account_party_type(self)


def patched_journal_entry_validate_party(self):
	"""Ensure Party Type and Party are mandatory ONLY for the 4 designated employee accounts.
	For all other accounts (Receivable / Payable / Customer / Supplier), Party is optional
	and saving/submitting is allowed without providing a Party.
	"""
	self.party_not_required = 1

	for d in self.get("accounts", []):
		account_type = frappe.get_cached_value("Account", d.account, "account_type")

		if is_employee_target_account(d.account):
			if not d.party_type:
				d.party_type = "Employee"
			elif d.party_type != "Employee":
				frappe.throw(
					_("Row {0}: Party Type must be 'Employee' for account {1}").format(
						d.idx, frappe.bold(d.account)
					),
					title=_("Invalid Party Type"),
				)

			# If accounting dimension employee field exists and is set, sync to party if party not set
			if not d.party and hasattr(d, "employee") and d.get("employee"):
				d.party = d.get("employee")

			if not d.party:
				frappe.throw(
					_("Row {0}: Party is mandatory for Employee account {1}").format(
						d.idx, frappe.bold(d.account)
					),
					title=_("Mandatory Field Missing"),
				)

			# If accounting dimension employee field is empty, sync from party
			if hasattr(d, "employee") and not d.get("employee"):
				d.employee = d.party
		else:
			# Non-employee accounts: Party is optional.
			# Only check account type mismatch IF both party_type and party are provided.
			if d.party_type and d.party:
				if (
					account_type in ["Receivable", "Payable"]
					and frappe.db.get_value("Party Type", d.party_type, "account_type") != account_type
					and d.party_type != "Employee"
				):
					frappe.throw(
						_("Row {0}: Account {1} and Party Type {2} have different account types").format(
							d.idx, d.account, d.party_type
						)
					)


def apply_gl_entry_patch():
	"""Apply monkey patch to erpnext.accounts.party, gl_entry, and journal_entry."""
	global _orig_validate_account_party_type, _orig_journal_entry_validate_party
	import erpnext.accounts.party
	import erpnext.accounts.doctype.gl_entry.gl_entry
	import erpnext.accounts.doctype.journal_entry.journal_entry as je_module

	if _orig_validate_account_party_type is None:
		_orig_validate_account_party_type = erpnext.accounts.party.validate_account_party_type

	erpnext.accounts.party.validate_account_party_type = patched_validate_account_party_type
	erpnext.accounts.doctype.gl_entry.gl_entry.validate_account_party_type = (
		patched_validate_account_party_type
	)
	je_module.get_account_details_and_party_type = get_account_details_and_party_type

	if hasattr(je_module, "JournalEntry"):
		if _orig_journal_entry_validate_party is None:
			_orig_journal_entry_validate_party = je_module.JournalEntry.validate_party
		je_module.JournalEntry.validate_party = patched_journal_entry_validate_party


# Apply immediately when module is imported
apply_gl_entry_patch()
