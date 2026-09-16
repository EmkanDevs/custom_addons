frappe.ui.form.on('Item', {

    refresh(frm) {
        frm.set_query('custom_item_group_l1', () => {
            return {
                filters: {
                    parent_item_group: 'All Item Groups'
                }
            }
        })
        frm.set_query('custom_item_group_l2', () => {
            return {
                filters: {
                    parent_item_group: frm.doc.custom_item_group_l1
                }
            }
        })
        frm.set_query('custom_item_group_l3', () => {
            return {
                filters: {
                    parent_item_group: frm.doc.custom_item_group_l2
                }
            }
        })
        frm.set_query('item_group', () => {
            return {
                filters: {
                    is_group: 0,
                    parent_item_group: frm.doc.custom_item_group_l3
                }
            }
        })
        remove_duplicate_description(frm);
        set_item_code_preview(frm);
    },

    onload: function (frm) {
        remove_duplicate_description(frm);
    },

    // Re-filter child level whenever a parent group changes, and clear
    // the now-invalid child selections so stale values can't linger.
    custom_item_group_l1(frm) {
        frm.set_value('custom_item_group_l2', '');
        frm.set_value('custom_item_group_l3', '');
        frm.set_value('item_group', '');
    },
    custom_item_group_l2(frm) {
        frm.set_value('custom_item_group_l3', '');
        frm.set_value('item_group', '');
    },
    custom_item_group_l3(frm) {
        frm.set_value('item_group', '');
    },

    // Abbreviation fields (likely fetched from the linked item groups) —
    // whenever any of them or the base abbreviation changes, refresh preview.
    custom_abbreviation_l1: set_item_code_preview,
    custom_abbreviation_l2: set_item_code_preview,
    custom_abbreviation_l3: set_item_code_preview,
    custom_abbreviation: set_item_code_preview,
})

function remove_duplicate_description(frm) {
    if (frm.doc.description && frm.doc.item_name &&
        frm.doc.description.trim() === frm.doc.item_name.trim()) {
        frm.doc.description = '';
        frm.refresh_field('description')
    }
}

function set_item_code_preview(frm) {
    // Only preview on a new, unsaved Item — never overwrite a real,
    // already-assigned item_code on an existing document.
    if (!frm.doc.__islocal) return;

    const l1 = (frm.doc.custom_abbreviation_l1 || '').trim();
    const l2 = (frm.doc.custom_abbreviation_l2 || '').trim();
    const l3 = (frm.doc.custom_abbreviation_l3 || '').trim();
    const abbr = (frm.doc.custom_abbreviation || '').trim();

    if (l1 && l2 && l3 && abbr) {
        // Preview only — the real running number is finalized server-side
        // in the before_insert hook (set_item_naming), which locks and
        // computes the next sequence. This is just so the mandatory
        // Item Code field isn't blank in the form before save.
        frm.set_value('item_code', `${l1}-${l2}-${l3}-${abbr}-####`);
    } else {
        frm.set_value('item_code', '');
    }
}