import hashlib
import json

import frappe
from frappe import _
from frappe.model import no_value_fields, table_fields
from frappe.model.document import Document
from frappe.utils import cint, cstr, flt, fmt_money, get_link_to_form, now_datetime, strip_html

# PENDING_STATES for workflow gates
PENDING_STATES = ("Pending Approval", "Pending Technical/Quality", "Pending Procurement", "Pending Finance")

from . import po_context
from .comparison_engine import compare_items, compare_mr

PO = "Purchase Order"
BUYER_ROLES = {"Buyer", "System Manager"}
DOCSTATUS_LABEL = {0: "Draft", 1: "Submitted", 2: "Cancelled"}
HASH_VERSION = 2

SNAPSHOT_TABLES = ["header_comparison", "item_comparison", "mr_references"]
SNAPSHOT_SCALARS = [
	"original_currency", "replacement_currency", "original_net_total", "replacement_net_total",
	"original_grand_total", "replacement_grand_total", "net_total_difference", "total_value_difference",
	"rate_benefit", "non_rate_value_change", "comparison_value_status", "rate_benefit_status",
	"items_added", "items_removed", "items_changed", "items_unresolved",
	"mr_comparison_status", "mr_comparison_summary", "comparison_hash",
]
# what the server generates and what the stored-vs-regenerated check covers
OUTPUT_FIELDS = SNAPSHOT_TABLES + SNAPSHOT_SCALARS
# fields only the server may write (client values are discarded on save)
SERVER_OWNED = SNAPSHOT_SCALARS + [
	"comparison_warnings", "comparison_taken_on", "comparison_taken_by", "snapshot_checksum", "comparison_stale",
	"prepared_by", "reviewed_by", "approver", "approval_datetime", "pending_since", "log_reference_no",
	"company", "original_supplier", "replacement_supplier", "budget_impact_currency", "project", "po_date_gap_days",
]
USER_FIELDS = [
	"log_date", "cancelled_po_number", "new_po_number", "requested_by", "requesting_department",
	"specification_change", "amendment_type", "other_amendment_type", "amendment_reason_category",
	"other_amendment_reason_category", "detailed_justification", "business_impact", "budget__cost_impact",
	"risk__impact_assessment", "corrective__preventive_action", "remarks", "mr_variance_explanation",
	"supporting_attachments", "supplier_notified_yesno", "supplier_acknowledgment_status",
	"supplier_acknowledgment_date", "closure_date",
]
# locked while pending at any approval gate (everything except the manager's decision fields)
LOCKED_WHEN_PENDING = USER_FIELDS + OUTPUT_FIELDS + ["company", "original_supplier", "replacement_supplier"]


