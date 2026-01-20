# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class TempRoomBookingRequest(Document):
	pass


@frappe.whitelist()
def create_temp_room_booking(source_name, target_doc=None):
	"""
	Create Temp Room Booking from Temp Room Booking Request using get_mapped_doc
	"""
	def postprocess(source, target):
		# Set the source request reference
		target.temp_room_booking_request = source.name
	
	doc = get_mapped_doc("Temp Room Booking Request", source_name, {
		"Temp Room Booking Request": {
			"doctype": "Temp Room Booking",
			"field_map": {
				"request_date": "request_date",
				"project": "project",
				"project_name": "project_name",
				"booking_request_reason": "booking_request_reason",
				"location_arabic": "location_arabic",
				"location": "location",
				"cost_center": "cost_center",
				"suggested_hotellodge": "suggested_hotellodge",
				"remark": "remark"
			},
			"field_no_map": [
				"status",
				"amended_from"
			]
		},
		"Temp Room Booking List": {
			"doctype": "Temp Room Booking List",
			"field_map": {
				"parent": "parent",
				"parentfield": "parentfield",
				"parenttype": "parenttype"
			}
		}
	}, target_doc, postprocess)
	
	return doc
