// Copyright (c) 2026, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Business Partner", {
    setup: function (frm) {
        frm.set_query("customer_primary_contact", function (doc) {
            return {
                query: "frappe.contacts.doctype.contact.contact.contact_query",
                filters: { link_doctype: "Business Partner", link_name: doc.name },
            };
        });
        frm.set_query("customer_primary_address", function (doc) {
            return {
                filters: {
                    link_doctype: "Business Partner",
                    link_name: doc.name,
                },
            };
        });
    },

    refresh: function (frm) {
        frappe.dynamic_link = {
            doc: frm.doc,
            fieldname: "name",
            doctype: "Business Partner",
        };

        if (!frm.is_new()) {
            frappe.contacts.render_address_and_contact(frm);
        }
    },

    customer_primary_contact: function (frm) {
        if (frm.doc.customer_primary_contact) {
            frappe.db.get_value(
                "Contact",
                frm.doc.customer_primary_contact,
                ["mobile_no", "email_id"],
                function (r) {
                    if (r) {
                        frm.set_value("mobile_no", r.mobile_no);
                        frm.set_value("email_id", r.email_id);
                    }
                }
            );
        }
    },

    customer_primary_address: function (frm) {
        if (frm.doc.customer_primary_address) {
            frappe.call({
                method: "frappe.contacts.doctype.address.address.get_condensed_address",
                args: {
                    name: frm.doc.customer_primary_address,
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value("primary_address", r.message);
                    }
                },
            });
        }
    },
});
