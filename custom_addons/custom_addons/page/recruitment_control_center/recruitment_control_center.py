import frappe


def _count(doctype, filters=None):
    """Count only records visible to the current user."""
    rows = frappe.get_list(doctype, filters=filters, fields=["count(name) as count"])
    return int(rows[0].count or 0) if rows else 0


@frappe.whitelist()
def get_filter_options():
    # Any user with read access to at least Job Opening can use this endpoint.
    frappe.has_permission("Job Opening", ptype="read", throw=True)
    try:
        companies = frappe.get_list("Company", fields=["name"], order_by="name asc")
        departments = frappe.get_list("Department", fields=["name"], order_by="name asc")
        designations = frappe.get_list("Designation", fields=["name"], order_by="name asc")
        job_openings = frappe.get_list("Job Opening", fields=["name", "job_title"], order_by="job_title asc")
        
        # User company info
        default_company = (
            frappe.defaults.get_user_default("Company")
            or frappe.db.get_single_value("Global Defaults", "default_company")
            or (companies[0].name if companies else "")
        )
        
        return {
            "companies": [c.name for c in companies],
            "departments": [d.name for d in departments],
            "designations": [d.name for d in designations],
            "job_openings": [{"name": j.name, "title": j.job_title or j.name} for j in job_openings],
            "default_company": default_company,
            "user_name": frappe.session.user
        }
    except Exception as e:
        frappe.log_error("get_filter_options error", str(e))
        return {
            "companies": [],
            "departments": [],
            "designations": [],
            "job_openings": [],
            "default_company": frappe.defaults.get_user_default("Company") or "",
            "user_name": frappe.session.user
        }

