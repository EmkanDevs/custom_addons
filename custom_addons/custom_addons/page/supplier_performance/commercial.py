"""Price and Payment Terms metrics. All rates are net, in company currency, per stock unit."""
from collections import defaultdict

import frappe
from frappe.utils import add_days, flt, getdate

from custom_addons.custom_addons.page.supplier_performance.metric import MetricSet

def price(ctx):
	builders = {"lowest": _lowest_quote, "previous": _previous_purchase}
	if ctx.rules.price_benchmark not in builders:
		return MetricSet("Purchase Order", "No approved budget rates set up")
	return builders[ctx.rules.price_benchmark](ctx)


def terms(ctx):
	"""Per PO: credit days weighted by each payment portion. Rows without a named
	payment term are the system default schedule, not an agreed term, so they are skipped."""
	metric = MetricSet("Purchase Order", "No agreed payment terms on POs in this month")
	rows = frappe.db.sql(
		"""
		select po.supplier, po.name, po.transaction_date, ps.invoice_portion, ps.credit_days, ps.credit_months
		from `tabPayment Schedule` ps
		join `tabPurchase Order` po on po.name = ps.parent and ps.parenttype = 'Purchase Order'
		where po.docstatus = 1 and po.company = %(company)s and ifnull(ps.payment_term, '') != ''
			and po.transaction_date between %(start)s and %(end)s
		""",
		ctx,
		as_dict=True,
	)
	orders = defaultdict(list)
	for row in rows:
		orders[(row.supplier, row.name, row.transaction_date)].append(row)
	for (supplier, name, date), parts in orders.items():
		portion = sum(flt(p.invoice_portion) for p in parts)
		if portion > 0:
			days = sum(flt(p.invoice_portion) * (flt(p.credit_days) + 30 * flt(p.credit_months)) for p in parts)
			metric.add(supplier, date, days / portion, name)
	return metric


def _lowest_quote(ctx):
	"""Per RFQ item: the supplier's rate against the lowest valid quote of all suppliers.
	Needs at least two quoting suppliers; zero rates are not valid quotes."""
	metric = MetricSet("Supplier Quotation", "No compared quotations in this month")
	quotes = defaultdict(dict)  # rfq item -> supplier -> (rate, quotation, date)
	for row in _quotes(ctx):
		best = quotes[row.rfq_item].get(row.supplier)
		if flt(row.rate) > 0 and (not best or row.rate < best[0]):
			quotes[row.rfq_item][row.supplier] = (flt(row.rate), row.name, row.transaction_date)
	start = getdate(ctx.start)
	for by_supplier in quotes.values():
		if len(by_supplier) < 2:
			continue
		lowest = min(rate for rate, _, _ in by_supplier.values())
		for supplier, (rate, name, date) in by_supplier.items():
			if getdate(date) >= start:
				metric.add(supplier, date, 100 * (rate / lowest - 1), name)
	return metric


def _previous_purchase(ctx):
	"""Per PO line: the rate against the item's last purchase on an earlier PO (any supplier)."""
	metric = MetricSet("Purchase Order", "No earlier purchase of these items")
	last = {}
	start = getdate(ctx.start)
	for row in _po_rates(ctx):
		prev = last.get(row.item_code)
		if prev and prev[1] != row.name and prev[0] > 0 and row.rate > 0 and getdate(row.transaction_date) >= start:
			metric.add(row.supplier, row.transaction_date, 100 * (flt(row.rate) / prev[0] - 1), row.name)
		if flt(row.rate) > 0:
			last[row.item_code] = (flt(row.rate), row.name)
	return metric


def _quotes(ctx):
	return frappe.db.sql(
		"""
		select sq.supplier, sq.name, sq.transaction_date, sqi.request_for_quotation_item as rfq_item,
			sqi.base_net_rate / ifnull(nullif(sqi.conversion_factor, 0), 1) as rate
		from `tabSupplier Quotation Item` sqi
		join `tabSupplier Quotation` sq on sq.name = sqi.parent
		where sq.docstatus = 1 and sq.company = %(company)s and ifnull(sqi.request_for_quotation_item, '') != ''
			and sq.transaction_date between %(from)s and %(end)s
		""",
		{**ctx, "from": add_days(ctx.start, -ctx.rules.quote_lookback_days)},
		as_dict=True,
	)


def _po_rates(ctx):
	return frappe.db.sql(
		"""
		select po.supplier, po.name, po.transaction_date, poi.item_code,
			poi.base_net_rate / ifnull(nullif(poi.conversion_factor, 0), 1) as rate
		from `tabPurchase Order Item` poi
		join `tabPurchase Order` po on po.name = poi.parent
		where po.docstatus = 1 and po.company = %(company)s and po.transaction_date <= %(end)s
		order by po.transaction_date, po.creation, poi.idx
		""",
		ctx,
		as_dict=True,
	)
