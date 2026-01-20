frappe.provide("frappe.bid_tabulation_discussion");

frappe.ui.form.on("Bid Tabulation Discussion", {
    refresh: function(frm) {
        frappe.bid_tabulation_discussion.render_schedule(frm);

        // Disable adding/removing rows manually
        frm.set_df_property('discussion', 'cannot_add_rows', true);
        frm.set_df_property('discussion', 'cannot_delete_rows', true);
        frm.set_df_property('discussion', 'cannot_delete_all_rows', true);

        // Show buttons after submit
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Purchase Order"), () => frm.events.make_purchase_order(frm), __("Create"));
            frm.add_custom_button(__("Quotation"), () => frm.events.make_quotation(frm), __("Create"));
        }

        // Fetch attachments for RFQ
        if (!frm.doc.request_for_quotation) return;
        frappe.call({
            method: "custom_addons.custom_addons.doctype.bid_tabulation_discussion.bid_tabulation_discussion.fetch_attachments_and_display",
            args: { request_for_quotation: frm.doc.request_for_quotation },
            callback: function(r) {
                $(frm.fields_dict.custom_html.wrapper).html(r.message || "<p>No attachments found.</p>");
            }
        });
    },

    final_supplier: function(frm) {
        frappe.call({
            method: "custom_addons.custom_addons.doctype.bid_tabulation_discussion.bid_tabulation_discussion.set_supplier_quotation_value",
            args: { request_for_quotation: frm.doc.request_for_quotation, supplier: frm.doc.final_supplier },
            async: false,
            callback: function(r) {
                if (r.message) {
                    frm.set_value("supplier_quotation", r.message[0]);
                    frm.save_or_update();
                }
            }
        });
    },

    make_purchase_order: function(frm) {
        let dialog = new frappe.ui.Dialog({
            title: 'Select Source Name',
            fields: [{
                label: 'Source Name',
                fieldname: 'source_name',
                fieldtype: 'Link',
                options: 'Supplier Quotation',
                reqd: 1,
                default: frm.doc.supplier_quotation
            }],
            primary_action_label: 'Proceed',
            primary_action(values) {
                if (values.source_name) {
                    frappe.model.open_mapped_doc({
                        method: "custom_addons.custom_addons.doctype.bid_tabulation_discussion.bid_tabulation_discussion.make_purchase_order",
                        frm: frm,
                        source_name: values.source_name,
                        args: { bid_tabulation: frm.doc.name }
                    });
                    dialog.hide();
                } else {
                    frappe.msgprint(__('Please select a source name.'));
                }
            }
        });
        dialog.show();
    },

    make_quotation: function(frm) {
        let dialog = new frappe.ui.Dialog({
            title: 'Select Source Name',
            fields: [{
                label: 'Source Name',
                fieldname: 'source_name',
                fieldtype: 'Link',
                options: 'Supplier Quotation',
                reqd: 1,
                default: frm.doc.supplier_quotation
            }],
            primary_action_label: 'Proceed',
            primary_action(values) {
                if (values.source_name) {
                    frappe.model.open_mapped_doc({
                        method: "custom_addons.custom_addons.doctype.bid_tabulation_discussion.bid_tabulation_discussion.make_quotation",
                        frm: frm,
                        source_name: values.source_name,
                        args: { bid_tabulation: frm.doc.name }
                    });
                    dialog.hide();
                } else {
                    frappe.msgprint(__('Please select a source name.'));
                }
            }
        });
        dialog.show();
    },

    onload: function(frm) {
        if (!frm.doc.request_for_quotation) return;

        frm.set_query("supplier", () => ({
            filters: { name: ["in", get_suppliers_from_rfq(frm.doc.request_for_quotation)] }
        }));
        frm.set_query("final_supplier", () => ({
            filters: { name: ["in", get_suppliers_from_rfq(frm.doc.request_for_quotation)] }
        }));
        frm.set_query("supplier_quotation", () => ({
            filters: { name: ["in", get_suppliers_quotation(frm.doc.request_for_quotation)] }
        }));
    }
});


function get_suppliers_from_rfq(rfq) {
    if (!rfq) return [];
    let suppliers = [];
    frappe.call({
        method: "custom_addons.custom_addons.doctype.bid_tabulation_discussion.bid_tabulation_discussion.get_supplier_options",
        args: { docname: rfq },
        async: false,
        callback: r => suppliers = r.message || []
    });
    return suppliers;
}

