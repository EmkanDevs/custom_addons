// Overview tab: cards, supplier comparison, trend, ranking and the Criteria table.

class SpdOverview {
	constructor({ parent, on_open }) {
		this.selection = null; // null = every supplier in view; else a Set of supplier IDs
		this.$root = $(`
			<div>
				<div class="spd-cards"></div>
				<div class="spd-grid-2">
					<div class="spd-box">
						<div class="spd-box-title">${__("Supplier Comparison")}<span class="spd-tag spd-month-tag"></span></div>
						<div class="spd-compare-controls">
							<label>${__("Compare by")} <select class="form-control input-sm spd-compare-key"></select></label>
							<div class="spd-picker">
								<button class="btn btn-default btn-sm spd-picker-btn"></button>
								<div class="spd-picker-menu">
									<input class="form-control input-sm spd-picker-search" placeholder="${__("Search supplier")}">
									<div class="spd-picker-actions">
										<a class="spd-picker-all">${__("Select all")}</a><a class="spd-picker-clear">${__("Clear")}</a>
									</div>
									<div class="spd-picker-list"></div>
								</div>
							</div>
						</div>
						<div class="spd-bars"></div>
					</div>
					<div class="spd-box">
						<div class="spd-box-title">${__("Monthly Performance Trend")}<span class="spd-tag spd-trend-tag"></span></div>
						<div class="spd-trend"></div>
					</div>
				</div>
				<div class="spd-box spd-ranking">
					<div class="spd-box-title">${__("Supplier Ranking & Actions")}
						<label class="spd-title-ctl">${__("Compare by")} <select class="form-control input-sm spd-rank-key"></select></label>
					</div>
					<div class="spd-scroll spd-ranking-table"></div>
				</div>
				<div class="spd-box spd-criteria">
					<div class="spd-box-title">${__("Criteria")}<span class="spd-tag spd-month-tag"></span></div>
					<div class="spd-scroll spd-criteria-table"></div>
				</div>
			</div>
		`).appendTo(parent);
		this.rank_pager = new SpdPager({ parent: this.$root.find(".spd-ranking"), on_change: () => this.render_ranking() });
		this.criteria_pager = new SpdPager({ parent: this.$root.find(".spd-criteria"), on_change: () => this.render_criteria() });
		this.bind(on_open);
	}

	bind(on_open) {
		const $r = this.$root;
		$r.on("click", "[data-supplier]", (e) => on_open($(e.currentTarget).data("supplier")));
		$r.find(".spd-compare-key").on("change", () => this.render_comparison());
		$r.find(".spd-rank-key").on("change", () => {
			this.rank_pager.reset();
			this.render_ranking();
		});
		$r.find(".spd-picker-btn").on("click", () => $r.find(".spd-picker").toggleClass("open"));
		$(document).on("click.spd_picker", (e) => {
			if (!$(e.target).closest(".spd-picker").length) $r.find(".spd-picker").removeClass("open");
		});
		$r.find(".spd-picker-search").on("input", () => this.render_picker());
		$r.find(".spd-picker-all").on("click", () => this.set_selection(null));
		$r.find(".spd-picker-clear").on("click", () => this.set_selection(new Set()));
		$r.on("change", ".spd-picker-list input", (e) => this.toggle(e.target.value, e.target.checked));
	}

	loading() {
		this.$root.css("opacity", 0.6);
	}

	render(data) {
		this.$root.css("opacity", 1);
		this.data = data;
		this.fill_keys(".spd-compare-key", "overall");
		this.fill_keys(".spd-rank-key", "overall");
		const month = data.months[data.months.length - 1].label;
		this.$root.find(".spd-month-tag").text(month);
		this.$root.find(".spd-trend-tag").text(data.trend.single || __("Average of suppliers in view"));
		this.render_cards(data.summary);
		this.render_comparison();
		this.$root.find(".spd-trend").html(SpdCharts.trend(data.trend.points));
		this.render_ranking();
		this.render_criteria();
	}

	sort_key() {
		return this.$root.find(".spd-rank-key").val() || "overall";
	}

	// Keeps the user's choice when the criteria list is unchanged.
	fill_keys(selector, fallback) {
		const $s = this.$root.find(selector);
		const current = $s.val() || fallback;
		const options = [["overall", __("Overall score")], ...this.data.criteria.map((c) => [c.key, c.label])];
		$s.html(options.map(([k, l]) => `<option value="${k}">${spd.esc(l)}</option>`).join(""));
		$s.val(options.some(([k]) => k === current) ? current : fallback);
	}

