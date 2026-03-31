frappe.ui.form.on("Expense Claim", {
    setup: function (frm) {
        // Filter tax accounts in the expense child table
        frm.set_query("custom_account_head", "expenses", function () {
            return {
                filters: [
                    ["company", "=", frm.doc.company],
                    ["account_type", "in", ["Tax", "Chargeable", "Income Account", "Expenses Included In Valuation"]],
                ],
            };
        });
    },

    refresh: function (frm) {
        // --- Grid Button Logic ---
        let grid = frm.fields_dict.expenses.grid;
        $(grid.wrapper).find('.custom-pi-btn').remove();

        let btn = $(`
            <button class="btn btn-xs btn-primary custom-pi-btn" style="margin-left: 10px;">
                Create Purchase Invoice
            </button>
        `);

        $(grid.wrapper).find('.grid-add-row').after(btn);

        btn.on('click', function () {
            let selected_rows = grid.get_selected_children();

            if (!selected_rows.length) {
                frappe.msgprint(__('Please select at least one row from the expenses table.'));
                return;
            }

            if (selected_rows.length > 1) {
                frappe.msgprint(__('You can only create a Purchase Invoice for one row at a time.'));
                return;
            }

            let first_row = selected_rows[0];

            frappe.model.with_doctype('Purchase Invoice', function () {
                let pi = frappe.model.get_new_doc('Purchase Invoice');

                pi.company = frm.doc.company;
                pi.employee = frm.doc.employee;
                pi.supplier = first_row.supplier;
                pi.bill_no = first_row.custom_invoice_number;
                pi.posting_date = first_row.expense_date;
                pi.project = frm.doc.project;
                pi.bill_date = first_row.expense_date;
                pi.cost_center = first_row.cost_center;

                // Mapping Child Rows to PI Items
                selected_rows.forEach(row => {
                    let item_row = frappe.model.add_child(pi, 'items');
                    item_row.qty = 1;
                    item_row.rate = row.amount; // Using 'amount' as the item rate
                    item_row.expense_account = row.default_account;
                    item_row.cost_center = row.cost_center || frm.doc.cost_center;

                    // Mapping Tax from Expense Row to PI Tax Table
                    if (row.custom_tax_amount && row.custom_account_head) {
                        let tax_row = frappe.model.add_child(pi, 'taxes');
                        tax_row.charge_type = "Actual";
                        tax_row.account_head = row.custom_account_head;
                        tax_row.tax_amount = row.custom_tax_amount;
                        tax_row.description = "VAT from Expense Row";
                    }
                });

                frappe.set_route('Form', 'Purchase Invoice', pi.name);
            });
        });
    },

    // When parent project changes, update all rows
    project: function (frm) {
        if (frm.doc.project) {
            (frm.doc.expenses || []).forEach(row => {
                frappe.model.set_value(row.doctype, row.name, "project", frm.doc.project);
            });
        }
    },
});
//     // Trigger the Python calculation method
//     calculate_taxes_from_server: function(frm) {
//         frappe.call({
//             doc: frm.doc,
//             method: 'calculate_taxes', // Your backend whitelisted method
//             callback: function() {
//                 frm.refresh_field("taxes");
//                 frm.refresh_field("total_taxes_and_charges");
//                 frm.refresh_field("grand_total");
//                 frm.refresh_field("total_claimed_amount");
//             }
//         });
//     }
// });

// // Handling updates in the Expense Table
// frappe.ui.form.on('Expense Claim Detail', {
//     amount: function(frm, cdt, cdn) {
//         frm.trigger('calculate_taxes_from_server');
//     },
//     sanctioned_amount: function(frm, cdt, cdn) {
//         frm.trigger('calculate_taxes_from_server');
//     },
//     expenses_remove: function(frm) {
//         frm.trigger('calculate_taxes_from_server');
//     }
// });