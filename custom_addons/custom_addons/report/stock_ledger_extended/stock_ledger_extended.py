# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import copy
from collections import defaultdict

import frappe
from frappe import _
from frappe.query_builder.functions import CombineDatetime, Sum
from frappe.utils import cint, flt, get_datetime
from frappe.query_builder.functions import Cast
from frappe.query_builder.functions import DateFormat
from erpnext.stock.doctype.inventory_dimension.inventory_dimension import get_inventory_dimensions
from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos
from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation import get_stock_balance_for
from erpnext.stock.doctype.warehouse.warehouse import apply_warehouse_filter
from erpnext.stock.utils import (
    is_reposting_item_valuation_in_progress,
    update_included_uom_in_report,
)


def execute(filters=None):
    is_reposting_item_valuation_in_progress()
    include_uom = filters.get("include_uom")
    columns = get_columns(filters)
    items = get_items(filters)
    sl_entries = get_stock_ledger_entries(filters, items)
    item_details = get_item_details(items, sl_entries, include_uom)
    if filters.get("batch_no"):
        opening_row = get_opening_balance_from_batch(filters, columns, sl_entries)
    else:
        opening_row = get_opening_balance(filters, columns, sl_entries)

    precision = cint(frappe.db.get_single_value("System Settings", "float_precision"))
    bundle_details = {}

    if filters.get("segregate_serial_batch_bundle"):
        bundle_details = get_serial_batch_bundle_details(sl_entries, filters)

    # ======================================================
    # BATCH-FETCH EXTENDED FIELDS (fixes N+1: was doing
    # 3-5 individual get_value() calls per SLE row, with
    # some of those calls literally duplicated).
    # ======================================================
    extended_maps = get_extended_field_maps(sl_entries)

    data = []
    conversion_factors = []
    if opening_row:
        data.append(opening_row)
        conversion_factors.append(0)

    actual_qty = stock_value = 0
    if opening_row:
        actual_qty = opening_row.get("qty_after_transaction")
        stock_value = opening_row.get("stock_value")

    available_serial_nos = {}
    inventory_dimension_filters_applied = check_inventory_dimension_filters_applied(filters)

    batch_balance_dict = frappe._dict({})
    if actual_qty and filters.get("batch_no"):
        batch_balance_dict[filters.batch_no] = [actual_qty, stock_value]

    for sle in sl_entries:
        item_detail = item_details[sle.item_code]
        sle.update(item_detail)

        # ======================================================
        # EXTENDED STOCK LEDGER FIELDS
        # ======================================================

        sle["creator"] = None
        sle["material_request"] = None
        sle["cost_center"] = None
        sle["is_petty_cash"] = 0
        sle["supplier_code"] = None
        sle["supplier_name"] = None
        sle["supplier_delivery_note"] = None
        sle["return_material_ref_doc"] = None
        sle["purchase_order"] = None
        sle["stock_entry_type"] = None
        sle["expense_account"] = sle.get("expense_account")

        # ======================================================
        # STOCK ENTRY DETAILS (from pre-fetched maps, no query here)
        # ======================================================

        if sle.voucher_type == "Stock Entry":

            stock_entry = extended_maps.stock_entries.get(sle.voucher_no)

            if stock_entry:

                sle["creator"] = stock_entry.owner
                sle["stock_entry_type"] = stock_entry.stock_entry_type

                sle["return_material_ref_doc"] = stock_entry.outgoing_stock_entry

                sle["supplier_code"] = stock_entry.custom_supplier_code_

                sle["supplier_name"] = stock_entry.custom_suppliers_name_

                if stock_entry.supplier:
                    sle["supplier_name"] = extended_maps.suppliers.get(stock_entry.supplier)

            # ------------------------------------------
            # STOCK ENTRY DETAIL (also covers material_request,
            # previously fetched again in a second, redundant query)
            # ------------------------------------------

            se_detail = extended_maps.se_details.get((sle.voucher_no, sle.item_code))

            if se_detail:

                sle["material_request"] = se_detail.material_request
                sle["cost_center"] = se_detail.cost_center
                sle["expense_account"] = se_detail.expense_account

        # ======================================================
        # PURCHASE RECEIPT DETAILS (from pre-fetched maps, no query here)
        # ======================================================

        elif sle.voucher_type == "Purchase Receipt":

            purchase_receipt = extended_maps.purchase_receipts.get(sle.voucher_no)

            if purchase_receipt:

                sle["creator"] = purchase_receipt.owner
                sle["supplier_code"] = purchase_receipt.supplier
                sle["supplier_name"] = purchase_receipt.supplier_name
                sle["supplier_delivery_note"] = purchase_receipt.supplier_delivery_note

            # ------------------------------------------
            # PURCHASE RECEIPT ITEM DETAILS (also covers purchase_order,
            # previously fetched again in a second, redundant query)
            # ------------------------------------------

            pr_item = extended_maps.pr_items.get((sle.voucher_no, sle.item_code))

            if pr_item:

                sle["purchase_order"] = pr_item.purchase_order
                sle["cost_center"] = pr_item.cost_center

        # IN/OUT Quantity
        sle["actual_qty"] = sle.actual_qty

        # Received Amount (only IN)
        sle["received_amount"] = abs(sle.stock_value_difference) if sle.actual_qty > 0 else 0

        # Issued Amount (only OUT)
        sle["issued_amount"] = abs(sle.stock_value_difference) if sle.actual_qty < 0 else 0

        # Project Name (from pre-fetched map, no query here)
        sle["project_name"] = extended_maps.projects.get(sle.project) if sle.project else None

        if bundle_info := bundle_details.get(sle.serial_and_batch_bundle):
            data.extend(get_segregated_bundle_entries(sle, bundle_info, batch_balance_dict, filters))
            continue

        if filters.get("batch_no") or inventory_dimension_filters_applied:
            actual_qty += flt(sle.actual_qty, precision)
            stock_value = flt(
                stock_value + sle.stock_value_difference,
                precision,
            )
            if sle.batch_no:
                if not batch_balance_dict.get(sle.batch_no):
                    batch_balance_dict[sle.batch_no] = [0, 0]

                batch_balance_dict[sle.batch_no][0] = flt(
                    batch_balance_dict[sle.batch_no][0] + sle.actual_qty,
                    precision,
                )

            if filters.get("segregate_serial_batch_bundle"):
                actual_qty = batch_balance_dict[sle.batch_no][0]

            if sle.voucher_type == "Stock Reconciliation" and not sle.actual_qty:
                actual_qty = sle.qty_after_transaction
                stock_value = sle.stock_value

            sle.update({"qty_after_transaction": actual_qty, "stock_value": stock_value})

        sle.update({"in_qty": max(sle.actual_qty, 0), "out_qty": min(sle.actual_qty, 0)})

        if sle.serial_no:
            update_available_serial_nos(available_serial_nos, sle)

        if sle.actual_qty:
            sle["in_out_rate"] = flt(sle.stock_value_difference / sle.actual_qty, precision)

        elif sle.voucher_type == "Stock Reconciliation":
            sle["in_out_rate"] = sle.valuation_rate

        data.append(sle)

        if include_uom:
            conversion_factors.append(item_detail.conversion_factor)

    update_included_uom_in_report(columns, data, include_uom, conversion_factors)
    return columns, data


