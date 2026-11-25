import frappe


@frappe.whitelist()
def get_dashboard_data(filters=None):
    frappe.has_permission("Purchase Order", "read", throw=True)
    filters = frappe.parse_json(filters) if filters else {}

    return {
        "kpis": get_kpis(filters),
        "supplier_chart": get_supplier_chart(filters),
        "project_chart": get_project_chart(filters),
        "approval_pipeline": get_approval_pipeline(filters),
        "team_summary": get_team_summary(filters),
        "purchase_orders": get_purchase_orders(filters),
    }


def get_kpis(filters):
    conditions = get_conditions(filters)

    result = frappe.db.sql(
        f"""
        SELECT
            COUNT(DISTINCT po.name) as po_count,
            IFNULL(SUM(po.grand_total), 0) as total_po,
            COUNT(DISTINCT po.supplier) as supplier_count,
            IFNULL(AVG(po.grand_total), 0) as avg_po
        FROM `tabPurchase Order` po
        WHERE po.docstatus = 1
            {conditions}
        """,
        filters,
        as_dict=True,
    )[0]

    pending = get_pending_approval_summary(filters)

    return {
        "total_po": result.total_po,
        "po_count": result.po_count,
        "new_suppliers": result.supplier_count,
        "average_po": result.avg_po,
        "pending_po_count": pending.count,
        "pending_po_value": pending.value,
    }


def get_state_case_expr(workflow_field):
    """SQL CASE expression that resolves each PO's display workflow state
    (its actual workflow_state label when set, else a docstatus-derived
    Approved/Draft). Shared by the pipeline chart, the pending KPI, and the
    detail log so all three agree on the same state per PO."""
    if workflow_field:
        return f"""
            CASE
                WHEN po.docstatus = 1 AND (po.{workflow_field} IS NULL OR po.{workflow_field} = '')
                    THEN 'Approved'
                WHEN po.{workflow_field} IS NOT NULL AND po.{workflow_field} != ''
                    THEN po.{workflow_field}
                ELSE 'Draft'
            END
        """
    return """
        CASE
            WHEN po.docstatus = 1 THEN 'Approved'
            ELSE 'Draft'
        END
    """


def get_pending_approval_summary(filters):
    """POs that are not yet fully approved (still awaiting sign-off).
    Matches by keyword rather than an exact string, since real workflow
    states are often suffixed with a role, e.g.
    'Pending Approval (Procurements Manager)'."""
    conditions = get_conditions(filters)
    state_expr = get_state_case_expr(get_workflow_field())

    data = frappe.db.sql(
        f"""
        SELECT
            COUNT(DISTINCT po.name) as cnt,
            IFNULL(SUM(po.grand_total), 0) as total
        FROM `tabPurchase Order` po
        WHERE po.docstatus < 2
            {conditions}
            AND (
                LOWER({state_expr}) LIKE '%%pending%%'
                OR LOWER({state_expr}) LIKE '%%review%%'
                OR LOWER({state_expr}) LIKE '%%awaiting%%'
            )
        """,
        filters,
        as_dict=True,
    )[0]

    return frappe._dict({"count": data.cnt, "value": data.total})


def get_approval_pipeline(filters):
    """Breakdown of every non-cancelled PO by workflow stage, for the
    PO Approval & Workflow Pipeline pie chart."""
    conditions = get_conditions(filters)
    state_expr = get_state_case_expr(get_workflow_field())

    rows = frappe.db.sql(
        f"""
        SELECT {state_expr} as state, COUNT(DISTINCT po.name) as cnt
        FROM `tabPurchase Order` po
        WHERE po.docstatus < 2
            {conditions}
        GROUP BY state
        ORDER BY cnt DESC
        """,
        filters,
        as_dict=True,
    )

    fallback_palette = ["#7cd6fd", "#ffa00a", "#28a745", "#dc3545"]

    labels, values, colors = [], [], []
    for i, r in enumerate(rows):
        labels.append(r.state)
        values.append(r.cnt)
        colors.append(get_pipeline_color(r.state) or fallback_palette[i % len(fallback_palette)])

    return {"labels": labels, "values": values, "colors": colors}


def get_pipeline_color(state):
    """Bucket a (possibly custom, e.g. 'Pending Approval (Procurements Manager)')
    workflow state into one of the wireframe's exact pipeline colors, so
    custom workflow labels still land on a sensible, consistent color."""
    label = (state or "").lower()

    if "cancel" in label:
        return "#cbd5e1"
    if "pending" in label or "review" in label or "awaiting" in label:
        return "#d94e34"
    if "draft" in label:
        return "#94a3b8"
    if "approved" in label or "complete" in label:
        return "#0b4c80"
    return None


def get_workflow_field():
    """Return the fieldname used to track PO approval state, if the site
    has one (e.g. a custom 'workflow_state' field from a Workflow)."""
    if not hasattr(frappe.local, "_spd_workflow_field_cache"):
        frappe.local._spd_workflow_field_cache = {}

    cache = frappe.local._spd_workflow_field_cache
    if "Purchase Order" not in cache:
        cache["Purchase Order"] = (
            "workflow_state" if frappe.db.has_column("Purchase Order", "workflow_state") else None
        )

    return cache["Purchase Order"]


