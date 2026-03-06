    
import frappe

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

def calculate_expense_tax(self,method):
    # customization for taxes are charges added in expense row 
    # self.taxes=[]
    for row in self.expenses:
        row.custom_tax_amount = row.amount*row.custom_rate/100
        if row.custom_account_head:
            self.append("taxes",{
                "account_head":row.custom_account_head,
                "rate":row.custom_rate,
                "tax_amount":row.custom_tax_amount,
                "description": " - ".join(row.custom_account_head.split(" - ")[:-1]),
                "custom_total_amount":row.amount,
                "total":row.amount + row.custom_tax_amount
                })

    count = 0
    for i in self.taxes:
        count += i.tax_amount

    self.total_taxes_and_charges = count
    self.total_claimed_amount = self.total_taxes_and_charges + self.total_sanctioned_amount

def on_cancel(self,method):
    # on cancel remove petty cash ref
    self.db_set("petty_cash_request",None)