def get_extended_field_maps(sl_entries):
    """
    Batch-fetch everything the row loop used to fetch one-row-at-a-time.

    Returns a frappe._dict of lookup maps:
        stock_entries      -> {voucher_no: row}
        se_details         -> {(voucher_no, item_code): row}
        purchase_receipts  -> {voucher_no: row}
        pr_items           -> {(voucher_no, item_code): row}
        suppliers          -> {supplier: supplier_name}
        projects           -> {project: project_name}
    """
    stock_entry_names = set()
    purchase_receipt_names = set()
    project_names = set()

    for sle in sl_entries:
        if sle.voucher_type == "Stock Entry":
            stock_entry_names.add(sle.voucher_no)
        elif sle.voucher_type == "Purchase Receipt":
            purchase_receipt_names.add(sle.voucher_no)
        if sle.project:
            project_names.add(sle.project)

    stock_entries = {}
    se_details = {}
    suppliers = {}

    if stock_entry_names:
        se_rows = frappe.get_all(
            "Stock Entry",
            filters={"name": ("in", list(stock_entry_names))},
            fields=[
                "name",
                "owner",
                "stock_entry_type",
                "outgoing_stock_entry",
                "custom_supplier_code_",
                "custom_suppliers_name_",
                "supplier",
            ],
        )

        supplier_codes = set()
        for row in se_rows:
            stock_entries[row.name] = row
            if row.supplier:
                supplier_codes.add(row.supplier)

        if supplier_codes:
            supplier_rows = frappe.get_all(
                "Supplier",
                filters={"name": ("in", list(supplier_codes))},
                fields=["name", "supplier_name"],
            )
            suppliers = {row.name: row.supplier_name for row in supplier_rows}

        sed_rows = frappe.get_all(
            "Stock Entry Detail",
            filters={"parent": ("in", list(stock_entry_names))},
            fields=["parent", "item_code", "material_request", "cost_center", "expense_account"],
        )
        for row in sed_rows:
            # Same (parent, item_code) can repeat across multiple detail rows in
            # rare edge cases (duplicate item rows) - last one wins, same as the
            # original single get_value() behaviour.
            se_details[(row.parent, row.item_code)] = row

    purchase_receipts = {}
    pr_items = {}

    if purchase_receipt_names:
        pr_rows = frappe.get_all(
            "Purchase Receipt",
            filters={"name": ("in", list(purchase_receipt_names))},
            fields=["name", "owner", "supplier", "supplier_name", "supplier_delivery_note"],
        )
        for row in pr_rows:
            purchase_receipts[row.name] = row

        pri_rows = frappe.get_all(
            "Purchase Receipt Item",
            filters={"parent": ("in", list(purchase_receipt_names))},
            fields=["parent", "item_code", "purchase_order", "cost_center"],
        )
        for row in pri_rows:
            pr_items[(row.parent, row.item_code)] = row

    projects = {}
    if project_names:
        proj_rows = frappe.get_all(
            "Project",
            filters={"name": ("in", list(project_names))},
            fields=["name", "project_name"],
        )
        projects = {row.name: row.project_name for row in proj_rows}

    return frappe._dict(
        {
            "stock_entries": stock_entries,
            "se_details": se_details,
            "purchase_receipts": purchase_receipts,
            "pr_items": pr_items,
            "suppliers": suppliers,
            "projects": projects,
        }
    )


