# import frappe
# import pandas as pd
# import os
# from frappe.utils import today, get_datetime, getdate, add_to_date, flt, time_diff_in_hours

# @frappe.whitelist()
# def upload_timesheet(file_url):
#     file_doc = frappe.get_doc("File", {"file_url": file_url})
#     file_path = file_doc.get_full_path()

#     # 1. ROBUST FILE READING
#     ext = os.path.splitext(file_path)[1].lower()
#     df_raw = None
    
#     try:
#         if ext == ".csv":
#             # Try different encodings to solve the 0xa0 (latin1) error
#             for enc in ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']:
#                 try:
#                     df_raw = pd.read_csv(file_path, encoding=enc, header=None)
#                     break 
#                 except (UnicodeDecodeError, TypeError):
#                     continue
#         elif ext in [".xlsx", ".xls"]:
#             df_raw = pd.read_excel(file_path, engine="openpyxl", header=None)
        
#         if df_raw is None:
#             frappe.throw("Could not read file. The character encoding is not supported.")

#     except Exception as e:
#         frappe.throw(f"Error reading file: {str(e)}")

#     # 2. FIND HEADER ROW DYNAMICALLY
#     header_idx = None
#     for i, row in df_raw.iterrows():
#         # Clean the row values for comparison
#         row_values = [str(val).strip().lower() for val in row.values if pd.notna(val)]
#         if "employees id" in row_values:
#             header_idx = i
#             break

#     if header_idx is None:
#         frappe.throw("Could not find 'Employees id' column. Please check your file headers.")

#     # 3. CLEAN AND PREPARE DATA
#     # Use the identified row as header
#     df = df_raw.iloc[header_idx + 1:].copy()
#     raw_headers = [str(c).strip().replace("\xa0", " ") for c in df_raw.iloc[header_idx]]
#     df.columns = raw_headers
    
#     # Remove non-breaking spaces from data values as well
#     df = df.applymap(lambda x: str(x).strip().replace("\xa0", " ") if pd.notna(x) else "")

#     created = []
#     skipped = []

#     # 4. LOOP AND CALCULATE
#     for i, row in df.iterrows():
#         emp_id = row.get("Employees id")
#         if not emp_id or emp_id.lower() in ["nan", ""]: 
#             continue
            
#         emp_id = emp_id.split('.')[0]

#         if not frappe.db.exists("Employee", emp_id):
#             skipped.append(f"Row {i+1}: Employee {emp_id} not found")
#             continue

#         try:
#             # Parse Date
#             row_date = getdate(row.get("Date") or today())
            
#             # Clean time strings (replace . with : so 17.00 becomes 17:00)
#             in_str = (row.get("In Time") or "08:00").replace(".", ":")
#             out_str = (row.get("Out Time") or "17:00").replace(".", ":")

#             from_time = get_datetime(f"{row_date} {in_str}")
#             to_time = get_datetime(f"{row_date} {out_str}")

#             # CALCULATIONS
#             # Total Duration for the 'hours' field (ERPNext uses this for total)
#             total_worked_hrs = time_diff_in_hours(to_time, from_time)
            
#             # Normal and OT from Excel
#             normal_hrs_excel = flt(row.get("Normal") or 0)
#             ot_hrs_excel = flt(row.get("OT") or 0)

#             project_id = row.get("IMC Ref #") or row.get("\nIMC Ref #")
#             company = frappe.db.get_value("Employee", emp_id, "company")
            
#             ts = frappe.new_doc("Timesheet")
#             ts.employee = emp_id
#             ts.company = company
#             ts.start_date = row_date
#             ts.end_date = row_date
            
#             if project_id and frappe.db.exists("Project", project_id):
#                 ts.parent_project = project_id

#             ts.append("time_logs", {
#                 "activity_type": "Work",
#                 "from_time": from_time,
#                 "to_time": to_time,
#                 "hours": total_worked_hrs, # Total Shift Duration
#                 "custom_normal_hours": normal_hrs_excel, # Mapping Excel Normal
#                 "ot_hrs": ot_hrs_excel, # Mapping Excel OT
#                 "project": project_id if frappe.db.exists("Project", project_id) else None,
#                 "discussion": row.get("Remark"),
#                 "description": row.get("Remark") or "Excel Upload"
#             })

#             ts.insert(ignore_permissions=True)
#             ts.save(ignore_permissions=True)
#             created.append(ts.name)

#         except Exception as e:
#             frappe.log_error(frappe.get_traceback(), "Timesheet Upload Error")
#             skipped.append(f"Row {i+1}: {str(e)}")

#     frappe.db.commit()
#     return {"created": created, "skipped": skipped}


#####################################################################################################

import frappe
import pandas as pd
import os
from frappe import _
from datetime import datetime, time
from frappe.utils import today, get_datetime, getdate, add_to_date, flt, time_diff_in_hours

@frappe.whitelist()
def mass_submit_timesheets(names):
    if isinstance(names, str):
        import json
        names = json.loads(names)

    count = 0
    errors = []

    for name in names:
        try:
            doc = frappe.get_doc("Timesheet", name)
            if doc.docstatus == 0:  # Only submit Drafts
                doc.submit()
                count += 1
        except Exception as e:
            errors.append(f"Error submitting {name}: {str(e)}")

    if errors:
        frappe.msgprint({
            "title": _("Partial Success"),
            "indicator": "orange",
            "message": _("Submitted {0} docs. Errors encountered:<br>{1}").format(count, "<br>".join(errors))
        })
    
    return count