function get_suppliers_quotation(rfq) {
    if (!rfq) return [];
    let quotations = [];
    frappe.call({
        method: "custom_addons.custom_addons.doctype.bid_tabulation_discussion.bid_tabulation_discussion.set_supplier_quotation",
        args: { request_for_quotation: rfq },
        async: false,
        callback: r => quotations = r.message || []
    });
    return quotations;
}

frappe.bid_tabulation_discussion.render_schedule = function(frm) {
    if (!frm.is_dirty()) {
        frappe.call({
            method: "custom_addons.custom_addons.doctype.bid_tabulation_discussion.bid_tabulation_discussion.get_supplier_details",
            args: { docname: frm.doc.request_for_quotation },
            callback: function(r) {
                if (!r.message || !r.message.length) {
                    frm.dashboard.hide();
                    frappe.msgprint({ title: __("No Data"), message: __("No supplier or item details found."), indicator: "orange" });
                    return;
                }

                const html = frappe.render_template("bid_tabulation_discussion", { schedule_details: r.message });
                frm.dashboard.add_section(html, __("Supplier Details"));
                frm.dashboard.show();

                // Delegated click for last PO popup
                $(document).off("click", ".bt-item").on("click", ".bt-item", function(e) {
                    e.preventDefault();
                    let $el = $(this);
                    let item_code = $el.attr("data-item-code");

                    if (!item_code) {
                        frappe.msgprint({ title: __("Error"), message: __("Item code not found on clicked element."), indicator: "red" });
                        return;
                    }

                    frappe.call({
                        method: "custom_addons.custom_addons.doctype.bid_tabulation_discussion.bid_tabulation_discussion.get_last_po_for_item",
                        args: { item_code: item_code },
                        callback: function(res) {
                            let data = res.message || [];
                            if (!data.length) {
                                frappe.msgprint({ title: __("No POs"), message: __("No Purchase Orders found for {0}", [item_code]), indicator: "orange" });
                                return;
                            }

                            let rows = data.map(d => `
                                <tr>
                                    <td><a href="/app/purchase-order/${d.purchase_order}" target="_blank" style="color:#1f6feb; font-weight:bold;">${d.purchase_order}</a></td>
                                    <td>${d.supplier_name}</td>
                                    <td>${d.party_name}</td>
                                    <td>${frappe.format(d.transaction_date, "Date")}</td>
                                    <td>${frappe.format(d.price_list_rate, {fieldtype: 'Currency', options: d.currency || frappe.defaults.get_default('currency')})}</td>
                                    <td>${frappe.format(d.discount_amount, {fieldtype: 'Currency', options: d.currency || frappe.defaults.get_default('currency')})}</td>
                                    <td>${frappe.format(d.rate, {fieldtype: 'Currency', options: d.currency || frappe.defaults.get_default('currency')})}</td>
                                </tr>
                            `).join("");

                            let table = `
                                <div style="max-height:60vh; overflow:auto;">
                                    <table class="table table-bordered small">
                                        <thead>
                                            <tr>
                                                <th>PO No</th>
                                                <th>Party</th>
                                                <th>Party Name</th>
                                                <th>Date</th>
                                                <th>MRP</th>
                                                <th>Discount</th>
                                                <th>Rate</th>
                                            </tr>
                                        </thead>
                                        <tbody>${rows}</tbody>
                                    </table>
                                </div>
                            `;

                            let dialog = new frappe.ui.Dialog({
                                title: __("Last Purchase Orders for {0}", [item_code]),
                                size: "large",
                                primary_action_label: __("Close"),
                                primary_action() { dialog.hide(); }
                            });

                            dialog.$body.html(table);
                            dialog.show();
                        },
                        error: function(err) {
                            console.error("Error fetching POs:", err);
                            frappe.msgprint({ title: __("Error"), message: __("Failed to fetch purchase orders. See console for details."), indicator: "red" });
                        }
                    });
                });
            },
            error: function(err) { console.error("Error in get_supplier_details:", err); }
        });
    } else {
        frm.dashboard.hide();
    }
};
