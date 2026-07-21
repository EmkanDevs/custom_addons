frappe.ui.form.on("Purchase Invoice", {
    refresh(frm) {
        if (frm.doc.docstatus === 0) {
            frm.page.remove_inner_button(__("Purchase Order"), __("Get Items From"));
            frm.page.remove_inner_button(__("Purchase Receipt"), __("Get Items From"));

            frm.add_custom_button(__("Purchase Order"), () => {
                open_get_items_dialog(frm, "Purchase Order", "custom_addons.custom_addons.doc_events.query.po_query_with_totals",
                    "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice");
            }, __("Get Items From"));

            frm.add_custom_button(__("Purchase Receipt"), () => {
                open_get_items_dialog(frm, "Purchase Receipt", "custom_addons.custom_addons.doc_events.query.pr_query_with_totals",
                    "erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_invoice");
            }, __("Get Items From"));
        }
    }
});

function open_get_items_dialog(frm, source_doctype, query_method, mapper_method) {
    const date_field = source_doctype === "Purchase Receipt" ? "posting_date" : "transaction_date";

    const dialog = new frappe.ui.form.MultiSelectDialog({
        doctype: source_doctype,
        target: frm,
        setters: { supplier: frm.doc.supplier || null },
        add_filters_group: 1,
        date_field: date_field,
        allow_child_item_selection: 1,
        child_fieldname: "items",
        child_columns: ["item_code", "item_name", "qty", "rate", "amount"],
        columns: ["name", date_field, "supplier", "total", "grand_total", "status"],
        get_query() {
            return {
                query: query_method,
                filters: { supplier: frm.doc.supplier || undefined }
            };
        },
        action(selections, args) {
            if (!selections.length) return;

            let mapper_args = {};
            if (args && args.filtered_children && args.filtered_children.length) {
                mapper_args = {
                    filtered_children: args.filtered_children,
                    child_docname: "items"
                };
            }

            remove_empty_item_rows(frm);

            // ADD THIS ↓
            frappe.dom.freeze(__("Mapping {0} ...", [source_doctype]));

            frappe.call({
                method: "frappe.model.mapper.map_docs",
                args: {
                    method: mapper_method,
                    source_names: selections,
                    target_doc: frm.doc,
                    args: mapper_args
                },
                callback: (r) => {
                    // ADD THIS ↓
                    frappe.dom.unfreeze();

                    if (r.message) {
                        frappe.model.sync(r.message);
                        frm.dirty();
                        frm.refresh();
                    }
                    dialog.dialog.hide();
                },
                error: (r) => {
                    // ADD THIS ↓ (so it unfreezes even on error)
                    frappe.dom.unfreeze();
                }
            });
        }
    });
}

function remove_empty_item_rows(frm) {
    let items = frm.doc.items || [];
    let rows_to_remove = [];

    items.forEach((row, idx) => {
        if (!row.item_code && !row.item_name && (!row.qty || row.qty == 0)) {
            rows_to_remove.push(row.name);
        }
    });

    rows_to_remove.forEach(row_name => {
        frm.doc.items = frm.doc.items.filter(r => r.name !== row_name);
    });

    frm.refresh_field('items');
}