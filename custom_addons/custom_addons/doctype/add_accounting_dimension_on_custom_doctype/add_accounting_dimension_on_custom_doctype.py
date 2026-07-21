
# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    create_accounting_dimensions_for_doctype
)
from frappe.model.document import Document


class AddAccountingDimensionOnCustomDoctype(Document):
    pass


# NOTE ON FIELDNAMES
# -------------------
# The child table row of "Add Accounting Dimension On Custom Doctype" has
# these fields:
#   custom_doctype   -> Parent Doctype (Link)
#   has_child_table  -> Has Child (Check)
#   child_table      -> Child Table (Link)
#   field_and_script -> Parent field/script flag used by existing entries
#                       (0 means child-only, 1 means parent + child)


def _get_doctype_config():
    """
    Returns a dict of:
    {
        custom_doctype: {
            "has_child_table": bool,
            "child_table": str | None,
            "dont_create_field_and_script_for_parent": bool,
        }
    }
    """
    try:
        config = frappe.get_single("Add Accounting Dimension On Custom Doctype")
        result = {}
        for row in (config.doctype_list or []):
            dt, row_config = _normalize_doctype_config_row(row)
            if dt:
                result[dt] = row_config
        return result
    except frappe.DoesNotExistError:
        return {}


def _get_row_value(row, *fieldnames):
    for fieldname in fieldnames:
        if isinstance(row, dict):
            value = row.get(fieldname)
        else:
            value = getattr(row, fieldname, None)

        if value is not None:
            return value

    return None


def _as_bool(value):
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}

    return bool(value)


def _normalize_doctype_config_row(row):
    dt = _get_row_value(row, "custom_doctype", "parent_doctype", "doctype")
    if not dt:
        return None, {}

    has_child_table = _as_bool(
        _get_row_value(row, "has_child_table", "has_child")
    )
    child_table = _get_row_value(row, "child_table")
    explicit_skip_parent = _get_row_value(
        row,
        "dont_create_field_and_script_for_parent",
        "dont_create_field_and_script_for_parent_account",
    )
    parent_field_and_script = _get_row_value(
        row,
        "field_and_script",
        "script_and_field",
    )

    if explicit_skip_parent is not None:
        skip_parent = _as_bool(explicit_skip_parent)
    elif has_child_table and child_table and parent_field_and_script is not None:
        skip_parent = not _as_bool(parent_field_and_script)
    else:
        skip_parent = False

    return dt, {
        "has_child_table": has_child_table,
        "child_table": child_table,
        "dont_create_field_and_script_for_parent": skip_parent,
    }


def _load_doctype_config_overrides(doctype_configs):
    if not doctype_configs:
        return {}

    if isinstance(doctype_configs, str):
        import json

        doctype_configs = json.loads(doctype_configs)

    if isinstance(doctype_configs, dict):
        rows = []
        for dt, cfg in doctype_configs.items():
            if isinstance(cfg, dict):
                rows.append({"custom_doctype": dt, **cfg})
            else:
                rows.append(cfg)
    else:
        rows = doctype_configs

    result = {}
    for row in rows:
        dt, row_config = _normalize_doctype_config_row(row)
        if dt:
            result[dt] = row_config

    return result


def _get_configured_child_table(cfg):
    """Return the configured child table only when the row opts into child support."""
    if not cfg.get("has_child_table"):
        return None

    return cfg.get("child_table")


def _resolve_field_targets(dt, cfg, warn=False):
    """
    Determine which doctype(s) should receive/lose/have-reordered
    accounting dimension custom fields for a given configuration row,
    and (indirectly, via `_use_child_only_template`) which Client Script
    template applies.

    Rules:
    - The child table is in-scope whenever "Has Child" is checked AND a
      Child Table is specified.
    - The parent doctype is in-scope UNLESS the child table is in-scope
      AND the row is configured as child-only. Existing rows store that
      as `field_and_script = 0`.

    This single helper is reused by field creation, field removal, and
    field reordering, so the targeting logic only lives in one place.
    """
    has_child_flag = bool(cfg.get("has_child_table"))
    child_table = _get_configured_child_table(cfg)
    skip_parent = bool(cfg.get("dont_create_field_and_script_for_parent"))

    if has_child_flag and not child_table:
        if warn:
            frappe.msgprint(
                f"{dt}: 'Has Child' is checked but no Child Table is "
                f"specified. Treating this as a parent-only doctype."
            )
        has_child_flag = False

    has_child = has_child_flag and bool(child_table)

    if skip_parent and not has_child and warn:
        frappe.msgprint(
            f"{dt}: 'Don't Create Field and Script for Parent Account' "
            f"has no effect because no valid child table is configured. "
            f"Fields/script will be created on the parent doctype."
        )

    targets = []
    if not (has_child and skip_parent):
        targets.append(dt)
    if has_child:
        targets.append(child_table)

    return targets


