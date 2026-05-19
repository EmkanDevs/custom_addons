# Copyright (c) 2026, Administrator and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EquipmentAssetManagement(Document):
    pass

def _get_employee_number(national_code):
    return frappe.db.get_value(
        "Employee",
        {"national_id": national_code, "status": "Active"},
        "employee_number",
    )