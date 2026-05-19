frappe.listview_settings['Timesheet'] = {
    onload: function(listview) {

        // =========================================================
        // 1. MASS SUBMIT BUTTON
        // =========================================================
        listview.page.add_inner_button(__('Submit'), function() {

            const selected_items = listview.get_checked_items();

            if (selected_items.length === 0) {

                frappe.msgprint({
                    message: __('Please select the Timesheets you want to submit using the checkboxes.'),
                    indicator: 'orange',
                    title: __('No Items Selected')
                });

                return;
            }

            frappe.confirm(
                __('Are you sure you want to submit {0} selected Timesheets?', [selected_items.length]),

                () => {

                    frappe.call({
                        method: 'custom_addons.custom_addons.doc_events.timesheet.mass_submit_timesheets',

                        args: {
                            names: selected_items.map(d => d.name)
                        },

                        freeze: true,
                        freeze_message: __("Submitting Timesheets..."),

                        callback: function(r) {

                            if (!r.exc) {

                                listview.refresh();

                                frappe.show_alert({
                                    message: __('{0} Timesheets submitted successfully', [selected_items.length]),
                                    indicator: 'green'
                                });
                            }
                        }
                    });
                }
            );
        });


        // =========================================================
        // 2. UPLOAD TIMESHEET EXCEL
        // =========================================================
        listview.page.add_inner_button(__('Upload Timesheet Excel'), function() {

            let dialog = new frappe.ui.Dialog({

                title: __('Upload Timesheet Excel'),

                size: 'large',

                fields: [

                    // -------------------------------------------------
                    // Instructions + Download Template
                    // -------------------------------------------------
                    {
                        fieldtype: 'HTML',
                        fieldname: 'template_section',

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
                                    1. Download the official Timesheet template.<br>
                                    2. Fill employee timesheet details in the same format.<br>
                                    3. Upload the completed Excel file below.
                                </div>

                                <a
                                    href="/api/method/custom_addons.custom_addons.doc_events.timesheet.download_timesheet_template"
                                    class="btn btn-primary btn-sm"
                                    target="_blank"
                                >
                                    <i class="fa fa-download"></i>
                                    Download Demo Template
                                </a>

                            </div>
                        `
                    },

                    // -------------------------------------------------
                    // File Upload
                    // -------------------------------------------------
                    {
                        label: __('Upload Filled Excel File'),
                        fieldname: 'file',
                        fieldtype: 'Attach',
                        reqd: 1
                    }

                ],

                primary_action_label: __('Upload Timesheet'),

                // =====================================================
                // UPLOAD ACTION
                // =====================================================
                primary_action(values) {

                    let btn = dialog.get_primary_btn();

                    btn.prop('disabled', true);

                    frappe.call({

                        method: 'custom_addons.custom_addons.doc_events.timesheet.upload_timesheet',

                        args: {
                            file_url: values.file
                        },

                        freeze: true,
                        freeze_message: __("Processing rows, please wait..."),

                        callback: function(r) {

                            if (!r.exc && r.message) {

                                let res = r.message;

                                let msg = `
                                    <div style="line-height: 1.8;">
                                        <b>Upload Completed</b><br><br>

                                        <span style="color: green;">
                                            ✅ Successfully Created:
                                        </span>
                                        <b>${res.created.length}</b><br>

                                        <span style="color: red;">
                                            ❌ Failed / Skipped:
                                        </span>
                                        <b>${res.skipped.length}</b>
                                    </div>
                                `;

                                // -------------------------------------------------
                                // SHOW ERRORS
                                // -------------------------------------------------
                                if (res.skipped.length > 0) {

                                    msg += `
                                        <hr>

                                        <div style="
                                            font-weight: 600;
                                            margin-bottom: 10px;
                                        ">
                                            Error Details
                                        </div>

                                        <div style="
                                            max-height: 250px;
                                            overflow-y: auto;
                                            background: #fff5f5;
                                            border: 1px solid #ffd6d6;
                                            padding: 12px;
                                            border-radius: 8px;
                                            font-size: 12px;
                                            line-height: 1.7;
                                        ">
                                            ${res.skipped.join('<br>')}
                                        </div>
                                    `;

                                    frappe.msgprint({
                                        title: __('Upload Results'),
                                        indicator: 'orange',
                                        message: msg
                                    });

                                } else {

                                    frappe.show_alert({
                                        message: __('{0} Timesheets created successfully', [res.created.length]),
                                        indicator: 'green'
                                    });
                                }

                                listview.refresh();

                                dialog.hide();
                            }
                        },

                        error: function() {

                            frappe.msgprint({
                                title: __('Upload Failed'),
                                indicator: 'red',
                                message: __('Something went wrong while processing the file.')
                            });
                        },

                        always: function() {
                            btn.prop('disabled', false);
                        }

                    });
                }
            });

            dialog.show();
        });
    }
};