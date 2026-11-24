"""State history of each log, read from the State Change table the Progress app fills."""
from collections import defaultdict

import frappe

from custom_addons.custom_addons.page.po_amendment_insights.filters import LOG


def for_scope(scope_query, L):
	"""History rows of all logs inside the scope, grouped by log name, oldest first."""
	SC, I = frappe.qb.DocType("State Change"), frappe.qb.DocType("State Change Items")
	rows = (
		frappe.qb.from_(I).join(SC).on(I.parent == SC.name)
		.select(SC.document_name, I.workflow_state, I.modification_time, I.username)
		.where(SC.doctype_name == LOG)
		.where(SC.document_name.isin(scope_query.select(L.name)))
		.orderby(SC.document_name).orderby(I.idx)
		.run(as_dict=True)
	)
	return _group(rows)


def for_log(name):
	return for_names([name]).get(name, [])


def for_names(names):
	if not names:
		return {}
	SC, I = frappe.qb.DocType("State Change"), frappe.qb.DocType("State Change Items")
	rows = (
		frappe.qb.from_(I).join(SC).on(I.parent == SC.name)
		.select(SC.document_name, I.workflow_state, I.modification_time, I.username)
		.where(SC.doctype_name == LOG).where(SC.document_name.isin(list(names)))
		.orderby(SC.document_name).orderby(I.idx)
		.run(as_dict=True)
	)
	return _group(rows)


def _group(rows):
	out = defaultdict(list)
	for r in rows:
		out[r.document_name].append(r)
	return out
