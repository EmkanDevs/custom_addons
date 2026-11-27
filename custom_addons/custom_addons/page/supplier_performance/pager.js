// Pager for a table whose rows are all loaded. Each table keeps its own page and size.

class SpdPager {
	constructor({ parent, on_change }) {
		this.size = 10;
		this.page = 1;
		this.on_change = on_change; // called after the user changes page or size
		this.$root = $(`<div class="spd-pager"></div>`).appendTo(parent);
		this.$root.on("change", ".spd-size", (e) => this.move(1, +e.target.value));
		this.$root.on("click", ".spd-prev", () => this.move(this.page - 1));
		this.$root.on("click", ".spd-next", () => this.move(this.page + 1));
	}

	reset() {
		this.page = 1;
	}

	// The rows of the current page. Clamps the page when the rows shrink after a filter change.
	slice(rows) {
		const pages = Math.max(1, Math.ceil(rows.length / this.size));
		this.page = Math.min(this.page, pages);
		const start = (this.page - 1) * this.size;
		this.render(rows.length, pages, start);
		return rows.slice(start, start + this.size);
	}

	render(total, pages, start) {
		const from = total ? start + 1 : 0;
		const to = Math.min(start + this.size, total);
		const sizes = [5, 10, 20, 50].map((n) => `<option ${n === this.size ? "selected" : ""}>${n}</option>`).join("");
		this.$root.html(`
			<span class="text-muted">${__("Showing {0}-{1} of {2}", [from, to, total])}</span>
			<span class="spd-pager-ctl">
				<label class="text-muted">${__("Rows")}</label>
				<select class="spd-size form-control input-xs">${sizes}</select>
				<button class="btn btn-xs btn-default spd-prev" ${this.page <= 1 ? "disabled" : ""}>&lsaquo; ${__("Previous")}</button>
				<b>${__("Page {0} of {1}", [this.page, pages])}</b>
				<button class="btn btn-xs btn-default spd-next" ${this.page >= pages ? "disabled" : ""}>${__("Next")} &rsaquo;</button>
			</span>`);
	}

	move(page, size) {
		if (size) this.size = size;
		this.page = Math.max(1, page);
		this.on_change();
	}
}
