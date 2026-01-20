// Copyright (c) 2025, Finbyz and contributors
// For license information, please see license.txt

frappe.ui.form.on('Project Site Violation', {
    onload: function(frm) {
        // Filter for Account fields
        let account_filter = {
            filters: {
                company: 'Construction Pillars Company',
                is_group: 0,
                account_currency: 'SAR'
            }
        };

        frm.set_query('from_account', () => account_filter);
        frm.set_query('to_account', () => account_filter);
    },

    refresh: function(frm) {
        // Add custom button
        frm.add_custom_button(__('Create Payment Request'), function() {
            frappe.call({
                method: "custom_addons.custom_addons.doctype.project_site_violation.project_site_violation.make_payment_request",
                args: {
                    docname: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.sync(r.message);
                        frappe.show_alert({
                            message: __("Payment Request {0} created as Draft", [r.message.name]),
                            indicator: "green"
                        });
                        frappe.set_route("Form", "Payment Requester", r.message.name);
                    }
                }
            });
        }, __("Create"));
        frm.add_custom_button('Create Journal Entry', () => {
            if (!frm.doc.from_account || !frm.doc.to_account) {
                frappe.msgprint(__('Please set both From Account and To Account'));
                return;
            }

            frappe.call({
                method: 'frappe.client.insert',
                args: {
                    doc: {
                        doctype: 'Journal Entry',
                        posting_date: frappe.datetime.now_date(),
                        project_site_violation:frm.doc.name,
                        company: frm.doc.company,
                        cheque_no: frm.doc.sadad_no,
                        cheque_date: frm.doc.payment_due_date,
                        accounts: [
                            {
                                account: frm.doc.from_account,
                                debit_in_account_currency: frm.doc.penalty_amount  // or set based on amount field
                            },
                            {
                                account: frm.doc.to_account,
                                credit_in_account_currency: frm.doc.penalty_amount  // should match credit
                            }
                        ],
                        user_remark: `Auto-created from Project Site Violation: ${frm.doc.name}`
                    }
                },
                callback: function(response) {
                    if (response.message) {
                        frappe.msgprint(__('Journal Entry {0} created', [response.message.name]));
                        frappe.set_route('Form', 'Journal Entry', response.message.name);
                    }
                }
            });
        });
    }
});


