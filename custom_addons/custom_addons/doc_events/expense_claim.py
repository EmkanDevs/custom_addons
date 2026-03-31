    
import frappe
import json
from frappe.utils import flt

def validate(self, method):
    validate_petty_cash(self,method)
    calculate_expense_tax(self,method)

def validate_petty_cash(self, method):

    if not self.petty_cash_request:
        return

    purchase_receipt_total = frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total),0)
        FROM `tabPurchase Receipt`
        WHERE petty_cash_request=%s
    """, self.petty_cash_request)[0][0]

    expense_claim_total = frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total),0)
        FROM `tabExpense Claim`
        WHERE petty_cash_request=%s
    """, self.petty_cash_request)[0][0]

    total = purchase_receipt_total + expense_claim_total

    petty_cash = frappe.get_doc("Petty Cash Request", self.petty_cash_request)
    limit = petty_cash.received_amount or petty_cash.required_amount

    if total >= limit:
        frappe.msgprint(
            f"Validation Error: Total amount for Petty Cash Request '{self.petty_cash_request}' "
            f"has exceeded the limit of {limit}. Current Total: {total}."
        )

# def calculate_expense_tax(self,method):
#     # customization for taxes are charges added in expense row 
#     # self.taxes=[]
#     for row in self.expenses:
#         row.custom_tax_amount = row.amount*row.custom_rate/100
#         if row.custom_account_head:
#             self.append("taxes",{
#                 "account_head":row.custom_account_head,
#                 "rate":row.custom_rate,
#                 "tax_amount":row.custom_tax_amount,
#                 "description": " - ".join(row.custom_account_head.split(" - ")[:-1]),
#                 "custom_total_amount":row.amount,
#                 "total":row.amount + row.custom_tax_amount
#                 })

#     count = 0
#     for i in self.taxes:
#         count += i.tax_amount

#     self.total_taxes_and_charges = count
#     self.total_claimed_amount = self.total_taxes_and_charges + self.total_sanctioned_amount



def calculate_expense_tax(self, method=None):
    # 1. CRITICAL: Clear the taxes table before rebuilding to stop duplication
    self.set("taxes", [])
    
    total_tax_accumulator = 0
    
    for row in self.expenses:
        # Calculate row tax amount
        row.custom_tax_amount = flt(row.amount) * flt(row.custom_rate) / 100
        
        if row.custom_account_head:
            # 2. Append fresh rows to the now-empty table
            self.append("taxes", {
                "account_head": row.custom_account_head,
                "rate": row.custom_rate,
                "tax_amount": row.custom_tax_amount,
                "description": "VAT 15% - " + (row.expense_type or "Expense"),
                "custom_total_amount": row.amount,
                "total": flt(row.amount) + flt(row.custom_tax_amount)
            })
            total_tax_accumulator += flt(row.custom_tax_amount)

    # 3. Update header totals safely
    self.total_taxes_and_charges = total_tax_accumulator
    
    # Use flt() to prevent the "float + NoneType" crash
    sanctioned = flt(self.total_sanctioned_amount)
    
    self.total_claimed_amount = flt(self.total_taxes_and_charges) + sanctioned
    
    # Update Grand Total
    self.grand_total = self.total_claimed_amount - flt(self.total_advance_amount)

def on_cancel(self,method):
    # on cancel remove petty cash ref
    self.db_set("petty_cash_request",None)




# @frappe.whitelist()
# def create_pi_from_expense(expense_claim, rows):

#     if isinstance(rows, str):
#         rows = json.loads(rows)

#     if not rows:
#         frappe.throw("No rows selected")

#     ec = frappe.get_doc("Expense Claim", expense_claim)

#     # ✅ Supplier from EC
#     supplier = ec.get("supplier") or ec.get("custom_supplier")

#     # if not supplier:
#     #     frappe.throw("Please set Supplier in Expense Claim")

#     pi = frappe.new_doc("Purchase Invoice")
#     pi.supplier = supplier
#     pi.company = ec.company
#     pi.posting_date = frappe.utils.nowdate()
#     pi.set_posting_time = 1

#     total_tax = 0

#     for row in rows:

#         # ✅ Add Item
#         pi.append("items", {
#             "item_name": row.get("expense_type"),
#             "description": row.get("expense_type"),
#             "qty": 1,
#             "rate": row.get("amount"),
#             "expense_account": row.get("default_account"),
#             "cost_center": row.get("cost_center") or frappe.get_cached_value(
#                 "Company", ec.company, "cost_center"
#             )
#         })

#         # ✅ Collect Tax
#         if row.get("custom_tax_amount"):
#             total_tax += float(row.get("custom_tax_amount"))

#     # ✅ Add Tax Row (Single consolidated tax)
#     if total_tax:
#         pi.append("taxes", {
#             "charge_type": "Actual",
#             "account_head": rows[0].get("custom_account_head"),
#             "description": "VAT 15%",
#             "tax_amount": total_tax
#         })

#     pi.insert(ignore_permissions=True)
#     pi.submit()

#     return pi.name