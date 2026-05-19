"""
File: custom_addons/custom_addons/doc_events/salary_slip_upload.py

Reads an uploaded Excel salary report and bulk-creates ERPNext Salary Slips.

How components work:
  - EARNINGS / DEDUCTIONS lists define known components with explicit mappings.
  - Any OTHER Excel column with a value > 0 is handled dynamically:
      * Column appears BEFORE  'Total Income'    → created as Earning
      * Column appears BETWEEN 'Total Income'
        and 'Total Deductions'                   → created as Deduction
      * Column appears AFTER   'Total Deductions' → ignored (standard field)
  - Components must exist in ERPNext BEFORE upload (enforced by pre-flight check).
  - Components the user chose to skip are excluded from every slip silently.
"""

import os
import json
import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.naming import make_autoname
import openpyxl

# ── Columns that are never treated as salary components ───────────────────────
STANDARD_FIELD_COLUMNS = {
    "S", "Code", "Employee Name", "No. of Days", "Working Days",
    "Vacation Days", "Absence", "Total Income", "Total Deductions",
    "Net Salary", "Cash Payments", "Bank Payments", "Check Payments",
    "Exchange Payments", "Main Bank", "Account Number", 
}

# ── Excel column  →  Salary Slip field (standard fields only) ─────────────────
COLUMN_MAP = {
    "Code"             : "employee",
    "Employee Name"    : "employee_name",
    "No. of Days"      : "total_working_days",
    "Working Days"     : "payment_days",
    "Vacation Days"    : "vacation_days",
    "Absence"          : "absent_days",
    "Total Income"     : "gross_pay",
    "Total Deductions" : "total_deduction",
    "Net Salary"       : "net_pay",
    "Cash Payments"    : "cash_payments",
    "Bank Payments"    : "bank_payments",
    "Check Payments"   : "check_payments",
    "Exchange Payments": "exchange_payments",
    "Main Bank"        : "bank_name",
    "Account Number"   : "bank_account_no",
}

# ── Known Earnings: (ERPNext component name, Excel column name) ───────────────
EARNINGS = [
    ("Basic",                    "Basic Salary"),
    ("Worth Salary",             "Worth Salary"),
    ("Working Days Amount",      "Working Days Amount"),
    ("Housing Allowance",        "Housing Allowance"),
    ("Transportation Allowance", "Transportation Allowance"),
    ("Food Allowance",           "Food Allowance"),
    ("Other Allowances",         "Other Allowances"),
    ("Overtime",                 "Overtime"),
    ("Other Income",             "Other Income"),
    ("Leave Encashment",         "Vacation Days Amount"),
]

# ── Known Deductions: (ERPNext component name, Excel column name) ─────────────
DEDUCTIONS = [
    ("GOSI",                 "Social Security"),
    ("Health Insurance",     "Health Insurance"),
    ("Loans and Deductions", "Loans and Deductions"),
]

# Build lookup sets for fast membership checks
_KNOWN_EARNING_COLS   = {col for _, col in EARNINGS}
_KNOWN_DEDUCTION_COLS = {col for _, col in DEDUCTIONS}
_ALL_KNOWN_COLS       = (
    STANDARD_FIELD_COLUMNS | _KNOWN_EARNING_COLS | _KNOWN_DEDUCTION_COLS
)


# =============================================================================
def _clean_date(value):
    """
    Normalise a date arg — handles datetime objects, date objects,
    "None"/"null"/"" strings, and plain YYYY-MM-DD strings.
    Always returns a "YYYY-MM-DD" string or None.
    """
    if value is None:
        return None

    # datetime / date objects coming from openpyxl Excel cells
    import datetime
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.strftime("%Y-%m-%d")

    s = str(value).strip()
    if s.lower() in ("none", "null", ""):
        return None

    # Truncate any time portion: "2026-03-01 00:00:00" → "2026-03-01"
    return s[:10]
 
 
