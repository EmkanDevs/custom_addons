// Approvals tab: gate health pipeline and the Waiting for Approval table (spec 5.4).

class PoiApprovals {
	constructor({ parent, context, fetch, on_drill }) {
		this.context = context;
		this.fetch = fetch; // (approver, offset, limit) -> promise
		this.on_drill = on_drill;
		this.esc = frappe.utils.escape_html;
		this.approver = context.default_approver || "";
		this.$root = $(`
			<div>
				<div class="poi-box"><div class="poi-box-title poi-title-row"><span>${__("Approval Gate Health")}</span><span class="poi-title-note">${__("Average days are measured from the workflow history")}</span></div>
					<div class="poi-pipeline"></div></div>
				<div class="poi-box"><div class="poi-box-title poi-title-row"><span>${__("Waiting for Approval")}</span>
					<span class="poi-approver-wrap"><span class="poi-title-note">${__("Approver")}</span><select class="form-control input-sm poi-approver"></select></span></div>
					<div class="poi-scroll poi-waiting"></div></div>
			</div>`).appendTo(parent);
		this.pager = new PoiPager({ parent: this.$root.find(".poi-waiting").parent(), on_change: () => this.load() });
		this.make_approver_control();
		this.$root.on("click", "[data-drill]", (e) => this.on_drill($(e.currentTarget).data("drill"), $(e.currentTarget).data("label")));
		this.$root.on("click", "[data-log]", (e) => this.on_drill("log:" + $(e.currentTarget).data("log")));
	}

	make_approver_control() {
		this.$root.on("change", ".poi-approver", (e) => {
			const value = e.target.value || "";
			if (value === this.approver) return;
			this.approver = value;
			this.pager.reset();
			this.load();
		});
	}

	reset() {
		this.pager.reset();
		this.load();
	}

	load() {
		const { limit, offset } = this.pager.state();
		this.fetch(this.approver, offset, limit).then((data) => {
			this.fill_approvers(data.approvers);
			this.render_gates(data);
			this.pager.render(data.waiting.total, this.note(data.waiting));
			this.render_waiting(data.waiting);
		});
	}

	fill_approvers(users) {
		if (this.filled) return;
		this.filled = true;
		const opts = [{ name: "", full_name: __("All approvers") }, ...users].map((u) =>
			`<option value="${this.esc(u.name)}" ${u.name === this.approver ? "selected" : ""}>${this.esc(u.full_name || u.name)}</option>`);
		this.$root.find(".poi-approver").html(opts.join(""));
	}

	note(w) {
		return `${w.total} ${__("waiting")}, ${w.overdue} ${__("for more than {0} days", [w.alert_days])}`;
	}

	// [title, role line] per gate
	gate_text(state) {
		return {
			"Draft": ["Draft", "Prepared by buyer"],
			"Pending Technical/Quality": ["Technical / Quality", "Technical Approver"],
			"Pending Procurement": ["Procurement", "Procurement Approver"],
			"Pending Finance": ["Finance", "Finance Approver"],
		}[state] || [state, ""];
	}

	render_gates(data) {
		const gates = data.gates.map((g) => {
			const slow = g.state === data.slowest_gate;
			const [title, role] = this.gate_text(g.state);
			const draft = g.state === "Draft";
			const stat = (v, k) => `<div><b>${v}</b><span>${k}</span></div>`;
			const stats = draft ? "" : `<div class="poi-gate-stats">${stat(g.approved, __("approved"))}${stat(g.rejected, __("rejected"))}${stat(g.avg_days ?? "-", __("avg days"))}</div>`;
			return `<div class="poi-gate ${slow ? "poi-slow" : ""}" data-drill="gate:${this.esc(g.state)}" data-label="${this.esc(__(g.state))}">
				<div class="poi-gate-name">${this.esc(__(title))}</div><div class="poi-gate-role">${this.esc(__(role))}</div>
				<div class="poi-gate-big"><b>${g.pending}</b> ${draft ? __("in draft") : __("pending")}</div>${stats}
				${slow ? `<div class="poi-gate-tag">${__("Slowest gate")}</div>` : ""}</div>`;
		});
		const done = `<div class="poi-gate" data-drill="state:Approved" data-label="${__("Approved")}">
			<div class="poi-gate-name">${__("Approved")}</div>
			<div class="poi-gate-role">${data.rejected_total} ${__("rejected in total")}</div>
			<div class="poi-gate-big poi-green-text"><b>${data.approved_total}</b> ${__("approved")}</div></div>`;
		this.$root.find(".poi-pipeline").html([...gates, done].join(`<span class="poi-arrow">&rsaquo;</span>`));
	}

	// red = cost went up, green = went down
	money(v) {
		const cls = v > 0 ? "poi-wait-red" : v < 0 ? "poi-green-text" : "";
		return `<span class="${cls}">${v > 0 ? "+" : ""}${format_number(v, null, 0)}</span>`;
	}

	render_waiting(w) {
		const body = w.rows.map((r) => {
			const cls = r.waiting_days > w.alert_days ? "poi-wait-red" : r.waiting_days > w.warn_days ? "poi-wait-amber" : "";
			const who = r.can_approve.length ? this.esc(r.can_approve.join(", ")) : `<span class="text-muted">-</span>`;
			const value = r.value === null ? __("N/A") : this.money(r.value);
			return `<tr class="poi-row-link" data-log="${this.esc(r.name)}"><td><a>${this.esc(r.name)}</a></td>
				<td>${this.esc(r.cancelled_po_number || "")}</td><td>${this.esc(r.original_supplier || "")}</td>
				<td><span class="poi-gate-pill">${this.esc(__(r.state))}</span></td><td class="num"><span class="${cls}">${r.waiting_days}</span></td>
				<td>${who}</td><td class="num">${value}</td></tr>`;
		}).join("");
		const head = [__("Log No."), __("Original PO"), __("Supplier"), __("Gate"), __("Waiting days"), __("Can approve"), `${__("Value change")} (${this.context.currency})`]
			.map((h, i) => `<th class="${i > 3 && i !== 5 ? "num" : ""}">${h}</th>`).join("");
		this.$root.find(".poi-waiting").html(w.rows.length
			? `<table class="poi-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`
			: `<div class="poi-empty">${__("No amendments for these filters.")}</div>`);
	}
}
