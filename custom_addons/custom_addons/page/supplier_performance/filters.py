"""Parse and check the report filters sent by the page."""
import json
import re

import frappe
from frappe import _
from frappe.utils import add_months, get_first_day, get_last_day, getdate, today

from custom_addons.custom_addons.page.supplier_performance import settings

MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def parse(raw):
        data = json.loads(raw) if isinstance(raw, str) else (raw or {})
        month = data.get("month") or default_month()
        if not MONTH_RE.match(month):
                frappe.throw(_("Invalid evaluation month."))
        return frappe._dict(
                company=_company(data.get("company")),
                month=month,
                supplier=link("Supplier", data.get("supplier")),
                supplier_group=link("Supplier Group", data.get("supplier_group")),
                item_group=link("Item Group", data.get("item_group")),
                item=link("Item", data.get("item")),
                include_inactive=bool(data.get("include_inactive")),
                months=window(month),
        )


def default_month():
        """The current month."""
        return month_key(get_first_day(today()))


def window(month):
        """The months set in the settings that end with the selected month, oldest first."""
        count = max(1, getattr(settings.get(), "trend_months", 12) or 12)
        first = getdate(month + "-01")
        return [month_key(add_months(first, -i)) for i in range(count - 1, -1, -1)]


def month_range(months):
        if not months:
                first = get_first_day(today())
                return getdate(first), get_last_day(first)
        return getdate(months[0] + "-01"), get_last_day(months[-1] + "-01")


def month_key(date):
        return getdate(date).strftime("%Y-%m")


def _company(company):
        allowed = frappe.get_list("Company", pluck="name")
        company = company or frappe.defaults.get_user_default("Company") or (allowed[0] if allowed else None)
        if company not in allowed:
                frappe.throw(_("You are not permitted to view company {0}.").format(company), frappe.PermissionError)
        return company


def link(doctype, value):
        if not value:
                return None
        if not frappe.db.exists(doctype, value):
                frappe.throw(_("{0} {1} does not exist.").format(_(doctype), value))
        return value
