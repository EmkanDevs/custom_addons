# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TempRoomBooking(Document):
	pass
@frappe.whitelist()
def make_trb_payment_request(docname):
    doc = frappe.get_doc("Temp Room Booking",docname)
    data = frappe.new_doc("Payment Requester")
    data.payment_request_type =  "Outward"
    data.reference_doctype = "Temp Room Booking"
    data.reference_name = doc.name
    data.grand_total = doc.amount 
    data.party_type = "Customer"
    data.party = frappe.db.get_value("Project",doc.project,"customer")
    data.save()
    
    return data