
(function () {
	if (window.__gl_report_print_fix_loaded) return;
	window.__gl_report_print_fix_loaded = true;

	let project_map_promise = null;

	function get_project_map() {
		if (!project_map_promise) {
			project_map_promise = frappe.db
				.get_list("Project", {
					fields: ["name", "project_name"],
					limit_page_length: 0,
				})
				.then((rows) => {
					const map = {};
					(rows || []).forEach((row) => {
						map[row.name] = row.project_name || row.name;
					});
					return map;
				})
				.catch(() => ({}));
		}
		return project_map_promise;
	}

	async function enrich_general_ledger_rows(report) {
		if (!report || report.report_name !== "General Ledger" || !report.data) return;
		const project_map = await get_project_map();
		report.data.forEach((row) => {
			if (row && row.project && !row.project_name) {
				row.project_name = project_map[row.project] || row.project;
			}
		});
	}

	function patch() {
		if (!frappe.views || !frappe.views.QueryReport) return;
		if (frappe.views.QueryReport.__gl_print_patched) return;
		frappe.views.QueryReport.__gl_print_patched = true;

		const proto = frappe.views.QueryReport.prototype;

		
		if (typeof proto.get_print_template === "function") {
			proto.get_print_template = function (print_settings, custom_format) {
				const has_picked_columns = !!(
					print_settings &&
					print_settings.columns &&
					print_settings.columns.length
				);
				if (has_picked_columns || !custom_format) return "print_grid";
				return custom_format;
			};
		}

		
		const original_print_report = proto.print_report;
		proto.print_report = async function (print_settings) {
			await enrich_general_ledger_rows(this);
			return original_print_report.call(this, print_settings);
		};

		const original_pdf_report = proto.pdf_report;
		proto.pdf_report = async function (print_settings) {
			await enrich_general_ledger_rows(this);
			return original_pdf_report.call(this, print_settings);
		};

		
		const old_get_print_settings = frappe.ui.get_print_settings;
		frappe.ui.get_print_settings = function (pdf, callback, letter_head, pick_columns, has_filters) {
			return old_get_print_settings(
				pdf,
				function (settings) {
					if (settings.print_format) {
						settings.pick_columns = 0;
						settings.columns = null;
					}
					callback(settings);
				},
				letter_head,
				pick_columns,
				has_filters
			);
		};
	}

	if (frappe.boot) {
		patch();
	}
	$(document).on("app_ready", patch);
})();
