# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class PettyCashRequest(Document):
	def validate(self):
		if not self.received_amount:
			self.received_amount = self.required_amount
		if self.received_amount > self.required_amount:
			frappe.throw("Received Amount can not be Greater than Required Amount")
   
	def on_update_after_submit(self):
		if not self.received_amount:
			self.db_set("received_amount",self.required_amount)
		if self.received_amount > self.required_amount:
			frappe.throw("Received Amount can not be Greater than Required Amount")

@frappe.whitelist()
def make_expense_claim(source_name, target_doc=None):
    def set_missing_values(source, target):
        # Map fields from PCR to Expense Claim
        target.employee = source.employee_id

        account = frappe.db.get_value(
            "Petty Cash Authorized Employees",
            {"employee": source.employee_id},
            "custom_payable_account"
        )
        if account:
            target.payable_account = account

    doc = get_mapped_doc(
        "Petty Cash Request",       # source doctype
        source_name,                # source name (PCR docname)
        {
            "Petty Cash Request": { # mapping
                "doctype": "Expense Claim",
            }
        },
        target_doc,
        set_missing_values
    )
    return doc


@frappe.whitelist()
def fetch_purchaseorder_and_expenseclaim_details(petty_cash_request):
    purchase_receipt = frappe.get_all(
        "Purchase Receipt",
        filters={"petty_cash_request": petty_cash_request, "docstatus": 1},
        fields=["name", "grand_total", "creation", "total_taxes_and_charges"]
    )
    expense_claim = frappe.get_all(
        "Expense Claim",
        filters={"petty_cash_request": petty_cash_request, "docstatus": 1},
        fields=["name", "grand_total", "creation", "total_taxes_and_charges"]
    )

    if not purchase_receipt and not expense_claim:
        return "<p style='color: red;'>Both Purchase Receipt & Expense Claim not found.</p>"

    max_length = max(len(purchase_receipt), len(expense_claim))

    html_content = """
        <div style="border: 1px solid #444; border-radius: 5px; overflow: hidden;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="color: #fff;">
                        <th width="50%" style="padding: 10px; border: 1px solid #444; color: red;">Purchase Receipt</th>
                        <th width="50%" style="padding: 10px; border: 1px solid #444; color: red;">Expense Claim</th>
                    </tr>
                </thead>
                <tbody>
    """

    for i in range(max_length):
        pr = purchase_receipt[i] if i < len(purchase_receipt) else None
        ec = expense_claim[i] if i < len(expense_claim) else None

        html_content += "<tr>"
        if pr:
            purchase_link = frappe.utils.get_url_to_form("Purchase Receipt", pr['name'])
            html_content += f"""
                <td width="50%" style="padding: 10px; border: 1px solid #444;">
                    <strong style="padding-right: 280px;">
                        <a href="{purchase_link}" target="_blank" style="color: #28a745; text-decoration: underline; font-weight: bold;">{pr['name']}</a>
                    </strong> 
                    <button type="button" class="btn btn-dark remove-pr" data-pr="{pr['name']}"> X </button><br>
                    Created On: {pr['creation'].date()}<br>
                    Total Taxes and Charges: {pr['total_taxes_and_charges']}<br>
                    Grand Total: {format(pr['grand_total'], ',.2f')}
                </td>
            """
        else:
            html_content += "<td style='padding: 10px; border: 1px solid #444;'></td>"

        if ec:
            expense_link = frappe.utils.get_url_to_form("Expense Claim", ec['name'])
            html_content += f"""
                <td width="50%" style="padding: 10px; border: 1px solid #444;">
                    <strong>
                        <a href="{expense_link}" target="_blank" style="color: #28a745; text-decoration: underline; font-weight: bold;">{ec['name']}</a>
                    </strong><br>
                    Created On: {ec['creation'].date()}<br>
                    Total Taxes and Charges: {ec['total_taxes_and_charges']}<br>
                    Grand Total: {format(ec['grand_total'], ',.2f')}
                </td>
            """
        else:
            html_content += "<td style='padding: 10px; border: 1px solid #444;'></td>"

        html_content += "</tr>"

    html_content += """
                </tbody>
            </table>
        </div>
    """

    return html_content


@frappe.whitelist()
def set_petty_cash(data, purchase_receipts):
    if isinstance(purchase_receipts, str):
        import json
        purchase_receipts = json.loads(purchase_receipts)
        
    for receipt_name in purchase_receipts:
        if frappe.db.exists("Purchase Receipt",receipt_name):
            doc = frappe.get_doc("Purchase Receipt", receipt_name)
            doc.db_set("petty_cash_request", data,update_modified=False)
            
@frappe.whitelist()
def clear_petty_cash_request(purchase_receipt):
    try:
        # frappe.throw(str(purchase_receipt))
        frappe.db.set_value("Purchase Receipt", purchase_receipt, "petty_cash_request", "")
        # frappe.db.commit()  # Ensure the change is saved in the database
        return "success"
    except Exception as e:
        frappe.log_error(f"Error clearing petty_cash_request: {str(e)}")
        return "error"


# from mkan_customization.api import send_email_on_state_change
# @frappe.whitelist()
# def notify_supervisor(petty_cash_request):
#     send_email_on_state_change(petty_cash_request)