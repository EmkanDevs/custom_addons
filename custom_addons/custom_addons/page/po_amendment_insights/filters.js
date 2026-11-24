// Filter bar. No Apply button: any change refreshes after a debounce (spec 5.2).

const POI_DEBOUNCE_MS = 350;
const POI_PERIODS = ["This Week", "This Month", "This Quarter", "This Year", "Custom Range"];

class PoiFilters {
	constructor({ parent, context, on_change }) {
		this.context = context;
		this.on_change = frappe.utils.debounce(on_change, POI_DEBOUNCE_MS);
		this.controls = {};
		const slots = ["period", "from", "to", "project", "supplier", "department", "requested_by", "type", "state"]
			.map((s) => `<div class="poi-filter poi-f-${s}"></div>`).join("");
		this.$root = $(`
			<div class="poi-filters">${slots}
				<div class="poi-filter poi-f-reset"><button class="btn btn-default btn-sm">${__("Reset")}</button></div>
			</div>
			<div class="poi-filter-note"></div>`).appendTo(parent);
		this.make_controls();
		this.$root.find(".poi-f-reset button").on("click", () => this.reset());
		this.apply_defaults();
	}

	make_controls() {
		const add = (key, slot, df) => {
			this.controls[key] = frappe.ui.form.make_control({
				parent: this.$root.find(`.poi-f-${slot}`),
				df: { ...df, fieldname: key, change: () => this.changed() },
				render_input: true,
			});
		};
		add("period", "period", { fieldtype: "Select", label: __("Period"), options: POI_PERIODS });
		add("from_date", "from", { fieldtype: "Date", label: __("From Date") });
		add("to_date", "to", { fieldtype: "Date", label: __("To Date") });
		add("project", "project", { fieldtype: "Link", options: "Project", label: __("Project") });
		add("supplier", "supplier", { fieldtype: "Link", options: "Supplier", label: __("Supplier") });
		add("requesting_department", "department", { fieldtype: "Link", options: "Department", label: __("Requesting Department") });
		add("requested_by", "requested_by", { fieldtype: "Link", options: "User", label: __("Requested By") });
		add("amendment_type", "type", { fieldtype: "Select", label: __("Amendment Type"), options: ["", ...this.context.amendment_types] });
		add("workflow_state", "state", { fieldtype: "Select", label: __("Workflow Status"), options: ["", ...this.context.states] });
	}

	apply_defaults() {
		this.silent = true;
		const blank = { project: "", supplier: "", requesting_department: "", requested_by: "", amendment_type: "", workflow_state: "", from_date: "", to_date: "" };
		Object.entries({ period: "This Year", ...blank }).forEach(([k, v]) => this.controls[k].set_value(v));
		this.silent = false;
		this.sync_ui();
	}

	reset() {
		this.apply_defaults();
		this.on_change();
	}

	changed() {
		if (this.silent) return;
		this.sync_ui();
		if (this.is_valid()) this.on_change();
	}

	sync_ui() {
		const custom = this.value("period") === "Custom Range";
		this.$root.find(".poi-f-from, .poi-f-to").toggle(custom);
		const { from_date, to_date } = this.range();
		let text = "";
		if (from_date && to_date && from_date > to_date) text = __("From date must be on or before To date");
		else if (!custom) text = `${moment(from_date).format("DD MMM YYYY")} ${__("to")} ${moment(to_date).format("DD MMM YYYY")}`;
		this.$root.siblings(".poi-filter-note").text(text).toggleClass("text-danger", from_date > to_date);
	}

	// Custom range needs both dates; any other period is computed here, in the browser's calendar.
	is_valid() {
		const { from_date, to_date } = this.range();
		return !!from_date && !!to_date && from_date <= to_date;
	}

	range() {
		const today = frappe.datetime.get_today();
		const period = this.value("period");
		if (period === "This Week") return { from_date: moment(today).startOf("week").format("YYYY-MM-DD"), to_date: today };
		if (period === "This Month") return { from_date: today.slice(0, 8) + "01", to_date: today };
		if (period === "This Quarter") {
			const q = Math.floor((moment(today).month()) / 3) * 3;
			return { from_date: moment(today).month(q).startOf("month").format("YYYY-MM-DD"), to_date: today };
		}
		if (period === "This Year") return { from_date: today.slice(0, 5) + "01-01", to_date: today };
		return { from_date: this.value("from_date"), to_date: this.value("to_date") };
	}

	get_values() {
		const out = { ...this.range() };
		["project", "supplier", "requesting_department", "requested_by", "amendment_type", "workflow_state"]
			.forEach((k) => (out[k] = this.value(k) || null));
		return out;
	}

	value(key) {
		return this.controls[key].get_value();
	}
}
