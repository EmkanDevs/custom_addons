"""Sample values for the Supplier Scorecard Settings. The client replaces them with approved limits."""

# criterion, label, short label, weight, data source, better when, unit, limits for ratings 5/4/3/2
CRITERIA = [
        ("Delivery", "Delivery / Lead Time", "Delivery / Lead time", 20, "Delivery", "Higher", "% of due quantity received on time", (95, 85, 70, 50)),
        ("Quality", "Quality & Defect Rate", "Quality & defects", 25, "Quality", "Higher", "% of received quantity accepted", (99, 97, 93, 85)),
        ("Price", "Price / Commercial", "Price / Commercial", 20, "Price", "Lower", "% premium above benchmark", (0, 5, 10, 20)),
        ("HSE", "HSE & Compliance", "HSE & compliance", 5, "No source", "Higher", "", None),
        ("Responsiveness", "Responsiveness & Communication", "Responsiveness", 10, "Response", "Lower", "average days to quote", (2, 5, 7, 10)),
        ("Documentation", "Documentation Accuracy", "Documentation", 10, "No source", "Higher", "", None),
        ("Payment Terms", "Payment Terms & Flexibility", "Payment terms", 5, "Payment Terms", "Higher", "agreed credit days", (60, 45, 30, 15)),
        ("Compliance", "Compliance", "Compliance", 5, "No source", "Higher", "", None),
]

# from overall %, band, colour, needs attention, action
BANDS = [
        (90, "Excellent", "green", 0, "Preferred vendor. Prioritize for long-term agreements / higher order volumes."),
        (75, "Good", "blue", 0, "Reliable. Continue standard monitoring."),
        (60, "Average", "amber", 1, "Needs improvement. Issue a formal improvement plan."),
        (40, "Poor", "orange", 1, "Corrective action. Reduce reliance and increase inspection / oversight."),
        (0, "Critical", "red", 1, "Consider suspension or termination from the approved vendor list, subject to review."),
]


def apply_defaults(doc):
        """Replace every setting on the document with the sample values."""
        doc.update({"max_rating": 5, "weak_rating": 3})
        doc.set("criteria", [])
        doc.set("rating_rules", [])
        for name, label, column, weight, source, direction, unit, limits in CRITERIA:
                doc.append("criteria", {"enabled": 1, "criterion": name, "label": label, "column_label": column,
                        "weight": weight, "provider": source, "direction": direction, "unit": unit})
                for rating, limit in zip((5, 4, 3, 2), limits or ()):
                        doc.append("rating_rules", {"criterion": name, "rating": rating, "threshold": limit})
        doc.set("bands", [])
        for lower, name, color, attention, action in BANDS:
                doc.append("bands", {"from_score": lower, "band": name, "color": color, "needs_attention": attention, "action": action})
