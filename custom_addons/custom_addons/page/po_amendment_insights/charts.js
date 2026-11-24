// Small SVG charts for the Overview tab: donut with legend, and a bar+line trend on two axes.
// frappe.Chart cannot draw two value axes, so these are drawn here.

const POI_STATUS_COLORS = {
	"Under Review": "#b7791f", "Approved": "#2563eb", "Implemented in ERP": "#0d9488",
	"Supplier Notified": "#7c3aed", "Closed": "#15803d", "Rejected": "#c0392b",
};
const POI_FALLBACK_COLORS = ["#64748b", "#db2777", "#0891b2", "#ca8a04"];

class PoiCharts {
	static esc(s) {
		return frappe.utils.escape_html(String(s));
	}

	static color(status, i) {
		return POI_STATUS_COLORS[status] || POI_FALLBACK_COLORS[i % POI_FALLBACK_COLORS.length];
	}

	// "+403k" style label for axes
	static short(v) {
		const a = Math.abs(v);
		const n = a >= 1e6 ? (a / 1e6).toFixed(1) + "M" : a >= 1e3 ? Math.round(a / 1e3) + "k" : String(Math.round(a));
		return (v > 0 ? "+" : v < 0 ? "-" : "") + n;
	}

	// "SAR -278,765" with the code, not the symbol (symbols can render badly)
	static money(v, cur) {
		const n = format_number(Math.abs(v), null, 0);
		return `${cur} ${v < 0 ? "-" : v > 0 ? "+" : ""}${n}`;
	}

	// Signed number: red = cost up, green = cost down
	static delta(v) {
		if (v === null || v === undefined) return __("N/A");
		const cls = v > 0 ? "poi-wait-red" : v < 0 ? "poi-green-text" : "";
		return `<span class="${cls}">${v > 0 ? "+" : ""}${format_number(v, null, 0)}</span>`;
	}

	static donut(rows) {
		const total = rows.reduce((s, r) => s + r.count, 0);
		const R = 62, W = 22, C = 2 * Math.PI * R;
		let offset = 0;
		const arcs = rows.map((r, i) => {
			const len = (r.count / total) * C;
			const arc = `<circle class="poi-arc" data-drill="impl:${this.esc(r.status)}" data-label="${this.esc(__(r.status))}"
				cx="80" cy="80" r="${R}" fill="none" stroke="${this.color(r.status, i)}" stroke-width="${W}"
				stroke-dasharray="${len} ${C - len}" stroke-dashoffset="${-offset}" transform="rotate(-90 80 80)"></circle>`;
			offset += len;
			return arc;
		});
		const legend = rows.map((r, i) => `
			<div class="poi-legend-row" data-drill="impl:${this.esc(r.status)}" data-label="${this.esc(__(r.status))}">
				<span class="poi-dot" style="background:${this.color(r.status, i)}"></span>
				<span class="poi-legend-name">${this.esc(__(r.status))}</span><b>${r.count}</b>
			</div>`).join("");
		return `<div class="poi-donut-wrap">
			<svg class="poi-donut" viewBox="0 0 160 160">${arcs.join("")}
				<text x="80" y="80" text-anchor="middle" class="poi-donut-total">${total}</text>
				<text x="80" y="97" text-anchor="middle" class="poi-donut-sub">${__("amendments")}</text>
			</svg><div class="poi-legend">${legend}</div></div>`;
	}

	// Bars = count (left axis), line = net value impact (right axis)
	static trend(rows, labels) {
		const W = 830, H = 175, L = 40, R = 56, T = 12, B = 30;
		const pw = W - L - R, ph = H - T - B, step = pw / rows.length;
		const counts = rows.map((r) => r.count), values = rows.map((r) => r.value);
		const cmax = this.niceMax(Math.max(...counts));
		const vmax = Math.max(0, ...values), vmin = Math.min(0, ...values);
		const vspan = vmax - vmin || 1;
		const yc = (c) => T + ph - (c / cmax) * ph;
		const yv = (v) => T + ph - ((v - vmin) / vspan) * ph;
		const grid = [0, 1, 2, 3, 4].map((i) => {
			const y = T + ph - (i / 4) * ph;
			return `<line x1="${L}" x2="${W - R}" y1="${y}" y2="${y}" class="poi-grid-line"/>
				<text x="${L - 8}" y="${y + 4}" text-anchor="end" class="poi-axis">${Math.round((cmax * i) / 4)}</text>`;
		}).join("");
		const right = [vmax, 0, vmin].filter((v, i, a) => a.indexOf(v) === i).map((v) =>
			`<text x="${W - R + 8}" y="${yv(v) + 4}" class="poi-axis">${v ? this.short(v) : "0"}</text>`).join("");
		const bw = Math.min(42, step * 0.60);
		const bars = rows.map((r, i) => {
			const x = L + step * i + (step - bw) / 2, y = yc(r.count);
			return `<rect class="poi-bar-hit" data-drill="month:${r.month}" data-label="${this.esc(labels[i])}"
				x="${x}" y="${y}" width="${bw}" height="${T + ph - y}" rx="3" fill="#2563eb" opacity=".85"><title>${this.esc(labels[i])}: ${r.count}</title></rect>`;
		}).join("");
		const pts = rows.map((r, i) => [L + step * i + step / 2, yv(r.value)]);
		const line = `<polyline points="${pts.map((p) => p.join(",")).join(" ")}" fill="none" stroke="#c0392b" stroke-width="2.5"/>`
			+ pts.map((p, i) => `<circle cx="${p[0]}" cy="${p[1]}" r="4" fill="#fff" stroke="#c0392b" stroke-width="2"><title>${this.esc(labels[i])}: ${this.short(values[i])}</title></circle>`).join("");
		const xs = labels.map((l, i) => `<text x="${L + step * i + step / 2}" y="${H - 10}" text-anchor="middle" class="poi-axis">${this.esc(l)}</text>`).join("");
		return `<div class="poi-trend-legend"><span><i class="poi-dot" style="background:#2563eb"></i>${__("Amendments")}</span>
			<span><i class="poi-dot" style="background:#c0392b"></i>${__("Net value impact")}</span></div>
			<svg class="poi-trend-svg" viewBox="0 0 ${W} ${H}">${grid}${right}${bars}${line}${xs}</svg>`;
	}

	static niceMax(n) {
		return Math.max(4, Math.ceil(n / 4) * 4);
	}
}
