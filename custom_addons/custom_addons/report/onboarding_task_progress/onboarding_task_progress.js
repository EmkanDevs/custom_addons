// Copyright (c) 2026, Administrator and contributors
// For license information, please see license.txt

frappe.query_reports["Onboarding Task Progress"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		},
		{
			fieldname: "boarding_status",
			label: __("Onboarding Status"),
			fieldtype: "Select",
			options: "\nPending\nIn Process\nCompleted",
		},
		{
			fieldname: "task_status",
			label: __("Task Status"),
			fieldtype: "Select",
			options: "\nOpen\nWorking\nPending Review\nCompleted\nCancelled",
		},
		{
			fieldname: "user",
			label: __("Assigned User"),
			fieldtype: "Link",
			options: "User",
		},
	],
};