@frappe.whitelist()
def get_kpi_counts(company=None, department=None, designation=None, job_opening=None, status=None, from_date=None, to_date=None):
    # Require at least read on Job Opening as a proxy for the KPI dashboard.
    frappe.has_permission("Job Opening", ptype="read", throw=True)
    try:
        # Build filter dictionaries for doctypes
        # 1. Job Requisition (Pending)
        req_filters = {}
        if company:
            req_filters["company"] = company
        if department:
            req_filters["department"] = department
        if designation:
            req_filters["designation"] = designation
        if status and status != "All Statuses":
            req_filters["status"] = status
        else:
            req_filters["status"] = "Pending"
        if from_date:
            req_filters["creation"] = [">=", from_date]
        if to_date:
            if "creation" in req_filters:
                req_filters["creation"] = ["between", [from_date, to_date]]
            else:
                req_filters["creation"] = ["<=", to_date]
                
        pending_requisitions = _count("Job Requisition", req_filters)
        
        # 2. Planned Vacancies from Staffing Plan
        sp_filters = {"docstatus": 1}
        if company:
            sp_filters["company"] = company
        if department:
            sp_filters["department"] = department
        if from_date:
            sp_filters["to_date"] = [">=", from_date]
        if to_date:
            sp_filters["from_date"] = ["<=", to_date]

        plan_names = frappe.get_list("Staffing Plan", filters=sp_filters, pluck="name")
        planned_vacancies = 0
        if plan_names:
            detail_filters = {"parent": ["in", plan_names]}
            if designation:
                detail_filters["designation"] = designation
            plan_details = frappe.get_list(
                "Staffing Plan Detail",
                parent_doctype="Staffing Plan",
                filters=detail_filters,
                fields=["vacancies"],
            )
            planned_vacancies = int(sum(row.vacancies or 0 for row in plan_details))

        # 3. Open Openings & 4. Published Openings
        jo_filters = {}
        if company:
            jo_filters["company"] = company
        if department:
            jo_filters["department"] = department
        if designation:
            jo_filters["designation"] = designation
        if job_opening:
            jo_filters["name"] = job_opening
        if status and status != "All Statuses":
            jo_filters["status"] = status
        else:
            jo_filters["status"] = "Open"
        if from_date:
            jo_filters["posted_on"] = [">=", from_date]
        if to_date:
            if "posted_on" in jo_filters:
                jo_filters["posted_on"] = ["between", [from_date, to_date]]
            else:
                jo_filters["posted_on"] = ["<=", to_date]

        open_openings = _count("Job Opening", jo_filters)

        jo_pub_filters = dict(jo_filters)
        jo_pub_filters["publish"] = 1
        published_openings = _count("Job Opening", jo_pub_filters)

        # 5. Job Applicants
        app_filters = {}
        if designation:
            app_filters["designation"] = designation
        if job_opening:
            app_filters["job_title"] = job_opening
        if status and status != "All Statuses":
            app_filters["status"] = status
        if from_date:
            app_filters["creation"] = [">=", from_date]
        if to_date:
            if "creation" in app_filters:
                app_filters["creation"] = ["between", [from_date, to_date]]
            else:
                app_filters["creation"] = ["<=", to_date]
        applicants = _count("Job Applicant", app_filters)

        # 6. Interviews
        int_filters = {}
        if designation:
            int_filters["designation"] = designation
        if job_opening:
            int_filters["job_applicant"] = ["in", frappe.get_list("Job Applicant", filters={"job_title": job_opening}, pluck="name") or [""]]
        if from_date:
            int_filters["scheduled_on"] = [">=", from_date]
        if to_date:
            if "scheduled_on" in int_filters:
                int_filters["scheduled_on"] = ["between", [from_date, to_date]]
            else:
                int_filters["scheduled_on"] = ["<=", to_date]
        interviews = _count("Interview", int_filters)

        # 7. Feedback Pending (Interviews where interviewer feedback has not yet been submitted)
        fb_int_filters = {"status": ["not in", ["Cancelled"]], "docstatus": ["<", 2]}
        if designation:
            fb_int_filters["designation"] = designation
        if job_opening:
            fb_int_filters["job_opening"] = job_opening
        elif company or department:
            jo_filter = {}
            if company:
                jo_filter["company"] = company
            if department:
                jo_filter["department"] = department
            matching_openings = frappe.get_list("Job Opening", filters=jo_filter, pluck="name")
            if matching_openings:
                fb_int_filters["job_opening"] = ["in", matching_openings]
            else:
                fb_int_filters["job_opening"] = ["in", [""]]
        if from_date:
            fb_int_filters["scheduled_on"] = [">=", from_date]
        if to_date:
            if "scheduled_on" in fb_int_filters:
                fb_int_filters["scheduled_on"] = ["between", [from_date, to_date]]
            else:
                fb_int_filters["scheduled_on"] = ["<=", to_date]

        # Exclude interviews that already have submitted feedback
        interviews_with_feedback = frappe.get_list(
            "Interview Feedback",
            filters={"docstatus": 1},
            pluck="interview"
        )
        if interviews_with_feedback:
            fb_int_filters["name"] = ["not in", list(set(interviews_with_feedback))]

        feedback_pending = _count("Interview", fb_int_filters)

        # 8. Awaiting Response (Job Offer)
        offer_filters = {"status": "Awaiting Response"}
        if company:
            offer_filters["company"] = company
        if designation:
            offer_filters["designation"] = designation
        awaiting_response = _count("Job Offer", offer_filters)

        # 9. Onboarding Active
        onb_filters = {"boarding_status": ["in", ["Pending", "In Process"]]}
        if company:
            onb_filters["company"] = company
        if department:
            onb_filters["department"] = department
        if designation:
            onb_filters["designation"] = designation
        onboarding_active = _count("Employee Onboarding", onb_filters)

        # 10. Employees Hired (Converted applicants: Job Applicant with status "Accepted")
        hired_filters = {"status": "Accepted"}
        if designation:
            hired_filters["designation"] = designation
        if job_opening:
            hired_filters["job_title"] = job_opening
        if from_date:
            hired_filters["creation"] = [">=", from_date]
        if to_date:
            if "creation" in hired_filters:
                hired_filters["creation"] = ["between", [from_date, to_date]]
            else:
                hired_filters["creation"] = ["<=", to_date]
        employees_hired = _count("Job Applicant", hired_filters)

        return {
            "pending_requisitions": pending_requisitions,
            "planned_vacancies": planned_vacancies,
            "open_openings": open_openings,
            "published_openings": published_openings,
            "applicants": applicants,
            "interviews": interviews,
            "feedback_pending": feedback_pending,
            "awaiting_response": awaiting_response,
            "onboarding_active": onboarding_active,
            "employees_hired": employees_hired
        }
    except Exception as e:
        frappe.log_error("get_kpi_counts error", str(e))
        return {
            "pending_requisitions": 0,
            "planned_vacancies": 0,
            "open_openings": 0,
            "published_openings": 0,
            "applicants": 0,
            "interviews": 0,
            "feedback_pending": 0,
            "awaiting_response": 0,
            "onboarding_active": 0,
            "employees_hired": 0
        }

