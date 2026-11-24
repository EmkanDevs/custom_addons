"""Approvals tab: gate health from State Change history, and the waiting list."""
import frappe
from frappe.query_builder.functions import Count
from frappe.utils import flt, get_datetime, now_datetime

from custom_addons.custom_addons.page.po_amendment_insights import history, scope
from custom_addons.custom_addons.page.po_amendment_insights.filters import GATE_STATES, scoped, state_col

# Draft is a gate too: how long buyers take to send a log
GATES = ("Draft",) + GATE_STATES
WARN_DAYS, ALERT_DAYS = 2, 5


def build(f, approver=None, limit=10, offset=0):
	gates = gate_stats(f)
	return {
		"gates": gates,
		"slowest_gate": _slowest(gates),
		"approved_total": _count_state(f, "Approved"),
		"rejected_total": _count_state(f, "Rejected"),
		"approvers": approver_options(),
		"waiting": waiting(f, approver, limit, offset),
	}


def gate_stats(f):
	pending = _pending_by_gate(f)
	L, q = scoped(f)
	approved, rejected, days = _walk_history(history.for_scope(q, L))
	return [
		{
			"state": g,
			"pending": pending.get(g, 0),
			"approved": approved.get(g, 0),
			"rejected": rejected.get(g, 0),
			"avg_days": flt(sum(days[g]) / len(days[g]), 1) if days.get(g) else None,
		}
		for g in GATES
	]


def slowest_gate(f):
	return _slowest(gate_stats(f))


def _slowest(gates):
	timed = [g for g in gates if g["avg_days"] is not None and g["state"] in GATE_STATES]
	return max(timed, key=lambda g: g["avg_days"])["state"] if timed else None


def _pending_by_gate(f):
	L, q = scoped(f)
	state = state_col(L)
	rows = q.select(state.as_("state"), Count(L.name).as_("n")).groupby(state).run(as_dict=True)
	return {r.state: r.n for r in rows}


def _count_state(f, name):
	return _pending_by_gate(f).get(name, 0)


def _walk_history(by_log):
	"""A stay ends when the next row exists. Logs with no history are left out (spec 8.4)."""
	approved, rejected, days = {}, {}, {g: [] for g in GATES}
	for rows in by_log.values():
		for i, row in enumerate(rows[:-1]):
			gate, nxt = row.workflow_state, rows[i + 1]
			if gate not in GATES:
				continue
			target = rejected if nxt.workflow_state == "Rejected" else approved
			target[gate] = target.get(gate, 0) + 1
			days[gate].append((get_datetime(nxt.modification_time) - get_datetime(row.modification_time)).total_seconds() / 86400)
	return approved, rejected, days


def approver_options():
	rows = frappe.get_all("Has Role", filters={"role": ["in", scope.APPROVER_ROLES], "parenttype": "User"}, pluck="parent", distinct=True)
	users = frappe.get_all("User", filters={"name": ["in", rows or [""]], "enabled": 1}, fields=["name", "full_name"], order_by="full_name")
	return users


def can_approve(state):
	role = scope.GATE_ROLES.get(state)
	if not role:
		return []
	names = frappe.get_all("Has Role", filters={"role": role, "parenttype": "User"}, pluck="parent")
	return frappe.get_all("User", filters={"name": ["in", names or [""]], "enabled": 1}, pluck="full_name", order_by="full_name")


def waiting(f, approver, limit, offset):
	L, q = scoped(f)
	states = _states_for(approver)
	rows = q.select(L.name, L.cancelled_po_number, L.original_supplier, L.total_value_difference, L.comparison_value_status, L.modified, state_col(L).as_("state")).where(state_col(L).isin(states)).run(as_dict=True)
	hist = history.for_names([r.name for r in rows])
	approvers = {s: can_approve(s) for s in states}
	now = now_datetime()
	for r in rows:
		entered = _entered(hist.get(r.name, []), r.state) or r.modified
		r["waiting_days"] = flt((now - get_datetime(entered)).total_seconds() / 86400, 1)
		r["can_approve"] = approvers[r.state]
		r["value"] = r.total_value_difference if r.comparison_value_status == "Comparable" else None
	rows.sort(key=lambda r: r["waiting_days"], reverse=True)
	overdue = sum(1 for r in rows if r["waiting_days"] > ALERT_DAYS)
	return {"rows": rows[offset: offset + limit], "total": len(rows), "overdue": overdue, "warn_days": WARN_DAYS, "alert_days": ALERT_DAYS}


def _states_for(approver):
	if not approver:
		return list(GATE_STATES)
	roles = set(frappe.get_roles(approver))
	return [s for s, role in scope.GATE_ROLES.items() if role in roles]


def _entered(rows, state):
	times = [r.modification_time for r in rows if r.workflow_state == state]
	return times[-1] if times else None
