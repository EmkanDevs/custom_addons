// Root Cause tab (Dashboard Manager only): changed fields, departments, requesters, suppliers, actions (spec 5.5).

class PoiRootCause {
	constructor({ parent, context, fetch, on_drill }) {
		this.context = context;
		this.fetch = fetch; // (offset, limit, only_with_action) -> promise
		this.on_drill = on_drill;
		this.esc = frappe.utils.escape_html;
		this.$root = $(`
			<div>
				<div class="poi-grid-2">
					<div class="poi-box"><div class="poi-box-title">${__("Most Changed PO Fields")}</div><div class="poi-fields"></div></div>
					<div class="poi-box"><div class="poi-box-title">${__("By Requesting Department")}</div><div class="poi-depts"></div></div>
				</div>
				<div class="poi-grid-2">
					<div class="poi-box"><div class="poi-box-title">${__("Requested By")}</div><div class="poi-scroll poi-requesters"></div></div>
					<div class="poi-box"><div class="poi-box-title">${__("Top Suppliers by Amendments")}</div><div class="poi-scroll poi-suppliers"></div></div>
				</div>
				<div class="poi-box"><div class="poi-box-title poi-title-row"><span>${__("Impact and Preventive Actions")}</span><span class="poi-only-action"></span></div>
					<div class="poi-scroll poi-impact"></div></div>
			</div>`).appendTo(parent);
		this.pager = new PoiPager({ parent: this.$root.find(".poi-impact").parent(), on_change: () => this.load() });
		this.only_action = frappe.ui.form.make_control({
			parent: this.$root.find(".poi-only-action"),
			df: { fieldtype: "Check", label: __("Only records with a corrective or preventive action"), fieldname: "only_action", change: () => this.reset() },
			render_input: true,
		});
		this.$root.on("click", "[data-drill]", (e) => this.on_drill($(e.currentTarget).data("drill"), $(e.currentTarget).data("label")));
	}

	reset() {
		this.pager.reset();
		this.load();
	}

	load() {
		const { limit, offset } = this.pager.state();
		this.fetch(offset, limit, this.only_action.get_value() ? 1 : 0).then((d) => {
			this.render_fields(d.fields);
			this.render_departments(d.departments);
			this.render_requesters(d.requesters);
			this.render_suppliers(d.suppliers);
			this.pager.render(d.impact.total);
			this.render_impact(d.impact.rows);
		});
	}

	money(v) {
		return PoiCharts.delta(v);
	}

	cur() {
		return `(${this.context.currency})`;
	}

	// Columns up to `text_cols` are text; the rest are numbers.
	table(head, rows, text_cols = 1) {
		if (!rows.length) return `<div class="poi-empty">${__("No amendments for these filters.")}</div>`;
		const th = head.map((h, i) => `<th class="${i >= text_cols ? "num" : ""}">${h}</th>`).join("");
		return `<table class="poi-table"><thead><tr>${th}</tr></thead><tbody>${rows.join("")}</tbody></table>`;
	}

	render_fields(rows) {
		const max = Math.max(1, ...rows.map((r) => r.count));
		const html = rows.map((r, i) => `<div class="poi-bar-row" data-drill="field:${this.esc(r.field)}" data-label="${this.esc(r.field)}">
			<span class="poi-bar-label" title="${this.esc(r.field)}">${this.esc(r.field)}</span>
			<span class="poi-bar-track"><span class="poi-bar-fill poi-bar-navy" style="width:${(r.count / max) * 100}%"></span></span>
			<span class="poi-bar-num"><b>${r.count}</b></span></div>`);
		this.$root.find(".poi-fields").html(html.join("") || `<div class="poi-empty">${__("No amendments for these filters.")}</div>`);
	}

	render_departments(rows) {
		const max = Math.max(1, ...rows.map((r) => r.count));
		const html = rows.map((r) => {
			const name = r.department || __("Not set");
			return `<div class="poi-bar-row" data-drill="dept:${this.esc(r.department)}" data-label="${this.esc(name)}">
				<span class="poi-bar-label" title="${this.esc(name)}">${this.esc(name)}</span>
				<span class="poi-bar-track"><span class="poi-bar-fill poi-bar-purple" style="width:${(r.count / max) * 100}%"></span></span>
				<span class="poi-bar-num"><b>${r.count}</b><span class="poi-bar-value">${PoiCharts.money(r.value, this.context.currency)}</span></span></div>`;
		});
		this.$root.find(".poi-depts").html(html.join("") || `<div class="poi-empty">${__("No amendments for these filters.")}</div>`);
	}

	render_requesters(rows) {
		const body = rows.map((r) => `<tr class="poi-row-link" data-drill="user:${this.esc(r.user)}" data-label="${this.esc(r.full_name)}">
			<td><a>${this.esc(r.full_name)}</a></td><td>${this.esc(r.department || "")}</td><td class="num">${r.count}</td><td class="num">${this.money(r.value)}</td></tr>`);
		this.$root.find(".poi-requesters").html(this.table([__("Requested by"), __("Department"), __("Amendments"), `${__("Value change")} ${this.cur()}`], body, 2));
	}

	render_suppliers(rows) {
		const body = rows.map((r) => `<tr class="poi-row-link" data-drill="supplier:${this.esc(r.supplier)}" data-label="${this.esc(r.supplier_name)}">
			<td><a>${this.esc(r.supplier_name)}</a></td><td class="num">${r.count}</td><td class="num">${r.changed}</td><td class="num">${this.money(r.value)}</td></tr>`);
		this.$root.find(".poi-suppliers").html(this.table([__("Original supplier"), __("Amendments"), __("Supplier changed"), `${__("Value change")} ${this.cur()}`], body));
	}

	render_impact(rows) {
		const cell = (v) => `<td>${this.esc(v || "")}</td>`;
		const body = rows.map((r) => `<tr><td><a href="/app/po-amendment-log/${encodeURIComponent(r.name)}" target="_blank" rel="noopener">${this.esc(r.name)}</a></td>
			<td>${this.esc(r.amendment_type || "")}<div class="text-muted">${this.esc(r.amendment_reason_category || "")}</div></td>${cell(r.business_impact)}${cell(r.risk__impact_assessment)}${cell(r.corrective__preventive_action)}<td class="num">${this.money(r.value)}</td></tr>`);
		const head = [__("Log No."), __("Type and reason"), __("Business impact"), __("Risk / impact assessment"), __("Corrective / preventive action"), `${__("Value change")} ${this.cur()}`]
			.map((h, i) => `<th class="${i === 5 ? "num" : ""}">${h}</th>`).join("");
		this.$root.find(".poi-impact").html(rows.length
			? `<table class="poi-table"><thead><tr>${head}</tr></thead><tbody>${body.join("")}</tbody></table>`
			: `<div class="poi-empty">${__("No amendments for these filters.")}</div>`);
	}
}