class POAmendmentLog(Document):
	# Frappe refuses links to cancelled docs from a submittable doctype. The whole point of this log is
	# to reference a cancelled PO, so exempt only that field. Existence is validated separately.
	def get_invalid_links(self, is_submittable=False):
		invalid, cancelled = super().get_invalid_links(is_submittable)
		cancelled = [c for c in cancelled if c[0] != "cancelled_po_number"]
		return invalid, cancelled

	# ------------------------------------------------------------------ lifecycle
	def validate(self):
		self.protect_server_fields()
		self.mirror_workflow_state()
		if not self.log_reference_no and self.name:
			self.log_reference_no = self.name

		self.validate_po_pair()
		self.validate_reason_for_type()
		self.sync_po_header_fields()
		self.reset_snapshot_if_pos_changed()
		self.validate_duplicate()
		self.enforce_edit_rules()
		self.validate_approval_stage()
		self.stamp_review_details()

	def mirror_workflow_state(self):
		"""workflow_state is the live workflow value. workflow_status mirrors it for the older code and reports."""
		if self.workflow_state:
			self.workflow_status = self.workflow_state
		else:
			self.workflow_status = self.workflow_status or "Draft"
			self.workflow_state = self.workflow_status

	def before_submit(self):
		if self.workflow_status != "Approved":
			frappe.throw(_("Only an approved log can be submitted. Use the workflow actions."))
		self.validate_final_po_states()

	def before_cancel(self):
		if not cstr(self.cancellation_reason).strip():
			frappe.throw(_("Cancellation Reason is mandatory to cancel an approved log. Enter it and click Update first."))

	def on_cancel(self):
		self.add_comment("Comment", _("Cancelled by {0}: {1}").format(frappe.session.user, self.cancellation_reason))

	def on_update(self):
		before = self.get_doc_before_save()
		if before and before.workflow_status in PENDING_STATES and self.workflow_status in ("Draft", "Rejected"):
			label = _("Returned for correction") if self.workflow_status == "Draft" else _("Rejected")
			self.add_comment("Comment", _("{0} by {1}: {2}").format(label, frappe.session.user, self.approval_comments))

	def on_submit(self):
		self.add_comment("Comment", _("Approved by {0}").format(self.approver or frappe.session.user))

	# ------------------------------------------------------------------ server-owned data
	def protect_server_fields(self):
		"""Identity, approval and snapshot values are never taken from the client."""
		if self.flags.in_fetch:
			return
		if self.is_new():
			for f in SERVER_OWNED:
				self.set(f, None)
			for t in SNAPSHOT_TABLES:
				self.set(t, [])
			self.comparison_stale = 0
			self.prepared_by = frappe.session.user
			return
		before = self.get_doc_before_save()
		if not before:
			return
		for f in SERVER_OWNED:
			self.set(f, before.get(f))
		for t in SNAPSHOT_TABLES:
			self.set(t, [d.as_dict() for d in before.get(t)])

	# ------------------------------------------------------------------ PO pair rules
	def validate_po_pair(self):
		orig, repl = self.cancelled_po_number, self.new_po_number
		if not (orig and repl):
			return
		if orig == repl:
			frappe.throw(_("Original PO and Replacement PO must be different."))
		info = {}
		for po in (orig, repl):
			row = frappe.db.get_value(PO, po, ["company", "docstatus"], as_dict=True)
			if not row:
				frappe.throw(_("Purchase Order {0} does not exist.").format(po))
			info[po] = row
		if info[orig].company != info[repl].company:
			frappe.throw(_("Original PO ({0}) and Replacement PO ({1}) belong to different companies.").format(info[orig].company, info[repl].company))
		if info[orig].docstatus != 2:
			frappe.throw(_("Original PO {0} must be Cancelled.").format(orig))
		if info[repl].docstatus != 1:
			frappe.throw(_("Replacement PO {0} must be an Approved (submitted) Purchase Order.").format(repl))

	def validate_reason_for_type(self):
		if self.amendment_type and self.amendment_reason_category:
			if not _reason_allowed(self.amendment_reason_category, self.amendment_type):
				frappe.throw(_("Reason for Change '{0}' is not valid for Amendment Type '{1}'. Allowed: {2}").format(
					self.amendment_reason_category, self.amendment_type, ", ".join(_allowed_reasons(self.amendment_type)) or _("none")))

	def sync_po_header_fields(self):
		"""Company / suppliers / budget currency always come from the saved POs."""
		if self.cancelled_po_number:
			self.company, self.original_supplier = frappe.db.get_value(PO, self.cancelled_po_number, ["company", "supplier"])
			self.budget_impact_currency = frappe.get_cached_value("Company", self.company, "default_currency")
		if self.new_po_number:
			self.replacement_supplier = frappe.db.get_value(PO, self.new_po_number, "supplier")

	def reset_snapshot_if_pos_changed(self):
		before = self.get_doc_before_save()
		if before and (before.cancelled_po_number != self.cancelled_po_number or before.new_po_number != self.new_po_number):
			self.clear_snapshot()

	def validate_duplicate(self):
		if not (self.cancelled_po_number and self.new_po_number) or self.docstatus == 2 or self.workflow_status in ("Rejected", "Cancelled"):
			return
		# serialise concurrent creators of the same pair: lock the original PO row, then do a locking read
		frappe.db.get_value(PO, self.cancelled_po_number, "name", for_update=True)
		dup = frappe.db.sql(
			"""select name from `tabPO Amendment Log`
			where cancelled_po_number=%s and new_po_number=%s and docstatus<2
				and workflow_status not in ('Rejected', 'Cancelled') and name != %s
			limit 1 for update""",
			(self.cancelled_po_number, self.new_po_number, self.name or "__new__"),
		)
		if dup:
			frappe.throw(
				_("An active PO Amendment Log {0} already exists for this Original / Replacement PO pair.").format(get_link_to_form("PO Amendment Log", dup[0][0])),
				title=_("Duplicate Log"),
			)

	def enforce_edit_rules(self):
		if self.is_new() or self.docstatus != 0 or self.flags.in_fetch:
			return
		before = self.get_doc_before_save()
		if not before:
			return
		changed = [f for f in LOCKED_WHEN_PENDING if _fingerprint(before, [f]) != _fingerprint(self, [f])]
		if not changed:
			return
		if before.workflow_status in PENDING_STATES:
			frappe.throw(
				_("This log is locked while pending approval. Return it for correction to change: {0}").format(
					", ".join(_(self.meta.get_label(f)) for f in changed[:5])),
				title=_("Locked"),
			)
		if before.workflow_status == "Rejected":
			frappe.throw(_("A rejected log is final. Create a new log to correct it."), title=_("Locked"))
		if not (set(frappe.get_roles()) & BUYER_ROLES):
			frappe.throw(_("Only a Buyer can edit a Draft log."), frappe.PermissionError)

	# ------------------------------------------------------------------ send / approve checks
	def validate_approval_stage(self):
		if self.workflow_status not in (set(PENDING_STATES) | {"Approved"}):
			return
		if not cstr(self.amendment_reason_category).strip():
			frappe.throw(_("Reason for Change is mandatory before sending for approval."))
		if not _text(self.detailed_justification):
			frappe.throw(_("Detailed Justification is mandatory before sending for approval."))
		if not cstr(self.amendment_type).strip():
			frappe.throw(_("Amendment Type is mandatory before sending for approval."))
		if self.amendment_reason_category == "Other" and not _text(self.other_amendment_reason_category):
			frappe.throw(_("Please describe the 'Other' reason."))
		if self.amendment_type == "Other" and not _text(self.other_amendment_type):
			frappe.throw(_("Please describe the 'Other' amendment type."))
		if not (self.comparison_hash and self.item_comparison):
			frappe.throw(_("Click 'Fetch Comparison' to take the PO comparison before sending for approval."))
		if self.mr_comparison_status in ("Mismatch", "Missing") and not _text(self.mr_variance_explanation):
			frappe.throw(_("Material Request references are {0} between the two POs. Explain the variance in 'MR Variance Explanation'.").format(_(self.mr_comparison_status).lower()))
		if self.items_unresolved and not _text(self.detailed_justification):
			frappe.throw(_("Some repeated item lines could not be matched. Explain the scope in the Detailed Justification."))

		before = self.get_doc_before_save()
		if not before or before.workflow_status not in PENDING_STATES or self.workflow_status == "Approved":
			self.validate_final_po_states()
			self.verify_snapshot()

	def validate_final_po_states(self):
		ods = frappe.db.get_value(PO, self.cancelled_po_number, "docstatus")
		rds = frappe.db.get_value(PO, self.new_po_number, "docstatus")
		if ods != 2:
			frappe.throw(_("Original PO {0} must be cancelled before sending for / granting approval.").format(self.cancelled_po_number))
		if rds != 1:
			frappe.throw(_("Replacement PO {0} must be submitted before sending for / granting approval.").format(self.new_po_number))

	def verify_snapshot(self):
		"""Re-read both POs under lock, regenerate the output on the server and compare with what is stored."""
		lock_pos(self.cancelled_po_number, self.new_po_number)
		data = build_comparison(self.cancelled_po_number, self.new_po_number)
		if data["hash"] != self.comparison_hash:
			frappe.throw(
				_("A Purchase Order changed after the comparison was taken. Return the log for correction, click 'Fetch Comparison' and review the refreshed comparison."),
				title=_("Comparison Out of Date"),
			)
		expected = frappe.new_doc(self.doctype)
		expected.cancelled_po_number, expected.new_po_number = self.cancelled_po_number, self.new_po_number
		apply_comparison(expected, data)
		if _fingerprint(expected, OUTPUT_FIELDS) != _fingerprint(self, OUTPUT_FIELDS) or self.snapshot_checksum != snapshot_checksum(expected):
			frappe.throw(_("The stored comparison does not match the server-generated comparison. Click 'Fetch Comparison' again."), title=_("Comparison Modified"))

	def stamp_review_details(self):
		before = self.get_doc_before_save()
		prev = before.workflow_status if before else None
		state = self.workflow_status
		if state == prev:
			return
		if state in PENDING_STATES and prev not in PENDING_STATES:
			self.approver = self.approval_datetime = self.approval_comments = None
			self.pending_since = now_datetime()
		elif prev in PENDING_STATES and state in ("Approved", "Rejected", "Draft"):
			if state != "Approved" and not _text(self.approval_comments):
				frappe.throw(_("Approval Comments are mandatory when rejecting or returning a log for correction."))
			if state == "Approved" and self.prepared_by == frappe.session.user:
				frappe.throw(_("You prepared this log, so another Procurement Manager must approve it."), frappe.PermissionError)
			self.reviewed_by = frappe.session.user
			if state == "Approved":
				self.approver, self.approval_datetime = frappe.session.user, now_datetime()
			else:
				self.approver = self.approval_datetime = None
		elif prev == "Rejected" and state == "Draft":
			self.approver = self.approval_datetime = self.reviewed_by = None

	# ------------------------------------------------------------------ snapshot helpers
	def clear_snapshot(self):
		for t in SNAPSHOT_TABLES:
			self.set(t, [])
		for f in SNAPSHOT_SCALARS + ["comparison_warnings", "comparison_taken_on", "comparison_taken_by", "snapshot_checksum", "mr_variance_explanation"]:
			self.set(f, None)
		self.comparison_stale = 0


