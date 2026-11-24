"""Whitelisted API of the PO Amendment Insights Dashboard (page po-amendment-insights)."""
import frappe

from custom_addons.custom_addons.page.po_amendment_insights import approvals, drill, export, overview, root_cause, scope
from custom_addons.custom_addons.page.po_amendment_insights import filters as fl


@frappe.whitelist()
def get_page_context():
	scope.require_view()
	meta = frappe.get_meta(fl.LOG)
	return {
		"is_manager": scope.is_manager(),
		"default_approver": scope.default_approver(),
		"amendment_types": [o for o in (meta.get_field("amendment_type").options or "").split("\n") if o],
		"states": ["Draft", *fl.GATE_STATES, "Approved", "Rejected"],
		"currency": _currency(),
	}


@frappe.whitelist()
def get_overview(filters=None):
	scope.require_view()
	return overview.build(fl.parse(filters))


@frappe.whitelist()
def get_approvals(filters=None, approver=None, limit=10, offset=0):
	scope.require_view()
	return approvals.build(fl.parse(filters), approver or None, _int(limit, 10), _int(offset))


@frappe.whitelist()
def get_root_cause(filters=None, limit=10, offset=0):
	scope.require_manager()
	return root_cause.build(fl.parse(filters), _int(limit, 10), _int(offset))


@frappe.whitelist()
def get_drill(filters=None, key="all", limit=10, offset=0):
	scope.require_view()
	return drill.logs(fl.parse(filters), key, _int(limit, 10), _int(offset))


@frappe.whitelist()
def get_log_summary(name):
	scope.require_view()
	return drill.summary(name)


@frappe.whitelist(methods=["POST"])
def export_excel(filters=None):
	scope.require_manager()
	name, content = export.build(fl.parse(filters))
	frappe.response["filename"] = name
	frappe.response["filecontent"] = content
	frappe.response["type"] = "binary"


def _int(value, default=0):
	try:
		return max(0, min(int(value), 1000))
	except (TypeError, ValueError):
		return default


def _currency():
	company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
	return frappe.get_cached_value("Company", company, "default_currency") if company else None
