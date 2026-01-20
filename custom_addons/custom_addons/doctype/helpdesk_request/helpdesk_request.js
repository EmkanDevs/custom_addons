// Copyright (c) 2025, Finbyz and contributors
// For license information, please see license.txt

frappe.ui.form.on("Helpdesk Request", {
    refresh(frm) {
        if (frappe.session.user) {
            if (frm.doc.custom_user_details && frm.doc.custom_user_details.length > 0) {
                frm.doc.custom_user_details.forEach(row => {
                    if (row.user != frappe.session.user && !hasITSupportRole()) {
                        frappe.throw("You are not authorized to access this ticket");
                    }
                });
            }
        }
    },

    validate(frm) {
        if (frm.doc.custom_user_details && frm.doc.custom_user_details.length > 0) {
            frm.doc.custom_user_details.forEach(row => {
                if (row.user != frappe.session.user && !hasITSupportRole()) {
                    frappe.throw("You are not authorized to access this ticket");
                }
            });
        }
    },
});

// Function to check if user has IT Support roles
function hasITSupportRole() {
    const userRoles = frappe.user_roles;
    return userRoles.includes('IT Support Manager') || userRoles.includes('IT Support User');
}

