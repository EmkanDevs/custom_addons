from frappe.model.document import Document
import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt
from custom_addons.custom_addons.override import assign_to
from frappe.utils import cint


class BidTabulationDiscussion(Document):
	def after_insert(self):
		# assign to selected user group
		doc = frappe.get_doc("User Group",self.user_list)
		for row in doc.user_group_members:
			assign_to.add(
				dict(
					assign_to=[row.user],
					doctype="Bid Tabulation Discussion",
					name=self.name,
					priority= "Medium",
					notify=True,
				),
				ignore_permissions=True,
			)
		data = frappe.get_doc("Request for Quotation", self.request_for_quotation)
		value = data.items[0].material_request if data.items else ""
		self.material_request = value
		if self.material_request:
			doc = frappe.get_doc("Material Request",self.material_request)
			assign_to.add(
				dict(
					assign_to=[doc.owner],
					doctype="Bid Tabulation Discussion",
					name=self.name,
					priority= "Medium",
					notify=True,
				),
				ignore_permissions=True,
			)
	def before_insert(self):
		# throw an error on duplicate entry of Big Tabulation
		existing_doc = frappe.get_all(
			"Bid Tabulation Discussion",
			filters={
				"docstatus": ["<", 2],  
				"request_for_quotation": self.request_for_quotation,
				"name": ["!=", self.name]  
			},
			fields=["name"]
		)
		
		if existing_doc:
			for row in existing_doc:
				doc_name = row.name
				frappe.throw(
					f"""
					Bid Tabulation is already created for this Request for Quotation.
					<a href="/app/bid-tabulation-discussion/{doc_name}" style="color:blue;">Click here to view it.</a>
					""",
					title="Duplicate Bid Tabulation"
				)
		data = frappe.get_doc("Request for Quotation", self.request_for_quotation)
		value = data.items[0].material_request if data.items else ""
		self.material_request = value
		if self.request_for_quotation:
			doc = frappe.get_doc("Request for Quotation",self.request_for_quotation)
			if len(doc.suppliers) < 3:
				frappe.throw("At least 3 suppliers are required to create Bid tabulation")
	def before_save(self):
		# append supplier, reason and user in discussion
		if self.supplier and not self.reason:
			frappe.throw("Please add reason for supplier")
		elif self.reason and not self.supplier:
			frappe.throw("Please set supplier")
			
		if self.supplier and self.reason:
			
			self.append("discussion", {
				"supplier": self.supplier,
				"reason": self.reason,
				"user": frappe.session.user,
			})
			
			self.supplier = None
			self.reason = None
		

	def before_submit(self):
		supplier_count = {}
		# find total suppliers and set supplier quotation
		for row in self.discussion:
			supplier = row.supplier
			if supplier and row.selected_supplier:
				supplier_count[supplier] = supplier_count.get(supplier, 0) + 1
		
		if supplier_count:
			final_supplier = max(supplier_count, key=supplier_count.get)
			self.final_supplier = final_supplier
		else:
			frappe.throw(_("No suppliers found in the discussion table."))
		doc = frappe.db.sql("""
			SELECT
				sqi.name AS item_name, sq.name AS parent_name
			FROM
				`tabSupplier Quotation Item` sqi
			JOIN
				`tabSupplier Quotation` sq
			ON
				sqi.parent = sq.name
			WHERE
				sqi.request_for_quotation = %s
		""", (self.request_for_quotation), as_dict=True)
		
		if doc:
			for record in doc:
				parent = frappe.get_doc("Supplier Quotation", record.parent_name)
				self.db_set("supplier_quotation",parent.name)

@frappe.whitelist()
def set_supplier_quotation(request_for_quotation):
    # return parent name to set supplier quotation 
	doc = frappe.db.sql("""
	SELECT
		sqi.name AS item_name,
		sq.name AS parent_name,
		sq.supplier AS supplier_name
	FROM
		`tabSupplier Quotation Item` sqi
	JOIN
		`tabSupplier Quotation` sq
	ON
		sqi.parent = sq.name
	WHERE
		sqi.request_for_quotation = %s
	
""", (request_for_quotation,), as_dict=True)
	return [row.parent_name for row in doc]

