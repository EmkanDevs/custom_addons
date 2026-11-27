// Monthly History tab: each supplier's score for the 12 months that end with the selected month.

class SpdHistory {
        constructor({ parent, on_open }) {
                this.$root = $(`
                        <div class="spd-box">
                                <div class="spd-box-title">${__("Monthly History")}</div>
                                <div class="spd-scroll spd-history-table"></div>
                        </div>
                `).appendTo(parent);
                this.pager = new SpdPager({ parent: this.$root, on_change: () => this.render_table() });
                this.$root.on("click", "[data-supplier]", (e) => on_open($(e.currentTarget).data("supplier")));
        }

        render(data) {
                this.data = data;
                this.render_table();
        }

        render_table() {
                const { months, history } = this.data;
                const rows = this.pager.slice(history).map((h) => `
                        <tr>
                                <td>${spd.supplier(h)}</td>
                                ${h.months.map((m) => `<td class="center">${this.cell(m)}</td>`).join("")}
                                <td class="num">${this.change(h.months)}</td>
                        </tr>`);
                if (!rows.length) return this.$root.find(".spd-history-table").html(spd.empty());
                const head = [__("Supplier"), ...months.map((m) => spd.esc(m.short)), __("Change")];
                this.$root.find(".spd-history-table").html(`
                        <table class="spd-table spd-history"><thead><tr>${head.map((h) => `<th>${h}</th>`).join("")}</tr></thead>
                        <tbody>${rows.join("")}</tbody></table>`);
        }

        cell(m) {
                if (m.score == null) return `<span class="spd-pill spd-pill-gray">${__("N/A")}</span>`;
                return `<div class="spd-hist-score">${spd.num(m.score)}<small>%</small></div>${spd.band(m.band)}
                        <div class="spd-hist-weight">${__("{0}% weight", [spd.num(m.weight)])}</div>`;
        }

        // First to last evaluated month in the window.
        change(months) {
                const scored = months.filter((m) => m.score != null);
                if (scored.length < 2) return `<span class="spd-pill spd-pill-gray">${__("N/A")}</span>`;
                const delta = scored[scored.length - 1].score - scored[0].score;
                const cls = delta > 0 ? "spd-up" : delta < 0 ? "spd-down" : "";
                return `<span class="${cls}">${delta > 0 ? "+" : ""}${spd.num(delta)} ${__("pts")}</span>`;
        }
}
