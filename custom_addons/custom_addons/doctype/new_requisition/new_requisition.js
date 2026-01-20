// Copyright (c) 2025, Finbyz and contributors
// For license information, please see license.txt

frappe.ui.form.on("New Requisition", {
    refresh(frm) {
        // Add "Reopen" button
        frm.add_custom_button("Reopen", function () {
            frappe.db.set_value("New Requisition", frm.doc.name, "doc_status", "Open")
                .then(() => {
                    frappe.show_alert({ message: "Requisition doc_status set to Open.", indicator: "green" });
                    frm.reload_doc(); // Reloads the form to reflect the changes
                })
                .catch(err => {
                    frappe.msgprint(__("Failed to update doc_status."));
                    console.error(err);
                });
        });

        // Make 'doc_status' field read-only when it's "Completed" or "Cancelled"
        if (frm.doc.doc_status === "Completed" || frm.doc.doc_status === "Cancelled") {
            frm.set_df_property("doc_status", "read_only", 1);
        } else {
            frm.set_df_property("doc_status", "read_only", 0);
        }
    },
});
