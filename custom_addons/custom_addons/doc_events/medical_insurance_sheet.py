import frappe
from frappe.model.document import Document



# ─── Batch Upload ────────────────────────────────────────────────────────────

# Column name in Excel  →  DocType fieldname
COLUMN_MAP = {
	"BupaID":               "bupa_id",
	"IDNo":                 "id_no",
	"Title":                "title",
	"MemberName":           "member_name",
	"MemberEffectiveDate":  "member_effective_date",
	"ContractNo":           "contract_no",
	"PolicyNo":             "policy_no",
	"CustomerName":         "customer_name",
	"BirthDate":            "birth_date",
	"Gender":               "gender",
	"Relationship":         "relationship",
	"RelationshipCode":     "relationship_code",
	"MainMembershipNo":     "main_membership_no",
	"MaritalStatus":        "marital_status",
	"JobName":              "job_name",
	"JobCode":              "job_code",
	"IDType":               "id_type",
	"IDExpiryDate":         "id_expiry_date",
	"DistrictName":         "district_name",
	"DistrictCode":         "district_code",
	"SponsorID":            "sponsor_id",
	"MainMemberID":         "main_member_id",
	"NationalityName":      "nationality_name",
	"NationalityCode":      "nationality_code",
	"ClassDescription":     "class_description",
	"StaffNumber":          "staff_number",
	"Department":           "department",
	"BranchDescription":    "branch_description",
	"CCHIPolicyStatus":     "cchi_policy_status",
	"PolicyUploadDate":     "policy_upload_date",
	"MemberCCHIStatus":     "member_cchi_status",
	"MemberCCHIUploadDate": "member_cchi_upload_date",
	"MemberRejectReason":   "member_reject_reason",
	"MemberMobileNo":       "member_mobile_no",
}

# Fields that should be stored as strings even if pandas reads them as numbers
STRING_FIELDS = {
	"bupa_id", "id_no", "contract_no", "policy_no", "main_membership_no",
	"relationship_code", "job_code", "id_type", "district_code", "sponsor_id",
	"main_member_id", "nationality_code", "staff_number", "member_mobile_no",
}

# Date fields — we normalise to YYYY-MM-DD
DATE_FIELDS = {
	"member_effective_date", "birth_date", "id_expiry_date",
	"policy_upload_date", "member_cchi_upload_date",
}


@frappe.whitelist()
def batch_upload(file_url):
	"""
	Read an uploaded Excel / CSV file and create (or update) Medical Insurance
	Sheet records for every row.

	Returns a summary dict: { created, updated, skipped, errors }
	"""
	frappe.has_permission("Medical Insurance Sheet", "create", throw=True)

	import pandas as pd
	from frappe.utils.file_manager import get_file_path

	file_path = get_file_path(file_url)

	# ── Read file ──────────────────────────────────────────────────────────
	if file_path.endswith(".csv"):
		df = pd.read_csv(file_path, dtype=str)
	else:
		df = pd.read_excel(file_path, dtype=str)

	df = df.where(pd.notnull(df), None)   # replace NaN → None

	# ── Normalise column names (strip whitespace) ──────────────────────────
	df.columns = [c.strip() for c in df.columns]

	# ── Validate required columns ──────────────────────────────────────────
	missing = [c for c in ("BupaID", "IDNo", "MemberName") if c not in df.columns]
	if missing:
		frappe.throw(_("Missing required columns: {0}").format(", ".join(missing)))

	created = updated = skipped = 0
	errors = []

	for idx, row in df.iterrows():
		bupa_id = str(row.get("BupaID") or "").strip()
		if not bupa_id:
			skipped += 1
			continue

		try:
			data = _build_doc_data(row)

			if frappe.db.exists("Medical Insurance Sheet", bupa_id):
				doc = frappe.get_doc("Medical Insurance Sheet", bupa_id)
				doc.update(data)
				doc.save(ignore_permissions=True)
				updated += 1
			else:
				doc = frappe.get_doc({"doctype": "Medical Insurance Sheet", **data})
				doc.insert(ignore_permissions=True)
				created += 1

		except Exception as e:
			errors.append({"row": idx + 2, "bupa_id": bupa_id, "error": str(e)})

	frappe.db.commit()

	return {
		"created": created,
		"updated": updated,
		"skipped": skipped,
		"errors": errors,
	}


def _build_doc_data(row):
	"""Map a DataFrame row to a dict of DocType fieldnames → values."""
	from datetime import datetime
	import pandas as pd

	data = {}
	for excel_col, fieldname in COLUMN_MAP.items():
		raw = row.get(excel_col)
		if raw is None:
			continue

		val = str(raw).strip() if raw is not None else None

		if not val or val.lower() == "nan":
			data[fieldname] = None
			continue

		# Normalise date fields
		if fieldname in DATE_FIELDS:
			for fmt in ("%d-%b-%y", "%d-%b-%Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
				try:
					data[fieldname] = datetime.strptime(val, fmt).strftime("%Y-%m-%d")
					break
				except ValueError:
					pass
			else:
				data[fieldname] = None   # unparseable date → skip
			continue

		# Force string for ID / code fields
		if fieldname in STRING_FIELDS:
			# remove trailing ".0" that pandas adds to numeric-looking strings
			if val.endswith(".0"):
				val = val[:-2]
			data[fieldname] = val
			continue

		data[fieldname] = val

	return data

@frappe.whitelist()
def delete_all_records():
	"""
	Delete every Medical Insurance Sheet record.
	Requires 'delete' permission on the DocType.
	"""
	frappe.has_permission("Medical Insurance Sheet", "delete", throw=True)
 
	names = frappe.get_all("Medical Insurance Sheet", pluck="name")
	count = 0
 
	for name in names:
		frappe.delete_doc(
			"Medical Insurance Sheet",
			name,
			ignore_permissions=True,
			force=True,
		)
		count += 1
 
	frappe.db.commit()
	return {"deleted": count}

@frappe.whitelist()
def download_medical_insurance_template():
    from frappe.utils.xlsxutils import make_xlsx

    columns = [
        "BupaID",
        "IDNo",
        "Title",
        "MemberName",
        "MemberEffectiveDate",
        "ContractNo",
        "PolicyNo",
        "CustomerName",
        "BirthDate",
        "Gender",
        "Relationship",
        "RelationshipCode",
        "MainMembershipNo",
        "MaritalStatus",
        "JobName",
        "JobCode",
        "IDType",
        "IDExpiryDate",
        "DistrictName",
        "DistrictCode",
        "SponsorID",
        "MainMemberID",
        "NationalityName",
        "NationalityCode",
        "ClassDescription",
        "StaffNumber",
        "Department",
        "BranchDescription",
        "CCHIPolicyStatus",
        "PolicyUploadDate",
        "MemberCCHIStatus",
        "MemberCCHIUploadDate",
        "MemberRejectReason",
        "MemberMobileNo",
    ]

    data = [columns]  # Header row only — user fills the rest

    xlsx_file = make_xlsx(data, "Medical Insurance Sheet Template")

    frappe.response["filename"]    = "Medical_Insurance_Sheet_Template.xlsx"
    frappe.response["filecontent"] = xlsx_file.getvalue()
    frappe.response["type"]        = "binary"