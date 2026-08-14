// frappe.ui.form.on("Purchase Invoice", {
//     refresh(frm) {
//         if (frm.doc.docstatus === 0) {
//             frm.page.remove_inner_button(__("Purchase Order"), __("Get Items From"));
//             frm.page.remove_inner_button(__("Purchase Receipt"), __("Get Items From"));

//             frm.add_custom_button(__("Purchase Order"), () => {
//                 open_get_items_dialog(frm, "Purchase Order", "custom_addons.custom_addons.doc_events.query.po_query_with_totals",
//                     "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice");
//             }, __("Get Items From"));

//             frm.add_custom_button(__("Purchase Receipt"), () => {
//                 open_get_items_dialog(frm, "Purchase Receipt", "custom_addons.custom_addons.doc_events.query.pr_query_with_totals",
//                     "erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_invoice");
//             }, __("Get Items From"));
//         }
//     }
// });

// function open_get_items_dialog(frm, source_doctype, query_method, mapper_method) {
//     const date_field = source_doctype === "Purchase Receipt" ? "posting_date" : "transaction_date";

//     const dialog = new frappe.ui.form.MultiSelectDialog({
//         doctype: source_doctype,
//         target: frm,
//         setters: { supplier: frm.doc.supplier || null },
//         add_filters_group: 1,
//         date_field: date_field,
//         allow_child_item_selection: 1,
//         child_fieldname: "items",
//         child_columns: ["item_code", "item_name", "qty", "rate", "amount"],
//         columns: ["name", date_field, "supplier", "total", "grand_total", "status"],
//         get_query() {
//             return {
//                 query: query_method,
//                 filters: { supplier: frm.doc.supplier || undefined }
//             };
//         },
//         action(selections, args) {
//             if (!selections.length) return;

//             let mapper_args = {};
//             if (args && args.filtered_children && args.filtered_children.length) {
//                 mapper_args = {
//                     filtered_children: args.filtered_children,
//                     child_docname: "items"
//                 };
//             }

//             remove_empty_item_rows(frm);

//             // ADD THIS ↓
//             frappe.dom.freeze(__("Mapping {0} ...", [source_doctype]));

//             frappe.call({
//                 method: "frappe.model.mapper.map_docs",
//                 args: {
//                     method: mapper_method,
//                     source_names: selections,
//                     target_doc: frm.doc,
//                     args: mapper_args
//                 },
//                 callback: (r) => {
//                     // ADD THIS ↓
//                     frappe.dom.unfreeze();

//                     if (r.message) {
//                         frappe.model.sync(r.message);
//                         frm.dirty();
//                         frm.refresh();
//                     }
//                     dialog.dialog.hide();
//                 },
//                 error: (r) => {
//                     // ADD THIS ↓ (so it unfreezes even on error)
//                     frappe.dom.unfreeze();
//                 }
//             });
//         }
//     });
// }

// function remove_empty_item_rows(frm) {
//     let items = frm.doc.items || [];
//     let rows_to_remove = [];

//     items.forEach((row, idx) => {
//         if (!row.item_code && !row.item_name && (!row.qty || row.qty == 0)) {
//             rows_to_remove.push(row.name);
//         }
//     });

//     rows_to_remove.forEach(row_name => {
//         frm.doc.items = frm.doc.items.filter(r => r.name !== row_name);
//     });

//     frm.refresh_field('items');
// }











frappe.ui.form.on("Purchase Invoice", {
    refresh(frm) {
        sync_is_blanket_invoice_flag(frm);

        if (frm.doc.docstatus === 0) {
            frm.page.remove_inner_button(__("Purchase Order"), __("Get Items From"));
            frm.page.remove_inner_button(__("Purchase Receipt"), __("Get Items From"));
            frm.page.remove_inner_button(__("Blanket Order"), __("Get Items From"));

            if (!frm.doc.is_blanket_invoice) {
                frm.add_custom_button(__("Purchase Order"), () => {
                    open_get_items_dialog(frm, "Purchase Order", "custom_addons.custom_addons.doc_events.query.po_query_with_totals",
                        "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice");
                }, __("Get Items From"));

                frm.add_custom_button(__("Purchase Receipt"), () => {
                    open_get_items_dialog(frm, "Purchase Receipt", "custom_addons.custom_addons.doc_events.query.pr_query_with_totals",
                        "erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_invoice");
                }, __("Get Items From"));
            } else {
                frm.add_custom_button(__("Blanket Order"), () => {
                    open_blanket_order_dialog(frm);
                }, __("Get Items From"));
            }
        }

        toggle_add_row_for_blanket_invoice(frm);

        // Deferred to the next tick so this always runs AFTER core's own
        // refresh (which registers its own item_code query and would
        // otherwise silently overwrite ours if it runs later in the same cycle).
        setTimeout(() => {
            set_item_code_filter(frm);
            toggle_rate_readonly(frm);
        }, 0);
    },

    is_blanket_invoice(frm) {
        const existing_blanket = get_existing_blanket_order(frm);
        if (!frm.doc.is_blanket_invoice && existing_blanket) {
            frappe.confirm(
                __("Unchecking this will remove items pulled from Blanket Order {0}. Continue?", [existing_blanket]),
                () => {
                    clear_blanket_invoice_rows(frm);
                    frm.refresh();
                },
                () => {
                    frm.set_value("is_blanket_invoice", 1);
                }
            );
            return;
        }
        setTimeout(() => {
            set_item_code_filter(frm);
            toggle_rate_readonly(frm);
        }, 0);
        frm.refresh();
    }
});

