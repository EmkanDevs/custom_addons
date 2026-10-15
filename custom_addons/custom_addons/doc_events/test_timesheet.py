import os
import unittest
from datetime import date
import pandas as pd
import frappe
from custom_addons.custom_addons.doc_events.timesheet import (
	download_timesheet_template,
	mass_submit_timesheets,
	upload_timesheet,
)


class TestTimesheetUpload(unittest.TestCase):
	def test_http_method_declarations(self):
		self.assertEqual(frappe.allowed_http_methods_for_whitelisted_func.get(upload_timesheet), ["POST"])
		self.assertEqual(frappe.allowed_http_methods_for_whitelisted_func.get(mass_submit_timesheets), ["POST"])
		self.assertEqual(frappe.allowed_http_methods_for_whitelisted_func.get(download_timesheet_template), ["GET"])

	def test_template_columns_not_merged(self):
		download_timesheet_template()
		xlsx_bytes = frappe.response.get("filecontent")
		self.assertIsNotNone(xlsx_bytes)
		import io
		import openpyxl

		wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes))
		ws = wb.active
		headers = [cell.value for cell in ws[1]]

		self.assertIn("Employees Name", headers)
		self.assertIn("Job Title", headers)
		self.assertNotIn("Employees NameJob Title", headers)
		self.assertIn("Date", headers)

	def test_missing_date_validation(self):
		with self.assertRaises(frappe.ValidationError):
			upload_timesheet("/dummy.xlsx", date=None)

		with self.assertRaises(frappe.ValidationError):
			upload_timesheet("/dummy.xlsx", date="")

		with self.assertRaises(frappe.ValidationError):
			upload_timesheet("/dummy.xlsx", date="invalid-date")

	def test_missing_in_or_out_time_fails_row(self):
		emp = frappe.db.get_value("Employee", {"status": "Active"}, "name") or frappe.db.get_value("Employee", {}, "name")
		if not emp:
			self.skipTest("No employee in database")

		df_data = {
			"Employees id": [emp, emp],
			"In Time": ["", "08:00"],
			"Out Time": ["17:00", ""],
			"Normal": [8, 8],
			"OT": [0, 0],
		}
		df = pd.DataFrame(df_data)
		test_file_path = os.path.join(frappe.get_site_path("public", "files"), "test_missing_times.xlsx")
		df.to_excel(test_file_path, index=False)

		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": "test_missing_times.xlsx",
			"file_url": "/files/test_missing_times.xlsx",
			"is_private": 0,
		}).insert(ignore_permissions=True)

		try:
			res = upload_timesheet(file_doc.file_url, date="2026-10-15")
			self.assertEqual(len(res.get("created", [])), 0)
			self.assertEqual(len(res.get("skipped", [])), 2)
			self.assertTrue(all("Missing In Time or Out Time" in s for s in res["skipped"]))
		finally:
			frappe.delete_doc("File", file_doc.name, force=1, ignore_permissions=True)
			if os.path.exists(test_file_path):
				os.remove(test_file_path)

	def test_successful_import_and_savepoint_on_error(self):
		emp = frappe.db.get_value("Employee", {"status": "Active"}, "name") or frappe.db.get_value("Employee", {}, "name")
		if not emp:
			self.skipTest("No employee in database")

		test_date = "2026-11-20"
		df_data = {
			"Employees id": [emp, "NON_EXISTING_EMP_99999"],
			"In Time": ["08:00", "08:00"],
			"Out Time": ["17:00", "17:00"],
			"Normal": [8, 8],
			"OT": [1, 1],
			"Remark": ["Test Row 1", "Test Row 2"],
		}
		df = pd.DataFrame(df_data)
		test_file_path = os.path.join(frappe.get_site_path("public", "files"), "test_partial.xlsx")
		df.to_excel(test_file_path, index=False)

		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": "test_partial.xlsx",
			"file_url": "/files/test_partial.xlsx",
			"is_private": 0,
		}).insert(ignore_permissions=True)

		try:
			res = upload_timesheet(file_doc.file_url, date=test_date)
			self.assertEqual(len(res.get("created", [])), 1)
			self.assertEqual(len(res.get("skipped", [])), 1)

			ts_name = res["created"][0]
			ts = frappe.get_doc("Timesheet", ts_name)
			self.assertEqual(str(ts.start_date), test_date)
			self.assertEqual(str(ts.end_date), test_date)
			self.assertEqual(str(ts.time_logs[0].from_time.date()), test_date)
			self.assertEqual(str(ts.time_logs[0].to_time.date()), test_date)
		finally:
			if "ts_name" in locals():
				frappe.delete_doc("Timesheet", ts_name, force=1, ignore_permissions=True)
			frappe.delete_doc("File", file_doc.name, force=1, ignore_permissions=True)
			if os.path.exists(test_file_path):
				os.remove(test_file_path)
