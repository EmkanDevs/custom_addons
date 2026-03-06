// Copyright (c) 2026, Administrator and contributors
// For license information, please see license.txt


frappe.ui.form.on('User Role Request', {
    onload(frm) {
        if (frm.is_new()) {
            frappe.db.get_value(
                "Employee",
                { user_id: frappe.session.user },
                "name",
                (r) => {
                    if (r?.name) {
                        frm.set_value("employee_id", r.name);
                        frm.set_value("internal_employee", 1);
                        frm.set_df_property("employee_id", "read_only", 1);
                    } else {
                        frm.set_value("external_user", 1);
                        frm.set_df_property("employee_id", "read_only", 0);
                    }
                }
            );
        } else {
            set_employee_id_permission(frm);
        }

        // set_approver_filter(frm);
        apply_workflow_state_permissions(frm);

        // Store initial workflow state for comparison
        if (!frm.doc.__initial_workflow_state) {
            frm.doc.__initial_workflow_state = frm.doc.workflow_state;
        }
    },
    internal_employee: function(frm) {
        // When internal_employee is unchecked, clear related fields
        if (!frm.doc.internal_employee) {
            frm.set_value('employee_id', '');
            frm.set_value('employee_name', '');
            frm.set_value('designation', '');
            frm.set_value('department', '');
        }
    },

    external_user: function(frm) {
        // When external_user is unchecked, clear related fields
        if (!frm.doc.external_user) {
            frm.set_value('email_id', '');
            frm.set_value('full_name', '');
            frm.set_value('presenting_who', '');
        }
    },

    refresh: function (frm) {
        apply_workflow_state_permissions(frm);
        set_employee_id_permission(frm);
        add_share_button(frm);


        // Clear actions menu based on workflow state
        const state = frm.doc.workflow_state;
        const session_user = frappe.session.user;
        const is_approver = frm.doc.approver === session_user;
        const is_sm = frappe.user.has_role("System Manager") || session_user === "Administrator";

        if (state === "Send for Approval" && !is_approver && !is_sm) {
            frm.page.clear_actions_menu();
        } else if (state === "Send for Approval (System Manager)" && !is_sm) {
            frm.page.clear_actions_menu();
        }

        // Add custom button for closing request
        add_close_button(frm);

        // Update initial state after refresh
        if (!frm.doc.__initial_workflow_state) {
            frm.doc.__initial_workflow_state = frm.doc.workflow_state;
        }
    },

    approver: function (frm) {
        if (frm.doc.approver === frappe.session.user) {
            frappe.msgprint({
                title: __("Error"),
                message: __("You cannot approve your own request."),
                indicator: "red"
            });
            frm.set_value("approver", null);
        }
        apply_workflow_state_permissions(frm);
    },

    workflow_state: function (frm) {
        apply_workflow_state_permissions(frm);

        // Trigger notifications when workflow state changes
        const previous_state = frm.doc.__initial_workflow_state;
        const current_state = frm.doc.workflow_state;

        if (previous_state !== current_state) {
            send_workflow_notifications(frm, previous_state, current_state);
            frm.doc.__initial_workflow_state = current_state;
        }
    },

    role_request_details_add: function (frm, cdt, cdn) {
        // When a new role is added, fetch its owners automatically
        var row = frappe.get_doc(cdt, cdn);
        if (row.requested_role) {
            frappe.call({
                method: 'custom_addons.custom_addons.doctype.user_role_request.user_role_request.get_owners_for_role',
                args: { role: row.requested_role },
                callback: function (r) {
                    if (r.message && r.message.length > 0) {
                        frappe.model.set_value(cdt, cdn, 'role_owners', r.message.join(", "));
                    }
                }
            });
        }
        // set_approver_filter(frm);
    },

    before_save: function (frm) {
        // Store workflow state before save for comparison
        if (!frm.doc.__before_save_workflow_state) {
            frm.doc.__before_save_workflow_state = frm.doc.workflow_state;
        }
    },

    after_save: function (frm) {
        // Check if workflow state changed during save
        const before_save_state = frm.doc.__before_save_workflow_state;
        const current_state = frm.doc.workflow_state;

        if (before_save_state && before_save_state !== current_state) {
            send_workflow_notifications(frm, before_save_state, current_state);
            frm.doc.__initial_workflow_state = current_state;
        }

        // Update the before_save state for next save
        frm.doc.__before_save_workflow_state = current_state;
    }
});

