import frappe
import pandas as pd
import os
from frappe import _
from frappe.utils import getdate, today, flt


# @frappe.whitelist()
# def mass_submit_rental_equipment_timesheets(names):
#     if isinstance(names, str):
#         import json
#         names = json.loads(names)

#     count = 0
#     errors = []

#     for name in names:
#         try:
#             doc = frappe.get_doc("Rental Equipment Timesheet", name)
#             if doc.docstatus == 0:  # Only submit Drafts
#                 doc.submit()
#                 count += 1
#         except Exception as e:
#             errors.append(f"Error submitting {name}: {str(e)}")

#     if errors:
#         frappe.msgprint({
#             "title": _("Partial Success"),
#             "indicator": "orange",
#             "message": _("Submitted {0} docs. Errors encountered:<br>{1}").format(count, "<br>".join(errors))
#         })

#     return count


@frappe.whitelist()
def upload_rental_equipment_timesheet(file_url):
    """
    Reads an Excel file and creates Rental Equipment Timesheet documents.

    Expected Excel columns (row 1 = headers):
        SN | EQUIPMENT NAME | Project ID | Door No-Plate No |
        Operator Nationality | Supplier Name | Hour | Date
    """

    # ── 1. RESOLVE FILE PATH ────────────────────────────────────────────────
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    file_path = file_doc.get_full_path()

    ext = os.path.splitext(file_path)[1].lower()

    # ── 2. READ FILE ─────────────────────────────────────────────────────────
    try:
        if ext == ".csv":
            df = None
            for enc in ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']:
                try:
                    df = pd.read_csv(file_path, encoding=enc)
                    break
                except (UnicodeDecodeError, TypeError):
                    continue
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path, engine="openpyxl")
        else:
            frappe.throw(_("Unsupported file type: {0}. Please upload .xlsx or .csv").format(ext))

        if df is None:
            frappe.throw(_("Could not read file. Please check the file encoding or format."))

    except Exception as e:
        frappe.throw(_("Error reading file: {0}").format(str(e)))

    # ── 3. NORMALIZE HEADERS ──────────────────────────────────────────────────
    # Strip whitespace and non-breaking spaces from column names
    df.columns = [str(c).strip().replace("\xa0", " ") for c in df.columns]

    # ── 4. VALIDATE REQUIRED COLUMNS ─────────────────────────────────────────
    required_cols = ["EQUIPMENT NAME", "Hour", "Date"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        frappe.throw(
            _("Missing required column(s): {0}. Found columns: {1}").format(
                ", ".join(missing), ", ".join(df.columns.tolist())
            )
        )

    # ── 5. CLEAN DATA ─────────────────────────────────────────────────────────
    df = df.applymap(lambda x: str(x).strip().replace("\xa0", " ") if pd.notna(x) else "")

    created = []
    skipped = []

    # ── 6. LOOP ROWS AND CREATE DOCS ──────────────────────────────────────────
    for i, row in df.iterrows():
        row_num = i + 2  # human-readable row number (1-indexed + header)

        # Skip completely empty rows
        equipment_name = row.get("EQUIPMENT NAME", "")
        if not equipment_name or equipment_name.lower() in ["nan", ""]:
            continue

        try:
            # ── Date ────────────────────────────────────────────────────────
            raw_date = row.get("Date", "")
            if not raw_date or raw_date.lower() in ["nan", ""]:
                row_date = getdate(today())
            else:
                row_date = getdate(raw_date)

            # ── Hours ───────────────────────────────────────────────────────
            raw_hours = row.get("Hour", "") or row.get("Hours", "")
            hours = flt(raw_hours) if raw_hours not in ["nan", ""] else 0.0

            # ── Project ID ──────────────────────────────────────────────────
            project_id = row.get("Project ID", "")
            if project_id.lower() in ["nan", ""]:
                project_id = None
            # Validate project exists
            if project_id and not frappe.db.exists("Project", project_id):
                project_id = None  # Don't block creation; just leave blank

            # ── Supplier Name ───────────────────────────────────────────────
            supplier_name = row.get("Supplier Name", "")
            if supplier_name.lower() in ["nan", ""]:
                supplier_name = None
            # Validate supplier exists in Supplier master
            if supplier_name and not frappe.db.exists("Supplier", supplier_name):
                supplier_name = None  # Leave blank if not found

            # ── Door No / Plate No ──────────────────────────────────────────
            door_plate = row.get("Door No-Plate No", "") or row.get("Door No or Plate No", "")
            if door_plate.lower() in ["nan", ""]:
                door_plate = None

            # ── Operator Nationality ────────────────────────────────────────
            operator_nationality = row.get("Operator Nationality", "")
            if operator_nationality.lower() in ["nan", "", "-"]:
                operator_nationality = None

            # ── Create Document ─────────────────────────────────────────────
            doc = frappe.new_doc("Rental Equipment Timesheet")

            # Map fields — fieldnames match what you see in the DocType Form
            doc.equipment_name        = equipment_name
            doc.date                  = row_date
            doc.hours                 = hours

            if project_id:
                doc.project_id        = project_id

            if supplier_name:
                doc.supplier_name     = supplier_name

            if door_plate:
                doc.door_no_or_plate_no = door_plate

            if operator_nationality:
                doc.operator_nationality = operator_nationality

            doc.insert(ignore_permissions=True)
            created.append(doc.name)

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Rental Equipment Timesheet Upload Error")
            skipped.append(f"Row {row_num} ({equipment_name}): {str(e)}")

    # ── 7. COMMIT AND RETURN ──────────────────────────────────────────────────
    frappe.db.commit()

    return {"created": created, "skipped": skipped}