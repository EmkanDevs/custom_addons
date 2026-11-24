// Overview tab: six cards, four charts. Anything clickable carries data-drill (spec 5.3).

const POI_CHART_COLORS = ["#2563eb", "#16a34a", "#d97706", "#7c3aed", "#dc2626", "#0d9488"];

class PoiOverview {
	constructor({ parent, context, on_drill }) {
		this.context = context;
		this.on_drill = on_drill;
		this.esc = frappe.utils.escape_html;
		this.$root = $(`
			<div>
				<div class="poi-cards"></div>
				<div class="poi-grid-2 poi-grid-35-65">
					<div class="poi-box"><div class="poi-box-title">${__("Implementation Status")}</div><div class="poi-impl"></div></div>
					<div class="poi-box"><div class="poi-box-title">${__("Monthly Trend")}</div><div class="poi-trend"></div></div>
				</div>
				<div class="poi-grid-2">
					<div class="poi-box"><div class="poi-box-title">${__("Amendment Types")}</div><div class="poi-types"></div></div>
					<div class="poi-box"><div class="poi-box-title">${__("Reason for Change")}</div><div class="poi-reasons"></div></div>
				</div>
			</div>`).appendTo(parent);
		this.$root.on("click", "[data-drill]", (e) => this.on_drill($(e.currentTarget).data("drill"), $(e.currentTarget).data("label")));
	}

	render(data) {
		this.render_cards(data.cards);
		this.render_donut(data.implementation);
		this.render_trend(data.trend);
		this.render_bars(".poi-types", data.types, "type", "amendment type", true);
		this.render_bars(".poi-reasons", data.reasons, "reason", "reason", false);
	}

	cards(c) {
		const cur = this.context.currency;
		const money = (v) => format_currency(v, cur);
		const tone = c.net_value > 0 ? "red" : c.net_value < 0 ? "green" : "navy";
		// [title, value, sub, drill, colour, tooltip]
		return [
			["Total Amendments", c.total, "Logs in these filters", "all", "navy", "How many amendment logs match the filters. Cancelled logs are not counted."],
			["Open / Active", c.open, "Not yet approved or rejected", "open", "blue", "Logs still moving through approval."],
			["Net Value Impact", money(c.net_value), `${c.increased} ${__("increased")}, ${c.reduced} ${__("reduced")}`, "increased", tone, "Replacement PO total minus Original PO total. Red means cost went up, green means it went down. Logs with different currencies are left out."],
			["Pending Approvals", c.pending, c.slowest_gate ? `${__("Slowest gate")}: ${__(c.slowest_gate)}` : __("No gate history yet"), "pending", "amber", "Logs waiting at one of the three approval gates."],
			["Rate Benefit", money(c.rate_benefit), __("Net, can be negative"), "benefit", "purple", "Money saved or lost from unit price changes only. Counted when the item comparison is complete."],
			["Avg Days to Replacement PO", c.avg_gap_days, __("Original to replacement PO date"), "gap", "navy", "Average days between the Original PO date and the Replacement PO date."],
		];
	}

	render_cards(c) {
		const html = this.cards(c).map(([title, value, sub, drill, colour, tip]) => `
			<div class="poi-stat poi-${colour}" data-drill="${drill}" data-label="${this.esc(__(title))}">
				<div class="poi-stat-title" title="${this.esc(__(tip))}">${__(title)}</div>
				<div class="poi-stat-value">${value}</div>
				<div class="poi-stat-sub">${this.esc(sub)}</div>
			</div>`);
		this.$root.find(".poi-cards").html(html.join(""));
	}

	render_donut(rows) {
		const $el = this.$root.find(".poi-impl");
		$el.html(rows.length ? PoiCharts.donut(rows) : this.empty());
	}

	render_trend(rows) {
		const $el = this.$root.find(".poi-trend");
		if (!rows.some((r) => r.count)) return $el.html(this.empty());
		const labels = rows.map((r) => moment(r.month + "-01").format("MMM"));
		$el.html(PoiCharts.trend(rows, labels));
	}

	// Plain HTML bars: horizontal and clickable.
	render_bars(sel, rows, kind, noun, with_value) {
		const max = Math.max(1, ...rows.map((r) => r.count));
		const cur = this.context.currency;
		const html = rows.map((r, i) => {
			const key = r[kind];
			const value = with_value ? `<span class="poi-bar-value">${PoiCharts.money(r.value, cur)}</span>` : "";
			const name = key || __("Not set");
			return `<div class="poi-bar-row" data-drill="${kind}:${this.esc(key)}" data-label="${this.esc(__(name))}">
				<span class="poi-bar-label" title="${this.esc(__(name))}">${this.esc(__(name))}</span>
				<span class="poi-bar-track"><span class="poi-bar-fill poi-bar-${with_value ? 0 : 1}" style="width:${(r.count / max) * 100}%"></span></span>
				<span class="poi-bar-num"><b>${r.count}</b>${value}</span></div>`;
		});
		this.$root.find(sel).html(html.join("") || this.empty());
	}

	empty() {
		return `<div class="poi-empty">${__("No amendments for these filters.")}</div>`;
	}
}
