    
import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt
import json
def validate(self, method):
    if not self.petty_cash_request:
        return
    total = 0
    purchase_receipt_total = 0
    expense_claim_total = 0

    purchase_receipt = frappe.get_all(
        "Purchase Receipt",
        filters={"petty_cash_request": self.petty_cash_request},
        fields=["name"]
    )
    for row in purchase_receipt:
        doc = frappe.get_doc("Purchase Receipt", row.name)
        purchase_receipt_total += doc.grand_total
        
    expense_claim = frappe.get_all(
        "Expense Claim",
        filters={"petty_cash_request": self.petty_cash_request},
        fields=["name"]
    )
    for row in expense_claim:
        doc = frappe.get_doc("Expense Claim", row.name)
        expense_claim_total += doc.grand_total

    total = purchase_receipt_total + expense_claim_total
    petty_cash = frappe.get_doc("Petty Cash Request",self.petty_cash_request)
    limit = petty_cash.received_amount or petty_cash.required_amount
    if total >= limit:
        frappe.msgprint(
            f"Validation Error: The total amount for Petty Cash Request '{self.petty_cash_request}' has exceeded the limit of {limit}. "
            f"Current Total: {total}. Please review your claims."
        )
def after_insert(self,method):
    if self.petty_cash_request:
        self.is_petty_cash = 1
        self.petty_cash_employee = frappe.db.get_value("Petty Cash Request",self.petty_cash_request,"employee")
def on_cancel(self,method):
    self.db_set("petty_cash_request",None)

@frappe.whitelist()
def make_purchase_receipt_from_multiple_mr(material_requests, supplier):
    """
    Create Purchase Receipt items from multiple Material Requests
    Args:
        material_requests: List of Material Request names
        supplier: Supplier name
    """
    if isinstance(material_requests, str):
        material_requests = json.loads(material_requests)
        
    items = []
    for mr in material_requests:
        mr_items = get_material_request_items(mr, supplier)
        items.extend(mr_items)
        
    return items
    
def get_material_request_items(material_request, supplier):
    """Fetch items from a single Material Request"""
    mr_doc = frappe.get_doc("Material Request", material_request)
    items = []
    
    for d in mr_doc.items:
        # if d.ordered_qty < d.qty and not d.purchase_receipt:
        item_data = {
            "item_code": d.item_code,
            "item_name": d.item_name,
            "description": d.description,
            "warehouse": d.warehouse,
            "material_request": material_request,
            "material_request_item": d.name,
            "qty": d.qty,
            "stock_uom": d.stock_uom,
            "uom": d.uom,
            "conversion_factor": d.conversion_factor,
            "rate": d.rate,
            "schedule_date": d.schedule_date
        }
        items.append(item_data)
            
    return items