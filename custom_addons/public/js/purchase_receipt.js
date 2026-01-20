frappe.ui.form.on("Purchase Receipt", {
	refresh: function(frm) {
        if (frm.doc.docstatus == 0) {
			frm.add_custom_button(
                __("Material Request"),
                function() {
                    if (!frm.doc.supplier) {
                        frappe.throw({
                            title: __("Mandatory"),
                            message: __("Please Select a Supplier"),
                        });
                    }
                    
                    // Create a dialog for multiple selection using Table MultiSelect instead
                    let d = new frappe.ui.Dialog({
                        title: __('Select Material Requests'),
                        fields: [
                            {
                                fieldtype: 'Link',
                                label: __('Supplier'),
                                fieldname: 'supplier',
                                options: 'Supplier',
                                default: frm.doc.supplier,
                                read_only: 1
                            },
                            {
                                fieldtype: 'Date',
                                label: __('From Date'),
                                fieldname: 'from_date',
                                reqd: 1,
                                // default: frm.doc.supplier
                            },
                            {
                                fieldtype: 'Date',
                                label: __('To Date'),
                                fieldname: 'to_date',
                                reqd: 1,
                                // default: frm.doc.supplier
                            },
                            {
                                fieldtype: 'Table',
                                label: __('Material Requests'),
                                fieldname: 'material_requests',
                                cannot_add_rows: false,
                                in_place_edit: true,
                                data: [],
                                fields: [
                                    {
                                        fieldtype: 'Link',
                                        fieldname: 'material_request',
                                        options: 'Material Request',
                                        label: __('Material Request'),
                                        in_list_view: 1,
                                        get_query: function() {
                                            const from_date = d.get_value('from_date');
                                            const to_date = d.get_value('to_date');
                                        let filters = {
                                                docstatus: 1,
                                                company: frm.doc.company,
                                                status: ["not in", ["Stopped", "Cancelled"]],
                                                material_request_type: "Purchase",
                                                transaction_date : ["between", [from_date, to_date]]
                                            };
                                            // if (from_date && to_date) {
                                            //     filters.transaction_date = ["between", [from_date, to_date]];
                                            // } 
                                            return { filters };
                                        }
                                    },     
                                ]
                            }
                        ],
                        primary_action_label: __('Get Items'),
                        primary_action: function() {
                            let values = d.get_values();
                            
                            if(!values.material_requests || values.material_requests.length === 0) {
                                frappe.throw(__("Please select at least one Material Request"));
                                return;
                            }
                            
                            // Extract material request names
                            let mr_list = values.material_requests.map(row => row.material_request);
                            
                            frappe.call({
                                method: "mkan_customization.mkan_customization.doc_events.purchase_receipt.make_purchase_receipt_from_multiple_mr",
                                args: {
                                    material_requests: mr_list,
                                    supplier: values.supplier
                                },
                                freeze: true,
                                freeze_message: __("Fetching items..."),
                                callback: function(r) {
                                    if(r.message) {
                                        // Add items to the current form
                                        $.each(r.message, function(i, item) {
                                            let d = frm.add_child("items");
                                            $.extend(d, item);
                                        });
                                        
                                        frm.refresh_field("items");
                                        frappe.show_alert({
                                            message: __("Items added from selected Material Requests"),
                                            indicator: 'green'
                                        });
                                    }
                                    d.hide();
                                }
                            });
                        }
                    });
                    
                    // Add handler to auto-fill Material Request fields
                    d.fields_dict.material_requests.grid.on_row_refresh = function(grid_row) {
                        let mr = grid_row.doc.material_request;
                        if(mr) {
                            frappe.db.get_value('Material Request', mr, ['status', 'transaction_date'], (r) => {
                                if(r) {
                                    grid_row.doc.status = r.status;
                                    grid_row.doc.transaction_date = r.transaction_date;
                                    d.fields_dict.material_requests.refresh();
                                }
                            });
                        }
                    };
                    
                    // Add an empty row to start
                    d.fields_dict.material_requests.df.data = [{}];
                    d.fields_dict.material_requests.refresh();
                    d.show();
                },
                __("Get Items From")
            );
		}
    }
});