// Copyright (c) 2026, Administrator and contributors
// For license information, please see license.txt

frappe.query_reports["Rental Equipment Timesheet Summary"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.month_start()
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.month_end()
		},
		{
			"fieldname": "project",
			"label": __("Project"),
			"fieldtype": "Link",
			"options": "Project"
		},
		{
			"fieldname": "supplier",
			"label": __("Supplier"),
			"fieldtype": "Link",
			"options": "Supplier"
		},
		{
			"fieldname": "state",
			"label": __("State"),
			"fieldtype": "Select",
			"options": "\nDraft\nSubmitted\nCancelled"
		},
		{
			"fieldname": "total_hours_greater_than",
			"label": __("Total Hours Greater Than"),
			"fieldtype": "Float",
			"default": 0
		}
	]
};