def _use_child_only_template(cfg):
    """
    True when the generated Client Script should contain ONLY child-table
    logic (no parent field handlers, no parent<->child sync) because the
    parent doctype has been explicitly excluded from field/script creation.
    """
    return (
        bool(_get_configured_child_table(cfg))
        and bool(cfg.get("dont_create_field_and_script_for_parent"))
    )


def create_client_scripts_for_all_doctypes(
    doc=None,
    method=None,
    doctypes=None,
    doctype_configs=None,
):
    doctype_config = _get_doctype_config()
    doctype_config.update(_load_doctype_config_overrides(doctype_configs))

    if not doctypes:
        doctypes = list(doctype_config.keys())

    if not doctypes:
        return

    # ------------------------------------------------------------------
    # FULL JS  –  parent fields exist, child fields exist
    # ------------------------------------------------------------------
    full_js_template = r"""

(function() {
const ACCOUNTING_DIMENSION_FIELDS = [
    'cost_center',
    'sector',
    'scope',
    'section',
    'department',
    'region_location',
    'project'
];

const DEPARTMENT_PROJECT_NAMES = [
    'Services Related to Operation and Production (Overhead)',
    'General and Administrative Expenses (G&A)'
];

const ENABLE_CHILD_TABLE_DIMENSIONS = __ENABLE_CHILD_TABLE_DIMENSIONS__;
const ACCOUNTING_DIMENSION_CHILD_DOCTYPE = '__CHILD_TABLE__';

frappe.ui.form.on('__DOCTYPE__', {
    sector: function(frm) {
        clear_parent_value(frm, 'scope');
        apply_accounting_dimension_rules(frm);
        sync_child_accounting_dimensions(frm);
    },

    department: function(frm) {
        clear_parent_value(frm, 'section');
        apply_accounting_dimension_rules(frm);
        sync_child_accounting_dimensions(frm);
    },

    scope: function(frm) {
        sync_child_accounting_dimensions(frm);
    },
    cost_center: function(frm) {
        sync_child_accounting_dimensions(frm);
    },
    section: function(frm) {
        sync_child_accounting_dimensions(frm);
    },
    region_location: function(frm) {
        sync_child_accounting_dimensions(frm);
    },

    project: function(frm) {
        clear_parent_value(frm, 'department');
        apply_accounting_dimension_rules(frm);
        sync_child_accounting_dimensions(frm);
    },

    refresh: function(frm) {
        apply_accounting_dimension_rules(frm);
    }
});

function apply_accounting_dimension_rules(frm) {
    apply_parent_accounting_dimension_rules(frm);
    apply_child_accounting_dimension_rules(frm);
}

function apply_parent_accounting_dimension_rules(frm) {
    set_parent_query(frm, 'scope', () => {
        return frm.doc.sector ? { sector: frm.doc.sector } : {};
    });
    set_parent_query(frm, 'section', () => {
        return frm.doc.department ? { department: frm.doc.department } : {};
    });
    set_parent_query(frm, 'department', () => {
        return frm.doc.project ? { custom_project: frm.doc.project } : {};
    });

    toggle_parent_field(frm, 'scope', !!frm.doc.sector);
    toggle_parent_field(frm, 'section', !!frm.doc.department);
    toggle_parent_department_visibility(frm);
}

function apply_child_accounting_dimension_rules(frm) {
    get_dimension_child_tables(frm).forEach(table_df => {
        set_child_query(frm, table_df, 'scope', row => {
            return row.sector ? { sector: row.sector } : {};
        });
        set_child_query(frm, table_df, 'section', row => {
            return row.department ? { department: row.department } : {};
        });
        set_child_query(frm, table_df, 'department', row => {
            return row.project ? { custom_project: row.project } : {};
        });

        toggle_child_grid_field(frm, table_df, 'scope', row_has_value(frm, table_df, 'sector'));
        toggle_child_grid_field(frm, table_df, 'section', row_has_value(frm, table_df, 'department'));
        toggle_child_department_visibility(frm, table_df);
        bind_child_dimension_events(table_df.options);
    });
}

function bind_child_dimension_events(child_doctype) {
    if (!child_doctype || window['__accounting_dimension_bound_' + child_doctype]) {
        return;
    }

    window['__accounting_dimension_bound_' + child_doctype] = true;

    frappe.ui.form.on(child_doctype, {
        sector: function(frm, cdt, cdn) {
            clear_child_value(cdt, cdn, 'scope');
            apply_child_accounting_dimension_rules(frm);
        },
        department: function(frm, cdt, cdn) {
            clear_child_value(cdt, cdn, 'section');
            apply_child_accounting_dimension_rules(frm);
        },
        project: function(frm, cdt, cdn) {
            clear_child_value(cdt, cdn, 'department');
            apply_child_accounting_dimension_rules(frm);
            apply_child_row_query(frm, cdt, cdn, 'department', row => {
                return row.project ? { custom_project: row.project } : {};
            });
        },
        scope: function(frm) {
            apply_child_accounting_dimension_rules(frm);
        },
        section: function(frm) {
            apply_child_accounting_dimension_rules(frm);
        },
        cost_center: function(frm) {
            apply_child_accounting_dimension_rules(frm);
        },
        region_location: function(frm) {
            apply_child_accounting_dimension_rules(frm);
        }
    });
}

function set_parent_query(frm, fieldname, get_filters) {
    if (!frm.fields_dict[fieldname]) return;
    frm.set_query(fieldname, () => {
        return { filters: get_filters() };
    });
}

function set_child_query(frm, table_df, fieldname, get_filters) {
    const grid = get_grid(frm, table_df);
    if (!grid || !child_has_field(table_df.options, fieldname)) return;

    const grid_field = grid.get_field(fieldname);
    if (!grid_field) return;

    grid_field.get_query = function(doc, cdt, cdn) {
        const row = locals[cdt] && locals[cdt][cdn] ? locals[cdt][cdn] : {};
        return { filters: get_filters(row) };
    };
}

function apply_child_row_query(frm, cdt, cdn, fieldname, get_filters) {
    const table_df = get_child_table_df(frm, cdt);
    if (!table_df || !child_has_field(cdt, fieldname)) return;

    set_child_query(frm, table_df, fieldname, get_filters);
    set_open_child_control_query(frm, table_df, cdt, cdn, fieldname, get_filters);
}

function set_open_child_control_query(frm, table_df, cdt, cdn, fieldname, get_filters) {
    const grid = get_grid(frm, table_df);
    if (!grid) return;

    const grid_row = grid.grid_rows_by_docname && grid.grid_rows_by_docname[cdn];
    if (!grid_row) return;

    const row = locals[cdt] && locals[cdt][cdn] ? locals[cdt][cdn] : {};
    const get_query = function() {
        return { filters: get_filters(row) };
    };

    get_open_child_controls(grid_row, fieldname).forEach(control => {
        control.get_query = get_query;
        if (control.df) {
            control.df.get_query = get_query;
        }
    });
}

function get_open_child_controls(grid_row, fieldname) {
    const controls = [];
    if (grid_row.grid_form && grid_row.grid_form.fields_dict && grid_row.grid_form.fields_dict[fieldname]) {
        controls.push(grid_row.grid_form.fields_dict[fieldname]);
    }
    if (grid_row.fields_dict && grid_row.fields_dict[fieldname]) {
        controls.push(grid_row.fields_dict[fieldname]);
    }
    if (grid_row.columns && grid_row.columns[fieldname] && grid_row.columns[fieldname].field) {
        controls.push(grid_row.columns[fieldname].field);
    }
    return controls;
}

function toggle_parent_field(frm, fieldname, show) {
    if (!frm.fields_dict[fieldname]) return;
    frm.toggle_display(fieldname, show);
}

function toggle_parent_department_visibility(frm) {
    if (!frm.fields_dict.department) return;
    should_show_department(frm.doc.project).then(show => {
        frm.toggle_display('department', show);
    });
}

function toggle_child_grid_field(frm, table_df, fieldname, show) {
    const grid = get_grid(frm, table_df);
    if (!grid || !child_has_field(table_df.options, fieldname)) return;
    grid.update_docfield_property(fieldname, 'hidden', show ? 0 : 1);
    grid.refresh();
}

function toggle_child_department_visibility(frm, table_df) {
    if (!child_has_field(table_df.options, 'department')) return;
    const project = get_first_row_value(frm, table_df, 'project') || frm.doc.project;
    should_show_department(project).then(show => {
        toggle_child_grid_field(frm, table_df, 'department', show);
    });
}

function should_show_department(project) {
    if (!project) return Promise.resolve(false);
    return frappe.db.get_value('Project', project, 'project_name').then(r => {
        const project_name = (r.message && r.message.project_name) || '';
        return DEPARTMENT_PROJECT_NAMES.includes(project_name);
    });
}

function clear_parent_value(frm, fieldname) {
    if (frm.fields_dict[fieldname] && frm.doc[fieldname]) {
        frm.set_value(fieldname, '');
    }
}

function clear_child_value(cdt, cdn, fieldname) {
    const row = locals[cdt] && locals[cdt][cdn] ? locals[cdt][cdn] : null;
    if (row && row[fieldname]) {
        frappe.model.set_value(cdt, cdn, fieldname, '');
    }
}

function sync_child_accounting_dimensions(frm) {
    get_dimension_child_tables(frm).forEach(table_df => {
        (frm.doc[table_df.fieldname] || []).forEach(row => {
            ACCOUNTING_DIMENSION_FIELDS.forEach(fieldname => {
                if (!child_has_field(row.doctype, fieldname)) return;
                const parent_value = frm.doc[fieldname] || '';
                if ((row[fieldname] || '') !== parent_value) {
                    frappe.model.set_value(row.doctype, row.name, fieldname, parent_value);
                }
            });
        });
    });
}

function get_dimension_child_tables(frm) {
    if (!ENABLE_CHILD_TABLE_DIMENSIONS || !ACCOUNTING_DIMENSION_CHILD_DOCTYPE) {
        return [];
    }

    return (frm.meta.fields || []).filter(df => {
        if (df.fieldtype !== 'Table' || !df.options || !frm.fields_dict[df.fieldname]) {
            return false;
        }
        if (df.options !== ACCOUNTING_DIMENSION_CHILD_DOCTYPE) {
            return false;
        }
        return ACCOUNTING_DIMENSION_FIELDS.some(fieldname => child_has_field(df.options, fieldname));
    });
}

function get_child_table_df(frm, child_doctype) {
    return get_dimension_child_tables(frm).find(df => df.options === child_doctype);
}

function get_grid(frm, table_df) {
    return frm.fields_dict[table_df.fieldname] && frm.fields_dict[table_df.fieldname].grid;
}

function child_has_field(child_doctype, fieldname) {
    return !!frappe.meta.get_docfield(child_doctype, fieldname);
}

function row_has_value(frm, table_df, fieldname) {
    return (frm.doc[table_df.fieldname] || []).some(row => !!row[fieldname]);
}

function get_first_row_value(frm, table_df, fieldname) {
    const row = (frm.doc[table_df.fieldname] || []).find(item => !!item[fieldname]);
    return row ? row[fieldname] : '';
}
})();
"""

    # ------------------------------------------------------------------
    # CHILD-ONLY JS  –  no parent accounting-dimension fields exist
    # ------------------------------------------------------------------
    child_only_js_template = r"""

(function() {
const ACCOUNTING_DIMENSION_FIELDS = [
    'cost_center',
    'sector',
    'scope',
    'section',
    'department',
    'region_location',
    'project'
];

const DEPARTMENT_PROJECT_NAMES = [
    'Services Related to Operation and Production (Overhead)',
    'General and Administrative Expenses (G&A)'
];

const ENABLE_CHILD_TABLE_DIMENSIONS = __ENABLE_CHILD_TABLE_DIMENSIONS__;
const ACCOUNTING_DIMENSION_CHILD_DOCTYPE = '__CHILD_TABLE__';

frappe.ui.form.on('__DOCTYPE__', {
    refresh: function(frm) {
        apply_child_accounting_dimension_rules(frm);
    }
});

function apply_child_accounting_dimension_rules(frm) {
    get_dimension_child_tables(frm).forEach(table_df => {
        set_child_query(frm, table_df, 'scope', row => {
            return row.sector ? { sector: row.sector } : {};
        });
        set_child_query(frm, table_df, 'section', row => {
            return row.department ? { department: row.department } : {};
        });
        set_child_query(frm, table_df, 'department', row => {
            return row.project ? { custom_project: row.project } : {};
        });

        toggle_child_grid_field(frm, table_df, 'scope', row_has_value(frm, table_df, 'sector'));
        toggle_child_grid_field(frm, table_df, 'section', row_has_value(frm, table_df, 'department'));
        toggle_child_department_visibility(frm, table_df);
        bind_child_dimension_events(table_df.options);
    });
}

function bind_child_dimension_events(child_doctype) {
    if (!child_doctype || window['__accounting_dimension_bound_' + child_doctype]) {
        return;
    }

    window['__accounting_dimension_bound_' + child_doctype] = true;

    frappe.ui.form.on(child_doctype, {
        sector: function(frm, cdt, cdn) {
            clear_child_value(cdt, cdn, 'scope');
            apply_child_accounting_dimension_rules(frm);
        },
        department: function(frm, cdt, cdn) {
            clear_child_value(cdt, cdn, 'section');
            apply_child_accounting_dimension_rules(frm);
        },
        project: function(frm, cdt, cdn) {
            clear_child_value(cdt, cdn, 'department');
            apply_child_accounting_dimension_rules(frm);
            apply_child_row_query(frm, cdt, cdn, 'department', row => {
                return row.project ? { custom_project: row.project } : {};
            });
        },
        scope: function(frm) {
            apply_child_accounting_dimension_rules(frm);
        },
        section: function(frm) {
            apply_child_accounting_dimension_rules(frm);
        },
        cost_center: function(frm) {
            apply_child_accounting_dimension_rules(frm);
        },
        region_location: function(frm) {
            apply_child_accounting_dimension_rules(frm);
        }
    });
}

function set_child_query(frm, table_df, fieldname, get_filters) {
    const grid = get_grid(frm, table_df);
    if (!grid || !child_has_field(table_df.options, fieldname)) return;

    const grid_field = grid.get_field(fieldname);
    if (!grid_field) return;

    grid_field.get_query = function(doc, cdt, cdn) {
        const row = locals[cdt] && locals[cdt][cdn] ? locals[cdt][cdn] : {};
        return { filters: get_filters(row) };
    };
}

function apply_child_row_query(frm, cdt, cdn, fieldname, get_filters) {
    const table_df = get_child_table_df(frm, cdt);
    if (!table_df || !child_has_field(cdt, fieldname)) return;

    set_child_query(frm, table_df, fieldname, get_filters);
    set_open_child_control_query(frm, table_df, cdt, cdn, fieldname, get_filters);
}

function set_open_child_control_query(frm, table_df, cdt, cdn, fieldname, get_filters) {
    const grid = get_grid(frm, table_df);
    if (!grid) return;

    const grid_row = grid.grid_rows_by_docname && grid.grid_rows_by_docname[cdn];
    if (!grid_row) return;

    const row = locals[cdt] && locals[cdt][cdn] ? locals[cdt][cdn] : {};
    const get_query = function() {
        return { filters: get_filters(row) };
    };

    get_open_child_controls(grid_row, fieldname).forEach(control => {
        control.get_query = get_query;
        if (control.df) {
            control.df.get_query = get_query;
        }
    });
}

function get_open_child_controls(grid_row, fieldname) {
    const controls = [];
    if (grid_row.grid_form && grid_row.grid_form.fields_dict && grid_row.grid_form.fields_dict[fieldname]) {
        controls.push(grid_row.grid_form.fields_dict[fieldname]);
    }
    if (grid_row.fields_dict && grid_row.fields_dict[fieldname]) {
        controls.push(grid_row.fields_dict[fieldname]);
    }
    if (grid_row.columns && grid_row.columns[fieldname] && grid_row.columns[fieldname].field) {
        controls.push(grid_row.columns[fieldname].field);
    }
    return controls;
}

function toggle_child_grid_field(frm, table_df, fieldname, show) {
    const grid = get_grid(frm, table_df);
    if (!grid || !child_has_field(table_df.options, fieldname)) return;
    grid.update_docfield_property(fieldname, 'hidden', show ? 0 : 1);
    grid.refresh();
}

function toggle_child_department_visibility(frm, table_df) {
    if (!child_has_field(table_df.options, 'department')) return;
    const project = get_first_row_value(frm, table_df, 'project');
    should_show_department(project).then(show => {
        toggle_child_grid_field(frm, table_df, 'department', show);
    });
}

function should_show_department(project) {
    if (!project) return Promise.resolve(false);
    return frappe.db.get_value('Project', project, 'project_name').then(r => {
        const project_name = (r.message && r.message.project_name) || '';
        return DEPARTMENT_PROJECT_NAMES.includes(project_name);
    });
}

function clear_child_value(cdt, cdn, fieldname) {
    const row = locals[cdt] && locals[cdt][cdn] ? locals[cdt][cdn] : null;
    if (row && row[fieldname]) {
        frappe.model.set_value(cdt, cdn, fieldname, '');
    }
}

function get_dimension_child_tables(frm) {
    if (!ENABLE_CHILD_TABLE_DIMENSIONS || !ACCOUNTING_DIMENSION_CHILD_DOCTYPE) {
        return [];
    }

    return (frm.meta.fields || []).filter(df => {
        if (df.fieldtype !== 'Table' || !df.options || !frm.fields_dict[df.fieldname]) {
            return false;
        }
        if (df.options !== ACCOUNTING_DIMENSION_CHILD_DOCTYPE) {
            return false;
        }
        return ACCOUNTING_DIMENSION_FIELDS.some(fieldname => child_has_field(df.options, fieldname));
    });
}

function get_child_table_df(frm, child_doctype) {
    return get_dimension_child_tables(frm).find(df => df.options === child_doctype);
}

function get_grid(frm, table_df) {
    return frm.fields_dict[table_df.fieldname] && frm.fields_dict[table_df.fieldname].grid;
}

function child_has_field(child_doctype, fieldname) {
    return !!frappe.meta.get_docfield(child_doctype, fieldname);
}

function row_has_value(frm, table_df, fieldname) {
    return (frm.doc[table_df.fieldname] || []).some(row => !!row[fieldname]);
}

function get_first_row_value(frm, table_df, fieldname) {
    const row = (frm.doc[table_df.fieldname] || []).find(item => !!item[fieldname]);
    return row ? row[fieldname] : '';
}
})();
"""

    for dt in doctypes:
        cfg = doctype_config.get(dt, {})

        # The Client Script is always keyed by/bound to the PARENT
        # doctype's form (`dt`), because that's where the child table's
        # grid actually lives. What changes is which handlers it contains:
        # - child-only template: pure child-row/grid logic, no parent
        #   field handlers (used when the parent has been excluded from
        #   field/script creation).
        # - full template: parent + configured child-table logic
        #   (used for parent-only doctypes and for parent+child doctypes
        #   where the parent was NOT excluded).
        child_only = _use_child_only_template(cfg)

        template = child_only_js_template if child_only else full_js_template
        child_table = _get_configured_child_table(cfg) or ""
        code_for_doctype = (
            template.replace("__DOCTYPE__", dt.replace("'", "\\'"))
            .replace("__CHILD_TABLE__", (child_table or "").replace("'", "\\'"))
            .replace(
                "__ENABLE_CHILD_TABLE_DIMENSIONS__",
                "true" if child_table else "false",
            )
        )

        cs_name = f"{dt} - Sector Scope Linkage"
        existing = frappe.db.exists("Client Script", cs_name)

        if existing:
            cs_doc = frappe.get_doc("Client Script", existing)
            if cs_doc.script != code_for_doctype or not cs_doc.enabled:
                cs_doc.script = code_for_doctype
                cs_doc.enabled = 1
                cs_doc.save(ignore_permissions=True)
                frappe.msgprint(f"Updated Client Script for: {dt}")
        else:
            cs_doc = frappe.get_doc({
                "doctype": "Client Script",
                "name": cs_name,
                "dt": dt,
                "script": code_for_doctype,
                "enabled": 1,
            })
            cs_doc.insert(ignore_permissions=True)
            frappe.msgprint(f"Created Client Script for: {dt}")