def get_segregated_bundle_entries(sle, bundle_details, batch_balance_dict, filters):
    segregated_entries = []
    qty_before_transaction = sle.qty_after_transaction - sle.actual_qty
    stock_value_before_transaction = sle.stock_value - sle.stock_value_difference

    for row in bundle_details:
        new_sle = copy.deepcopy(sle)
        new_sle.update(row)
        new_sle.update(
            {
                "in_out_rate": flt(new_sle.stock_value_difference / row.qty) if row.qty else 0,
                "in_qty": row.qty if row.qty > 0 else 0,
                "out_qty": row.qty if row.qty < 0 else 0,
                "qty_after_transaction": qty_before_transaction + row.qty,
                "stock_value": stock_value_before_transaction + new_sle.stock_value_difference,
                "incoming_rate": row.incoming_rate if row.qty > 0 else 0,
            }
        )

        if filters.get("batch_no") and row.batch_no:
            if not batch_balance_dict.get(row.batch_no):
                batch_balance_dict[row.batch_no] = [0, 0]

            batch_balance_dict[row.batch_no][0] += row.qty
            batch_balance_dict[row.batch_no][1] += row.stock_value_difference

            new_sle.update(
                {
                    "qty_after_transaction": batch_balance_dict[row.batch_no][0],
                    "stock_value": batch_balance_dict[row.batch_no][1],
                }
            )

        qty_before_transaction += row.qty
        stock_value_before_transaction += new_sle.stock_value_difference

        new_sle.valuation_rate = (
            stock_value_before_transaction / qty_before_transaction if qty_before_transaction else 0
        )

        segregated_entries.append(new_sle)

    return segregated_entries


