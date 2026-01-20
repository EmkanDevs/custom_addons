// Copyright (c) 2025, Finbyz and contributors
// For license information, please see license.txt

frappe.ui.form.on("Request New SIM", {
	refresh(frm) {
        frm.trigger('sim_management');
	},
    sim_provider(frm){
        frm.trigger('sim_management');
    },
    sim_management(frm){
        frm.set_query("sim_package_plan", function () {
            return {
                filters: {
                    sim_provider: frm.doc.sim_provider,
                }
            };
        }); 
    }
});
