# Copyright (c) 2026, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.contacts.address_and_contact import load_address_and_contact


class BusinessPartner(Document):
	def onload(self):
		"""Load address and contact in `__onload`"""
		load_address_and_contact(self)

	def validate(self):
		self.set_primary_address_and_contact()

	def set_primary_address_and_contact(self):
		if self.customer_primary_contact:
			contact_details = frappe.db.get_value(
				"Contact",
				self.customer_primary_contact,
				["mobile_no", "email_id"],
				as_dict=True,
			)
			if contact_details:
				self.mobile_no = contact_details.mobile_no
				self.email_id = contact_details.email_id

		if self.customer_primary_address:
			from frappe.contacts.doctype.address.address import get_condensed_address

			address_doc = frappe.get_cached_doc("Address", self.customer_primary_address)
			self.primary_address = get_condensed_address(address_doc)
