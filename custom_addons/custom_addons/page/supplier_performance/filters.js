// Report-wide filters. No Apply button: any change refreshes after a debounce.

const SPD_DEBOUNCE_MS = 400;

class SpdFilters {
	constructor({ parent, context, on_change }) {
		this.context = context;
		this.on_change = frappe.utils.debounce(on_change, SPD_DEBOUNCE_MS);
		this.controls = {};
		this.$root = $(`
			<div class="spd-filters">
				<div class="spd-filter spd-f-year"></div>
				<div class="spd-filter spd-f-month"></div>
				<div class="spd-filter spd-f-supplier"></div>
				<div class="spd-filter spd-f-supplier_group"></div>
				<div class="spd-filter spd-f-item_group"></div>
				<div class="spd-filter spd-f-item"></div>
				<div class="spd-filter spd-f-include_inactive"></div>
				<div class="spd-filter spd-f-reset"><button class="btn btn-default btn-sm">${__("Reset")}</button></div>
			</div>
		`).appendTo(parent);
		this.make_controls();
		this.$root.find(".spd-f-reset button").on("click", () => this.reset());
		this.apply_defaults();
		setTimeout(() => this.align_unlabelled(), 0);
		$(window).off("resize.spd_filters").on("resize.spd_filters", () => this.align_unlabelled());
	}

	// The checkbox and Reset have no label above them. Centre them on the input line,
	// measured from a real input, whatever spacing Frappe adds around its controls.
	align_unlabelled() {
		const $input = this.$root.find(".spd-f-month .control-input").first();
		if (!$input.is(":visible")) return;
		const line = $input.offset().top + $input.outerHeight() / 2;
		[[".spd-f-include_inactive", ".checkbox"], [".spd-f-reset", "button"]].forEach(([slot, part]) => {
			const $slot = this.$root.find(slot).css("top", 0);
			const $el = $slot.find(part).first();
			$slot.css("top", line - ($el.offset().top + $el.outerHeight() / 2));
		});
	}

	make_controls() {
		const add = (key, df) => {
			this.controls[key] = frappe.ui.form.make_control({
				parent: this.$root.find(`.spd-f-${key}`),
				df: { ...df, fieldname: key, change: () => this.changed(key) },
				render_input: true,
			});
		};
		add("year", { fieldtype: "Select", label: __("Evaluation Year"), options: this.years() });
		add("month", { fieldtype: "Select", label: __("Evaluation Month"), options: [] });
		add("supplier", { fieldtype: "Link", options: "Supplier", label: __("Supplier") });
		add("supplier_group", { fieldtype: "Link", options: "Supplier Group", label: __("Supplier Type") });
		add("item_group", { fieldtype: "Link", options: "Item Group", label: __("Item Group") });
		add("item", {
			fieldtype: "Link", options: "Item", label: __("Item"),
			get_query: () => {
				const group = this.value("item_group");
				return group ? { filters: { item_group: ["descendants of (inclusive)", group] } } : {};
			},
		});
		add("include_inactive", { fieldtype: "Check", label: __("Show suppliers with no activity") });
	}

	// Years that have at least one selectable month, newest first.
	years() {
		return [...new Set(this.context.months.map((m) => m.value.slice(0, 4)))];
	}

	// Month names for one year. The list limits them to the selectable range.
	set_month_options(year) {
		const options = this.context.months
			.filter((m) => m.value.startsWith(year + "-"))
			.map((m) => ({ value: m.value.slice(5), label: m.label.replace(/\s*\d{4}$/, "") }))
			.reverse();
		this.controls.month.df.options = options;
		this.controls.month.set_options();
		return options;
	}

	apply_defaults() {
		const [year, month] = this.context.default_month.split("-");
		this.set_month_options(year);
		this.set_silently({
			year, month,
			supplier: "", supplier_group: "", item_group: "", item: "", include_inactive: 0,
		});
	}

	reset() {
		this.apply_defaults();
		this.on_change();
	}

	changed(key) {
		if (this.silent) return;
		if (key === "year") return this.year_changed();
		if (key === "item_group") return this.check_item().then(() => this.on_change());
		this.on_change();
	}

	// Keep the chosen month when the new year has it, else use its latest month.
	year_changed() {
		const month = this.value("month");
		const options = this.set_month_options(this.value("year"));
		const keep = options.some((o) => o.value === month);
		this.set_silently({ month: keep ? month : options[options.length - 1].value }).then(() => this.on_change());
	}

	// An Item outside the new Item Group goes back to All.
	check_item() {
		const item = this.value("item");
		const group = this.value("item_group");
		if (!item || !group) return Promise.resolve();
		return frappe
			.xcall("frappe.client.get_count", {
				doctype: "Item",
				filters: { name: item, item_group: ["descendants of (inclusive)", group] },
			})
			.then((count) => count || this.set_silently({ item: "" }));
	}

	get_values() {
		const values = {};
		Object.keys(this.controls).forEach((key) => (values[key] = this.value(key) || null));
		values.month = values.year && values.month ? `${values.year}-${values.month}` : this.context.default_month;
		delete values.year;
		values.include_inactive = this.value("include_inactive") ? 1 : 0;
		return values;
	}

	value(key) {
		return this.controls[key].get_value();
	}

	set_silently(values) {
		this.silent = true;
		const sets = Object.entries(values).map(([key, value]) => this.controls[key].set_value(value));
		return Promise.all(sets).finally(() => (this.silent = false));
	}
}