frappe.ui.form.on('User Role Request Details', {
    requested_role: function (frm, cdt, cdn) {
        set_role_owner_for_row(frm, cdt, cdn);
        set_approver_filter(frm);
    },

    rejected: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.rejected) {
            frappe.prompt(
                {
                    label: __("Rejection Reason"),
                    fieldname: "rejection_reason",
                    fieldtype: "Small Text",
                    reqd: 1
                },
                values => {
                    frm.set_value("rejection_reason", values.rejection_reason);
                    frm.save();
                },
                __("Enter Rejection Reason"),
                __("Reject")
            );
        }
    },
});

function apply_workflow_state_permissions(frm) {
    const state = frm.doc.workflow_state;
    const session_user = frappe.session.user;
    const is_approver = frm.doc.approver === session_user;
    const is_sm = frappe.user.has_role("System Manager") || session_user === "Administrator";


    // Get the grid if it exists
    const grid = frm.fields_dict.role_request_details?.grid;

    if (!state || state === "Draft") {
        frm.set_df_property('projects_for_approval', 'read_only', 1);
        frm.set_df_property('role_request_details', 'read_only', 1);

        if (grid) {
            grid.update_docfield_property("approved", "hidden", 1);
            grid.update_docfield_property("system_manager_approved", "hidden", 1);
            grid.update_docfield_property("rejected", "hidden", 1);
            grid.update_docfield_property("requested_role", "read_only", 1);
            grid.refresh();
        }
    }

    // SEND FOR APPROVAL STATE
    else if (state === "Send for Approval") {

        if (is_approver) {

            // Approver can edit project field
            frm.set_df_property('projects_for_approval', 'read_only', 1);

            // Approver can edit the table
            frm.set_df_property('role_request_details', 'read_only', 0);

            if (grid) {
                // Show all columns
                grid.update_docfield_property("requested_role", "hidden", 0);
                grid.update_docfield_property("approved", "hidden", 0);
                grid.update_docfield_property("rejected", "hidden", 0);
                grid.update_docfield_property("system_manager_approved", "hidden", 1);

                // Approver can add new roles AND approve/reject
                grid.update_docfield_property("requested_role", "read_only", 0);
                grid.update_docfield_property("approved", "read_only", 0);
                grid.update_docfield_property("rejected", "read_only", 0);
                grid.refresh();
            }

        } else {
            frm.set_df_property('project', 'read_only', 1);
            frm.set_df_property('role_request_details', 'read_only', 1);

            if (grid) {
                // Non-approvers can see requested roles but not approval columns
                grid.update_docfield_property("requested_role", "hidden", 0);
                grid.update_docfield_property("approved", "hidden", 1);
                grid.update_docfield_property("system_manager_approved", "hidden", 1);
                grid.update_docfield_property("rejected", "hidden", 1);
                grid.update_docfield_property("requested_role", "read_only", 1);
                grid.refresh();
            }
        }
    }

    // SEND FOR APPROVAL (SYSTEM MANAGER) STATE
    else if (state === "Send for Approval (System Manager)") {

        frm.set_df_property('projects_for_approval', 'read_only', 0);
        frm.set_df_property('role_request_details', 'read_only', 0);

        if (is_sm) {
            if (grid) {
                // Show all columns
                grid.update_docfield_property("requested_role", "hidden", 0);
                grid.update_docfield_property("approved", "hidden", 0);
                grid.update_docfield_property("system_manager_approved", "hidden", 0);
                grid.update_docfield_property("rejected", "hidden", 0);

                // Only SM can edit SM approval and rejection
                grid.update_docfield_property("requested_role", "read_only", 0);
                grid.update_docfield_property("approved", "read_only", 1);
                grid.update_docfield_property("system_manager_approved", "read_only", 0);
                grid.update_docfield_property("rejected", "read_only", 0);

                grid.refresh();
            }
        } else {
            if (grid) {
                // Show all columns but read-only
                grid.update_docfield_property("requested_role", "hidden", 0);
                grid.update_docfield_property("approved", "hidden", 0);
                grid.update_docfield_property("system_manager_approved", "hidden", 0);
                grid.update_docfield_property("rejected", "hidden", 0);

                // Everything read-only
                grid.update_docfield_property("requested_role", "read_only", 1);
                grid.update_docfield_property("approved", "read_only", 1);
                grid.update_docfield_property("system_manager_approved", "read_only", 1);
                grid.update_docfield_property("rejected", "read_only", 1);

                grid.refresh();
            }
        }
    }

    // FINAL STATES
    else if (state === "Approve by System Manager" || state === "Rejected") {

        frm.set_df_property('project', 'read_only', 1);
        frm.set_df_property('role_request_details', 'read_only', 1);

        if (grid) {
            // Show all columns
            grid.update_docfield_property("requested_role", "hidden", 0);
            grid.update_docfield_property("approved", "hidden", 0);
            grid.update_docfield_property("system_manager_approved", "hidden", 0);
            grid.update_docfield_property("rejected", "hidden", 0);

            // Everything read-only
            grid.update_docfield_property("requested_role", "read_only", 1);
            grid.update_docfield_property("approved", "read_only", 1);
            grid.update_docfield_property("system_manager_approved", "read_only", 1);
            grid.update_docfield_property("rejected", "read_only", 1);

            grid.refresh();
        }
    }
}

