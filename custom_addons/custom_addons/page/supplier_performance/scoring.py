"""Turn metrics into ratings and the overall score. The rating scale comes from the settings.

    points  = rating / scale * weight, for each criterion that has data
    overall = points / evaluated weight * 100
    weighted score = points / evaluated weight * scale

A criterion with no data is N/A and its weight is left out of the evaluated weight.
"""
from frappe import _


class Scorer:
	def __init__(self, settings, metrics):
		self.settings = settings
		self.criteria = settings.criteria
		self.metrics = metrics  # provider key -> MetricSet; a criterion without a provider has none

	def result(self, supplier, month):
		scale = self.settings.scale
		ratings, points, weight = {}, 0.0, 0.0
		for c in self.criteria:
			metric = self.metrics.get(c.provider)
			rating = c.rate(metric.value(supplier, month)) if metric else None
			ratings[c.key] = rating
			if rating is not None:
				points += rating / scale * c.weight
				weight += c.weight
		score = round(points / weight * 100, 1) if weight else None
		return {
			"ratings": ratings,
			"score": score,
			"weighted": round(points / weight * scale, 2) if weight else None,
			"weight": weight,
			"evaluated": sum(1 for r in ratings.values() if r is not None),
			"band": self.settings.band(score)[0],
		}

	def detail(self, supplier, month):
		"""Per criterion: metric, rating, weight, points and N/A reason or evidence."""
		rows = []
		for c in self.criteria:
			metric = self.metrics.get(c.provider)
			value = metric.value(supplier, month) if metric else None
			rating = c.rate(value)
			rows.append({
				**c.as_dict(),
				"value": None if value is None else round(value, 2),
				"rating": rating,
				"points": None if rating is None else round(rating / self.settings.scale * c.weight, 2),
				"reason": (metric.na_reason if metric else self.settings.no_source_reason) if rating is None else None,
				"evidence": metric.evidence(supplier, month) if metric and rating is not None else None,
			})
		return rows


def comment(result, settings):
	if result["score"] is None:
		return {"title": _("Not evaluated"), "text": _("No recorded activity to assess this month.")}
	weak = [c.label for c in settings.criteria if (result["ratings"].get(c.key) or 99) <= settings.weak_rating]
	title = _("Review {0}").format(", ".join(weak)) if weak else _("Maintain performance")
	return {"title": title, "text": _(settings.band(result["score"])[1] or "")}
