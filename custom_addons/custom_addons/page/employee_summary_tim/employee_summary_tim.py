import frappe
from frappe.utils import getdate, add_days, flt, date_diff



@frappe.whitelist()
def get_timesheet_data(
    from_date,
    to_date,
    employee=None,
    branch=None,
    employment_type=None,
    employee_category=None
):

    filters = frappe._dict({
        "from_date": from_date,
        "to_date": to_date,
        "employee": employee,
        "branch": branch,
        "employment_type": employment_type,
        "employee_category": employee_category
    })

    columns = get_columns(filters)
    data = get_data(filters)

    return {
        "columns": columns,
        "data": data
    }


def get_columns(filters):

    columns = [
        {"label": "SN", "fieldname": "sn"},
        {"label": "EMP. ID", "fieldname": "employee"},
        {"label": "EMP. NAME", "fieldname": "employee_name"},
        {"label": "JOB TITLE", "fieldname": "designation"},
        {"label": "NATIONALITY", "fieldname": "custom_nationality"},
        {"label": "IMC REF #", "fieldname": "parent_project"},
        {"label": "TOTAL MONTHLY NORMAL HOURS", "fieldname": "total_hours"},
        {"label": "TOTAL NO. OF DAYS", "fieldname": "total_days"},
        {"label": "TOTAL FRIDAY OVERTIME", "fieldname": "total_friday_ot"},
        {"label": "TOTAL DAILY OVERTIME", "fieldname": "total_daily_ot"},
        {"label": "TOTAL MONTHLY OVERTIME", "fieldname": "total_ot_hours"},
        {"label": "Remarks", "fieldname": "remarks"},
    ]

    from_date = getdate(filters.from_date)
    to_date = getdate(filters.to_date)

    curr = from_date

    while curr <= to_date:

        d_str = curr.strftime("%Y-%m-%d")

        columns.append({
            "label": curr.strftime("%d-%b"),
            "day": curr.strftime("%a"),
            "fieldname": f"nh_{d_str}",
            "type": "NH"
        })

        columns.append({
            "label": curr.strftime("%d-%b"),
            "day": curr.strftime("%a"),
            "fieldname": f"ot_{d_str}",
            "type": "OT"
        })

        curr = add_days(curr, 1)

    return columns


def get_data(filters):

    from_date = getdate(filters.from_date)
    to_date = getdate(filters.to_date)

    diff_days = date_diff(to_date, from_date) + 1

    # =========================================
    # THEORETICAL NH
    # =========================================

    theoretical_nh = 0

    temp_date = from_date

    while temp_date <= to_date:

        if temp_date.weekday() != 4:
            theoretical_nh += 8

        temp_date = add_days(temp_date, 1)

    # =========================================
    # CONDITIONS
    # =========================================

    conditions = ""

    if filters.employee:
        conditions += " AND emp.name = %(employee)s "

    if filters.branch:
        conditions += " AND emp.branch = %(branch)s "

    if filters.employment_type:
        conditions += """
            AND emp.employment_type = %(employment_type)s
        """

    if filters.employee_category == "Company Employee":

        conditions += """
            AND (
                IFNULL(emp.branch, '') = ''
                AND emp.employment_type = 'Full-time'
            )
        """

    elif filters.employee_category == "Non-Company":

        conditions += """
            AND NOT (
                IFNULL(emp.branch, '') = ''
                AND emp.employment_type = 'Full-time'
            )
        """

    # =========================================
    # EMPLOYEES
    # =========================================

    employees = frappe.db.sql(f"""
        SELECT
            emp.name,
            emp.employee_name,
            emp.designation,
            emp.custom_nationality

        FROM `tabEmployee` emp

        WHERE emp.status = 'Active'
        {conditions}

        ORDER BY emp.employee_name

    """, filters, as_dict=1)

    # =========================================
    # TIMESHEETS
    # =========================================

    ts_details = frappe.db.sql("""

        SELECT
            ts.employee,

            DATE(tsd.from_time) as date,

            SUM(IFNULL(tsd.working_hours, 0)) as nh,

            SUM(IFNULL(tsd.ot_hrs, 0)) as ot,

            GROUP_CONCAT(
                DISTINCT ts.parent_project
                SEPARATOR ' / '
            ) as projects

        FROM `tabTimesheet` ts

        INNER JOIN `tabTimesheet Detail` tsd
            ON ts.name = tsd.parent

        WHERE ts.docstatus = 1

        AND DATE(tsd.from_time)
            BETWEEN %(from_date)s
            AND %(to_date)s

        GROUP BY
            ts.employee,
            DATE(tsd.from_time)

    """, filters, as_dict=1)

    ts_map = {
        (d.employee, str(d.date)): d
        for d in ts_details
    }

    emp_projects = {
        d.employee: d.projects
        for d in ts_details if d.projects
    }

    # =========================================
    # ATTENDANCE
    # =========================================

    attendance_records = frappe.db.sql("""

        SELECT
            employee,
            attendance_date,
            status,
            leave_type

        FROM `tabAttendance`

        WHERE attendance_date
            BETWEEN %(from_date)s
            AND %(to_date)s

        AND (
            status = 'Absent'
            OR leave_type IS NOT NULL
        )

    """, filters, as_dict=1)

    attendance_map = {}

    for att in attendance_records:

        key = att.employee

        if key not in attendance_map:
            attendance_map[key] = {}

        date_str = getdate(
            att.attendance_date
        ).strftime("%d-%b")

        if att.status == "Absent":

            if "Absent" not in attendance_map[key]:
                attendance_map[key]["Absent"] = []

            attendance_map[key]["Absent"].append(date_str)

        elif att.leave_type:

            if att.leave_type not in attendance_map[key]:
                attendance_map[key][att.leave_type] = []

            attendance_map[key][att.leave_type].append(date_str)

    # =========================================
    # FINAL DATA
    # =========================================

    final_data = []

    for i, emp in enumerate(employees, 1):

        row = {
            "sn": i,
            "employee": emp.name,
            "employee_name": emp.employee_name,
            "designation": emp.designation,
            "custom_nationality": emp.custom_nationality,
            "parent_project": emp_projects.get(emp.name, ""),
            "total_hours": theoretical_nh,
            "total_days": diff_days,
            "total_friday_ot": 0,
            "total_daily_ot": 0,
            "total_ot_hours": 0,
            "remarks": ""
        }

        curr = from_date

        while curr <= to_date:

            d_str = str(curr)

            log = ts_map.get(
                (emp.name, d_str),
                {"nh": 0, "ot": 0}
            )

            val_nh = flt(log["nh"], 2)
            val_ot = flt(log["ot"], 2)

            row[f"nh_{d_str}"] = val_nh
            row[f"ot_{d_str}"] = val_ot

            if curr.weekday() == 4:

                row["total_friday_ot"] += (
                    val_nh + val_ot
                )

            else:

                row["total_daily_ot"] += val_ot

            curr = add_days(curr, 1)

        row["total_ot_hours"] = (
            row["total_friday_ot"]
            + row["total_daily_ot"]
        )

        # =========================================
        # REMARKS
        # =========================================

        remarks = []

        emp_attendance = attendance_map.get(
            emp.name,
            {}
        )

        for remark_type, dates in emp_attendance.items():

            remarks.append(
                f"{remark_type.upper()} "
                f"({', '.join(dates)})"
            )

        row["remarks"] = " | ".join(remarks)

        final_data.append(row)

    return final_data