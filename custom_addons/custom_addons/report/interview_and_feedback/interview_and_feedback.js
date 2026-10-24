// Copyright (c) 2026, Administrator and contributors
// For license information, please see license.txt

frappe.query_reports["Interview and Feedback"] = {
	filters: [
		{
			fieldname: "designation",
			label: __("Designation"),
			fieldtype: "Link",
			options: "Designation",
		},
		{
			fieldname: "interview_round",
			label: __("Interview Round"),
			fieldtype: "Link",
			options: "Interview Round",
		},
		{
			fieldname: "interviewer",
			label: __("Interviewer"),
			fieldtype: "Link",
			options: "User",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nPending\nUnder Review\nScheduled\nCleared\nRejected\nCancelled",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
		},
	],
};
