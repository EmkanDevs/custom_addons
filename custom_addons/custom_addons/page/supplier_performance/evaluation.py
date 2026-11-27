"""Monthly evaluation of every supplier for the window that ends with the selected month."""
import hashlib

import frappe
from frappe.utils import today

from custom_addons.custom_addons.page.supplier_performance import commercial, receipts, responsiveness, settings
from custom_addons.custom_addons.page.supplier_performance.filters import month_range
from custom_addons.custom_addons.page.supplier_performance.scoring import Scorer

PROVIDERS = {
	"delivery": receipts.delivery,
	"quality": receipts.quality,
	"price": commercial.price,
	"response": responsiveness.response,
	"terms": commercial.terms,
}


class Evaluation:
	def __init__(self, f):
		self.f = f
		self.settings = settings.get()
		self.criteria = self.settings.criteria
		self.metrics = _cached_metrics(self.settings, f.company, f.months)
		self.scorer = Scorer(self.settings, self.metrics)

	def active(self, month=None):
		"""Suppliers with at least one measured metric in the month (or the whole window)."""
		found = set()
		for metric in self.metrics.values():
			found |= metric.suppliers(month)
		return found

	def result(self, supplier, month=None):
		return self.scorer.result(supplier, month or self.f.month)

	def detail(self, supplier):
		return self.scorer.detail(supplier, self.f.month)


def _cached_metrics(rules, company, months):
	"""Source queries are the slow part, so share them for a few minutes per company and window."""
	start, end = month_range(months)
	signature = hashlib.md5(repr(rules.metric_signature).encode()).hexdigest()[:8]
	key = f"supplier_performance:{company}:{start}:{end}:{today()}:{signature}"
	metrics = frappe.cache.get_value(key)
	if metrics is None:
		ctx = frappe._dict(company=company, start=start, end=end, today=today(), rules=rules)
		metrics = {name: build(ctx) for name, build in PROVIDERS.items()}
		frappe.cache.set_value(key, metrics, expires_in_sec=rules.cache_seconds)
	return metrics
