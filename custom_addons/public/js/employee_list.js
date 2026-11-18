// Employee list view: adds a "Batch Upload" button.
// Server side: employee_batch_upload.py

(function () {
	// Dotted path of employee_batch_upload.py inside your app
	const API = "custom_addons.custom_addons.doc_events.employee_batch_upload";
	const esc = frappe.utils.escape_html;

	let listening = false;

	// Add the button once per list view instance. Never let a failure here break the list.
	function attach(listview) {
		try {
			if (!listview || listview.doctype !== "Employee") return true;
			if (listview.__ebu_attached) return true;
			if (!listview.page || !listview.$result) return false; // list not fully built yet
			listview.__ebu_attached = true;
			listen();
			if (frappe.model.can_create("Employee")) {
				listview.page.add_inner_button(__("Batch Upload"), () => open_dialog());
			}
			return true;
		} catch (e) {
			console.error("Employee Batch Upload: could not add button", e);
			return true;
		}
	}

	// 1) normal route: listview_settings.onload (runs when the list is being built)
	const settings = (frappe.listview_settings["Employee"] = frappe.listview_settings["Employee"] || {});
	const prev_onload = settings.onload;
	settings.onload = function (listview) {
		if (prev_onload) prev_onload.call(this, listview);
		setTimeout(() => attach(listview), 300); // after the list has finished its own setup
	};

	// 2) fallback: another script may replace listview_settings, so also try after route changes
	function try_attach(tries) {
		try {
			const route = frappe.get_route ? frappe.get_route() : [];
			if (route[0] !== "List" || route[1] !== "Employee") return;
			if (window.cur_list && attach(cur_list)) return;
			if (tries > 0) setTimeout(() => try_attach(tries - 1), 500);
		} catch (e) {
			console.error("Employee Batch Upload:", e);
		}
	}
	frappe.router.on("change", () => setTimeout(() => try_attach(12), 800));
	setTimeout(() => try_attach(12), 800);

	function open_dialog() {
		const d = new frappe.ui.Dialog({
			title: __("Employee Batch Upload"),
			fields: [
				{
					fieldtype: "HTML",
					fieldname: "help",
					options: `<p class="text-muted small">
						${__("Upload an .xlsx or .csv with these columns:")}
						<i>Employee Code, Birth Date, Hiring Date, Gender, National Code, Nationality,
						Employee First Name, Employee Second Name, Employee Family Name, Department,
						Position, Government Classification</i>.
						${__("Dates are read as dd/mm/yyyy.")}
						<a href="#" class="ebu-template">${__("Download template")}</a></p>`,
				},
				{
					fieldname: "company",
					label: __("Company"),
					fieldtype: "Link",
					options: "Company",
					reqd: 1,
					default: frappe.defaults.get_user_default("Company"),
				},
				{ fieldname: "file", label: __("File (.xlsx / .csv)"), fieldtype: "Attach", reqd: 1 },
				{ fieldtype: "Section Break" },
				{
					fieldname: "create_masters",
					label: __("Create missing Department / Designation / other linked records"),
					fieldtype: "Check",
					default: 1,
				},
				{
					fieldname: "validate_only",
					label: __("Validate only (nothing is saved)"),
					fieldtype: "Check",
					default: 1,
					change() {
						d.get_primary_btn().text(d.get_value("validate_only") ? __("Validate") : __("Upload"));
					},
				},
			],
			primary_action_label: __("Validate"),
			primary_action(v) {
				run(d, v);
			},
		});

		d.fields_dict.help.$wrapper.find(".ebu-template").on("click", (e) => {
			e.preventDefault();
			window.open(frappe.urllib.get_full_url(`/api/method/${API}.get_template`));
		});
		d.show();
	}

	function run(d, v) {
		const args = {
			file_url: v.file,
			company: v.company,
			create_masters: v.create_masters ? 1 : 0,
		};

		if (v.validate_only) {
			frappe.call({
				method: `${API}.validate_file`,
				args,
				freeze: true,
				freeze_message: __("Checking file…"),
				callback: (r) => r.message && show_result(r.message),
			});
			return;
		}

		frappe.confirm(__("Create new employees from this file now? Existing Employee Codes will be skipped."), () => {
			frappe.call({
				method: `${API}.start_upload`,
				args,
				callback: () => {
					d.hide();
					frappe.show_alert({ message: __("Upload started in the background"), indicator: "blue" });
				},
			});
		});
	}

	function listen() {
		if (listening) return;
		listening = true;
		frappe.realtime.on("employee_batch_upload", (data) => {
			if (data.progress) {
				frappe.show_progress(
					__("Uploading Employees"),
					data.progress[0],
					data.progress[1],
					__("Processed {0} of {1}", [data.progress[0], data.progress[1]])
				);
			}
			if (!data.done) return;
			frappe.hide_progress();
			if (data.error) {
				frappe.msgprint({ title: __("Upload failed"), message: esc(data.error), indicator: "red" });
				return;
			}
			show_result(data);
			if (window.cur_list && cur_list.doctype === "Employee") cur_list.refresh();
		});
	}

	function show_result(r) {
		const s = r.summary;
		const dry = r.dry_run;
		const row = (label, n) => `<tr><td>${label}</td><td class="text-right"><b>${n}</b></td></tr>`;

		let html = `<table class="table table-bordered table-sm">
			${row(__("Rows in file"), s.total)}
			${row(dry ? __("Will be created") : __("Created"), s.created)}
			${row(__("Skipped (already exist)"), s.skipped)}
			${row(__("Failed"), s.failed)}
		</table>`;

		html += `<p class="text-muted small mb-1">${__("Column mapping")}</p>
			<table class="table table-bordered table-sm"><tbody>${r.mapping
				.map((m) => `<tr><td>${esc(m.column)}</td><td>${m.field ? esc(m.field) : `<span class="text-danger">${__("ignored")}</span>`}</td></tr>`)
				.join("")}</tbody></table>`;

		(r.warnings || []).forEach((w) => (html += `<div class="text-warning small">${esc(w)}</div>`));

		const masters = Object.entries(r.new_masters || {});
		if (masters.length) {
			html += `<p class="mt-3 mb-1 text-muted small">${dry ? __("Will be created") : __("Created")}:</p>`;
			masters.forEach(([dt, vals]) => {
				html += `<div class="small"><b>${esc(__(dt))}</b> (${vals.length}): ${esc(vals.join(", "))}</div>`;
			});
		}

		if ((r.problems || []).length) {
			html += `<p class="mt-3 mb-1 text-muted small">${__("Rows needing attention")}${s.failed + s.skipped > r.problems.length ? " (" + __("first {0}", [r.problems.length]) + ")" : ""}:</p>
				<div style="max-height:260px;overflow:auto"><table class="table table-bordered table-sm">
				<thead><tr><th>${__("Row")}</th><th>${__("Code")}</th><th>${__("Name")}</th><th>${__("Result")}</th><th>${__("Message")}</th></tr></thead>
				<tbody>${r.problems
					.map((p) => `<tr><td>${p.row}</td><td>${esc(p.code)}</td><td>${esc(p.name)}</td><td>${esc(p.result)}</td><td>${esc(p.message)}</td></tr>`)
					.join("")}</tbody></table></div>`;
		}

		if (r.report_url) {
			html += `<p class="mt-3"><a href="${r.report_url}" target="_blank">${__("Download full result file")}</a></p>`;
		}
		if (dry) {
			html += `<p class="mt-3 text-muted small">${__("Nothing has been saved. Untick “Validate only” and click Upload to import.")}</p>`;
		}

		frappe.msgprint({
			title: dry ? __("Validation result") : __("Upload result"),
			message: html,
			wide: true,
			indicator: s.failed ? "orange" : "green",
		});
	}
})();