import frappe
from frappe.utils import cint, getdate
from frappe import _
from frappe.query_builder.functions import Max, Min
from frappe.query_builder import Order

from frappe.utils import (
	add_months,
	cint,
	flt,
	get_last_day,
	get_link_to_form,
	getdate,
	is_last_day_of_the_month,
	nowdate,
	today,
)
import erpnext
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_checks_for_pl_and_bs_accounts,
)
from erpnext.accounts.doctype.journal_entry.journal_entry import make_reverse_journal_entry
from erpnext.assets.doctype.asset_activity.asset_activity import add_asset_activity
from erpnext.assets.doctype.asset_depreciation_schedule.asset_depreciation_schedule import (
	get_asset_depr_schedule_doc,
	get_asset_depr_schedule_name,
	get_temp_asset_depr_schedule_doc,
	make_new_active_asset_depr_schedules_and_cancel_current_ones,
)

def post_depreciation_entries(date=None):
	# Return if automatic booking of asset depreciation is disabled
	if not cint(
		frappe.db.get_value("Accounts Settings", None, "book_asset_depreciation_entry_automatically")
	):
		return

	if not date:
		date = today()

	failed_asset_names = []
	error_log_names = []

	depreciable_asset_depr_schedules_data = get_depreciable_asset_depr_schedules_data(date)

	credit_and_debit_accounts_for_asset_category_and_company = {}
	depreciation_cost_center_and_depreciation_series_for_company = (
		get_depreciation_cost_center_and_depreciation_series_for_company()
	)

	accounting_dimensions = get_checks_for_pl_and_bs_accounts()

	for asset_depr_schedule_data in depreciable_asset_depr_schedules_data:
		(
			asset_depr_schedule_name,
			asset_name,
			asset_category,
			asset_company,
			sch_start_idx,
			sch_end_idx,
		) = asset_depr_schedule_data

		if (
			asset_category,
			asset_company,
		) not in credit_and_debit_accounts_for_asset_category_and_company:
			credit_and_debit_accounts_for_asset_category_and_company.update(
				{
					(
						asset_category,
						asset_company,
					): get_credit_and_debit_accounts_for_asset_category_and_company(
						asset_category, asset_company
					),
				}
			)

		try:
			_make_depreciation_entry(
				asset_depr_schedule_name,
				date,
				sch_start_idx,
				sch_end_idx,
				credit_and_debit_accounts_for_asset_category_and_company[(asset_category, asset_company)],
				depreciation_cost_center_and_depreciation_series_for_company[asset_company],
				accounting_dimensions,
			)

			frappe.db.commit()
		except Exception as e:
			frappe.db.rollback()
			failed_asset_names.append(asset_name)
			error_log = frappe.log_error(e)
			error_log_names.append(error_log.name)

	if failed_asset_names:
		set_depr_entry_posting_status_for_failed_assets(failed_asset_names)
		notify_depr_entry_posting_error(failed_asset_names, error_log_names)

	frappe.db.commit()

def _make_depreciation_entry(
	asset_depr_schedule_name,
	date=None,
	sch_start_idx=None,
	sch_end_idx=None,
	credit_and_debit_accounts=None,
	depreciation_cost_center_and_depreciation_series=None,
	accounting_dimensions=None,
):
	frappe.has_permission("Journal Entry", throw=True)

	if not date:
		date = today()

	asset_depr_schedule_doc = frappe.get_doc("Asset Depreciation Schedule", asset_depr_schedule_name)

	asset = frappe.get_doc("Asset", asset_depr_schedule_doc.asset)

	if credit_and_debit_accounts:
		credit_account, debit_account = credit_and_debit_accounts
	else:
		credit_account, debit_account = get_credit_and_debit_accounts_for_asset_category_and_company(
			asset.asset_category, asset.company
		)

	if depreciation_cost_center_and_depreciation_series:
		depreciation_cost_center, depreciation_series = depreciation_cost_center_and_depreciation_series
	else:
		depreciation_cost_center, depreciation_series = frappe.get_cached_value(
			"Company", asset.company, ["depreciation_cost_center", "series_for_depreciation_entry"]
		)

	depreciation_cost_center = asset.cost_center or depreciation_cost_center

	if not accounting_dimensions:
		accounting_dimensions = get_checks_for_pl_and_bs_accounts()

	depreciation_posting_error = None

	for d in asset_depr_schedule_doc.get("depreciation_schedule")[
		sch_start_idx or 0 : sch_end_idx or len(asset_depr_schedule_doc.get("depreciation_schedule"))
	]:
		try:
			_make_journal_entry_for_depreciation(
				asset_depr_schedule_doc,
				asset,
				date,
				d,
				sch_start_idx,
				sch_end_idx,
				depreciation_cost_center,
				depreciation_series,
				credit_account,
				debit_account,
				accounting_dimensions,
			)
		except Exception as e:
			depreciation_posting_error = e

	asset.set_status()

	if not depreciation_posting_error:
		asset.db_set("depr_entry_posting_status", "Successful")
		return asset_depr_schedule_doc

	raise depreciation_posting_error

