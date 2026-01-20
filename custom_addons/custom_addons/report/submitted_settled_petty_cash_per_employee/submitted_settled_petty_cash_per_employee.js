frappe.query_reports["Submitted Settled Petty Cash per Employee"] = {
    "filters": [
        {
            "fieldname": "employee",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options": "Employee",
            "default": "",
            "reqd": 0,
            "get_query": function() {
                return {
                    query: "frappe.desk.search.search_link",
                    filters: {
                        doctype: "Employee"
                    }
                };
            }
        },
        {
            "fieldname": "project",
            "label": __("Project"),
            "fieldtype": "Link",
            "options": "Project"
        },
        {
            "fieldname": "date_range",
            "label": __("Date Range"),
            "fieldtype": "DateRange"
        }
    ],

    onload: function(report) {
        frappe.call({
            method: "frappe.client.get_value",
            args: {
                doctype: "Employee",
                filters: { user_id: frappe.session.user },
                fieldname: "name"
            },
            callback: function(r) {
                if (r.message) {
                    report.set_filter_value("employee", r.message.name);
                }
            }
        });
    }
};
