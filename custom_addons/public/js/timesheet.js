frappe.ui.form.on("Timesheet", {
    employee: function(frm) {
        if (frm.doc.employee) {
            frappe.db.get_value(
                "Employee",
                frm.doc.employee,
                ["working_hour_rate", "ot_hour_rate"],
                function(r) {
                    if (r) {
                        // Set rates on each existing time log row
                        (frm.doc.time_logs || []).forEach(function(row) {
                            frappe.model.set_value(
                                row.doctype,
                                row.name,
                                "working_hour_rate_",
                                r.working_hour_rate || 0
                            );
                            frappe.model.set_value(
                                row.doctype,
                                row.name,
                                "ot_hours_rate_",
                                r.ot_hour_rate || 0
                            );
                        });

                        frm.refresh_field("time_logs");
                    }
                }
            );
        }
    }
});

frappe.ui.form.on("Timesheet Detail", {
    time_logs_add: function(frm, cdt, cdn) {
        // Auto-fill rates when a new row is added
        if (frm.doc.employee) {
            frappe.db.get_value(
                "Employee",
                frm.doc.employee,
                ["working_hour_rate", "ot_hour_rate"],
                function(r) {
                    if (r) {
                        frappe.model.set_value(cdt, cdn, "working_hour_rate_", r.working_hour_rate || 0);
                        frappe.model.set_value(cdt, cdn, "ot_hours_rate_", r.ot_hour_rate || 0);
                    }
                }
            );
        }
    }
});