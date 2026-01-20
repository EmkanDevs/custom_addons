# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProjectSiteViolation(Document):
	pass

@frappe.whitelist()
def make_payment_request(docname):
    doc = frappe.get_doc("Project Site Violation",docname)
    data = frappe.new_doc("Payment Requester")
    data.payment_request_type =  "Outward"
    data.reference_doctype = "Project Site Violation"
    data.reference_name = doc.name
    data.grand_total = doc.penalty_amount 
    data.party_type = "Customer"
    data.party = frappe.db.get_value("Project",doc.project,"customer")
    data.save()
    
    return data