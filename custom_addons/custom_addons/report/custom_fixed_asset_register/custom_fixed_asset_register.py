# Copyright (c) 2026, FinByz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from itertools import chain

import frappe
from frappe import _
from frappe.query_builder.functions import Count, IfNull, Sum
from frappe.utils import add_months, cstr, flt, formatdate, getdate, nowdate, today

from erpnext.accounts.report.financial_statements import (
	get_fiscal_year_data,
	get_period_list,
	validate_fiscal_year,
)
from erpnext.accounts.utils import get_fiscal_year

# Custom fieldnames we couldn't confirm against the live schema — checked at
# runtime via frappe.db.has_column so the report degrades gracefully instead
# of crashing if these don't exist. Update these lists if the real fieldnames
# are different.
ASSET_CLASS_FIELD_CANDIDATES = ["custom_asset_class", "asset_class"]
PROJECT_FIELD_CANDIDATES = ["project", "custom_project"]


def _first_existing_field(doctype, candidates):
	for f in candidates:
		if frappe.db.has_column(doctype, f):
			return f
	return None


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns(filters)
	data = get_data(filters)
	chart = (
		prepare_chart_data(data, filters)
		if filters.get("group_by") not in ("Asset Category", "Location")
		else {}
	)

	return columns, data, None, chart