def _reorder_fields_for_doctype(target_dt, dimension_fieldnames, modified):
    """
    Reorders accounting dimension custom fields on a single doctype
    (parent OR child table) so they stay grouped together, anchored near
    Project/Cost Center. Shared by every doctype that has fields created
    on it, regardless of whether it's a parent or a child table.
    """
    meta = frappe.get_meta(target_dt)
    all_fieldnames = {f.fieldname for f in meta.fields}

    custom_fields_data = frappe.get_all(
        "Custom Field",
        filters={"dt": target_dt},
        fields=["fieldname"],
    )
    all_fieldnames.update({f.fieldname for f in custom_fields_data})

    insert_after_section = _get_accounting_dimensions_anchor(all_fieldnames)

    if "accounting_dimensions_section" not in all_fieldnames:
        section_doc = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": target_dt,
            "fieldname": "accounting_dimensions_section",
            "label": "Accounting Dimensions",
            "fieldtype": "Section Break",
            "insert_after": insert_after_section,
        })
        section_doc.insert(ignore_permissions=True)
        modified.setdefault(target_dt, []).append(section_doc.name)
        all_fieldnames.add("accounting_dimensions_section")
    else:
        cf_name = frappe.db.exists(
            "Custom Field",
            {"dt": target_dt, "fieldname": "accounting_dimensions_section"},
        )
        if cf_name:
            cf_doc = frappe.get_doc("Custom Field", cf_name)
            if cf_doc.insert_after != insert_after_section:
                cf_doc.insert_after = insert_after_section
                cf_doc.save(ignore_permissions=True)
                modified.setdefault(target_dt, []).append(cf_name)

    updated_fields = []
    previous_field = "accounting_dimensions_section"

    for fieldname in dimension_fieldnames:
        if fieldname not in all_fieldnames:
            continue

        cf_name = frappe.db.exists(
            "Custom Field",
            {"dt": target_dt, "fieldname": fieldname},
        )

        if cf_name:
            cf_doc = frappe.get_doc("Custom Field", cf_name)
            if cf_doc.insert_after != previous_field:
                cf_doc.insert_after = previous_field
                cf_doc.save(ignore_permissions=True)
                updated_fields.append(cf_name)

            previous_field = fieldname

    if updated_fields:
        modified.setdefault(target_dt, []).extend(updated_fields)

    if target_dt in modified:
        frappe.clear_cache(doctype=target_dt)


