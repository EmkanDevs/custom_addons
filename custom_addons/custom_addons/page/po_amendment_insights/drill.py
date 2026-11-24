"""Side panel: logs behind a number, and one log's summary."""
import frappe
from frappe import _
from frappe.query_builder.functions import Count
from pypika import Order

from custom_addons.custom_addons.page.po_amendment_insights import history
from custom_addons.custom_addons.page.po_amendment_insights.filters import (
	CLOSED_STATES, LOG, PENDING_STATES, MonthOf, scoped, state_col,
)
from custom_addons.custom_addons.page.po_amendment_insights.root_cause import IGNORED_FIELDS

LIST_FIELDS = (
	"name", "log_date", "cancelled_po_number", "new_po_number", "original_supplier",
	"total_value_difference", "comparison_value_status", "original_currency", "implementation_status",
)
NOT_SET = "Not set"


def logs(f, key, limit, offset):
	L, q = scoped(f)
	q = _apply_key(q, L, f, key or "all")
	total = q.select(Count(L.name)).run()[0][0]
	rows = (
		q.select(*[getattr(L, c) for c in LIST_FIELDS], state_col(L).as_("state"))
		.orderby(L.log_date, order=Order.desc).orderby(L.name, order=Order.desc).limit(limit).offset(offset).run(as_dict=True)
	)
	return {"rows": rows, "total": total}


def _apply_key(q, L, f, key):
	kind, _sep, value = key.partition(":")
	if kind == "all":
		return q
	if kind == "open":
		return q.where(state_col(L).notin(CLOSED_STATES))
	if kind == "pending":
		return q.where(state_col(L).isin(PENDING_STATES))
	if kind in ("state", "gate"):
		return q.where(state_col(L) == value)
	if kind == "increased":
		return q.where(L.comparison_value_status == "Comparable").where(L.total_value_difference > 0)
	if kind == "reduced":
		return q.where(L.comparison_value_status == "Comparable").where(L.total_value_difference < 0)
	if kind == "benefit":
		return q.where(L.rate_benefit_status == "Complete")
	if kind == "gap":
		return q.where(L.po_date_gap_days.isnotnull())
	if kind == "month":
		return q.where(MonthOf(L.log_date, "%Y-%m") == value)
	if kind == "field":
		return q.where(L.name.isin(_with_changed_field(value)))
	column = {"impl": "implementation_status", "type": "amendment_type", "reason": "amendment_reason_category",
		"dept": "requesting_department", "user": "requested_by", "supplier": "original_supplier"}.get(kind)
	if not column:
		frappe.throw(_("Unknown drill-down: {0}").format(key))
	return _equals(q, L, column, value, "Under Review" if kind == "impl" else None)


def _equals(q, L, column, value, default):
	if value == NOT_SET or (default and value == default):
		return q.where(getattr(L, column).isnull() | (getattr(L, column) == "") | (getattr(L, column) == (default or "")))
	return q.where(getattr(L, column) == value)


def _with_changed_field(label):
	H = frappe.qb.DocType("PO Amendment Header Comparison")
	return frappe.qb.from_(H).select(H.parent).where(H.parenttype == LOG).where(H.is_different == 1).where(H.field_label == label)


def summary(name):
	if not frappe.has_permission(LOG, "read", name):
		frappe.throw(_("You are not permitted to read this log."), frappe.PermissionError)
	doc = frappe.get_doc(LOG, name)
	changed = [
		{"field": r.field_label, "original": r.original_value, "replacement": r.replacement_value}
		for r in doc.header_comparison if r.is_different and r.field_label not in IGNORED_FIELDS
	]
	return {
		"name": doc.name, "log_date": doc.log_date, "stale": doc.comparison_stale,
		"state": doc.get("workflow_state") or "Draft", "implementation_status": doc.implementation_status,
		"original_po": doc.cancelled_po_number, "replacement_po": doc.new_po_number,
		"original_supplier": doc.original_supplier, "replacement_supplier": doc.replacement_supplier,
		"project": doc.get("project"), "requested_by": doc.requested_by, "department": doc.requesting_department,
		"amendment_type": doc.amendment_type, "reason": doc.amendment_reason_category,
		"currency": doc.replacement_currency, "value_status": doc.comparison_value_status,
		"value_difference": doc.total_value_difference, "rate_benefit": doc.rate_benefit,
		"rate_benefit_status": doc.rate_benefit_status, "po_date_gap_days": doc.get("po_date_gap_days"),
		"changed_fields": changed, "justification": doc.detailed_justification,
		"business_impact": doc.business_impact, "risk": doc.risk__impact_assessment,
		"action": doc.corrective__preventive_action,
		"history": [{"state": r.workflow_state, "user": r.username, "time": r.modification_time} for r in history.for_log(name)],
	}
