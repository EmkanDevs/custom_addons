// Copyright (c) 2026, Administrator and contributors
// For license information, please see license.txt

frappe.query_reports["Timesheet All Employee"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.month_start(),
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.month_end(),
        },
        {
            fieldname: "specific_date",
            label: __("Specific Date"),
            fieldtype: "Date",
            description: __("Filter logs for a specific day"),
        },
        {
            fieldname: "employee",
            label: __("Employee"),
            fieldtype: "MultiSelectList",
            get_data: function (txt) {
                return frappe.db.get_link_options("Employee", txt);
            },
        },
        {
            fieldname: "department",
            label: __("Department"),
            fieldtype: "MultiSelectList",
            get_data: function (txt) {
                return frappe.db.get_link_options("Department", txt);
            },
        },
        {
            fieldname: "designation",
            label: __("Designation"),
            fieldtype: "MultiSelectList",
            get_data: function (txt) {
                return frappe.db.get_list("Designation", {
                    fields: ["name"],
                    filters: txt ? [["name", "like", "%" + txt + "%"]] : [],
                    limit: 50,
                }).then(function (data) {
                    return data.map(function (d) {
                        return { value: d.name, description: d.name };
                    });
                });
            },
        },
        {
            fieldname: "status",
            label: __("Timesheet Status"),
            fieldtype: "Select",
            options: "\nDraft\nSubmitted\nCancelled",
        },
        {
            fieldname: "total_hours_gt",
            label: __("Total Hours >"),
            fieldtype: "Float",
        },
        {
            fieldname: "total_hours_lt",
            label: __("Total Hours <"),
            fieldtype: "Float",
        },
        {
            fieldname: "show_zero_working_hours",
            label: __("Show Zero Working Hours Only"),
            fieldtype: "Check",
            default: 0,
        },
    ],
};