// ---------------- Rate lock (child table: Purchase Invoice Item) ----------------
// Client-side convenience only — the real guard is the server-side
// rate re-assertion in validate_against_direct_purchase_invoice_blanket_order,
// which throws if item.rate != blanket_order_item.rate before submit.

frappe.ui.form.on("Purchase Invoice Item", {
    form_render(frm, cdt, cdn) {
        if (!frm.doc.is_blanket_invoice) return;

        const grid_row = frm.fields_dict["items"].grid.grid_rows_by_docname[cdn];
        if (grid_row && grid_row.grid_form && grid_row.grid_form.fields_dict.rate) {
            grid_row.grid_form.fields_dict.rate.df.read_only = 1;
            grid_row.grid_form.fields_dict.rate.refresh();
        }
    }
});

function sync_is_blanket_invoice_flag(frm) {
    if (!frm.doc.is_blanket_invoice && get_existing_blanket_order(frm)) {
        frm.doc.is_blanket_invoice = 1;
        frm.refresh_field("is_blanket_invoice");
    }
}

// ---------------- Purchase Order / Purchase Receipt ----------------

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
                    frappe.dom.unfreeze();
                    if (r.message) {
                        frappe.model.sync(r.message);
                        frm.dirty();
                        frm.refresh();
                    }
                    dialog.dialog.hide();
                },
                error: (r) => {
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

// ---------------- Blanket Order (own dialog, same UX as PO/PR) ----------------

function open_blanket_order_dialog(frm) {
    // if (!frm.doc.supplier) {
    //     frappe.throw(__("Select the Supplier first."));
    // }

    const dialog = new frappe.ui.form.MultiSelectDialog({
        doctype: "Blanket Order",
        target: frm,
        setters: { supplier: frm.doc.supplier || null },
        add_filters_group: 1,
        date_field: "from_date",
        allow_child_item_selection: 1,
        child_fieldname: "items",
        child_columns: ["item_code", "item_name", "qty", "rate"],
        columns: ["name", "supplier", "from_date", "to_date", "blanket_order_type"],
        get_query() {
            return {
                query: "custom_addons.custom_addons.doc_events.query.bo_query_with_totals"
            };
        },
        action(selections, args) {
            if (!selections.length) return;

            if (selections.length > 1) {
                frappe.msgprint(__("Please select items from a single Blanket Order only."));
                return;
            }

            let mapper_args = {};
            if (args && args.filtered_children && args.filtered_children.length) {
                // filtered_children is a flat list of Blanket Order Item row names.
                // No per-row parent info to check here — but since `selections` is
                // already capped to exactly one Blanket Order above, every row in
                // filtered_children necessarily belongs to that same one blanket.
                mapper_args = {
                    filtered_children: args.filtered_children,
                    child_docname: "items"
                };
            }

            remove_empty_item_rows(frm);
            frappe.dom.freeze(__("Mapping Blanket Order ..."));

            frappe.call({
                method: "frappe.model.mapper.map_docs",
                args: {
                    method: "custom_addons.custom_addons.doc_events.blanket_order.make_direct_purchase_invoice",
                    source_names: selections,
                    target_doc: frm.doc,
                    args: mapper_args
                },
                callback: (r) => {
                    frappe.dom.unfreeze();
                    if (r.message) {
                        frappe.model.sync(r.message);
                        frm.set_value("is_blanket_invoice", 1);
                        frm.dirty();
                        frm.refresh();
                    }
                    dialog.dialog.hide();
                },
                error: () => frappe.dom.unfreeze()
            });
        }
    });
}

function toggle_add_row_for_blanket_invoice(frm) {
    const grid = frm.fields_dict["items"].grid;
    grid.cannot_add_rows = !!frm.doc.is_blanket_invoice;
    grid.refresh();
}

function get_existing_blanket_order(frm) {
    const row = (frm.doc.items || []).find(r => r.blanket_order);
    return row ? row.blanket_order : null;
}

function clear_blanket_invoice_rows(frm) {
    frm.doc.items = (frm.doc.items || []).filter(row => !row.blanket_order);
    frm.refresh_field("items");
}

// ---------------- Item Code filter on the Items grid ----------------

function set_item_code_filter(frm) {
    frm.set_query("item_code", "items", function () {
        if (frm.doc.is_blanket_invoice) {
            return {
                query: "custom_addons.custom_addons.doc_events.query.blanket_eligible_item_query"
            };
        }
        return {};
    });

    frm.fields_dict["items"].grid.refresh();
}

// ---------------- Rate read-only toggle ----------------

function toggle_rate_readonly(frm) {
    const is_locked = !!frm.doc.is_blanket_invoice;

    frm.fields_dict["items"].grid.update_docfield_property("rate", "read_only", is_locked);
    frm.fields_dict["items"].grid.grid_rows.forEach(row => {
        if (row.grid_form && row.grid_form.fields_dict && row.grid_form.fields_dict.rate) {
            row.grid_form.fields_dict.rate.df.read_only = is_locked;
            row.grid_form.fields_dict.rate.refresh();
        }
    });

    frm.fields_dict["items"].grid.refresh();
}