"""Delivery and Quality metrics from Purchase Orders and Purchase Receipts."""
import frappe
from frappe.utils import add_days, flt, getdate

from custom_addons.custom_addons.page.supplier_performance.metric import MetricSet


def delivery(ctx):
	"""Per due PO line: % of the ordered stock quantity received on or before the schedule date.

	A due line with no receipt counts as 0%, so missed deliveries do not disappear.
	Lines not yet due are left out. A closed PO only expects what was received.
	"""
	metric = MetricSet("Purchase Order", "No PO lines due in this month")
	for row in _due_lines(ctx):
		ordered = flt(row.ordered)
		if row.status == "Closed":
			ordered = min(ordered, flt(row.received))
		if ordered <= 0:
			continue
		on_time = min(flt(row.on_time), ordered)
		metric.add(row.supplier, row.schedule_date, 100 * on_time / ordered, row.po)
	return metric


def quality(ctx):
	"""Per receipt line: % of the received quantity accepted (same unit on both sides)."""
	metric = MetricSet("Purchase Receipt", "No receipts in this month")
	rows = frappe.db.sql(
		"""
		select pr.supplier, pr.name, pr.posting_date, pri.qty, pri.rejected_qty
		from `tabPurchase Receipt Item` pri
		join `tabPurchase Receipt` pr on pr.name = pri.parent
		where pr.docstatus = 1 and pr.is_return = 0 and pr.company = %(company)s
			and pr.posting_date between %(start)s and %(end)s
		""",
		ctx,
		as_dict=True,
	)
	for row in rows:
		received = flt(row.qty) + flt(row.rejected_qty)
		if received > 0:
			metric.add(row.supplier, row.posting_date, 100 * flt(row.qty) / received, row.name)
	return metric


def _due_lines(ctx):
	"""Stock lines due in the window and already past their schedule date."""
	due_end = min(getdate(ctx.end), getdate(add_days(ctx.today, -1)))
	receipt = """
		select coalesce(sum(pri.received_stock_qty), 0)
		from `tabPurchase Receipt Item` pri
		join `tabPurchase Receipt` pr on pr.name = pri.parent
		where pri.purchase_order_item = poi.name and pr.docstatus = 1 and pr.is_return = 0
	"""
	return frappe.db.sql(
		f"""
		select po.supplier, po.name as po, po.status, poi.schedule_date, poi.stock_qty as ordered,
			({receipt} and pr.posting_date <= poi.schedule_date) as on_time,
			({receipt}) as received
		from `tabPurchase Order Item` poi
		join `tabPurchase Order` po on po.name = poi.parent
		join `tabItem` item on item.name = poi.item_code
		where po.docstatus = 1 and po.company = %(company)s and item.is_stock_item = 1
			and ifnull(poi.delivered_by_supplier, 0) = 0
			and poi.schedule_date between %(start)s and %(due_end)s
		""",
		{**ctx, "due_end": due_end},
		as_dict=True,
	)
