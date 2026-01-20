import frappe
from frappe import _

def after_insert(self, method):
    self.custom_bid_tabulation_check = 1
    self.db_set("custom_bid_tabulation_check", 1)

    if not self.supplier:
        return

    supplier = frappe.get_doc("Supplier", self.supplier)

    missing_fields = []

    if not supplier.get("custom_default_iban_no"):
        missing_fields.append("Default IBAN No.")

    if not supplier.get("custom_section_materials_services"):
        missing_fields.append("Section, Materials, Services")

    if not supplier.get("tax_id"):
        missing_fields.append("Tax ID")

    if not supplier.get("custom_cr_number"):
        missing_fields.append("CR Number")

    if not supplier.get("primary_address"):
        missing_fields.append("Address")

    if missing_fields:
        frappe.throw(
            _("Supplier {0} is missing required data: {1}").format(
                self.supplier_name, ", ".join(missing_fields)
            )
        )
    
@frappe.whitelist()
def service_status_map(source_name):
    from frappe.model.mapper import get_mapped_doc

    # Step 1: Check if a Service Status already exists with this Purchase Order
    existing = frappe.get_all("Service Status", filters={"purchase_order": source_name}, fields=["name"])
    if existing:
        frappe.throw(f"Service Status <a href='/app/service-status/{existing[0].name}' style='color:blue;'>{existing[0].name}</a> already exists for this Purchase Order.")

    # Step 2: Map Purchase Order → Service Status
    def postprocess(source_doc, target_doc):
        target_doc.purchase_order = source_doc.name
        target_doc.customer = source_doc.customer

    return get_mapped_doc(
        "Purchase Order",
        source_name,
        {
            "Purchase Order": {
                "doctype": "Service Status",
                "validation": {
                    "docstatus": ["=", 1]
                }
            },
            "Purchase Order Item": {
                "doctype": "Service Status Details",
                "field_map": {
                    "item_code": "item",
                    "item_name": "item_name",
                    "description": "description",
                    "material_request": "material_request"
                },
                "add_if_empty": True
            }
        },
        postprocess=postprocess
    )

