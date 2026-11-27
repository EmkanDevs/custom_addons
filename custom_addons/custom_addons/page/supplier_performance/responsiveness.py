"""Responsiveness metric: days from an RFQ to the supplier's first quotation for it."""
import frappe
from frappe.utils import date_diff

from custom_addons.custom_addons.page.supplier_performance.metric import MetricSet


def response(ctx):
	"""One value per RFQ and supplier, so a multi-item RFQ counts once.

	No RFQ in the month gives N/A. An RFQ still unanswered after the deadline counts
	as the unanswered-days setting, so silence is never treated as a good response.
	An unanswered RFQ inside the deadline is still open and is left out.
	"""
	metric = MetricSet("Request for Quotation", "No RFQs sent in this month")
	for row in _requests(ctx):
		if row.answered:
			metric.add(row.supplier, row.rfq_date, max(0, date_diff(row.answered, row.rfq_date)), row.rfq)
		elif date_diff(ctx.today, row.rfq_date) > ctx.rules.response_deadline_days:
			metric.add(row.supplier, row.rfq_date, ctx.rules.unanswered_days, row.rfq)
	return metric


def _requests(ctx):
	return frappe.db.sql(
		"""
		select rs.supplier, rfq.name as rfq, rfq.transaction_date as rfq_date,
			(select min(sq.transaction_date)
				from `tabSupplier Quotation` sq
				join `tabSupplier Quotation Item` sqi on sqi.parent = sq.name
				where sq.docstatus = 1 and sq.supplier = rs.supplier
					and sqi.request_for_quotation = rfq.name) as answered
		from `tabRequest for Quotation Supplier` rs
		join `tabRequest for Quotation` rfq on rfq.name = rs.parent
		where rfq.docstatus = 1 and rfq.company = %(company)s
			and rfq.transaction_date between %(start)s and %(end)s
		group by rs.supplier, rfq.name
		""",
		ctx,
		as_dict=True,
	)