def _resolve_date_range(raw_start, raw_end):
    """
    Returns (posting_date, start_date, end_date) as strings.
 
    - Both supplied  -> use them; posting_date = start_date.
    - Neither        -> current month first/last; posting_date = today().
    - Only one       -> frappe.throw().
    """
    start_date = _clean_date(raw_start)
    end_date   = _clean_date(raw_end)
 
    if start_date and end_date:
        if start_date > end_date:
            frappe.throw(_("Start Date cannot be after End Date."))
        return start_date, start_date, end_date
 
    if not start_date and not end_date:
        pd = today()
        return pd, str(get_first_day(pd)), str(get_last_day(pd))
 
    frappe.throw(
        _("Please provide both Start Date and End Date, or leave both blank.")
    )
# ═════════════════════════════════════════════════════════════════════════════
def _ensure_component(component_name, component_type):
    """
    Guards the upload path. All components must exist BEFORE upload_salary_slips
    is called (enforced by the JS pre-flight check). If one is still missing,
    raises a clear error rather than silently creating it.

    Also corrects the component type if it was previously saved with the wrong one.
    """
    if not frappe.db.exists("Salary Component", component_name):
        frappe.throw(
            _(
                "Salary Component '{0}' does not exist. "
                "Please create it before uploading."
            ).format(component_name)
        )

    # Correct the type if it was previously created with the wrong one
    existing_type = frappe.db.get_value(
        "Salary Component", component_name, "type"
    )
    if existing_type != component_type:
        frappe.db.set_value(
            "Salary Component", component_name, "type", component_type
        )
        frappe.db.commit()
        frappe.logger().info(
            f"Salary Slip Upload: Fixed Salary Component '{component_name}' "
            f"type from '{existing_type}' to '{component_type}'"
        )


# ═════════════════════════════════════════════════════════════════════════════
def _add_component_to_slip(slip, component_name, amount):
    """
    Adds a salary component to the correct child table (earnings/deductions).
    Reads the component type from ERPNext. Skips duplicates and zero amounts.

    Returns True if added, False if skipped.
    """
    if not amount or flt(amount) <= 0:
        return False

    component_type = frappe.db.get_value("Salary Component", component_name, "type")
    if not component_type:
        frappe.throw(_(f"Salary Component '{component_name}' does not exist."))

    table_field = "earnings" if component_type == "Earning" else "deductions"

    # Avoid duplicates
    if any(r.salary_component == component_name for r in slip.get(table_field)):
        return False

    slip.append(table_field, {
        "salary_component": component_name,
        "amount"          : flt(amount),
    })
    return True


# ═════════════════════════════════════════════════════════════════════════════
def _infer_component_type(col_name, col_index, total_income_index, total_deductions_index):
    """
    Determines whether an unknown Excel column is an Earning or Deduction
    based purely on its position relative to 'Total Income' and
    'Total Deductions' columns.

    Layout assumption (matches Main_Salary_report):
        [fields] ... [earnings] ... Total Income ... [deductions] ... Total Deductions ... [fields]

    Returns 'Earning', 'Deduction', or None (if outside component range).
    """
    if total_income_index is not None and col_index < total_income_index:
        return "Earning"

    if (
        total_income_index is not None
        and total_deductions_index is not None
        and total_income_index < col_index < total_deductions_index
    ):
        return "Deduction"

    return None  # after Total Deductions — treat as a standard field, ignore


# ═════════════════════════════════════════════════════════════════════════════
@frappe.whitelist()
def check_salary_components(file_url):
    """
    Pre-flight check called from the listview dialog BEFORE the actual upload.

    Parses the Excel file and returns a list of salary components referenced
    in it that do NOT yet exist in ERPNext. The upload is blocked until all
    returned components are either created or skipped by the user.

    Returns:
        [{"name": "Basic", "type": "Earning"}, ...]
    """
    rows    = _parse_excel(file_url)
    seen    = set()     # avoid duplicate entries across rows
    missing = []

    for row in rows:
        raw                    = row.get("__raw__", {})
        col_index              = row.get("__col_index__", {})
        total_income_index     = row.get("__total_income_index__")
        total_deductions_index = row.get("__total_deductions_index__")

        # ── Known earnings ────────────────────────────────────────────────────
        for component, excel_col in EARNINGS:
            if component in seen:
                continue
            if flt(raw.get(excel_col) or 0) > 0:
                seen.add(component)
                if not frappe.db.exists("Salary Component", component):
                    missing.append({"name": component, "type": "Earning"})

        # ── Known deductions ──────────────────────────────────────────────────
        for component, excel_col in DEDUCTIONS:
            if component in seen:
                continue
            if flt(raw.get(excel_col) or 0) > 0:
                seen.add(component)
                if not frappe.db.exists("Salary Component", component):
                    missing.append({"name": component, "type": "Deduction"})

        # ── Dynamic columns ───────────────────────────────────────────────────
        for col_name, value in raw.items():
            if col_name in _ALL_KNOWN_COLS or col_name in seen:
                continue
            if flt(value or 0) <= 0:
                continue

            idx            = col_index.get(col_name)
            component_type = _infer_component_type(
                col_name, idx, total_income_index, total_deductions_index
            )
            if component_type is None:
                continue

            seen.add(col_name)
            if not frappe.db.exists("Salary Component", col_name):
                missing.append({"name": col_name, "type": component_type})

    return missing


