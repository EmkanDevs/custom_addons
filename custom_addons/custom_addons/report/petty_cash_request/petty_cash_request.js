// Copyright (c) 2025, Finbyz and contributors
// For license information, please see license.txt

frappe.query_reports["Petty Cash Request"] = {
	"filters": [
		{
			"fieldname": "project",
			"label": "Project",
			"fieldtype": "Link",
			"options": "Project",
		},
		{
			"fieldname": "name",
			"label": "Petty Cash Request",
			"fieldtype": "Link",
			"options": "Petty Cash Request",
		},
	]
};
