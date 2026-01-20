import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, getdate, nowdate

@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.run_method("set_missing_values")
		target.run_method("get_schedule_dates")
		target.run_method("calculate_taxes_and_totals")

	def update_item(obj, target, source_parent):
		target.stock_qty = flt(obj.qty) * flt(obj.conversion_factor)

	valid_items_found = []

	def item_condition(d):
		# Assuming d.request_for_quotation is the field linking to RFQ
		if not d.request_for_quotation:
			return False

		# Check if a Bid Tabulation Discussion exists for this RFQ
		has_bid_tab = frappe.db.exists("Bid Tabulation Discussion", {
			"reference_rfq": d.request_for_quotation
		})

		is_valid = bool(has_bid_tab)
		if is_valid:
			valid_items_found.append(d.name)

		return is_valid

	doclist = get_mapped_doc(
		"Supplier Quotation",
		source_name,
		{
			"Supplier Quotation": {
				"doctype": "Purchase Order",
				"field_no_map": ["transaction_date"],
				"validation": {
					"docstatus": ["=", 1],
				},
			},
			"Supplier Quotation Item": {
				"doctype": "Purchase Order Item",
				"field_map": [
					["name", "supplier_quotation_item"],
					["parent", "supplier_quotation"],
					["material_request", "material_request"],
					["material_request_item", "material_request_item"],
					["sales_order", "sales_order"],
				],
				"postprocess": update_item,
				"condition": item_condition,
			},
			"Purchase Taxes and Charges": {
				"doctype": "Purchase Taxes and Charges",
			},
		},
		target_doc,
		set_missing_values,
	)

	if not valid_items_found:
		frappe.throw("Cannot create Purchase Order: No linked Request for Quotation or Bid Tabulation Discussion found for any items.")

	return doclist
