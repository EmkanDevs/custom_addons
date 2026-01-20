frappe.ui.form.on("Rental Contract", {
    refresh: function(frm) {
        frm.add_custom_button(__('Create Payment Request'), function() {
            frappe.call({
                method: "custom_addons.custom_addons.doctype.rental_contract.rental_contract.make_payment_request",
                args: {
                    rental_contract: frm.doc.name
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
    }
});