@frappe.whitelist()
def get_analytics_data():
    frappe.has_permission("Job Applicant", ptype="read", throw=True)
    try:
        from frappe.utils import format_date, nowdate
        
        today_date = nowdate()
        as_of_date = format_date(today_date, "d MMM YYYY")
        
        # 1. Requisitions
        req_total = _count("Job Requisition")
        req_pending = _count("Job Requisition", {"status": "Pending"})
        
        pending_req = frappe.get_list("Job Requisition", filters={"status": "Pending"}, fields=["designation", "name"], limit=1)
        if pending_req:
            req_name = pending_req[0].designation or pending_req[0].name
            req_subtitle = f"{req_name} requisition is awaiting approval"
        else:
            req_subtitle = "No requisitions awaiting approval"

        # 2. Open Job Openings
        jo_open = _count("Job Opening", {"status": "Open"})
        jo_published = _count("Job Opening", {"status": "Open", "publish": 1})

        # 3. Applicants
        app_total = _count("Job Applicant")
        app_accepted = _count("Job Applicant", {"status": "Accepted"})

        # 4. Interviews Pending
        int_pending = _count("Interview", {"status": ["in", ["Pending", "Under Review", "Scheduled"]]})

        # 5. Offers Awaiting
        offers_awaiting = _count("Job Offer", {"status": "Awaiting Response"})

        # 6. Onboarding Active & Overdue
        onb_active = _count("Employee Onboarding", {"boarding_status": ["in", ["Pending", "In Process"]]})
        
        # Calculate real onboarding overdue count from tasks belonging to onboarding projects
        onb_projects = frappe.get_list(
            "Employee Onboarding",
            filters=[["project", "is", "set"]],
            pluck="project"
        )
        task_overdue_filters = [
            ["exp_end_date", "<", today_date],
            ["status", "not in", ["Completed", "Cancelled"]]
        ]
        if onb_projects:
            task_overdue_filters.append(["project", "in", onb_projects])
        else:
            task_overdue_filters.append(["type", "=", "Onboarding"])
            
        onb_overdue = _count("Task", task_overdue_filters)

        kpis = {
            "open_requisitions": req_total,
            "pending_requisitions": req_pending,
            "open_job_openings": jo_open,
            "published_openings": jo_published,
            "applicants": app_total,
            "accepted_applicants": app_accepted,
            "interviews_pending": int_pending,
            "offers_awaiting": offers_awaiting,
            "onboarding_overdue": onb_overdue,
            "active_onboarding": onb_active,
        }

        # Hiring Funnel
        hiring_funnel = [
            {"stage": "Requisitions", "count": req_total},
            {"stage": "Job Openings", "count": jo_open},
            {"stage": "Applicants", "count": app_total},
            {"stage": "Interviews", "count": _count("Interview")},
            {"stage": "Job Offers", "count": _count("Job Offer")},
            {"stage": "Onboarding", "count": onb_active},
            {"stage": "Employees", "count": app_accepted},
        ]

        # Hiring Demand by Department (from Open Job Openings, Job Requisitions, or active Staffing Plans)
        dept_demand = {}
        openings = frappe.get_list(
            "Job Opening",
            filters={"status": "Open"},
            fields=["department", "vacancies"]
        )
        for jo in openings:
            dept = jo.department or "General"
            dept_demand[dept] = dept_demand.get(dept, 0) + (int(jo.vacancies) if jo.get("vacancies") else 1)

        if not dept_demand:
            requisitions = frappe.get_list(
                "Job Requisition",
                filters={"status": ["in", ["Pending", "Open"]]},
                fields=["department", "no_of_positions"]
            )
            for req in requisitions:
                dept = req.department or "General"
                dept_demand[dept] = dept_demand.get(dept, 0) + (int(req.no_of_positions) if req.get("no_of_positions") else 1)

        if not dept_demand:
            departments = frappe.get_list("Department", fields=["name"], limit=5)
            hiring_demand = [{"department": d.name, "count": 0} for d in departments]
        else:
            hiring_demand = [
                {"department": dept, "count": count}
                for dept, count in sorted(dept_demand.items(), key=lambda x: x[1], reverse=True)
            ]

        # Applicants by Status
        app_status_counts = {"Open": 0, "Replied": 0, "Hold": 0, "Accepted": 0, "Rejected": 0}
        db_app_statuses = frappe.get_list(
            "Job Applicant", fields=["status", "count(name) as count"], group_by="status"
        )
        for row in db_app_statuses:
            if row.status in app_status_counts:
                app_status_counts[row.status] = int(row.count or 0)

        applicants_by_status = [
            {"status": "Open", "count": app_status_counts.get("Open", 0)},
            {"status": "Replied", "count": app_status_counts.get("Replied", 0)},
            {"status": "Hold", "count": app_status_counts.get("Hold", 0)},
            {"status": "Accepted", "count": app_status_counts.get("Accepted", 0)},
            {"status": "Rejected", "count": app_status_counts.get("Rejected", 0)},
        ]

        # Offer Status
        offer_status_counts = {"Awaiting Response": 0, "Accepted": 0, "Rejected": 0}
        db_offer_statuses = frappe.get_list(
            "Job Offer", fields=["status", "count(name) as count"], group_by="status"
        )
        for row in db_offer_statuses:
            if row.status in offer_status_counts:
                offer_status_counts[row.status] = int(row.count or 0)

        offer_status = [
            {"status": "Awaiting Response", "count": offer_status_counts.get("Awaiting Response", 0)},
            {"status": "Accepted", "count": offer_status_counts.get("Accepted", 0)},
            {"status": "Rejected", "count": offer_status_counts.get("Rejected", 0)},
        ]

        # Needs Attention
        pending_interview = frappe.get_list(
            "Interview",
            filters={"status": ["in", ["Pending", "Under Review", "Scheduled"]]},
            fields=["name", "job_applicant", "interview_round"],
            limit=1
        )
        if pending_interview:
            round_name = pending_interview[0].interview_round or "Interview"
            int_subtitle = f"{round_name} remains under review"
        else:
            int_subtitle = "No interviews currently under review"

        pending_offer = frappe.get_list(
            "Job Offer",
            filters={"status": "Awaiting Response"},
            fields=["applicant_name", "job_applicant"],
            limit=1
        )
        if pending_offer:
            cand_name = pending_offer[0].applicant_name or pending_offer[0].job_applicant or "Candidate"
            offer_subtitle = f"{cand_name}'s response is still awaited"
        else:
            offer_subtitle = "No offers currently awaiting response"

        if onb_overdue > 0:
            onb_subtitle = f"{onb_overdue} onboarding task{'s have' if onb_overdue > 1 else ' has'} exceeded due date"
        else:
            onb_subtitle = "All onboarding tasks are on schedule"

        needs_attention = [
            {
                "key": "requisition_approvals",
                "icon": "clipboard-list",
                "bg": "#fef3c7",
                "color": "#d97706",
                "title": "Requisition approvals",
                "subtitle": req_subtitle,
                "badge_text": f"{req_pending} pending",
                "badge_color": "#d97706",
                "route_doctype": "Job Requisition",
                "route_filters": {"status": "Pending"}
            },
            {
                "key": "interview_followup",
                "icon": "messages-square",
                "bg": "#ede9fe",
                "color": "#7c3aed",
                "title": "Interview follow-up",
                "subtitle": int_subtitle,
                "badge_text": f"{int_pending} pending",
                "badge_color": "#2563eb",
                "route_doctype": "Interview",
                "route_filters": {}
            },
            {
                "key": "offer_responses",
                "icon": "mail-check",
                "bg": "#fce7f3",
                "color": "#db2777",
                "title": "Offer responses",
                "subtitle": offer_subtitle,
                "badge_text": f"{offers_awaiting} waiting",
                "badge_color": "#db2777",
                "route_doctype": "Job Offer",
                "route_filters": {"status": "Awaiting Response"}
            },
            {
                "key": "onboarding_deadlines",
                "icon": "triangle-alert",
                "bg": "#fee2e2",
                "color": "#dc2626",
                "title": "Onboarding task deadlines",
                "subtitle": onb_subtitle,
                "badge_text": f"{onb_overdue} overdue",
                "badge_color": "#dc2626",
                "route_doctype": "Employee Onboarding",
                "route_filters": {}
            }
        ]

        return {
            "as_of_date": as_of_date,
            "kpis": kpis,
            "hiring_funnel": hiring_funnel,
            "hiring_demand": hiring_demand,
            "applicants_by_status": applicants_by_status,
            "offer_status": offer_status,
            "needs_attention": needs_attention
        }
    except Exception as e:
        frappe.log_error("get_analytics_data error", str(e))
        now_formatted = ""
        try:
            from frappe.utils import format_date, nowdate
            now_formatted = format_date(nowdate(), "d MMM YYYY")
        except Exception:
            now_formatted = ""

        return {
            "as_of_date": now_formatted,
            "kpis": {
                "open_requisitions": 0,
                "pending_requisitions": 0,
                "open_job_openings": 0,
                "published_openings": 0,
                "applicants": 0,
                "accepted_applicants": 0,
                "interviews_pending": 0,
                "offers_awaiting": 0,
                "onboarding_overdue": 0,
                "active_onboarding": 0,
            },
            "hiring_funnel": [],
            "hiring_demand": [],
            "applicants_by_status": [],
            "offer_status": [],
            "needs_attention": []
        }


