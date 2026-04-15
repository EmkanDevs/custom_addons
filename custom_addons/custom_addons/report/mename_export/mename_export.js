// Copyright (c) 2026, Administrator and contributors
// For license information, please see license.txt

frappe.query_reports["MenaME Export"] = {
	filters: [
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
			width: "200px",
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
			width: "200px",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			width: "100px",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			width: "100px",
		},
	],
};