def get_serial_batch_bundle_details(sl_entries, filters=None):
    bundle_details = []
    for sle in sl_entries:
        if sle.serial_and_batch_bundle:
            bundle_details.append(sle.serial_and_batch_bundle)

    if not bundle_details:
        return frappe._dict({})

    query_filers = {"parent": ("in", bundle_details)}
    if filters.get("batch_no"):
        query_filers["batch_no"] = filters.batch_no

    _bundle_details = frappe._dict({})
    batch_entries = frappe.get_all(
        "Serial and Batch Entry",
        filters=query_filers,
        fields=["parent", "qty", "incoming_rate", "stock_value_difference", "batch_no", "serial_no"],
        order_by="parent, idx",
    )
    for entry in batch_entries:
        _bundle_details.setdefault(entry.parent, []).append(entry)

    return _bundle_details


def update_available_serial_nos(available_serial_nos, sle):
    serial_nos = get_serial_nos(sle.serial_no)
    key = (sle.item_code, sle.warehouse)
    if key not in available_serial_nos:
        stock_balance = get_stock_balance_for(
            sle.item_code, sle.warehouse, sle.posting_date, sle.posting_time
        )
        serials = get_serial_nos(stock_balance["serial_nos"]) if stock_balance["serial_nos"] else []
        available_serial_nos.setdefault(key, serials)

    existing_serial_no = available_serial_nos[key]
    for sn in serial_nos:
        if sle.actual_qty > 0:
            if sn in existing_serial_no:
                existing_serial_no.remove(sn)
            else:
                existing_serial_no.append(sn)
        else:
            if sn in existing_serial_no:
                existing_serial_no.remove(sn)
            else:
                existing_serial_no.append(sn)

    sle.balance_serial_no = "\n".join(existing_serial_no)


