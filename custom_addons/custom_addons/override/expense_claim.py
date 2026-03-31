from hrms.hr.doctype.expense_claim.expense_claim import ExpenseClaim as _ExpenseClaim
import frappe
from frappe.utils import flt

class ExpenseClaim(_ExpenseClaim):
    @frappe.whitelist()
    def calculate_taxes(self):
        # 1. TRIPLE CHECK: Clear the taxes list completely to stop duplicates
        # Using self.set ensures the child table is overwritten, not appended.
        self.set("taxes", [])
        self.total_taxes_and_charges = 0.0
        
        # 2. Rebuild taxes 1:1 from expense rows
        for row in self.expenses:
            # Use sanctioned_amount if available, else use amount
            amt = flt(row.sanctioned_amount) or flt(row.amount)
            
            if amt > 0:
                # Use self.append to add a fresh row to the cleared table
                tax_row = self.append("taxes", {})
                tax_row.account_head = "1156101 - Value Added Tax 15% Paid - IMC"
                tax_row.rate = 15.0
                tax_row.description = f"VAT 15% for {row.expense_type or 'Expense Item'}"
                
                # Custom total amount for reference
                tax_row.custom_total_amount = amt
                
                # Calculate tax amount
                tax_row.tax_amount = flt(
                    amt * (tax_row.rate / 100),
                    tax_row.precision("tax_amount")
                )
                
                # Individual row total (Base + Tax) 
                # This results in the 115.00 / 1725.00 look from your first image
                tax_row.total = tax_row.tax_amount + amt
                
                # Summing up the header total
                self.total_taxes_and_charges += tax_row.tax_amount

        # 3. Update Header Totals
        self.round_floats_in(self, ["total_taxes_and_charges"])

        # Prevent NoneType crashes by using flt()
        sanctioned = flt(self.total_sanctioned_amount)
        if sanctioned == 0:
             # Recalculate sanctioned if it's not set yet
             sanctioned = sum(flt(r.sanctioned_amount) or flt(r.amount) for r in self.expenses)
             self.total_sanctioned_amount = sanctioned

        taxes = flt(self.total_taxes_and_charges)
        advances = flt(self.total_advance_amount)

        # Update Grand Total and Claimed Amount
        self.total_claimed_amount = sanctioned + taxes
        self.grand_total = self.total_claimed_amount - advances
        
        self.round_floats_in(self, ["grand_total", "total_claimed_amount"])