// Target employee accounts matching constants
const EMPLOYEE_ACCOUNT_NUMBERS = ["1158101", "1159000", "1159104", "1159102"];
const EMPLOYEE_ACCOUNT_NAMES = [
    "petty cash (business advance)",
    "employee loans",
    "employee other deduction",
    "employee other deductions",
    "employee loans (e.o.s)",
    "employee loan (e.o.s)",
    "mega employee loan"
];

function is_employee_target_account(account) {
    if (!account) return false;
    const acc_str = String(account).trim();

    for (const num of EMPLOYEE_ACCOUNT_NUMBERS) {
        if (acc_str.startsWith(num) || acc_str.includes(num)) {
            return true;
        }
    }

    const lower = acc_str.toLowerCase();
    for (const name of EMPLOYEE_ACCOUNT_NAMES) {
        if (lower.includes(name)) {
            return true;
        }
    }

    return false;
}

function reset_shared_table_meta(frm) {
    const grid = frm.fields_dict.accounts && frm.fields_dict.accounts.grid;
    if (grid) {
        (grid.docfields || []).forEach(df => {
            if (df.fieldname === "party_type" || df.fieldname === "party") {
                df.reqd = 0;
                df.mandatory_depends_on = null;
            }
        });
        if (grid.fields_map) {
            if (grid.fields_map.party) {
                grid.fields_map.party.reqd = 0;
                grid.fields_map.party.mandatory_depends_on = null;
            }
            if (grid.fields_map.party_type) {
                grid.fields_map.party_type.reqd = 0;
                grid.fields_map.party_type.mandatory_depends_on = null;
            }
        }
        if (grid.header_row && grid.header_row.columns) {
            ["party_type", "party"].forEach(fieldname => {
                const col = grid.header_row.columns[fieldname];
                if (col && col.static_area) {
                    col.static_area.removeClass("reqd");
                }
            });
        }
    }

    const pt_df = frappe.meta.get_docfield("Journal Entry Account", "party_type");
    if (pt_df) {
        pt_df.reqd = 0;
        pt_df.mandatory_depends_on = null;
    }
    const p_df = frappe.meta.get_docfield("Journal Entry Account", "party");
    if (p_df) {
        p_df.reqd = 0;
        p_df.mandatory_depends_on = null;
    }

    (frappe.meta.docfield_list["Journal Entry Account"] || []).forEach(df => {
        if (df.fieldname === "party_type" || df.fieldname === "party") {
            df.reqd = 0;
            df.mandatory_depends_on = null;
        }
    });
}

function sync_row_mandatory_states(frm) {
    if (!frm || frm.doctype !== "Journal Entry") return;

    reset_shared_table_meta(frm);

    const grid = frm.fields_dict.accounts && frm.fields_dict.accounts.grid;

    (frm.doc.accounts || []).forEach(row => {
        const is_target = is_employee_target_account(row.account);
        const copy = frappe.meta.get_docfield_copy("Journal Entry Account", row.name);
        if (copy) {
            if (copy.party) {
                copy.party.reqd = is_target ? 1 : 0;
                copy.party.mandatory_depends_on = null;
            }
            if (copy.party_type) {
                copy.party_type.reqd = is_target ? 1 : 0;
                copy.party_type.mandatory_depends_on = null;
            }
        }

        const grid_row = grid && grid.grid_rows_by_docname && grid.grid_rows_by_docname[row.name];
        if (grid_row) {
            if (grid_row.grid_form) {
                grid_row.grid_form.toggle_reqd("party_type", is_target);
                grid_row.grid_form.toggle_reqd("party", is_target);
            }
        }
    });

    reset_shared_table_meta(frm);
}

// Hook check_mandatory so that when saving, Journal Entry always sets row-level reqd correctly
if (!frappe.ui.form._orig_check_mandatory) {
    frappe.ui.form._orig_check_mandatory = frappe.ui.form.check_mandatory;
    frappe.ui.form.check_mandatory = function (frm) {
        if (frm && frm.doctype === "Journal Entry") {
            frm.doc.party_not_required = 1;
            sync_row_mandatory_states(frm);
        }
        return frappe.ui.form._orig_check_mandatory.apply(this, arguments);
    };
}

