const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const overhead = "Services Related to Operation and Production (Overhead)";
const ga = "General and Administrative Expenses (G&A)";

function make_form(rows, parent_project = "") {
	const handlers = {};
	const fields = {};
	const queries = {};
	const records = {
		"PROJ-OVERHEAD": { project_name: overhead, cost_center: "" },
		"PROJ-GA": { project_name: ga, cost_center: "" },
		"PROJ-REGULAR": { project_name: "Construction", cost_center: "Project CC" },
		Operations: { cost_center: "Department CC" },
		Unconfigured: { cost_center: "" },
	};
	const locals = { "Material Request Item": {} };
	rows.forEach((row, index) => {
		Object.assign(row, { doctype: "Material Request Item", name: `row-${index}`, idx: index + 1 });
		locals[row.doctype][row.name] = row;
		fields[row.name] = {};
	});
	const frm = {
		doc: { items: rows, custom_project: parent_project },
		fields_dict: { items: { grid: { grid_rows_by_docname: {} } } },
		set_query: (field, table, query) => { queries[field] = query; },
	};
	const frappe = {
		ui: { form: { on: (doctype, events) => { handlers[doctype] = events; } } },
		meta: { get_docfield: (doctype, field, name) => fields[name] },
		db: { get_value: async (doctype, name) => ({ message: records[name] || {} }) },
		model: {
			async set_value(doctype, name, field, value) {
				const row = locals[doctype][name];
				if (row[field] === value) return;
				row[field] = value;
				if (handlers[doctype][field]) await handlers[doctype][field](frm, doctype, name);
			},
		},
		throw: message => { throw new Error(message); },
	};
	const context = vm.createContext({
		frappe, locals,
		$: () => ({ on() {} }),
		__: (message, args = []) => message.replace("{0}", args[0]),
	});
	vm.runInContext(fs.readFileSync(path.join(__dirname, "../material_request.js"), "utf8"), context);
	handlers["Material Request"].setup(frm);
	return { frm, frappe, handlers, fields, context, queries };
}

test("both special projects require department using the Project link ID", async () => {
	for (const project of ["PROJ-OVERHEAD", "PROJ-GA"]) {
		const row = { project };
		const { frm, handlers, fields } = make_form([row]);
		await assert.rejects(handlers["Material Request"].before_save(frm), /Department is mandatory.*1/);
		assert.equal(fields[row.name].reqd, 1);
	}
});

test("parent project propagates to existing and new rows with project cost center", async () => {
	const row = { project: "PROJ-GA" };
	const { frm, handlers } = make_form([row], "PROJ-REGULAR");
	await handlers["Material Request"].custom_project(frm);
	assert.equal(row.project, "PROJ-REGULAR");
	assert.equal(row.cost_center, "Project CC");
	row.project = "";
	await handlers["Material Request Item"].items_add(frm, row.doctype, row.name);
	assert.equal(row.project, "PROJ-REGULAR");
	assert.equal(row.cost_center, "Project CC");
});

test("save awaits defaults and handles mixed row requirements independently", async () => {
	const rows = [{ department: "Operations" }, { project: "PROJ-REGULAR" }];
	const { frm, handlers, fields } = make_form(rows, "PROJ-OVERHEAD");
	await handlers["Material Request"].before_save(frm);
	assert.equal(rows[0].project, "PROJ-OVERHEAD");
	assert.equal(fields[rows[0].name].reqd, 1);
	assert.equal(fields[rows[1].name].reqd, 0);
	assert.equal(rows[0].cost_center, "Department CC");
	assert.equal(rows[1].cost_center, "Project CC");
});

test("changing a row to a regular project removes its department requirement", async () => {
	const row = { project: "PROJ-OVERHEAD", department: "Operations" };
	const { frm, handlers, fields, frappe } = make_form([row]);
	await handlers["Material Request Item"].form_render(frm, row.doctype, row.name);
	assert.equal(fields[row.name].reqd, 1);
	await frappe.model.set_value(row.doctype, row.name, "project", "PROJ-REGULAR");
	assert.equal(fields[row.name].reqd, 0);
	assert.equal(row.cost_center, "Department CC");
	await frappe.model.set_value(row.doctype, row.name, "department", "");
	assert.equal(row.cost_center, "Project CC");
});

test("an unconfigured department clears old cost center and does not fall back", async () => {
	const row = { project: "PROJ-REGULAR", department: "Unconfigured", cost_center: "Old CC" };
	const { frm, handlers } = make_form([row]);
	await handlers["Material Request"].before_save(frm);
	assert.equal(row.cost_center, "");
});