def get_data(filters):
	data = []

	conditions = get_conditions(filters)
	pr_supplier_map = get_purchase_receipt_supplier_map()
	pi_supplier_map = get_purchase_invoice_supplier_map()

	assets_linked_to_fb = get_assets_linked_to_fb(filters)

	company_fb = frappe.get_cached_value("Company", filters.company, "default_finance_book")

	if filters.include_default_book_assets and company_fb:
		finance_book = company_fb
	elif filters.finance_book:
		finance_book = filters.finance_book
	else:
		finance_book = None

	depreciation_amount_map = get_asset_depreciation_amount_map(filters, finance_book)
	revaluation_amount_map = get_asset_value_adjustment_map(filters, finance_book)
	gross_cost_movement_map = get_asset_gross_cost_movement_map(filters, finance_book)

	group_by = frappe.scrub(filters.get("group_by"))

	if group_by in ("asset_category", "location"):
		data = get_group_by_data(
			group_by, conditions, assets_linked_to_fb, depreciation_amount_map, revaluation_amount_map
		)
		return data

	asset_class_field = _first_existing_field("Asset", ASSET_CLASS_FIELD_CANDIDATES)
	project_field = _first_existing_field("Asset", PROJECT_FIELD_CANDIDATES)

	fields = [
		"name as asset_id",
		"asset_name",
		"status",
		"department",
		"company",
		"cost_center",
		"calculate_depreciation",
		"purchase_receipt",
		"asset_category",
		"purchase_date",
		"gross_purchase_amount",
		"location",
		"available_for_use_date",
		"purchase_invoice",
		"opening_accumulated_depreciation",
		"item_code",
	]
	if asset_class_field:
		fields.append(asset_class_field)
	if project_field:
		fields.append(project_field)

	assets_record = frappe.db.get_all("Asset", filters=conditions, fields=fields)
	asset_ids = [a.asset_id for a in assets_record]
	item_codes = list({a.item_code for a in assets_record if a.item_code})

	item_description_map = get_item_description_map(item_codes)
	asset_category_accounts_map = get_asset_category_accounts_map(filters.company)
	account_name_map = get_account_name_map(
		[v.fixed_asset_account for v in asset_category_accounts_map.values()]
		+ [v.depreciation_expense_account for v in asset_category_accounts_map.values()]
		+ [v.accumulated_depreciation_account for v in asset_category_accounts_map.values()]
	)
	finance_book_map = get_asset_finance_book_map(asset_ids, finance_book)

	as_of_date = filters.to_date if filters.filter_based_on == "Date Range" else (
		filters.year_end_date if filters.filter_based_on == "Fiscal Year" else nowdate()
	)
	booked_depreciation_count_map = get_booked_depreciation_count_map(asset_ids, finance_book, as_of_date)

	for asset in assets_record:
		if assets_linked_to_fb and asset.calculate_depreciation and asset.asset_id not in assets_linked_to_fb:
			continue

		depreciation_amount = depreciation_amount_map.get(asset.asset_id) or 0.0
		revaluation_amount = revaluation_amount_map.get(asset.asset_id, 0.0)
		asset_value = (
			asset.gross_purchase_amount
			- asset.opening_accumulated_depreciation
			- depreciation_amount
			+ revaluation_amount
		)

		movement = gross_cost_movement_map.get(asset.asset_id, {})
		additions = flt(movement.get("additions"))
		disposals = flt(movement.get("disposals"))
		closing_gross_cost = asset.gross_purchase_amount
		opening_gross_cost = closing_gross_cost - additions + disposals
		closing_accumulated_depreciation = asset.opening_accumulated_depreciation + depreciation_amount

		cat_accounts = asset_category_accounts_map.get(asset.asset_category) or frappe._dict()
		bs_account = cat_accounts.get("fixed_asset_account")

		afb = finance_book_map.get(asset.asset_id) or frappe._dict()
		freq = flt(afb.get("frequency_of_depreciation"))
		total_dep = flt(afb.get("total_number_of_depreciations"))
		useful_life_months = freq * total_dep if (freq and total_dep) else None
		booked_count = booked_depreciation_count_map.get(asset.asset_id, 0)
		remaining_life_months = (
			max(useful_life_months - (booked_count * freq), 0) if useful_life_months and freq else None
		)

		if asset_class_field:
			asset_class_value = asset.get(asset_class_field)
		else:
			# No dedicated Asset Class field found — falling back to Asset
			# Category. Tell me the real fieldname if you have one and
			# I'll wire it in directly.
			asset_class_value = asset.asset_category

		project_value = asset.get(project_field) if project_field else None

		row = {
			"bs_account": bs_account,
			"account_name": account_name_map.get(bs_account),
			"depreciation_expense_account": cat_accounts.get("depreciation_expense_account"),
			"accumulated_depreciation_account": cat_accounts.get("accumulated_depreciation_account"),
			"asset_class": asset_class_value,
			"asset_category": asset.asset_category,
			"asset_id": asset.asset_id,
			"asset_code": asset.item_code,
			"asset_description": item_description_map.get(asset.item_code) or asset.asset_name,
			"purchase_date": asset.purchase_date,
			"available_for_use_date": asset.available_for_use_date,
			"useful_life_months": useful_life_months,
			"remaining_life_months": remaining_life_months,
			"depreciation_method": afb.get("depreciation_method"),
			"purchase_receipt": asset.purchase_receipt,
			"project": project_value,
			"department": asset.department,
			"vendor_name": pr_supplier_map.get(asset.purchase_receipt)
			or pi_supplier_map.get(asset.purchase_invoice),
			"location": asset.location,
			"status": asset.status,
			"opening_gross_cost": opening_gross_cost,
			"additions": additions,
			"disposals": disposals,
			"closing_gross_cost": closing_gross_cost,
			"opening_accumulated_depreciation": asset.opening_accumulated_depreciation,
			"depreciated_amount": depreciation_amount,
			"closing_accumulated_depreciation": closing_accumulated_depreciation,
			"asset_value": asset_value,
			"cost_center": asset.cost_center,
			"company": asset.company,
		}
		data.append(row)

	return data


def get_item_description_map(item_codes):
	if not item_codes:
		return {}
	rows = frappe.get_all("Item", filters={"name": ["in", item_codes]}, fields=["name", "description"])
	return {r.name: r.description for r in rows}


