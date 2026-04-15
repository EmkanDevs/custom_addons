# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import pandas as pd
import os
from frappe.utils import get_site_path


class Gosi(Document):
	def before_insert(self):
		"""Update Employee before insert"""
		self.update_employee()
	
	def validate(self):
		"""Fallback update after insert"""
		self.update_employee()
	

	def update_employee(self):
		"""Update Employee record when Gosi record is inserted, then update Gosi with employee name"""
		if not self.national_code:
			frappe.log_error("No national_code provided", "Gosi Update")
			return
		
		try:
			# ✓ Find employee by exact match on national code ONLY
			employee = frappe.db.get_value(
				"Employee",
				{"custom_national_code": self.national_code},
				["name", "employee_name"],
				as_dict=True
			)

			if not employee:
				frappe.log_error(
					f"No Employee found for national_code: {self.national_code}",
					"Gosi Update"
				)
				return
			
			
			employee_doc = frappe.get_doc("Employee", employee.name)

			# Field mapping Gosi → Employee
			if employee_doc:
				employee_doc.db_set("custom_designation_name_arabic",self.designation_name_arabic)
				employee_doc.db_set("date_of_birth",self.date_of_birth)
				employee_doc.db_set("date_of_joining",self.date_of_enrollment)
				# employee_doc.db_set("ctc",self.total_salary)
				self.db_set("employee_number", employee.name)
		   

		except Exception as e:
			frappe.log_error(
				f"Error for national_code {self.national_code}: {str(e)}",
				"Gosi Update Error"
			)

@frappe.whitelist()
def delete_all_gosi():
	frappe.db.sql("DELETE FROM `tabGosi`")
	frappe.db.commit()

@frappe.whitelist()
def import_gosi_data(file_url):
	"""Import Gosi data from Excel or CSV file"""
	try:		
		file_url_stripped = file_url.lstrip('/')
		
		if file_url_stripped.startswith('private/'):
			file_url_stripped = file_url_stripped.replace('private/', '', 1)
		
		file_path = get_site_path('private', file_url_stripped)
		
		if not os.path.exists(file_path):
			file_path = get_site_path('public', file_url_stripped)
		
		if not os.path.exists(file_path):
			frappe.throw(f"File not found: {file_url}")
		
		# Read the file based on extension
		file_ext = os.path.splitext(file_path)[1].lower()
		
		if file_ext in ['.xlsx', '.xls']:
			df = pd.read_excel(file_path)
		elif file_ext == '.csv':
			df = pd.read_csv(file_path)
		else:
			frappe.throw("Unsupported file format. Please upload Excel (.xlsx, .xls) or CSV (.csv) file.")
		
		# Column mapping - map Excel/CSV column names to Gosi field names
		column_mapping = {
			'Full Name': 'full_name',
			'National Code': 'national_code',
			'Country': 'country',
			'Gender': 'gender',
			'Date of Birth': 'date_of_birth',
			'Basic Salary': 'basic_salary',
			'Housing': 'housing',
			'Commissions': 'commissions',
			'Other Allowances': 'other_allowances',
			'Total Salary': 'total_salary',
			'Subject to Contributions': 'subject_to_contributions',
			'Designation Name Arabic': 'designation_name_arabic',
			'Date of Enrollment': 'date_of_enrollment',
			'Eligibility for Social Insurance System 1445': 'eligibility_for_social_insurance_system_1445',
			'Employee Number': 'employee_number'
		}
		
		# Rename columns to match field names
		df.rename(columns=column_mapping, inplace=True)
		
		# Replace NaN with None
		df = df.where(pd.notnull(df), None)
		
		success_count = 0
		error_count = 0
		errors = []
		
		# Process each row
		for index, row in df.iterrows():
			try:
				# Create a new Gosi document
				gosi_doc = frappe.new_doc("Gosi")
				
				# Set field values from the row
				for field in column_mapping.values():
					if field in row and row[field] is not None:
						# Handle date fields
						if field in ['date_of_birth', 'date_of_enrollment']:
							if pd.notna(row[field]):
								gosi_doc.set(field, pd.to_datetime(row[field]).strftime('%Y-%m-%d'))
						else:
							gosi_doc.set(field, row[field])
				
				# Save the document
				gosi_doc.insert(ignore_permissions=True)
				success_count += 1
				
			except Exception as e:
				error_count += 1
				error_msg = f"Row {index + 2}: {str(e)[:100]}"
				errors.append(error_msg)
				frappe.log_error(f"Error importing row {index + 2}: {str(e)}", "Gosi Import Error")
		
		frappe.db.commit()
		
		# Prepare result message
		result_message = f"Import completed: {success_count} records imported successfully"
		
		if error_count > 0:
			result_message += f", {error_count} errors occurred"
			if errors:
				result_message += f"<br><br><b>First few errors:</b><br>" + "<br>".join(errors[:5])
		
		return result_message
		
	except Exception as e:
		frappe.log_error(f"Import failed: {str(e)}", "Gosi Import Error")
		frappe.throw(f"Import failed: {str(e)}")