test("save preserves a manual cost center when no dimensions are selected", async () => {
	const row = { cost_center: "Manual CC" };
	const { frm, handlers } = make_form([row]);
	await handlers["Material Request"].before_save(frm);
	assert.equal(row.cost_center, "Manual CC");
});

test("clearing the last dimension clears its derived cost center", async () => {
	const row = { project: "PROJ-REGULAR", cost_center: "Project CC" };
	const { frappe } = make_form([row]);
	await frappe.model.set_value(row.doctype, row.name, "project", "");
	assert.equal(row.cost_center, "");
});

test("a delayed cost center lookup cannot overwrite a newer selection", async () => {
	const row = { project: "PROJ-REGULAR", department: "Operations" };
	const { frm, handlers, frappe } = make_form([row]);
	const get_value = frappe.db.get_value;
	let finish_old_lookup;
	frappe.db.get_value = (doctype, name, field) => {
		if (name === "Operations") return new Promise(resolve => { finish_old_lookup = resolve; });
		return get_value(doctype, name, field);
	};
	const old_lookup = handlers["Material Request Item"].department(frm, row.doctype, row.name);
	row.department = "";
	await handlers["Material Request Item"].department(frm, row.doctype, row.name);
	finish_old_lookup({ message: { cost_center: "Department CC" } });
	await old_lookup;
	assert.equal(row.cost_center, "Project CC");
});

test("Overhead Department choices match the child row project link", async () => {
	const row = { project: "PROJ-OVERHEAD", department: "Operations" };
	const { frm, handlers, queries } = make_form([row], "PROJ-REGULAR");
	await handlers["Material Request Item"].form_render(frm, row.doctype, row.name);
	const query = queries.department(frm.doc, row.doctype, row.name);
	assert.equal(query.filters.custom_project, "PROJ-OVERHEAD");
	assert.equal(Object.keys(query.filters).length, 1);
});

test("the new Department filter does not restrict G&A or regular project rows", async () => {
	const rows = [{ project: "PROJ-GA" }, { project: "PROJ-REGULAR" }, {}];
	const { frm, handlers, queries } = make_form(rows);
	for (const row of rows) {
		await handlers["Material Request Item"].form_render(frm, row.doctype, row.name);
		const query = queries.department(frm.doc, row.doctype, row.name);
		assert.equal(Object.keys(query.filters).length, 0);
	}
});

test("top Project changes update Department filters on all item rows", async () => {
	const rows = [{}, {}];
	const { frm, handlers, queries } = make_form(rows, "PROJ-OVERHEAD");
	await handlers["Material Request"].custom_project(frm);
	for (const row of rows) {
		assert.equal(queries.department(frm.doc, row.doctype, row.name).filters.custom_project, "PROJ-OVERHEAD");
	}
	frm.doc.custom_project = "PROJ-REGULAR";
	await handlers["Material Request"].custom_project(frm);
	for (const row of rows) {
		assert.equal(Object.keys(queries.department(frm.doc, row.doctype, row.name).filters).length, 0);
	}
});

test("Department choices wait until a pending Project name lookup finishes", async () => {
	const row = { project: "PROJ-OVERHEAD" };
	const { frm, handlers, frappe, queries } = make_form([row]);
	const get_value = frappe.db.get_value;
	let finish_lookup;
	frappe.db.get_value = (doctype, name, field) => {
		if (field === "project_name") return new Promise(resolve => { finish_lookup = resolve; });
		return get_value(doctype, name, field);
	};
	const rendering = handlers["Material Request Item"].form_render(frm, row.doctype, row.name);
	const pending_query = queries.department(frm.doc, row.doctype, row.name);
	assert.equal(pending_query.filters.name[0], "=");
	assert.equal(pending_query.filters.name[1], "");
	finish_lookup({ message: { project_name: overhead } });
	await rendering;
	assert.equal(queries.department(frm.doc, row.doctype, row.name).filters.custom_project, "PROJ-OVERHEAD");
});


test("row Department Cost Center takes priority after existing scripts copy the parent value", async () => {
	const row = { project: "PROJ-OVERHEAD", department: "Operations", cost_center: "Department CC" };
	const { frm, handlers, frappe } = make_form([row], "PROJ-OVERHEAD");
	frm.doc.custom_cost_center = "Parent CC";
	await frappe.model.set_value(row.doctype, row.name, "cost_center", frm.doc.custom_cost_center);
	assert.equal(row.cost_center, "Parent CC");
	await handlers["Material Request"].before_save(frm);
	assert.equal(row.cost_center, "Department CC");
});
