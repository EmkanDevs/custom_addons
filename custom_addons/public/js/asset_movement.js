frappe.ui.form.on('Asset Movement', {
    onload(frm) { frm.trigger('set_project_reqd'); },
    refresh(frm) { 
        frm.trigger('set_project_reqd'); 
        frm.trigger('fill_asset_project');
    },
    purpose(frm) { frm.trigger('set_project_reqd'); },
    assets_add(frm) { 
        frm.trigger('set_project_reqd'); 
        frm.trigger('fill_asset_project');
    },

    set_project_reqd(frm) {
        let source_reqd = ['Transfer'].includes(frm.doc.purpose);
        let target_reqd = ['Transfer', 'Receipt'].includes(frm.doc.purpose);

        
        frm.fields_dict.assets.grid.toggle_reqd('custom_source_project', source_reqd);
        frm.fields_dict.assets.grid.toggle_reqd('custom_target_project', target_reqd);
    },
    fill_asset_project(frm) {
        if (!frm.is_new()) return;
        (frm.doc.assets || []).forEach(row => {
            if (!row.asset || row.custom_target_project) return;
            frappe.db.get_value('Asset', row.asset, 'custom_project').then(r => {
                const p = r.message && r.message.custom_project;
                if (p) frappe.model.set_value(row.doctype, row.name, 'custom_target_project', p);
            });
        });
    }
});

frappe.ui.form.on('Asset Movement Item', {
    form_render(frm) { frm.trigger('set_project_reqd'); },
    asset(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.asset || row.custom_target_project) return;
        frappe.db.get_value('Asset', row.asset, 'custom_project').then(r => {
            const p = r.message && r.message.custom_project;
            if (p) frappe.model.set_value(cdt, cdn, 'custom_target_project', p);
        });
    }
});