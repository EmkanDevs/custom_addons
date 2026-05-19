// Copyright (c) 2026, Finbyz and contributors
// For license information, please see license.txt

frappe.query_reports["Equipment Custody Balance"] = {

    filters: [

        {
            fieldname: "custody_holder_id",
            label: __("Employee"),
            fieldtype: "Link",
            options: "Employee"
        },

        {
            fieldname: "project",
            label: __("Project"),
            fieldtype: "Link",
            options: "Project"
        },

        {
            fieldname: "transaction_type",
            label: __("Transaction Type"),
            fieldtype: "Select",
            options: "\nIssue / Receiving\nReturn"
        },

        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date"
        },

        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date"
        },

		{
			fieldname: "with_employee",
			label: __("With Employee"),
			fieldtype: "Check",
			default: 1
		}
    ]
};