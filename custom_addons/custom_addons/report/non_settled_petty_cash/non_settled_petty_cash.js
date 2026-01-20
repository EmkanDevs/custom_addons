// Copyright (c) 2025, Finbyz and contributors
// For license information, please see license.txt

frappe.query_reports["Non-Settled Petty Cash"] = {
	"filters": [
		{
			"fieldname": "project",
			"label": "Project",
			"fieldtype": "Link",
			"options": "Project",
		},
		{
			"fieldname":"department",
			"label":"Department",
			"fieldtype":"Link",
			"options":"Department"
		},
		{
			"fieldname": "employee",
			"label": "Employee",
			"fieldtype": "Link",
			"options": "Employee",
		},
	],
	"formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (!data) return value;

        if (column.fieldname === "total_received" && data.total_received > 0) {
            value = `<span style="color: green; font-weight: bold;">${value}</span>`;
        }
		if (column.fieldname === "project_name" && data.project_name){
			value = `<span style="color:red;font-weight: bold;">${value}</span>`;
		}

        return value;
    }
};
