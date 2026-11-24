"""Filter parsing and the one scoped query every metric starts from."""
import json

import frappe
from frappe import _
from frappe.query_builder.functions import IfNull, Sum
from frappe.utils import getdate, nowdate
from pypika import CustomFunction
from pypika.terms import Case

from custom_addons.custom_addons.page.po_amendment_insights.constants import (  # noqa: F401
	CLOSED_STATES, GATE_STATES, PENDING_STATES,
)

LOG = "PO Amendment Log"
# The one place that names the state field the dashboard reads.
STATE_FIELD = "workflow_state"
MonthOf = CustomFunction("DATE_FORMAT", ["date", "fmt"])
EQUALS = ("project", "requested_by", "requesting_department", "amendment_type")


def parse(filters):
	"""Return a clean filter dict. Raises on a bad date range."""
	f = json.loads(filters) if isinstance(filters, str) else dict(filters or {})
	today = getdate(nowdate())
	f["from_date"] = getdate(f.get("from_date") or today.replace(month=1, day=1))
	f["to_date"] = getdate(f.get("to_date") or today)
	if f["from_date"] > f["to_date"]:
		frappe.throw(_("From date must be on or before To date"))
	return f


def doc():
	return frappe.qb.DocType(LOG)


def state_col(L):
	return IfNull(getattr(L, STATE_FIELD), "Draft")


def scoped(f):
	"""Logs inside the filters, cancelled ones excluded. Returns (table, query)."""
	L = doc()
	q = frappe.qb.from_(L).where(L.docstatus != 2).where(L.log_date >= f["from_date"]).where(L.log_date <= f["to_date"])
	for key in EQUALS:
		if f.get(key):
			q = q.where(getattr(L, key) == f[key])
	if f.get("workflow_state"):
		q = q.where(state_col(L) == f["workflow_state"])
	if f.get("supplier"):
		q = q.where((L.original_supplier == f["supplier"]) | (L.replacement_supplier == f["supplier"]))
	return L, q


def comparable_sum(L, field="total_value_difference"):
	"""Sum that skips logs whose two POs are in different currencies."""
	return Sum(Case().when(L.comparison_value_status == "Comparable", getattr(L, field)).else_(0))


def count_case(condition):
	return Sum(Case().when(condition, 1).else_(0))
