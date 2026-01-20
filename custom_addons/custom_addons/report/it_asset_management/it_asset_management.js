// Copyright (c) 2025, Finbyz and contributors
// For license information, please see license.txt

frappe.query_reports["It Asset Management"] = {
	"filters": [
		{
			"fieldname": "project",
			"label": "Project",
			"fieldtype": "Link",
			"options": "Project",
		},
		{
			"fieldname": "name",
			"label": "It Asset Management",
			"fieldtype": "Link",
			"options": "IT Asset Management",
		},
		{
			"fieldname": "item",
			"label": "Item",
			"fieldtype": "Link",
			"options": "Item",
		},
	]
};