def _make_journal_entry_for_depreciation(
	asset_depr_schedule_doc,
	asset,
	date,
	depr_schedule,
	sch_start_idx,
	sch_end_idx,
	depreciation_cost_center,
	depreciation_series,
	credit_account,
	debit_account,
	accounting_dimensions,
):
	if not (sch_start_idx and sch_end_idx) and not (
		not depr_schedule.journal_entry and getdate(depr_schedule.schedule_date) <= getdate(date)
	):
		return

	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Depreciation Entry"
	je.naming_series = depreciation_series
	je.posting_date = depr_schedule.schedule_date
	je.company = asset.company
	je.finance_book = asset_depr_schedule_doc.finance_book
	je.remark = _("Depreciation Entry against {0} worth {1}").format(
		asset.name, depr_schedule.depreciation_amount
	)

	credit_entry = {
		"account": credit_account,
		"credit_in_account_currency": depr_schedule.depreciation_amount,
		"reference_type": "Asset",
		"reference_name": asset.name,
		"cost_center": depreciation_cost_center,
	}

	debit_entry = {
		"account": debit_account,
		"debit_in_account_currency": depr_schedule.depreciation_amount,
		"reference_type": "Asset",
		"reference_name": asset.name,
		"cost_center": depreciation_cost_center,
	}

	for dimension in accounting_dimensions:
		if asset.get(dimension["fieldname"]) or dimension.get("mandatory_for_bs"):
			credit_entry.update(
				{
					dimension["fieldname"]: asset.get(dimension["fieldname"])
					or dimension.get("default_dimension")
				}
			)

		if asset.get(dimension["fieldname"]) or dimension.get("mandatory_for_pl"):
			debit_entry.update(
				{
					dimension["fieldname"]: asset.get(dimension["fieldname"])
					or dimension.get("default_dimension")
				}
			)

	project = get_asset_project(asset.name)
	if project:
		je.custom_project = project
		credit_entry["project"] = project
		debit_entry["project"] = project

	je.append("accounts", credit_entry)
	je.append("accounts", debit_entry)

	je.flags.ignore_permissions = True
	je.flags.planned_depr_entry = True
	je.save()

	depr_schedule.db_set("journal_entry", je.name)

	if not je.meta.get_workflow():
		print("Submitting Journal Entry for Depreciation")
		# ── NEW LOGIC ──────────────────────────────────────────────────────────
		accounts_settings = frappe.get_cached_doc("Accounts Settings")
		book_automatically = accounts_settings.book_asset_depreciation_entry_automatically
		entry_type = accounts_settings.get("custom_entry_type")  # "Draft" or "Submit"

		should_submit = book_automatically and entry_type == "Submit"
		# ───────────────────────────────────────────────────────────────────────

		if should_submit:
			je.submit()
			asset.reload()
			idx = cint(asset_depr_schedule_doc.finance_book_id)
			row = asset.get("finance_books")[idx - 1]
			row.value_after_depreciation -= depr_schedule.depreciation_amount
			row.db_update()

def get_depreciable_asset_depr_schedules_data(date):
	a = frappe.qb.DocType("Asset")
	ads = frappe.qb.DocType("Asset Depreciation Schedule")
	ds = frappe.qb.DocType("Depreciation Schedule")

	res = (
		frappe.qb.from_(ads)
		.join(a)
		.on(ads.asset == a.name)
		.join(ds)
		.on(ads.name == ds.parent)
		.select(ads.name, a.name, a.asset_category, a.company, Min(ds.idx) - 1, Max(ds.idx))
		.where(a.calculate_depreciation == 1)
		.where(a.docstatus == 1)
		.where(ads.docstatus == 1)
		.where(a.status.isin(["Submitted", "Partially Depreciated"]))
		.where(ds.journal_entry.isnull())
		.where(ds.schedule_date <= date)
		.groupby(ads.name)
		.orderby(a.creation, order=Order.desc)
	)

	acc_frozen_upto = get_acc_frozen_upto()
	if acc_frozen_upto:
		res = res.where(ds.schedule_date > acc_frozen_upto)

	res = res.run()

	return res


