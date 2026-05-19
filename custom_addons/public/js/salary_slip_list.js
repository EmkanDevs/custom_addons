frappe.listview_settings["Salary Slip"] = {
    onload: function (listview) {
        listview.page.add_inner_button(__("Upload Salary Slip Excel"), function () {

            // ── Step 1 : file-picker dialog ───────────────────────────────────
            let d = new frappe.ui.Dialog({
                title : __("Upload Salary Slip Excel"),
                fields: [
                    {
                        fieldtype: "HTML",
                        fieldname: "template_section",
                        options: `
                            <div style="
                                background: #f8f9fa;
                                border: 1px solid #dfe3e6;
                                border-radius: 10px;
                                padding: 18px;
                                margin-bottom: 15px;
                            ">
                                <div style="
                                    font-size: 15px;
                                    font-weight: 600;
                                    margin-bottom: 8px;
                                    color: #2c3e50;
                                ">
                                    Upload Instructions
                                </div>
                                <div style="
                                    font-size: 13px;
                                    line-height: 1.7;
                                    color: #555;
                                    margin-bottom: 15px;
                                ">
                                    1. Download the official Salary Slip template.<br>
                                    2. Fill employee salary details in the same format.<br>
                                    3. Upload the completed Excel file below.
                                </div>
                                
                                <a
                                    href="/api/method/custom_addons.custom_addons.doc_events.salary_slip.download_salary_slip_template"
                                    class="btn btn-primary btn-sm"
                                    target="_blank"
                                >
                                    <i class="fa fa-download"></i>
                                    Download Demo Template
                                </a>
                            </div>
                        `
                    },
                    {
                        label    : __("Attach File"),
                        fieldname: "file",
                        fieldtype: "Attach",
                        reqd     : 1,
                    },

                    {
                        fieldtype: "Section Break",
                        label    : __("Date Range (optional)"),
                        description: __(
                        ),
                    },
                    {
                        label    : __("Start Date"),
                        fieldname: "start_date",
                        fieldtype: "Date",
                    },
                    {
                        fieldtype: "Column Break",
                    },
                    {
                        label    : __("End Date"),
                        fieldname: "end_date",
                        fieldtype: "Date",
                    },
                ],
                primary_action_label: __("Upload"),
                primary_action(values) {
                    let file_url   = values.file;
                    let start_date = values.start_date || null;
                    let end_date   = values.end_date   || null;

                    // Guard: if one date is filled the other must be too
                    if ((start_date && !end_date) || (!start_date && end_date)) {
                        frappe.msgprint({
                            title    : __("Invalid Date Range"),
                            indicator: "orange",
                            message  : __("Please provide <b>both</b> Start Date and End Date, or leave both blank to upload everything."),
                        });
                        return;
                    }

                    if (start_date && end_date && start_date > end_date) {
                        frappe.msgprint({
                            title    : __("Invalid Date Range"),
                            indicator: "orange",
                            message  : __("Start Date cannot be after End Date."),
                        });
                        return;
                    }

                    let btn = d.get_primary_btn();
                    btn.prop("disabled", true);

                    // ── Step 2 : pre-flight component check ───────────────────
                    frappe.call({
                        method:
                           "custom_addons.custom_addons.doc_events.salary_slip.check_salary_components",
                        args         : { file_url },
                        freeze        : true,
                        freeze_message: __("Checking salary components…"),

                        callback: function (r) {
                            btn.prop("disabled", false);

                            if (r.exc || !r.message) return;

                            let missing = r.message; // [{name, type}, ...]

                            if (missing.length > 0) {
                                // ── Missing components found → block & inform ──
                                _show_missing_components_dialog(
                                    missing,
                                    file_url,
                                    start_date,
                                    end_date,
                                    listview,
                                    d
                                );
                            } else {
                                // ── All components exist → proceed to upload ───
                                _do_upload(file_url, start_date, end_date, listview, d);
                            }
                        },
                        always: function () {
                            btn.prop("disabled", false);
                        },
                    });
                },
            });

            d.show();
        });
    },
};