# ═════════════════════════════════════════════════════════════════════════════
@frappe.whitelist()
def upload_salary_slips(file_url, skipped_components=None, start_date=None, end_date=None):
    from frappe.utils import today, get_first_day, get_last_day

    if isinstance(skipped_components, str):
        skipped_components = json.loads(skipped_components)
    skipped_components = set(skipped_components or [])

    dialog_start = _clean_date(start_date)
    dialog_end   = _clean_date(end_date)

    _today = today()

    # If user set dialog dates → use them; else → current month
    if dialog_start and dialog_end:
        slip_start   = dialog_start
        slip_end     = dialog_end
        slip_posting = _today
    else:
        slip_start   = str(get_first_day(_today))
        slip_end     = str(get_last_day(_today))
        slip_posting = _today

    rows    = _parse_excel(file_url)
    created = []
    skipped = []
    company = frappe.defaults.get_global_default("company")

    for row in rows:
        emp = str(row.get("employee", "")).strip()
        if not emp:
            skipped.append("Row skipped – Employee ID (Code) is missing")
            continue

        try:
            name = _create_slip(
                row, company, slip_posting, slip_start, slip_end,
                skipped_components=skipped_components,
            )
            created.append(name)
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"Salary Slip Upload – {emp}")
            skipped.append(f"{emp} – {str(e)}")

    return {
        "created"   : created,
        "skipped"   : skipped,
        "start_date": slip_start,
        "end_date"  : slip_end,
    }
# ═════════════════════════════════════════════════════════════════════════════
def _parse_excel(file_url):
    """
    Reads the Excel file. For each data row returns a dict containing:
      - Standard fields mapped via COLUMN_MAP
      - __raw__      : original {col_name: value} dict
      - __col_index__: {col_name: index} for position-based type inference
      - __total_income_index__     : int
      - __total_deductions_index__ : int
    """
    file_doc  = frappe.get_doc("File", {"file_url": file_url})
    file_path = file_doc.get_full_path()

    if not os.path.exists(file_path):
        frappe.throw(_("Uploaded file not found on disk: {0}").format(file_path))

    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb.active

    rows_iter   = ws.iter_rows(values_only=True)
    raw_headers = next(rows_iter, None)

    if not raw_headers:
        frappe.throw(_("Excel file is empty or has no header row"))

    headers = [str(h).strip() if h else "" for h in raw_headers]

    # Build column-index lookup
    col_index = {h: i for i, h in enumerate(headers)}
    total_income_index     = col_index.get("Total Income")
    total_deductions_index = col_index.get("Total Deductions")

    results = []
    for raw_row in rows_iter:
        row_dict = dict(zip(headers, raw_row))

        code = str(row_dict.get("Code", "") or "").strip()
        if not code or code.lower() == "report total":
            continue

        # Map standard fields
        mapped = {}
        for excel_col, internal_key in COLUMN_MAP.items():
            mapped[internal_key] = row_dict.get(excel_col, "") or ""

        # Attach metadata for dynamic detection
        mapped["__raw__"]                    = row_dict
        mapped["__col_index__"]              = col_index
        mapped["__total_income_index__"]     = total_income_index
        mapped["__total_deductions_index__"] = total_deductions_index

        results.append(mapped)

    return results
