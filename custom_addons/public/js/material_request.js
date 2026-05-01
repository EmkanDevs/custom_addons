frappe.ui.form.on('Material Request', {

    validate: function(frm) {
        if (frm.doc.items) {
            frm.doc.items.forEach(row => {
                if (!row.project) {
                    row.project = frm.doc.custom_project || frm.doc.project;
                }
            });
        }
    },

    custom_project: function(frm) {
        if (frm.doc.items) {
            frm.doc.items.forEach(row => {
                frappe.model.set_value(row.doctype, row.name, "project", frm.doc.custom_project);
            });
        }
    }

});