// Copyright (c) 2025, Finbyz and contributors
// For license information, please see license.txt

// frappe.ui.form.on("IT Asset Management", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("IT Asset Management", {
    supplier: function(frm) {
        frm.set_query("purchase_order", function() {
            return {
                filters: {
                    supplier: frm.doc.supplier,
                }
            };
        });
    },

});


// frappe.ui.form.on("IT Asset Management", {
//     supplier: function(frm) {
//         if (frm.doc.supplier) {
//             frappe.call({
//                 method: "frappe.client.get_list",
//                 args: {
//                     doctype: "Purchase Order",
//                     filters: { supplier: frm.doc.supplier},
//                     fields: ["name"],
//                     limit_page_length: 1
//                 },
//                 callback: function(response) {
//                     if (response.message) {
//                         frm.set_value("purchase_order", response.message[0].name);
//                     }
//                 }
//             });
//         } else {
//             frm.set_value("purchase_order", null);
//         }
//     }
// });

