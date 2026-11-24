"""Overview tab: six cards and four charts."""
import frappe
from frappe.query_builder.functions import Avg, Count, IfNull, Sum
from frappe.utils import flt, add_months, getdate
from pypika import Order

from custom_addons.custom_addons.page.po_amendment_insights import approvals
from custom_addons.custom_addons.page.po_amendment_insights.filters import (
	CLOSED_STATES, PENDING_STATES, MonthOf, comparable_sum, count_case, scoped, state_col,
)


def build(f):
	return {
		"cards": cards(f),
		"implementation": implementation(f),
		"trend": trend(f),
		"types": by_type(f),
		"reasons": by_reason(f),
	}


def cards(f):
	L, q = scoped(f)
	state = state_col(L)
	row = q.select(
		Count(L.name).as_("total"),
		count_case(state.notin(CLOSED_STATES)).as_("open"),
		count_case(state.isin(PENDING_STATES)).as_("pending"),
		comparable_sum(L).as_("net"),
		count_case((L.comparison_value_status == "Comparable") & (L.total_value_difference > 0)).as_("increased"),
		count_case((L.comparison_value_status == "Comparable") & (L.total_value_difference < 0)).as_("reduced"),
		Avg(L.po_date_gap_days).as_("gap"),
	).run(as_dict=True)[0]
	L2, q2 = scoped(f)
	benefit = q2.select(Sum(L2.rate_benefit)).where(L2.rate_benefit_status == "Complete").run()[0][0]
	slowest = approvals.slowest_gate(f)
	return {
		"total": row.total or 0,
		"open": int(row.open or 0),
		"pending": int(row.pending or 0),
		"slowest_gate": slowest,
		"net_value": flt(row.net),
		"increased": int(row.increased or 0),
		"reduced": int(row.reduced or 0),
		"rate_benefit": flt(benefit),
		"avg_gap_days": flt(row.gap, 1),
	}


def implementation(f):
	L, q = scoped(f)
	col = IfNull(L.implementation_status, "Under Review")
	return q.select(col.as_("status"), Count(L.name).as_("count")).groupby(col).orderby(Count(L.name), order=Order.desc).run(as_dict=True)


def trend(f):
	L, q = scoped(f)
	month = MonthOf(L.log_date, "%Y-%m")
	rows = q.select(month.as_("month"), Count(L.name).as_("count"), comparable_sum(L).as_("value")).groupby(month).run(as_dict=True)
	by_month = {r.month: r for r in rows}
	out, d, end = [], getdate(f["from_date"]).replace(day=1), getdate(f["to_date"])
	while d <= end:  # fill empty months so the chart has no gaps
		key = d.strftime("%Y-%m")
		r = by_month.get(key)
		out.append({"month": key, "count": r.count if r else 0, "value": flt(r.value) if r else 0})
		d = add_months(d, 1)
	return out


def by_type(f):
	L, q = scoped(f)
	col = IfNull(L.amendment_type, "Not set")
	return q.select(col.as_("type"), Count(L.name).as_("count"), comparable_sum(L).as_("value")).groupby(col).orderby(Count(L.name), order=Order.desc).run(as_dict=True)


def by_reason(f):
	L, q = scoped(f)
	col = IfNull(L.amendment_reason_category, "Not set")
	return q.select(col.as_("reason"), Count(L.name).as_("count")).groupby(col).orderby(Count(L.name), order=Order.desc).limit(15).run(as_dict=True)
