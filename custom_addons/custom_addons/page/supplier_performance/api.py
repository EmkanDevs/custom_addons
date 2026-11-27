"""Whitelisted API of the Supplier Performance Dashboard (page supplier-performance)."""
import frappe
from frappe import _
from frappe.utils import add_months, get_first_day, today

from custom_addons.custom_addons.page.supplier_performance import cohort, dashboard, export, scope, settings
from custom_addons.custom_addons.page.supplier_performance import filters as fl
from custom_addons.custom_addons.page.supplier_performance.evaluation import Evaluation
from custom_addons.custom_addons.page.supplier_performance.scoring import comment


@frappe.whitelist()
def get_page_context():
	scope.require_view()
	rules = settings.get()
	first = get_first_day(today())
	months = [fl.month_key(add_months(first, -i)) for i in range(rules.month_options)]
	return {
		"company": fl.parse({}).company,
		"default_month": fl.default_month(),
		"scale": rules.scale,
		"months": [{"value": m, "label": dashboard.month_label(m)} for m in months],
	}


@frappe.whitelist()
def get_dashboard(filters=None):
	scope.require_view()
	return dashboard.build(fl.parse(filters))


@frappe.whitelist()
def get_supplier_detail(filters=None, supplier=None):
	"""The selected month's breakdown for one supplier. The report filters still apply."""
	scope.require_view()
	f = fl.parse(filters)
	f.supplier = fl.link("Supplier", supplier)
	ev = Evaluation(f)
	if not f.supplier or not cohort.suppliers(f, ev.active(f.month)):
		frappe.throw(_("Supplier {0} is not in this report.").format(supplier), frappe.PermissionError)
	result = ev.result(f.supplier)
	info = frappe.db.get_value("Supplier", f.supplier, ["supplier_name", "supplier_group"], as_dict=True)
	return {
		**result,
		"supplier": f.supplier,
		"supplier_name": info.supplier_name or f.supplier,
		"supplier_group": info.supplier_group or "",
		"month_label": dashboard.month_label(f.month),
		"action": ev.settings.band(result["score"])[1],
		"comment": comment(result, ev.settings),
		"criteria": _permitted_evidence(ev.detail(f.supplier)),
	}


@frappe.whitelist(methods=["POST"])
def export_excel(filters=None, sort=None):
	scope.require_view()
	name, content = export.build(fl.parse(filters), sort)
	frappe.response["filename"] = name
	frappe.response["filecontent"] = content
	frappe.response["type"] = "download"


def _permitted_evidence(rows):
	"""List only source documents the user may open."""
	for row in rows:
		evidence = row.get("evidence")
		if evidence:
			readable = frappe.has_permission(evidence["doctype"], "read")
			evidence["docs"] = evidence["docs"][:settings.get().max_evidence_docs] if readable else []
	return rows
