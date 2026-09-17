# Copyright (c) 2026, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet, rebuild_tree


class BusinessPartnerGroup(NestedSet):
	nsm_parent_field = "parent_business_partner_group"

	def validate(self):
		if not self.parent_business_partner_group:
			root_group = frappe.db.get_value(
				"Business Partner Group",
				{"is_group": 1, "parent_business_partner_group": ("in", ["", None])},
				"name",
			)
			if root_group and self.name != root_group:
				self.parent_business_partner_group = root_group

	def on_trash(self):
		super().on_trash()

	def on_update(self):
		super().on_update()
		self.validate_one_root()

	def validate_one_root(self):
		if not self.parent_business_partner_group:
			parent = frappe.db.sql(
				"""select count(*) from `tabBusiness Partner Group`
				where ifnull(parent_business_partner_group, '') = '' and docstatus < 2"""
			)
			if parent and parent[0][0] > 1:
				frappe.throw(
					frappe._("Multiple root nodes not allowed for Business Partner Group")
				)
