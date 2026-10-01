// Copyright (c) 2026, Finbyz and contributors
// For license information, please see license.txt

frappe.query_reports["Custom General Ledger Detailed"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
        {
            "fieldname": "finance_book",
            "label": __("Finance Book"),
            "fieldtype": "Link",
            "options": "Finance Book"
        },
        {
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
			width: "60px",
		},
        {
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
			width: "60px",
		},
        {
			fieldname: "account",
			label: __("Account"),
			fieldtype: "MultiSelectList",
			options: "Account",
			get_data: function (txt) {
				return frappe.db.get_link_options("Account", txt, {
					company: frappe.query_report.get_filter_value("company"),
				});
			},
		},
        {
            "fieldname": "voucher_no",
            "label": __("Voucher No"),
            "fieldtype": "Data",
            "on_change": function () {
                // This will safely trigger because the categorize_by filter exists in your report
                frappe.query_report.set_filter_value("categorize_by", "Categorize by Voucher (Consolidated)");
            }
        },
		{
            "fieldname": "against_voucher_no",
            "label": __("Against Voucher No"),
            "fieldtype": "Data"
        },
        {
			fieldtype: "Break",
		},
		{
			fieldname: "party_type",
			label: __("Party Type"),
			fieldtype: "Autocomplete",
			options: Object.keys(frappe.boot.party_account_types),
			on_change: function () {
				frappe.query_report.set_filter_value("party", []);
			},
		},
        // {
        //     "fieldname": "party",
        //     "label": __("Party"),
        //     "fieldtype": "MultiSelectList",
        //     "get_data": function(txt) {
        //         let party_type = frappe.query_report.get_filter_value("party_type");
        //         if (!party_type) {
        //             frappe.msgprint(__("Please select a Party Type first."));
        //             return [];
        //         }
        //         return frappe.db.get_link_options(party_type, txt);
        //     }
        // },
        {
            "fieldname": "party",
            "label": __("Party"),
            "fieldtype": "MultiSelectList",
            "options": "party_type",
            "get_data": function (txt) {
                if (!frappe.query_report.filters) return;

                let party_type = frappe.query_report.get_filter_value("party_type");
                if (!party_type) return;

                return frappe.db.get_link_options(party_type, txt);
            },
            "on_change": function () {
                var party_type = frappe.query_report.get_filter_value("party_type");
                var parties = frappe.query_report.get_filter_value("party") || [];

                if (!party_type || parties.length === 0 || parties.length > 1) {
                    if (frappe.query_report.get_filter("party_name")) {
                        frappe.query_report.set_filter_value("party_name", "");
                    }
                    if (frappe.query_report.get_filter("tax_id")) {
                        frappe.query_report.set_filter_value("tax_id", "");
                    }
                    return;
                } else {
                    var party = parties[0];
                    var fieldname = erpnext.utils.get_party_name(party_type) || "name";
                    
                    frappe.db.get_value(party_type, party, fieldname, function (value) {
                        if (value && frappe.query_report.get_filter("party_name")) {
                            frappe.query_report.set_filter_value("party_name", value[fieldname]);
                        }
                    });

                    if (party_type === "Customer" || party_type === "Supplier") {
                        frappe.db.get_value(party_type, party, "tax_id", function (value) {
                            if (value && frappe.query_report.get_filter("tax_id")) {
                                frappe.query_report.set_filter_value("tax_id", value["tax_id"]);
                            }
                        });
                    }
                }
            }
        },
        {
			fieldname: "party_name",
			label: __("Party Name"),
			fieldtype: "Data",
			hidden: 1,
		},
		{
			fieldname: "categorize_by",
			label: __("Categorize by"),
			fieldtype: "Select",
			options: [
				"",
				{
					label: __("Categorize by Voucher"),
					value: "Categorize by Voucher",
				},
				{
					label: __("Categorize by Voucher (Consolidated)"),
					value: "Categorize by Voucher (Consolidated)",
				},
				{
					label: __("Categorize by Account"),
					value: "Categorize by Account",
				},
				{
					label: __("Categorize by Party"),
					value: "Categorize by Party",
				},
			],
			default: "Categorize by Voucher (Consolidated)",
		},
        {
            "fieldname": "presentation_currency",
            "label": __("Currency"),
            "fieldtype": "Select",
            "options": erpnext.get_presentation_currency_list()
        },
        {
			fieldname: "tax_id",
			label: __("Tax Id"),
			fieldtype: "Data",
			hidden: 1,
		},
        {
            "fieldname": "cost_center",
            "label": __("Cost Center"),
            "fieldtype": "MultiSelectList",
            get_data: function (txt) {
				return frappe.db.get_link_options("Cost Center", txt, {
					company: frappe.query_report.get_filter_value("company"),
				});
			},
        },
		{
            "fieldname": "task",
            "label": __("Task"),
            "fieldtype": "MultiSelectList",
            "get_data": function(txt) {
                return frappe.db.get_link_options('Task', txt);
            }
        },
        {
            "fieldname": "region_location",
            "label": __("Region Location"),
			"fieldtype": "MultiSelectList",
            "get_data": function(txt) {
                return frappe.db.get_link_options('Location', txt);
            }
        },
        {
            "fieldname": "employee",
            "label": __("Employee"),
			"fieldtype": "MultiSelectList",
            "get_data": function(txt) {
                return frappe.db.get_link_options('Employee', txt);
            }
        },
        {
            "fieldname": "department",
            "label": __("Department"),
			"fieldtype": "MultiSelectList",
            "get_data": function(txt) {
                return frappe.db.get_link_options('Department', txt);
            }
        },
        {
            "fieldname": "asset",
            "label": __("Asset"),
			"fieldtype": "MultiSelectList",
            "get_data": function(txt) {
                return frappe.db.get_link_options('Asset', txt);
            }
        },
        {
            "fieldname": "project",
            "label": __("Project"),
			"fieldtype": "MultiSelectList",
            "get_data": function(txt) {
                return frappe.db.get_link_options('Project', txt);
            }
        },
        {
            "fieldname": "include_dimensions",
            "label": __("Consider Accounting Dimensions"),
            "fieldtype": "Check",
            "default": frappe.boot.sysdefaults.disable_include_dimensions ? 0 : 1
        },
        {
            "fieldname": "disable_opening_balance_calculation",
            "label": __("Disable Opening Balance Calculation"),
            "fieldtype": "Check",
            "default": 0
        },
        {
            "fieldname": "show_opening_entries",
            "label": __("Show Opening Entries"),
            "fieldtype": "Check",
            "default": 0
        },
        {
            "fieldname": "include_default_book_entries",
            "label": __("Include Default FB Entries"),
            "fieldtype": "Check",
            "default": 1
        },
        {
            "fieldname": "show_cancelled_entries",
            "label": __("Show Cancelled Entries"),
            "fieldtype": "Check",
            "default": 0
        },
        {
            "fieldname": "show_net_values_in_party_account",
            "label": __("Show Net Values in Party Account"),
            "fieldtype": "Check",
            "default": 0
        },

        // Row 5 (Checkboxes)
        {
            "fieldname": "show_amount_in_company_currency",
            "label": __("Show Credit / Debit in Company Currency"),
            "fieldtype": "Check",
            "default": 0
        },
        {
            "fieldname": "add_values_in_transaction_currency",
            "label": __("Add Columns in Transaction Currency"),
            "fieldtype": "Check",
            "default": 0
        },
        {
            "fieldname": "show_remarks",
            "label": __("Show Remarks"),
            "fieldtype": "Check",
            "default": 0
        },
        {
            "fieldname": "ignore_err",
            "label": __("Ignore Exchange Rate Revaluation and Gain / Loss Journals"),
            "fieldtype": "Check",
            "default": 0
        },
        {
            "fieldname": "ignore_cr_dr_notes",
            "label": __("Ignore System Generated Credit / Debit Notes"),
            "fieldtype": "Check",
            "default": 0
        }

	]
};