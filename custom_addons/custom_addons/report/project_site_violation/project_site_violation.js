// Copyright (c) 2025, Finbyz and contributors
// For license information, please see license.txt

frappe.query_reports["Project Site Violation"] = {
	"filters": [
		{
			"fieldname": "project",
			"label": "Project",
			"fieldtype": "Link",
			"options": "Project",
		},
		{
			"fieldname": "project_site_violation",
			"label": "Project Site Violation",
			"fieldtype": "Link",
			"options": "Project Site Violation",
		},
		{
			"fieldname": "violation_penalty_reason",
			"label": "Violation Penalty Reason",
			"fieldtype": "Link",
			"options": "Violation Penalty Reason",
		}
	]
};