	render_cards(s) {
		const cards = [
			[__("Evaluated Suppliers"), s.evaluated, __("{0} in view · {1} not evaluated", [s.in_view, s.in_view - s.evaluated]), "navy"],
			[__("Average Monthly Score"), s.average == null ? "N/A" : `${spd.num(s.average)}%`,
				s.average == null ? __("No applicable source records") : __("Average evaluated weight: {0}%", [spd.num(s.average_weight)]), "blue"],
			[__("{0} Suppliers", [s.top_band.name]), s.top_count, __("Overall score of {0}% or above", [s.top_band.from]), "green"],
			[__("Needs Attention"), s.attention, s.attention_bands.join(", ") || __("No band is marked for attention"), "red"],
		];
		this.$root.find(".spd-cards").html(cards.map(([title, value, sub, colour]) => `
			<div class="spd-stat spd-${colour}">
				<div class="spd-stat-title">${title}</div>
				<div class="spd-stat-value">${value}</div>
				<div class="spd-stat-sub">${sub}</div>
			</div>`).join(""));
	}

	// The comparison selection only changes this chart, never the rest of the report.
	render_comparison() {
		const rows = this.data.rows.filter((r) => !this.selection || this.selection.has(r.supplier));
		const key = this.$root.find(".spd-compare-key").val();
		this.$root.find(".spd-bars").html(SpdCharts.comparison(rows, key));
		const label = this.selection ? __("{0} selected", [rows.length]) : __("All suppliers");
		this.$root.find(".spd-picker-btn").html(`${label} &#9662;`);
		this.render_picker();
	}

	render_picker() {
		const term = (this.$root.find(".spd-picker-search").val() || "").toLowerCase();
		const rows = this.data.rows.filter((r) => r.supplier_name.toLowerCase().includes(term));
		this.$root.find(".spd-picker-list").html(rows.map((r) => `
			<label class="spd-picker-item">
				<input type="checkbox" value="${spd.esc(r.supplier)}" ${!this.selection || this.selection.has(r.supplier) ? "checked" : ""}>
				<span>${spd.esc(r.supplier_name)}<small>${spd.esc(r.supplier_group)}</small></span>
			</label>`).join("") || spd.empty(__("No suppliers available")));
	}

	set_selection(selection) {
		this.selection = selection;
		this.render_comparison();
	}

	toggle(supplier, checked) {
		const selection = this.selection || new Set(this.data.rows.map((r) => r.supplier));
		checked ? selection.add(supplier) : selection.delete(supplier);
		this.set_selection(selection.size === this.data.rows.length ? null : selection);
	}

	// Ranked suppliers first (by rank, then name); suppliers without a value last.
	ranked_rows() {
		const key = this.sort_key();
		return [...this.data.rows].sort((a, b) => {
			const ra = a.ranks[key], rb = b.ranks[key];
			if ((ra == null) !== (rb == null)) return ra == null ? 1 : -1;
			return (ra || 0) - (rb || 0) || a.supplier_name.localeCompare(b.supplier_name) || a.supplier.localeCompare(b.supplier);
		});
	}

	render_ranking() {
		const key = this.sort_key();
		const criteria = this.data.criteria;
		const rows = this.rank_pager.slice(this.ranked_rows()).map((r) => `
			<tr>
				<td class="spd-rank">${r.ranks[key] ?? "&mdash;"}</td>
				<td>${spd.supplier(r)}</td>
				<td class="spd-weighted">${r.weighted == null ? `<span class="spd-pill spd-pill-gray">${__("N/A")}</span>` : `<b>${r.weighted.toFixed(2)}</b><small> / ${SPD_SCALE.max}</small>`}</td>
				<td>${spd.overall(r)}</td>
				<td>${spd.coverage(r, criteria)}</td>
				<td class="spd-comment"><b>${spd.esc(r.comment.title)}</b><div>${spd.esc(r.comment.text)}</div></td>
			</tr>`);
		const head = [__("Rank"), __("Supplier / Supplier Type"), __("Weighted Score /{0}", [SPD_SCALE.max]), __("Overall Score & Rating"),
			__("Evaluated Weight"), __("Comments / Action Required")];
		this.$root.find(".spd-ranking-table").html(this.table(head, rows));
	}

	render_criteria() {
		const criteria = this.data.criteria;
		const rows = this.criteria_pager.slice(this.ranked_rows()).map((r) => `
			<tr><td>${spd.supplier(r)}</td>${criteria.map((c) => `<td class="center">${spd.rating(r.ratings[c.key])}</td>`).join("")}</tr>`);
		const head = [__("Supplier"), ...criteria.map((c) => `${spd.esc(__(c.column))}<span class="spd-th-sub">${spd.num(c.weight)}% ${__("weight")}</span>`)];
		this.$root.find(".spd-criteria-table").html(this.table(head, rows, "spd-matrix"));
	}

	table(head, rows, cls = "") {
		if (!rows.length) return spd.empty();
		return `<table class="spd-table ${cls}"><thead><tr>${head.map((h) => `<th>${h}</th>`).join("")}</tr></thead>
			<tbody>${rows.join("")}</tbody></table>`;
	}
}
