# Copyright (c) 2026, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe import _


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_dimensions_for_doctype(submitting_doctype):
	"""Return every enabled Accounting Dimension that applies to *submitting_doctype*,
	together with the per-DocType child-table and account-field configuration."""

	all_dims = frappe.get_all(
		"Accounting Dimension",
		filters={"disabled": 0},
		fields=["name", "label", "fieldname"],
	)

	applicable = []
	for dim in all_dims:
		dim_doc = frappe.get_doc("Accounting Dimension", dim.name)

		# Find the row in the custom_doctype child table that matches this doctype
		doctype_rows = dim_doc.get("custom_doctype") or []
		matched_row = None
		for row in doctype_rows:
			if row.doctype_ == submitting_doctype:
				matched_row = row
				break

		if not matched_row:
			continue

		# Collect the accounts governed by this dimension.
		# The Accounting Dimension CT Accounts child field is named "account".
		accounts = {
			row.account
			for row in (dim_doc.get("custom_accounts") or [])
			if row.account
		}

		applicable.append(
			frappe._dict(
				name=dim.name,
				label=dim.label,
				fieldname=dim.fieldname,
				accounts=accounts,
				child_table=matched_row.child_table,
				field_name=matched_row.field_name,
			)
		)

	return applicable


def _validate_configuration(doc, dim, child_table, account_fieldname):
	"""Verify the configured Child Table / Field Name actually exist on the
	target DocType, and that Child Table is really a Table field."""

	parent_meta = frappe.get_meta(doc.doctype)

	if child_table:
		child_field = parent_meta.get_field(child_table)
		if not child_field:
			frappe.throw(
				_(
					"Accounting Dimension '<b>{dimension}</b>': Child Table"
					" '<b>{child_table}</b>' does not exist on DocType"
					" '<b>{doctype}</b>'."
				).format(
					dimension=dim.label,
					child_table=child_table,
					doctype=doc.doctype,
				),
				title=_("Invalid Configuration"),
			)

		if child_field.fieldtype != "Table":
			frappe.throw(
				_(
					"Accounting Dimension '<b>{dimension}</b>': '<b>{child_table}</b>'"
					" on DocType '<b>{doctype}</b>' is a '{fieldtype}' field, not a"
					" Table field."
				).format(
					dimension=dim.label,
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
					"Accounting Dimension '<b>{dimension}</b>': Table field"
					" '<b>{child_table}</b>' on DocType '<b>{doctype}</b>' has no"
					" linked Child DocType."
				).format(
					dimension=dim.label,
					child_table=child_table,
					doctype=doc.doctype,
				),
				title=_("Invalid Configuration"),
			)

		child_meta = frappe.get_meta(child_doctype)
		if not child_meta.get_field(account_fieldname):
			frappe.throw(
				_(
					"Accounting Dimension '<b>{dimension}</b>': Field Name"
					" '<b>{field_name}</b>' does not exist on Child DocType"
					" '<b>{child_doctype}</b>'."
				).format(
					dimension=dim.label,
					field_name=account_fieldname,
					child_doctype=child_doctype,
				),
				title=_("Invalid Configuration"),
			)
	else:
		if not parent_meta.get_field(account_fieldname):
			frappe.throw(
				_(
					"Accounting Dimension '<b>{dimension}</b>': Field Name"
					" '<b>{field_name}</b>' does not exist on DocType"
					" '<b>{doctype}</b>'."
				).format(
					dimension=dim.label,
					field_name=account_fieldname,
					doctype=doc.doctype,
				),
				title=_("Invalid Configuration"),
			)


def _validate_dimension_on_parent(doc, dim, account_fieldname):
	"""Validate the dimension field directly on the parent document."""
	parent_account = doc.get(account_fieldname)
	if not parent_account:
		return

	if parent_account not in dim.accounts:
		return

	if not doc.get(dim.fieldname):
		frappe.throw(
			_(
				"<b>{dimension}</b> is mandatory for account <b>{account}</b>"
				" on {doctype}. Please fill in the {dimension} field."
			).format(
				dimension=dim.label,
				account=parent_account,
				doctype=doc.doctype,
			),
			title=_("Missing Accounting Dimension"),
		)


def _validate_dimension_on_child_table(doc, dim, child_table, account_fieldname):
	"""Validate the dimension field on each row of the specified child table."""
	child_rows = doc.get(child_table) or []

	if not isinstance(child_rows, list):
		frappe.throw(
			_(
				"Accounting Dimension '<b>{dimension}</b>': Child Table"
				" '<b>{child_table}</b>' is not a valid table field on DocType"
				" '<b>{doctype}</b>'."
			).format(
				dimension=dim.label,
				child_table=child_table,
				doctype=doc.doctype,
			),
			title=_("Invalid Configuration"),
		)

	for row in child_rows:
		row_account = row.get(account_fieldname)
		if not row_account:
			continue

		if row_account not in dim.accounts:
			continue

		if not row.get(dim.fieldname):
			frappe.throw(
				_(
					"Row {row_no}: <b>{dimension}</b> is mandatory for account"
					" <b>{account}</b>. Please fill in the {dimension} field."
				).format(
					row_no=row.idx,
					dimension=dim.label,
					account=row_account,
				),
				title=_("Missing Accounting Dimension"),
			)


# ---------------------------------------------------------------------------
# Dynamic hook handler (shared by all registered DocTypes)
# ---------------------------------------------------------------------------

def validate(doc, event=None):
	"""Validate that every applicable accounting dimension is filled.

	The child-table and account-field names are read directly from the
	Accounting Dimension's DocType child table — no hard-coded registry.
	"""
	dimensions = _get_dimensions_for_doctype(doc.doctype)
	if not dimensions:
		return

	for dim in dimensions:
		if not dim.accounts:
			continue

		# --- Configuration validation ---
		account_fieldname = dim.field_name
		if not account_fieldname:
			frappe.throw(
				_(
					"Accounting Dimension '<b>{dimension}</b>': 'Field Name'"
					" is not configured for DocType '<b>{doctype}</b>'. Please"
					" set the account field name in the Accounting Dimension"
					" Doctype table."
				).format(dimension=dim.label, doctype=doc.doctype),
				title=_("Missing Configuration"),
			)

		child_table = dim.child_table

		_validate_configuration(doc, dim, child_table, account_fieldname)

		if child_table:
			_validate_dimension_on_child_table(
				doc, dim, child_table, account_fieldname
			)
		else:
			_validate_dimension_on_parent(doc, dim, account_fieldname)
