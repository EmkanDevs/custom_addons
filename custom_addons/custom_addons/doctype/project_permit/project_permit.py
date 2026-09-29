# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProjectPermit(Document):
    pass

@frappe.whitelist()
def make_pp_payment_request(docname):
    doc = frappe.get_doc("Project Permit",docname)
    data = frappe.new_doc("Payment Requester")
    data.transaction_date = doc.permit_date
    data.party_type = "Supplier"
    data.party = doc.permit_under_supplier
    data.party_name = doc.permit_under_supplier_name
    data.payment_request_type =  "Outward"
    data.reference_doctype = "Project Permit"
    data.reference_name = doc.name
    data.grand_total = doc.amount
    data.project = doc.project
    data.save()
    
    return data