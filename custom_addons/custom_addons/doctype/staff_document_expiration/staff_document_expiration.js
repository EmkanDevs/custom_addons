// Copyright (c) 2026, Administrator and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Staff Document Expiration", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("Staff Document Expiration", {

    expire_on: function(frm) {
        calculate_expires_in_days(frm);
    },

    refresh: function(frm) {
        calculate_expires_in_days(frm);
    }

});

function calculate_expires_in_days(frm) {
    if (!frm.doc.expire_on) {
        frm.doc.expires_in_days = null;
        frm.refresh_field("expires_in_days");
        return;
    }

    const today = frappe.datetime.get_today();
    const expire_on = frm.doc.expire_on;

    const today_obj = frappe.datetime.str_to_obj(today);
    const expire_obj = frappe.datetime.str_to_obj(expire_on);

    const diff = frappe.datetime.get_diff(expire_obj, today_obj);

    frm.doc.expires_in_days = diff;
    frm.refresh_field("expires_in_days");
}