// Copyright (c) 2026, Administrator and contributors
// For license information, please see license.txt

// Copyright (c) 2024, Your Company and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Rental Equipment Timesheet Monthly Summary"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 1,
			width: "100",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
			reqd: 1,
			width: "100",
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
			width: "100",
		},
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier",
			width: "100",
		},
		{
			fieldname: "door_no_or_plate_no",
			label: __("Door No or Plate No"),
			fieldtype: "Link",
			options:"Equipment Asset Management",
			width: "100",
		},
		
	],
};