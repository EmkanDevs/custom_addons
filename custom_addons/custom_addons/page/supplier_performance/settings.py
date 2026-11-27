"""The dashboard's rules, read from the Supplier Scorecard Settings document."""
import frappe
from frappe import _
from frappe.utils import cint, flt

# Data Source choice -> metric provider key. Providers are code; which criterion uses which is a setting.
PROVIDER_KEYS = {
        "Delivery": "delivery", "Quality": "quality", "Price": "price",
        "Response": "response", "Payment Terms": "terms",
}

# Standard technical constants (no need to clutter business settings)
PRICE_BENCHMARK = "lowest"
QUOTE_LOOKBACK_DAYS = 90
RESPONSE_DEADLINE_DAYS = 7
UNANSWERED_DAYS = 15
NO_SOURCE_REASON = "No source records available yet"
TREND_MONTHS = 12
MONTH_OPTIONS = 24
MAX_EVIDENCE_DOCS = 15
CACHE_SECONDS = 600

# Absorbs float noise so a value that sits exactly on a limit gets that limit's rating.
EPSILON = 1e-9


def get():
        """One snapshot of the settings. frappe.get_cached_doc is refreshed when the settings are saved."""
        doc = frappe.get_cached_doc("Supplier Scorecard Settings")
        if not doc.criteria:
                frappe.throw(_("Supplier Scorecard Settings are empty. Open the settings and use Load Sample Values."))
        return _Settings(doc)


class Criterion:
        def __init__(self, row, rules):
                self.name, self.label, self.column = row.criterion, row.label, row.column_label or row.label
                self.key = frappe.scrub(row.criterion)
                self.provider = PROVIDER_KEYS.get(row.provider)
                self.unit, self.weight = row.unit or "", flt(row.weight)
                self.higher = row.direction != "Lower"
                self.rules = sorted(rules, reverse=True)  # (rating, limit), best rating first

        def rate(self, value):
                if value is None or not self.rules:
                        return None
                for rating, limit in self.rules:
                        passed = value + EPSILON >= limit if self.higher else value - EPSILON <= limit
                        if passed:
                                return rating
                return 1

        def as_dict(self):
                return {"key": self.key, "label": self.label, "column": self.column, "weight": self.weight, "unit": self.unit}


class _Settings:
        def __init__(self, doc):
                self.scale = cint(doc.max_rating)
                self.weak_rating = cint(doc.weak_rating)
                self.price_benchmark = PRICE_BENCHMARK
                self.quote_lookback_days = QUOTE_LOOKBACK_DAYS
                self.response_deadline_days = RESPONSE_DEADLINE_DAYS
                self.unanswered_days = UNANSWERED_DAYS
                self.no_source_reason = _(NO_SOURCE_REASON)
                self.trend_months = TREND_MONTHS
                self.month_options = MONTH_OPTIONS
                self.max_evidence_docs = MAX_EVIDENCE_DOCS
                self.cache_seconds = CACHE_SECONDS
                self.bands = sorted(
                        ({"from": flt(b.from_score), "name": b.band, "color": b.color, "attention": bool(b.needs_attention), "action": b.action}
                                for b in doc.bands),
                        key=lambda b: -b["from"],
                )
                rules = {}
                for r in doc.rating_rules:
                        rules.setdefault(r.criterion, []).append((cint(r.rating), flt(r.threshold)))
                self.criteria = [Criterion(c, rules.get(c.criterion, [])) for c in doc.criteria if c.enabled and flt(c.weight) > 0]
                # Metric values change only with these, so they are part of the cache key.
                self.metric_signature = (self.price_benchmark, self.quote_lookback_days, self.response_deadline_days, self.unanswered_days)

        def band(self, score):
                """(name, action) of the band a score falls in, or (None, None) without a score."""
                if score is None:
                        return None, None
                for b in self.bands:
                        if score >= b["from"]:
                                return b["name"], b["action"]
                return self.bands[-1]["name"], self.bands[-1]["action"]

        def band_info(self):
                return [{"name": b["name"], "color": b["color"], "from": b["from"], "attention": b["attention"]} for b in self.bands]