def reorder_accounting_dimension_fields(
    doc=None,
    method=None,
    doctypes=None,
    doctype_configs=None,
):
    """
    Reorders accounting dimension fields so they stay grouped with
    Project/Cost Center, on every doctype that actually has fields
    (parent and/or child table), as determined by `_resolve_field_targets`.
    """
    doctype_config = _get_doctype_config()
    doctype_config.update(_load_doctype_config_overrides(doctype_configs))

    if not doctypes:
        doctypes = list(doctype_config.keys())

    if not doctypes:
        return

    dimension_fieldnames = _get_accounting_dimension_fieldnames()

    if not dimension_fieldnames:
        return

    target_dts = []
    for dt in doctypes:
        cfg = doctype_config.get(dt, {})
        for target_dt in _resolve_field_targets(dt, cfg):
            if target_dt not in target_dts:
                target_dts.append(target_dt)

    if not target_dts:
        return

    modified = {}

    for target_dt in target_dts:
        _reorder_fields_for_doctype(target_dt, dimension_fieldnames, modified)

    if modified:
        frappe.logger().info(
            f"[Accounting Dimension] Reordered fields for "
            f"{len(modified)} doctypes: {modified}"
        )


def delete_client_scripts_on_dimension_delete(doc, method):
    """
    Deletes all dynamically created Client Scripts if one of the
    Accounting Dimensions (Scope, Section, Department, Sector) is deleted.
    """
    tracked_dimensions = ["Scope", "Section", "Department", "Sector"]

    if doc.accounting_dimension not in tracked_dimensions:
        return

    deleted_count = 0

    doctype_config = _get_doctype_config()
    doctypes = list(doctype_config.keys())

    for dt in doctypes:
        cs_name = f"{dt} - Sector Scope Linkage"
        existing = frappe.get_all(
            "Client Script",
            filters={"name": cs_name},
        )

        for e in existing:
            frappe.delete_doc(
                "Client Script",
                e.name,
                ignore_permissions=True,
                force=True,
            )
            deleted_count += 1

    frappe.msgprint(
        f"Deleted {deleted_count} Client Scripts linked to Accounting "
        f"Dimension '{doc.accounting_dimension}'."
    )


