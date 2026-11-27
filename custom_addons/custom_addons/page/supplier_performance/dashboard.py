"""Build the dashboard data: ranked rows for the month, the monthly trend and history."""
from frappe.utils import getdate

from custom_addons.custom_addons.page.supplier_performance import cohort
from custom_addons.custom_addons.page.supplier_performance.evaluation import Evaluation
from custom_addons.custom_addons.page.supplier_performance.scoring import comment


def build(f):
	ev = Evaluation(f)
	rows = month_rows(ev, f)
	history = history_rows(ev, f)
	return {
		"month": f.month,
		"months": [{"key": m, "label": month_label(m), "short": month_label(m, short=True)} for m in f.months],
		"criteria": [c.as_dict() for c in ev.criteria],
		"scale": ev.settings.scale,
		"bands": ev.settings.band_info(),
		"rows": rows,
		"summary": summary(rows, ev.settings),
		"history": history,
		"trend": trend(history, f),
	}


def month_rows(ev, f):
	"""All suppliers in view for the selected month, each with a rank per comparison key."""
	rows = []
	for s in cohort.suppliers(f, ev.active(f.month)):
		result = ev.result(s.name)
		rows.append({**_identity(s), **result, "comment": comment(result, ev.settings)})
	keys = ["overall", *(c.key for c in ev.criteria)]
	for key in keys:
		_rank(rows, key)
	return rows


def history_rows(ev, f):
	"""Suppliers with data anywhere in the window, with their score per month (None = N/A)."""
	out = []
	for s in cohort.suppliers(f, ev.active()):
		months = [ev.result(s.name, m) for m in f.months]
		out.append({**_identity(s), "months": [{"score": r["score"], "weight": r["weight"], "band": r["band"]} for r in months]})
	return out


def summary(rows, settings):
	top = settings.bands[0]
	attention = [b["name"] for b in settings.bands if b["attention"]]
	evaluated = [r for r in rows if r["score"] is not None]
	return {
		"in_view": len(rows),
		"evaluated": len(evaluated),
		"average": _mean(r["score"] for r in evaluated),
		"average_weight": _mean(r["weight"] for r in evaluated),
		"top_band": {"name": top["name"], "from": top["from"]},
		"top_count": sum(1 for r in evaluated if r["band"] == top["name"]),
		"attention_bands": attention,
		"attention": sum(1 for r in evaluated if r["band"] in attention),
	}


def trend(history, f):
	"""One supplier's monthly scores, or the average of the suppliers in view. N/A stays a gap."""
	points = []
	for i, month in enumerate(f.months):
		scores = [h["months"][i] for h in history if h["months"][i]["score"] is not None]
		points.append({
			"label": month_label(month, short=True),
			"score": _mean(s["score"] for s in scores),
			"weight": _mean(s["weight"] for s in scores),
		})
	single = history[0]["supplier_name"] if f.supplier and history else None
	return {"points": points, "single": single}


def month_label(month, short=False):
	return getdate(month + "-01").strftime("%b %y" if short else "%B %Y")


def comparison_value(row, key):
	"""Ranks use the displayed value: overall to 1 decimal, criteria as whole ratings."""
	return row["score"] if key == "overall" else row["ratings"].get(key)


def _rank(rows, key):
	"""Competition ranking (1, 1, 3). Suppliers with no value get no rank."""
	values = sorted((v for v in (comparison_value(r, key) for r in rows) if v is not None), reverse=True)
	first = {}
	for i, v in enumerate(values):
		first.setdefault(v, i + 1)
	for r in rows:
		v = comparison_value(r, key)
		r.setdefault("ranks", {})[key] = first.get(v) if v is not None else None


def _identity(s):
	return {"supplier": s.name, "supplier_name": s.supplier_name or s.name, "supplier_group": s.supplier_group or ""}


def _mean(values):
	values = list(values)
	return round(sum(values) / len(values), 1) if values else None
