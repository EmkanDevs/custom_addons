import frappe
from frappe import _


DEPARTMENT_PROJECT_NAMES = {
	"Services Related to Operation and Production (Overhead)",
	"General and Administrative Expenses (G&A)",
}


def validate_item_dimensions(doc, method=None):
	projects = {}
	missing_departments = []
	for row in doc.get("items") or []:
		if not row.get("project") and doc.get("custom_project"):
			row.project = doc.custom_project
		project = _get_project(row.get("project"), projects)
		requires_department = (
			row.get("project") in DEPARTMENT_PROJECT_NAMES
			or project.get("project_name") in DEPARTMENT_PROJECT_NAMES
		)
		if requires_department and not row.get("department"):
			missing_departments.append(row.idx)

	if missing_departments:
		frappe.throw(
			_("Department is mandatory for row(s): {0}").format(
				", ".join(str(idx) for idx in missing_departments)
			)
		)
	_set_cost_centers(doc.get("items") or [], projects)


def _set_cost_centers(rows, projects):
	departments = {}
	for row in rows:
		department = row.get("department")
		if department:
			if department not in departments:
				departments[department] = frappe.db.get_value("Department", department, "cost_center")
			row.cost_center = departments[department] or None
		elif row.get("project"):
			row.cost_center = _get_project(row.get("project"), projects).get("cost_center") or None


def _get_project(name, projects):
	if not name:
		return frappe._dict()
	if name not in projects:
		projects[name] = frappe.db.get_value(
			"Project", name, ["project_name", "cost_center"], as_dict=True
		) or frappe._dict()
	return projects[name]