// ── Shows a blocking dialog listing every missing Salary Component ─────────────
function _show_missing_components_dialog(
    missing, file_url, start_date, end_date, listview, upload_dialog
) {
    let rows_html = missing.map(c => `
        <tr data-name="${frappe.utils.escape_html(c.name)}">
            <td style="padding:6px 10px; font-weight:500;">${frappe.utils.escape_html(c.name)}</td>
            <td style="padding:6px 10px;">
                <span class="indicator-pill ${c.type === "Earning" ? "green" : "red"} no-indicator-dot"
                      style="font-size:11px;">
                    ${c.type}
                </span>
            </td>
            <td style="padding:6px 10px;">
                <button class="btn btn-xs btn-primary create-component-btn"
                        data-name="${frappe.utils.escape_html(c.name)}"
                        data-type="${c.type}">
                    + Create
                </button>
            </td>
            <td style="padding:6px 10px; text-align:center;">
                <input type="checkbox" class="skip-component-chk"
                       data-name="${frappe.utils.escape_html(c.name)}"
                       title="Skip this component" />
            </td>
        </tr>
    `).join("");

    let msg_html = `
        <p style="margin-bottom:12px;">
            The following Salary Components are referenced in the Excel file but
            <b>do not exist</b> in ERPNext.<br>
            Either <b>Create</b> them, or <b>Skip</b> them (those rows will be
            uploaded without that component).
        </p>
        <table style="width:100%; border-collapse:collapse;">
            <thead>
                <tr style="border-bottom:1px solid var(--border-color);">
                    <th style="padding:6px 10px; text-align:left;">Component</th>
                    <th style="padding:6px 10px; text-align:left;">Type</th>
                    <th style="padding:6px 10px; text-align:left;">Action</th>
                    <th style="padding:6px 10px; text-align:center;">Skip</th>
                </tr>
            </thead>
            <tbody>${rows_html}</tbody>
        </table>
        <p style="margin-top:12px; color:var(--text-muted); font-size:12px;">
            After creating / skipping all components, click
            <b>Re-check &amp; Upload</b>.
        </p>
    `;

    let warn = new frappe.ui.Dialog({
        title               : __("Missing Salary Components"),
        indicator           : "orange",
        primary_action_label: __("Re-check & Upload"),

        primary_action() {
            // Collect skipped names from checked boxes
            let skipped_components = [];
            warn.$body.find(".skip-component-chk:checked").each(function () {
                skipped_components.push($(this).data("name"));
            });

            warn.hide();

            frappe.call({
                method:
                   "custom_addons.custom_addons.doc_events.salary_slip.check_salary_components",
                args         : { file_url },
                freeze        : true,
                freeze_message: __("Re-checking salary components…"),
                callback(r) {
                    if (r.exc || !r.message) return;

                    // Filter out components the user chose to skip
                    let still_missing = r.message.filter(
                        c => !skipped_components.includes(c.name)
                    );

                    if (still_missing.length > 0) {
                        _show_missing_components_dialog(
                            still_missing, file_url, start_date, end_date,
                            listview, upload_dialog
                        );
                    } else {
                        upload_dialog.hide();
                        _do_upload(
                            file_url, start_date, end_date,
                            listview, null, skipped_components
                        );
                    }
                },
            });
        },
    });

    warn.set_df_property = () => {};
    warn.$body.html(msg_html);
    warn.show();

    // "Create" button → open new Salary Component form in new tab
    warn.$body.find(".create-component-btn").on("click", function () {
        let name = $(this).data("name");
        let type = $(this).data("type");

        let params = new URLSearchParams({
            salary_component: name,
            type            : type,
        });
        let url = `/app/salary-component/new-salary-component-1?${params.toString()}`;
        window.open(url, "_blank");
    });

    // Checking "Skip" disables the Create button for that row (and vice-versa)
    warn.$body.find(".skip-component-chk").on("change", function () {
        let row = $(this).closest("tr");
        let btn = row.find(".create-component-btn");
        if ($(this).is(":checked")) {
            btn.prop("disabled", true).addClass("disabled");
        } else {
            btn.prop("disabled", false).removeClass("disabled");
        }
    });
}


function _do_upload(file_url, start_date, end_date, listview, dialog, skipped_components) {
    frappe.call({
        method:
           "custom_addons.custom_addons.doc_events.salary_slip.upload_salary_slips",
        args: {
            file_url,
            skipped_components: skipped_components || [],
            start_date        : start_date || null,
            end_date          : end_date   || null,
        },
        freeze        : true,
        freeze_message: __("Processing rows, please wait…"),
        callback: function (r) {
            if (!r.exc && r.message) {
                let res = r.message;

                // Surface the resolved date range to the user for clarity
                let date_info = (res.start_date && res.end_date)
                    ? `<br><small style="color:var(--text-muted);">
                           Period: ${res.start_date} → ${res.end_date}
                       </small>`
                    : "";

                let msg =
                    `<b>Upload Complete</b>${date_info}<br>` +
                    `Successfully created: <b>${res.created.length}</b><br>` +
                    `Failed / Skipped: <b>${res.skipped.length}</b>`;

                if (res.skipped.length > 0) {
                    frappe.msgprint({
                        title    : __("Upload Results"),
                        indicator: "orange",
                        message  :
                            msg +
                            `<br><br><b>Errors:</b><br>` +
                            `<small>${res.skipped.join("<br>")}</small>`,
                    });
                } else {
                    frappe.show_alert({
                        message  : __(
                            "{0} Salary Slips created successfully",
                            [res.created.length]
                        ),
                        indicator: "green",
                    });
                }

                listview.refresh();
                if (dialog) dialog.hide();
            }
        },
    });
}