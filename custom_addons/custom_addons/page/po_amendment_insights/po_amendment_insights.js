try {
	delete localStorage["_page:po-amendment-insights"];
} catch (e) {}

// Page entry point. Parts are inlined by Frappe's include directive (no build step).
{% include "custom_addons/custom_addons/page/po_amendment_insights/filters.js" %}
{% include "custom_addons/custom_addons/page/po_amendment_insights/charts.js" %}
{% include "custom_addons/custom_addons/page/po_amendment_insights/pager.js" %}
{% include "custom_addons/custom_addons/page/po_amendment_insights/side_panel.js" %}
{% include "custom_addons/custom_addons/page/po_amendment_insights/overview_view.js" %}
{% include "custom_addons/custom_addons/page/po_amendment_insights/approvals_view.js" %}
{% include "custom_addons/custom_addons/page/po_amendment_insights/root_cause_view.js" %}

const POI_API = "custom_addons.custom_addons.page.po_amendment_insights.api.";

frappe.pages["po-amendment-insights"].on_page_load = function (wrapper) {
	frappe.xcall(POI_API + "get_page_context").then((context) => new PoiPage(wrapper, context));
};

class PoiPage {
	constructor(wrapper, context) {
		this.context = context;
		this.tab = "overview";
		this.token = 0;
		this.page = frappe.ui.make_app_page({
			parent: wrapper, title: __("PO Amendment Insights Dashboard"), single_column: true,
		});
		this.tabs = [["overview", "Overview"], ["approvals", "Approvals"]];
		if (context.is_manager) this.tabs.push(["root_cause", "Root Cause"]);
		this.build_layout();
		this.panel = new PoiSidePanel(context);
		this.filters = new PoiFilters({ parent: this.$body.find(".poi-filters-slot"), context, on_change: () => this.refresh() });
		this.build_views();
		if (context.is_manager) {
			this.page.set_primary_action(__("Export to Excel"), () => this.export_excel(), "es-line-download");
		}
		this.refresh();
	}

	build_layout() {
		const tabs = this.tabs.map(([k, label], i) => `<a class="poi-tab ${i ? "" : "active"}" data-tab="${k}">${__(label)}</a>`).join("");
		const panes = this.tabs.map(([k], i) => `<div class="poi-tab-${k}" ${i ? 'style="display:none"' : ""}></div>`).join("");
		this.$body = $(`<div class="poi-page"><div class="poi-tabs">${tabs}</div><div class="poi-filters-slot"></div>${panes}</div>`).appendTo(this.page.main);
		this.$body.on("click", ".poi-tab", (e) => this.show_tab($(e.currentTarget).data("tab")));
	}

	build_views() {
		const on_drill = (key, label) => this.drill(key, label);
		this.views = {
			overview: new PoiOverview({ parent: this.$body.find(".poi-tab-overview"), context: this.context, on_drill }),
			approvals: new PoiApprovals({
				parent: this.$body.find(".poi-tab-approvals"), context: this.context, on_drill,
				fetch: (approver, offset, limit) => this.call("get_approvals", { approver, offset, limit }),
			}),
		};
		if (this.context.is_manager) {
			this.views.root_cause = new PoiRootCause({
				parent: this.$body.find(".poi-tab-root_cause"), context: this.context, on_drill,
				fetch: (offset, limit, only_with_action) =>
					this.call("get_root_cause", { offset, limit }, { only_with_action }),
			});
		}
	}

	call(method, args, extra_filters = {}) {
		return frappe.xcall(POI_API + method, { filters: { ...this.filters.get_values(), ...extra_filters }, ...args });
	}

	show_tab(key) {
		this.$body.find(".poi-tab").removeClass("active").filter(`[data-tab=${key}]`).addClass("active");
		this.tabs.forEach(([k]) => this.$body.find(`.poi-tab-${k}`).toggle(k === key));
		this.tab = key;
		this.load_tab();
	}

	// Each tab loads when it is open, and again after a filter change.
	refresh() {
		if (!this.filters.is_valid()) return;
		this.loaded = {};
		this.load_tab();
	}

	load_tab() {
		if (!this.filters.is_valid() || this.loaded[this.tab]) return;
		this.loaded[this.tab] = true;
		if (this.tab === "overview") {
			const token = ++this.token;
			this.call("get_overview").then((data) => token === this.token && this.views.overview.render(data));
		} else {
			this.views[this.tab].reset();
		}
	}

	drill(key, label) {
		if (key.startsWith("log:")) {
			this.panel.list_args = null; // opened from a table, so there is no list to go back to
			return this.panel.open_log(key.slice(4));
		}
		this.panel.open_list(label || key, (offset, limit) => this.call("get_drill", { key, offset, limit }));
	}

	// POST download, so the filters never go in the URL.
	export_excel() {
		if (!this.filters.is_valid()) return frappe.msgprint(__("Select a valid date range first."));
		open_url_post(`/api/method/${POI_API}export_excel`, { filters: JSON.stringify(this.filters.get_values()) });
	}
}