@frappe.whitelist()
def get_onboarding_tasks_data():
    """Returns all Employee Onboarding projects, their tasks, connections, and KPI stats."""
    frappe.has_permission("Task", ptype="read", throw=True)
    import json
    try:
        today = frappe.utils.today()
        user = frappe.session.user

        # 1. Fetch Employee Onboardings
        onboardings = frappe.get_list(
            "Employee Onboarding",
            fields=[
                "name", "employee", "employee_name", "job_applicant",
                "project", "boarding_status", "company", "department",
                "designation", "date_of_joining"
            ],
            order_by="creation desc"
        )

        onboarding_by_project = {}
        for onb in onboardings:
            if onb.get("project"):
                onboarding_by_project[onb["project"]] = onb

        # 2. Fetch Projects (linked or titled Onboarding)
        project_names = list(onboarding_by_project.keys())
        projects = []
        if project_names:
            projects = frappe.get_list(
                "Project",
                fields=["name", "project_name", "status", "company", "department", "percent_complete", "expected_start_date", "expected_end_date"],
                filters=[["name", "in", project_names]]
            )

        extra_projects = frappe.get_list(
            "Project",
            fields=["name", "project_name", "status", "company", "department", "percent_complete", "expected_start_date", "expected_end_date"],
            filters=[
                ["project_name", "like", "%Employee Onboarding%"],
                ["name", "not in", project_names]
            ] if project_names else [["project_name", "like", "%Employee Onboarding%"]]
        )
        all_projects = projects + extra_projects
        all_project_names = [p.name for p in all_projects]

        # Map project details
        project_meta = {}
        for p in all_projects:
            project_meta[p.name] = p

        # 3. Fetch Tasks
        task_filters = []
        if all_project_names:
            task_filters = [["project", "in", all_project_names]]
        else:
            task_filters = [["type", "=", "Onboarding"]]

        tasks = frappe.get_list(
            "Task",
            fields=[
                "name", "subject", "project", "status", "priority", "type",
                "progress", "exp_end_date", "exp_start_date", "expected_time",
                "color", "issue", "task_weight", "parent_task", "description",
                "is_group", "is_milestone", "review_date", "closing_date",
                "completed_by", "completed_on", "is_template", "start",
                "duration", "act_start_date", "act_end_date", "actual_time",
                "total_costing_amount", "total_billing_amount",
                "_assign", "modified", "creation", "company", "department"
            ],
            filters=task_filters,
            order_by="creation asc"
        )

        # Dependent tasks (child table "Task Depends On") keyed by parent task.
        task_names = [t.name for t in tasks]
        depends_on_map = {}
        if task_names:
            depends = frappe.get_list(
                "Task Depends On",
                parent_doctype="Task",
                fields=["parent", "task", "subject", "project"],
                filters=[["parent", "in", task_names]],
                order_by="idx asc",
            )
            for d in depends:
                depends_on_map.setdefault(d.parent, []).append({
                    "task": d.task or "",
                    "subject": d.subject or "",
                    "project": d.project or "",
                })

        # Collect assignees from ToDo (both Open and Closed assignments) so completed tasks retain assignees
        todo_assignees_map = {}
        if task_names:
            try:
                todos = frappe.get_list(
                    "ToDo",
                    fields=["reference_name", "allocated_to"],
                    filters=[
                        ["reference_type", "=", "Task"],
                        ["reference_name", "in", task_names],
                        ["status", "in", ["Open", "Closed"]],
                        ["allocated_to", "is", "set"]
                    ]
                )
                for td in todos:
                    if td.allocated_to:
                        todo_assignees_map.setdefault(td.reference_name, set()).add(td.allocated_to)
            except Exception:
                pass

        # Also collect assignees directly configured in Employee Boarding Activity
        activity_assignees_map = {}
        if task_names:
            try:
                activities = frappe.get_list(
                    "Employee Boarding Activity",
                    parent_doctype="Employee Onboarding",
                    fields=["task", "user"],
                    filters=[
                        ["task", "in", task_names],
                        ["user", "is", "set"]
                    ]
                )
                for act in activities:
                    if act.user:
                        activity_assignees_map.setdefault(act.task, set()).add(act.user)
            except Exception:
                pass

        # Build list of enriched tasks
        formatted_tasks = []
        assignees_set = set()
        employees_set = set()
        statuses_set = set()

        for t in tasks:
            proj_info = onboarding_by_project.get(t.project, {})
            p_obj = project_meta.get(t.project, {})

            emp_name = proj_info.get("employee_name") or ""
            if not emp_name and ": " in (t.subject or ""):
                parts = t.subject.split(": ")
                if len(parts) > 1:
                    emp_name = parts[-1].strip()

            if not emp_name and p_obj.get("project_name"):
                if ":" in p_obj["project_name"]:
                    emp_name = p_obj["project_name"].split(":")[-1].strip()

            is_overdue = bool(
                t.exp_end_date and str(t.exp_end_date) < str(today) and t.status not in ("Completed", "Cancelled")
            )

            # Assignees (active _assign + ToDo history including Closed + Boarding Activity + completed_by)
            combined_assignees = set()
            if t.get("_assign"):
                try:
                    loaded = json.loads(t._assign) if isinstance(t._assign, str) else t._assign
                    for u in (loaded or []):
                        if u:
                            combined_assignees.add(u)
                except Exception:
                    pass

            for u in todo_assignees_map.get(t.name, []):
                combined_assignees.add(u)

            for u in activity_assignees_map.get(t.name, []):
                combined_assignees.add(u)

            if t.completed_by:
                combined_assignees.add(t.completed_by)

            task_assignees = sorted(list(combined_assignees))

            for a in task_assignees:
                if a:
                    assignees_set.add(a)

            if emp_name:
                employees_set.add(emp_name)

            if t.status:
                statuses_set.add(t.status)

            # Friendly project display name
            display_project = p_obj.get("project_name") or t.project or (f"Employee Onboarding: {emp_name}" if emp_name else "Employee Onboarding")

            formatted_tasks.append({
                "name": t.name,
                "subject": t.subject or "",
                "project": t.project or "",
                "project_name": display_project,
                "status": t.status or "Open",
                "priority": t.priority or "Medium",
                "type": t.type or "Onboarding",
                "progress": float(t.progress or 0),
                "exp_end_date": str(t.exp_end_date) if t.exp_end_date else "",
                "exp_start_date": str(t.exp_start_date) if t.exp_start_date else "",
                "expected_time": float(t.expected_time or 0),
                "color": t.color or "#dbeafe",
                "issue": t.issue or "",
                "weight": float(t.task_weight or 0),
                "parent_task": t.parent_task or "",
                "description": t.description or "",
                "is_group": int(t.is_group or 0),
                "is_milestone": int(t.is_milestone or 0),
                "review_date": str(t.review_date) if t.review_date else "",
                "closing_date": str(t.closing_date) if t.closing_date else "",
                "completed_by": t.completed_by or "",
                "completed_on": str(t.completed_on) if t.completed_on else "",
                "is_template": int(t.is_template or 0),
                "start": int(t.start or 0),
                "duration": int(t.duration or 0),
                "act_start_date": str(t.act_start_date) if t.act_start_date else "",
                "act_end_date": str(t.act_end_date) if t.act_end_date else "",
                "actual_time": float(t.actual_time or 0),
                "total_costing_amount": float(t.total_costing_amount or 0),
                "total_billing_amount": float(t.total_billing_amount or 0),
                "depends_on": depends_on_map.get(t.name, []),
                "assignees": task_assignees,
                "is_overdue": is_overdue,
                "onboarding_id": proj_info.get("name") or "",
                "employee": proj_info.get("employee") or "",
                "employee_name": emp_name or "Candidate",
                "job_applicant": proj_info.get("job_applicant") or "",
                "department": t.department or proj_info.get("department") or "",
                "company": t.company or proj_info.get("company") or ""
            })

        # Pre-group tasks by project for easy tree rendering
        grouped_projects = {}
        for t in formatted_tasks:
            pid = t["project"] or "other"
            if pid not in grouped_projects:
                grouped_projects[pid] = {
                    "project": pid,
                    "project_name": t["project_name"],
                    "employee_name": t["employee_name"],
                    "onboarding_id": t["onboarding_id"],
                    "tasks": []
                }
            grouped_projects[pid]["tasks"].append(t)

        return {
            "tasks": formatted_tasks,
            "projects": list(grouped_projects.values()),
            "assignees": sorted(list(assignees_set)),
            "employees": sorted(list(employees_set)),
            "statuses": sorted(list(statuses_set)),
            "current_user": user,
            "today": today
        }
    except Exception as e:
        frappe.log_error("get_onboarding_tasks_data error", str(e))
        return {
            "tasks": [],
            "projects": [],
            "assignees": [],
            "employees": [],
            "statuses": ["Open", "Working", "Pending Review", "Completed", "Cancelled"],
            "current_user": frappe.session.user,
            "today": frappe.utils.today()
        }


