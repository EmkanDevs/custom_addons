import frappe
from collections import defaultdict


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters or {})
    return columns, data


def get_columns():
    return [
        {"label": "Material Request", "fieldname": "material_request", "fieldtype": "Link", "options": "Material Request", "width": 160},
        {"label": "MR Date", "fieldname": "mr_date", "fieldtype": "Date", "width": 100},
        {"label": "MR Item Code", "fieldname": "mr_item_code", "fieldtype": "Link", "options": "Item", "width": 120},
        {"label": "MR Item Name", "fieldname": "mr_item_name", "fieldtype": "Data", "width": 150},
        {"label": "MR Description", "fieldname": "mr_description", "fieldtype": "Data", "width": 200},
        {"label": "MR Item Group", "fieldname": "mr_item_group", "fieldtype": "Link", "options": "Item Group", "width": 120},
        {"label": "MR Qty", "fieldname": "mr_qty", "fieldtype": "Float", "width": 100},
        {"label": "MR Transferred Qty", "fieldname": "mr_transferred_qty", "fieldtype": "Float", "width": 120},
        {"label": "MR Qty To Transfer", "fieldname": "mr_qty_to_transfer", "fieldtype": "Float", "width": 130},

        {"label": "Stock Entry (From)", "fieldname": "stock_entry_from", "fieldtype": "Link", "options": "Stock Entry", "width": 160},
        {"label": "SE From Date", "fieldname": "se_from_date", "fieldtype": "Date", "width": 100},
        {"label": "SE Source Whse", "fieldname": "se_from_whse", "fieldtype": "Link", "options": "Warehouse", "width": 160},
        {"label": "SE Target Whse", "fieldname": "se_to_whse", "fieldtype": "Link", "options": "Warehouse", "width": 160},
        {"label": "SE Item Code", "fieldname": "se_item_code", "fieldtype": "Link", "options": "Item", "width": 120},
        {"label": "SE Item Name", "fieldname": "se_item_name", "fieldtype": "Data", "width": 150},
        {"label": "SE Qty", "fieldname": "se_qty", "fieldtype": "Float", "width": 100},
        {"label": "SE Rate", "fieldname": "se_rate", "fieldtype": "Currency", "width": 100},
        {"label": "SE Amount", "fieldname": "se_amount", "fieldtype": "Currency", "width": 120},
        {"label": "SE Project", "fieldname": "se_project", "fieldtype": "Link", "options": "Project", "width": 120},
        {"label": "SE Project Name", "fieldname": "se_project_name", "fieldtype": "Data", "width": 120},
        {"label": "SE Project Code", "fieldname": "se_project_code", "fieldtype": "Data", "width": 120},

        {"label": "Stock Entry (To)", "fieldname": "stock_entry_to", "fieldtype": "Link", "options": "Stock Entry", "width": 160},
        {"label": "SE To Date", "fieldname": "se_to_date", "fieldtype": "Date", "width": 100},
        {"label": "To Source Whse", "fieldname": "to_from_whse", "fieldtype": "Link", "options": "Warehouse", "width": 160},
        {"label": "To Target Whse", "fieldname": "to_to_whse", "fieldtype": "Link", "options": "Warehouse", "width": 160},
        {"label": "To Item Code", "fieldname": "to_item_code", "fieldtype": "Link", "options": "Item", "width": 120},
        {"label": "To Item Name", "fieldname": "to_item_name", "fieldtype": "Data", "width": 150},
        {"label": "To Qty", "fieldname": "to_qty", "fieldtype": "Float", "width": 100},
        {"label": "To Rate", "fieldname": "to_rate", "fieldtype": "Currency", "width": 100},
        {"label": "To Amount", "fieldname": "to_amount", "fieldtype": "Currency", "width": 120},
        {"label": "To Project", "fieldname": "to_project", "fieldtype": "Link", "options": "Project", "width": 120},
        {"label": "To Project Name", "fieldname": "to_project_name", "fieldtype": "Data", "width": 120},
        {"label": "To Project Code", "fieldname": "to_project_code", "fieldtype": "Data", "width": 120},
    ]


