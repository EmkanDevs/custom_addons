# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.desk.form import assign_to

class NewRequisition(Document):
	def validate(self):
		if self.request_from:
			self.head_of_department = []
			doc = frappe.get_doc("Department", self.request_from)

			for row in doc.head_of_department:
				self.append("head_of_department", {
					"head_of_department": row.head_of_department
				})
	def on_submit(self):
		user = self.get("head_of_department")
		if not user:
			frappe.throw("User field cannot be empty.")
		for row in user:
			assign_to.add(
				dict(
					assign_to=[row.head_of_department],
					doctype="New Requisition",
					name=self.name,
					priority=self.priority or "Medium",
					notify=True,
				),
				ignore_permissions=True,
			)
	def on_update(self):
		if self.workflow_state == "Completed" and not self.attachment:
		# if self.doc_status == "Completed" and not self.attachment:
			frappe.msgprint("Please add Attachment")