@frappe.whitelist()
def fetch_attachments_and_display(request_for_quotation):
    # fetch attachments from supplier quotation and display
	doc = frappe.db.sql("""
		SELECT
			sqi.name AS item_name,
			sq.name AS parent_name,
			sq.supplier AS supplier_id
		FROM
			`tabSupplier Quotation Item` sqi
		JOIN
			`tabSupplier Quotation` sq
		ON
			sqi.parent = sq.name
		WHERE
			sqi.request_for_quotation = %s and 
			sq.docstatus = 1
		GROUP BY sq.name
	""", (request_for_quotation,), as_dict=True)
	
	if not doc:
		return "<p style='color: red;'>No supplier quotations found.</p>"
	
	html_content = """
		<div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; background-color: #fafafa;">
			<div style="display: flex; flex-direction: column; gap: 10px;">
	"""
	
	total_suppliers = len(doc)
	rows_needed = (total_suppliers + 1) // 2 
	
	for row_index in range(rows_needed):
		html_content += "<div style='display: flex; width: 100%; gap: 10px;'>"
		
		start_index = row_index * 2
		end_index = min(start_index + 2, total_suppliers)
		
		for i in range(start_index, end_index):
			row = doc[i]
			supplier_name = frappe.db.get_value("Supplier", row.supplier_id, "supplier_name") or "Unknown Supplier"
			
			files = frappe.get_all("File", filters={
				"attached_to_doctype": "Supplier Quotation",
				"attached_to_name": row.parent_name
			}, fields=["file_name", "file_url"])
			
			file_links = "".join(
				f'<a href="{file["file_url"]}" target="_blank" style="display: block; color: #007bff; text-decoration: none; padding: 3px 0;">📎 {file["file_name"]}</a>'
				for file in files
			) if files else "<span style='color: gray;'>No Attachments</span>"
			
			quotation_link = frappe.utils.get_url_to_form("Supplier Quotation", row.parent_name)
			
			html_content += f"""
				<div style="flex: 1; min-width: 45%; padding: 10px; border: 1px solid #ccc; border-radius: 5px; background: white;">
					<strong style="color: #333;">Supplier:</strong> {row.supplier_id} ({supplier_name}) <br>
					<strong style="color: #333;">Supplier Quotation:</strong> <a href="{quotation_link}" target="_blank" style="color: #28a745; text-decoration: none; font-weight: bold;">{row.parent_name}</a><br>
					<strong style="color: #333;">Attachments:</strong> {file_links}
				</div>
			"""
		
		if end_index - start_index == 1:
			html_content += """
				<div style="flex: 1; min-width: 45%;"></div>
			"""
		
		html_content += "</div>"
	
	html_content += "</div></div>"
	
	return html_content



@frappe.whitelist()
def get_supplier_options(docname):
    # return supplier 
	doc = frappe.get_doc("Request for Quotation", docname)
	return [row.supplier for row in doc.suppliers]

@frappe.whitelist()
def get_supplier_details(docname):
    # get all details of supplier
	rfq_doc = frappe.get_doc("Request for Quotation", docname)

	processed_suppliers = set()
	processed_items = set()

	supplier_details = []

	supplier_quotations = frappe.get_all(
		"Supplier Quotation",
		filters={"request_for_quotation": rfq_doc.name,"docstatus":1},
		fields=["name", "supplier", "total", "total_qty"],
		group_by = "name"
	)

	for sq in supplier_quotations:
		if sq.supplier not in processed_suppliers:
			supplier_name = frappe.db.get_value("Supplier", sq.supplier, "supplier_name") or ""
			supplier_details.append({
				"supplier": sq.supplier,
				"supplier_name": supplier_name,  # Added supplier name
				"item_code": None,
				"item_name": None,
				"qty": None,
				"uom": None,
				"price": None,
				"amount": None,
				"is_supplier_row": True,
				"total_qty": sq.total_qty,  # Total quantity
				"total": sq.total           # Total amount
			})
			processed_suppliers.add(sq.supplier)

		items = frappe.get_all(
			"Supplier Quotation Item",
			filters={"parent": sq.name,"docstatus":1},
			fields=["item_code", "item_name", "qty", "uom", "rate", "amount"]
		)
		for item in items:
			unique_item_key = f"{sq.supplier}-{item.item_code}-{item.qty}-{item.rate}"
			if unique_item_key not in processed_items:
				supplier_details.append({
					"supplier": sq.supplier,
					"supplier_name": supplier_name, 
					"item_code": item.item_code,
					"item_name": item.item_name,
					"qty": item.qty,
					"uom": item.uom,
					"price": item.rate,
					"amount": item.amount,
					"is_supplier_row": False
				})
				processed_items.add(unique_item_key)
	supplier_details = sorted(supplier_details, key=lambda i: i['supplier'], reverse=True)
	return supplier_details


