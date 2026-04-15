// Copyright (c) 2026, Administrator and contributors
// For license information, please see license.txt

frappe.query_reports["Staff Document Expiration"] = {
    filters: [
        {
            fieldname: "days_to_expire",
            label: __("Days to Expire"),
            fieldtype: "Int",
        },
		{
            fieldname: "employee",
            label: __("Employee"),
            fieldtype: "Link",
            options: "Employee",
        },
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer",
        },
		{
            fieldname: "supplier",
            label: __("Supplier"),
            fieldtype: "Link",
            options: "Supplier",
        },
        {
            fieldname: "show_expired",
            label: __("Expired"),
            fieldtype: "Check",
        },
    ]
};

