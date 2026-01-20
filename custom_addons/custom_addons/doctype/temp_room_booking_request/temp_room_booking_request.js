// Copyright (c) 2025, Finbyz and contributors
// For license information, please see license.txt

frappe.ui.form.on("Temp Room Booking Request", {
	refresh(frm) {
		// Add Create button to create Temp Room Booking
		if (frm.doc.docstatus == 1) {
			frm.add_custom_button(__("Create Temp Room Booking"), function() {
				frm.call({
					method: "custom_addons.custom_addons.doctype.temp_room_booking_request.temp_room_booking_request.create_temp_room_booking",
					args: {
						source_name: frm.doc.name
					},
					callback: function(r) {
						if (r.message) {
							frappe.model.sync(r.message)
							frappe.set_route("Form", "Temp Room Booking", r.message.name);
						}
					}
				});
			}, __("Create"));
		}
	},
});