# ═════════════════════════════════════════════════════════════════════════════
def _create_slip(row, company, posting_date, start_date, end_date,
                 skipped_components=None):
    """
    Creates and inserts a single Salary Slip. Returns the slip name.

    Args:
        skipped_components : set of component names to silently ignore.
    """
    skipped_components = skipped_components or set()
    employee           = str(row.get("employee", "")).strip()

    # Duplicate guard ─────────────────────────────────────────────────────────
    existing = frappe.db.get_value(
        "Salary Slip",
        {
            "employee"  : employee,
            "start_date": start_date,
            "end_date"  : end_date,
            "docstatus" : ["!=", 2],
        },
        "name",
    )
    if existing:
        frappe.throw(
            _(f"Salary Slip {existing} already exists for {employee} in this period")
        )

    # Fetch latest active salary structure ────────────────────────────────────
    result = frappe.db.get_all(
        "Salary Structure Assignment",
        filters={"employee": employee, "docstatus": 1},
        fields=["salary_structure"],
        order_by="from_date desc",
        limit=1,
    )
    salary_structure = result[0].salary_structure if result else None

    slip                   = frappe.new_doc("Salary Slip")
    slip.employee          = employee
    slip.company           = company
    slip.posting_date      = posting_date
    slip.start_date        = start_date
    slip.end_date          = end_date
    slip.payroll_frequency = "Monthly"

    if salary_structure:
        slip.salary_structure = salary_structure

    # Payment days ─────────────────────────────────────────────────────────────
    slip.total_working_days   = flt(row.get("total_working_days") or 0)
    slip.payment_days         = flt(row.get("payment_days") or 0)
    slip.absent_days          = flt(row.get("absent_days") or 0)
    slip.leave_without_pay    = 0.0
    slip.custom_vacation_days = flt(row.get("vacation_days") or 0)

    raw                    = row.get("__raw__", {})
    col_index              = row.get("__col_index__", {})
    total_income_index     = row.get("__total_income_index__")
    total_deductions_index = row.get("__total_deductions_index__")

    # ── Step 1: Known Earnings ────────────────────────────────────────────────
    for component, excel_col in EARNINGS:
        if component in skipped_components:
            continue
        amount = flt(raw.get(excel_col) or 0)
        if amount > 0:
            _ensure_component(component, "Earning")
            _add_component_to_slip(slip, component, amount)

    # ── Step 2: Known Deductions ──────────────────────────────────────────────
    for component, excel_col in DEDUCTIONS:
        if component in skipped_components:
            continue
        amount = flt(raw.get(excel_col) or 0)
        if amount > 0:
            _ensure_component(component, "Deduction")
            _add_component_to_slip(slip, component, amount)

    # ── Step 3: Dynamic — any unknown column with a value ─────────────────────
    for col_name, value in raw.items():
        if col_name in _ALL_KNOWN_COLS:
            continue
        if col_name in skipped_components:
            continue

        amount = flt(value or 0)
        if amount <= 0:
            continue

        idx            = col_index.get(col_name)
        component_type = _infer_component_type(
            col_name, idx, total_income_index, total_deductions_index
        )

        if component_type is None:
            continue

        _ensure_component(col_name, component_type)
        _add_component_to_slip(slip, col_name, amount)

    # ── Totals — recalculated from actual slip rows ───────────────────────────
    # slip.gross_pay       = flt(raw.get("Total Income") or 0)
    # slip.total_deduction = sum(flt(d.amount) for d in slip.get("deductions"))
    # slip.net_pay         = slip.gross_pay - slip.total_deduction

    # Disbursement custom fields ───────────────────────────────────────────────
    slip.cash_payments     = flt(raw.get("Cash Payments") or 0)
    slip.bank_payments     = flt(raw.get("Bank Payments") or 0)
    slip.check_payments    = flt(raw.get("Check Payments") or 0)
    slip.exchange_payments = flt(raw.get("Exchange Payments") or 0)

    # Bank details ─────────────────────────────────────────────────────────────
    if row.get("bank_name"):
        slip.bank_name = row["bank_name"]
    if row.get("bank_account_no"):
        slip.bank_account_no = str(row["bank_account_no"])

    # Build name manually so {employee} token is never None ───────────────────
    slip.name          = make_autoname("Sal Slip/" + employee + "/.####")
    slip.naming_series = "Sal Slip/{employee}/.####"

    slip.flags.ignore_permissions = True
    # slip.flags.ignore_validate    = True
    slip.flags.ignore_mandatory   = True
    slip.flags.name_set           = True

    slip.insert()

    return slip.name

