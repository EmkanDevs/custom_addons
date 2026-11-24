# Copyright (c) 2026, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, flt, nowdate

# PENDING_STATES for workflow gates
PENDING_STATES = ("Pending Approval", "Pending Technical/Quality", "Pending Procurement", "Pending Finance")


def execute(filters=None):
	filters = frappe._dict(filters or {})
	f = {}
	for k in ("company", "workflow_status", "original_supplier", "replacement_supplier", "cancelled_po_number", "new_po_number", "amendment_reason_category"):
		if filters.get(k):
			f[k] = filters[k]
	if filters.from_date and filters.to_date:
		f["log_date"] = ["between", [filters.from_date, filters.to_date]]
	elif filters.from_date:
		f["log_date"] = [">=", filters.from_date]
	elif filters.to_date:
		f["log_date"] = ["<=", filters.to_date]

	# get_list applies role + company/user permissions
	logs = frappe.get_list(
		"PO Amendment Log", filters=f, order_by="log_date desc, creation desc", limit_page_length=0,
		fields=["name", "log_date", "company", "workflow_status", "docstatus", "cancelled_po_number", "new_po_number",
			"original_supplier", "replacement_supplier", "amendment_reason_category", "approver", "approval_datetime",
			"pending_since", "original_currency", "replacement_currency", "comparison_value_status", "total_value_difference",
			"rate_benefit", "rate_benefit_status", "non_rate_value_change", "mr_comparison_status", "comparison_stale",
			"items_unresolved", "comparison_hash"],
	)
	data = []
	for l in logs:
		has_snap = bool(l.comparison_hash)
		money_ok = has_snap and l.comparison_value_status == "Comparable"
		rate_ok = money_ok and l.rate_benefit_status != "Not Comparable"
		l.comparison_available = "Yes" if has_snap else "No"
		l.total_value_difference = l.total_value_difference if money_ok else None   # None renders as N/A
		l.rate_benefit = l.rate_benefit if rate_ok else None
		l.non_rate_value_change = l.non_rate_value_change if rate_ok else None
		l.days_pending = date_diff(nowdate(), l.pending_since) if (l.workflow_status in PENDING_STATES and l.pending_since) else None
		data.append(l)

	columns = [
		{"label": _("Log"), "fieldname": "name", "fieldtype": "Link", "options": "PO Amendment Log", "width": 150},
		{"label": _("Log Date"), "fieldname": "log_date", "fieldtype": "Date", "width": 95},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 130},
		{"label": _("Status"), "fieldname": "workflow_status", "fieldtype": "Data", "width": 110},
		{"label": _("Original PO"), "fieldname": "cancelled_po_number", "fieldtype": "Link", "options": "Purchase Order", "width": 150},
		{"label": _("Replacement PO"), "fieldname": "new_po_number", "fieldtype": "Link", "options": "Purchase Order", "width": 150},
		{"label": _("Original Supplier"), "fieldname": "original_supplier", "fieldtype": "Link", "options": "Supplier", "width": 130},
		{"label": _("Replacement Supplier"), "fieldname": "replacement_supplier", "fieldtype": "Link", "options": "Supplier", "width": 130},
		{"label": _("Reason"), "fieldname": "amendment_reason_category", "fieldtype": "Data", "width": 140},
		{"label": _("Approver"), "fieldname": "approver", "fieldtype": "Link", "options": "User", "width": 130},
		{"label": _("Approved On"), "fieldname": "approval_datetime", "fieldtype": "Datetime", "width": 150},
		{"label": _("Pending Since"), "fieldname": "pending_since", "fieldtype": "Datetime", "width": 150},
		{"label": _("Days Pending"), "fieldname": "days_pending", "fieldtype": "Int", "width": 90},
		{"label": _("Original Currency"), "fieldname": "original_currency", "fieldtype": "Link", "options": "Currency", "width": 80},
		{"label": _("Replacement Currency"), "fieldname": "replacement_currency", "fieldtype": "Link", "options": "Currency", "width": 80},
		{"label": _("Comparison Available"), "fieldname": "comparison_available", "fieldtype": "Data", "width": 90},
		{"label": _("Total Value Difference"), "fieldname": "total_value_difference", "fieldtype": "Float", "width": 130},
		{"label": _("Rate Benefit"), "fieldname": "rate_benefit", "fieldtype": "Float", "width": 110},
		{"label": _("Rate Benefit Coverage"), "fieldname": "rate_benefit_status", "fieldtype": "Data", "width": 110},
		{"label": _("Other Commitment Change"), "fieldname": "non_rate_value_change", "fieldtype": "Float", "width": 130},
		{"label": _("MR Status"), "fieldname": "mr_comparison_status", "fieldtype": "Data", "width": 90},
		{"label": _("Unresolved Rows"), "fieldname": "items_unresolved", "fieldtype": "Int", "width": 90},
		{"label": _("Out of Date"), "fieldname": "comparison_stale", "fieldtype": "Check", "width": 80},
	]
	return columns, data, None, None, _summary(data)


def _summary(rows):
	approved = [r for r in rows if r.workflow_status == "Approved"]
	by_cur_move, by_cur_rate, excluded = {}, {}, 0
	for r in approved:
		if r.total_value_difference is None:
			excluded += 1
			continue
		by_cur_move[r.replacement_currency] = by_cur_move.get(r.replacement_currency, 0) + flt(r.total_value_difference)
		if r.rate_benefit is not None:
			by_cur_rate[r.replacement_currency] = by_cur_rate.get(r.replacement_currency, 0) + flt(r.rate_benefit)
	fmt = lambda d: "; ".join("{0} {1:,.2f}".format(k, v) for k, v in sorted(d.items())) or "-"
	return [
		{"value": len(approved), "label": _("Approved Change Events"), "datatype": "Int", "indicator": "Green"},
		{"value": len([r for r in approved if r.original_supplier != r.replacement_supplier]), "label": _("Approved Supplier Changes"), "datatype": "Int"},
		{"value": len([r for r in approved if r.mr_comparison_status in ("Mismatch", "Missing")]), "label": _("Approved MR Exceptions"), "datatype": "Int", "indicator": "Orange"},
		{"value": len([r for r in rows if r.workflow_status in PENDING_STATES]), "label": _("Pending Approval"), "datatype": "Int", "indicator": "Blue"},
		{"value": fmt(by_cur_move), "label": _("Commitment Movement by Currency (approved, comparable)"), "datatype": "Data"},
		{"value": fmt(by_cur_rate), "label": _("Matched Rate Benefit by Currency (not realised savings)"), "datatype": "Data"},
		{"value": excluded, "label": _("Approved Logs Excluded (currency mismatch)"), "datatype": "Int"},
	]

