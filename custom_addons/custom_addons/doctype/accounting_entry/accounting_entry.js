// Copyright (c) 2026, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Accounting Entry', {
    setup: function (frm) {
        // Set query filters
        frm.set_query('company', function () {
            return {
                filters: {
                    is_group: 0
                }
            };
        });

        

        frm.set_query('account', 'accounts', function (doc, cdt, cdn) {
            return {
                filters: {
                    company: doc.company,
                    is_group: 0
                }
            };
        });

        frm.set_query('tax_category', 'accounts', function (doc, cdt, cdn) {
            return {
                filters: {
                    company: doc.company,
                    disabled: 0
                }
            };
        });
    },

    department: function (frm) {
        (frm.doc.accounts || []).forEach(row => {
            frappe.model.set_value(
                row.doctype,
                row.name,
                'department',
                frm.doc.department
            );
        });

        frm.refresh_field('accounts');
    },

    onload: function (frm) {
        if (frm.is_new() && !frm.doc.company) {
            let default_company = frappe.defaults.get_user_default("Company") || frappe.defaults.get_default("company");
            if (default_company) {
                frm.set_value('company', default_company);
            }
        }
    },

    refresh: function (frm) {
        frm.trigger('update_party_field_and_tax_types');
        frm.trigger('toggle_auto_row_readonly');
        frm.trigger('calculate_totals');
        frm.trigger('setup_invoice_actions');
    },

    onload_post_render: function (frm) {
        frm.trigger('update_party_field_and_tax_types');
        frm.trigger('toggle_auto_row_readonly');
    },

    tax_type: function (frm) {
        frm.set_value('party', '');
        frm.trigger('update_party_field_and_tax_types');
        frm.trigger('sync_auto_tax_rows');
        frm.trigger('setup_invoice_actions');
    },

    company: function (frm) {
        if (frm.doc.company) {
            frappe.db.get_value('Company', frm.doc.company, 'default_currency', function (r) {
                if (r && r.default_currency) {
                    frm.set_value('company_currency', r.default_currency);
                }
            });
        }
        frm.trigger('sync_auto_tax_rows');
    },

    tax_method: function (frm) {
        frm.trigger('sync_auto_tax_rows');
    },

    setup_invoice_actions: function (frm) {
        if (frm.is_new()) return;

        const is_inward = (frm.doc.tax_type === 'Inward');
        const invoice_doctype = is_inward ? 'Purchase Invoice' : 'Sales Invoice';
        const linked_invoice = is_inward ? frm.doc.purchase_invoice : frm.doc.sales_invoice;

        if (linked_invoice) {
            frm.add_custom_button(__('View {0}', [__(invoice_doctype)]), function () {
                frappe.set_route('Form', invoice_doctype, linked_invoice);
            });
        }
    },

    update_party_field_and_tax_types: function (frm) {
        const is_inward = (frm.doc.tax_type === 'Inward');
        const party_type = is_inward ? 'Supplier' : 'Customer';
        const party_label = is_inward ? __('Supplier (If Any)') : __('Customer (If Any)');
        const template_type = is_inward ? 'Purchase Taxes and Charges Template' : 'Sales Taxes and Charges Template';

        if (frm.doc.party_type !== party_type) {
            frm.set_value('party_type', party_type);
        }
        frm.set_df_property('party', 'label', party_label);

        // Update tax template type in all child rows
        (frm.doc.accounts || []).forEach(row => {
            if (row.tax_template_type !== template_type) {
                frappe.model.set_value(row.doctype, row.name, 'tax_template_type', template_type);
            }
        });
    },

    sync_auto_tax_rows: function (frm) {
        if (frm.doc.docstatus !== 0) return;

        if (frm.doc.tax_method !== 'Auto') {
            // Remove any auto tax rows in Manually mode
            let rows_to_remove = (frm.doc.accounts || []).filter(r => r.is_auto_tax_row);
            rows_to_remove.forEach(r => {
                frappe.model.clear_doc(r.doctype, r.name);
            });
            frm.refresh_field('accounts');
            frm.trigger('calculate_totals');
            return;
        }

        let is_inward = (frm.doc.tax_type === 'Inward');
        let template_type = is_inward ? 'Purchase Taxes and Charges Template' : 'Sales Taxes and Charges Template';
        let company_currency = frm.doc.company_currency || 'SAR';

        let manual_rows = (frm.doc.accounts || []).filter(r => !r.is_auto_tax_row && (flt(r.debit) > 0 || flt(r.credit) > 0));

        // Collect all unique templates selected in manual rows
        let templates_to_fetch = [];
        manual_rows.forEach(r => {
            if (r.tax_category && !templates_to_fetch.includes(r.tax_category)) {
                templates_to_fetch.push(r.tax_category);
            }
        });

        if (templates_to_fetch.length === 0) {
            // No tax templates selected -> remove existing auto tax rows
            let rows_to_remove = (frm.doc.accounts || []).filter(r => r.is_auto_tax_row);
            rows_to_remove.forEach(r => {
                frappe.model.clear_doc(r.doctype, r.name);
            });
            frm.refresh_field('accounts');
            frm.trigger('calculate_totals');
            return;
        }

        // Fetch tax template doc using standard frappe.db.get_doc
        let promises = templates_to_fetch.map(tmpl_name => {
            return frappe.db.get_doc(template_type, tmpl_name);
        });

        Promise.all(promises).then(results => {
            let template_taxes_map = {};
            templates_to_fetch.forEach((name, idx) => {
                let doc = results[idx];
                template_taxes_map[name] = (doc && doc.taxes) ? doc.taxes : [];
            });

            let tax_summary = {}; // { account_head: total_tax_amount }

            manual_rows.forEach(r => {
                let base_amount = flt(is_inward ? r.debit_in_company_currency : r.credit_in_company_currency);
                if (base_amount > 0 && r.tax_category && template_taxes_map[r.tax_category]) {
                    let taxes = template_taxes_map[r.tax_category];
                    taxes.forEach(t => {
                        if (t.account_head && flt(t.rate) > 0) {
                            let tax_amt = flt(base_amount * (flt(t.rate) / 100.0), 2);
                            if (!tax_summary[t.account_head]) {
                                tax_summary[t.account_head] = 0.0;
                            }
                            tax_summary[t.account_head] += tax_amt;
                        }
                    });
                }
            });

            // Remove existing auto tax rows
            let existing_auto_rows = (frm.doc.accounts || []).filter(r => r.is_auto_tax_row);
            existing_auto_rows.forEach(r => {
                frappe.model.clear_doc(r.doctype, r.name);
            });

            // Add newly calculated auto tax rows
            Object.keys(tax_summary).forEach(account_head => {
                let tax_amt = flt(tax_summary[account_head], 2);
                if (tax_amt > 0) {
                    frm.add_child('accounts', {
                        'account': account_head,
                        'account_currency': company_currency,
                        'currency': company_currency,
                        'exchange_rate': 1.0,
                        'debit': is_inward ? tax_amt : 0,
                        'debit_in_company_currency': is_inward ? tax_amt : 0,
                        'credit': is_inward ? 0 : tax_amt,
                        'credit_in_company_currency': is_inward ? 0 : tax_amt,
                        'tax_template_type': template_type,
                        'is_auto_tax_row': 1
                    });
                }
            });

            frm.refresh_field('accounts');
            frm.trigger('calculate_totals');
            frm.trigger('toggle_auto_row_readonly');
        });
    },

    toggle_auto_row_readonly: function (frm) {
        const grid = frm.get_field('accounts').grid;
        if (grid && grid.grid_rows) {
            const readonly_fields = [
                'account', 'currency', 'exchange_rate', 'debit', 'credit',
                'debit_in_company_currency', 'credit_in_company_currency',
                'tax_category', 'project', 'employee', 'department'
            ];
            grid.grid_rows.forEach(grid_row => {
                if (grid_row.doc && grid_row.doc.is_auto_tax_row) {
                    readonly_fields.forEach(f => {
                        grid_row.toggle_editable(f, false);
                    });
                }
            });
        }
    },

    calculate_totals: function (frm) {
        let total_debit = 0;
        let total_debit_cc = 0;
        let total_credit = 0;
        let total_credit_cc = 0;

        (frm.doc.accounts || []).forEach(r => {
            total_debit += flt(r.debit);
            total_debit_cc += flt(r.debit_in_company_currency);
            total_credit += flt(r.credit);
            total_credit_cc += flt(r.credit_in_company_currency);
        });

        let difference = flt(total_debit_cc - total_credit_cc, 2);

        frm.set_value('total_debit', flt(total_debit, 2));
        frm.set_value('total_debit_company_currency', flt(total_debit_cc, 2));
        frm.set_value('total_credit', flt(total_credit, 2));
        frm.set_value('total_credit_company_currency', flt(total_credit_cc, 2));
        frm.set_value('difference', difference);

        frm.trigger('update_balance_indicator');
    },

    update_balance_indicator: function (frm) {
        // Always clear previous headline first so they never duplicate/stack
        frm.dashboard.clear_headline();

        let manual_rows = (frm.doc.accounts || []).filter(r => !r.is_auto_tax_row);
        let total_credit_cc = flt(frm.doc.total_credit_company_currency, 2);
        let total_debit_cc = flt(frm.doc.total_debit_company_currency, 2);

        // Do not show headline if there are no rows or both debit & credit are 0
        if (!manual_rows.length || (total_credit_cc === 0 && total_debit_cc === 0)) {
            return;
        }

        let diff = flt(frm.doc.difference, 2);

        if (Math.abs(diff) < 0.01) {
            frm.dashboard.set_headline(
                __('<span class="indicator green">&#10003; Entry is balanced. Debit and Credit both total {0}.</span>', [
                    format_currency(frm.doc.total_credit_company_currency, frm.doc.company_currency)
                ])
            );
        } else {
            let direction = diff > 0 ? __('more debit') : __('more credit');
            frm.dashboard.set_headline(
                __('<span class="indicator orange">&#9888; Not balanced &mdash; difference of {0} ({1}). Balance rows before submitting.</span>', [
                    format_currency(Math.abs(diff), frm.doc.company_currency),
                    direction
                ])
            );
        }
    },

    validate: function (frm) {
        frm.trigger('calculate_totals');
    }
});