def get_columns(filters):
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 150},
        {
            "label": _("Item"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 100,
        },
        {"label": _("Item Name"), "fieldname": "item_name", "width": 100},

        {
            "label": _("Expense Account"),
            "fieldname": "expense_account",
            "fieldtype": "Link",
            "options": "Account",
            "width": 150,
        },
        
        {
            "label": _("Stock UOM"),
            "fieldname": "stock_uom",
            "fieldtype": "Link",
            "options": "UOM",
            "width": 90,
        },
    ]

    for dimension in get_inventory_dimensions():
        columns.append(
            {
                "label": _(dimension.doctype),
                "fieldname": dimension.fieldname,
                "fieldtype": "Link",
                "options": dimension.doctype,
                "width": 110,
            }
        )

    columns.extend(
        [
            {
                "label": _("In Qty"),
                "fieldname": "in_qty",
                "fieldtype": "Float",
                "width": 80,
                "convertible": "qty",
            },
            {
                "label": _("Out Qty"),
                "fieldname": "out_qty",
                "fieldtype": "Float",
                "width": 80,
                "convertible": "qty",
            },
            {
                "label": _("Balance Qty"),
                "fieldname": "qty_after_transaction",
                "fieldtype": "Float",
                "width": 100,
                "convertible": "qty",
            },
            {
                "label": _("Warehouse"),
                "fieldname": "warehouse",
                "fieldtype": "Link",
                "options": "Warehouse",
                "width": 150,
            },
            {
                "label": _("Item Group"),
                "fieldname": "item_group",
                "fieldtype": "Link",
                "options": "Item Group",
                "width": 100,
            },
            {
                "label": _("Brand"),
                "fieldname": "brand",
                "fieldtype": "Link",
                "options": "Brand",
                "width": 100,
            },
            {"label": _("Description"), "fieldname": "description", "width": 200},
            {
                "label": _("Incoming Rate"),
                "fieldname": "incoming_rate",
                "fieldtype": "Currency",
                "width": 110,
                "options": "Company:company:default_currency",
                "convertible": "rate",
            },
            {
                "label": _("Avg Rate (Balance Stock)"),
                "fieldname": "valuation_rate",
                "fieldtype": filters.valuation_field_type,
                "width": 180,
                "options": "Company:company:default_currency"
                if filters.valuation_field_type == "Currency"
                else None,
                "convertible": "rate",
            },
            {
                "label": _("Valuation Rate"),
                "fieldname": "in_out_rate",
                "fieldtype": filters.valuation_field_type,
                "width": 140,
                "options": "Company:company:default_currency"
                if filters.valuation_field_type == "Currency"
                else None,
                "convertible": "rate",
            },
            {
                "label": _("Balance Value"),
                "fieldname": "stock_value",
                "fieldtype": "Currency",
                "width": 110,
                "options": "Company:company:default_currency",
            },
            {
                "label": _("Value Change"),
                "fieldname": "stock_value_difference",
                "fieldtype": "Currency",
                "width": 110,
                "options": "Company:company:default_currency",
            },
            {"label": _("Voucher Type"), "fieldname": "voucher_type", "width": 110},
            {
                "label": _("Voucher #"),
                "fieldname": "voucher_no",
                "fieldtype": "Dynamic Link",
                "options": "voucher_type",
                "width": 100,
            },
            {
                "label": _("Stock Entry Type"),
                "fieldname": "stock_entry_type",
                "fieldtype": "Data",
                "width": 120,
            },

            {
                "label": _("Supplier Code"),
                "fieldname": "supplier_code",
                "fieldtype": "Link",
                "options": "Supplier",
                "width": 140,
            },

            {
                "label": _("Supplier Name"),
                "fieldname": "supplier_name",
                "fieldtype": "Data",
                "width": 200,
            },

            {
                "label": _("Received Amount"),
                "fieldname": "received_amount",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 120,
            },


            {
                "label": _("Issued Amount"),
                "fieldname": "issued_amount",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 120,
            },

            {
                "label": _("Batch"),
                "fieldname": "batch_no",
                "fieldtype": "Link",
                "options": "Batch",
                "width": 100,
            },
            {
                "label": _("Serial No"),
                "fieldname": "serial_no",
                "fieldtype": "Link",
                "options": "Serial No",
                "width": 100,
            },
            {
                "label": _("Serial and Batch Bundle"),
                "fieldname": "serial_and_batch_bundle",
                "fieldtype": "Link",
                "options": "Serial and Batch Bundle",
                "width": 100,
            },
            {
                "label": _("Project"),
                "fieldname": "project",
                "fieldtype": "Link",
                "options": "Project",
                "width": 100,
            },
            {
                "label": _("Project Name"),
                "fieldname": "project_name",
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "label": _("Company"),
                "fieldname": "company",
                "fieldtype": "Link",
                "options": "Company",
                "width": 110,
            },

            {
                "label": _("Creator"),
                "fieldname": "creator",
                "fieldtype": "Data",
                "width": 200,
            },

            {
                "label": _("Material Request"),
                "fieldname": "material_request",
                "fieldtype": "Link",
                "options": "Material Request",
                "width": 200,
            },

            {
                "label": _("Cost Center"),
                "fieldname": "cost_center",
                "fieldtype": "Link",
                "options": "Cost Center",
                "width": 150,
            },

            {
                "label": _("Is Petty Cash"),
                "fieldname": "is_petty_cash",
                "fieldtype": "Check",
                "width": 100,
            },

            
            {
                "label": _("Supplier Delivery Note"),
                "fieldname": "supplier_delivery_note",
                "fieldtype": "Data",
                "width": 180,
            },

            {
                "label": _("Return Material Ref Doc"),
                "fieldname": "return_material_ref_doc",
                "fieldtype": "Data",
                "width": 180,
            },

            {
                "label": _("Purchase Order"),
                "fieldname": "purchase_order",
                "fieldtype": "Link",
                "options": "Purchase Order",
                "width": 200,
            },
        ]
    )

    return columns


