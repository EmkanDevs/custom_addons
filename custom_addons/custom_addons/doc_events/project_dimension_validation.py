# Copyright (c) 2026, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe import _


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_project_config_for_doctype(submitting_doctype):
	"""Return project-dimension configuration for *submitting_doctype* read
	from Projects Settings.

	Returns a frappe._dict with:
	  - accounts    : set of account names that require the project field
	  - child_table : fieldname of the child table on the submitting doctype
	                  (empty/None = validate on the parent row directly)
	  - field_name  : the account fieldname to inspect (on parent or child row)

	Returns None if Projects Settings has no accounts configured, or if the
	submitting doctype is not listed in the Accounting Dimension Doctypes table.
	"""

	ps = frappe.get_single("Projects Settings")

	# Collect all governed accounts from the accounts child table.
	accounts = {
		row.account
		for row in (ps.get("accounting_dimension_accounts") or [])
		if row.account
	}

	if not accounts:
		return None

	# Find the row in the doctypes child table that matches this doctype.
	matched_row = None
	for row in (ps.get("accounting_dimension_doctypes") or []):
		if row.doctype_ == submitting_doctype:
			matched_row = row
			break

	if not matched_row:
		return None

	return frappe._dict(
		accounts=accounts,
		child_table=matched_row.child_table or None,
		field_name=matched_row.field_name,
	)


def _validate_configuration(doc, config):
	"""Verify the configured child_table and field_name actually exist on the
	target DocType, and that child_table is really a Table field."""

	parent_meta = frappe.get_meta(doc.doctype)
	child_table = config.child_table
	account_fieldname = config.field_name

	if child_table:
		child_field = parent_meta.get_field(child_table)
		if not child_field:
			frappe.throw(
				_(
					"Projects Settings — Accounting Dimension Doctypes: Child Table"
					" '<b>{child_table}</b>' does not exist on DocType '<b>{doctype}</b>'."
				).format(child_table=child_table, doctype=doc.doctype),
				title=_("Invalid Configuration"),
			)

		if child_field.fieldtype != "Table":
			frappe.throw(
				_(
					"Projects Settings — Accounting Dimension Doctypes: '<b>{child_table}</b>'"
					" on DocType '<b>{doctype}</b>' is a '{fieldtype}' field, not a Table field."
				).format(
					child_table=child_table,
					doctype=doc.doctype,
					fieldtype=child_field.fieldtype,
				),
				title=_("Invalid Configuration"),
			)

		child_doctype = child_field.options
		if not child_doctype:
			frappe.throw(
				_(
					"Projects Settings — Accounting Dimension Doctypes: Table field"
					" '<b>{child_table}</b>' on DocType '<b>{doctype}</b>' has no linked Child DocType."
				).format(child_table=child_table, doctype=doc.doctype),
				title=_("Invalid Configuration"),
			)

		child_meta = frappe.get_meta(child_doctype)
		if not child_meta.get_field(account_fieldname):
			frappe.throw(
				_(
					"Projects Settings — Accounting Dimension Doctypes: Field Name"
					" '<b>{field_name}</b>' does not exist on Child DocType '<b>{child_doctype}</b>'."
				).format(field_name=account_fieldname, child_doctype=child_doctype),
				title=_("Invalid Configuration"),
			)
	else:
		if not parent_meta.get_field(account_fieldname):
			frappe.throw(
				_(
					"Projects Settings — Accounting Dimension Doctypes: Field Name"
					" '<b>{field_name}</b>' does not exist on DocType '<b>{doctype}</b>'."
				).format(field_name=account_fieldname, doctype=doc.doctype),
				title=_("Invalid Configuration"),
			)


def _validate_project_on_parent(doc, config):
	"""Validate the project field directly on the parent document."""

	parent_account = doc.get(config.field_name)
	if not parent_account:
		return

	if parent_account not in config.accounts:
		return

	if not doc.get("project"):
		frappe.throw(
			_(
				"<b>Project</b> is mandatory for account <b>{account}</b>"
				" on {doctype}. Please fill in the Project field."
			).format(account=parent_account, doctype=doc.doctype),
			title=_("Missing Project"),
		)


def _validate_project_on_child_table(doc, config):
	"""Validate the project field on each row of the configured child table."""

	child_rows = doc.get(config.child_table) or []

	if not isinstance(child_rows, list):
		frappe.throw(
			_(
				"Projects Settings — Accounting Dimension Doctypes: Child Table"
				" '<b>{child_table}</b>' is not a valid table field on DocType '<b>{doctype}</b>'."
			).format(child_table=config.child_table, doctype=doc.doctype),
			title=_("Invalid Configuration"),
		)

	for row in child_rows:
		row_account = row.get(config.field_name)
		if not row_account:
			continue

		if row_account not in config.accounts:
			continue

		if not row.get("project"):
			frappe.throw(
				_(
					"Row {row_no}: <b>Project</b> is mandatory for account"
					" <b>{account}</b>. Please fill in the Project field."
				).format(row_no=row.idx, account=row_account),
				title=_("Missing Project"),
			)


# ---------------------------------------------------------------------------
# Dynamic hook handler (shared by all registered DocTypes)
# ---------------------------------------------------------------------------

def validate(doc, event=None):
	"""Validate that the project field is filled whenever an account governed
	by Projects Settings is used.

	Flow:
	  1. Read Projects Settings once.
	  2. If the submitting doctype is listed in Accounting Dimension Doctypes,
	     get its child_table and field_name (account field).
	  3. For each row in that child table (or on the parent if no child table),
	     if the account is in the governed accounts list → project must be filled.
	"""

	config = _get_project_config_for_doctype(doc.doctype)
	if not config:
		return

	if not config.field_name:
		frappe.throw(
			_(
				"Projects Settings — Accounting Dimension Doctypes: 'Field Name'"
				" is not configured for DocType '<b>{doctype}</b>'."
				" Please set the account field name in Projects Settings."
			).format(doctype=doc.doctype),
			title=_("Missing Configuration"),
		)

	_validate_configuration(doc, config)

	if config.child_table:
		_validate_project_on_child_table(doc, config)
	else:
		_validate_project_on_parent(doc, config)
