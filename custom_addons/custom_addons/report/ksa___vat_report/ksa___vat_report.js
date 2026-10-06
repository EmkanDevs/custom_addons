frappe.query_reports["KSA - VAT Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_start()
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_end()
        },
        {
            fieldname: "root_type",
            label: __("Root Type"),
            fieldtype: "Select",
            options: [
                "",
                "Asset",
                "Liability",
                "Equity",
                "Income",
                "Expense"
            ].join("\n")
        },
        {
            fieldname: "source",
            label: __("Source"),
            fieldtype: "Select",
            options: [
                "",
                "Sales Invoice",
                "Purchase Invoice",
                "Payment Entry",
                "Journal Entry"
            ].join("\n")
        },
        {
            fieldname: "customer_supplier",
            label: __("Customer/Supplier"),
            fieldtype: "Data"
        }
    ]
};