# ═════════════════════════════════════════════════════════════════════════════
@frappe.whitelist()
def move_component_in_draft_slips(component_name, old_type, new_type):
    """
    Called from the Salary Component Client Script after_save when the type changes.
    Moves the component row from the old table to the new table in every
    Draft Salary Slip (docstatus = 0) and recalculates totals.

    Args:
        component_name : Salary Component name  e.g. "PF"
        old_type       : "Earning" or "Deduction"  (what it WAS)
        new_type       : "Earning" or "Deduction"  (what it IS NOW)

    Returns:
        {"updated": ["Sal Slip/130141/0002", ...]}
    """
    old_table = "earnings"   if old_type == "Earning" else "deductions"
    new_table = "earnings"   if new_type == "Earning" else "deductions"

    # Find every Salary Detail row for this component in the OLD table
    affected = frappe.db.get_all(
        "Salary Detail",
        filters={
            "salary_component": component_name,
            "parenttype"      : "Salary Slip",
            "parentfield"     : old_table,
        },
        fields=["parent", "amount"],
    )

    if not affected:
        return {"updated": []}

    # Keep only Draft slips
    draft_parents = {
        r.name
        for r in frappe.db.get_all(
            "Salary Slip",
            filters={
                "name"     : ["in", list({r.parent for r in affected})],
                "docstatus": 0,
            },
            fields=["name"],
        )
    }

    if not draft_parents:
        return {"updated": []}

    updated = []

    for row in affected:
        if row.parent not in draft_parents:
            continue

        slip = frappe.get_doc("Salary Slip", row.parent)

        # Remove from old table
        slip.set(
            old_table,
            [r for r in slip.get(old_table) if r.salary_component != component_name],
        )

        # Add to new table (guard against duplicates)
        if not any(r.salary_component == component_name for r in slip.get(new_table)):
            slip.append(new_table, {
                "salary_component": component_name,
                "amount"          : row.amount,
            })

        # Recalculate totals
        slip.gross_pay       = sum(flt(r.amount) for r in slip.get("earnings"))
        slip.total_deduction = sum(flt(r.amount) for r in slip.get("deductions"))
        slip.net_pay         = slip.gross_pay - slip.total_deduction

        slip.flags.ignore_permissions = True
        slip.flags.ignore_validate    = True
        slip.save()

        updated.append(row.parent)

    frappe.db.commit()
    return {"updated": updated}


@frappe.whitelist()
def download_salary_slip_template():
    from frappe.utils.xlsxutils import make_xlsx

    columns = [
        # Standard identification
        "S",
        "Code",
        "Employee Name",
        # Attendance
        "No. of Days",
        "Working Days",
        "Vacation Days",
        "Absence",
        # Known Earnings (EARNINGS list)
        "Basic Salary",
        "Worth Salary",
        "Working Days Amount",
        "Housing Allowance",
        "Transportation Allowance",
        "Food Allowance",
        "Other Allowances",
        "Overtime",
        "Other Income",
        "Vacation Days Amount",
        # Totals
        "Total Income",
        # Known Deductions (DEDUCTIONS list)
        "Social Security",
        "Health Insurance",
        "Loans and Deductions",
        # Net & Disbursement
        "Total Deductions",
        "Net Salary",
        "Cash Payments",
        "Bank Payments",
        "Check Payments",
        "Exchange Payments",
        "Main Bank",
        "Account Number",
    ]

    data = [columns]  # Header row only — user fills the rest

    xlsx_file = make_xlsx(data, "Salary Slip Template")

    frappe.response["filename"]    = "Salary_Slip_Template.xlsx"
    frappe.response["filecontent"] = xlsx_file.getvalue()
    frappe.response["type"]        = "binary"