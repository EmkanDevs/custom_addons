frappe.listview_settings['Timesheet'] = {
    onload: function(listview) {
        
        // --- 1. Mass Submit Button ---
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
                        freeze_message: __("Submitting..."),
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

        // --- 2. Upload Timesheet Excel Button ---
        listview.page.add_inner_button(__('Upload Timesheet Excel'), function() {
            let dialog = new frappe.ui.Dialog({
                title: __('Upload Timesheet Excel'),
                fields: [
                    {
                        label: __('Attach File'),
                        fieldname: 'file',
                        fieldtype: 'Attach',
                        reqd: 1
                    }
                ],
                primary_action_label: __('Upload'),
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
                                let msg = `<b>Upload Complete</b><br>`;
                                msg += `Successfully Created: ${res.created.length}<br>`;
                                msg += `Failed/Skipped: ${res.skipped.length}`;

                                if (res.skipped.length > 0) {
                                    frappe.msgprint({
                                        title: __('Upload Results'),
                                        indicator: 'orange',
                                        message: msg + `<br><br><b>Errors:</b><br><small>${res.skipped.join('<br>')}</small>`
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