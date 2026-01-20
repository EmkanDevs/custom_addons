# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from custom_addons.custom_addons.override import assign_to

class PublicRelationVisit(Document):
	def after_insert(self):
		doc = frappe.get_doc("Public Relations Resource",self.pr_representative)
		assign_to.add(
				dict(
					assign_to=[doc.email],
					doctype="Public Relation Visit",
					name=self.name,
					priority= "Medium",
					notify=True,
				),
				ignore_permissions=True,
			)