def _create_dimension_fields_for_target(target_dt, dimensions):
    """
    Creates any missing accounting dimension Link fields on `target_dt`
    (which may be a parent doctype or a child table doctype). Returns
    (created_count, skipped_count).
    """
    meta = frappe.get_meta(target_dt)
    existing_fields = {f.fieldname for f in meta.fields}

    custom_fields = frappe.get_all(
        "Custom Field",
        filters={"dt": target_dt},
        fields=["fieldname"],
    )
    existing_custom_fields = {f.fieldname for f in custom_fields}
    existing_fields.update(existing_custom_fields)

    created_count = 0
    skipped_count = 0

    for dim in dimensions:
        if dim.fieldname in existing_fields:
            skipped_count += 1
            continue

        insert_after = _get_insert_after_for_field(
            dim.fieldname,
            existing_fields,
            existing_custom_fields,
        )

        try:
            cf = frappe.get_doc({
                "doctype": "Custom Field",
                "dt": target_dt,
                "fieldname": dim.fieldname,
                "label": dim.label,
                "fieldtype": "Link",
                "options": dim.document_type,
                "insert_after": insert_after,
            })
            cf.insert(ignore_permissions=True)
            created_count += 1
            existing_fields.add(dim.fieldname)
            existing_custom_fields.add(dim.fieldname)
        except frappe.DuplicateEntryError:
            skipped_count += 1
        except Exception as e:
            frappe.log_error(
                f"Failed to create {dim.fieldname} for {target_dt}: {str(e)}"
            )

    return created_count, skipped_count


