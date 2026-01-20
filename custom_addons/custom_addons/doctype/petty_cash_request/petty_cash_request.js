frappe.ui.form.on("Petty Cash Request", {
    setup(frm) {
        frm.make_methods = {
            "Expense Claim": () => {
                frappe.model.open_mapped_doc({
                    method: "custom_addons.custom_addons.doctype.petty_cash_request.petty_cash_request.make_expense_claim",
                    frm: frm,
                });
            },
        };
    },
    refresh(frm) {
        frm.set_query("employee", function () {
            return {
                filters: {
                    user_id: frappe.session.user,
                    docstatus:1
                }
            };
        });
        frm.trigger('show_request_message');
        frm.trigger('show_purchase_expense_data');
        frm.trigger('add_custom_popup_for_purchase_receipt')
    },

    onload(frm) {
        frm.trigger('show_request_message');
    },

    validate(frm) {
        frm.trigger('show_request_message');
    },

    show_request_message(frm) {
        let required_amount = frm.doc.required_amount;
        let received_amount = frm.doc.received_amount;
        let component = $(`
            <div class="current-company-branch-message form-message red"><div style="font-size:25px">Request Amount <strong>"${required_amount}"</strong> is changed.Total Received is <strong>"${received_amount}"</strong></div></div>
        `);

        // Insert the component at the top of the .form-layout
        $('.form-layout .current-company-branch-message').remove();
        if (required_amount > received_amount ){
            $(".form-layout").prepend(component);
    }
    },
    show_purchase_expense_data(frm) {
        frappe.call({
            method: "custom_addons.custom_addons.doctype.petty_cash_request.petty_cash_request.fetch_purchaseorder_and_expenseclaim_details",
            args: { petty_cash_request: frm.doc.name },
            callback: function (r) {
                if (r.message) {
                    $(frm.fields_dict.custom_html_tab.wrapper).html(r.message);
    
                    // Bind click event after rendering
                    $(".remove-pr").click(function () {
                        let pr_name = $(this).data("pr");
                        clear_petty_cash_request(pr_name, frm);
                        
                    });
                } else {
                    $(frm.fields_dict.custom_html_tab.wrapper).html("<p>No attachments found.</p>");
                }
            }
        });
    },
    
    add_custom_popup_for_purchase_receipt(frm) {
        frm.add_custom_button(__("Purchase Receipt"), function() {
            frappe.db.get_list('Purchase Receipt', {
                fields: ['name', 'posting_date'],
                filters: { 
                    docstatus: 1, 
                    petty_cash_employee: frm.doc.employee ,
                    petty_cash_request : ["is","not set"]
                },
                limit: 50
            }).then(records => {
                console.log("Fetched Purchase Receipts: ", records);
    
                if (!records || records.length === 0) {
                    frappe.msgprint(__("No new Purchase Receipts available."));
                    return;
                }
    
                const already_linked_receipts = frm.doc.purchase_receipts?.map(d => d.purchase_receipt) || [];
                console.log("Existing linked receipts:", already_linked_receipts);
    
                // Keep full records instead of just names
                const available_records = records.filter(rec => !already_linked_receipts.includes(rec.name));
    
                if (available_records.length === 0) {
                    frappe.msgprint(__("No new Purchase Receipts available."));
                    return;
                }
    
                const message_html = `<div style="margin-bottom: 10px; color: #007bff; font-weight: bold;">
                                        Please select the Purchase Receipts you want to link:
                                      </div>`;
    
                let options_html = `<table class="table table-bordered">
                                    <thead>
                                        <tr>
                                            <th>Select</th>
                                            <th>Purchase Receipt</th>
                                            <th>Posting Date</th>
                                        </tr>
                                    </thead>
                                    <tbody>`;
    
                available_records.forEach(pr => {
                    options_html += `<tr>
                                        <td><input type="checkbox" class="pr_check" value="${pr.name}"></td>
                                        <td>${pr.name}</td>
                                        <td>${pr.posting_date || 'Not Available'}</td>
                                    </tr>`;
                });
    
                options_html += `</tbody></table>`;
    
                const dialog = new frappe.ui.Dialog({
                    title: __("Select Purchase Receipts"),
                    fields: [
                        {
                            fieldname: "receipt_selection",
                            fieldtype: "HTML",
                            options: `${message_html}${options_html}`
                        }
                    ],
                    primary_action_label: __('Submit'),
                    primary_action() {
                        const selected = [];
                        $(dialog.fields_dict.receipt_selection.wrapper).find('.pr_check:checked').each(function() {
                            selected.push($(this).val());
                        });
    
                        if (selected.length === 0) {
                            frappe.throw(__("Please select at least one Purchase Receipt"));
                            return;
                        }
    
                        frappe.call({
                            method: "custom_addons.custom_addons.doctype.petty_cash_request.petty_cash_request.set_petty_cash",
                            args: {
                                purchase_receipts: selected,
                                data: frm.doc.name
                            },
                            callback: function(response) {
                                frappe.show_alert({
                                    message: __(`Processed ${selected.length} Purchase Receipt(s).`),
                                    indicator: 'green'
                                });
                                frm.refresh();
                            }
                        });
    
                        dialog.hide();
                    }
                });
    
                dialog.show();
            });
        }, __("Mapping"));
    }
    
});

function clear_petty_cash_request(pr_name, frm) {
    frappe.call({
        method: "custom_addons.custom_addons.doctype.petty_cash_request.petty_cash_request.clear_petty_cash_request",
        args: { purchase_receipt: pr_name },
        callback: function (r) {
            if (r.message === "success") {
                frappe.show_alert({ message: "Successfully Removed", indicator: 'green' });
                // Re-fetch the data after deletion
                window.location.reload();
            } else {
                frappe.msgprint("Failed to remove.");
            }
        }
    });
}