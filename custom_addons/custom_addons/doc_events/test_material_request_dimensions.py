import unittest
from unittest.mock import patch

import frappe

from custom_addons.custom_addons.doc_events.material_request_dimensions import (
	DEPARTMENT_PROJECT_NAMES,
	validate_item_dimensions,
)


class TestMaterialRequestDimensions(unittest.TestCase):
	def setUp(self):
		self.projects = {
			"PROJ-REGULAR": frappe._dict(project_name="Construction", cost_center="Project CC"),
			**{
				f"PROJ-{idx}": frappe._dict(project_name=name, cost_center=None)
				for idx, name in enumerate(sorted(DEPARTMENT_PROJECT_NAMES))
			},
		}
		self.lookup = patch(
			"frappe.db", frappe._dict(get_value=unittest.mock.Mock(side_effect=self.get_value))
		)
		self.db = self.lookup.start()
		self.addCleanup(self.lookup.stop)
		throw = patch("frappe.throw", side_effect=lambda message: self.raise_validation(message))
		throw.start()
		self.addCleanup(throw.stop)
		translate = patch(
			"custom_addons.custom_addons.doc_events.material_request_dimensions._",
			side_effect=lambda message: message,
		)
		translate.start()
		self.addCleanup(translate.stop)

	def get_value(self, doctype, name, fields, **kwargs):
		if doctype == "Project":
			return self.projects.get(name)
		return {"Operations": "Department CC", "Unconfigured": None}.get(name)

	def raise_validation(self, message):
		raise frappe.ValidationError(message)

	def make_doc(self, *rows, project=None):
		return frappe._dict(
			custom_project=project,
			items=[frappe._dict(idx=idx, **row) for idx, row in enumerate(rows, 1)],
		)

	def test_named_projects_require_department_even_when_link_is_an_id(self):
		for project in ("PROJ-0", "PROJ-1"):
			with self.subTest(project=project):
				doc = self.make_doc({}, project=project)
				with self.assertRaisesRegex(frappe.ValidationError, "row\\(s\\): 1"):
					validate_item_dimensions(doc)
				self.assertEqual(doc.get("items")[0].project, project)

	def test_parent_default_preserves_row_project_and_mixed_requirements(self):
		doc = self.make_doc(
			{"project": "PROJ-REGULAR"}, {"department": "Operations"}, project="PROJ-0"
		)
		validate_item_dimensions(doc)
		self.assertEqual(doc.get("items")[0].project, "PROJ-REGULAR")
		self.assertEqual(doc.get("items")[0].cost_center, "Project CC")
		self.assertEqual(doc.get("items")[1].cost_center, "Department CC")

	def test_department_takes_priority_for_regular_projects(self):
		doc = self.make_doc({"project": "PROJ-REGULAR", "department": "Operations"})
		validate_item_dimensions(doc)
		self.assertEqual(doc.get("items")[0].cost_center, "Department CC")

	def test_missing_source_cost_center_clears_old_value(self):
		doc = self.make_doc(
			{"project": "PROJ-REGULAR", "department": "Unconfigured", "cost_center": "Old CC"},
			{"cost_center": "Old CC"},
		)
		validate_item_dimensions(doc)
		self.assertIsNone(doc.get("items")[0].cost_center)
		self.assertEqual(doc.get("items")[1].cost_center, "Old CC")

	def test_repeated_links_are_only_queried_once(self):
		doc = self.make_doc(
			{"project": "PROJ-0", "department": "Operations"},
			{"project": "PROJ-0", "department": "Operations"},
		)
		validate_item_dimensions(doc)
		self.assertEqual(self.db.get_value.call_count, 2)