def get_asset_category_accounts_map(company):
	aca = frappe.qb.DocType("Asset Category Account")
	rows = (
		frappe.qb.from_(aca)
		.select(
			aca.parent,
			aca.fixed_asset_account,
			aca.depreciation_expense_account,
			aca.accumulated_depreciation_account,
		)
		.where(aca.company_name == company)
		.run(as_dict=True)
	)
	return {r.parent: r for r in rows}


def get_account_name_map(account_names):
	account_names = list({a for a in account_names if a})
	if not account_names:
		return {}
	rows = frappe.get_all("Account", filters={"name": ["in", account_names]}, fields=["name", "account_name"])
	return {r.name: r.account_name for r in rows}


def get_asset_finance_book_map(asset_names, finance_book):
	if not asset_names:
		return {}
	afb = frappe.qb.DocType("Asset Finance Book")
	rows = (
		frappe.qb.from_(afb)
		.select(
			afb.parent,
			afb.finance_book,
			afb.depreciation_method,
			afb.total_number_of_depreciations,
			afb.frequency_of_depreciation,
			afb.idx,
		)
		.where(afb.parent.isin(asset_names))
		.run(as_dict=True)
	)

	result = {}
	for r in rows:
		if finance_book:
			if cstr(r.finance_book) != cstr(finance_book):
				continue
		else:
			if r.idx != 1:
				continue
		result[r.parent] = r
	return result


def get_booked_depreciation_count_map(asset_names, finance_book, as_of_date=None):
	if not asset_names:
		return {}
	ds = frappe.qb.DocType("Depreciation Schedule")
	query = (
		frappe.qb.from_(ds)
		.select(ds.parent, Count(ds.name).as_("booked_count"))
		.where(ds.parent.isin(asset_names))
		.where(ds.journal_entry.isnotnull())
		.where(ds.journal_entry != "")
	)
	if finance_book:
		query = query.where(ds.finance_book == finance_book)
	if as_of_date:
		query = query.where(ds.schedule_date <= as_of_date)
	query = query.groupby(ds.parent)
	rows = query.run(as_dict=True)
	return {r.parent: r.booked_count for r in rows}


def get_asset_gross_cost_movement_map(filters, finance_book):
	start_date = filters.from_date if filters.filter_based_on == "Date Range" else filters.year_start_date
	end_date = filters.to_date if filters.filter_based_on == "Date Range" else filters.year_end_date

	asset = frappe.qb.DocType("Asset")
	gle = frappe.qb.DocType("GL Entry")
	aca = frappe.qb.DocType("Asset Category Account")
	company = frappe.qb.DocType("Company")

	query = (
		frappe.qb.from_(gle)
		.join(asset)
		.on(gle.against_voucher == asset.name)
		.join(aca)
		.on((aca.parent == asset.asset_category) & (aca.company_name == asset.company))
		.join(company)
		.on(company.name == asset.company)
		.select(
			asset.name.as_("asset"),
			Sum(gle.debit).as_("additions"),
			Sum(gle.credit).as_("disposals"),
		)
		.where(gle.account == aca.fixed_asset_account)
		.where(gle.is_cancelled == 0)
		.where(gle.is_opening == "No")
		.where(company.name == filters.company)
		.where(asset.docstatus == 1)
	)

	if filters.only_existing_assets:
		query = query.where(asset.is_existing_asset == 1)
	if filters.asset_category:
		query = query.where(asset.asset_category == filters.asset_category)
	if filters.cost_center:
		query = query.where(asset.cost_center == filters.cost_center)
	if filters.status:
		if filters.status == "In Location":
			query = query.where(asset.status.notin(["Sold", "Scrapped", "Capitalized"]))
		else:
			query = query.where(asset.status.isin(["Sold", "Scrapped", "Capitalized"]))
	if finance_book:
		query = query.where((gle.finance_book.isin([cstr(finance_book), ""])) | (gle.finance_book.isnull()))
	else:
		query = query.where((gle.finance_book.isin([""])) | (gle.finance_book.isnull()))
	if filters.filter_based_on in ("Date Range", "Fiscal Year"):
		query = query.where(gle.posting_date >= start_date)
		query = query.where(gle.posting_date <= end_date)

	query = query.groupby(asset.name)

	rows = query.run(as_dict=True)
	return {r.asset: {"additions": flt(r.additions), "disposals": flt(r.disposals)} for r in rows}