# ---------------------------------------------------------------------- whitelisted actions
@frappe.whitelist()
def fetch_comparison(name, original_po, replacement_po):
	"""Take / refresh the comparison snapshot for a saved Draft log. Never touches either PO."""
	doc = frappe.get_doc("PO Amendment Log", name)
	doc.check_permission("write")
	if doc.docstatus != 0 or (doc.workflow_status or "Draft") != "Draft":
		frappe.throw(_("The comparison can only be fetched while the log is in Draft."))
	if (doc.cancelled_po_number, doc.new_po_number) != (original_po, replacement_po):
		frappe.throw(_("The PO selection changed. Save the log and fetch again."))
	if not (doc.cancelled_po_number and doc.new_po_number):
		frappe.throw(_("Select both the Original PO and the Replacement PO first."))
	doc.validate_po_pair()
	for po in (doc.cancelled_po_number, doc.new_po_number):
		frappe.has_permission(PO, "read", doc=po, throw=True)

	lock_pos(doc.cancelled_po_number, doc.new_po_number)
	data = build_comparison(doc.cancelled_po_number, doc.new_po_number)
	if build_comparison(doc.cancelled_po_number, doc.new_po_number)["hash"] != data["hash"]:
		frappe.throw(_("A Purchase Order changed while the comparison was being prepared. Please try again."))

	doc.flags.in_fetch = True
	apply_comparison(doc, data)
	po_context.apply(doc)
	doc.comparison_taken_on = now_datetime()
	doc.comparison_taken_by = frappe.session.user
	doc.comparison_stale = 0
	doc.snapshot_checksum = snapshot_checksum(doc)
	conflict = _conflicting_logs(doc)
	if conflict:
		doc.comparison_warnings = ((doc.comparison_warnings or "") + "\n" + conflict).strip()
	doc.save()  # one transaction: any failure rolls back the whole refresh
	return {"warnings": [w for w in (doc.comparison_warnings or "").split("\n") if w], "mr_status": doc.mr_comparison_status}


