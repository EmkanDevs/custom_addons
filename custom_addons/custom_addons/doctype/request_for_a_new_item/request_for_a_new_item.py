# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class RequestforaNewItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		date_required: DF.Date | None
		item_code: DF.Data | None
		item_description: DF.SmallText | None
		item_group_name: DF.Literal["Item Group"]
		item_name: DF.Data | None
		manufacturer: DF.Link | None
		project: DF.Link | None
		unit_of_measure: DF.Link | None
	# end: auto-generated types
	pass
