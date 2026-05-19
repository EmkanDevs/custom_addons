# Copyright (c) 2026, Administrator and contributors
# For license information, please see license.txt

# Copyright (c) 2026, Administrator and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MedicalInsuranceSheet(Document):

	def before_save(self):
		if self.main_member_id:
			main_id = str(self.main_member_id).strip().rstrip(".0") if str(self.main_member_id).strip().endswith(".0") else str(self.main_member_id).strip()
			result = frappe.db.get_value(
				"Employee",
				{"custom_national_code": main_id},
				["name", "employee_number"],
				as_dict=True,
			)
			if result:
				self.employee_number = result.employee_number or result.name
	

	