def _remove_dimension_fields_for_target(target_dt, fieldnames):
    removed_count = 0

    for fieldname in fieldnames:
        cf_name = frappe.db.exists(
            "Custom Field",
            {"dt": target_dt, "fieldname": fieldname},
        )
        if cf_name:
            frappe.delete_doc(
                "Custom Field",
                cf_name,
                ignore_permissions=True,
                force=True,
            )
            removed_count += 1

    if removed_count:
        frappe.clear_cache(doctype=target_dt)

    return removed_count


@frappe.whitelist()
def add_dimensions_for_custom_doctypes(doctypes=None, doctype_configs=None):
    """
    Reads doctypes from the single doctype
    'Add Accounting Dimension On Custom Doctype'.

    For each configured doctype, `_resolve_field_targets()` decides where
    accounting dimension fields (and, correspondingly, script logic) are
    created:

    - Has Child unchecked (no child table):
        Fields are created on the parent doctype only (existing/legacy
        behaviour, fully preserved).

    - Has Child checked + Child Table specified,
      field_and_script = 1:
        Fields are created on BOTH the parent doctype and the child
        table. The generated Client Script contains both parent and
        child logic, so the accounting-dimension functionality works on
        both.

    - Has Child checked + Child Table specified,
      field_and_script = 0:
        Fields are created ONLY on the child table (nothing on the
        parent). The generated Client Script contains ONLY child-table
        logic.
    """
    doctype_config = _get_doctype_config()
    doctype_config.update(_load_doctype_config_overrides(doctype_configs))

    if not doctypes:
        doctypes = list(doctype_config.keys())

    if isinstance(doctypes, str):
        import json

        doctypes = json.loads(doctypes)

    doctypes = list(dict.fromkeys(filter(None, doctypes)))

    if not doctypes:
        frappe.msgprint("No valid doctypes provided in the list.")
        return

    # Get all active accounting dimensions
    dimensions = frappe.get_all(
        "Accounting Dimension",
        filters={"disabled": 0},
        fields=["fieldname", "document_type", "label"],
    )

    for dt in doctypes:
        cfg = doctype_config.get(dt, {})
        targets = _resolve_field_targets(dt, cfg, warn=True)

        if not targets:
            continue

        if _use_child_only_template(cfg):
            removed_count = _remove_dimension_fields_for_target(
                dt,
                [d.fieldname for d in dimensions if d.fieldname],
            )
            if removed_count:
                frappe.msgprint(
                    f"Removed {removed_count} parent dimension fields for: {dt}"
                )

        for target_dt in targets:
            created_count, skipped_count = _create_dimension_fields_for_target(
                target_dt, dimensions
            )

            if created_count:
                frappe.msgprint(
                    f"Created {created_count} dimension fields for: {target_dt}"
                )
            if skipped_count:
                frappe.msgprint(
                    f"Skipped {skipped_count} existing fields for: {target_dt}"
                )

    # Reorder fields on every doctype (parent and/or child) that has them.
    reorder_accounting_dimension_fields(
        doctypes=doctypes,
        doctype_configs=doctype_configs,
    )

    # Always create/update Client Scripts (full or child-only as needed).
    create_client_scripts_for_all_doctypes(
        doctypes=doctypes,
        doctype_configs=doctype_configs,
    )

    frappe.db.commit()
    frappe.msgprint(f"Successfully processed {len(doctypes)} doctypes.")


