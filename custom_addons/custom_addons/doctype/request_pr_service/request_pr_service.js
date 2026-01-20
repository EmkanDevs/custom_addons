// Copyright (c) 2025, Finbyz and contributors
// For license information, please see license.txt

frappe.ui.form.on("Request PR Service", {
	refresh(frm) {

        frm.add_custom_button('Public Relation Visit', () => {
            frappe.model.with_doctype('Public Relation Visit', () => {
                let new_doc = frappe.model.get_new_doc('Public Relation Visit');

                // Set main fields
                new_doc.location = frm.doc.location;
                new_doc.project = frm.doc.project;
                new_doc.project_name = frm.doc.project_name;
                new_doc.remark = frm.doc.remark;
                new_doc.pr_request_type = frm.doc.pr_request_type;
                new_doc.request_pr_service_no = frm.doc.name;

                // Copy child table: serviced_employees
                if (frm.doc.serviced_employees && frm.doc.serviced_employees.length > 0) {
                    frm.doc.serviced_employees.forEach(row => {
                        const child = frappe.model.add_child(new_doc, 'serviced_employees');
                        frappe.model.set_value(child.doctype, child.name, {
                            assigned_user: row.assigned_user,
                            name1: row.name1,
                            department: row.department,
                            designation: row.designation,
                            project: row.project,
                            project_name: row.project_name,
                            pr_request_type: row.pr_request_type,
                            application_stage: row.application_stage,
                            remark: row.remark
                        });
                    });
                }

                frappe.set_route('Form', 'Public Relation Visit', new_doc.name);

                // Optional: Show a success message
                frappe.show_alert({
                    message: __('Public Relation Visit draft created successfully!'),
                    indicator: 'green'
                }, 5);
            })
        }, 'Create');

    }
    
});
