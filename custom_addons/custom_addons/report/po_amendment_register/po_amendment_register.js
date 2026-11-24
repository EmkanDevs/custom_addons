// Copyright (c) 2026, Finbyz and contributors
// For license information, please see license.txt

// Copyright (c) 2026, Finbyz and contributors
// For license information, please see license.txt

frappe.query_reports["PO Amendment Register"] = {
	filters: [
		{ fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company" },
		{ fieldname: "from_date", label: __("From Log Date"), fieldtype: "Date" },
		{ fieldname: "to_date", label: __("To Log Date"), fieldtype: "Date" },
		{ fieldname: "original_supplier", label: __("Original Supplier"), fieldtype: "Link", options: "Supplier" },
		{ fieldname: "replacement_supplier", label: __("Replacement Supplier"), fieldtype: "Link", options: "Supplier" },
		{ fieldname: "cancelled_po_number", label: __("Original PO"), fieldtype: "Link", options: "Purchase Order" },
		{ fieldname: "new_po_number", label: __("Replacement PO"), fieldtype: "Link", options: "Purchase Order" },
		{ fieldname: "amendment_reason_category", label: __("Reason"), fieldtype: "Select",
			options: "\nBetter Price\nDelivery Issue\nQuality Issue\nSupplier Performance\nQuantity/Scope Change\nPayment Terms\nBudget Constraint\nOther" },
		{ fieldname: "workflow_status", label: __("Status"), fieldtype: "Select", options: "\nDraft\nPending Approval\nPending Technical/Quality\nPending Procurement\nPending Finance\nApproved\nRejected\nCancelled" },
	],

	onload(report) {
		if (document.getElementById("po-amd-register-style")) return;

		const style = document.createElement("style");
		style.id = "po-amd-register-style";
		style.textContent = `
			/* Let the filter area show overflowing dropdowns */
			.page-form,
			.standard-filter-section,
			.layout-main-section,
			.layout-main-section-wrapper {
				overflow: visible !important;
			}

			/* Open Link dropdowns leftward from the field and wrap long text */
			.page-form .awesomplete > ul {
				min-width: 320px;
				max-width: 420px;
				right: 0;
				left: auto;
				white-space: normal;
			}
			.page-form .awesomplete > ul > li {
				white-space: normal;
				word-break: break-word;
			}
			.page-form .awesomplete > ul > li p {
				white-space: normal;
				overflow-wrap: anywhere;
			}
		`;
		document.head.appendChild(style);
	},

	formatter(value, row, column, data, default_formatter) {
		const na = ["total_value_difference", "rate_benefit", "non_rate_value_change"];
		if (na.includes(column.fieldname) && (value === null || value === undefined || value === "")) return __("N/A");
		return default_formatter(value, row, column, data);
	},
};