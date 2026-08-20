import frappe
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def make_sales_invoice_from_project(source_name, target_doc=None):
    def set_missing_values(source, target):
        # Set essential document-level fields
        target.project = source.name
        target.customer = source.customer
        target.company = source.get("company")
        target.currency = source.get("currency")
        target.selling_price_list = source.get("selling_price_list")
        
        # Set the project name in custom_pro_number field
        target.custom_pro_number = source.name
        
        # Get the sales order linked to this project and set in custom_contract_number
        if source.sales_order:
            target.custom_contract_number = source.sales_order
        
        # Let standard function handle the rest
        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    # Create mapping without items first
    doclist = get_mapped_doc(
        "Project",
        source_name,
        {
            "Project": {
                "doctype": "Sales Invoice",
                "field_map": {
                    "name": "project",
                    "customer": "customer",
                    "company": "company",
                    "currency": "currency",
                },
                
            }
        },
        target_doc,
        set_missing_values,
        ignore_permissions=False
    )
    
    # Fetch project doc once
    project = frappe.get_doc("Project", source_name)
    company = project.company
    
    # Get default accounts
    cost_center = project.cost_center or frappe.get_cached_value("Company", company, "cost_center")
    default_income_account = frappe.get_cached_value("Company", company, "default_income_account") if company else ""
    income_account = project.get("income_account") or default_income_account
    
    # Get the project items directly from the custom_items child table
    for project_item in project.custom_items:
        item_row = doclist.append("items", {})
        
        # Map only fields that exist in both tables
        item_row.item_code = project_item.item_code
        item_row.item_name = project_item.item_name
        item_row.description = project_item.description
        item_row.qty = project_item.qty
        item_row.rate = project_item.rate
        item_row.amount = project_item.amount
        
        # Add these if they exist in your schema
        if hasattr(project_item, "uom"):
            item_row.uom = project_item.uom
        if hasattr(project_item, "conversion_factor"):
            item_row.conversion_factor = project_item.conversion_factor
        if hasattr(project_item, "discount_percentage"):
            item_row.discount_percentage = project_item.discount_percentage
        if hasattr(project_item, "discount_amount"):
            item_row.discount_amount = project_item.discount_amount
            
        # Set required fields
        item_row.cost_center = cost_center
        item_row.project = source_name
        item_row.income_account = income_account
    
    # Save after all items are added
    doclist.flags.ignore_permissions = True
    
    return doclist


@frappe.whitelist()
def make_delivery_note_from_project(source_name, target_doc=None):
    def set_missing_values(source, target):
        # Set essential document-level fields
        target.project = source.name
        target.customer = source.customer
        target.company = source.get("company")
        target.currency = source.get("currency")

        # Set the project name in custom_pro_number field (if you use that)
        target.custom_pro_number = source.name

        # Get the sales order linked to this project and set in custom_contract_number
        if source.sales_order:
            target.custom_contract_number = source.sales_order

        # Let standard function handle the rest
        target.run_method("set_missing_values")

    # Create mapping without items first
    doclist = get_mapped_doc(
        "Project",
        source_name,
        {
            "Project": {
                "doctype": "Delivery Note",
                "field_map": {
                    "name": "project",
                    "customer": "customer",
                    "company": "company",
                    "currency": "currency",
                },
                
            }
        },
        target_doc,
        set_missing_values,
        ignore_permissions=False
    )

    # Fetch project doc once
    project = frappe.get_doc("Project", source_name)
    company = project.company

    # Get default cost center
    cost_center = project.cost_center or frappe.get_cached_value("Company", company, "cost_center")

    # Get project items from custom_items child table
    for project_item in project.custom_items:
        item_row = doclist.append("items", {})

        item_row.item_code = project_item.item_code
        item_row.item_name = project_item.item_name
        item_row.description = project_item.description
        item_row.qty = project_item.qty
        item_row.stock_uom=project_item.uom

        # Optional fields
        if hasattr(project_item, "uom"):
            item_row.uom = project_item.uom
        if hasattr(project_item, "conversion_factor"):
            item_row.conversion_factor = project_item.conversion_factor
        if hasattr(project_item, "rate"):
            item_row.rate = project_item.rate

        # Required fields
        item_row.cost_center = cost_center
        item_row.project = source_name

    doclist.flags.ignore_permissions = True

    return doclist