@frappe.whitelist()
def upload_timesheet(file_url):
    # Get file details and path
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    file_path = file_doc.get_full_path()

    # 1. ROBUST FILE READING
    ext = os.path.splitext(file_path)[1].lower()
    df_raw = None
    
    try:
        if ext == ".csv":
            for enc in ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']:
                try:
                    df_raw = pd.read_csv(file_path, encoding=enc, header=None)
                    break 
                except (UnicodeDecodeError, TypeError):
                    continue
        elif ext in [".xlsx", ".xls"]:
            df_raw = pd.read_excel(file_path, engine="openpyxl", header=None)
        
        if df_raw is None:
            frappe.throw("Could not read file. The character encoding is not supported.")

    except Exception as e:
        frappe.throw(f"Error reading file: {str(e)}")

    # 2. FIND HEADER ROW DYNAMICALLY
    header_idx = None
    for i, row in df_raw.iterrows():
        row_values = [str(val).strip().lower() for val in row.values if pd.notna(val)]
        if "employees id" in row_values:
            header_idx = i
            break

    if header_idx is None:
        frappe.throw("Could not find 'Employees id' column. Please check your file headers.")

    # 3. CLEAN AND PREPARE DATA
    df = df_raw.iloc[header_idx + 1:].copy()
    raw_headers = [str(c).strip().replace("\xa0", " ") for c in df_raw.iloc[header_idx]]
    df.columns = raw_headers
    
    # Clean whitespace and handle NaNs
    df = df.applymap(lambda x: str(x).strip().replace("\xa0", " ") if pd.notna(x) else "")

    created = []
    skipped = []

    # 4. LOOP AND CALCULATE
    for i, row in df.iterrows():
        emp_id = row.get("Employees id")
        if not emp_id or emp_id.lower() in ["nan", ""]: 
            continue
            
        # Clean ID (e.g., 'EMP-001.0' -> 'EMP-001')
        emp_id = emp_id.split('.')[0]

        # Fetch Company and Custom Rates from Employee Master (The 'emp_data' object)
        emp_data = frappe.db.get_value("Employee", emp_id, 
            ["company", "working_hour_rate", "ot_hour_rate"], as_dict=True)

        if not emp_data:
            skipped.append(f"Row {i+1}: Employee {emp_id} not found in system")
            continue

        try:
            # Parse Date and Time Strings
            row_date = getdate(row.get("Date") or today())
            in_str = (row.get("In Time") or "08:00").replace(".", ":")
            out_str = (row.get("Out Time") or "17:00").replace(".", ":")

            from_time = get_datetime(f"{row_date} {in_str}")
            to_time = get_datetime(f"{row_date} {out_str}")

            # Calculate total duration
            total_worked_hrs = time_diff_in_hours(to_time, from_time)
            
            project_id = row.get("IMC Ref #") or row.get("\nIMC Ref #")
            
            # Create main Timesheet Document
            ts = frappe.new_doc("Timesheet")
            ts.employee = emp_id
            ts.company = emp_data.company  # Fixed: Accessing via emp_data
            ts.start_date = row_date
            ts.end_date = row_date
            
            if project_id and frappe.db.exists("Project", project_id):
                ts.parent_project = project_id

            # Append the time log row with correct Rates from Employee
            ts.append("time_logs", {
                "activity_type": "Work",
                "from_time": from_time,
                "to_time": to_time,
                "hours": total_worked_hrs,
                # FIXED: These now use 'emp_data.' to avoid NameError
                "working_hour_rate_": flt(emp_data.working_hour_rate) or 0,
                "ot_hours_rate_": flt(emp_data.ot_hour_rate) or 0,
                # Other Excel fields
                "project": project_id if frappe.db.exists("Project", project_id) else None,
                "discussion": row.get("Remark"),
                "description": row.get("Remark") or "Excel Upload"
            })

            # 5. CALCULATION BLOCK (OFFICE HOURS VS OT)
            OFFICE_START = time(8, 0, 0)
            OFFICE_END = time(17, 0, 0)

            for d in ts.time_logs:
                if not d.from_time or not d.to_time:
                    continue

                from_dt = d.from_time
                to_dt = d.to_time

                if to_dt <= from_dt:
                    continue

                total_hours = (to_dt - from_dt).total_seconds() / 3600

                office_start_dt = datetime.combine(from_dt.date(), OFFICE_START)
                office_end_dt = datetime.combine(from_dt.date(), OFFICE_END)

                # Determine overlap with 08:00 - 17:00
                normal_start = max(from_dt, office_start_dt)
                normal_end = min(to_dt, office_end_dt)

                normal_hours = 0
                if normal_end > normal_start:
                    normal_hours = (normal_end - normal_start).total_seconds() / 3600

                ot_hours = total_hours - normal_hours

                # Update row values
                d.working_hours = round(normal_hours, 2)
                d.ot_hrs = round(ot_hours, 2)
                d.hours = round(normal_hours, 2)

            # Insert document into database
            ts.insert(ignore_permissions=True)
            created.append(ts.name)

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Timesheet Upload Error")
            skipped.append(f"Row {i+1}: {str(e)}")

    # Commit changes to database
    frappe.db.commit()
    
    return {"created": created, "skipped": skipped}