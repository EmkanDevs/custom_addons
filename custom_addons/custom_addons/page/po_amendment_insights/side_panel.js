// Drawer: a list of logs behind a number, then one log's summary, without leaving the page (spec 5.6).

class PoiSidePanel {
	constructor(context) {
		this.context = context;
		this.esc = frappe.utils.escape_html;
		this.$el = $(`
			<div class="poi-panel poi-panel-wide">
				<div class="poi-panel-head">
					<div class="poi-panel-title"></div>
					<button class="btn btn-xs btn-default poi-panel-close">${__("Close")}</button>
				</div>
				<div class="poi-panel-body"></div>
			</div>`).appendTo(document.body);
		this.$el.find(".poi-panel-close").on("click", () => this.close());
		this.$el.on("click", ".poi-back", () => this.open_list(...this.list_args));
		this.$el.on("click", "[data-log]", (e) => this.open_log($(e.currentTarget).data("log")));
	}

	// fetch(offset, limit) -> promise of {rows, total}
	open_list(title, fetch) {
		this.list_args = [title, fetch];
		this.$el.find(".poi-panel-title").text(title);
		const $body = this.$el.find(".poi-panel-body").empty();
		this.$list = $(`<div class="poi-scroll"></div>`).appendTo($body);
		this.pager = new PoiPager({ parent: $body, on_change: () => this.load_list() });
		this.fetch = fetch;
		this.$el.addClass("open");
		this.load_list();
	}

	load_list() {
		const { limit, offset } = this.pager.state();
		this.fetch(offset, limit).then((data) => {
			this.pager.render(data.total);
			this.$list.html(this.list_table(data.rows));
		});
	}

	list_table(rows) {
		if (!rows.length) return `<div class="poi-empty">${__("No amendments for these filters.")}</div>`;
		const body = rows.map((r) => `
			<tr class="poi-row-link" data-log="${this.esc(r.name)}">
				<td><a>${this.esc(r.name)}</a></td><td>${this.esc(r.cancelled_po_number || "")}</td>
				<td>${this.esc(r.original_supplier || "")}</td><td>${this.esc(__(r.state))}</td>
				<td class="num">${this.money(r.total_value_difference, r.comparison_value_status, r.original_currency)}</td>
			</tr>`).join("");
		const head = [__("Log"), __("Original PO"), __("Supplier"), __("Status"), __("Value change")]
			.map((h, i) => `<th class="${i === 4 ? "num" : ""}">${h}</th>`).join("");
		return `<table class="poi-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
	}

	open_log(name) {
		this.$el.find(".poi-panel-title").text(name);
		this.$el.find(".poi-panel-body").html(`<div class="text-muted">${__("Loading...")}</div>`);
		this.$el.addClass("open");
		frappe.xcall("custom_addons.custom_addons.page.po_amendment_insights.api.get_log_summary", { name })
			.then((d) => this.$el.find(".poi-panel-body").html(this.log_html(d)))
			.catch(() => this.close());
	}

	log_html(d) {
		const e = this.esc;
		const back = this.list_args ? `<a class="btn btn-default btn-sm poi-back">&lsaquo; ${__("Back to list")}</a> ` : "";
		const kv = (k, v) => `<div class="poi-kv"><span>${k}</span><b>${e(v ?? "-")}</b></div>`;
		const text = (title, v) => (v ? `<div class="poi-h">${title}</div><div class="poi-text-block">${e(v)}</div>` : "");
		const changed = d.changed_fields.map((c) => `<tr><td>${e(c.field)}</td><td>${e(c.original || "")}</td><td>${e(c.replacement || "")}</td></tr>`).join("");
		const hist = d.history.map((h) => `<tr><td>${e(__(h.state))}</td><td>${e(h.user || "")}</td><td>${e(frappe.datetime.str_to_user(h.time) || "")}</td></tr>`).join("");
		const value = d.value_status === "Comparable" ? this.fmt(d.value_difference, d.currency) : __("N/A");
		return `
			${back}<a class="btn btn-primary btn-sm" target="_blank" rel="noopener" href="/app/po-amendment-log/${encodeURIComponent(d.name)}">${__("Open document")}</a>
			${d.stale ? `<div class="poi-warn">${__("The comparison is out of date: a Purchase Order changed after it was taken.")}</div>` : ""}
			<div class="poi-kvs">
				${kv(__("Status"), __(d.state))}${kv(__("Implementation Status"), d.implementation_status)}
				${kv(__("Original PO"), d.original_po)}${kv(__("Replacement PO"), d.replacement_po)}
				${kv(__("Original Supplier"), d.original_supplier)}${kv(__("Replacement Supplier"), d.replacement_supplier)}
				${kv(__("Project"), d.project)}${kv(__("Requested By"), d.requested_by)}${kv(__("Department"), d.department)}
				${kv(__("Amendment Type"), d.amendment_type)}${kv(__("Reason"), d.reason)}
				${kv(__("Value change"), value)}${kv(__("Rate benefit"), d.rate_benefit_status === "Complete" ? this.fmt(d.rate_benefit, d.currency) : __("N/A"))}
				${kv(__("PO date gap (days)"), d.po_date_gap_days)}
			</div>
			<div class="poi-h">${__("Changed fields")}</div>
			${changed ? `<table class="poi-table"><thead><tr><th>${__("Field")}</th><th>${__("Original")}</th><th>${__("Replacement")}</th></tr></thead><tbody>${changed}</tbody></table>` : `<div class="text-muted">${__("None")}</div>`}
			${text(__("Detailed Justification"), d.justification)}${text(__("Business Impact"), d.business_impact)}
			${text(__("Risk / Impact Assessment"), d.risk)}${text(__("Corrective / Preventive Action"), d.action)}
			<div class="poi-h">${__("Approval progress")}</div>
			${hist ? `<table class="poi-table"><thead><tr><th>${__("Status")}</th><th>${__("User")}</th><th>${__("Time")}</th></tr></thead><tbody>${hist}</tbody></table>` : `<div class="text-muted">${__("No history yet")}</div>`}`;
	}

	money(value, status, currency) {
		return status === "Comparable" ? this.fmt(value, currency) : __("N/A");
	}

	fmt(value, currency) {
		const n = flt(value || 0);
		return `<span class="${n > 0 ? "poi-up" : n < 0 ? "poi-down" : ""}">${format_currency(n, currency || this.context.currency)}</span>`;
	}

	close() {
		this.$el.removeClass("open");
	}
}
