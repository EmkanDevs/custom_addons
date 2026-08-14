frappe.ui.form.on("Blanket Order", {
	refresh: function (frm) {
		if (frm.doc.supplier && frm.doc.docstatus === 1 && frm.doc.blanket_order_po_exemption) {
			// Hide the standard "Purchase Order" button under Create
			frm.remove_custom_button("Purchase Order", "Create");
			// Show only "Purchase Invoice" under Create
			frm.add_custom_button(__("Purchase Invoice"), function () {
				frappe.model.open_mapped_doc({
					method: "custom_addons.custom_addons.doc_events.blanket_order.make_direct_purchase_invoice",
					frm: frm
				});
			}, __("Create"));
		}

		set_item_code_filter(frm);
	},

	blanket_order_po_exemption: function (frm) {
		set_item_code_filter(frm);
	}
});

function set_item_code_filter(frm) {
	frm.set_query("item_code", "items", function () {
		if (frm.doc.blanket_order_po_exemption) {
			return {
				filters: {
					is_stock_item: 0,
					is_fixed_asset: 0,
					blanket_order_po_exemption: 1
				}
			};
		}
		return {};
	});
	frm.fields_dict["items"].grid.refresh();
}