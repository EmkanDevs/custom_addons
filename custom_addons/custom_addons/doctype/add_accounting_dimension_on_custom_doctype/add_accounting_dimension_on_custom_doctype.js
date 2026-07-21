// Copyright (c) 2025, Finbyz and contributors
// For license information, please see license.txt

frappe.ui.form.on("Add Accounting Dimension On Custom Doctype", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(
				__("Apply Accounting Dimensions"),
				() => apply_dimensions(frm),
				__("Actions")
			);
			frm.add_custom_button(
				__("Remove Accounting Dimensions"),
				() => remove_dimensions(frm),
				__("Actions")
			);
		}
	},
});

function apply_dimensions(frm) {
	let selected_configs = get_selected_doctype_configs(frm);
	if (!selected_configs.length) {
		frappe.msgprint(__("Please select at least one doctype from the list."));
		return;
	}

	let doctypes = selected_configs.map(row => row.custom_doctype).filter(dt => !!dt);

	if (!doctypes.length) {
		frappe.msgprint(__("Selected rows do not have valid doctypes."));
		return;
	}

	(frm.is_dirty() ? frm.save() : Promise.resolve()).then(() => {
		frappe.call({
			method: "custom_addons.custom_addons.doctype.add_accounting_dimension_on_custom_doctype.add_accounting_dimension_on_custom_doctype.add_dimensions_for_custom_doctypes",
			args: {
				doctypes: doctypes,
				doctype_configs: selected_configs,
			},
			freeze: true,
			freeze_message: __("Applying accounting dimensions to selected doctypes..."),
			callback: () => {
				frappe.show_alert({
					message: __("Accounting dimensions applied to {0} doctypes.", [doctypes.length]),
					indicator: "green",
				});
			},
		});
	});
}

function remove_dimensions(frm) {
	let selected_configs = get_selected_doctype_configs(frm);
	if (!selected_configs.length) {
		frappe.msgprint(__("Please select at least one doctype from the list."));
		return;
	}

	let doctypes = selected_configs.map(row => row.custom_doctype).filter(dt => !!dt);

	if (!doctypes.length) {
		frappe.msgprint(__("Selected rows do not have valid doctypes."));
		return;
	}

	(frm.is_dirty() ? frm.save() : Promise.resolve()).then(() => {
		frappe.call({
			method: "custom_addons.custom_addons.doctype.add_accounting_dimension_on_custom_doctype.add_accounting_dimension_on_custom_doctype.remove_dimensions_for_custom_doctypes",
			args: {
				doctypes: doctypes,
				doctype_configs: selected_configs,
			},
			freeze: true,
			freeze_message: __("Removing accounting dimensions from selected doctypes..."),
			callback: () => {
				frappe.show_alert({
					message: __("Accounting dimensions removed from {0} doctypes.", [doctypes.length]),
					indicator: "green",
				});
			},
		});
	});
}

function get_selected_doctype_configs(frm) {
	let selected_rows = frm.get_field('doctype_list').grid.get_selected_children();

	return selected_rows.map(row => ({
		custom_doctype: row.custom_doctype,
		has_child_table: row.has_child_table,
		child_table: row.child_table,
		field_and_script: row.field_and_script,
	}));
}