def get_supplier_chart(filters):
    """One row per supplier — total PO value, ranked highest first, matching
    the wireframe's aggregated Purchase Analysis by Supplier chart (rather
    than one bar per PO)."""
    conditions = get_conditions(filters)

    data = frappe.db.sql(
        f"""
        SELECT
            po.supplier as supplier,
            IFNULL(po.supplier_name, po.supplier) as supplier_name,
            SUM(po.grand_total) as total
        FROM `tabPurchase Order` po
        WHERE po.docstatus = 1
            {conditions}
        GROUP BY po.supplier, po.supplier_name
        ORDER BY total DESC
        """,
        filters,
        as_dict=True,
    )

    return {
        "labels": [d.supplier_name for d in data],
        "values": [d.total for d in data],
        "table": [
            {"supplier_name": d.supplier_name, "supplier_code": d.supplier, "total": d.total}
            for d in data
        ],
    }


def get_project_chart(filters):
    """One row per project — total PO value, ranked highest first, matching
    the wireframe's aggregated Purchase Analysis by Project chart (rather
    than one bar per PO)."""
    conditions = get_conditions(filters)

    data = frappe.db.sql(
        f"""
        SELECT
            COALESCE(NULLIF(po.project, ''), NULLIF(poi.project, ''), '(No Project)') as project_id,
            COALESCE(NULLIF(prj.project_name, ''), NULLIF(po.project, ''), NULLIF(poi.project, ''), '(No Project)') as project_name,
            SUM(po.grand_total) as total
        FROM `tabPurchase Order` po
        LEFT JOIN `tabPurchase Order Item` poi
            ON poi.parent = po.name AND poi.idx = 1
        LEFT JOIN `tabProject` prj
            ON prj.name = COALESCE(NULLIF(po.project, ''), poi.project)
        WHERE po.docstatus = 1
            {conditions}
        GROUP BY project_id, project_name
        ORDER BY total DESC
        """,
        filters,
        as_dict=True,
    )

    return {
        "labels": [d.project_name for d in data],
        "values": [d.total for d in data],
        "table": [
            {"project_name": d.project_name, "total": d.total}
            for d in data
        ],
    }


def get_team_summary(filters):
    conditions = get_conditions(filters)

    return frappe.db.sql(
        f"""
        SELECT
            IFNULL(u.full_name, po.owner) as team_member,
            COUNT(DISTINCT po.name) as po_count
        FROM `tabPurchase Order` po
        LEFT JOIN `tabUser` u ON u.name = po.owner
        WHERE po.docstatus = 1
            {conditions}
        GROUP BY po.owner, u.full_name
        ORDER BY po_count DESC
        """,
        filters,
        as_dict=True,
    )


def get_purchase_orders(filters):
    """Purchase Orders log — includes Draft / Pending Approval / Approved
    (i.e. everything except cancelled), with the linked Material Request
    (MR No. & MR Date) and a workflow-state pill."""
    conditions = get_conditions(filters)
    status_expr = get_state_case_expr(get_workflow_field())

    return frappe.db.sql(
        f"""
        SELECT
            po.name as po_number,
            po.transaction_date as date,
            first_mr.material_request as mr_no,
            mr.transaction_date as mr_date,
            po.supplier,
            po.supplier_name,
            po.grand_total,
            po.owner,
            IFNULL(u.full_name, po.owner) as created_by,
            proj.project as project,
            IFNULL(prj.project_name, proj.project) as project_name,
            {status_expr} as workflow_status
        FROM `tabPurchase Order` po
        LEFT JOIN (
            SELECT poi.parent, MIN(poi.project) as project
            FROM `tabPurchase Order Item` poi
            GROUP BY poi.parent
        ) proj ON proj.parent = po.name
        LEFT JOIN `tabProject` prj
            ON prj.name = proj.project
        LEFT JOIN (
            -- earliest non-empty Material Request linked on any line item
            SELECT poi.parent, MIN(poi.material_request) as material_request
            FROM `tabPurchase Order Item` poi
            WHERE poi.material_request IS NOT NULL AND poi.material_request != ''
            GROUP BY poi.parent
        ) first_mr ON first_mr.parent = po.name
        LEFT JOIN `tabMaterial Request` mr
            ON mr.name = first_mr.material_request
        LEFT JOIN `tabUser` u
            ON u.name = po.owner
        WHERE po.docstatus < 2
            {conditions}
        GROUP BY po.name
        ORDER BY po.transaction_date DESC
        LIMIT 100
        """,
        filters,
        as_dict=True,
    )


def get_conditions(filters):
    conditions = ""

    if filters.get("company"):
        conditions += " AND po.company = %(company)s"

    if filters.get("year"):
        conditions += " AND YEAR(po.transaction_date) = %(year)s"

    if filters.get("month"):
        conditions += " AND MONTH(po.transaction_date) = %(month)s"

    if filters.get("from_date"):
        conditions += " AND po.transaction_date >= %(from_date)s"

    if filters.get("to_date"):
        conditions += " AND po.transaction_date <= %(to_date)s"

    if filters.get("supplier"):
        conditions += " AND po.supplier = %(supplier)s"

    if filters.get("project"):
        conditions += """
            AND EXISTS (
                SELECT 1
                FROM `tabPurchase Order Item` poi
                WHERE poi.parent = po.name
                  AND poi.project = %(project)s
            )
        """

    if filters.get("owner"):
        conditions += " AND po.owner = %(owner)s"

    return conditions