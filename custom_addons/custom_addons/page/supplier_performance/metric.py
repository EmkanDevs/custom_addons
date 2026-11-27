"""One measured metric: values per supplier and month, with the documents behind them."""
from collections import defaultdict

from frappe.utils import getdate


class MetricSet:
	"""Each source line adds one value. The monthly metric is the mean of its lines,
	so lines in different units (BAG, M/L, Nos) are never added together."""

	def __init__(self, doctype, na_reason="No transactions in this month"):
		self.doctype = doctype
		self.na_reason = na_reason
		self.lines = defaultdict(list)
		self.docs = defaultdict(set)

	def add(self, supplier, date, value, doc):
		key = (supplier, getdate(date).strftime("%Y-%m"))
		self.lines[key].append(float(value))
		self.docs[key].add(doc)

	def value(self, supplier, month):
		values = self.lines.get((supplier, month))
		return sum(values) / len(values) if values else None

	def evidence(self, supplier, month):
		key = (supplier, month)
		return {"count": len(self.lines.get(key, ())), "doctype": self.doctype, "docs": sorted(self.docs.get(key, ()))}

	def suppliers(self, month=None):
		return {s for s, m in self.lines if month is None or m == month}


class Unavailable(MetricSet):
	"""A criterion with no source records yet. Always N/A."""

	def add(self, *args):
		raise NotImplementedError