def get_stock_ledger_entries(filters, items):
	from_date = get_datetime(filters.from_date + " 00:00:00")
	to_date = get_datetime(filters.to_date + " 23:59:59")

	sle = frappe.qb.DocType("Stock Ledger Entry")
	query = (
		frappe.qb.from_(sle)
		.select(
            sle.item_code,

            DateFormat(sle.posting_datetime, "%Y-%m-%d").as_("date"),
            sle.warehouse,
            sle.posting_date,
            sle.posting_time,
            sle.actual_qty,
            sle.incoming_rate,
            sle.valuation_rate,
            sle.company,
            sle.voucher_type,
            sle.qty_after_transaction,
            sle.stock_value_difference,
            sle.serial_and_batch_bundle,
            sle.voucher_no,
            sle.stock_value,
            sle.batch_no,
            sle.serial_no,
            sle.creation,
            sle.project,
        )
		.where(
			(sle.docstatus < 2)
			& (sle.is_cancelled == 0)
			& (sle.posting_datetime[from_date:to_date])
		)
		.orderby(sle.posting_datetime)
		.orderby(sle.creation)
	)

	inventory_dimension_fields = get_inventory_dimension_fields()
	if inventory_dimension_fields:
		for fieldname in inventory_dimension_fields:
			query = query.select(fieldname)
			if fieldname in filters and filters.get(fieldname):
				query = query.where(sle[fieldname].isin(filters.get(fieldname)))

	if items:
		query = query.where(sle.item_code.isin(items))

	for field in ["voucher_no", "project", "company"]:
		if filters.get(field) and field not in inventory_dimension_fields:
			query = query.where(sle[field] == filters.get(field))

	if filters.get("batch_no"):
		bundles = get_serial_and_batch_bundles(filters)

		if bundles:
			query = query.where(
				(sle.serial_and_batch_bundle.isin(bundles))
				| (sle.batch_no == filters.batch_no)
			)
		else:
			query = query.where(sle.batch_no == filters.batch_no)

	query = apply_warehouse_filter(query, sle, filters)

	return query.run(as_dict=True)



def get_serial_and_batch_bundles(filters):
    SBB = frappe.qb.DocType("Serial and Batch Bundle")
    SBE = frappe.qb.DocType("Serial and Batch Entry")

    query = (
        frappe.qb.from_(SBE)
        .inner_join(SBB)
        .on(SBE.parent == SBB.name)
        .select(SBE.parent)
        .where(
            (SBB.docstatus == 1)
            & (SBB.has_batch_no == 1)
            & (SBB.voucher_no.notnull())
            & (SBE.batch_no == filters.batch_no)
        )
    )

    return query.run(pluck=SBE.parent)


def get_inventory_dimension_fields():
    return [dimension.fieldname for dimension in get_inventory_dimensions()]


def get_items(filters):
    item = frappe.qb.DocType("Item")
    query = frappe.qb.from_(item).select(item.name)

    conditions = []

    # ✅ Active Items filter
    if filters.get("active_items"):
        conditions.append(item.disabled == 0)

    if item_codes := filters.get("item_code"):
        conditions.append(item.name.isin(item_codes))
    else:
        if brand := filters.get("brand"):
            conditions.append(item.brand == brand)

        if filters.get("item_group") and (
            condition := get_item_group_condition(filters.get("item_group"), item)
        ):
            conditions.append(condition)

    if conditions:
        for condition in conditions:
            query = query.where(condition)

        return [r[0] for r in query.run()]

    return []



