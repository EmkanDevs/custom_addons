frappe.ui.form.on("Journal Entry", {
    custom_project(frm) {
        update_project_cost_center(frm);
    },

    custom_cost_center(frm) {
        update_project_cost_center(frm);
    }

});

function update_project_cost_center(frm) {
    (frm.doc.accounts || []).forEach(row => {
        if (frm.doc.custom_project) {
            row.project = frm.doc.custom_project;
        }

        if (frm.doc.custom_cost_center) {
            row.cost_center = frm.doc.custom_cost_center;
        }
    });

    frm.refresh_field("accounts");
}