def get_conditions(filters):
	conditions = {"docstatus": 1}
	status = filters.status
	date_field = frappe.scrub(filters.date_based_on or "Purchase Date")

	if filters.get("company"):
		conditions["company"] = filters.company

	if filters.filter_based_on == "Date Range":
		if not filters.from_date and not filters.to_date:
			filters.from_date = add_months(nowdate(), -12)
			filters.to_date = nowdate()

		conditions[date_field] = ["between", [filters.from_date, filters.to_date]]
	elif filters.filter_based_on == "Fiscal Year":
		if not filters.from_fiscal_year and not filters.to_fiscal_year:
			default_fiscal_year = get_fiscal_year(today())[0]
			filters.from_fiscal_year = default_fiscal_year
			filters.to_fiscal_year = default_fiscal_year

		fiscal_year = get_fiscal_year_data(filters.from_fiscal_year, filters.to_fiscal_year)
		validate_fiscal_year(fiscal_year, filters.from_fiscal_year, filters.to_fiscal_year)
		filters.year_start_date = getdate(fiscal_year.year_start_date)
		filters.year_end_date = getdate(fiscal_year.year_end_date)

		conditions[date_field] = ["between", [filters.year_start_date, filters.year_end_date]]

	if filters.get("only_existing_assets"):
		conditions["is_existing_asset"] = filters.get("only_existing_assets")
	if filters.get("asset_category"):
		conditions["asset_category"] = filters.get("asset_category")
	if filters.get("cost_center"):
		conditions["cost_center"] = filters.get("cost_center")

	if status:
		operand = "not in"
		if status not in "In Location":
			operand = "in"
		conditions["status"] = (operand, ["Sold", "Scrapped", "Capitalized"])

	return conditions


def prepare_chart_data(data, filters):
	if not data:
		return
	labels_values_map = {}
	if filters.filter_based_on not in ("Date Range", "Fiscal Year"):
		filters_filter_based_on = "Date Range"
		date_field = "purchase_date"
		filtered_data = [d for d in data if d.get(date_field)]
		filters_from_date = min(filtered_data, key=lambda a: a.get(date_field)).get(date_field)
		filters_to_date = max(filtered_data, key=lambda a: a.get(date_field)).get(date_field)
	else:
		filters_filter_based_on = filters.filter_based_on
		date_field = frappe.scrub(filters.date_based_on)
		filters_from_date = filters.from_date
		filters_to_date = filters.to_date

	period_list = get_period_list(
		filters.from_fiscal_year,
		filters.to_fiscal_year,
		filters_from_date,
		filters_to_date,
		filters_filter_based_on,
		"Monthly",
		company=filters.company,
		ignore_fiscal_year=True,
	)

	for d in period_list:
		labels_values_map.setdefault(
			d.get("label"), frappe._dict({"asset_value": 0, "depreciated_amount": 0})
		)

	for d in data:
		if d.get(date_field):
			date = d.get(date_field)
			belongs_to_month = formatdate(date, "MMM YYYY")
			labels_values_map[belongs_to_month].asset_value += d.get("asset_value")
			labels_values_map[belongs_to_month].depreciated_amount += d.get("depreciated_amount")

	return {
		"data": {
			"labels": labels_values_map.keys(),
			"datasets": [
				{"name": _("Asset Value"), "values": [flt(d.get("asset_value"), 2) for d in labels_values_map.values()]},
				{"name": _("Depreciatied Amount"), "values": [flt(d.get("depreciated_amount"), 2) for d in labels_values_map.values()]},
			],
		},
		"type": "bar",
		"barOptions": {"stacked": 1},
	}


