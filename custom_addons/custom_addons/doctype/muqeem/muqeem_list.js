frappe.listview_settings['Muqeem'] = {
    onload: function (listview) {
        listview.page.add_inner_button("Import Excel/CSV", function () {
            let d = new frappe.ui.Dialog({
                title: 'Import Muqeem Data',
                fields: [
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
                                    <strong>Expected columns:</strong> Full Name, Gender, Country, Date of Birth, 
                                    National Code, Outside Country, Designation Name Arabic, Passport Number, 
                                    Passport Valid Upto, Residence Issue, Residence Expire, Resident Expire Hijri, 
                                    Employer Number, Employee Number
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
                        method: 'custom_addons.custom_addons.doctype.muqeem.muqeem.import_muqeem_data',
                        args: {
                            file_url: values.file
                        },
                        freeze: true,
                        freeze_message: __('Importing data, please wait...'),
                        callback: function (r) {
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
        listview.page.add_inner_button("Delete All", function () {
            frappe.confirm(
                "Are you sure you want to delete <b>ALL</b> records from Muqeem?",
                () => {
                    frappe.call({
                        method: "custom_addons.custom_addons.doctype.muqeem.muqeem.delete_all_muqeem",
                        freeze: true,
                        freeze_message: "Deleting all entries...",
                        callback: function (r) {
                            if (!r.exc) {
                                frappe.msgprint("All Muqeem entries deleted successfully.");
                                listview.refresh();
                            }
                        }
                    });
                }
            );
        });
    }
};
