# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProjectSiteViolation(Document):
	pass

import frappe

@frappe.whitelist()
def make_payment_request(docname):
    # API-level permission check
    if not frappe.has_permission(
        "Project Site Violation",
        ptype="read",
        doc=docname
    ):
        frappe.throw(
            _("You do not have permission to access this Project Site Violation"),
            frappe.PermissionError,
        )

    # Get source document
    doc = frappe.get_doc("Project Site Violation", docname)

    # Additional document-level permission check
    doc.check_permission("read")

    data = frappe.new_doc("Payment Requester")
    data.payment_request_type = "Outward"
    data.reference_doctype = "Project Site Violation"
    data.reference_name = doc.name
    data.grand_total = doc.penalty_amount
    data.party_type = "Customer"
    data.party = frappe.db.get_value("Project", doc.project, "customer")

    data.insert()

    return data