import frappe
from frappe import _
from frappe.utils import getdate, add_days, flt, date_diff

def execute(filters=None):
    if not filters: filters = {}
    if not filters.get("from_date") or not filters.get("to_date"):
        return [], []

    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    columns = [
        {"label": _("SN"), "fieldname": "sn", "fieldtype": "Int", "width": 60},
        {"label": _("EMP. ID"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 110},
        {"label": _("EMP. NAME"), "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
        {"label": _("JOB TITLE"), "fieldname": "designation", "fieldtype": "Data", "width": 150},
        {"label": _("NATIONALITY"), "fieldname": "custom_nationality", "fieldtype": "Data", "width": 120},
        {"label": _("IMC REF #"), "fieldname": "parent_project", "fieldtype": "Data", "width": 180},
        {"label": _("TOTAL MONTHLY NORMAL HOURS"), "fieldname": "total_hours", "fieldtype": "Float", "width": 220},
        {"label": _("TOTAL NO. OF DAYS"), "fieldname": "total_days", "fieldtype": "Int", "width": 140},
        {"label": _("TOTAL FRIDAY OVERTIME"), "fieldname": "total_friday_ot", "fieldtype": "Float", "width": 180},
        {"label": _("TOTAL DAILY OVERTIME"), "fieldname": "total_daily_ot", "fieldtype": "Float", "width": 180},
        {"label": _("TOTAL MONTHLY OVERTIME"), "fieldname": "total_ot_hours", "fieldtype": "Float", "width": 180},
        {"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Data", "width": 250},
    ]

    from_date, to_date = getdate(filters.get("from_date")), getdate(filters.get("to_date"))
    curr = from_date
    while curr <= to_date:
        d_str = curr.strftime("%Y-%m-%d")
        label = curr.strftime("%-d-%b")
        columns.append({"label": _(f"{label} | NH"), "fieldname": f"nh_{d_str}", "fieldtype": "Float", "width": 110})
        columns.append({"label": _(f"{label} | OT"), "fieldname": f"ot_{d_str}", "fieldtype": "Float", "width": 110})
        curr = add_days(curr, 1)

    return columns

def get_data(filters):
    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))

    # 1. Formula Constants: Total No. of Days
    # date_diff is inclusive of the end date if we add +1
    diff_days = date_diff(to_date, from_date) + 1
    
    # Calculate Total Normal Hours (Excluding Fridays)
    theoretical_nh = 0
    temp_date = from_date
    while temp_date <= to_date:
        if temp_date.weekday() != 4: # Not Friday
            theoretical_nh += 8
        temp_date = add_days(temp_date, 1)

    # 2. Fetch Employees
    conditions = ""
    if filters.get("employee"): conditions += " AND emp.name = %(employee)s "
    
    employees = frappe.db.sql(f"""
        SELECT name, employee_name, designation, custom_nationality
        FROM `tabEmployee` emp
        WHERE status = 'Active' {conditions}
        ORDER BY employee_name ASC
    """, filters, as_dict=1)

    # 3. Fetch Timesheet Details for Overtime and Specific daily NH
    ts_details = frappe.db.sql("""
        SELECT 
            ts.employee, 
            DATE(tsd.from_time) as date,
            SUM(CASE WHEN tsd.hours > 0 THEN tsd.hours ELSE tsd.billing_hours END) as nh,
            SUM(IFNULL(tsd.ot_hrs, 0)) as ot,
            GROUP_CONCAT(DISTINCT ts.parent_project SEPARATOR ' / ') as projects
        FROM `tabTimesheet` ts
        JOIN `tabTimesheet Detail` tsd ON ts.name = tsd.parent
        WHERE ts.docstatus = 1 
          AND DATE(tsd.from_time) BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY ts.employee, DATE(tsd.from_time)
    """, filters, as_dict=1)

    ts_map = {(entry.employee, str(entry.date)): entry for entry in ts_details}
    emp_projects = {entry.employee: entry.projects for entry in ts_details if entry.projects}

    # 4. Process Rows
    final_data = []
    for i, emp in enumerate(employees, 1):
        row = {
            "sn": i, 
            "employee": emp.name, 
            "employee_name": emp.employee_name,
            "designation": emp.designation, 
            "custom_nationality": emp.custom_nationality,
            "total_days": diff_days,           # FORMULA: Days between dates
            "total_hours": theoretical_nh,     # FORMULA: (Days - Fridays) * 8
            "total_friday_ot": 0,
            "total_daily_ot": 0,
            "total_ot_hours": 0,
            "parent_project": emp_projects.get(emp.name, ""),
            "remarks": ""
        }

        curr = from_date
        while curr <= to_date:
            d_str = str(curr)
            log = ts_map.get((emp.name, d_str), {"nh": 0, "ot": 0})
            
            val_nh, val_ot = flt(log['nh']), flt(log['ot'])
            row[f"nh_{d_str}"] = val_nh
            row[f"ot_{d_str}"] = val_ot
            
            # FORMULA: Total Friday OT vs Daily OT
            if curr.weekday() == 4: # It's Friday
                # Total Friday OT = No of Worked Hours on Fridays Only
                # This includes both 'normal' hours and 'ot' hours logged on a Friday
                row["total_friday_ot"] += (val_nh + val_ot)
            else:
                # Total Daily OT = No of Overtime Hours Except Fridays
                row["total_daily_ot"] += val_ot
                
            curr = add_days(curr, 1)

        row["total_ot_hours"] = row["total_friday_ot"] + row["total_daily_ot"]
        final_data.append(row)

    return final_data