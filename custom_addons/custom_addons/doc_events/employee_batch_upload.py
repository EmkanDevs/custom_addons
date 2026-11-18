"""
Employee Batch Upload
=====================
Bulk-create new Employee records (existing Employee Codes are skipped, never updated); from an .xlsx / .csv file that has the
HR-export layout:

    Employee Code | Birth Date | Hiring Date | Gender | National Code | Nationality |
    Employee First Name | Employee Second Name | Employee Family Name |
    Department | Position | Government Classification

Entry points (all whitelisted, called from public/js/employee_list.js):
    get_template()   -> downloads a blank template
    validate_file()  -> dry run, writes nothing, returns what *would* happen
    start_upload()   -> queues the real import on the "long" worker queue
"""
import re
from collections import defaultdict
from datetime import date, datetime

import frappe
from frappe import _
from frappe.utils import cint, getdate, now_datetime, strip_html_tags, today
from frappe.utils.csvutils import read_csv_content
from frappe.utils.file_manager import save_file
from frappe.utils.xlsxutils import make_xlsx, read_xlsx_file_from_attached_file

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# key -> (header text in the sheet, required?)
COLUMNS = {
	"employee_code": ("Employee Code", True),
	"birth_date": ("Birth Date", True),
	"hiring_date": ("Hiring Date", True),
	"gender": ("Gender", True),
	"national_code": ("National Code", False),
	"nationality": ("Nationality", False),
	"first_name": ("Employee First Name", True),
	"second_name": ("Employee Second Name", False),
	"family_name": ("Employee Family Name", False),
	"department": ("Department", False),
	"position": ("Position", False),
	"government_classification": ("Government Classification", False),
}

# Columns that always land in the same standard Employee field
FIXED_FIELDS = {
	"employee_code": "employee_number",
	"birth_date": "date_of_birth",
	"hiring_date": "date_of_joining",
	"gender": "gender",
	"first_name": "first_name",
	"second_name": "middle_name",
	"family_name": "last_name",
	"department": "department",
	"position": "designation",
}

# The three custom columns are auto-detected by field label (see _resolve_targets).
# If auto-detection picks the wrong field, pin it here: key -> Employee fieldname.
FIELD_OVERRIDES = {
	# "national_code": "custom_national_code",
	# "nationality": "custom_nationality",
	# "government_classification": "branch",
}

# Spelling fixes applied to cell values before lookup: key -> {lowercase value: replacement}
VALUE_ALIASES = {
	"nationality": {"indian": "India"},  # the existing master uses "India"
}

GENDER_ALIASES = {"m": "Male", "f": "Female", "male": "Male", "female": "Female"}
DATE_FORMATS = ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d")
SAVEPOINT = "employee_batch_row"
NON_DATA_FIELDS = (
	"Section Break", "Column Break", "Tab Break", "HTML", "Button", "Table", "Table MultiSelect",
)


# --------------------------------------------------------------------------- #
# Whitelisted API
# --------------------------------------------------------------------------- #

@frappe.whitelist()
def get_template():
	_check_permission()
	data = [
		[label for label, _req in COLUMNS.values()],
		[600001, "01/01/1990", "01/01/2024", "Male", 2400000000, "Egypt",
		 "AHMED", "ALI", "HASSAN", "Operations", "Foreman", "1963075-15 CPC"],
	]
	frappe.response["filename"] = "employee_batch_upload_template.xlsx"
	frappe.response["filecontent"] = make_xlsx(data, "Employees").getvalue()
	frappe.response["type"] = "binary"


@frappe.whitelist()
def validate_file(file_url, company, create_masters=1):
	"""Dry run. Reads and checks the file; nothing is created or changed."""
	_check_permission()
	return _run(file_url, company, cint(create_masters), dry_run=True)


@frappe.whitelist()
def start_upload(file_url, company, create_masters=1):
	_check_permission()
	frappe.enqueue(
		f"{__name__}.run_background",
		queue="long",
		timeout=3600,
		file_url=file_url,
		company=company,
		create_masters=cint(create_masters),
	)
	return "queued"


def run_background(file_url, company, create_masters):
	"""Worker entry point. Runs as the user who clicked Upload."""
	user = frappe.session.user
	try:
		result = _run(file_url, company, create_masters, dry_run=False, publish=True)
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(title="Employee Batch Upload failed")
		frappe.publish_realtime("employee_batch_upload", {"done": True, "error": _error_text(e)}, user=user)
		return

	s = result["summary"]
	frappe.publish_realtime("employee_batch_upload", {"done": True, **result}, user=user)
	_notify(
		user,
		_("Employee Batch Upload finished: {0} created, {1} skipped, {2} failed").format(
			s["created"], s["skipped"], s["failed"]
		),
	)