def get_data(filters):
    data = []

    mr_filters = {"material_request_type": "Material Transfer", "docstatus": 1}
    if filters.get("material_request"):
        mr_filters["name"] = filters["material_request"]
    if filters.get("company"):
        mr_filters["company"] = filters["company"]
    if filters.get("from_date") and filters.get("to_date"):
        mr_filters["transaction_date"] = ["between", [filters["from_date"], filters["to_date"]]]
    elif filters.get("from_date"):
        mr_filters["transaction_date"] = [">=", filters["from_date"]]
    elif filters.get("to_date"):
        mr_filters["transaction_date"] = ["<=", filters["to_date"]]

    mrs = frappe.get_all(
        "Material Request",
        filters=mr_filters,
        fields=["name", "transaction_date as posting_date"],
    )

    if not mrs:
        return data

    mr_names = [mr.name for mr in mrs]

    maps = get_transfer_maps(mr_names, filters)

    for mr in mrs:
        mr_items = maps.mr_items.get(mr.name, [])
        se_names = maps.se_names_by_mr.get(mr.name, [])

        for item in mr_items:
            row_base = {
                "material_request": mr.name,
                "mr_date": mr.posting_date,
                "mr_item_code": item.item_code,
                "mr_item_name": item.item_name,
                "mr_description": item.description,
                "mr_item_group": item.item_group,
                "mr_qty": item.qty,
                "mr_transferred_qty": item.received_qty,
                "mr_qty_to_transfer": (item.qty or 0) - (item.received_qty or 0),
            }

            if not se_names:
                data.append(row_base)
                continue

            for se_name in se_names:
                se_header = maps.se_headers.get(se_name)
                if not se_header:
                    continue

                se_items = maps.se_details.get((se_name, item.item_code), [])

                for se_item in se_items:
                    project_name, project_code = None, None
                    if se_item.project:
                        project_info = maps.projects.get(se_item.project)
                        if project_info:
                            project_name = project_info.project_name
                            project_code = project_info.custom_project_code

                    row = row_base.copy()
                    row.update({
                        "stock_entry_from": se_header.name,
                        "se_from_date": se_header.posting_date,
                        "se_from_whse": se_header.from_warehouse,
                        "se_to_whse": se_header.to_warehouse,
                        "se_item_code": se_item.item_code,
                        "se_item_name": se_item.item_name,
                        "se_qty": se_item.qty,
                        "se_rate": se_item.basic_rate,
                        "se_amount": se_item.amount,
                        "se_project": se_item.project,
                        "se_project_name": project_name,
                        "se_project_code": project_code,
                    })

                    se_to_names = maps.se_to_names_by_se.get(se_name, [])

                    if not se_to_names:
                        data.append(row)
                        continue

                    for se_to_name in se_to_names:
                        se_to_header = maps.se_headers.get(se_to_name)
                        if not se_to_header:
                            continue

                        se_to_items = maps.se_details.get((se_to_name, se_item.item_code), [])

                        for to_item in se_to_items:
                            to_project_name, to_project_code = None, None
                            if to_item.project:
                                to_project_info = maps.projects.get(to_item.project)
                                if to_project_info:
                                    to_project_name = to_project_info.project_name
                                    to_project_code = to_project_info.custom_project_code

                            row_to = row.copy()
                            row_to.update({
                                "stock_entry_to": se_to_header.name,
                                "se_to_date": se_to_header.posting_date,
                                "to_from_whse": se_to_header.from_warehouse,
                                "to_to_whse": se_to_header.to_warehouse,
                                "to_item_code": to_item.item_code,
                                "to_item_name": to_item.item_name,
                                "to_qty": to_item.qty,
                                "to_rate": to_item.basic_rate,
                                "to_amount": to_item.amount,
                                "to_project": to_item.project,
                                "to_project_name": to_project_name,
                                "to_project_code": to_project_code,
                            })
                            data.append(row_to)

    return data


