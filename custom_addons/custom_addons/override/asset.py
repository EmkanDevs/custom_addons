import frappe
from frappe.utils import cint, getdate
from frappe import _


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