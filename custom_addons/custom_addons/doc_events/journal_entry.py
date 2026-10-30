# Copyright (c) 2026, Incharge and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from custom_addons.custom_addons.override.journal_entry import is_employee_target_account


def before_validate(doc, method=None):
	"""Set party_not_required = 1 before validations run so standard ERPNext
	does not require Party on non-employee accounts (e.g. Accounts Receivable / Payable).
	"""
	doc.party_not_required = 1


def validate(doc, method=None):
	"""Server validation hook for Journal Entry.
	- Ensures party_not_required = 1 so ERPNext standard does NOT force Party
	  on non-employee accounts.
	- For every row containing one of the 4 designated employee accounts:
	  * Verifies party_type is set to 'Employee'.
	  * Throws an error if party is not filled.
	  * Syncs party and employee dimension if present.
	"""
	doc.party_not_required = 1

	for row in doc.get("accounts", []):
		if is_employee_target_account(row.account):
			if not row.party_type:
				row.party_type = "Employee"
			elif row.party_type != "Employee":
				frappe.throw(
					_("Row {0}: Party Type must be 'Employee' for account {1}").format(
						row.idx, frappe.bold(row.account)
					),
					title=_("Invalid Party Type"),
				)

			# If accounting dimension employee field exists and is set, sync to party if party not set
			if not row.party and hasattr(row, "employee") and row.get("employee"):
				row.party = row.get("employee")

			if not row.party:
				frappe.throw(
					_("Row {0}: Party is mandatory for Employee account {1}").format(
						row.idx, frappe.bold(row.account)
					),
					title=_("Mandatory Field Missing"),
				)

			# If accounting dimension employee field is empty, sync from party
			if hasattr(row, "employee") and not row.get("employee"):
				row.employee = row.party
