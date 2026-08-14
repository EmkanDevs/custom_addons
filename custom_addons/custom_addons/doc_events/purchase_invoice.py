import frappe
from frappe import _
from frappe.utils import flt, getdate

from custom_addons.custom_addons.doc_events.blanket_order import (
	update_ordered_qty_from_purchase_invoice,
)


def validate(self, method):
	if not has_direct_purchase_invoice_blanket_order_items(self):
		return

	set_missing_direct_purchase_invoice_blanket_order_items(self)
	self.set_advances()
	for row in self.advances:
		row.allocated_amount = self.total

	validate_against_direct_purchase_invoice_blanket_order(self)


def is_direct_blanket_order_row(item):
	"""True only for rows with no originating Purchase Order -
	i.e. genuinely 'direct' invoices against a Blanket Order."""
	return (item.get("blanket_order") or item.get("blanket_order_item")) and not item.get("purchase_order")


def has_direct_purchase_invoice_blanket_order_items(doc):
	return any(is_direct_blanket_order_row(item) for item in doc.get("items"))


def set_missing_direct_purchase_invoice_blanket_order_items(doc):
	for item in doc.get("items"):
		if not is_direct_blanket_order_row(item):
			continue
		if item.get("blanket_order") and not item.get("blanket_order_item"):
			blanket_order_items = frappe.get_all(
				"Blanket Order Item",
				filters={"parent": item.blanket_order, "item_code": item.item_code},
				pluck="name",
				limit=2,
			)
			if len(blanket_order_items) == 1:
				item.blanket_order_item = blanket_order_items[0]

	# Keep the header flag in sync regardless of entry point (picker, button, or API)
	if any(is_direct_blanket_order_row(i) for i in doc.get("items")):
		doc.is_blanket_invoice = 1


def validate_against_direct_purchase_invoice_blanket_order(order_doc):
	"""Enforces the hard guards from spec section 6.7:
	1. Strict one blanket per PI (rule 8 / AC2)
	2. Every direct-flow line must not be a stock item / fixed asset, and must be PO-exempt
	3. Rate is locked to the blanket line rate (rule 5 / AC4)
	4. Posting date must fall within the blanket's validity period (rule 6 / AC6)
	5. Supplier must match the blanket's supplier (rule 7 / AC9)

	Deliberately NOT enforced (per locked v0.3 decisions #1/#2): no quantity cap,
	no amount cap, no allowance/tolerance of any kind.
	"""
	direct_rows = [item for item in order_doc.get("items") if is_direct_blanket_order_row(item)]
	if not direct_rows:
		return

	# --- Rule 8: strict one blanket per PI ---
	blanket_orders_on_doc = {item.blanket_order for item in direct_rows if item.get("blanket_order")}
	if len(blanket_orders_on_doc) > 1:
		frappe.throw(
			_("A Purchase Invoice may be linked to only one Blanket Order. Found: {0}").format(
				", ".join(blanket_orders_on_doc)
			)
		)

	order_data = {}
	for item in direct_rows:
		if not item.get("blanket_order") or not item.get("blanket_order_item"):
			frappe.throw(
				_("Row {0}: Blanket Order and Blanket Order Item are both required.").format(item.idx)
			)

		# --- Eligibility: is_stock_item, is_fixed_asset, blanket_order_po_exemption ---
		item_details = frappe.db.get_value(
			"Item",
			item.item_code,
			["is_stock_item", "is_fixed_asset", "blanket_order_po_exemption"],
			as_dict=True,
		)
		if (
			not item_details
			or item_details.is_stock_item
			or item_details.is_fixed_asset
			or not item_details.blanket_order_po_exemption
		):
			frappe.throw(
				_(
					"Row {0}: Item {1} is not eligible for Direct Purchase Invoice from Blanket Order."
				).format(item.idx, frappe.bold(item.item_code))
			)

		blanket_order_item = frappe.db.get_value(
			"Blanket Order Item", item.blanket_order_item, ["parent", "item_code", "rate"], as_dict=True
		)
		if (
			not blanket_order_item
			or blanket_order_item.parent != item.blanket_order
			or blanket_order_item.item_code != item.item_code
		):
			frappe.throw(
				_("Row {0}: Blanket Order Item does not match the Purchase Invoice Item.").format(
					item.idx
				)
			)

		# --- Rate lock: re-assert server-side, never trust the client read-only alone ---
		if flt(item.rate) != flt(blanket_order_item.rate):
			frappe.throw(
				_("Row {0}: Rate must match the Blanket Order rate of {1}.").format(
					item.idx, blanket_order_item.rate
				)
			)

		order_data.setdefault(item.blanket_order, []).append(item.blanket_order_item)

	# --- Per-blanket checks: type, exemption flag, supplier, validity period ---
	for bo_name in order_data:
		bo_doc = frappe.get_doc("Blanket Order", bo_name)

		if bo_doc.blanket_order_type != "Purchasing" or not bo_doc.get("blanket_order_po_exemption"):
			frappe.throw(_("Blanket Order {0} is not enabled for Direct Purchase Invoice.").format(bo_name))

		if bo_doc.supplier != order_doc.supplier:
			frappe.throw(
				_("Supplier on the Purchase Invoice must match the Blanket Order {0} supplier ({1}).").format(
					bo_name, bo_doc.supplier
				)
			)

		posting_date = getdate(order_doc.posting_date)
		if bo_doc.from_date and posting_date < getdate(bo_doc.from_date):
			frappe.throw(
				_("Posting date is before Blanket Order {0}'s validity start ({1}).").format(
					bo_name, bo_doc.from_date
				)
			)
		if bo_doc.to_date and posting_date > getdate(bo_doc.to_date):
			frappe.throw(
				_("Posting date is after Blanket Order {0}'s validity end ({1}).").format(
					bo_name, bo_doc.to_date
				)
			)


def on_submit(doc, method):
	update_direct_purchase_invoice_ordered_qty(doc)


def on_cancel(doc, method):
	update_direct_purchase_invoice_ordered_qty(doc)


def update_direct_purchase_invoice_ordered_qty(doc):
	"""Kept for audit/visibility on the Blanket Order Item's native `ordered_qty` field only.
	Per locked spec decision #1, this is informational — it is never used to cap or
	block invoicing, since services have no quantity ceiling."""
	set_missing_direct_purchase_invoice_blanket_order_items(doc)

	for item in doc.get("items"):
		if not is_direct_blanket_order_row(item):
			continue
		if item.get("blanket_order") and item.get("blanket_order_item"):
			item.db_set("blanket_order_item", item.blanket_order_item)

	blanket_orders = {
		item.blanket_order for item in doc.get("items") if is_direct_blanket_order_row(item)
	}

	for blanket_order in blanket_orders:
		update_ordered_qty_from_purchase_invoice(blanket_order)


@frappe.whitelist()
def repair_direct_purchase_invoice_blanket_order_links(purchase_invoice):
	doc = frappe.get_doc("Purchase Invoice", purchase_invoice)
	update_direct_purchase_invoice_ordered_qty(doc)