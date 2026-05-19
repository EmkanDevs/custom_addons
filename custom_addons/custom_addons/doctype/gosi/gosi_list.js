frappe.listview_settings['Gosi'] = {
    onload: function(listview) {
        // Import Excel/CSV Button
        listview.page.add_inner_button("Import Excel/CSV", function() {
            let d = new frappe.ui.Dialog({
                title: 'Import Gosi Data',
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
                                    1. Download the official GOSI template.<br>
                                    2. Fill in employee details in the same format.<br>
                                    3. Upload the completed Excel or CSV file below.
                                </div>
                                <a
                                    href="/api/method/custom_addons.custom_addons.doctype.gosi.gosi.download_gosi_template"
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
                        label: 'Upload File',
                        fieldname: 'file',
                        fieldtype: 'Attach',
                        reqd: 1,
                        options: {
                            restrictions: {
                                allowed_file_types: ['.xlsx', '.xls', '.csv']
                            }
                        }
                    },
                    {
                        fieldtype: 'HTML',
                        fieldname: 'help_text',
                        options: `
                            <div style="margin-top: 10px; padding: 10px; background-color: #f8f9fa; border-radius: 4px;">
                                <p style="margin: 0; font-size: 12px; color: #6c757d;">
                                    <strong>Supported formats:</strong> Excel (.xlsx, .xls) and CSV (.csv)<br>
                                    <strong>Expected columns:</strong> Full Name, National Code, Country, Gender, Date of Birth, 
                                    Basic Salary, Housing, Commissions, Other Allowances, Total Salary, 
                                    Subject to Contributions, Designation Name Arabic, Date of Enrollment, 
                                    Eligibility for Social Insurance System 1445
                                </p>
                            </div>
                        `
                    }
                ],
                primary_action_label: 'Import',
                primary_action(values) {
                    if (!values.file) {
                        frappe.msgprint(__('Please select a file to import'));
                        return;
                    }

                    frappe.call({
                        method: 'custom_addons.custom_addons.doctype.gosi.gosi.import_gosi_data',
                        args: {
                            file_url: values.file
                        },
                        freeze: true,
                        freeze_message: __('Importing data, please wait...'),
                        callback: function(r) {
                            if (!r.exc) {
                                d.hide();
                                frappe.msgprint({
                                    title: __('Import Successful'),
                                    message: r.message,
                                    indicator: 'green'
                                });
                                listview.refresh();
                            }
                        }
                    });
                }
            });
            d.show();
        });

        // Delete All Button
        listview.page.add_inner_button("Delete All", function() {
            frappe.confirm(
                "Are you sure you want to delete <b>ALL</b> records from Gosi?",
                () => {
                    frappe.call({
                        method: "custom_addons.custom_addons.doctype.gosi.gosi.delete_all_gosi",
                        freeze: true,
                        freeze_message: "Deleting all entries...",
                        callback: function(r) {
                            if (!r.exc) {
                                frappe.msgprint("All Gosi entries deleted successfully.",);
                                listview.refresh();
                            }
                        }
                    });
                }
            );
        });
    }
};
