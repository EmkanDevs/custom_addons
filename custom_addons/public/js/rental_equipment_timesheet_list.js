frappe.listview_settings['Rental Equipment Timesheet'] = {
    onload: function(listview) {

        // // --- 1. Mass Submit Button ---
        // listview.page.add_inner_button(__('Submit'), function() {
        //     const selected_items = listview.get_checked_items();

        //     if (selected_items.length === 0) {
        //         frappe.msgprint({
        //             message: __('Please select the Rental Equipment Timesheets you want to submit using the checkboxes.'),
        //             indicator: 'orange',
        //             title: __('No Items Selected')
        //         });
        //         return;
        //     }

        //     frappe.confirm(
        //         __('Are you sure you want to submit {0} selected Rental Equipment Timesheets?', [selected_items.length]),
        //         () => {
        //             frappe.call({
        //                 method: 'custom_addons.custom_addons.doc_events.rental_equipment_timesheet.mass_submit_rental_equipment_timesheets',
        //                 args: {
        //                     names: selected_items.map(d => d.name)
        //                 },
        //                 freeze: true,
        //                 freeze_message: __("Submitting..."),
        //                 callback: function(r) {
        //                     if (!r.exc) {
        //                         listview.refresh();
        //                         frappe.show_alert({
        //                             message: __('{0} Rental Equipment Timesheets submitted successfully', [r.message]),
        //                             indicator: 'green'
        //                         });
        //                     }
        //                 }
        //             });
        //         }
        //     );
        // });

        // --- 2. Upload Rental Equipment Timesheet Excel Button ---
        listview.page.add_inner_button(__('Upload Timesheet Excel'), function() {
            let dialog = new frappe.ui.Dialog({
                title: __('Upload Rental Equipment Timesheet Excel'),
                fields: [
                    {
                        label: __('Attach Excel File'),
                        fieldname: 'file',
                        fieldtype: 'Attach',
                        reqd: 1,
                        description: __('Upload .xlsx file with columns: SN, EQUIPMENT NAME, Project ID, Door No-Plate No, Operator Nationality, Supplier Name, Hour, Date')
                    }
                ],
                primary_action_label: __('Upload'),
                primary_action(values) {
                    let btn = dialog.get_primary_btn();
                    btn.prop('disabled', true);

                    frappe.call({
                        method: 'custom_addons.custom_addons.doc_events.rental_equipment_timesheet.upload_rental_equipment_timesheet',
                        args: {
                            file_url: values.file
                        },
                        freeze: true,
                        freeze_message: __("Processing rows, please wait..."),
                        callback: function(r) {
                            if (!r.exc && r.message) {
                                let res = r.message;
                                let msg = `<b>Upload Complete</b><br>`;
                                msg += `✅ Successfully Created: <b>${res.created.length}</b><br>`;
                                msg += `❌ Failed / Skipped: <b>${res.skipped.length}</b>`;

                                if (res.skipped.length > 0) {
                                    frappe.msgprint({
                                        title: __('Upload Results'),
                                        indicator: 'orange',
                                        message: msg + `<br><br><b>Errors:</b><br><small>${res.skipped.join('<br>')}</small>`
                                    });
                                } else {
                                    frappe.show_alert({
                                        message: __('{0} Rental Equipment Timesheets created successfully', [res.created.length]),
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