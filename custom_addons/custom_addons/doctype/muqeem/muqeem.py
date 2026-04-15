import frappe
from frappe.model.document import Document
import pandas as pd
import os
from frappe.utils import get_site_path


class Muqeem(Document):

    def before_insert(self):
        """Update Employee before insert"""
        self.update_employee()
    
    def validate(self):
        """Fallback update after insert"""
        self.update_employee()
    

    def update_employee(self):
        """Update Employee record when Muqeem record is inserted, then update Muqeem with employee name"""
        if not self.national_code:
            frappe.log_error("No national_code provided", "Muqeem Update")
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
                    "Muqeem Update"
                )
                return
            
            employee_doc = frappe.get_doc("Employee", employee.name)
            if employee_doc:
            
                employee_doc.db_set("date_of_birth",self.date_of_birth)
                employee_doc.db_set("passport_number",self.passport_number)
                employee_doc.db_set("valid_upto",self.passport_valid_upto)
                employee_doc.db_set("custom_designation_name_arabic",self.designation_name_arabic)
                employee_doc.db_set("custom_residence_expire",self.residence_expire)
                employee_doc.db_set("custom_outside_country",self.outside_country)
                employee_doc.db_set("custom_residence_expire_hijri",self.resident_expire_hijri)
                employee_doc.db_set("custom_residence_number",self.national_code)
                employee_doc.db_set("custom_residence_issue",self.residence_issue)
                # ✓ Update only if value is present
                self.db_set("employee_number", employee.name)
                # ✓ Update Muqeem with employee name and number
        
        except Exception as e:
            frappe.log_error(
                f"Error for national_code {self.national_code}: {str(e)}",
                "Muqeem Update Error"
            )


@frappe.whitelist()
def delete_all_muqeem():
    frappe.db.sql("DELETE FROM `tabMuqeem`")
    frappe.db.commit()

@frappe.whitelist()
def import_muqeem_data(file_url):
	"""Import Muqeem data from Excel or CSV file"""
	try:
		# Get the file path from the URL - check both private and public folders
		# Frappe file URLs can be in formats like:
		# - /private/files/filename.xlsx
		# - /files/filename.xlsx
		# - /private/files/subfolder/filename.xlsx
		
		file_url_stripped = file_url.lstrip('/')
		
		# Remove 'private/' prefix if present to get the actual file path
		if file_url_stripped.startswith('private/'):
			file_url_stripped = file_url_stripped.replace('private/', '', 1)
		
		# Try private folder first (for files marked as private)
		file_path = get_site_path('private', file_url_stripped)
		
		# If not found in private, try public folder
		if not os.path.exists(file_path):
			file_path = get_site_path('public', file_url_stripped)
		
		# If still not found, throw error
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
		
		# Column mapping - map Excel/CSV column names to Muqeem field names
		column_mapping = {
			'Full Name': 'full_name',
			'Gender': 'gender',
			'Country': 'country',
			'Date of Birth': 'date_of_birth',
			'National Code': 'national_code',
			'Outside Country': 'outside_country',
			'Designation Name Arabic': 'designation_name_arabic',
			'Passport Number': 'passport_number',
			'Passport Valid Upto': 'passport_valid_upto',
			'Residence Issue': 'residence_issue',
			'Residence Expire': 'residence_expire',
			'Resident Expire Hijri': 'resident_expire_hijri',
			'Employer Number': 'employer_number',
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
				# Create a new Muqeem document
				muqeem_doc = frappe.new_doc("Muqeem")
				
				# Set field values from the row
				for field in column_mapping.values():
					if field in row and row[field] is not None:
						# Handle date fields
						if field in ['date_of_birth', 'passport_valid_upto', 'residence_issue', 'residence_expire']:
							if pd.notna(row[field]):
								muqeem_doc.set(field, pd.to_datetime(row[field]).strftime('%Y-%m-%d'))
						else:
							muqeem_doc.set(field, row[field])
				
				# Save the document
				muqeem_doc.insert(ignore_permissions=True)
				success_count += 1
				
			except Exception as e:
				error_count += 1
				error_msg = f"Row {index + 2}: {str(e)[:100]}"
				errors.append(error_msg)
				frappe.log_error(f"Error importing row {index + 2}: {str(e)}", "Muqeem Import Error")
		
		frappe.db.commit()
		
		# Prepare result message
		result_message = f"Import completed: {success_count} records imported successfully"
		
		if error_count > 0:
			result_message += f", {error_count} errors occurred"
			if errors:
				result_message += f"<br><br><b>First few errors:</b><br>" + "<br>".join(errors[:5])
		
		return result_message
		
	except Exception as e:
		frappe.log_error(f"Import failed: {str(e)}", "Muqeem Import Error")
		frappe.throw(f"Import failed: {str(e)}")
