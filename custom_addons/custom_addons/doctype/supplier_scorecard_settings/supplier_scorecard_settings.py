"""Settings of the Supplier Performance Dashboard: scale, weights, rating rules and standing bands."""
import frappe
from frappe import _
from frappe.model.document import Document

from custom_addons.custom_addons.doctype.supplier_scorecard_settings.defaults import apply_defaults


class SupplierScorecardSettings(Document):
        def validate(self):
                self.validate_scale()
                self.validate_criteria()
                self.validate_rules()
                self.validate_bands()

        @frappe.whitelist()
        def load_defaults(self):
                """Fill the form with the sample values. Nothing is saved until the user saves."""
                apply_defaults(self)
                return self.as_dict()

        def validate_scale(self):
                if not 2 <= self.max_rating <= 10:
                        frappe.throw(_("Highest Rating must be between 2 and 10."))
                if not 1 <= self.weak_rating <= self.max_rating:
                        frappe.throw(_("Weak Rating Limit must be between 1 and the Highest Rating."))

        def validate_criteria(self):
                names = [c.criterion for c in self.criteria]
                if len(set(names)) != len(names):
                        frappe.throw(_("A criterion is listed more than once."))
                enabled = [c for c in self.criteria if c.enabled]
                if not enabled:
                        frappe.throw(_("Enable at least one criterion."))
                total = sum(c.weight or 0 for c in enabled)
                if round(total, 6) != 100:
                        frappe.throw(_("Weights of enabled criteria must add up to 100%, not {0}%.").format(total))

        def validate_rules(self):
                by_criterion = {}
                for rule in self.rating_rules:
                        if not 2 <= rule.rating <= self.max_rating:
                                frappe.throw(_("Row {0}: rating must be between 2 and {1}.").format(rule.idx, self.max_rating))
                        by_criterion.setdefault(rule.criterion, []).append(rule)
                directions = {c.criterion: c.direction for c in self.criteria}
                for name, rules in by_criterion.items():
                        if name not in directions:
                                frappe.throw(_("Rating rule for {0}, which is not in the criteria table.").format(name))
                        self.check_order(name, directions[name], rules)

        def check_order(self, name, direction, rules):
                ratings = [r.rating for r in rules]
                if len(set(ratings)) != len(ratings):
                        frappe.throw(_("{0}: a rating has more than one rule.").format(name))
                ordered = sorted(rules, key=lambda r: -r.rating)
                for higher, lower in zip(ordered, ordered[1:]):
                        ok = higher.threshold > lower.threshold if direction == "Higher" else higher.threshold < lower.threshold
                        if not ok:
                                word = "higher" if direction == "Higher" else "lower"
                                frappe.throw(_("{0}: the limit for rating {1} must be {2} than the limit for rating {3}.").format(
                                        name, higher.rating, word, lower.rating))

        def validate_bands(self):
                if not self.bands:
                        frappe.throw(_("Add at least one standing band."))
                starts = [b.from_score for b in self.bands]
                if len(set(starts)) != len(starts):
                        frappe.throw(_("Two bands start at the same overall %."))
                if min(starts) != 0:
                        frappe.throw(_("One band must start at 0%, so every score has a band."))
