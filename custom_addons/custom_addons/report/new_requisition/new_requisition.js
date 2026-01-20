// Copyright (c) 2025, Finbyz and contributors
// For license information, please see license.txt

frappe.query_reports["New Requisition"] = {
	"filters": [
		{
			"fieldname": "for_project",
			"label": "Project",
			"fieldtype": "Link",
			"options": "Project",
		},
		{
			"fieldname": "name",
			"label": "New Requisition",
			"fieldtype": "Link",
			"options": "New Requisition",
		},
	]
};
