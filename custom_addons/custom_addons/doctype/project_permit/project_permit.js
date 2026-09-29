// Copyright (c) 2025, Finbyz and contributors

frappe.ui.form.on("Project Permit", {
    valid_from(frm) { calculate_duration(frm); },
    valid_to(frm) { calculate_duration(frm); },

    refresh(frm) {
        if (frm.is_new()) return;

        // Always show Payment Request button
        frm.add_custom_button(__('Create Payment Request'), () => {
            frappe.call({
                method: "custom_addons.custom_addons.doctype.project_permit.project_permit.make_pp_payment_request",
                args: { docname: frm.doc.name },
                callback(r) {
                    if (r.message) {
                        frappe.model.sync(r.message);
                        frappe.set_route("Form", "Payment Requester", r.message.name);
                    }
                }
            });
        }, __("Create"));

        // Show PI button only after Payment Requester exists
        frappe.db.get_value("Payment Requester", {
            reference_doctype: frm.doctype,
            reference_name: frm.doc.name
        }, "name").then(r => {
            if (r?.message?.name) {
                frm.add_custom_button(__('Create Purchase Invoice'), () => {
                    create_pp_purchase_invoice(frm, r.message.name);
                }, __("Create"));
            }
        });
    }
});

function calculate_duration(frm) {
    if (frm.doc.valid_from && frm.doc.valid_to) {
        let from_date = frappe.datetime.str_to_obj(frm.doc.valid_from);
        let to_date = frappe.datetime.str_to_obj(frm.doc.valid_to);
        frm.set_value("permit_duration_days",
            frappe.datetime.get_day_diff(to_date, from_date)
        );
    }
}

function create_pp_purchase_invoice(frm, payment_requester) {
    frappe.new_doc("Purchase Invoice", {
        supplier : frm.doc.permit_under_supplier,
        project: frm.doc.project,
        cost_center: frm.doc.cost_center,
        bill_no : frm.doc.invoice_no,
        bill_date : frm.doc.invoice_date,
        reference_doctype_payment: "Payment Requester",
        ref_payment_name: payment_requester,
        reference_doctype: frm.doctype,
        reference_name: frm.doc.name,
    });
}