def _allowed_reasons(amendment_type):
	return frappe.db.sql_list(
		"""select c.name from `tabAmendment Reason Category` c
		where exists (select 1 from `tabAmendment Reason Type` t
			where t.parent = c.name and t.parenttype = 'Amendment Reason Category' and t.amendment_type = %s)
		order by c.name""", amendment_type)


def _reason_allowed(reason, amendment_type):
	return bool(frappe.db.exists("Amendment Reason Type",
		{"parent": reason, "parenttype": "Amendment Reason Category", "amendment_type": amendment_type}))


@frappe.whitelist()
def get_allowed_reasons(amendment_type):
	return _allowed_reasons(amendment_type) if amendment_type else []


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def reason_query(doctype, txt, searchfield, start, page_len, filters):
	"""Link-field search: only reasons configured for the selected Amendment Type."""
	amendment_type = (filters or {}).get("amendment_type")
	if not amendment_type:
		return []
	return frappe.db.sql(
		"""select c.name from `tabAmendment Reason Category` c
		where c.name like %(txt)s and exists (select 1 from `tabAmendment Reason Type` t
			where t.parent = c.name and t.parenttype = 'Amendment Reason Category' and t.amendment_type = %(type)s)
		order by c.name limit %(start)s, %(page_len)s""",
		{"txt": "%{0}%".format(txt), "type": amendment_type, "start": cint(start), "page_len": cint(page_len)})