def get_assets_linked_to_fb(filters):
	afb = frappe.qb.DocType("Asset Finance Book")
	query = frappe.qb.from_(afb).select(afb.parent)

	if filters.include_default_book_assets:
		company_fb = frappe.get_cached_value("Company", filters.company, "default_finance_book")
		if filters.finance_book and company_fb and cstr(filters.finance_book) != cstr(company_fb):
			frappe.throw(_("To use a different finance book, please uncheck 'Include Default FB Assets'"))
		query = query.where(
			(afb.finance_book.isin([cstr(filters.finance_book), cstr(company_fb), ""]))
			| (afb.finance_book.isnull())
		)
	else:
		query = query.where(
			(afb.finance_book.isin([cstr(filters.finance_book), ""])) | (afb.finance_book.isnull())
		)

	return list(chain(*query.run(as_list=1)))


def get_asset_depreciation_amount_map(filters, finance_book):
	start_date = filters.from_date if filters.filter_based_on == "Date Range" else filters.year_start_date
	end_date = filters.to_date if filters.filter_based_on == "Date Range" else filters.year_end_date

	asset = frappe.qb.DocType("Asset")
	gle = frappe.qb.DocType("GL Entry")
	aca = frappe.qb.DocType("Asset Category Account")
	company = frappe.qb.DocType("Company")

	query = (
		frappe.qb.from_(gle)
		.join(asset)
		.on(gle.against_voucher == asset.name)
		.join(aca)
		.on((aca.parent == asset.asset_category) & (aca.company_name == asset.company))
		.join(company)
		.on(company.name == asset.company)
		.select(asset.name.as_("asset"), Sum(gle.debit).as_("depreciation_amount"))
		.where(gle.account == IfNull(aca.depreciation_expense_account, company.depreciation_expense_account))
		.where(gle.debit != 0)
		.where(gle.is_cancelled == 0)
		.where(gle.is_opening == "No")
		.where(company.name == filters.company)
		.where(asset.docstatus == 1)
	)

	if filters.only_existing_assets:
		query = query.where(asset.is_existing_asset == 1)
	if filters.asset_category:
		query = query.where(asset.asset_category == filters.asset_category)
	if filters.cost_center:
		query = query.where(asset.cost_center == filters.cost_center)
	if filters.status:
		if filters.status == "In Location":
			query = query.where(asset.status.notin(["Sold", "Scrapped", "Capitalized"]))
		else:
			query = query.where(asset.status.isin(["Sold", "Scrapped", "Capitalized"]))
	if finance_book:
		query = query.where((gle.finance_book.isin([cstr(finance_book), ""])) | (gle.finance_book.isnull()))
	else:
		query = query.where((gle.finance_book.isin([""])) | (gle.finance_book.isnull()))
	if filters.filter_based_on in ("Date Range", "Fiscal Year"):
		query = query.where(gle.posting_date >= start_date)
		query = query.where(gle.posting_date <= end_date)

	query = query.groupby(asset.name)
	return dict(query.run())


