const NA = __("N/A");
// Keep in step with PENDING_STATES in page/po_amendment_insights/constants.py
const PENDING_STATES = ["Pending Approval", "Pending Technical/Quality", "Pending Procurement", "Pending Finance"];

frappe.ui.form.on("PO Amendment Log", {
	setup(frm) {
		// Original PO: cancelled POs only
		frm.set_query("cancelled_po_number", () => {
			const f = { docstatus: 2 };
			if (frm.doc.new_po_number) f.name = ["!=", frm.doc.new_po_number];
			return { filters: f };
		});
		// Replacement PO: submitted (approved) POs only
		frm.set_query("new_po_number", () => {
			const f = { docstatus: 1 };
			if (frm.doc.cancelled_po_number) f.name = ["!=", frm.doc.cancelled_po_number];
			if (frm.doc.company) f.company = frm.doc.company;
			return { filters: f };
		});
		// Reason for Change: only reasons configured for the selected Amendment Type
		frm.set_query("amendment_reason_category", () => ({
			query: "custom_addons.custom_addons.doctype.po_amendment_log.po_amendment_log.reason_query",
			filters: { amendment_type: frm.doc.amendment_type },
		}));
		set_na_formatters(frm);
	},

	refresh(frm) {
		const state = frm.doc.workflow_status || "Draft";
		if (frm.doc.comparison_stale && frm.doc.docstatus === 0) {
			frm.dashboard.add_comment(
				__("A Purchase Order changed after this comparison was taken. Return the log for correction, click 'Fetch Comparison' and review the refreshed comparison."),
				"red", true);
		}
		if (frm.doc.mr_comparison_status && frm.doc.mr_comparison_status !== "Match" && frm.doc.docstatus === 0) {
			frm.dashboard.add_comment(
				__("Material Request references are {0} between the two POs. You can continue, but explain the variance in 'MR Variance Explanation'.", [__(frm.doc.mr_comparison_status).toLowerCase()]),
				"orange", true);
		}
		if (frm.doc.comparison_value_status === "Currency Mismatch") {
			frm.dashboard.add_comment(
				__("Currency differs between the POs: monetary differences and rate benefit are N/A. You can continue."), "orange", true);
		}

		// Pending at any gate: only the approver's comments are editable (the server enforces this too)
		if (PENDING_STATES.includes(state) && frm.doc.docstatus === 0) {
			const layout = ["Section Break", "Column Break", "Tab Break", "HTML", "Heading", "Button"];
			frm.meta.fields.forEach((df) => {
				if (df.fieldname !== "approval_comments" && !layout.includes(df.fieldtype)) {
					frm.set_df_property(df.fieldname, "read_only", 1);
				}
			});
		}
		show_na_in_summary(frm);
	},

	amendment_type(frm) { sync_reason_with_type(frm); },
	cancelled_po_number(frm) { po_changed(frm); },
	new_po_number(frm) { po_changed(frm); },

	async fetch_comparison_btn(frm) {
		if (!frm.doc.cancelled_po_number || !frm.doc.new_po_number) {
			frappe.msgprint(__("Select both the Original PO and the Replacement PO first."));
			return;
		}
		const pair = [frm.doc.cancelled_po_number, frm.doc.new_po_number];
		try {
			// the comparison is generated from the saved log, so save the current selections/content first
			if (frm.is_new() || frm.is_dirty()) await frm.save();
			// frm.save() does not reject on a server validation error: stop here if the log is still unsaved,
			// otherwise the fetch would run against a document that does not exist yet
			if (frm.is_new() || frm.is_dirty()) return;
			if (frm.doc.cancelled_po_number !== pair[0] || frm.doc.new_po_number !== pair[1]) return; // selection changed meanwhile
			const r = await frappe.call({
				method: "custom_addons.custom_addons.doctype.po_amendment_log.po_amendment_log.fetch_comparison",
				args: { name: frm.doc.name, original_po: pair[0], replacement_po: pair[1] },
				freeze: true,
				freeze_message: __("Fetching comparison..."),
			});
			if (frm.doc.cancelled_po_number !== pair[0] || frm.doc.new_po_number !== pair[1]) {
				frm.reload_doc(); // a late response never overwrites a newer selection
				return;
			}
			await frm.reload_doc();
			const warnings = (r.message && r.message.warnings) || [];
			if (warnings.length) {
				frappe.msgprint({
					title: __("Please review"), indicator: "orange",
					message: "<ul>" + warnings.map((w) => `<li>${frappe.utils.escape_html(w)}</li>`).join("") + "</ul>",
				});
			}
		} catch (e) {
			// server errors are already shown by frappe; keep the form as last saved
		}
	},
});

function po_changed(frm) {
	if (frm.doc.comparison_hash) {
		frappe.show_alert({ message: __("PO changed: the earlier comparison and MR explanation will be cleared when you save. Click 'Fetch Comparison' afterwards."), indicator: "orange" });
	}
	["header_comparison", "item_comparison", "mr_references"].forEach((t) => frm.clear_table(t));
	["comparison_hash", "snapshot_checksum", "comparison_warnings", "mr_comparison_status", "mr_comparison_summary", "mr_variance_explanation", "comparison_value_status", "rate_benefit_status"]
		.forEach((f) => (frm.doc[f] = null));
	frm.refresh_fields();
}

// Float storage turns "unavailable" into 0, so applicability flags drive an explicit N/A display.
function set_na_formatters(frm) {
	const grid = frm.get_field("item_comparison") && frm.get_field("item_comparison").grid;
	if (!grid) return;
	const val = (v, df, o, d) => frappe.form.formatters.Float(v, df, o, d);
	const rules = {
		qty_difference: (d) => d.qty_comparable,
		rate_difference: (d) => d.rate_comparable,
		amount_difference: (d) => d.amount_comparable,
		delivery_days_difference: (d) => d.original_delivery_date && d.replacement_delivery_date && ["Changed", "Unchanged"].includes(d.match_status),
		original_rate: (d) => d.original_po_detail,
		replacement_rate: (d) => d.replacement_po_detail,
		original_qty: (d) => d.original_po_detail,
		replacement_qty: (d) => d.replacement_po_detail,
	};
	Object.keys(rules).forEach((f) => {
		const df = grid.get_docfield(f);
		if (df) df.formatter = (v, d, o, doc) => (doc && !rules[f](doc) ? NA : val(v, d, o, doc));
	});
}

function show_na_in_summary(frm) {
	const same = frm.doc.comparison_value_status === "Comparable";
	const rb = same && frm.doc.rate_benefit_status && frm.doc.rate_benefit_status !== "Not Comparable";
	const set = (f, ok) => {
		const fld = frm.fields_dict[f];
		if (!fld || !frm.doc.comparison_hash) return;
		if (!ok) fld.$wrapper.find(".control-value").text(NA);
	};
	set("total_value_difference", same);
	set("net_total_difference", same);
	set("rate_benefit", rb);
	set("non_rate_value_change", rb);
}

// When the Amendment Type changes, keep the reason only if it is still allowed; preselect it when there is just one.
async function sync_reason_with_type(frm) {
	if (!frm.doc.amendment_type) { frm.set_value("amendment_reason_category", ""); return; }
	const r = await frappe.call({
		method: "custom_addons.custom_addons.doctype.po_amendment_log.po_amendment_log.get_allowed_reasons",
		args: { amendment_type: frm.doc.amendment_type },
	});
	const allowed = r.message || [];
	const cur = frm.doc.amendment_reason_category;
	if (!cur || !allowed.includes(cur)) frm.set_value("amendment_reason_category", allowed.length === 1 ? allowed[0] : "");
}