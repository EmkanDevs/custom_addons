# Copyright (c) 2026, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class AmendmentReasonCategory(Document):
	def validate(self):
		seen = set()
		for row in self.amendment_types:
			if row.amendment_type in seen:
				frappe.throw(_("Row {0}: Amendment Type {1} is listed more than once.").format(row.idx, row.amendment_type))
			seen.add(row.amendment_type)
		if not seen:
			frappe.throw(_("Add at least one Amendment Type for which this reason can be used."))
		# legacy single-type field kept only for migration; mirror the first row so old reports still show something
		self.amendment_type = self.amendment_types[0].amendment_type
