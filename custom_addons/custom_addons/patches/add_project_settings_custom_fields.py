import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    if not frappe.db.exists("DocType", "Accounting Dimension CT Accounts"):
        frappe.throw("Doctype 'Accounting Dimension CT Accounts' must exist before running this patch")
    if not frappe.db.exists("DocType", "Accounting Dimension CT Doctypes"):
        frappe.throw("Doctype 'Accounting Dimension CT Doctypes' must exist before running this patch")

    create_custom_fields(
        {
            "Projects Settings": [
                {
                    "fieldname": "accounting_dimensions_section",
                    "label": "Accounting Dimensions",
                    "fieldtype": "Section Break",
                    "insert_after": "fetch_timesheet_in_sales_invoice",
                },
                {
                    "fieldname": "accounting_dimension_accounts_column",
                    "fieldtype": "Column Break",
                    "insert_after": "accounting_dimensions_section",
                },
                {
                    "fieldname": "accounting_dimension_accounts",
                    "label": "Accounting Dimension Accounts",
                    "fieldtype": "Table",
                    "options": "Accounting Dimension CT Accounts",
                    "insert_after": "accounting_dimension_accounts_column",
                },
                {
                    "fieldname": "accounting_dimension_doctypes_column",
                    "fieldtype": "Column Break",
                    "insert_after": "accounting_dimension_accounts",
                },
                {
                    "fieldname": "accounting_dimension_doctypes",
                    "label": "Accounting Dimension Doctypes",
                    "fieldtype": "Table",
                    "options": "Accounting Dimension CT Doctypes",
                    "insert_after": "accounting_dimension_doctypes_column",
                },
            ]
        },
        update=True,
    )