// Drawer with one supplier's monthly breakdown, opened from the chart or a table.

class SpdDetailPanel {
	constructor({ fetch }) {
		this.fetch = fetch;
		this.$el = $(`
			<div class="spd-panel">
				<div class="spd-panel-head">
					<div><div class="spd-panel-title"></div><div class="spd-sub spd-panel-sub"></div></div>
					<button class="btn btn-xs btn-default spd-panel-close">${__("Close")}</button>
				</div>
				<div class="spd-panel-body"></div>
			</div>
		`).appendTo(document.body);
		this.$el.find(".spd-panel-close").on("click", () => this.$el.removeClass("open"));
		frappe.router.on("change", () => this.$el.removeClass("open"));
	}

	open(supplier) {
		this.$el.find(".spd-panel-title").text(supplier);
		this.$el.find(".spd-panel-sub").text("");
		this.$el.find(".spd-panel-body").html(`<div class="text-muted">${__("Loading...")}</div>`);
		this.$el.addClass("open");
		this.fetch(supplier).then((d) => this.render(d)).catch(() => this.$el.removeClass("open"));
	}

	render(d) {
		this.$el.find(".spd-panel-title").text(d.supplier_name);
		this.$el.find(".spd-panel-sub").text([d.supplier, d.supplier_group, d.month_label].filter(Boolean).join(" · "));
		this.$el.find(".spd-panel-body").html(`
			<div class="spd-detail-cards">
				<div class="spd-detail-card"><div class="spd-label">${__("Overall Score")}</div>${spd.overall(d)}</div>
				<div class="spd-detail-card"><div class="spd-label">${__("Weighted Score")}</div>
					<div class="spd-overall">${d.weighted == null ? "N/A" : d.weighted.toFixed(2)}<small>${d.weighted == null ? "" : ` / ${SPD_SCALE.max}`}</small></div></div>
				<div class="spd-detail-card"><div class="spd-label">${__("Evaluated Weight")}</div>
					<div class="spd-overall">${d.weight ? spd.num(d.weight) + "<small>%</small>" : "N/A"}</div>
					<div class="spd-sub">${__("{0} of {1} criteria", [d.evaluated, d.criteria.length])}</div></div>
			</div>
			<div class="spd-detail-action"><b>${spd.esc(d.comment.title)}</b><div>${spd.esc(d.comment.text)}</div></div>
			<table class="spd-table">
				<thead><tr><th>${__("Criterion")}</th><th>${__("Metric")}</th><th>${__("Rating")}</th><th class="num">${__("Weight")}</th><th class="num">${__("Points")}</th></tr></thead>
				<tbody>${d.criteria.map((c) => this.row(c)).join("")}</tbody>
			</table>`);
	}

	row(c) {
		const na = c.rating == null;
		return `
			<tr>
				<td><b>${spd.esc(c.label)}</b></td>
				<td>${na ? `<span class="spd-pill spd-pill-gray">${__("N/A")}</span><div class="spd-sub">${spd.esc(c.reason)}</div>` : this.metric(c)}</td>
				<td class="center">${spd.rating(c.rating)}</td>
				<td class="num">${spd.num(c.weight)}%</td>
				<td class="num">${na ? `<span class="spd-na">&mdash;</span>` : spd.num(c.points, 2)}</td>
			</tr>`;
	}

	metric(c) {
		const ev = c.evidence;
		const docs = ev.docs.map((name) =>
			`<a href="/app/${frappe.router.slug(ev.doctype)}/${encodeURIComponent(name)}" target="_blank" rel="noopener">${spd.esc(name)}</a>`
		).join(", ");
		return `<b>${spd.num(c.value, 2)}</b> <span class="spd-sub">${spd.esc(__(c.unit))}</span>
			<div class="spd-sub">${__("Based on {0} record(s)", [ev.count])}${docs ? ": " + docs : ""}</div>`;
	}
}