frappe.ui.form.on("Journal Entry", {
    onload(frm) {
        frm.set_value("party_not_required", 1);
        sync_row_mandatory_states(frm);
    },

    refresh(frm) {
        if (!frm.doc.party_not_required) {
            frm.set_value("party_not_required", 1);
        }
        sync_row_mandatory_states(frm);
    },

    before_save(frm) {
        frm.doc.party_not_required = 1;
        sync_row_mandatory_states(frm);
    },

    before_submit(frm) {
        frm.doc.party_not_required = 1;
        sync_row_mandatory_states(frm);
    },

    validate(frm) {
        frm.doc.party_not_required = 1;
        sync_row_mandatory_states(frm);

        let missing_party_rows = [];
        (frm.doc.accounts || []).forEach(row => {
            if (is_employee_target_account(row.account)) {
                if (!row.party_type) {
                    frappe.model.set_value(row.doctype, row.name, "party_type", "Employee");
                }
                if (!row.party && row.employee) {
                    frappe.model.set_value(row.doctype, row.name, "party", row.employee);
                }
                if (row.party && !row.employee && frm.fields_dict.accounts?.grid?.docfields?.some(f => f.fieldname === "employee")) {
                    frappe.model.set_value(row.doctype, row.name, "employee", row.party);
                }
                if (!row.party) {
                    missing_party_rows.push(row.idx);
                }
            }
        });

        if (missing_party_rows.length > 0) {
            frappe.throw(
                __("Row #{0}: Party is mandatory for Employee accounts.", [missing_party_rows.join(", ")])
            );
            frappe.validated = false;
            return false;
        }
    },

    custom_project(frm) {
        update_project_cost_center(frm);
    },

    custom_cost_center(frm) {
        update_project_cost_center(frm);
    }
});

frappe.ui.form.on("Journal Entry Account", {
    account(frm, cdt, cdn) {
        const row = locals[cdt] && locals[cdt][cdn];
        if (!row) return;

        if (is_employee_target_account(row.account)) {
            frappe.model.set_value(cdt, cdn, "party_type", "Employee");
        }
        sync_row_mandatory_states(frm);
    },

    party_type(frm, cdt, cdn) {
        sync_row_mandatory_states(frm);
    },

    party(frm, cdt, cdn) {
        const row = locals[cdt] && locals[cdt][cdn];
        if (row && is_employee_target_account(row.account) && row.party) {
            if (!row.employee && frm.fields_dict.accounts?.grid?.docfields?.some(f => f.fieldname === "employee")) {
                frappe.model.set_value(cdt, cdn, "employee", row.party);
            }
        }
        sync_row_mandatory_states(frm);
    },

    employee(frm, cdt, cdn) {
        const row = locals[cdt] && locals[cdt][cdn];
        if (row && is_employee_target_account(row.account) && row.employee) {
            if (!row.party) {
                frappe.model.set_value(cdt, cdn, "party", row.employee);
            }
        }
        sync_row_mandatory_states(frm);
    },

    form_render(frm, cdt, cdn) {
        const row = locals[cdt] && locals[cdt][cdn];
        if (row && is_employee_target_account(row.account)) {
            if (!row.party_type) {
                frappe.model.set_value(cdt, cdn, "party_type", "Employee");
            }
        }
        sync_row_mandatory_states(frm);
    },

    accounts_add(frm, cdt, cdn) {
        sync_row_mandatory_states(frm);
    },

    accounts_remove(frm, cdt, cdn) {
        sync_row_mandatory_states(frm);
    }
});

function update_project_cost_center(frm) {
    (frm.doc.accounts || []).forEach(row => {
        if (frm.doc.custom_project) {
            row.project = frm.doc.custom_project;
        }

        if (frm.doc.custom_cost_center) {
            row.cost_center = frm.doc.custom_cost_center;
        }
    });

    frm.refresh_field("accounts");
}
