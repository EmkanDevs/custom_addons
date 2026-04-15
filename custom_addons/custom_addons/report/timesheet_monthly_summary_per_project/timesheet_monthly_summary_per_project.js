// // Copyright (c) 2026, Administrator and contributors
// // For license information, please see license.txt
// frappe.query_reports["Timesheet Monthly Summary Per Project"] = {
// 	filters: [
// 		{
// 			fieldname: "month",
// 			label: __("Month"),
// 			fieldtype: "Select",
// 			options: [
// 				"",
// 				"January",
// 				"February",
// 				"March",
// 				"April",
// 				"May",
// 				"June",
// 				"July",
// 				"August",
// 				"September",
// 				"October",
// 				"November",
// 				"December",
// 			].join("\n"),
// 			width: "100",
// 		},
// 		{
// 			fieldname: "year",
// 			label: __("Year"),
// 			fieldtype: "Int",
// 			default: frappe.datetime.now_datetime().substring(0, 4),
// 			width: "80",
// 		},
// 		{
// 			fieldname: "project",
// 			label: __("Project"),
// 			fieldtype: "Link",
// 			options: "Project",
// 			width: "100",
// 		},
// 		{
// 			fieldname: "department",
// 			label: __("Department"),
// 			fieldtype: "Link",
// 			options: "Department",
// 			width: "100",
// 			get_query: function () {
// 				return {
// 					filters: {
// 						company: frappe.defaults.get_default("company"),
// 					},
// 				};
// 			},
// 		},
// 		{
// 			fieldname: "branch",
// 			label: __("Branch"),
// 			fieldtype: "Link",
// 			options: "Branch",
// 			width: "100",
// 		},
// 		{
// 			fieldname: "employment_type",
// 			label: __("Employment Type"),
// 			fieldtype: "Link",
// 			options: "Employment Type",
// 			width: "100",
// 		},
// 		{
// 			fieldname: "state",
// 			label: __("State"),
// 			fieldtype: "Select",
// 			// Timesheet status values in ERPNext / HRMS
// 			options: [
// 				"",
// 				"Draft",
// 				"Submitted",
// 				"Cancelled",
// 				"Payslip",
// 				"Completed",
// 			].join("\n"),
// 			width: "100",
// 		},
// 	],

// 	// -------------------------------------------------------------------------
// 	// Formatter: highlight total rows, colour-code key numeric columns
// 	// -------------------------------------------------------------------------
// 	formatter: function (value, row, column, data, default_formatter) {
// 		value = default_formatter(value, row, column, data);

// 		if (data && data.bold) {
// 			// Subtotal rows: bold + light background
// 			value = `<span style="font-weight:700;">${value}</span>`;
// 		}

// 		if (data && !data.bold) {
// 			// Colour negative or zero working hours as muted
// 			if (column.fieldname === "working_hours" && data.working_hours === 0) {
// 				value = `<span style="color:#aaa;">${value}</span>`;
// 			}
// 			// Highlight OT hours in amber when > 0
// 			if (column.fieldname === "ot_hours" && data.ot_hours > 0) {
// 				value = `<span style="color:#e67e22;font-weight:600;">${value}</span>`;
// 			}
// 		}

// 		return value;
// 	},

// 	// -------------------------------------------------------------------------
// 	// Chart: bar chart of Working Hours grouped by Month
// 	// -------------------------------------------------------------------------
// 	get_chart_data: function (columns, result) {
// 		// Collect unique months (preserve order)
// 		const months = [];
// 		const monthSeen = {};
// 		result.forEach(function (row) {
// 			if (row.month && row.month !== __("Total") && !monthSeen[row.month]) {
// 				months.push(row.month);
// 				monthSeen[row.month] = true;
// 			}
// 		});

// 		// Working Hours per month (sum across all projects)
// 		const workingHoursData = months.map(function (m) {
// 			return result
// 				.filter((r) => r.month === m && r.month !== __("Total"))
// 				.reduce((acc, r) => acc + (r.working_hours || 0), 0);
// 		});