def get_item_details(items, sl_entries, include_uom):
    item_details = {}
    if not items:
        items = list(set(d.item_code for d in sl_entries))

    if not items:
        return item_details

    item = frappe.qb.DocType("Item")
    query = (
        frappe.qb.from_(item)
        .select(item.name, item.item_name, item.description, item.item_group, item.brand, item.stock_uom)
        .where(item.name.isin(items))
    )

    if include_uom:
        ucd = frappe.qb.DocType("UOM Conversion Detail")
        query = (
            query.left_join(ucd)
            .on((ucd.parent == item.name) & (ucd.uom == include_uom))
            .select(ucd.conversion_factor)
        )

    res = query.run(as_dict=True)

    for item in res:
        item_details.setdefault(item.name, item)

    return item_details


# TODO: THIS IS NOT USED
def get_sle_conditions(filters):
    conditions = []
    if filters.get("warehouse"):
        warehouse_condition = get_warehouse_condition(filters.get("warehouse"))
        if warehouse_condition:
            conditions.append(warehouse_condition)
    if filters.get("voucher_no"):
        conditions.append("voucher_no=%(voucher_no)s")
    if filters.get("batch_no"):
        conditions.append("batch_no=%(batch_no)s")
    if filters.get("project"):
        conditions.append("project=%(project)s")

    for dimension in get_inventory_dimensions():
        if filters.get(dimension.fieldname):
            conditions.append(f"{dimension.fieldname} in %({dimension.fieldname})s")

    return "and {}".format(" and ".join(conditions)) if conditions else ""


def get_opening_balance_from_batch(filters, columns, sl_entries):
    query_filters = {
        "batch_no": filters.batch_no,
        "docstatus": 1,
        "is_cancelled": 0,
        "posting_date": ("<", filters.from_date),
        "company": filters.company,
    }

    for fields in ["item_code", "warehouse"]:
        if value := filters.get(fields):
            query_filters[fields] = ("in", value)

    opening_data = frappe.get_all(
        "Stock Ledger Entry",
        fields=["sum(actual_qty) as qty_after_transaction", "sum(stock_value_difference) as stock_value"],
        filters=query_filters,
    )[0]

    for field in ["qty_after_transaction", "stock_value", "valuation_rate"]:
        if opening_data.get(field) is None:
            opening_data[field] = 0.0

    table = frappe.qb.DocType("Stock Ledger Entry")
    sabb_table = frappe.qb.DocType("Serial and Batch Entry")
    query = (
        frappe.qb.from_(table)
        .inner_join(sabb_table)
        .on(table.serial_and_batch_bundle == sabb_table.parent)
        .select(
            Sum(sabb_table.qty).as_("qty"),
            Sum(sabb_table.stock_value_difference).as_("stock_value"),
        )
        .where(
            (sabb_table.batch_no == filters.batch_no)
            & (sabb_table.docstatus == 1)
            & (table.posting_date < filters.from_date)
            & (table.is_cancelled == 0)
        )
    )

    for field in ["item_code", "warehouse", "company"]:
        value = filters.get(field)

        if not value:
            continue

        if isinstance(value, list | tuple):
            query = query.where(table[field].isin(value))

        else:
            query = query.where(table[field] == value)

    bundle_data = query.run(as_dict=True)

    if bundle_data:
        opening_data.qty_after_transaction += flt(bundle_data[0].qty)
        opening_data.stock_value += flt(bundle_data[0].stock_value)
        if opening_data.qty_after_transaction:
            opening_data.valuation_rate = flt(opening_data.stock_value) / flt(
                opening_data.qty_after_transaction
            )

    return {
        "item_code": _("'Opening'"),
        "qty_after_transaction": opening_data.qty_after_transaction,
        "valuation_rate": opening_data.valuation_rate,
        "stock_value": opening_data.stock_value,
    }


