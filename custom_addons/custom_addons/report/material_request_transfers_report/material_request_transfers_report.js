// Copyright (c) 2025, Finbyz and contributors
// For license information, please see license.txt

frappe.query_reports["Material Request Transfers Report"] = {
    "filters": [
        {
            "fieldname": "material_request",
            "label": __("Material Request"),
            "fieldtype": "Link",
            "options": "Material Request",
            "width": "160px"
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 0,
            "width": "120px"
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 0,
            "width": "120px"
        }
    ]
};