# --------------------------------------------------------------------------- #
# Core
# --------------------------------------------------------------------------- #

def _run(file_url, company, create_masters, dry_run, publish=False):
	if not frappe.db.exists("Company", company):
		frappe.throw(_("Company {0} does not exist").format(company))

	data, col_index = parse_sheet(_read_file(file_url))
	if not data:
		frappe.throw(_("The file has no data rows."))

	meta = frappe.get_meta("Employee")
	targets = _resolve_targets(meta)
	mapping, warnings = _describe_mapping(col_index, targets, meta)

	ctx = _Ctx(company, create_masters, dry_run)
	_prepare_masters(data, ctx, targets)

	results, seen, total = [], {}, len(data)
	for i, rec in enumerate(data, 1):
		results.append(_process_row(rec, ctx, targets, seen, dry_run))
		if publish and (i % 10 == 0 or i == total):
			frappe.publish_realtime(
				"employee_batch_upload", {"progress": [i, total]}, user=frappe.session.user
			)

	counts = defaultdict(int)
	for r in results:
		counts[r["result"]] += 1

	out = {
		"dry_run": dry_run,
		"summary": {
			"total": total,
			"created": counts["Created"],
			"skipped": counts["Skipped"],
			"failed": counts["Failed"],
		},
		"mapping": mapping,
		"warnings": warnings,
		"new_masters": {dt: values for dt, values in ctx.new_masters.items()},
		"problems": [r for r in results if r["result"] in ("Failed", "Skipped")][:100],
	}
	if not dry_run:
		out["report_url"] = _save_report(results)
	return out


def _process_row(rec, ctx, targets, seen, dry_run):
	code = _clean(rec.get("employee_code"))
	full_name = " ".join(
		p for p in (_clean(rec.get(k)) for k in ("first_name", "second_name", "family_name")) if p
	)
	out = {"row": rec["_row"], "code": code, "name": full_name, "result": "", "message": ""}

	try:
		if not code:
			raise ValueError(_("Employee Code is empty"))
		if code in seen:
			raise ValueError(_("Duplicate Employee Code in file (first seen on row {0})").format(seen[code]))
		seen[code] = rec["_row"]

		vals = _build_values(rec, ctx, targets)
		existing = frappe.db.get_value("Employee", {"employee_number": code}, "name")

		if existing:
			out.update(result="Skipped", message=_("Employee {0} already exists").format(existing))
			return out

		name = None
		if not dry_run:
			name = _write(lambda: _insert_employee(vals, ctx.company))
		out.update(result="Created", message=name or "")
	except Exception as e:
		frappe.clear_messages()
		out.update(result="Failed", message=_error_text(e))
	return out


def _write(fn):
	"""Run a DB write inside a savepoint so one bad row doesn't poison the batch."""
	frappe.db.savepoint(SAVEPOINT)
	try:
		return fn()
	except Exception:
		frappe.db.rollback(save_point=SAVEPOINT)
		raise


def _insert_employee(vals, company):
	doc = frappe.get_doc({"doctype": "Employee", "company": company, "status": "Active", **vals})
	doc.insert()
	frappe.clear_messages()
	return doc.name


def _build_values(rec, ctx, targets):
	first = _clean(rec.get("first_name"))
	if not first:
		raise ValueError(_("Employee First Name is empty"))

	dob = _parse_date(rec.get("birth_date"), _("Birth Date"))
	doj = _parse_date(rec.get("hiring_date"), _("Hiring Date"))
	if dob > getdate(today()):
		raise ValueError(_("Birth Date cannot be in the future"))
	if doj <= dob:
		raise ValueError(_("Hiring Date must be after Birth Date"))

	gender = _gender(rec.get("gender"))
	if not gender:
		raise ValueError(_("Gender is empty"))

	vals = {
		"employee_number": _clean(rec.get("employee_code")),
		"first_name": first,
		"middle_name": _clean(rec.get("second_name")),
		"last_name": _clean(rec.get("family_name")),
		"gender": ctx.link("Gender", gender, create=False),
		"date_of_birth": dob,
		"date_of_joining": doj,
	}

	dept = _value(rec, "department")
	if dept:
		vals["department"] = ctx.link("Department", dept)
	pos = _value(rec, "position")
	if pos:
		vals["designation"] = ctx.link("Designation", pos)

	for key in ("national_code", "nationality", "government_classification"):
		df, value = targets.get(key), _value(rec, key)
		if not df or not value:
			continue
		vals[df.fieldname] = ctx.link(df.options, value) if df.fieldtype == "Link" else value

	return {k: v for k, v in vals.items() if v not in ("", None)}


