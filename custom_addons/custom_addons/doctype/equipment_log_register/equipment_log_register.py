import frappe
from frappe.model.document import Document

class EquipmentLogRegister(Document):

    def validate(self):

        for row in self.equipment_log_item:

            if not row.item_code:
                continue

            is_fixed_asset = frappe.db.get_value(
                "Item",
                row.item_code,
                "is_fixed_asset"
            )

            row.fixed_asset = is_fixed_asset

            if is_fixed_asset:

                if not row.tag_number:
                    frappe.throw(
                        f"Row #{row.idx}: Tag Number is mandatory for Fixed Asset item {row.item_code}"
                    )

                if row.quantity > 1:
                    frappe.throw(
                        f"Row #{row.idx}: Quantity cannot exceed 1 for Fixed Asset item {row.item_code}"
                    )