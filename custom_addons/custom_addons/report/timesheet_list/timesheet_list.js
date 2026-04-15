// Copyright (c) 2026, Administrator and contributors
// For license information, please see license.txt

// frappe.query_reports["Timesheet List"] = {
// 	"filters": [

// 	]
// };


// Copyright (c) 2025, Finbyz Tech Pvt. Ltd.
// Timesheet List Report – Client-side filter definitions

frappe.query_reports["Timesheet List"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.month_start(),
		},
		{
			fieldname: "to_date",
			label: __("To"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.month_end(),
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
		},
		{
			fieldname: "employment_type",
			label: __("Employment Type"),
			fieldtype: "Link",
			options: "Employment Type",
		},
		{
			fieldname: "designation",
			label: __("Designation"),
			fieldtype: "Link",
			options: "Designation",
		},
		{
			fieldname: "status",
			label: __("State"),
			fieldtype: "Select",
			options: "\nDraft\nSubmitted\nCancelled\nPayslip",
		},
	],
};