function send_workflow_notifications(frm, previous_state, current_state) {
    // Use provided states or fall back to doc properties
    const prev_state = previous_state || frm.doc.__initial_workflow_state;
    const curr_state = current_state || frm.doc.workflow_state;

    // Only send notifications if state actually changed
    if (prev_state === curr_state) {
        return;
    }


    // Send to Approver when state changes to "Send for Approval"
    if (curr_state === "Send for Approval" && prev_state !== "Send for Approval") {
        if (frm.doc.approver) {
            send_email_to_approver(frm);
        } else {
            console.warn("No approver assigned, skipping approver notification");
        }
    }

    // Send to System Manager when state changes to "Send for Approval (System Manager)"
    else if (curr_state === "Send for Approval (System Manager)" && prev_state !== "Send for Approval (System Manager)") {
        send_email_to_system_manager(frm);
    }

    // Send final notification and share document when approved by System Manager
    else if (curr_state === "Approve by System Manager" && prev_state !== "Approve by System Manager") {

        // Send approval notification AND share document simultaneously
        send_approval_notification(frm);

        // Also trigger document sharing immediately
        share_document_with_role_owners(frm);
    }
}

// Separate function for sharing document
function share_document_with_role_owners(frm) {
+    frappe.call({
        method: "custom_addons.custom_addons.doctype.user_role_request.user_role_request.share_document_with_role_owners",
        args: { docname: frm.doc.name },
        callback: function (r) {
            if (r.message) {
                frappe.show_alert({
                    message: __('Document automatically shared with role owners!'),
                    indicator: 'green'
                }, 5);
            } else {
                console.warn("⚠️ No role owners found to share with");
                frappe.show_alert({
                    message: __('No role owners found to share with'),
                    indicator: 'orange'
                }, 5);
            }
            // Reload to show updated sharing
            frm.reload_doc();
        }
    });
}


function send_email_to_approver(frm) {
    frappe.call({
        method: "custom_addons.custom_addons.doctype.user_role_request.user_role_request.send_approval_email",
        args: {
            doc: frm.doc
        },
    });
}

