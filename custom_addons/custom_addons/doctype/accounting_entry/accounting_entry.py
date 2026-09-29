# Copyright (c) 2026, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, fmt_money


@frappe.whitelist()
def get_tax_template_details(template_type, template_name):
	"""Fetches taxes list (account_head, rate, description) from the selected tax template."""
	if not template_type or not template_name:
		return []

	if template_type not in ["Purchase Taxes and Charges Template", "Sales Taxes and Charges Template"]:
		return []

	template = frappe.get_cached_doc(template_type, template_name)
	taxes = []
	for row in template.get("taxes") or []:
		taxes.append({
			"account_head": row.account_head,
			"rate": flt(row.rate),
			"description": row.description or template_name,
			"charge_type": row.charge_type or "On Net Total"
		})
	return taxes


def get_accounting_entry_settings():
	"""Fetches global defaults from Accounting Entry Settings Single DocType."""
	if frappe.db.exists("DocType", "Accounting Entry Settings"):
		return frappe.get_single("Accounting Entry Settings")
	return frappe._dict()


def get_mode_of_payment_for_account(account, company, account_type):
	"""Resolves the appropriate Mode of Payment based on linked account or account type."""
	# 1. Check if a Mode of Payment has this account explicitly configured for this company
	mop = frappe.db.get_value(
		"Mode of Payment Account",
		{"default_account": account, "company": company},
		"parent"
	)
	if mop and frappe.db.get_value("Mode of Payment", mop, "enabled"):
		return mop

	# 2. Check if a Mode of Payment matches the account_type ('Cash' or 'Bank')
	mop = frappe.db.get_value(
		"Mode of Payment",
		{"type": account_type, "enabled": 1},
		"name"
	)
	if mop:
		return mop

	# 3. Fallback to any enabled Mode of Payment
	return frappe.db.get_value("Mode of Payment", {"enabled": 1}, "name")