def _get_insert_after_for_field(
    fieldname,
    existing_fields,
    existing_custom_fields=None,
):
    """Determine appropriate insert_after for accounting dimension fields."""

    anchor = _get_accounting_dimensions_anchor(existing_fields)
    existing_custom_fields = existing_custom_fields or existing_fields

    field_order = (
        ["accounting_dimensions_section"]
        + _get_accounting_dimension_fieldnames()
    )

    if fieldname not in field_order:
        return anchor

    idx = field_order.index(fieldname)

    # Look backwards for the first existing field to insert after
    for i in range(idx - 1, -1, -1):
        if field_order[i] in existing_custom_fields:
            return field_order[i]

    return anchor


def _get_accounting_dimensions_anchor(existing_fields):
    """Prefer Project as the visual anchor for accounting dimensions."""

    if "project" in existing_fields:
        return "project"
    if "cost_center" in existing_fields:
        return "cost_center"
    if "dimension_col_break" in existing_fields:
        return "dimension_col_break"

    return None


def _get_accounting_dimension_fieldnames():
    dimension_fieldnames = [
        d.fieldname
        for d in frappe.get_all(
            "Accounting Dimension",
            filters={"disabled": 0},
            fields=["fieldname"],
            order_by="creation asc",
        )
        if d.fieldname
    ]

    preferred_order = [
        "cost_center",
        "sector",
        "scope",
        "department",
        "section",
        "region_location",
    ]

    return sorted(
        dimension_fieldnames,
        key=lambda fieldname: (
            preferred_order.index(fieldname)
            if fieldname in preferred_order
            else len(preferred_order),
            dimension_fieldnames.index(fieldname),
        ),
    )


