// Copyright (c) 2026, Administrator and contributors
// For license information, please see license.txt

frappe.query_reports["Rental Equipment Timesheet Monthly Summary Per Project"] = {
	"filters": [
		{
			"fieldname": "project",
			"label":     __("Project"),
			"fieldtype": "Link",
			"options":   "Project",
		},
		{
			"fieldname": "supplier",
			"label":     __("Supplier"),
			"fieldtype": "Link",
			"options":   "Supplier",
		},
		{
			"fieldname": "year",
			"label":     __("Year"),
			"fieldtype": "Select",
			"options":   [
				"",
				...Array.from({ length: 10 }, (_, i) => String(new Date().getFullYear() - 4 + i))
			].join("\n"),
			"default":   String(new Date().getFullYear()),
		},
		{
			"fieldname": "month",
			"label":     __("Month"),
			"fieldtype": "Select",
			"options":   [
				"", "January", "February", "March", "April",
				"May", "June", "July", "August", "September",
				"October", "November", "December",
			].join("\n"),
		},
		{
			"fieldname": "state",
			"label":     __("State"),
			"fieldtype": "Select",
			"options":   "\nDraft\nSubmitted\nCancelled",
		},
	],
};