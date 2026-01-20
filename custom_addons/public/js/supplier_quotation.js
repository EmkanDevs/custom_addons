frappe.ui.form.on("Supplier Quotation", {
    refresh: function (frm) {
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
        // Reopen button when Expired and not submitted
        if (frm.doc.status === "Expired" && frm.doc.docstatus !== 1) {
            frm.add_custom_button("Reopen", function () {
                frm.set_value("status", "Draft");
                frm.set_value("valid_till", frappe.datetime.get_today());
                frm.save();
            });
        }

        // Set default valid_till on new doc
        if (frm.doc.__islocal && !frm.doc.valid_till) {
            frm.set_value("valid_till", frappe.datetime.add_months(frm.doc.transaction_date, 1));
        }

        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Purchase Order"), () => frm.events.make_purchase_order(frm), __("Create"));
            frm.add_custom_button(__("Quotation"), () => frm.events.make_quotation(frm), __("Create"));
            frm.page.set_inner_btn_group_as_primary(__("Create"));
        } else if (frm.doc.docstatus === 0) {
            frm.add_custom_button(
                __("Material Request"),
                function () {
                    erpnext.utils.map_current_doc({
                        method: "erpnext.stock.doctype.material_request.material_request.make_supplier_quotation",
                        source_doctype: "Material Request",
                        target: frm,
                        setters: {
                            schedule_date: undefined,
                            status: undefined,
                        },
                        get_query_filters: {
                            material_request_type: "Purchase",
                            docstatus: 1,
                            status: ["!=", "Stopped"],
                            per_ordered: ["<", 100],
                            company: frm.doc.company,
                        },
                    });
                },
                __("Get Items From")
            );

            frm.add_custom_button(
                __("Link to Material Requests"),
                function () {
                    erpnext.buying.link_to_mrs(frm);
                },
                __("Tools")
            );

            frm.add_custom_button(
                __("Request for Quotation"),
                function () {
                    if (!frm.doc.supplier) {
                        frappe.throw({ message: __("Please select a Supplier"), title: __("Mandatory") });
                    }
                    erpnext.utils.map_current_doc({
                        method: "erpnext.buying.doctype.request_for_quotation.request_for_quotation.make_supplier_quotation_from_rfq",
                        source_doctype: "Request for Quotation",
                        target: frm,
                        setters: {
                            transaction_date: null,
                        },
                        get_query_filters: {
                            supplier: frm.doc.supplier,
                            company: frm.doc.company,
                        },
                        get_query_method: "erpnext.buying.doctype.request_for_quotation.request_for_quotation.get_rfq_containing_supplier",
                    });
                },
                __("Get Items From")
            );
        }
    },
	make_purchase_order(frm) {
    const rfqs = frm.doc.items
        .map(item => item.request_for_quotation)
        .filter(rfq => rfq);

    if (rfqs.length === 0) {
        frappe.throw("Please create Request for Quotation before creating Purchase Order");
        return;
    }

    // Search directly in Bid Tabulation Discussion for matching RFQs
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Bid Tabulation Discussion",
            filters: [
                ["request_for_quotation", "in", rfqs],
                ["docstatus", "=", 1]
            ],
            fields: ["name"]
        },
        callback: function (res) {
            if (!res.message || res.message.length === 0) {
                frappe.throw("No submitted Bid Tabulation Discussion found for the linked RFQ(s).");
                return;
            }

            // ✅ Proceed to create Purchase Order
            frappe.model.open_mapped_doc({
                method: "erpnext.buying.doctype.supplier_quotation.supplier_quotation.make_purchase_order",
                frm: frm,
            });
        }
    });
},


	make_quotation() {
		frappe.model.open_mapped_doc({
			method: "erpnext.buying.doctype.supplier_quotation.supplier_quotation.make_quotation",
			frm: cur_frm,
		});
	}
});