@frappe.whitelist()
def get_related_logs(purchase_order):
	return frappe.get_list(
		"PO Amendment Log",
		or_filters=[["cancelled_po_number", "=", purchase_order], ["new_po_number", "=", purchase_order]],
		fields=["name", "workflow_status", "docstatus", "cancelled_po_number", "new_po_number"],
		order_by="creation desc",
		limit_page_length=20,
	)


def on_purchase_order_change(doc, method=None):
	"""Flag Pending Approval logs whose snapshot no longer matches the POs. Only the log is touched."""
	logs = frappe.get_all(
		"PO Amendment Log",
		filters={"docstatus": 0, "workflow_status": ["in", list(PENDING_STATES)]},
		or_filters=[["cancelled_po_number", "=", doc.name], ["new_po_number", "=", doc.name]],
		fields=["name", "cancelled_po_number", "new_po_number", "comparison_hash", "comparison_stale"],
	)
	for log in logs:
		try:
			stale = int(build_comparison(log.cancelled_po_number, log.new_po_number)["hash"] != log.comparison_hash)
		except Exception:
			frappe.log_error(title="PO Amendment Log stale check failed")
			continue
		if stale != cint(log.comparison_stale):
			frappe.db.set_value("PO Amendment Log", log.name, "comparison_stale", stale, update_modified=False)
			if stale:
				frappe.get_doc("PO Amendment Log", log.name).add_comment(
					"Comment", _("{0} changed after the comparison was taken. Return for correction and refresh the comparison.").format(doc.name))


# ---------------------------------------------------------------------- helpers
def po_state_field():
	"""Field that holds the Purchase Order's workflow state (from its active Workflow), or None."""
	return frappe.db.get_value("Workflow", {"document_type": PO, "is_active": 1}, "workflow_state_field")


def lock_pos(*names):
	for n in sorted(set(names)):
		frappe.db.get_value(PO, n, "name", for_update=True)


def _text(v):
	return strip_html(cstr(v)).strip()


def _norm(df, val):
	t = df.fieldtype
	if t in ("Float", "Currency", "Percent", "Int", "Check", "Long Int", "Rating"):
		return round(flt(val), 6)
	if t == "Datetime":
		return cstr(val)[:19]
	return cstr(val).strip()


def _fingerprint(doc, fieldnames):
	out = {}
	for fn in fieldnames:
		df = doc.meta.get_field(fn)
		val = doc.get(fn)
		if df.fieldtype in table_fields:
			cfields = [c for c in frappe.get_meta(df.options).fields if c.fieldtype not in no_value_fields]
			out[fn] = [[_norm(c, d.get(c.fieldname)) for c in cfields] for d in (val or [])]
		else:
			out[fn] = _norm(df, val)
	return out


def snapshot_checksum(doc):
	payload = _fingerprint(doc, OUTPUT_FIELDS + ["cancelled_po_number", "new_po_number"])
	return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def apply_comparison(doc, data):
	doc.set("header_comparison", data["header_rows"])
	doc.set("item_comparison", data["item_rows"])
	doc.set("mr_references", data["mr_rows"])
	for k, v in data["fields"].items():
		doc.set(k, v)
	doc.comparison_hash = data["hash"]


def _conflicting_logs(doc):
	rows = frappe.get_all(
		"PO Amendment Log",
		filters={"cancelled_po_number": doc.cancelled_po_number, "new_po_number": ["!=", doc.new_po_number],
			"docstatus": ["<", 2], "workflow_status": ["not in", ["Rejected", "Cancelled"]], "name": ["!=", doc.name]},
		fields=["name", "new_po_number"],
	)
	if not rows:
		return ""
	return _("Original PO {0} is already proposed as replaced by another PO in: {1}. Reviewers should confirm which replacement is correct.").format(
		doc.cancelled_po_number, ", ".join("{0} ({1})".format(r.name, r.new_po_number) for r in rows))


def _po_rows(po):
	return [
		{
			"po_detail": d.name, "item_code": d.item_code, "item_name": d.item_name,
			"item_group": d.item_group, "description": " ".join(strip_html(cstr(d.description)).split()), "uom": d.uom,
			"qty": flt(d.qty), "rate": flt(d.rate), "amount": flt(d.amount),
			"schedule_date": d.schedule_date, "warehouse": d.warehouse,
			"material_request": d.material_request, "material_request_item": d.material_request_item,
		}
		for d in po.items
	]


