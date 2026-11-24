// Small pager (10/25/50/100) used by tables that load one page at a time.

class PoiPager {
	constructor({ parent, on_change }) {
		this.size = 10;
		this.offset = 0;
		this.total = 0;
		this.on_change = on_change; // called after the user changes page or size
		this.$root = $(`<div class="poi-pager"></div>`).appendTo(parent);
		this.$root.on("change", ".poi-size", (e) => this.move(0, +e.target.value));
		this.$root.on("click", ".poi-prev", () => this.move(this.offset - this.size));
		this.$root.on("click", ".poi-next", () => this.move(this.offset + this.size));
	}

	state() {
		return { limit: this.size, offset: this.offset };
	}

	reset() {
		this.offset = 0;
	}

	render(total, note = "") {
		this.total = total;
		const pages = Math.max(1, Math.ceil(total / this.size));
		const page = Math.floor(this.offset / this.size) + 1;
		const from = total ? this.offset + 1 : 0;
		const to = Math.min(this.offset + this.size, total);
		const sizes = [10, 25, 50, 100].map((n) => `<option ${n === this.size ? "selected" : ""}>${n}</option>`).join("");
		this.$root.html(`
			<span class="text-muted">${note}</span>
			<span class="poi-pager-ctl">
				<span class="text-muted">${from}-${to} ${__("of")} ${total}</span>
				<select class="poi-size form-control input-xs">${sizes}</select>
				<button class="btn btn-xs btn-default poi-prev" ${page <= 1 ? "disabled" : ""}>&lsaquo; ${__("Prev")}</button>
				<b>${__("Page")} ${page} ${__("of")} ${pages}</b>
				<button class="btn btn-xs btn-default poi-next" ${page >= pages ? "disabled" : ""}>${__("Next")} &rsaquo;</button>
			</span>`);
	}

	move(offset, size) {
		if (size) this.size = size;
		this.offset = Math.max(0, offset);
		this.on_change();
	}
}
