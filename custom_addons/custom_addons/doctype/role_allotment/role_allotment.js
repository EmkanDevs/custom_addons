// Copyright (c) 2026, Administrator and contributors
// For license information, please see license.txt

frappe.ui.form.on("Role Allotment", {
	refresh(frm) {
        frm.add_custom_button(__("Add All Roles"), () => {
            frappe.db.get_list("Role", {
                fields: ["name"],
                limit: 500
            }).then(roles => {
                let existing_roles = (frm.doc.role_owner_list || []).map(row => row.role);
                roles.forEach(role => {
                    if (!existing_roles.includes(role.name)) {
                        let row = frm.add_child("role_owner_list");
                        row.role = role.name;
                    }
                });
                frm.refresh_field("role_owner_list");
            });
        });

	},
});
