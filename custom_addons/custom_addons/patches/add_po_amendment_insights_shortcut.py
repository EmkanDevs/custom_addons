"""Link the PO Amendment Insights Dashboard in the Buying workspace."""
import json

import frappe

LABEL, PAGE = "PO Amendment Insights", "po-amendment-insights"


def execute():
	if not frappe.db.exists("Workspace", "Buying"):
		return
	ws = frappe.get_doc("Workspace", "Buying")
	if any(s.link_to == PAGE for s in ws.shortcuts):
		return
	ws.append("shortcuts", {"label": LABEL, "type": "Page", "link_to": PAGE})
	ws.content = _with_block(ws.content)
	ws.save(ignore_permissions=True)


def _with_block(content):
	blocks = json.loads(content or "[]")
	block = {"id": "poiInsights1", "type": "shortcut", "data": {"shortcut_name": LABEL, "col": 3}}
	# Put it after the last shortcut so it sits with the others
	last = max((i for i, b in enumerate(blocks) if b.get("type") == "shortcut"), default=len(blocks) - 1)
	blocks.insert(last + 1, block)
	return json.dumps(blocks)
