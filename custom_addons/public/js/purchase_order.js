frappe.ui.form.on("Purchase Order", {
    refresh: function (frm) {
        frm.add_custom_button(
            __("Service Status"),
            () => {
                frappe.call({
                    method: "mkan_customization.mkan_customization.doc_events.purchase_order.service_status_map",
                    args: {
                        source_name: frm.doc.name
                    },
                    callback: function (response) {
                        if (response.message) {
                            frappe.model.sync(response.message);
                            frappe.set_route("Form", response.message.doctype, response.message.name);
                        }
                    }
                });
            },
            __("Create")
        );
        if (frm.doc.custom_bid_tabulation_check == 0) {
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Purchase Order",
                    filters: {
                        docstatus: ["<", 2],
                        bid_tabulation: frm.doc.bid_tabulation
                    },
                    fields: ["name"]
                },
                callback: function (response) {
                    let existing_docs = response.message;
                    if (existing_docs.length > 0) {
                        let po_links = existing_docs
                            .map(row => `<a href="/app/purchase-order/${row.name}" style="color:blue;">${row.name}</a>`)
                            .join("<br>");

                        frappe.confirm(
                            `The following Purchase Orders already exist for this Bid Tabulation:<br><br>${po_links}<br><br>Do you want to proceed?`,
                            () => {
                                frappe.validated = true;
                                frm.save();
                            },
                            () => {
                                frappe.validated = false;
                                if (frm.doc.bid_tabulation) {
                                    frappe.set_route("Form", "Bid Tabulation Discussion", frm.doc.bid_tabulation);
                                }
                            }
                        );

                    }
                }
            });
        }
    }
});
