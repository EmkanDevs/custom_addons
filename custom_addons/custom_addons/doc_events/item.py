import frappe
from frappe import _

def validate_stock_blanket_exclusivity(doc, method):
    if doc.is_stock_item and doc.blanket_order_po_exemption:
        frappe.throw(
            _("You can only enable either <b>Maintain Stock</b> or <b>Blanket Order PO Exemption</b>, not both."),
            title=_("Invalid Selection")
        )