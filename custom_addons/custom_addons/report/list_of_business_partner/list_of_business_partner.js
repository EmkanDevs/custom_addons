// Copyright (c) 2026, Finbyz Tech Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["List of Business Partner"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "bp_type",
			label: __("Business Partner Type"),
			fieldtype: "Select",
			options: ["", "Customer", "Supplier"],
			default: "",
			on_change: function (report) {
				// reset party + group_code when type changes, since
				// the link target / options differ for Customer vs Supplier
				report.set_filter_value("party", "");
				report.set_filter_value("group_code", "");
				report.refresh();
			},
		},
		{
			fieldname: "party",
			label: __("Business Partner"),
			fieldtype: "Dynamic Link",
			get_options: function () {
				let bp_type = frappe.query_report.get_filter_value("bp_type");
				return bp_type || "Customer";
			},
		},
		{
			fieldname: "tax_id",
			label: __("Tax ID / CR No."),
			fieldtype: "Data",
		},
		{
			fieldname: "account",
			label: __("Account (Receivable/Payable)"),
			fieldtype: "Link",
			options: "Account",
			get_query: function () {
				return {
					filters: {
						account_type: ["in", ["Receivable", "Payable"]],
					},
				};
			},
		},
		{
			fieldname: "group_code",
			label: __("Group Code"),
			fieldtype: "Data",
			// Customer Group / Supplier Group share no single doctype,
			// kept as free-text data filter so it works whichever bp_type
			// is selected (or both).
		},
		{
			fieldname: "payment_terms",
			label: __("Payment Terms"),
			fieldtype: "Link",
			options: "Payment Terms Template",
		},
		{
			fieldname: "active",
			label: __("Active"),
			fieldtype: "Select",
			options: ["", "Yes", "No"],
			default: "",
		},
	],
};