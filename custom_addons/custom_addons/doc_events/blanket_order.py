import frappe
import json
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.query_builder.functions import Sum
from frappe.utils import flt, nowdate

from erpnext.stock.doctype.item.item import get_item_defaults


def is_direct_purchase_invoice_item(item_code):
	return frappe.db.get_value(
		"Item",
		item_code,
		["is_stock_item", "is_fixed_asset", "blanket_order_po_exemption"],
		as_dict=True,
	)


def update_direct_purchase_invoice_item(source, target, source_parent):
	# Qty is seeded from the full blanket line qty as a convenience only, and is
	# freely editable by the user to the actual consumed amount. No remaining-qty
	# subtraction, no cap — per locked spec decision #1.
	target.qty = source.get("qty")
	target.rate = source.get("rate")
	target.blanket_order = source_parent.name
	target.blanket_order_item = source.name

	item = get_item_defaults(target.item_code, source_parent.company)
	if item:
		target.item_name = item.get("item_name")
		target.description = item.get("description")
		target.uom = item.get("stock_uom")
		target.expense_account = item.get("expense_account")

	if not target.expense_account:
		# Fall back to the company's default expense account — same fallback
		# core itself would use for a non-stock item with no Item Defaults
		# entry for this company.
		target.expense_account = frappe.get_cached_value(
			"Company", source_parent.company, "default_expense_account"
		)


@frappe.whitelist()
def make_direct_purchase_invoice(source_name, target_doc=None, args=None):
	if isinstance(args, str):
		args = json.loads(args) if args else {}
	args = frappe._dict(args or {})

	selected_child_names = None
	filtered_children = args.get("filtered_children")
	if filtered_children:
		# filtered_children is a flat list of Blanket Order Item row names
		# (strings), not a list of dicts — handle both defensively.
		selected_child_names = {
			(row.get("name") if isinstance(row, dict) else row)
			for row in filtered_children
		}

	def update_doc(source_doc, target_doc, source_parent):
		target_doc.update_stock = 0
		target_doc.posting_date = nowdate()
		if source_doc.get("custom_default_purchase_taxes_template"):
			target_doc.taxes_and_charges = source_doc.get("custom_default_purchase_taxes_template")

	def can_map_item(item):
		if selected_child_names is not None and item.name not in selected_child_names:
			return False
		item_details = is_direct_purchase_invoice_item(item.item_code)
		return (
			item_details
			and not item_details.is_stock_item
			and not item_details.is_fixed_asset
			and item_details.blanket_order_po_exemption
		)

	doc = frappe.get_doc("Blanket Order", source_name)
	if doc.blanket_order_type != "Purchasing" or not doc.get("blanket_order_po_exemption"):
		frappe.throw(_("Direct Purchase Invoice is allowed only for eligible Purchasing Blanket Orders."))

	target_doc = get_mapped_doc(
		"Blanket Order",
		source_name,
		{
			"Blanket Order": {
				"doctype": "Purchase Invoice",
				"field_map": {
					"supplier": "supplier",
					"supplier_name": "supplier_name",
					"company": "company",
				},
				"postprocess": update_doc,
			},
			"Blanket Order Item": {
				"doctype": "Purchase Invoice Item",
				"field_map": {
					"rate": "blanket_order_rate",
					"parent": "blanket_order",
					"name": "blanket_order_item",
				},
				"postprocess": update_direct_purchase_invoice_item,
				"condition": can_map_item,
			},
		},
		target_doc,
	)

	if not target_doc.get("items"):
		frappe.throw(
			_(
				"No eligible service items were selected for Direct Purchase Invoice. "
				"Please check that the selected items are non-stock, non-asset, and PO-exempt."
			)
		)

	target_doc.set_missing_values()
	return target_doc

def update_ordered_qty_from_purchase_invoice(blanket_order):
	"""Informational only — see note in the PI doc_events module."""
	trans = frappe.qb.DocType("Purchase Invoice")
	trans_item = frappe.qb.DocType("Purchase Invoice Item")

	item_ordered_qty = frappe._dict(
		(
			frappe.qb.from_(trans_item)
			.from_(trans)
			.select(trans_item.blanket_order_item, Sum(trans_item.qty).as_("qty"))
			.where(
				(trans.name == trans_item.parent)
				& (trans_item.blanket_order == blanket_order)
				& (trans.docstatus == 1)
			)
			.groupby(trans_item.blanket_order_item)
		).run()
	)

	bo_doc = frappe.get_doc("Blanket Order", blanket_order)
	for d in bo_doc.items:
		item_details = is_direct_purchase_invoice_item(d.item_code)
		if (
			item_details
			and not item_details.is_stock_item
			and not item_details.is_fixed_asset
			and item_details.blanket_order_po_exemption
		):
			d.db_set("ordered_qty", item_ordered_qty.get(d.name, 0))


def update_item(source, target, source_parent):
	target.against_blanket_order = 1
	target.blanket_order_item = source.name


def on_submit(doc, method):
	if doc.blanket_order_type != "Purchasing":
		return

	# --- Fix: a PO-exempt blanket must never auto-spawn a Purchase Order.
	# The exemption's whole point is to skip the PO; otherwise the "hidden PO
	# button" in the client script is cosmetic while a PO gets created anyway.
	if doc.get("blanket_order_po_exemption"):
		return

	try:
		po = get_mapped_doc(
			"Blanket Order",
			doc.name,
			{
				"Blanket Order": {
					"doctype": "Purchase Order",
					"field_map": {
						"name": "blanket_order",
						"supplier": "supplier",
						"to_date": "schedule_date",
						"from_date": "transaction_date",
						"company": "company",
					},
				},
				"Blanket Order Item": {
					"doctype": "Purchase Order Item",
					"field_map": {
						"name": "blanket_order_item",
						"rate": "blanket_order_rate",
						"item_code": "item_code",
						"qty": "qty",
						"rate": "rate",
						"uom": "uom",
					},
					"postprocess": update_item,
				},
			},
		)

		for item in po.items:
			item.against_blanket_order = 1

		po.flags.ignore_permissions = True
		po.flags.ignore_mandatory = True

		po.insert()
		po.submit()

		frappe.msgprint(
			msg=f'Purchase Order <b><a href="/app/purchase-order/{po.name}">{po.name}</a></b> created successfully.',
			title="Purchase Order Created",
			indicator="green",
			alert=True,
		)

	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			"Blanket Order PO Creation Failed",
		)
		frappe.throw("Failed to create Purchase Order. Check Error Log for details.")