def get_asset_value_adjustment_map(filters, finance_book):
	start_date = filters.from_date if filters.filter_based_on == "Date Range" else filters.year_start_date
	end_date = filters.to_date if filters.filter_based_on == "Date Range" else filters.year_end_date

	asset = frappe.qb.DocType("Asset")
	gle = frappe.qb.DocType("GL Entry")
	aca = frappe.qb.DocType("Asset Category Account")
	company = frappe.qb.DocType("Company")

	query = (
		frappe.qb.from_(gle)
		.join(asset)
		.on(gle.against_voucher == asset.name)
		.join(aca)
		.on((aca.parent == asset.asset_category) & (aca.company_name == asset.company))
		.join(company)
		.on(company.name == asset.company)
		.select(asset.name.as_("asset"), Sum(gle.debit - gle.credit).as_("adjustment_amount"))
		.where(gle.account == aca.fixed_asset_account)
		.where(gle.is_cancelled == 0)
		.where(gle.is_opening == "No")
		.where(company.name == filters.company)
		.where(asset.docstatus == 1)
	)

	if filters.only_existing_assets:
		query = query.where(asset.is_existing_asset == 1)
	if filters.asset_category:
		query = query.where(asset.asset_category == filters.asset_category)
	if filters.cost_center:
		query = query.where(asset.cost_center == filters.cost_center)
	if filters.status:
		if filters.status == "In Location":
			query = query.where(asset.status.notin(["Sold", "Scrapped", "Capitalized"]))
		else:
			query = query.where(asset.status.isin(["Sold", "Scrapped", "Capitalized"]))
	if finance_book:
		query = query.where((gle.finance_book.isin([cstr(finance_book), ""])) | (gle.finance_book.isnull()))
	else:
		query = query.where((gle.finance_book.isin([""])) | (gle.finance_book.isnull()))
	if filters.filter_based_on in ("Date Range", "Fiscal Year"):
		query = query.where(gle.posting_date >= start_date)
		query = query.where(gle.posting_date <= end_date)

	query = query.groupby(asset.name)
	return dict(query.run())


def get_group_by_data(group_by, conditions, assets_linked_to_fb, depreciation_amount_map, revaluation_amount_map):
	fields = [
		group_by, "name", "gross_purchase_amount", "opening_accumulated_depreciation", "calculate_depreciation",
	]
	assets = frappe.db.get_all("Asset", filters=conditions, fields=fields)
	data = []
	for a in assets:
		if assets_linked_to_fb and a.calculate_depreciation and a.name not in assets_linked_to_fb:
			continue
		a["depreciated_amount"] = depreciation_amount_map.get(a["name"], 0.0)
		a["revaluation_amount"] = revaluation_amount_map.get(a["name"], 0.0)
		a["asset_value"] = (
			a["gross_purchase_amount"] - a["opening_accumulated_depreciation"]
			- a["depreciated_amount"] + a["revaluation_amount"]
		)
		del a["name"]
		del a["calculate_depreciation"]
		idx = ([i for i, d in enumerate(data) if a[group_by] == d[group_by]] or [None])[0]
		if idx is None:
			data.append(a)
		else:
			for field in ("gross_purchase_amount", "opening_accumulated_depreciation", "depreciated_amount", "asset_value"):
				data[idx][field] = data[idx][field] + a[field]
	return data


def get_purchase_receipt_supplier_map():
	return frappe._dict(
		frappe.db.sql(
			"""Select pr.name, pr.supplier
			FROM `tabPurchase Receipt` pr, `tabPurchase Receipt Item` pri
			WHERE pri.parent = pr.name AND pri.is_fixed_asset=1 AND pr.docstatus=1 AND pr.is_return=0"""
		)
	)


def get_purchase_invoice_supplier_map():
	return frappe._dict(
		frappe.db.sql(
			"""Select pi.name, pi.supplier
			FROM `tabPurchase Invoice` pi, `tabPurchase Invoice Item` pii
			WHERE pii.parent = pi.name AND pii.is_fixed_asset=1 AND pi.docstatus=1 AND pi.is_return=0"""
		)
	)


