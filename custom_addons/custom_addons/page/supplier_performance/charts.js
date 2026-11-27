// Shared formatting, the comparison bars and the monthly trend line.

// Band name -> colour and the rating scale. Both are settings, refreshed with every load.
const SPD_BAND_CLASS = {};
const SPD_SCALE = { max: 5 };

const spd = {
	esc: (v) => frappe.utils.escape_html(v == null ? "" : String(v)),
	num: (v, digits = 1) => (v == null ? null : (+v).toFixed(digits).replace(/\.0+$/, "")),

	band(name) {
		return name ? `<span class="spd-pill spd-pill-${SPD_BAND_CLASS[name] || "blue"}">${__(name)}</span>` : "";
	},

	overall(row) {
		if (row.score == null) return `<span class="spd-na">${__("Not evaluated")}</span>`;
		return `<div class="spd-overall">${spd.num(row.score)}<small>%</small></div>${spd.band(row.band)}`;
	},

	rating(r) {
		if (r == null) return `<span class="spd-pill spd-pill-gray">${__("N/A")}</span>`;
		// Colour by share of the top rating, so any scale gets the same five shades.
		const shade = Math.max(1, Math.ceil((r / SPD_SCALE.max) * 5));
		return `<span class="spd-rating spd-rating-${shade}">${r}</span>`;
	},

	coverage(row, criteria) {
		if (!row.weight) return `<span class="spd-pill spd-pill-gray">${__("N/A")}</span><div class="spd-sub">${__("No activity")}</div>`;
		return `<b>${spd.num(row.weight)}%</b>
			<div class="spd-sub">${__("{0} of {1} criteria", [row.evaluated, criteria.length])}</div>
			<span class="spd-meter"><span style="width:${row.weight}%"></span></span>`;
	},

	supplier(row) {
		return `<a class="spd-supplier" data-supplier="${spd.esc(row.supplier)}" title="${spd.esc(row.supplier_name)}">${spd.esc(row.supplier_name)}</a>
			<div class="spd-sub">${spd.esc(row.supplier)}${row.supplier_group ? " &middot; " + spd.esc(row.supplier_group) : ""}</div>`;
	},

	empty(text) {
		return `<div class="spd-empty">${text || __("No suppliers match these filters")}</div>`;
	},
};

const SpdCharts = {
	// Horizontal bars, highest first. Overall is out of 100, a criterion out of the rating scale.
	comparison(rows, key) {
		const value = (r) => (key === "overall" ? r.score : r.ratings[key]);
		const max = key === "overall" ? 100 : SPD_SCALE.max;
		const ordered = [...rows].sort((a, b) => (value(b) ?? -1) - (value(a) ?? -1) || a.supplier_name.localeCompare(b.supplier_name));
		if (!ordered.length) return spd.empty(__("No suppliers selected for comparison"));
		return ordered.map((r) => {
			const v = value(r);
			const fill = v == null ? "" : `<span class="spd-bar-fill spd-fill-${SPD_BAND_CLASS[r.band] || "blue"}" style="width:${(v / max) * 100}%"></span>`;
			const label = v == null ? "N/A" : key === "overall" ? `${spd.num(v)}%` : `${v}/${SPD_SCALE.max}`;
			return `
				<div class="spd-bar-row" data-supplier="${spd.esc(r.supplier)}">
					<span class="spd-bar-label" title="${spd.esc(r.supplier_name)}">${spd.esc(r.supplier_name)}</span>
					<span class="spd-bar-track">${fill}</span>
					<b class="spd-bar-count">${label}</b>
				</div>`;
		}).join("");
	},

	// SVG line with a gap for each N/A month, so missing data never shows as zero.
	trend(points) {
		if (!points.some((p) => p.score != null)) return spd.empty(__("No evaluated months"));
		const w = 640, h = 260, left = 40, right = 16, top = 16, bottom = 40;
		const step = (w - left - right) / Math.max(1, points.length - 1);
		const x = (i) => left + i * step;
		const y = (v) => top + ((100 - v) / 100) * (h - top - bottom);
		let svg = `<svg class="spd-trend-svg" viewBox="0 0 ${w} ${h}" role="img" aria-label="${__("Monthly score")}">`;
		[0, 25, 50, 75, 100].forEach((n) => {
			svg += `<line x1="${left}" x2="${w - right}" y1="${y(n)}" y2="${y(n)}" class="spd-grid"/>
				<text x="${left - 8}" y="${y(n) + 4}" text-anchor="end" class="spd-axis">${n}</text>`;
		});
		SpdCharts.segments(points).forEach((seg) => {
			svg += `<polyline class="spd-line" points="${seg.map((i) => `${x(i)},${y(points[i].score)}`).join(" ")}"/>`;
		});
		points.forEach((p, i) => {
			svg += `<text x="${x(i)}" y="${h - 14}" text-anchor="middle" class="spd-axis">${spd.esc(p.label)}</text>`;
			if (p.score == null) return;
			const tip = `${p.label}: ${spd.num(p.score)}% · ${__("evaluated weight")} ${spd.num(p.weight)}%`;
			svg += `<circle cx="${x(i)}" cy="${y(p.score)}" r="4.5" class="spd-point"><title>${spd.esc(tip)}</title></circle>`;
		});
		return svg + "</svg>";
	},

	// Runs of consecutive months that have a score.
	segments(points) {
		const runs = [];
		let run = [];
		points.forEach((p, i) => {
			if (p.score == null) {
				if (run.length) runs.push(run);
				run = [];
			} else run.push(i);
		});
		if (run.length) runs.push(run);
		return runs;
	},
};
