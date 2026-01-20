# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PettyCashAuthorizedEmployees(Document):
	def validate(self):
		if self.department:
			doc = frappe.get_doc("Department", self.department)
			self.set("head_of_department", [])
			for row in doc.head_of_department:
				self.append("head_of_department", {"head_of_department": row.head_of_department})
			if self.head_of_department and not self.supervisor:
				self.supervisor = self.head_of_department[0].head_of_department