frappe.ui.form.on('Accounting Entry Detail', {
    account: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.is_auto_tax_row) return;

        if (row.account) {
            frappe.db.get_value('Account', row.account, 'account_currency', function (r) {
                let acc_currency = (r && r.account_currency) ? r.account_currency : (frm.doc.company_currency || 'SAR');
                frappe.model.set_value(cdt, cdn, 'account_currency', acc_currency);
                frappe.model.set_value(cdt, cdn, 'currency', acc_currency);

                if (acc_currency === frm.doc.company_currency) {
                    frappe.model.set_value(cdt, cdn, 'exchange_rate', 1.0);
                } else {
                    frappe.call({
                        method: 'erpnext.setup.utils.get_exchange_rate',
                        args: {
                            from_currency: acc_currency,
                            to_currency: frm.doc.company_currency,
                            transaction_date: frm.doc.posting_date
                        },
                        callback: function (res) {
                            frappe.model.set_value(cdt, cdn, 'exchange_rate', flt(res.message) || 1.0);
                        }
                    });
                }
            });
        }
    },

    exchange_rate: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.is_auto_tax_row) return;

        let rate = flt(row.exchange_rate) || 1.0;
        frappe.model.set_value(cdt, cdn, 'debit_in_company_currency', flt(flt(row.debit) * rate, 2));
        frappe.model.set_value(cdt, cdn, 'credit_in_company_currency', flt(flt(row.credit) * rate, 2));
        frm.trigger('sync_auto_tax_rows');
    },

    debit: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.is_auto_tax_row) return;

        let debit_val = flt(row.debit);
        let rate = flt(row.exchange_rate) || 1.0;
        if (debit_val > 0) {
            frappe.model.set_value(cdt, cdn, 'credit', 0);
            frappe.model.set_value(cdt, cdn, 'credit_in_company_currency', 0);
        }
        frappe.model.set_value(cdt, cdn, 'debit_in_company_currency', flt(debit_val * rate, 2));
        frm.trigger('sync_auto_tax_rows');
    },

    credit: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.is_auto_tax_row) return;

        let credit_val = flt(row.credit);
        let rate = flt(row.exchange_rate) || 1.0;
        if (credit_val > 0) {
            frappe.model.set_value(cdt, cdn, 'debit', 0);
            frappe.model.set_value(cdt, cdn, 'debit_in_company_currency', 0);
        }
        frappe.model.set_value(cdt, cdn, 'credit_in_company_currency', flt(credit_val * rate, 2));
        frm.trigger('sync_auto_tax_rows');
    },

    tax_category: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.is_auto_tax_row) return;
        frm.trigger('sync_auto_tax_rows');
    },

    accounts_add: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (frm.doc.company_currency) {
            frappe.model.set_value(cdt, cdn, 'currency', frm.doc.company_currency);
            frappe.model.set_value(cdt, cdn, 'account_currency', frm.doc.company_currency);
            frappe.model.set_value(cdt, cdn, 'exchange_rate', 1.0);
        }
        let is_inward = (frm.doc.tax_type === 'Inward');
        let template_type = is_inward ? 'Purchase Taxes and Charges Template' : 'Sales Taxes and Charges Template';
        frappe.model.set_value(cdt, cdn, 'tax_template_type', template_type);
    },

    accounts_remove: function (frm) {
        frm.trigger('sync_auto_tax_rows');
    },

    before_accounts_remove: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row && row.is_auto_tax_row && frm.doc.tax_method === 'Auto') {
            frappe.throw(__('Cannot manually remove auto-calculated tax row. Switch Tax Method to "Manually" to edit or delete tax rows.'));
        }
    },

    form_render: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let is_inward = (frm.doc.tax_type === 'Inward');
        let template_type = is_inward ? 'Purchase Taxes and Charges Template' : 'Sales Taxes and Charges Template';
        if (row.tax_template_type !== template_type) {
            frappe.model.set_value(cdt, cdn, 'tax_template_type', template_type);
        }

        let grid_row = frm.get_field('accounts').grid.grid_rows_by_docname[cdn];
        if (row.is_auto_tax_row && grid_row) {
            const readonly_fields = [
                'account', 'currency', 'exchange_rate', 'debit', 'credit',
                'debit_in_company_currency', 'credit_in_company_currency',
                'tax_category', 'project', 'employee', 'department'
            ];
            readonly_fields.forEach(f => {
                grid_row.toggle_editable(f, false);
            });
        }
    }
});