function send_email_to_system_manager(frm) {
    // Get approved roles
    const approved_roles = (frm.doc.role_request_details || [])
        .filter(row => row.approved && row.requested_role)
        .map(row => row.requested_role);

    frappe.call({
        method: "custom_addons.custom_addons.doctype.user_role_request.user_role_request.send_system_manager_approval_email",
        args: {
            doc: frm.doc,
            roles: approved_roles
        },
    });
}

function send_approval_notification(frm) {

    // Trigger role owner notifications only
    frappe.call({
        method: "custom_addons.custom_addons.doctype.user_role_request.user_role_request.fetch_role_owners_for_doc",
        args: {
            docname: frm.doc.name
        },
    });
}


function add_close_button(frm) {
    const is_sm = frappe.user.has_role("System Manager") || frappe.session.user === "Administrator";

    if (is_sm && frm.doc.docstatus === 1) {
        if (frm.doc.status != "Closed") {
            frm.add_custom_button(__('Close Request'), function () {
                close_request(frm);
            });
        }
    }
}

function close_request(frm) {
    frappe.confirm(
        __('Are you sure you want to close this request?'),
        function () {
            frappe.call({
                method: "custom_addons.custom_addons.doctype.user_role_request.user_role_request.close_request",
                args: {
                    docname: frm.doc.name
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.msgprint({
                            title: __('Success'),
                            message: __('Request has been closed successfully.'),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    }
                }
            });
        }
    );
}

function set_role_owner_for_row(frm, cdt, cdn) {
    const row = locals[cdt][cdn];

    if (!row.requested_role) {
        frappe.model.set_value(cdt, cdn, "role_owners", "");
        return;
    }

    frappe.call({
        method: "custom_addons.custom_addons.doctype.user_role_request.user_role_request.get_owners_for_role",
        args: { role: row.requested_role },
        callback: r => {
            frappe.model.set_value(
                cdt,
                cdn,
                "role_owners",
                r.message ? r.message.join(", ") : ""
            );
        }
    });
}

function prompt_rejection(frm) {
    frappe.prompt(
        {
            label: __("Rejection Reason"),
            fieldname: "rejection_reason",
            fieldtype: "Small Text",
            reqd: 1
        },
        values => {
            frappe.call({
                method: "custom_addons.custom_addons.doctype.user_role_request.user_role_request.reject_request",
                args: {
                    docname: frm.doc.name,
                    reason: values.rejection_reason
                },
                callback: r => r.message && frm.reload_doc()
            });
        },
        __("Enter Rejection Reason"),
        __("Reject")
    );
}

function set_employee_id_permission(frm) {
    if (!frm.doc.employee_id) {
        frm.set_df_property("employee_id", "read_only", 0);
        return;
    }

    frappe.db.get_value(
        "Employee",
        frm.doc.employee_id,
        "user_id",
        r => {
            frm.set_df_property(
                "employee_id",
                "read_only",
                r?.user_id === frappe.session.user
            );
        }
    );
}

function set_approver_filter(frm) {
    const roles = (frm.doc.role_request_details || [])
        .map(r => r.requested_role)
        .filter(Boolean);

    if (!roles.length) {
        frappe.call({
            method: "custom_addons.custom_addons.doctype.user_role_request.user_role_request.get_all_approvers",
            callback: r => {
                let approvers = r.message || [];
                // Filter out session user client-side
                approvers = approvers.filter(u => u !== frappe.session.user);

                // frm.set_query("approver", () => ({
                //     filters: {
                //         "name": ["in", approvers]
                //     }
                // }));
            }
        });
        return;
    }

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
}

function add_share_button(frm) {
    const is_sm =
        frappe.user.has_role("System Manager") ||
        frappe.session.user === "Administrator";

    if (
        frm.is_new() ||
        frm.doc.workflow_state !== "Approve by System Manager" ||
        !is_sm
    ) {
        return;
    }

    frm.add_custom_button(__('Share'), () => {
        share_document_with_role_owners(frm);
    });
}

