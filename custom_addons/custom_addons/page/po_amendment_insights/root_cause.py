"""Root Cause tab (Dashboard Manager only): what changes, who asks, which suppliers."""
import frappe
from frappe.query_builder.functions import Count, IfNull, Max
from frappe.utils import flt
from pypika import Order

from custom_addons.custom_addons.page.po_amendment_insights.filters import comparable_sum, count_case, scoped

# Always different between a cancelled and a submitted PO, so they say nothing
IGNORED_FIELDS = ("PO Number", "Document Status")


def build(f, limit=10, offset=0):
	return {
		"fields": changed_fields(f),
		"departments": by_department(f),
		"requesters": by_requester(f),
		"suppliers": by_supplier(f),
		"impact": impact_list(f, limit, offset),
	}


def changed_fields(f):
	L, scope_q = scoped(f)
	H = frappe.qb.DocType("PO Amendment Header Comparison")
	return (
		frappe.qb.from_(H).select(H.field_label.as_("field"), Count(H.parent).distinct().as_("count"))
		.where(H.parenttype == "PO Amendment Log").where(H.is_different == 1)
		.where(H.field_label.notin(IGNORED_FIELDS)).where(H.parent.isin(scope_q.select(L.name)))
		.groupby(H.field_label).orderby(Count(H.parent).distinct(), order=Order.desc).limit(10).run(as_dict=True)
	)


def by_department(f):
	L, q = scoped(f)
	col = IfNull(L.requesting_department, "Not set")
	return q.select(col.as_("department"), Count(L.name).as_("count"), comparable_sum(L).as_("value")).groupby(col).orderby(Count(L.name), order=Order.desc).run(as_dict=True)


def by_requester(f):
	L, q = scoped(f)
	col = IfNull(L.requested_by, "Not set")
	rows = q.select(col.as_("user"), Max(L.requesting_department).as_("department"), Count(L.name).as_("count"), comparable_sum(L).as_("value")).groupby(col).orderby(Count(L.name), order=Order.desc).limit(200).run(as_dict=True)
	names = dict(frappe.get_all("User", filters={"name": ["in", [r.user for r in rows] or [""]]}, fields=["name", "full_name"], as_list=True))
	for r in rows:
		r["full_name"] = names.get(r.user) or r.user
	return rows


def by_supplier(f):
	L, q = scoped(f)
	rows = (
		q.select(
			L.original_supplier.as_("supplier"), Count(L.name).as_("count"),
			count_case(L.original_supplier != L.replacement_supplier).as_("changed"),
			comparable_sum(L).as_("value"),
		)
		.where(L.original_supplier.isnotnull()).groupby(L.original_supplier)
		.orderby(Count(L.name), order=Order.desc).limit(10).run(as_dict=True)
	)
	names = dict(frappe.get_all("Supplier", filters={"name": ["in", [r.supplier for r in rows] or [""]]}, fields=["name", "supplier_name"], as_list=True))
	for r in rows:
		r["supplier_name"] = names.get(r.supplier) or r.supplier
		r["changed"] = int(r.changed or 0)
	return rows


def impact_list(f, limit, offset):
	L, q = scoped(f)
	if f.get("only_with_action"):
		q = q.where(L.corrective__preventive_action.isnotnull()).where(L.corrective__preventive_action != "")
	total = q.select(Count(L.name)).run()[0][0]
	rows = (
		q.select(L.name, L.log_date, L.amendment_type, L.amendment_reason_category, L.total_value_difference, L.comparison_value_status, L.business_impact, L.risk__impact_assessment, L.corrective__preventive_action)
		.orderby(L.log_date, order=Order.desc).orderby(L.name, order=Order.desc).limit(limit).offset(offset).run(as_dict=True)
	)
	for r in rows:
		r["value"] = r.total_value_difference if r.comparison_value_status == "Comparable" else None
	return {"rows": rows, "total": total}
