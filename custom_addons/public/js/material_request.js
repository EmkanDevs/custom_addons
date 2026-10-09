const DEPT_MANDATORY_PROJECTS = [
	"Services Related to Operation and Production (Overhead)",
	"General and Administrative Expenses (G&A)",
];
const material_request_project_names = new Map();

frappe.ui.form.on("Material Request", {
	setup(frm) {
		frm.set_query("department", "items", (doc, cdt, cdn) => {
			const row = locals[cdt][cdn];
			const project_name = DEPT_MANDATORY_PROJECTS.includes(row.project)
				? row.project : material_request_project_names.get(row.project);
			// Wait for the Project name before offering Department choices.
			if (row.project && typeof project_name !== "string") {
				return { filters: { name: ["=", ""] } };
			}
			return {
				filters: project_name === "Services Related to Operation and Production (Overhead)"
					? { custom_project: row.project } : {},
			};
		});
		$(frm.wrapper).on("grid-row-render.custom_addons_project_dimensions", (event, grid_row) => {
			if (grid_row.doc?.doctype === "Material Request Item") {
				set_row_department_requirement(frm, grid_row.doc);
			}
		});
	},
	refresh(frm) {
		(frm.doc.items || []).forEach(row => set_row_department_requirement(frm, row));
	},
	custom_project(frm) {
		return Promise.all((frm.doc.items || []).map(row =>
			frappe.model.set_value(row.doctype, row.name, "project", frm.doc.custom_project || "")
		));
	},

	async before_save(frm) {
		const missing = [];
		await Promise.all((frm.doc.items || []).map(async row => {
			if (!row.project && frm.doc.custom_project) {
				await frappe.model.set_value(row.doctype, row.name, "project", frm.doc.custom_project);
			}
			const required = await set_row_department_requirement(frm, row);
			if (required && !row.department) missing.push(row.idx);
		}));
		if (missing.length) {
			missing.sort((a, b) => a - b);
			frappe.throw(__("Department is mandatory for row(s): {0}", [missing.join(", ")]));
		}
		await Promise.all((frm.doc.items || []).filter(row => row.project || row.department).map(row =>
			set_row_cost_center(row.doctype, row.name)
		));
	},
});

frappe.ui.form.on("Material Request Item", {
	async items_add(frm, cdt, cdn) {
		if (frm.doc.custom_project) {
			await frappe.model.set_value(cdt, cdn, "project", frm.doc.custom_project);
		}
		await set_row_department_requirement(frm, locals[cdt][cdn]);
		await set_row_cost_center(cdt, cdn);
	},
	async project(frm, cdt, cdn) {
		await set_row_department_requirement(frm, locals[cdt][cdn]);
		await set_row_cost_center(cdt, cdn);
	},
	department(frm, cdt, cdn) {
		return set_row_cost_center(cdt, cdn);
	},
	form_render(frm, cdt, cdn) {
		return set_row_department_requirement(frm, locals[cdt][cdn]);
	},
});

async function set_row_department_requirement(frm, row) {
	const project = row.project;
	const project_name = await get_material_request_project_name(project);
	if (locals[row.doctype]?.[row.name] !== row || row.project !== project) return;
	const required = DEPT_MANDATORY_PROJECTS.includes(project_name);
	const df = frappe.meta.get_docfield(row.doctype, "department", row.name);
	if (df) df.reqd = required ? 1 : 0;
	const grid_row = frm.fields_dict.items.grid.grid_rows_by_docname[row.name];
	if (grid_row) grid_row.toggle_reqd("department", required);
	return required;
}

async function get_material_request_project_name(project) {
	if (!project || DEPT_MANDATORY_PROJECTS.includes(project)) {
		return Promise.resolve(project || "");
	}
	if (!material_request_project_names.has(project)) {
		const lookup = frappe.db.get_value("Project", project, "project_name")
			.then(r => {
				const project_name = r.message?.project_name || "";
				material_request_project_names.set(project, project_name);
				return project_name;
			})
			.catch(error => {
				material_request_project_names.delete(project);
				throw error;
			});
		material_request_project_names.set(project, lookup);
	}
	return material_request_project_names.get(project);
}

async function set_row_cost_center(cdt, cdn) {
	const row = locals[cdt][cdn];
	const { project, department } = row;
	const name = department || project;
	let cost_center = "";
	if (name) {
		const doctype = department ? "Department" : "Project";
		const result = await frappe.db.get_value(doctype, name, "cost_center");
		cost_center = result.message?.cost_center || "";
	}
	// Ignore a lookup that finished after the row changed or was deleted.
	if (locals[cdt]?.[cdn] !== row || row.project !== project || row.department !== department) return;
	await frappe.model.set_value(cdt, cdn, "cost_center", cost_center);
}
