
frappe.ui.form.on("Equipment Log Register", {
	refresh(frm) {

	},
});

frappe.ui.form.on("Equipment Log Item", {
    item_code: async function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (!row.item_code) return;

        // Fetch item details
        let item = await frappe.db.get_doc("Item", row.item_code);

        // Detect fixed asset
        let is_fixed_asset = item.is_fixed_asset || 0;

        // Set checkbox
        frappe.model.set_value(cdt, cdn, "fixed_asset", is_fixed_asset);

        if (is_fixed_asset) {

            // Force qty = 1
            frappe.model.set_value(cdt, cdn, "quanity", 1);

            // Make tag number mandatory
            row.reqd_tag_number = 1;

            frappe.msgprint(
                __("This item is a Fixed Asset. Tag Number is mandatory and Quantity cannot exceed 1.")
            );

        } else {

            // Remove tag number requirement
            frappe.model.set_value(cdt, cdn, "tag_number", "");

            row.reqd_tag_number = 0;
        }

        frm.refresh_field("equipment_log_item");
    },

    quanity: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.fixed_asset && row.quanity > 1) {

            frappe.model.set_value(cdt, cdn, "quanity", 1);

            frappe.throw(__("Quantity cannot exceed 1 for Fixed Asset items."));
        }
    }
});