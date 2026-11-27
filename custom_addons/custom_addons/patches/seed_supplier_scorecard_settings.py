"""Create the Supplier Scorecard Settings from the sample values, plus any missing criteria records."""
import frappe

from custom_addons.custom_addons.doctype.supplier_scorecard_settings.defaults import CRITERIA, apply_defaults


def execute():
	frappe.reload_doc("Custom Addons", "doctype", "supplier_scorecard_setting_criterion")
	frappe.reload_doc("Custom Addons", "doctype", "supplier_scorecard_rating_rule")
	frappe.reload_doc("Custom Addons", "doctype", "supplier_scorecard_band")
	frappe.reload_doc("Custom Addons", "doctype", "supplier_scorecard_settings")
	for name, *_rest in CRITERIA:
		if not frappe.db.exists("Supplier Scorecard Criteria", name):
			frappe.get_doc({"doctype": "Supplier Scorecard Criteria", "criteria_name": name,
				"max_score": 100, "formula": "0", "weight": 0}).insert(ignore_permissions=True)
	settings = frappe.get_doc("Supplier Scorecard Settings")
	if not settings.criteria:
		apply_defaults(settings)
		settings.save(ignore_permissions=True)
