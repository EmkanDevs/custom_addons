// Copyright (c) 2026, Administrator and contributors
// For license information, please see license.txt

// Copyright (c) 2025, Finbyz and contributors
// For license information, please see license.txt

frappe.ui.form.on("User Deactivate Access", {
    onload(frm) {
        if (frm.is_new()) {
            frappe.db.get_value(
                "Employee",
                { user_id: frappe.session.user },
                "name",
                (r) => {
                    if (r && r.name) {
                        frm.set_value("employee_id", r.name);
                    }
                }
            );
        }

        frm.set_query("approver", () => ({
            filters: {
                name: ["!=", frappe.session.user]
            }
        }));
    },
    approver:function(frm){
        frappe.call({
            method: "custom_addons.custom_addons.doctype.user_role_request.user_role_request.get_role_owners",
            args: { roles },
            callback: r => {
                let owners = r.message || [];
                // Filter out session user client-side
                owners = owners.filter(u => u !== frappe.session.user);
        
                if (owners.length === 1 && !frm.doc.approver) {
                    frm.set_value("approver", owners[0]);
                }
        
                frm.set_query("approver", () => ({
                    filters: {
                        "name": ["in", owners]
                    }
                }));
            }
        });
    },
    

    refresh(frm) {
        set_approver_filter(frm);
    }
});


function set_approver_filter(frm) {
    // Basic filter for approver as no role_request_details child table exists here
    frm.set_query("approver", () => ({
        filters: {
            name: ["!=", frappe.session.user],
            user_type: "System User",
            enabled: 1
        }
    }));
}