def get_transfer_maps(mr_names, filters):
    """
    Batch-fetch every level of data the nested loops used to query
    one row at a time (MR items, linked Stock Entries, SE line items,
    outgoing/"to" Stock Entries, and Projects).

    Returns a frappe._dict with:
        mr_items          -> {mr_name: [item, ...]}
        se_names_by_mr     -> {mr_name: [se_name, ...]}
        se_headers         -> {se_name: header}   (only docstatus=1 / company-matching)
        se_details         -> {(parent, item_code): [detail, ...]}
        se_to_names_by_se  -> {se_name: [se_to_name, ...]}
        projects           -> {project: project_info}
    """
    company = filters.get("company")

    # ------------------------------------------------------------------
    # MR Items for all MRs in one query
    # ------------------------------------------------------------------
    mr_items = defaultdict(list)
    mri_rows = frappe.get_all(
        "Material Request Item",
        filters={"parent": ("in", mr_names)},
        fields=["parent", "item_code", "item_name", "description", "item_group", "qty", "received_qty"],
    )
    for row in mri_rows:
        mr_items[row.parent].append(row)

    # ------------------------------------------------------------------
    # Stock Entries linked to these MRs (any item), in one query
    # ------------------------------------------------------------------
    se_names_by_mr = defaultdict(set)
    all_se_names = set()
    sed_link_rows = frappe.get_all(
        "Stock Entry Detail",
        filters={"material_request": ("in", mr_names)},
        fields=["parent", "material_request"],
    )
    for row in sed_link_rows:
        se_names_by_mr[row.material_request].add(row.parent)
        all_se_names.add(row.parent)

    se_names_by_mr = {mr: list(names) for mr, names in se_names_by_mr.items()}

    se_headers = {}
    se_to_names_by_se = defaultdict(list)
    se_details = defaultdict(list)
    all_se_to_names = set()

    if all_se_names:
        se_filters = {"name": ("in", list(all_se_names)), "docstatus": 1}
        if company:
            se_filters["company"] = company

        se_header_rows = frappe.get_all(
            "Stock Entry",
            filters=se_filters,
            fields=["name", "posting_date", "from_warehouse", "to_warehouse"],
        )
        for row in se_header_rows:
            se_headers[row.name] = row

        # SE line items for these SEs, in one query (kept ungrouped by item_code
        # here, grouped in python since one (parent,item_code) can repeat)
        se_detail_rows = frappe.get_all(
            "Stock Entry Detail",
            filters={"parent": ("in", list(all_se_names))},
            fields=["parent", "item_code", "item_name", "qty", "basic_rate", "amount", "project"],
        )
        for row in se_detail_rows:
            se_details[(row.parent, row.item_code)].append(row)

        # "To" Stock Entries (outgoing_stock_entry) - only need this for SEs
        # that actually passed the header filter above
        valid_se_names = list(se_headers.keys())
        if valid_se_names:
            se_to_link_rows = frappe.get_all(
                "Stock Entry",
                filters={"outgoing_stock_entry": ("in", valid_se_names)},
                fields=["name", "outgoing_stock_entry"],
            )
            for row in se_to_link_rows:
                se_to_names_by_se[row.outgoing_stock_entry].append(row.name)
                all_se_to_names.add(row.name)

    if all_se_to_names:
        se_to_filters = {"name": ("in", list(all_se_to_names)), "docstatus": 1}
        if company:
            se_to_filters["company"] = company

        se_to_header_rows = frappe.get_all(
            "Stock Entry",
            filters=se_to_filters,
            fields=["name", "posting_date", "from_warehouse", "to_warehouse"],
        )
        for row in se_to_header_rows:
            se_headers[row.name] = row

        se_to_detail_rows = frappe.get_all(
            "Stock Entry Detail",
            filters={"parent": ("in", list(all_se_to_names))},
            fields=["parent", "item_code", "item_name", "qty", "basic_rate", "amount", "project"],
        )
        for row in se_to_detail_rows:
            se_details[(row.parent, row.item_code)].append(row)

    # ------------------------------------------------------------------
    # Projects referenced anywhere above, in one query
    # ------------------------------------------------------------------
    project_names = set()
    for rows in se_details.values():
        for row in rows:
            if row.project:
                project_names.add(row.project)

    projects = {}
    if project_names:
        project_rows = frappe.get_all(
            "Project",
            filters={"name": ("in", list(project_names))},
            fields=["name", "project_name", "custom_project_code"],
        )
        projects = {row.name: row for row in project_rows}

    return frappe._dict(
        {
            "mr_items": mr_items,
            "se_names_by_mr": se_names_by_mr,
            "se_headers": se_headers,
            "se_details": se_details,
            "se_to_names_by_se": se_to_names_by_se,
            "projects": projects,
        }
    )