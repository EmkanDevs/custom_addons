// Copyright (c) 2026, Finbyz and contributors
// For license information, please see license.txt

frappe.query_reports["Subcontractor Material Return Cycle"] = {
	"filters": [
        {
            "fieldname": "from_date",
            "fieldtype": "Date",
            "label": "From Date",
            "mandatory": 0,
            "default": "Today"
        },
        {
            "fieldname": "to_date",
            "fieldtype": "Date",
            "label": "To Date",
            "mandatory": 0,
            "default": "Today"
        },
        {
            "fieldname": "project",
            "fieldtype": "Link",
            "label": "Project",
            "mandatory": 0,
            "options": "Project"
        },
        {
            "fieldname": "issue_stock_entry",
            "fieldtype": "Link",
            "label": "Issue Stock Entry",
            "mandatory": 0,
            "options": "Stock Entry"
        },
        {
            "fieldname": "return_request",
            "fieldtype": "Link",
            "label": "Return Request",
            "mandatory": 0,
            "options": "Returned Material to Warehouse Request"
        },
        {
            "fieldname": "return_stock_entry",
            "fieldtype": "Link",
            "label": "Return Stock Entry",
            "mandatory": 0,
            "options": "Stock Entry"
        },
        {
            "fieldname": "item_code",
            "fieldtype": "Link",
            "label": "Stock Code",
            "mandatory": 0,
            "options": "Item"
        },
        {
            "fieldname": "reason_of_return",
            "fieldtype": "Data",
            "label": "Reason for Return",
            "mandatory": 0
        },
		{
			"fieldname": "supplier",
			"fieldtype": "Link",
			"label": "Supplier",
			"mandatory": 0,
			"options": "Supplier"
		},
		{
			"fieldname": "target_warehouse",
			"fieldtype": "Link",
			"label": "Target Warehouse",
			"mandatory": 0,
			"options": "Warehouse"
		}
    ]
}