@frappe.whitelist()
def remove_dimensions_for_custom_doctypes(doctypes=None, doctype_configs=None):
    """
    Removes accounting dimension custom fields from configured doctypes.

    Uses `_resolve_field_targets()` (same logic as field creation) to
    determine whether fields live on the parent, the child table, or
    both, and removes them from exactly those doctypes.
    """
    doctype_config = _get_doctype_config()
    doctype_config.update(_load_doctype_config_overrides(doctype_configs))

    if not doctypes:
        doctypes = list(doctype_config.keys())

    if isinstance(doctypes, str):
        import json

        doctypes = json.loads(doctypes)

    doctypes = list(dict.fromkeys(filter(None, doctypes)))

    if not doctypes:
        frappe.msgprint("No valid doctypes provided in the list.")
        return

    dimensions = frappe.get_all(
        "Accounting Dimension",
        filters={"disabled": 0},
        fields=["fieldname"],
    )
    fieldnames = [d.fieldname for d in dimensions if d.fieldname]

    removed_total = 0

    for dt in doctypes:
        cfg = doctype_config.get(dt, {})
        targets = _resolve_field_targets(dt, cfg)

        for target_dt in targets:
            removed_for_dt = _remove_dimension_fields_for_target(
                target_dt,
                fieldnames,
            )
            removed_total += removed_for_dt

        # The Client Script is always keyed by the parent doctype name,
        # regardless of where the fields themselves were created.
        cs_name = f"{dt} - Sector Scope Linkage"
        if frappe.db.exists("Client Script", cs_name):
            frappe.delete_doc(
                "Client Script",
                cs_name,
                ignore_permissions=True,
                force=True,
            )

    frappe.msgprint(
        f"Removed {removed_total} accounting dimension fields and "
        f"associated Client Scripts across {len(doctypes)} doctypes."
    )