class AccountingEntry(Document):
	def validate(self):
		self.validate_mandatory()
		self.set_company_currency()
		self.set_party_and_template_types()
		self.set_row_currencies_and_exchange_rates()
		self.validate_accounts()
		self.sync_auto_tax_rows()
		self.calculate_totals()

	def on_submit(self):
		self.validate_balance()
		self.create_and_submit_invoice()

	def on_cancel(self):
		self.cancel_linked_invoices()

	def on_trash(self):
		self.delete_linked_invoices()

	def validate_mandatory(self):
		if not self.company:
			frappe.throw(_("Company is mandatory"))
		if not self.posting_date:
			frappe.throw(_("Posting Date is mandatory"))
		if not self.accounts:
			frappe.throw(_("Please add at least one row in Accounting Entries table"))

	def set_company_currency(self):
		if self.company and not self.company_currency:
			self.company_currency = frappe.get_cached_value("Company", self.company, "default_currency")

	def set_party_and_template_types(self):
		# Sync Party Type based on Tax Type
		if self.tax_type == "Inward":
			self.party_type = "Supplier"
			template_type = "Purchase Taxes and Charges Template"
		else:
			self.party_type = "Customer"
			template_type = "Sales Taxes and Charges Template"

		# Sync tax_template_type in all child rows
		for row in self.accounts:
			row.tax_template_type = template_type

	def set_row_currencies_and_exchange_rates(self):
		company_currency = self.company_currency or "SAR"

		for row in self.accounts:
			# Auto fetch account currency if missing
			if not row.account_currency and row.account:
				row.account_currency = frappe.db.get_value("Account", row.account, "account_currency") or company_currency

			if not row.currency:
				row.currency = row.account_currency or company_currency

			if not row.exchange_rate:
				row.exchange_rate = 1.0

			if row.currency == company_currency:
				row.exchange_rate = 1.0

			# Calculate company currency amounts
			row.debit_in_company_currency = flt(flt(row.debit) * flt(row.exchange_rate), 2)
			row.credit_in_company_currency = flt(flt(row.credit) * flt(row.exchange_rate), 2)

	def validate_accounts(self):
		has_cash_or_bank = False

		for idx, row in enumerate(self.accounts, 1):
			if not row.account:
				frappe.throw(_("Row #{0}: Account is required").format(idx))

			# Ensure account belongs to this company and is not a group
			account_details = frappe.db.get_value(
				"Account",
				row.account,
				["company", "is_group", "account_type"],
				as_dict=1
			)
			if account_details:
				if account_details.company != self.company:
					frappe.throw(
						_("Row #{0}: Account {1} does not belong to Company {2}").format(
							idx, frappe.bold(row.account), frappe.bold(self.company)
						)
					)
				if account_details.is_group:
					frappe.throw(
						_("Row #{0}: Account {1} cannot be a group account").format(
							idx, frappe.bold(row.account)
						)
					)
				if account_details.account_type in ["Cash", "Bank"]:
					has_cash_or_bank = True

		if not has_cash_or_bank:
			frappe.throw(
				_("At least one Cash or Bank account (where Account Type is 'Cash' or 'Bank') is required in Accounting Entries to process payment."),
				frappe.ValidationError
			)

	def sync_auto_tax_rows(self):
		"""Dynamically calculates taxes based on the selected tax templates (no hardcoded rate)."""
		if self.docstatus != 0:
			return

		if self.tax_method != "Auto":
			# Manually mode: remove any auto-generated tax rows
			self.accounts = [r for r in self.accounts if not r.is_auto_tax_row]
			return

		manual_rows = [r for r in self.accounts if not r.is_auto_tax_row and (flt(r.debit) > 0 or flt(r.credit) > 0)]
		is_inward = (self.tax_type == "Inward")
		template_type = "Purchase Taxes and Charges Template" if is_inward else "Sales Taxes and Charges Template"
		company_currency = self.company_currency or "SAR"

		# Map to accumulate tax amounts by account_head
		tax_summary = {}  # { account_head: { "amount": flt, "rate": flt, "description": str } }

		for r in manual_rows:
			base_amount = flt(r.debit_in_company_currency if is_inward else r.credit_in_company_currency)
			if base_amount <= 0:
				continue

			if r.tax_category:
				taxes = get_tax_template_details(template_type, r.tax_category)
				for tax in taxes:
					account_head = tax.get("account_head")
					rate = flt(tax.get("rate"))
					if account_head and rate > 0:
						calculated_tax = flt(base_amount * (rate / 100.0), 2)
						if account_head not in tax_summary:
							tax_summary[account_head] = {
								"amount": 0.0,
								"rate": rate,
								"description": tax.get("description", "")
							}
						tax_summary[account_head]["amount"] += calculated_tax

		# Preserve manual rows, remove old auto tax rows
		new_account_rows = [r for r in self.accounts if not r.is_auto_tax_row]

		# Append computed dynamic tax rows
		for account_head, data in tax_summary.items():
			tax_amount = flt(data["amount"], 2)
			if tax_amount > 0:
				new_account_rows.append(self.new_auto_tax_row(
					account_head=account_head,
					tax_amount=tax_amount,
					is_inward=is_inward,
					company_currency=company_currency,
					template_type=template_type
				))

		self.accounts = new_account_rows

	def new_auto_tax_row(self, account_head, tax_amount, is_inward, company_currency, template_type):
		row = self.append("accounts", {})
		row.account = account_head
		row.account_currency = company_currency
		row.currency = company_currency
		row.exchange_rate = 1.0
		row.debit = tax_amount if is_inward else 0.0
		row.debit_in_company_currency = tax_amount if is_inward else 0.0
		row.credit = 0.0 if is_inward else tax_amount
		row.credit_in_company_currency = 0.0 if is_inward else tax_amount
		row.tax_template_type = template_type
		row.is_auto_tax_row = 1
		return row

	def calculate_totals(self):
		total_debit = 0.0
		total_debit_cc = 0.0
		total_credit = 0.0
		total_credit_cc = 0.0

		for r in self.accounts:
			total_debit += flt(r.debit)
			total_debit_cc += flt(r.debit_in_company_currency)
			total_credit += flt(r.credit)
			total_credit_cc += flt(r.credit_in_company_currency)

		self.total_debit = flt(total_debit, 2)
		self.total_debit_company_currency = flt(total_debit_cc, 2)
		self.total_credit = flt(total_credit, 2)
		self.total_credit_company_currency = flt(total_credit_cc, 2)
		self.difference = flt(self.total_debit_company_currency - self.total_credit_company_currency, 2)

	def validate_balance(self):
		self.calculate_totals()
		if abs(flt(self.difference)) >= 0.01:
			formatted_diff = fmt_money(abs(self.difference), currency=self.company_currency)
			direction = _("more debit") if self.difference > 0 else _("more credit")
			frappe.throw(
				_("Cannot submit: Debit and Credit are not balanced. Difference: {0} ({1}).").format(
					formatted_diff, direction
				),
				frappe.ValidationError
			)

	def _linked_invoice_pairs(self):
		"""Returns [(fieldname, doctype), ...] for whichever invoices this
		Accounting Entry actually generated."""
		return [
			("purchase_invoice", "Purchase Invoice"),
			("sales_invoice", "Sales Invoice"),
		]

	def cancel_linked_invoices(self):
		for fieldname, doctype in self._linked_invoice_pairs():
			docname = self.get(fieldname)
			if not docname or not frappe.db.exists(doctype, docname):
				continue
			doc = frappe.get_doc(doctype, docname)
			if doc.docstatus == 1:
				doc.flags.ignore_permissions = True
				doc.cancel()


	def delete_linked_invoices(self):
		"""Called on_trash: cancels (if still submitted) and permanently
		deletes any Purchase/Sales Invoice this Accounting Entry generated,
		so deleting an Accounting Entry doesn't leave an orphaned invoice behind."""
		for fieldname, doctype in self._linked_invoice_pairs():
			docname = self.get(fieldname)
			if not docname or not frappe.db.exists(doctype, docname):
				continue
			doc = frappe.get_doc(doctype, docname)
			if doc.docstatus == 1:
				doc.flags.ignore_permissions = True
				doc.cancel()
			# docstatus is now 0 (draft, shouldn't normally happen) or 2 (cancelled)
			frappe.delete_doc(
				doctype, docname,
				ignore_permissions=True,
				force=True,
			)

	def _propagate_accounting_dimensions(self, invoice):
		"""Copy every enabled Accounting Dimension field value from this
		Accounting Entry header to the target invoice header, so that
		ERPNext can stamp them on the auto-created AP/AR GL entry."""
		try:
			dimensions = frappe.get_all(
				"Accounting Dimension",
				filters={"disabled": 0},
				fields=["fieldname"],
			)
		except Exception:
			return

		for dim in dimensions:
			fn = dim.fieldname
			val = self.get(fn)
			if val:
				try:
					invoice.set(fn, val)
				except Exception:
					pass

	def get_cash_bank_row(self, for_inward=True):
		"""Finds the Cash or Bank account row in accounts.
		For Inward (Purchase): Payment is in Credit.
		For Outward (Sales): Payment is in Debit.
		"""
		for row in self.accounts:
			if row.is_auto_tax_row:
				continue
			acc_type = frappe.db.get_value("Account", row.account, "account_type")
			if acc_type in ["Cash", "Bank"]:
				if for_inward and flt(row.credit) > 0:
					return row, acc_type
				elif not for_inward and flt(row.debit) > 0:
					return row, acc_type

		# Fallback to any Cash/Bank row if strict debit/credit side isn't met
		for row in self.accounts:
			if row.is_auto_tax_row:
				continue
			acc_type = frappe.db.get_value("Account", row.account, "account_type")
			if acc_type in ["Cash", "Bank"]:
				return row, acc_type

		return None, None

	def make_purchase_invoice(self):
		"""Generates a standard ERPNext Purchase Invoice marked as Paid from this Accounting Entry."""
		settings = get_accounting_entry_settings()

		# 1. Resolve Supplier
		supplier = self.party or settings.get("default_supplier")
		if not supplier:
			frappe.throw(
				_("Supplier is required. Please specify a Supplier in the Accounting Entry or set Default Supplier in Accounting Entry Settings.")
			)

		# 2. Resolve Default Purchase Item
		default_item = settings.get("default_purchase_item")
		if not default_item:
			default_item = frappe.db.get_value("Item", {"is_purchase_item": 1, "disabled": 0}, "name")
		if not default_item:
			frappe.throw(
				_("Default Purchase Item is required. Please configure Default Purchase Item in Accounting Entry Settings.")
			)

		# 3. Identify Cash/Bank Account for Payment
		cash_bank_row, acc_type = self.get_cash_bank_row(for_inward=True)
		if not cash_bank_row:
			frappe.throw(
				_("No Cash or Bank account with Credit amount found to mark the Purchase Invoice as Paid.")
			)

		paid_amount = flt(cash_bank_row.credit)
		base_paid_amount = flt(cash_bank_row.credit_in_company_currency) or paid_amount
		mode_of_payment = get_mode_of_payment_for_account(cash_bank_row.account, self.company, acc_type)

		# 3b. Batch-fetch account_type for every distinct account on this entry,
		# so we can detect tax rows even when is_auto_tax_row wasn't set upstream.
		account_names = list({row.account for row in self.accounts if row.account})
		account_type_map = {
			d["name"]: d["account_type"]
			for d in frappe.get_all(
				"Account",
				filters={"name": ["in", account_names]},
				fields=["name", "account_type"],
			)
		}

		def _is_tax_row(row):
			return bool(row.is_auto_tax_row) or account_type_map.get(row.account) == "Tax"

		# Resolve a project to propagate to the invoice header (needed for accounts with mandatory project)
		invoice_project = cash_bank_row.project if cash_bank_row.project else None
		if not invoice_project:
			for row in self.accounts:
				if not _is_tax_row(row) and row.name != cash_bank_row.name and flt(row.debit) > 0 and row.project:
					invoice_project = row.project
					break

		# 4. Instantiate Purchase Invoice Doc
		pi = frappe.new_doc("Purchase Invoice")
		pi.company = self.company
		pi.supplier = supplier
		pi.posting_date = self.posting_date
		pi.currency = self.company_currency
		pi.bill_no = self.ref_number or ""
		pi.bill_date = self.ref_date or self.posting_date
		pi.remarks = self.user_remark or _("Generated from Accounting Entry {0}").format(self.name)
		if invoice_project:
			pi.project = invoice_project

		# Propagate all accounting dimensions to the PI header so ERPNext
		# stamps them on the auto-created AP GL / Payment Ledger Entry.
		self._propagate_accounting_dimensions(pi)

		# Payment Details (Standard ERPNext is_paid flow)
		pi.is_paid = 1
		pi.cash_bank_account = cash_bank_row.account
		pi.paid_amount = paid_amount
		pi.base_paid_amount = base_paid_amount
		if mode_of_payment:
			pi.mode_of_payment = mode_of_payment

		# 5. Populate Items: Each separate non-tax debit row -> separate item row with its expense_account
		for row in self.accounts:
			if _is_tax_row(row):
				continue
			if row.name == cash_bank_row.name:
				continue
			if flt(row.debit) <= 0:
				continue

			item_row = pi.append("items", {})
			item_row.item_code = default_item
			item_row.qty = 1.0
			item_row.rate = flt(row.debit)
			item_row.amount = flt(row.debit)
			item_row.expense_account = row.account
			if row.project:
				item_row.project = row.project
			if row.department:
				item_row.department = row.department
			# Propagate per-row accounting dimensions (task, employee, etc.)
			for _dim_field in ["task", "employee", "region_location", "asset"]:
				_val = row.get(_dim_field) or self.get(_dim_field)
				if _val:
					try:
						item_row.set(_dim_field, _val)
					except Exception:
						pass

		# 6. Populate Taxes: from Auto Tax rows OR rows on a Tax-type account
		for row in self.accounts:
			if _is_tax_row(row) and flt(row.debit) > 0:
				tax_row = pi.append("taxes", {})
				tax_row.charge_type = "Actual"
				tax_row.account_head = row.account
				tax_row.tax_amount = flt(row.debit)
				tax_row.description = frappe.db.get_value("Account", row.account, "account_name") or row.account
				tax_row.category = "Total"
				tax_row.add_deduct_tax = "Add"

		# Trigger standard ERPNext calculation
		# Clear taxes_and_charges so set_missing_values does not auto-apply a
		# supplier default template (which would add 0-rate rows and fail validation)
		# Save expense_account per item index — set_missing_values() resets it
		# to the item master default, overriding our Accounting Entry accounts.
		_saved_expense_accounts = [r.expense_account for r in pi.items]
		# Set the Purchase Taxes and Charges Template from the Accounting Entry's tax
		# category (required by KSA/ZATCA compliance and for tax table population).
		_first_tax_category = None
		for r in self.accounts:
			if r.tax_category and not _is_tax_row(r):
				_first_tax_category = r.tax_category
				break
		if _first_tax_category:
			pi.taxes_and_charges = _first_tax_category
		pi.run_method("set_missing_values")
		pi.run_method("calculate_taxes_and_totals")
		pi.paid_amount = paid_amount
		pi.base_paid_amount = base_paid_amount
		# Restore expense accounts overridden by set_missing_values
		for _idx, _item in enumerate(pi.items):
			if _idx < len(_saved_expense_accounts) and _saved_expense_accounts[_idx]:
				_item.expense_account = _saved_expense_accounts[_idx]

		return pi

	def make_sales_invoice(self):
		"""Generates a standard ERPNext Sales Invoice marked as Paid from this Accounting Entry."""
		settings = get_accounting_entry_settings()

		# 1. Resolve Customer
		customer = self.party or settings.get("default_customer")
		if not customer:
			frappe.throw(
				_("Customer is required. Please specify a Customer in the Accounting Entry or set Default Customer in Accounting Entry Settings.")
			)

		# 2. Resolve Default Sales Item
		default_item = settings.get("default_sales_item")
		if not default_item:
			default_item = frappe.db.get_value("Item", {"is_sales_item": 1, "disabled": 0}, "name")
		if not default_item:
			frappe.throw(
				_("Default Sales Item is required. Please configure Default Sales Item in Accounting Entry Settings.")
			)

		# 3. Identify Cash/Bank Account for Payment
		cash_bank_row, acc_type = self.get_cash_bank_row(for_inward=False)
		if not cash_bank_row:
			frappe.throw(
				_("No Cash or Bank account with Debit amount found to mark the Sales Invoice as Paid.")
			)

		paid_amount = flt(cash_bank_row.debit)
		base_paid_amount = flt(cash_bank_row.debit_in_company_currency) or paid_amount
		mode_of_payment = get_mode_of_payment_for_account(cash_bank_row.account, self.company, acc_type)

		# 3b. Batch-fetch account_type for every distinct account on this entry,
		# so we can detect tax rows even when is_auto_tax_row wasn't set upstream.
		account_names = list({row.account for row in self.accounts if row.account})
		account_type_map = {
			d["name"]: d["account_type"]
			for d in frappe.get_all(
				"Account",
				filters={"name": ["in", account_names]},
				fields=["name", "account_type"],
			)
		}

		def _is_tax_row(row):
			return bool(row.is_auto_tax_row) or account_type_map.get(row.account) == "Tax"

		# Resolve a project to propagate to the invoice header (needed for accounts with mandatory project)
		invoice_project = cash_bank_row.project if cash_bank_row.project else None
		if not invoice_project:
			for row in self.accounts:
				if not _is_tax_row(row) and row.name != cash_bank_row.name and flt(row.credit) > 0 and row.project:
					invoice_project = row.project
					break

		# 4. Instantiate Sales Invoice Doc
		si = frappe.new_doc("Sales Invoice")
		si.company = self.company
		si.customer = customer
		si.posting_date = self.posting_date
		si.due_date = self.posting_date
		si.currency = self.company_currency
		si.remarks = self.user_remark or _("Generated from Accounting Entry {0}").format(self.name)
		if invoice_project:
			si.project = invoice_project

		# Propagate all accounting dimensions to the SI header so ERPNext
		# stamps them on the auto-created AR GL / Payment Ledger Entry.
		self._propagate_accounting_dimensions(si)

		# Payment Details (Standard ERPNext is_pos flow with payments table)
		si.is_pos = 1
		payment_row = si.append("payments", {})
		payment_row.mode_of_payment = mode_of_payment
		payment_row.amount = paid_amount
		payment_row.base_amount = base_paid_amount
		payment_row.account = cash_bank_row.account

		# 5. Populate Items: Each separate non-tax credit row -> separate item row with its income_account
		for row in self.accounts:
			if _is_tax_row(row):
				continue
			if row.name == cash_bank_row.name:
				continue
			if flt(row.credit) <= 0:
				continue

			item_row = si.append("items", {})
			item_row.item_code = default_item
			item_row.qty = 1.0
			item_row.rate = flt(row.credit)
			item_row.amount = flt(row.credit)
			item_row.income_account = row.account
			if row.project:
				item_row.project = row.project
			if row.department:
				item_row.department = row.department
			# Propagate per-row accounting dimensions (task, employee, etc.)
			for _dim_field in ["task", "employee", "region_location", "asset"]:
				_val = row.get(_dim_field) or self.get(_dim_field)
				if _val:
					try:
						item_row.set(_dim_field, _val)
					except Exception:
						pass

		# 6. Populate Taxes: from Auto Tax rows OR rows on a Tax-type account
		for row in self.accounts:
			if _is_tax_row(row) and flt(row.credit) > 0:
				tax_row = si.append("taxes", {})
				tax_row.charge_type = "Actual"
				tax_row.account_head = row.account
				tax_row.tax_amount = flt(row.credit)
				tax_row.description = frappe.db.get_value("Account", row.account, "account_name") or row.account
				tax_row.category = "Total"
				tax_row.add_deduct_tax = "Add"

		# Trigger standard ERPNext calculation
		# Clear taxes_and_charges so set_missing_values does not auto-apply a
		# customer default template (which would add 0-rate rows and fail validation)
		# Save income_account per item index — set_missing_values() resets it
		# to the item master default, overriding our Accounting Entry accounts.
		_saved_income_accounts = [r.income_account for r in si.items]
		# Set the Sales Taxes and Charges Template from the Accounting Entry's tax
		# category (required by KSA/ZATCA compliance). Without this ZATCA rejects
		# the invoice with: "Please Include Sales Taxes and Charges Template on invoice"
		_first_tax_category = None
		for r in self.accounts:
			if r.tax_category and not _is_tax_row(r):
				_first_tax_category = r.tax_category
				break
		if _first_tax_category:
			si.taxes_and_charges = _first_tax_category
		si.run_method("set_missing_values")
		si.run_method("calculate_taxes_and_totals")
		# Restore income accounts overridden by set_missing_values
		for _idx, _item in enumerate(si.items):
			if _idx < len(_saved_income_accounts) and _saved_income_accounts[_idx]:
				_item.income_account = _saved_income_accounts[_idx]

		# Re-build the payments table from scratch after set_missing_values and
		# calculate_taxes_and_totals, because set_missing_values (via set_pos_data)
		# rebuilds the payments child table using the Mode of Payment's *default*
		# account for this company — not our cash_bank_row.account. Clearing and
		# re-appending the single correct row guarantees the right bank account is used.
		si.set("payments", [])
		payment_row = si.append("payments", {})
		payment_row.mode_of_payment = mode_of_payment
		payment_row.amount = paid_amount
		payment_row.base_amount = base_paid_amount
		payment_row.account = cash_bank_row.account
		si.paid_amount = paid_amount
		si.base_paid_amount = base_paid_amount

		# Carry the correct account on the doc so create_and_submit_invoice can
		# patch it after insert() (before_save wipes it via set_account_for_mode_of_payment).
		si._correct_payment_account = cash_bank_row.account
		return si

	@frappe.whitelist()
	def create_and_submit_invoice(self):
		"""Generates, saves, submits the standard invoice on submit and links it to Accounting Entry."""
		if self.tax_type == "Inward":
			if self.purchase_invoice:
				return {"doctype": "Purchase Invoice", "name": self.purchase_invoice}
			invoice = self.make_purchase_invoice()
			invoice.insert(ignore_permissions=True)
			invoice.submit()
			self._backfill_actual_tax_rate(invoice)
			frappe.db.set_value("Accounting Entry", self.name, "purchase_invoice", invoice.name)
			self.purchase_invoice = invoice.name
			frappe.msgprint(
				_("Purchase Invoice {0} created and submitted.").format(
					f'<a href="/app/purchase-invoice/{invoice.name}">{invoice.name}</a>'
				),
				indicator="green",
				alert=True
			)
			return {"doctype": "Purchase Invoice", "name": invoice.name}
		else:
			if self.sales_invoice:
				return {"doctype": "Sales Invoice", "name": self.sales_invoice}
			invoice = self.make_sales_invoice()
			invoice.insert(ignore_permissions=True)
			# ERPNext's before_save() calls set_account_for_mode_of_payment() during
			# insert(), which overwrites our payment account with the Mode of Payment's
			# default account for the company. Patch the correct account directly in DB
			# BEFORE submit() so GL entries are created against the right bank account.
			correct_payment_account = getattr(invoice, "_correct_payment_account", None)
			if correct_payment_account and invoice.payments:
				payment_child = invoice.payments[0]
				frappe.db.set_value(
					payment_child.doctype,
					payment_child.name,
					"account",
					correct_payment_account,
				)
				payment_child.account = correct_payment_account
			invoice.submit()
			self._backfill_actual_tax_rate(invoice)
			frappe.db.set_value("Accounting Entry", self.name, "sales_invoice", invoice.name)
			self.sales_invoice = invoice.name
			frappe.msgprint(
				_("Sales Invoice {0} created and submitted.").format(
					f'<a href="/app/sales-invoice/{invoice.name}">{invoice.name}</a>'
				),
				indicator="green",
				alert=True
			)
			return {"doctype": "Sales Invoice", "name": invoice.name}


	def _backfill_actual_tax_rate(self, invoice):
		"""Cosmetic-only fix: charge_type='Actual' tax rows don't derive `rate`
		from anything, so ERPNext leaves it at 0. Must run AFTER insert()/submit(),
		via direct db.set_value, because ERPNext's own calculate_taxes_and_totals()
		(triggered during insert()) would otherwise overwrite any rate we set
		in-memory before that point. Does not touch tax_amount or GL entries —
		purely updates the displayed percentage.
		"""
		net_total = flt(invoice.net_total)
		if not net_total:
			return
		for t in invoice.get("taxes") or []:
			if t.charge_type == "Actual" and flt(t.tax_amount) > 0:
				rate = flt(flt(t.tax_amount) / net_total * 100, 2)
				frappe.db.set_value(t.doctype, t.name, "rate", rate)

@frappe.whitelist()
def make_invoice(docname):
	"""Returns the mapped Purchase Invoice or Sales Invoice doc as dict for client-side routing/preview."""
	doc = frappe.get_doc("Accounting Entry", docname)
	if doc.tax_type == "Inward":
		invoice = doc.make_purchase_invoice()
	else:
		invoice = doc.make_sales_invoice()
	return invoice.as_dict()
