    
import frappe

def validate(self, method):
    validate_petty_cash(self,method)
    calculate_expense_tax(self,method)

def validate_petty_cash(self,method):
    #validation for total amount not greater then petty cash connected
    
    # compare both expense claim and purchase receipt grand total
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

def calculate_expense_tax(self,method):
    # customization for taxes are charges added in expense row 
    self.taxes=[]
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