# --------------------------------------------------------------------------- #
# Master data (Department / Designation / Branch / ...)
# --------------------------------------------------------------------------- #

class _Ctx:
	"""Resolves link values once per run and remembers the answer (or the error)."""

	def __init__(self, company, create_masters, dry_run):
		self.company = company
		self.create_masters = create_masters
		self.dry_run = dry_run
		self.cache = {}
		self.new_masters = defaultdict(list)

	def link(self, doctype, value, create=True):
		key = (doctype, value.lower())
		if key not in self.cache:
			try:
				self.cache[key] = (self._resolve(doctype, value, create), None)
			except Exception as e:
				frappe.clear_messages()
				self.cache[key] = (None, _error_text(e))
		name, err = self.cache[key]
		if err:
			raise ValueError(err)
		return name

	def _find(self, doctype, value):
		if doctype == "Department":
			return frappe.db.get_value(
				"Department", {"department_name": value, "company": self.company}, "name"
			)
		return frappe.db.get_value(doctype, value, "name")

	def _resolve(self, doctype, value, create):
		name = self._find(doctype, value)
		if name:
			return name
		if not (create and self.create_masters):
			raise ValueError(_("{0} '{1}' does not exist").format(_(doctype), value))
		self.new_masters[doctype].append(value)
		if self.dry_run:
			return value
		return _create_master(doctype, value, self.company)


def _create_master(doctype, value, company):
	doc = frappe.new_doc(doctype)
	if doctype == "Department":
		doc.department_name = value
		doc.company = company
		if frappe.db.exists("Department", "All Departments"):
			doc.parent_department = "All Departments"
	else:
		meta = frappe.get_meta(doctype)
		autoname = meta.autoname or ""
		scrubbed = f"{frappe.scrub(doctype)}_name"
		fieldname = autoname[6:] if autoname.startswith("field:") else None
		if not fieldname and meta.get_field(scrubbed):
			fieldname = scrubbed
		if fieldname:
			doc.set(fieldname, value)
		if autoname.lower() == "prompt":
			doc.__newname = value
		elif not fieldname:
			raise ValueError(_("{0} '{1}' does not exist").format(_(doctype), value))
	doc.insert(ignore_permissions=True)
	frappe.clear_messages()
	return doc.name


def _prepare_masters(data, ctx, targets):
	"""Resolve/create every distinct master value up front, outside any row savepoint."""
	specs = [("department", "Department", True), ("position", "Designation", True), ("gender", "Gender", False)]
	for key in ("nationality", "government_classification"):
		df = targets.get(key)
		if df and df.fieldtype == "Link":
			specs.append((key, df.options, True))

	for key, doctype, create in specs:
		done = set()
		for rec in data:
			value = _gender(rec.get(key)) if key == "gender" else _value(rec, key)
			if not value or value.lower() in done:
				continue
			done.add(value.lower())
			try:
				ctx.link(doctype, value, create)
			except ValueError:
				pass  # remembered in the cache and reported on every affected row


# --------------------------------------------------------------------------- #
# Field mapping
# --------------------------------------------------------------------------- #

def _resolve_targets(meta):
	def label(df):
		return (df.label or "").strip().lower()

	def candidates():
		return [df for df in meta.fields if df.fieldtype not in NON_DATA_FIELDS]

	def find(key, labels, fieldnames, prefix=None, not_prefix=None):
		if FIELD_OVERRIDES.get(key):
			df = meta.get_field(FIELD_OVERRIDES[key])
			if not df:
				frappe.throw(_("FIELD_OVERRIDES: Employee has no field {0}").format(FIELD_OVERRIDES[key]))
			return df
		for df in candidates():
			if df.fieldname in fieldnames or label(df) in labels:
				return df
		if prefix:
			for df in candidates():
				lab = label(df)
				if lab.startswith(prefix) and not (not_prefix and lab.startswith(not_prefix)):
					return df
		return None

	targets = {
		"national_code": find(
			"national_code",
			{"national code", "national id", "national id number", "national number", "national id no"},
			("national_code", "national_id", "custom_national_code", "custom_national_id"),
			prefix="national",
			not_prefix="nationality",
		),
		"nationality": find("nationality", {"nationality"}, ("nationality", "custom_nationality")),
		"government_classification": find(
			"government_classification",
			{"government classification"},
			("government_classification", "custom_government_classification"),
		),
	}
	if not targets["government_classification"] and not FIELD_OVERRIDES.get("government_classification"):
		targets["government_classification"] = meta.get_field("branch")  # fallback
	return targets


