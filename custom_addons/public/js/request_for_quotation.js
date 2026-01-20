frappe.ui.form.on("Request for Quotation", {
    refresh: function (frm, cdt, cdn) {
		if (frm.fields_dict["items"].grid.get_field("uom")) {
			frm.set_query("uom", "items", function(doc, cdt, cdn) {
				let row = locals[cdt][cdn];

				return {
					query: "erpnext.controllers.queries.get_item_uom_query",
					filters: {
						"item_code": row.item_code
					}
				};
			});
		}
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(
				__("Supplier Quotation"),
				function () {
					frm.trigger("make_supplier_quotation");
				},
				__("Create")

			);
            
			frm.add_custom_button(
				__("Send Emails to Suppliers"),
				function () {
					frappe.call({
						method: "erpnext.buying.doctype.request_for_quotation.request_for_quotation.send_supplier_emails",
						freeze: true,
						args: {
							rfq_name: frm.doc.name,
						},
						callback: function (r) {
							frm.reload_doc();
						},
					});
				},
				__("Tools")
			);

			frm.add_custom_button(
				__("Download PDF"),
				() => {
					frappe.prompt(
						[
							{
								fieldtype: "Link",
								label: "Select a Supplier",
								fieldname: "supplier",
								options: "Supplier",
								reqd: 1,
								default: frm.doc.suppliers?.length == 1 ? frm.doc.suppliers[0].supplier : "",
								get_query: () => {
									return {
										filters: [
											[
												"Supplier",
												"name",
												"in",
												frm.doc.suppliers.map((row) => {
													return row.supplier;
												}),
											],
										],
									};
								},
							},
							{
								fieldtype: "Section Break",
								label: "Print Settings",
								fieldname: "print_settings",
								collapsible: 1,
							},
							{
								fieldtype: "Link",
								label: "Print Format",
								fieldname: "print_format",
								options: "Print Format",
								placeholder: "Standard",
								get_query: () => {
									return {
										filters: {
											doc_type: "Request for Quotation",
										},
									};
								},
							},
							{
								fieldtype: "Link",
								label: "Language",
								fieldname: "language",
								options: "Language",
								default: frappe.boot.lang,
							},
							{
								fieldtype: "Link",
								label: "Letter Head",
								fieldname: "letter_head",
								options: "Letter Head",
								default: frm.doc.letter_head,
							},
						],
						(data) => {
							var w = window.open(
								frappe.urllib.get_full_url(
									"/api/method/erpnext.buying.doctype.request_for_quotation.request_for_quotation.get_pdf?" +
										new URLSearchParams({
											name: frm.doc.name,
											supplier: data.supplier,
											print_format: data.print_format || "Standard",
											language: data.language || frappe.boot.lang,
											letterhead: data.letter_head || frm.doc.letter_head || "",
										}).toString()
								)
							);
							if (!w) {
								frappe.msgprint(__("Please enable pop-ups"));
								return;
							}
						},
						__("Download PDF for Supplier"),
						__("Download")
					);
				},
				__("Tools")
			);

			frm.page.set_inner_btn_group_as_primary(__("Create"));
		}
		frm.add_custom_button(
			__("Bid Tabulation Discussion"),
			function () {
				frm.trigger("bid_tabulation");
			},
			__("Create")
			
		);
	},
    bid_tabulation() {
		frappe.model.open_mapped_doc({
			method: "custom_addons.custom_addons.doc_events.request_for_quotation.bid_tabulation",
			frm: cur_frm,
		});
	}
})