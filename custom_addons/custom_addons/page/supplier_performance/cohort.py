"""Which suppliers the report shows, after the report-wide filters and user permissions."""
import frappe
from frappe.utils.nestedset import get_descendants_of

from custom_addons.custom_addons.page.supplier_performance.filters import month_range
from custom_addons.custom_addons.page.supplier_performance.scope import allowed_suppliers


def suppliers(f, active):
	"""Supplier rows (name, supplier_name, supplier_group) sorted by name.

	`active` is the set of suppliers with data. With include_inactive, enabled suppliers
	without data are listed too (as N/A). A selected supplier is always listed.
	"""
	names = set(active)
	if f.supplier:
		names = {f.supplier}
	elif f.include_inactive:
		names |= set(frappe.get_all("Supplier", filters={"disabled": 0}, pluck="name"))
	if f.item or f.item_group:
		names &= _dealt_in(f)
	allowed = allowed_suppliers()
	if allowed is not None:
		names &= allowed
	if not names:
		return []
	filters = {"name": ["in", list(names)]}
	if f.supplier_group:
		filters["supplier_group"] = f.supplier_group
	return frappe.get_all(
		"Supplier", filters=filters, fields=["name", "supplier_name", "supplier_group"], order_by="supplier_name asc, name asc"
	)


def _dealt_in(f):
	"""Suppliers with a PO line for the item / item group in the 12-month window."""
	start, end = month_range(f.months)
	conditions, values = [], {"company": f.company, "start": start, "end": end}
	if f.item:
		conditions.append("poi.item_code = %(item)s")
		values["item"] = f.item
	if f.item_group:
		conditions.append("poi.item_group in %(groups)s")
		values["groups"] = [f.item_group, *get_descendants_of("Item Group", f.item_group)]
	rows = frappe.db.sql(
		f"""
		select distinct po.supplier
		from `tabPurchase Order Item` poi
		join `tabPurchase Order` po on po.name = poi.parent
		where po.docstatus = 1 and po.company = %(company)s
			and po.transaction_date between %(start)s and %(end)s
			and {" and ".join(conditions)}
		""",
		values,
	)
	return {r[0] for r in rows}
