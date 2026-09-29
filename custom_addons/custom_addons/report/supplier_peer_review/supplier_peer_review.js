// Copyright (c) 2025, Finbyz and contributors
// For license information, please see license.txt

frappe.query_reports["Supplier Peer Review"] = {
	"filters": [
			{
				"fieldname": "id",
				"label": __("ID"),
				"fieldtype": "MultiSelectList",
				"options": "Purchase Order",
				"get_data": function(txt) {
					return frappe.db.get_link_options("Purchase Order", txt);
				}
			},
			{
				"fieldname": "project",
				"label": __("Project"),
				"fieldtype": "MultiSelectList",
				"options": "Project",
				"get_data": function(txt) {
					return frappe.db.get_link_options("Project", txt);
				}
			},
			{
				"fieldname": "from_date",
				"label": "From Date",
				"fieldtype": "Date",
				"default": frappe.datetime.add_days(frappe.datetime.get_today(), -7),
				"reqd": 1
			},
			{
				"fieldname": "to_date",
				"label": "To Date",
				"fieldtype": "Date",
				"default": frappe.datetime.get_today(),
				"reqd": 1
			}
		]
};
