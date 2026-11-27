"""Excel export of every supplier in view, regardless of page or chart selection."""
from frappe import _
from frappe.utils.xlsxutils import make_xlsx

from custom_addons.custom_addons.page.supplier_performance import dashboard

# Text starting with these can run as a formula in Excel.
FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def build(f, sort_key):
	data = dashboard.build(f)
	criteria = data["criteria"]
	keys = {"overall", *(c["key"] for c in criteria)}
	sort_key = sort_key if sort_key in keys else "overall"
	rows = sorted(data["rows"], key=lambda r: (r["ranks"][sort_key] is None, r["ranks"][sort_key] or 0, r["supplier_name"]))
	basis = _("Overall score") if sort_key == "overall" else next(c["label"] for c in criteria if c["key"] == sort_key)

	table = [[_("Month"), _("Rank basis"), _("Rank"), _("Supplier ID"), _("Supplier"), _("Supplier Type"),
		*[f"{c['label']} ({c['weight']:g}%)" for c in criteria],
		_("Weighted Score /{0}").format(data["scale"]), _("Overall %"), _("Rating Band"), _("Evaluated Weight %"), _("Comments / Action Required")]]
	for r in rows:
		table.append([_safe(v) for v in [
			dashboard.month_label(f.month), basis, _na(r["ranks"][sort_key]), r["supplier"], r["supplier_name"], r["supplier_group"],
			*[_na(r["ratings"].get(c["key"])) for c in criteria],
			_na(r["weighted"]), _na(r["score"]), r["band"] or "N/A", _na(r["weight"] or None),
			f"{r['comment']['title']}. {r['comment']['text']}",
		]])
	name = f"Supplier_Scorecard_{f.company}_{f.month}.xlsx".replace(" ", "_")
	return name, make_xlsx(table, _("Supplier Scorecard")).getvalue()


def _na(value):
	return "N/A" if value is None else value


def _safe(value):
	if isinstance(value, str) and value.startswith(FORMULA_START):
		return "'" + value
	return value
