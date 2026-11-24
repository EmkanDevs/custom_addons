"""Single source of truth: which Reasons for Change are allowed for each Amendment Type.
Used by the controller (server validation), the form (via get_amendment_reason_map) and the DocType JSON generator."""

REASON_MAP = {
	"Cancellation": ["Incorrect PO Data"],
	"Delivery Date": ["Delivery / Schedule Change"],
	"Delivery Terms": ["Delivery / Schedule Change"],
	"Item / Specification": ["Quality / Specification"],
	"Payment Terms": ["Price / Commercial Revision"],
	"Quantity": ["Quantity Revision", "Requester Change"],
	"Scope": ["Incorrect PO Data"],
	"Supplier Details": ["Emergency / Operational Requirement"],
	"Total Value": ["Budget Constraint", "Contractual / Regulatory Requirement"],
	"Unit Price": ["Price / Commercial Revision"],
	"Other": ["Other"],
}


def all_reasons():
	seen = []
	for reasons in REASON_MAP.values():
		for r in reasons:
			if r not in seen:
				seen.append(r)
	return seen
