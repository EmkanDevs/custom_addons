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

	// ----------------------------------------------------------------
	// Highlight rows that have no matching Blanket Order so the Cost
	// Control team can spot them immediately.
	// ----------------------------------------------------------------
	// formatter: function (value, row, column, data, default_formatter) {
	// 	value = default_formatter(value, row, column, data);

	// 	if (
	// 		data &&
	// 		data.blanket_order_status &&
	// 		data.blanket_order_status.includes("No Blanket Order")
	// 	) {
	// 		value = `<span style="color: #e03e3e; font-weight: 600;">${value}</span>`;
	// 	}

	// 	return value;
	// },

	// ----------------------------------------------------------------
	// Optional: after the report renders, add a legend note below the
	// table explaining the warning indicator.
	// ----------------------------------------------------------------
	// after_datatable_render: function (datatable_obj) {
	// 	const wrapper = datatable_obj.wrapper;
	// 	if (wrapper && !wrapper.querySelector(".bo-legend")) {
	// 		const legend = document.createElement("div");
	// 		legend.className = "bo-legend";
	// 		legend.style.cssText =
	// 			"margin-top:8px;font-size:12px;color:#6b7280;padding:4px 8px;";
	// 		legend.innerHTML =
	// 			'<span style="color:#e03e3e;font-weight:600;">⚠ No Blanket Order Found</span> — ' +
	// 			"Record has no matching approved Blanket Order for the given supplier, " +
	// 			"equipment and date range. Please verify before approving.";
	// 		wrapper.appendChild(legend);
	// 	}
	// },
};