def get_opening_balance(filters, columns, sl_entries):
    if not (filters.item_code and filters.warehouse and filters.from_date):
        return

    # filters.item_code can be a single string or a list (multi-select Item
    # filter). Normalise to a list so we can always drive the query off a
    # single IN clause below, instead of the previous get_previous_sle()
    # helper, which only accepts one scalar item_code and raises
    # "Operand should contain 1 column(s)" the moment more than one item is
    # selected.
    item_codes = filters.item_code
    if isinstance(item_codes, str):
        item_codes = [item_codes]

    from_datetime = get_datetime(filters.from_date + " 00:00:00")

    sle = frappe.qb.DocType("Stock Ledger Entry")
    query = (
        frappe.qb.from_(sle)
        .select(
            Sum(sle.actual_qty).as_("qty_after_transaction"),
            Sum(sle.stock_value_difference).as_("stock_value"),
        )
        .where(
            (sle.item_code.isin(item_codes))
            & (sle.docstatus < 2)
            & (sle.is_cancelled == 0)
            & (sle.posting_datetime < from_datetime)
        )
    )

    # Same tree-aware (lft/rgt) warehouse filter used for the main ledger
    # query, so parent-warehouse selections and multi-warehouse filters are
    # handled consistently, and it works whether filters.warehouse is a
    # single warehouse or a list.
    query = apply_warehouse_filter(query, sle, filters)

    if filters.get("company"):
        query = query.where(sle.company == filters.company)

    opening_data = query.run(as_dict=True)[0]

    for field in ["qty_after_transaction", "stock_value"]:
        if opening_data.get(field) is None:
            opening_data[field] = 0.0

    valuation_rate = (
        flt(opening_data.qty_after_transaction)
        and flt(opening_data.stock_value) / flt(opening_data.qty_after_transaction)
        or 0
    )

    # check if any SLEs are actually Opening Stock Reconciliation.
    # This exact-row override only makes sense when a single item is being
    # reported on (an Opening Stock Reconciliation row belongs to one
    # item+warehouse); with multiple items selected the summed balance above
    # already covers all of them correctly via the IN clause.
    if len(item_codes) == 1:
        for row in list(sl_entries):
            if (
                row.get("voucher_type") == "Stock Reconciliation"
                and row.posting_date == filters.from_date
                and frappe.db.get_value("Stock Reconciliation", row.voucher_no, "purpose") == "Opening Stock"
            ):
                opening_data.qty_after_transaction = row.get("qty_after_transaction", 0)
                opening_data.stock_value = row.get("stock_value", 0)
                valuation_rate = row.get("valuation_rate", 0)
                sl_entries.remove(row)

    row = {
        "item_code": _("'Opening'"),
        "qty_after_transaction": opening_data.qty_after_transaction,
        "valuation_rate": valuation_rate,
        "stock_value": opening_data.stock_value,
    }

    return row


def get_warehouse_condition(warehouses):
    if not warehouses:
        return ""

    if isinstance(warehouses, str):
        warehouses = [warehouses]

    warehouse_range = frappe.get_all(
        "Warehouse",
        filters={
            "name": ("in", warehouses),
        },
        fields=["lft", "rgt"],
        as_list=True,
    )

    if not warehouse_range:
        return ""

    alias = "wh"
    conditions = []
    for lft, rgt in warehouse_range:
        conditions.append(f"({alias}.lft >= {lft} and {alias}.rgt <= {rgt})")

    conditions = " or ".join(conditions)

    return f" exists (select name from `tabWarehouse` {alias} \
        where ({conditions}) and warehouse = {alias}.name)"


def get_item_group_condition(item_group, item_table=None):
    item_group_details = frappe.db.get_value("Item Group", item_group, ["lft", "rgt"], as_dict=1)
    if item_group_details:
        if item_table:
            ig = frappe.qb.DocType("Item Group")
            return item_table.item_group.isin(
                frappe.qb.from_(ig)
                .select(ig.name)
                .where(
                    (ig.lft >= item_group_details.lft)
                    & (ig.rgt <= item_group_details.rgt)
                    & (item_table.item_group == ig.name)
                )
            )
        else:
            return f"item.item_group in (select ig.name from `tabItem Group` ig \
                where ig.lft >= {item_group_details.lft} and ig.rgt <= {item_group_details.rgt} and item.item_group = ig.name)"


def check_inventory_dimension_filters_applied(filters) -> bool:
    for dimension in get_inventory_dimensions():
        if dimension.fieldname in filters and filters.get(dimension.fieldname):
            return True

    return False