@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None):
    # make purchase order 
	bid_tabulation = frappe.flags.args.bid_tabulation
	def set_missing_values(source, target):
		# set missing values 
		target.run_method("set_missing_values")
		target.run_method("get_schedule_dates")
		target.run_method("calculate_taxes_and_totals")
		target.bid_tabulation = bid_tabulation

	def update_item(obj, target, source_parent):
		# update item
		target.stock_qty = flt(obj.qty) * flt(obj.conversion_factor)


	doclist = get_mapped_doc(
		"Supplier Quotation",
		source_name,
		{
			"Supplier Quotation": {
				"doctype": "Purchase Order",
				"validation": {
					"docstatus": ["=", 1],
				},
			},
			"Supplier Quotation Item": {
				"doctype": "Purchase Order Item",
				"field_map": [
					["name", "supplier_quotation_item"],
					["parent", "supplier_quotation"],
					["material_request", "material_request"],
					["material_request_item", "material_request_item"],
					["sales_order", "sales_order"],
				],
				"postprocess": update_item,
			},
			"Purchase Taxes and Charges": {
				"doctype": "Purchase Taxes and Charges",
			},
		},
		target_doc,
		set_missing_values,
	)
	return doclist

@frappe.whitelist()
def make_quotation(source_name, target_doc=None):
    # make quotation
	bid_tabulation = frappe.flags.args.bid_tabulation
	def set_missing_values(source, target):
		# set missing value
		target.bid_tabulation = bid_tabulation
	doclist = get_mapped_doc(
		"Supplier Quotation",
		source_name,
		{
			"Supplier Quotation": {
				"doctype": "Quotation",
				"field_map": {
					"name": "supplier_quotation",
				},
				"validation": {
					"docstatus": ["=", 1],
				},
			},
			"Supplier Quotation Item": {
				"doctype": "Quotation Item",
				"condition": lambda doc: frappe.db.get_value("Item", doc.item_code, "is_sales_item") == 1,
				"add_if_empty": True,
			},
		},
		target_doc,
		set_missing_values
	)

	return doclist

@frappe.whitelist()
def set_supplier_quotation_value(request_for_quotation,supplier):
    # return parent name to set supplier quotation value
	doc = frappe.db.sql("""
		SELECT
			sq.name AS parent_name,
			sq.supplier AS supplier_name
		FROM
			`tabSupplier Quotation Item` sqi
		JOIN
			`tabSupplier Quotation` sq
		ON
			sqi.parent = sq.name
		WHERE
			sqi.request_for_quotation = %s and sq.supplier = %s and sq.docstatus = 1
		GROUP BY sq.name, sq.supplier
	""", (request_for_quotation,supplier,), as_dict=True)

	return [row.parent_name for row in doc]



@frappe.whitelist()
def get_last_po_for_item(item_code):
    settings_list = frappe.get_all(
        "Price Settings",           
        fields=["limit_for_last_fetched_po"],
        limit=1                
    )
    
    limit_val = cint(settings_list[0].limit_for_last_fetched_po) if settings_list else 5

    po_list = frappe.db.sql("""
        SELECT 
            po.name AS purchase_order,
			po.supplier AS party,
            po.transaction_date,
			po.supplier_name AS party_name,
            poi.discount_amount,
            poi.rate,
            poi.price_list_rate,
			poi.item_code,
            po.supplier AS supplier_name
        FROM `tabPurchase Order Item` poi
        LEFT JOIN `tabPurchase Order` po ON poi.parent = po.name
        WHERE poi.item_code = %s
        ORDER BY po.transaction_date DESC
        LIMIT %s
    """, (item_code, limit_val), as_dict=True)

    return po_list



