"""Project and PO date gap of a log, read from its two POs. Kept out of the comparison engine."""
import frappe
from frappe.utils import date_diff

PO = "Purchase Order"


def apply(doc):
	"""Set project and po_date_gap_days on a log from its linked POs. Does not save."""
	doc.project = project_of(doc.cancelled_po_number)
	doc.po_date_gap_days = date_gap(doc.cancelled_po_number, doc.new_po_number)


def project_of(po):
	"""Header project when the PO has one, else the first item's project."""
	if not po:
		return None
	header = frappe.db.get_value(PO, po, "project")
	if header:
		return header
	return frappe.db.get_value(
		"Purchase Order Item", {"parent": po, "parenttype": PO, "project": ["is", "set"]}, "project", order_by="idx"
	)


def date_gap(original_po, replacement_po):
	"""Replacement PO date minus Original PO date, in days."""
	if not (original_po and replacement_po):
		return None
	original = frappe.db.get_value(PO, original_po, "transaction_date")
	replacement = frappe.db.get_value(PO, replacement_po, "transaction_date")
	return date_diff(replacement, original) if original and replacement else None