def _describe_mapping(col_index, targets, meta):
	mapping, warnings = [], []
	for key, (label, _req) in COLUMNS.items():
		if key not in col_index:
			continue
		df = meta.get_field(FIXED_FIELDS[key]) if key in FIXED_FIELDS else targets.get(key)
		if df:
			mapping.append({"column": label, "field": f"{df.label} ({df.fieldname})"})
		else:
			mapping.append({"column": label, "field": None})
			warnings.append(
				_("No Employee field found for column '{0}' – it will be ignored. "
				  "Set FIELD_OVERRIDES in employee_batch_upload.py if the field exists under another label.").format(label)
			)
	for key, (label, _req) in COLUMNS.items():
		if key not in col_index:
			warnings.append(_("Optional column '{0}' is not in the file.").format(label))
	return mapping, warnings


# --------------------------------------------------------------------------- #
# File parsing (pure helpers – no DB)
# --------------------------------------------------------------------------- #

def _read_file(file_url):
	file_doc = frappe.get_doc("File", {"file_url": file_url})
	name = (file_doc.file_name or "").lower()
	content = file_doc.get_content()
	if name.endswith((".xlsx", ".xlsm")):
		return read_xlsx_file_from_attached_file(fcontent=content)
	if name.endswith(".csv"):
		return read_csv_content(content)
	frappe.throw(_("Please upload an .xlsx or .csv file."))


def parse_sheet(rows):
	"""rows: list of lists. Returns (records, {key: column index}).
	Each record is {key: raw cell, "_row": 1-based sheet row number}."""
	rows = list(rows)
	header_idx = next((i for i, r in enumerate(rows) if any(_clean(c) for c in r)), None)
	if header_idx is None:
		frappe.throw(_("The file is empty."))

	by_header = {_norm(label): key for key, (label, _req) in COLUMNS.items()}
	col_index = {}
	for i, cell in enumerate(rows[header_idx]):
		key = by_header.get(_norm(cell))
		if key and key not in col_index:
			col_index[key] = i

	missing = [label for key, (label, req) in COLUMNS.items() if req and key not in col_index]
	if missing:
		frappe.throw(_("Missing required column(s): {0}").format(", ".join(missing)))

	records = []
	for row_no, r in enumerate(rows[header_idx + 1:], start=header_idx + 2):
		if not any(_clean(c) for c in r):
			continue
		rec = {key: (r[i] if i < len(r) else None) for key, i in col_index.items()}
		rec["_row"] = row_no
		records.append(rec)
	return records, col_index


def _norm(v):
	return re.sub(r"\s+", " ", str(v or "")).strip().lower()


def _clean(v):
	if v is None:
		return ""
	if isinstance(v, float) and v.is_integer():
		v = int(v)
	return re.sub(r"\s+", " ", str(v)).strip()


def _value(rec, key):
	value = _clean(rec.get(key))
	return VALUE_ALIASES.get(key, {}).get(value.lower(), value)


def _gender(v):
	s = _clean(v)
	return GENDER_ALIASES.get(s.lower(), s.title())


def _parse_date(v, label):
	if isinstance(v, datetime):
		return v.date()
	if isinstance(v, date):
		return v
	s = _clean(v)
	if not s:
		raise ValueError(_("{0} is empty").format(label))
	for fmt in DATE_FORMATS:
		try:
			return datetime.strptime(s, fmt).date()
		except ValueError:
			continue
	raise ValueError(_("{0} '{1}' is not a valid date (expected dd/mm/yyyy)").format(label, s))


# --------------------------------------------------------------------------- #
# Misc
# --------------------------------------------------------------------------- #

def _check_permission():
	frappe.has_permission("Employee", "create", throw=True)


def _error_text(e):
	return strip_html_tags(str(e) or "").strip() or e.__class__.__name__


def _save_report(results):
	rows = [["Row", "Employee Code", "Employee Name", "Result", "Message"]]
	rows += [[r["row"], r["code"], r["name"], r["result"], r["message"]] for r in results]
	stamp = now_datetime().strftime("%Y%m%d_%H%M%S")
	f = save_file(
		f"employee_batch_upload_result_{stamp}.xlsx",
		make_xlsx(rows, "Result").getvalue(),
		None,
		None,
		is_private=1,
	)
	return f.file_url


def _notify(user, subject):
	try:
		frappe.get_doc(
			{"doctype": "Notification Log", "subject": subject, "for_user": user, "type": "Alert"}
		).insert(ignore_permissions=True)
	except Exception:
		pass