def get_columns(filters):
	if filters.get("group_by") in ["Asset Category", "Location"]:
		return [
			{"label": _("{}").format(filters.get("group_by")), "fieldtype": "Link", "fieldname": frappe.scrub(filters.get("group_by")), "options": filters.get("group_by"), "width": 216},
			{"label": _("Gross Purchase Amount"), "fieldname": "gross_purchase_amount", "fieldtype": "Currency", "options": "Company:company:default_currency", "width": 250},
			{"label": _("Opening Accumulated Depreciation"), "fieldname": "opening_accumulated_depreciation", "fieldtype": "Currency", "options": "Company:company:default_currency", "width": 250},
			{"label": _("Depreciated Amount"), "fieldname": "depreciated_amount", "fieldtype": "Currency", "options": "Company:company:default_currency", "width": 250},
			{"label": _("Asset Value"), "fieldname": "asset_value", "fieldtype": "Currency", "options": "Company:company:default_currency", "width": 250},
			{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 120},
		]

	return [
		{"label": _("B.S. Account"), "fieldname": "bs_account", "fieldtype": "Link", "options": "Account", "width": 140},
		{"label": _("Account Name"), "fieldname": "account_name", "fieldtype": "Data", "width": 140},
		{"label": _("Depreciation Expense Account"), "fieldname": "depreciation_expense_account", "fieldtype": "Link", "options": "Account", "width": 160},
		{"label": _("Accumulated Depreciation Account"), "fieldname": "accumulated_depreciation_account", "fieldtype": "Link", "options": "Account", "width": 160},
		{"label": _("Asset Class"), "fieldname": "asset_class", "fieldtype": "Data", "width": 100},
		{"label": _("Asset Category"), "fieldname": "asset_category", "fieldtype": "Link", "options": "Asset Category", "width": 100},
		{"label": _("Asset ID"), "fieldname": "asset_id", "fieldtype": "Link", "options": "Asset", "width": 100},
		{"label": _("Asset Code"), "fieldname": "asset_code", "fieldtype": "Data", "width": 100},
		{"label": _("Asset Description"), "fieldname": "asset_description", "fieldtype": "Data", "width": 160},
		{"label": _("Purchase Date"), "fieldname": "purchase_date", "fieldtype": "Date", "width": 90},
		{"label": _("Available for Use Date"), "fieldname": "available_for_use_date", "fieldtype": "Date", "width": 90},
		{"label": _("Useful Life (Months)"), "fieldname": "useful_life_months", "fieldtype": "Float", "width": 100},
		{"label": _("Remaining Life (Months)"), "fieldname": "remaining_life_months", "fieldtype": "Float", "width": 110},
		{"label": _("Depreciation Method"), "fieldname": "depreciation_method", "fieldtype": "Data", "width": 120},
		{"label": _("Purchase Receipt"), "fieldname": "purchase_receipt", "fieldtype": "Link", "options": "Purchase Receipt", "width": 120},
		{"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 100},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 100},
		{"label": _("Vendor Name"), "fieldname": "vendor_name", "fieldtype": "Data", "width": 100},
		{"label": _("Location"), "fieldname": "location", "fieldtype": "Link", "options": "Location", "width": 100},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 80},
		{"label": _("Opening Gross Cost (APC)"), "fieldname": "opening_gross_cost", "fieldtype": "Currency", "options": "Company:company:default_currency", "width": 130},
		{"label": _("Additions / Capitalization"), "fieldname": "additions", "fieldtype": "Currency", "options": "Company:company:default_currency", "width": 130},
		{"label": _("Disposals / Transfers"), "fieldname": "disposals", "fieldtype": "Currency", "options": "Company:company:default_currency", "width": 130},
		{"label": _("Closing Gross Cost (APC)"), "fieldname": "closing_gross_cost", "fieldtype": "Currency", "options": "Company:company:default_currency", "width": 130},
		{"label": _("Opening Accumulated Depreciation"), "fieldname": "opening_accumulated_depreciation", "fieldtype": "Currency", "options": "Company:company:default_currency", "width": 140},
		{"label": _("Current Period Depreciation"), "fieldname": "depreciated_amount", "fieldtype": "Currency", "options": "Company:company:default_currency", "width": 140},
		{"label": _("Closing Accumulated Depreciation"), "fieldname": "closing_accumulated_depreciation", "fieldtype": "Currency", "options": "Company:company:default_currency", "width": 140},
		{"label": _("Closing Net Book Value (NBV)"), "fieldname": "asset_value", "fieldtype": "Currency", "options": "Company:company:default_currency", "width": 140},
	]