def _payment_schedule(po):
	parts = []
	for d in po.get("payment_schedule") or []:
		p = "{0}: {1}% / {2}".format(d.payment_term or d.description or _("Row {0}").format(d.idx), flt(d.invoice_portion, 4),
			fmt_money(d.payment_amount, currency=po.currency))
		if d.due_date:
			p += " due {0}".format(d.due_date)
		parts.append(p)
	return "; ".join(parts)


def _precisions():
	qty_prec = cint(frappe.get_system_settings("float_precision")) or 3
	amt_prec = cint(frappe.get_system_settings("currency_precision")) or 2
	return qty_prec, amt_prec


def build_comparison(original, replacement):
	"""Read-only. Returns header / item / MR rows, summary fields, warnings and the source-input hash."""
	o, r = frappe.get_doc(PO, original), frappe.get_doc(PO, replacement)
	same_cur = o.currency == r.currency
	qty_prec, amt_prec = _precisions()
	o_rows, r_rows = _po_rows(o), _po_rows(r)

	def money(po, v):
		return fmt_money(v, currency=po.currency)

	def has(po, f):
		return po.meta.has_field(f)

	terms = lambda po: _text(po.terms)
	specs = [  # label, original display, replacement display, original raw, replacement raw, kind
		("PO Number", o.name, r.name, o.name, r.name, "text"),
		("PO Date", o.transaction_date, r.transaction_date, cstr(o.transaction_date), cstr(r.transaction_date), "text"),
		("Supplier", "{0} ({1})".format(o.supplier, o.supplier_name), "{0} ({1})".format(r.supplier, r.supplier_name), o.supplier, r.supplier, "text"),
		("Company", o.company, r.company, o.company, r.company, "text"),
		("Currency", o.currency, r.currency, o.currency, r.currency, "text"),
		("Net Total", money(o, o.net_total), money(r, r.net_total), round(flt(o.net_total), amt_prec), round(flt(r.net_total), amt_prec), "money"),
		("Grand Total", money(o, o.grand_total), money(r, r.grand_total), round(flt(o.grand_total), amt_prec), round(flt(r.grand_total), amt_prec), "money"),
		("Payment Terms Template", o.payment_terms_template, r.payment_terms_template, cstr(o.payment_terms_template), cstr(r.payment_terms_template), "text"),
		("Payment Schedule", _payment_schedule(o), _payment_schedule(r), _payment_schedule(o), _payment_schedule(r), "text"),
		("Terms & Conditions Template", o.tc_name, r.tc_name, cstr(o.tc_name), cstr(r.tc_name), "text"),
		("Terms & Conditions", terms(o), terms(r), " ".join(terms(o).split()), " ".join(terms(r).split()), "text"),
		("Required By", o.schedule_date, r.schedule_date, cstr(o.schedule_date), cstr(r.schedule_date), "text"),
		("Document Status", DOCSTATUS_LABEL[o.docstatus], DOCSTATUS_LABEL[r.docstatus], o.docstatus, r.docstatus, "text"),
	]
	sf = po_state_field()
	if sf and has(o, sf) and has(r, sf):
		specs.append(("Workflow State", o.get(sf), r.get(sf), cstr(o.get(sf)), cstr(r.get(sf)), "text"))
	for f, label in (("incoterm", "Incoterm"), ("named_place", "Named Place"), ("set_warehouse", "Target Warehouse")):
		if has(o, f) and has(r, f):
			specs.append((label, o.get(f), r.get(f), cstr(o.get(f)), cstr(r.get(f)), "text"))

	header_rows, hash_hdr = [], []
	for label, ov, rv, oraw, rraw, kind in specs:
		diff = ""
		if kind == "money":
			diff = money(r, flt(rraw) - flt(oraw)) if same_cur else "N/A"
		header_rows.append({"field_label": label, "original_value": cstr(ov), "replacement_value": cstr(rv),
			"difference": diff, "is_different": int(oraw != rraw)})
		hash_hdr.append([label, cstr(oraw), cstr(rraw)])

	ic = compare_items(o_rows, r_rows, same_currency=same_cur, qty_prec=qty_prec, amt_prec=amt_prec)
	mr = compare_mr(o_rows, r_rows)
	mr_rows = [
		{"po_side": side, "material_request": x["material_request"], "material_request_item": x["material_request_item"],
			"item_code": x["item_code"], "item_name": x["item_name"], "item_group": x["item_group"], "po_detail": x["po_detail"]}
		for side, rows in (("Original", o_rows), ("Replacement", r_rows)) for x in rows
	]

	status = ic["rate_benefit_status"]
	net_diff = flt(r.net_total) - flt(o.net_total) if same_cur else 0
	total_diff = flt(r.grand_total) - flt(o.grand_total) if same_cur else 0
	benefit = ic["rate_benefit"] if same_cur else 0
	fields = {
		"original_currency": o.currency, "replacement_currency": r.currency,
		"original_net_total": flt(o.net_total), "replacement_net_total": flt(r.net_total),
		"original_grand_total": flt(o.grand_total), "replacement_grand_total": flt(r.grand_total),
		"comparison_value_status": "Comparable" if same_cur else "Currency Mismatch",
		"net_total_difference": net_diff, "total_value_difference": total_diff,
		"rate_benefit": benefit, "rate_benefit_status": status if same_cur else "Not Comparable",
		"non_rate_value_change": (total_diff + benefit) if (same_cur and status != "Not Comparable") else 0,
		"items_added": ic["items_added"], "items_removed": ic["items_removed"],
		"items_changed": ic["items_changed"], "items_unresolved": ic["items_unresolved"],
		"mr_comparison_status": mr["status"], "mr_comparison_summary": mr["summary"],
	}

	w = []
	if not same_cur:
		w.append(_("Currency changed from {0} to {1}. Both values are shown in their currencies. Monetary differences and rate benefit are not comparable (N/A). You may continue.").format(o.currency, r.currency))
	if ic["uom_diff_count"]:
		w.append(_("Purchase UOM changed on {0} row(s). Quantity and unit rate differences are not comparable (N/A). You may continue.").format(ic["uom_diff_count"]))
	if ic["items_unresolved"]:
		w.append(_("Repeated item lines could not be matched reliably ({0} source rows). Review the source rows and explain the scope in the justification.").format(ic["items_unresolved"]))
	if ic["spec_diff_count"]:
		w.append(_("{0} matched row(s) have a different specification / description.").format(ic["spec_diff_count"]))
	if ic["fallback_count"]:
		w.append(_("{0} row(s) were matched on a unique item code only (not on MR item). Please verify.").format(ic["fallback_count"]))
	if ic["missing_date_count"]:
		w.append(_("{0} matched row(s) have a missing delivery date; the delivery difference is N/A.").format(ic["missing_date_count"]))
	if mr["status"] in ("Mismatch", "Missing"):
		w.append(_("MR references differ or are missing. Explain the variance before sending for approval."))
	if mr["lineage_diff"] or ic["lineage_diff_count"]:
		w.append(_("The same MR documents are referenced but on different MR item rows (line-level lineage change)."))
	if same_cur and fields["rate_benefit_status"] != "Complete":
		w.append(_("Rate benefit coverage is {0}: only matched lines with the same item, UOM and currency are included.").format(fields["rate_benefit_status"]))
	if o.docstatus != 2:
		w.append(_("Original PO {0} is not cancelled yet. It must be cancelled before the log is sent for approval.").format(o.name))
	if r.docstatus != 1:
		w.append(_("Replacement PO {0} is not submitted yet. It must be submitted before the log is sent for approval.").format(r.name))
	fields["comparison_warnings"] = "\n".join(w)

	def item_key(x):
		return json.dumps([x["item_code"], x["uom"], round(x["qty"], qty_prec), round(x["rate"], qty_prec),
			round(x["amount"], amt_prec), cstr(x["schedule_date"]), cstr(x["warehouse"]), cstr(x["material_request"]),
			cstr(x["material_request_item"]), x["description"]])

	digest = hashlib.sha256(json.dumps({
		"v": HASH_VERSION, "o": o.name, "r": r.name, "hdr": hash_hdr,
		"io": sorted(item_key(x) for x in o_rows), "ir": sorted(item_key(x) for x in r_rows),
	}, sort_keys=True).encode()).hexdigest()

	return {"header_rows": header_rows, "item_rows": ic["rows"], "mr_rows": mr_rows, "fields": fields,
		"warnings": w, "hash": digest}