@frappe.whitelist()
def save_onboarding_task(task_id, values):
    """Saves changes made to an onboarding Task record."""
    import json
    if not task_id:
        frappe.throw("Task ID is required")

    if isinstance(values, str):
        values = json.loads(values)

    doc = frappe.get_doc("Task", task_id)
    # Validate both generic write permission and document-level permission.
    frappe.has_permission("Task", ptype="write", throw=True)
    doc.check_permission("write")

    allowed_fields = [
        "subject", "status", "priority", "type", "progress",
        "color", "issue", "parent_task", "exp_start_date",
        "exp_end_date", "expected_time", "is_group", "is_milestone",
        "review_date", "closing_date", "company", "department",
        "completed_by", "completed_on", "is_template", "start",
        "duration", "description",
    ]
    for field in allowed_fields:
        if field in values:
            setattr(doc, field, values[field])

    if "weight" in values:
        doc.task_weight = values["weight"]

    if "depends_on" in values:
        depends = values["depends_on"]
        if isinstance(depends, str):
            depends = json.loads(depends)
        doc.set("depends_on", [])
        for row in depends or []:
            if not row.get("task"):
                continue
            doc.append("depends_on", {
                "task": row.get("task"),
                "subject": row.get("subject") or "",
                "project": row.get("project") or "",
            })

    if "status" in values and values["status"] == "Completed":
        if not doc.completed_by:
            doc.completed_by = frappe.session.user
        if not doc.completed_on:
            doc.completed_on = frappe.utils.today()
        if not doc.progress or doc.progress < 100:
            doc.progress = 100

    doc.save()
    
    return {
        "success": True,
        "name": doc.name,
        "subject": doc.subject,
        "status": doc.status,
        "priority": doc.priority,
        "progress": doc.progress,
        "completed_by": doc.completed_by or "",
        "completed_on": str(doc.completed_on) if doc.completed_on else "",
    }
