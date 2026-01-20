// Copyright (c) 2025, Finbyz and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Temp Room Booking", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Temp Room Booking", {
    refresh: function(frm) {
        frm.add_custom_button(__('Create Payment Request'), function() {
            frappe.call({
                method: "custom_addons.custom_addons.doctype.temp_room_booking.temp_room_booking.make_trb_payment_request",
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
    }
});