// 		const otHoursData = months.map(function (m) {
// 			return result
// 				.filter((r) => r.month === m && r.month !== __("Total"))
// 				.reduce((acc, r) => acc + (r.ot_hours || 0), 0);
// 		});

// 		return {
// 			data: {
// 				labels: months,
// 				datasets: [
// 					{
// 						name: __("Working Hours"),
// 						values: workingHoursData,
// 						chartType: "bar",
// 					},
// 					{
// 						name: __("OT Hours"),
// 						values: otHoursData,
// 						chartType: "bar",
// 					},
// 				],
// 			},
// 			type: "bar",
// 			barOptions: { stacked: false },
// 		};
// 	},
// };


frappe.query_reports["Timesheet Monthly Summary Per Project"] = {
	filters: [
		{
			fieldname: "month",
			label: __("Month"),
			fieldtype: "Select",
			options: [
				"",
				"January","February","March","April","May","June",
				"July","August","September","October","November","December",
			].join("\n"),
			width: "100",
		},
		{
			fieldname: "year",
			label: __("Year"),
			fieldtype: "Int",
			default: frappe.datetime.now_datetime().substring(0, 4),
			width: "80",
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
			width: "100",
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
			width: "100",
			get_query: function () {
				return { filters: { company: frappe.defaults.get_default("company") } };
			},
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
			width: "100",
		},
		{
			fieldname: "employment_type",
			label: __("Employment Type"),
			fieldtype: "Link",
			options: "Employment Type",
			width: "100",
		},
		{
			fieldname: "state",
			label: __("State"),
			fieldtype: "Select",
			options: ["", "Draft", "Submitted", "Cancelled", "Payslip", "Completed"].join("\n"),
			width: "100",
		},
	],

	// -------------------------------------------------------------------------
	// Formatter
	// -------------------------------------------------------------------------
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (data && data.bold) {
			value = `<span style="font-weight:700;">${value}</span>`;
		}
		if (data && !data.bold) {
			if (column.fieldname === "working_hours" && data.working_hours === 0) {
				value = `<span style="color:#aaa;">${value}</span>`;
			}
			if (column.fieldname === "ot_hours" && data.ot_hours > 0) {
				value = `<span style="">${value}</span>`;
			}
		}
		return value;
	},

	// -------------------------------------------------------------------------
	// Chart — 4 datasets: Working Hours, OT Hours, Working Amount, OT Amount
	// Uses two Y-axes: hours (left) and amounts (right via scale label trick)
	// -------------------------------------------------------------------------
	get_chart_data: function (columns, result) {
		// Skip Total/bold rows and collect unique months in order
		const months    = [];
		const monthSeen = {};

		result.forEach(function (row) {
			if (row.month && row.month !== __("Total") && !row.bold && !monthSeen[row.month]) {
				months.push(row.month);
				monthSeen[row.month] = true;
			}
		});

		function sumByMonth(field) {
			return months.map(function (m) {
				return result
					.filter(r => r.month === m && !r.bold)
					.reduce((acc, r) => acc + (r[field] || 0), 0);
			});
		}

		return {
			data: {
				labels: months,
				datasets: [
					{
						name:      __("Working Hours"),
						values:    sumByMonth("working_hours"),
						chartType: "bar",
					},
					{
						name:      __("OT Hours"),
						values:    sumByMonth("ot_hours"),
						chartType: "bar",
					},
					{
						name:      __("Working Hour Amount"),
						values:    sumByMonth("working_hour_amount"),
						chartType: "bar",
					},
					{
						name:      __("OT Hour Amount"),
						values:    sumByMonth("ot_hour_amount"),
						chartType: "bar",
					},
				],
			},
			type: "axis-mixed",
			barOptions:  { stacked: false },
			lineOptions: { regionFill: 0, hideDots: 0 },
			colors: ["#fa5d77ff", "#4da6ff", "#00c49f", "#ff7f50"],
		};
	},
};