def get_asset_project(asset_name):
	res = frappe.db.sql(
		"""
		SELECT ami.custom_target_project
		FROM `tabAsset Movement Item` ami
		JOIN `tabAsset Movement` am ON am.name = ami.parent
		WHERE ami.asset = %s AND am.docstatus = 1
		  AND IFNULL(ami.custom_target_project, '') != ''
		ORDER BY am.transaction_date DESC, am.creation DESC
		LIMIT 1
		""",
		asset_name,
		as_dict=True
	)
	return res[0].get("custom_target_project") if res else frappe.db.get_value("Asset", asset_name, "custom_project")

def get_acc_frozen_upto():
	acc_frozen_upto = frappe.db.get_single_value("Accounts Settings", "acc_frozen_upto")

	if not acc_frozen_upto:
		return

	frozen_accounts_modifier = frappe.db.get_single_value("Accounts Settings", "frozen_accounts_modifier")

	if frozen_accounts_modifier not in frappe.get_roles() or frappe.session.user == "Administrator":
		return getdate(acc_frozen_upto)

	return

def get_depreciation_cost_center_and_depreciation_series_for_company():
	company_names = frappe.db.get_all("Company", pluck="name")

	res = {}

	for company_name in company_names:
		depreciation_cost_center, depreciation_series = frappe.get_cached_value(
			"Company", company_name, ["depreciation_cost_center", "series_for_depreciation_entry"]
		)
		res.update({company_name: (depreciation_cost_center, depreciation_series)})

	return res


def get_credit_and_debit_accounts_for_asset_category_and_company(asset_category, company):
	(
		_,
		accumulated_depreciation_account,
		depreciation_expense_account,
	) = get_depreciation_accounts(asset_category, company)

	credit_account, debit_account = get_credit_and_debit_accounts(
		accumulated_depreciation_account, depreciation_expense_account
	)

	return (credit_account, debit_account)


def get_depreciation_accounts(asset_category, company):
	fixed_asset_account = accumulated_depreciation_account = depreciation_expense_account = None

	non_depreciable_category = frappe.db.get_value(
		"Asset Category", asset_category, "non_depreciable_category"
	)

	accounts = frappe.db.get_value(
		"Asset Category Account",
		filters={"parent": asset_category, "company_name": company},
		fieldname=[
			"fixed_asset_account",
			"accumulated_depreciation_account",
			"depreciation_expense_account",
		],
		as_dict=1,
	)

	if accounts:
		fixed_asset_account = accounts.fixed_asset_account
		accumulated_depreciation_account = accounts.accumulated_depreciation_account
		depreciation_expense_account = accounts.depreciation_expense_account

	if not fixed_asset_account:
		frappe.throw(_("Please set Fixed Asset Account in Asset Category {0}").format(asset_category))

	if not non_depreciable_category:
		accounts = frappe.get_cached_value(
			"Company", company, ["accumulated_depreciation_account", "depreciation_expense_account"]
		)

		if not accumulated_depreciation_account:
			accumulated_depreciation_account = accounts[0]
		if not depreciation_expense_account:
			depreciation_expense_account = accounts[1]

		if not accumulated_depreciation_account or not depreciation_expense_account:
			frappe.throw(
				_("Please set Depreciation related Accounts in Asset Category {0} or Company {1}").format(
					asset_category, company
				)
			)

	return fixed_asset_account, accumulated_depreciation_account, depreciation_expense_account


def get_credit_and_debit_accounts(accumulated_depreciation_account, depreciation_expense_account):
	root_type = frappe.get_value("Account", depreciation_expense_account, "root_type")

	if root_type == "Expense":
		credit_account = accumulated_depreciation_account
		debit_account = depreciation_expense_account
	elif root_type == "Income":
		credit_account = depreciation_expense_account
		debit_account = accumulated_depreciation_account
	else:
		frappe.throw(_("Depreciation Expense Account should be an Income or Expense Account."))

	return credit_account, debit_account
