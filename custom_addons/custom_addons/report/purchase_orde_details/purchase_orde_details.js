// Copyright (c) 2026, Finbyz and contributors
// For license information, please see license.txt

frappe.query_reports["Purchase Orde Details"] = {
	"filters": [
		{
			"fieldname": "project",
			"label": __("Project"),
			"fieldtype": "Link",
			"options": "Project",
			"get_query": function() {
				return {
					"filters": {
						"status": ["not in", ["Completed", "Cancelled"]]
					}
				};
			}
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 0
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 0
		},
		{
			"fieldname": "material_request_purpose",
			"label": __("Material Request Purpose"),
			"fieldtype": "Select",
			"options": ["", "Purchase", "Material Transfer", "Material Issue", "Manufacture", "Customer Provided"],
			"default": "Purchase"
		}
	],
	
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		// Apply row-level styling based on indent (parent vs child rows)
		if (data && data.indent === 0) {
			// Parent row - Purchase Order level
			if (column.fieldname === "purchase_order") {
				value = `<span style="font-weight: bold; color: #2c3e50;">${value}</span>`;
			}
		} else if (data && data.indent === 1) {
			// Child row - Item level
			if (column.fieldname === "item_code" || column.fieldname === "item_name") {
				value = `<span style="color: #34495e; padding-left: 20px;">${value}</span>`;
			}
		}
		
		return value;
	}
};