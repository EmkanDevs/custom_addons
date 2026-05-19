frappe.listview_settings['Medical Insurance Sheet'] = {
    onload: function(listview) {

        listview.page.add_inner_button(__('Upload'), function() {
            let dialog = new frappe.ui.Dialog({
                title: __('Batch Upload – Medical Insurance Sheet'),
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
                                    1. Download the official Medical Insurance Sheet template.<br>
                                    2. Fill in member details in the same format (BupaID, IDNo, MemberName …).<br>
                                    3. Upload the completed Excel or CSV file below.
                                </div>
                                <a
                                    href="/api/method/custom_addons.custom_addons.doc_events.medical_insurance_sheet.download_medical_insurance_template"
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
                        fieldtype: 'HTML',
                        fieldname: 'info',
                        options: `
                            <div class="alert alert-info" style="font-size:13px;margin-bottom:0">
                                Upload an <strong>Excel (.xlsx)</strong> or <strong>CSV</strong>
                                file exported from Bupa / CCHI.<br>
                                The first row must be the header row with the original column names
                                (<em>BupaID, IDNo, MemberName …</em>).<br>
                                Existing records (matched by <strong>BupaID</strong>) are
                                <strong>updated</strong>; new ones are <strong>created</strong>.
                            </div>`
                    },
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
                        method: 'custom_addons.custom_addons.doc_events.medical_insurance_sheet.batch_upload',
                        args: {
                            file_url: values.file
                        },
                        freeze: true,
                        freeze_message: __('Processing rows, please wait...'),
                        callback: function(r) {
                            if (!r.exc && r.message) {
                                let res = r.message;
                                let msg = `<b>Upload Complete</b><br>
                                    Created: ${res.created}<br>
                                    Updated: ${res.updated}<br>
                                    Skipped: ${res.skipped}`;

                                if (res.errors.length > 0) {
                                    let error_lines = res.errors
                                        .slice(0, 20)
                                        .map(e => `Row ${e.row} (${e.bupa_id}): ${e.error}`)
                                        .join('<br>');

                                    frappe.msgprint({
                                        title: __('Upload Results'),
                                        indicator: 'orange',
                                        message: msg + `<br><br><b>Errors:</b><br><small>${error_lines}</small>`
                                    });
                                } else {
                                    frappe.show_alert({
                                        message: __('Upload complete. Created: {0}, Updated: {1}', [res.created, res.updated]),
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
 
        // --- Delete All Records Button ---
        listview.page.add_inner_button(__('Delete All Records'), function() {
            frappe.confirm(
                __('Are you sure you want to <b>delete ALL</b> Medical Insurance Sheet records? This cannot be undone.'),
                function() {
                    frappe.call({
                        method: 'custom_addons.custom_addons.doc_events.medical_insurance_sheet.delete_all_records',
                        freeze: true,
                        freeze_message: __('Deleting all records, please wait...'),
                        callback: function(r) {
                            if (!r.exc && r.message) {
                                frappe.show_alert({
                                    message: __('{0} records deleted successfully', [r.message.deleted]),
                                    indicator: 'green'
                                });
                                listview.refresh();
                            }
                        }
                    });
                }
            );
        });
 
    }
};