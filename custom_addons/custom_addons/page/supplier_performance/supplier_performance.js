try {
	delete localStorage["_page:supplier-performance"];
} catch (e) {}

// Page entry point. Parts are inlined by Frappe's include directive (no build step).
{% include "custom_addons/custom_addons/page/supplier_performance/filters.js" %}
{% include "custom_addons/custom_addons/page/supplier_performance/pager.js" %}
{% include "custom_addons/custom_addons/page/supplier_performance/charts.js" %}
{% include "custom_addons/custom_addons/page/supplier_performance/overview_view.js" %}
{% include "custom_addons/custom_addons/page/supplier_performance/history_view.js" %}
{% include "custom_addons/custom_addons/page/supplier_performance/detail_panel.js" %}

const SPD_API = "custom_addons.custom_addons.page.supplier_performance.api.";
const SPD_TABS = [
	["overview", "Overview"],
	["history", "Monthly History"],
];

frappe.pages["supplier-performance"].on_page_load = function (wrapper) {
	frappe.xcall(SPD_API + "get_page_context").then((context) => new SpdPage(wrapper, context));
};

class SpdPage {
	constructor(wrapper, context) {
		this.context = context;
		this.token = 0;
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Supplier Performance Dashboard"),
			single_column: true,
		});
		this.build_layout();
		this.panel = new SpdDetailPanel({ fetch: (supplier) => this.fetch_detail(supplier) });
		const open = (supplier) => this.panel.open(supplier);
		this.filters = new SpdFilters({
			parent: this.$body.find(".spd-filters-slot"),
			context,
			on_change: () => this.refresh(),
		});
		this.overview = new SpdOverview({ parent: this.$body.find(".spd-tab-overview"), on_open: open });
		this.history = new SpdHistory({ parent: this.$body.find(".spd-tab-history"), on_open: open });
		this.page.set_primary_action(__("Export to Excel"), () => this.export_excel(), "es-line-download");
		this.page.set_secondary_action(__("Print"), () => window.print());
		this.refresh();
	}

	build_layout() {
		const tabs = SPD_TABS.map(([key, label], i) =>
			`<a class="spd-tab ${i ? "" : "active"}" data-tab="${key}">${__(label)}</a>`
		).join("");
		this.$body = $(`
			<div class="spd-page">
				<div class="spd-tabs">${tabs}</div>
				<div class="spd-filters-slot"></div>
				<div class="spd-periodline"></div>
				<div class="spd-tab-overview"></div>
				<div class="spd-tab-history" style="display:none"></div>
			</div>
		`).appendTo(this.page.main);
		this.$body.on("click", ".spd-tab", (e) => this.show_tab($(e.currentTarget).data("tab")));
	}

	show_tab(key) {
		this.$body.find(".spd-tab").removeClass("active").filter(`[data-tab=${key}]`).addClass("active");
		SPD_TABS.forEach(([k]) => this.$body.find(`.spd-tab-${k}`).toggle(k === key));
	}

	refresh() {
		const token = ++this.token;
		const values = this.filters.get_values();
		this.overview.loading();
		frappe.xcall(SPD_API + "get_dashboard", { filters: values }).then((data) => {
			if (token !== this.token) return;
			this.apply_settings(data);
			this.filters.align_unlabelled();
			this.render_periodline(data);
			this.overview.render(data);
			this.history.render(data);
		});
	}

	// Band colours and the rating scale are settings, so take them from each response.
	apply_settings(data) {
		SPD_SCALE.max = data.scale || 5;
		Object.keys(SPD_BAND_CLASS).forEach((k) => delete SPD_BAND_CLASS[k]);
		(data.bands || []).forEach((b) => (SPD_BAND_CLASS[b.name] = b.color));
	}

	render_periodline(data) {
		const month = data.months[data.months.length - 1].label;
		const esc = frappe.utils.escape_html;
		this.$body.find(".spd-periodline").html(`
			<span class="spd-dot"></span><b>${esc(month)}</b>
			<span class="text-muted">&middot; ${__("Monthly evaluation")} &middot; ${esc(this.context.company || "")}</span>`);
	}

	fetch_detail(supplier) {
		return frappe.xcall(SPD_API + "get_supplier_detail", { filters: this.filters.get_values(), supplier });
	}

	// POST download: the server answers with the file, so the filters never go in the URL.
	export_excel() {
		open_url_post(`/api/method/${SPD_API}export_excel`, {
			filters: JSON.stringify(this.filters.get_values()),
			sort: this.overview.sort_key(),
		});
	}
}
