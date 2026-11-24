// Copyright (c) 2026, Finbyz and contributors
// For license information, please see license.txt

frappe.query_reports["Cancelled POs Without Approved Log"] = {
	filters: [
		{ fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company" },
		{ fieldname: "supplier", label: __("Supplier"), fieldtype: "Link", options: "Supplier" },
		{ fieldname: "from_date", label: __("From PO Date"), fieldtype: "Date" },
		{ fieldname: "to_date", label: __("To PO Date"), fieldtype: "Date" },
		{ fieldname: "log_status", label: __("Log Status"), fieldtype: "Select", options: "\nNo Log\nDraft\nPending Approval\nRejected" },
	],
};
