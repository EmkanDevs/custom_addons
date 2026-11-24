# Copyright (c) 2026, Finbyz and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _

# PENDING_STATES for workflow gates
PENDING_STATES = ("Pending Approval", "Pending Technical/Quality", "Pending Procurement", "Pending Finance")


def execute(filters=None):
	filters = frappe._dict(filters or {})
	f = {"docstatus": 2}
	for k in ("company", "supplier"):
		if filters.get(k):
			f[k] = filters[k]
	if filters.from_date and filters.to_date:
		f["transaction_date"] = ["between", [filters.from_date, filters.to_date]]
	elif filters.from_date:
		f["transaction_date"] = [">=", filters.from_date]
	elif filters.to_date:
		f["transaction_date"] = ["<=", filters.to_date]

	pos = frappe.get_list("Purchase Order", filters=f, fields=["name", "company", "supplier", "transaction_date", "grand_total", "currency"],
		order_by="transaction_date desc", limit_page_length=0)   # permission-aware
	names = [p.name for p in pos]
	logs = {}
	if names:
		for l in frappe.get_all("PO Amendment Log", filters={"cancelled_po_number": ["in", names], "docstatus": ["<", 2]},
				fields=["name", "cancelled_po_number", "workflow_status", "new_po_number"]):
			logs.setdefault(l.cancelled_po_number, []).append(l)

	rank = ["Approved", *PENDING_STATES, "Draft", "Rejected"]
	data = []
	for p in pos:
		ls = logs.get(p.name, [])
		statuses = {l.workflow_status for l in ls}
		if "Approved" in statuses:
			continue
		p.log_status = next((s for s in rank if s in statuses), "No Log")
		p.logs = ", ".join("{0} ({1})".format(l.name, l.workflow_status) for l in ls)
		p.cancelled_on = _cancelled_on(p.name)
		data.append(p)
	if filters.log_status:
		data = [d for d in data if d.log_status == filters.log_status]

	columns = [
		{"label": _("Cancelled PO"), "fieldname": "name", "fieldtype": "Link", "options": "Purchase Order", "width": 160},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 130},
		{"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 140},
		{"label": _("PO Date"), "fieldname": "transaction_date", "fieldtype": "Date", "width": 95},
		{"label": _("Cancelled On (audit log)"), "fieldname": "cancelled_on", "fieldtype": "Datetime", "width": 160},
		{"label": _("Currency"), "fieldname": "currency", "fieldtype": "Link", "options": "Currency", "width": 80},
		{"label": _("Grand Total"), "fieldname": "grand_total", "fieldtype": "Currency", "options": "currency", "width": 120},
		{"label": _("Log Status"), "fieldname": "log_status", "fieldtype": "Data", "width": 120},
		{"label": _("Logs"), "fieldname": "logs", "fieldtype": "Data", "width": 300},
	]
	message = _("A cancelled PO without a replacement is a review exception, not automatically a non-compliance.")
	return columns, data, message


def _cancelled_on(po):
	"""Only from the audited Version log (docstatus 1 -> 2); blank when it cannot be established."""
	for v in frappe.get_all("Version", filters={"ref_doctype": "Purchase Order", "docname": po}, fields=["data", "creation"], order_by="creation desc", limit_page_length=20):
		try:
			for ch in (json.loads(v.data).get("changed") or []):
				if ch[0] == "docstatus" and int(ch[2] or 0) == 2:
					return v.creation
		except Exception:
			continue
	return None
