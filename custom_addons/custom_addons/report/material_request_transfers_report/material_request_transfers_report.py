import frappe

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

    mr_filters = {"material_request_type": "Material Transfer"}
    if filters.get("material_request"):
        mr_filters["name"] = filters["material_request"]
    if filters.get("from_date") and filters.get("to_date"):
        mr_filters["transaction_date"] = ["between", [filters["from_date"], filters["to_date"]]]
    elif filters.get("from_date"):
        mr_filters["transaction_date"] = [">=", filters["from_date"]]
    elif filters.get("to_date"):
        mr_filters["transaction_date"] = ["<=", filters["to_date"]]

    mrs = frappe.db.get_values(
        "Material Request",
        mr_filters,
        ["name", "transaction_date as posting_date"],
        as_dict=True
    )

    for mr in mrs:
        mr_items = frappe.db.get_values(
            "Material Request Item",
            {"parent": mr.name},
            ["item_code", "item_name", "description", "item_group", "qty", "received_qty"],
            as_dict=True
        )

        se_names = frappe.db.get_values(
            "Stock Entry Detail",
            filters={"material_request": mr.name},
            fieldname="parent",
            as_dict=False
        )
        se_names = list(set(x[0] for x in se_names)) if se_names else []

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

            if se_names:
                for se_name in se_names:
                    se_header = frappe.db.get_value(
                        "Stock Entry",
                        se_name,
                        ["posting_date", "from_warehouse", "to_warehouse"],
                        as_dict=True
                    )
                    se_header.name = se_name

                    se_items = frappe.db.get_values(
                        "Stock Entry Detail",
                        {"parent": se_name, "item_code": item.item_code},
                        ["item_code", "item_name", "qty", "basic_rate", "amount", "project"],
                        as_dict=True
                    )

                    for se_item in se_items:
                        row = row_base.copy()
                        project_name, project_code = None, None
                        if se_item.project:
                            project_info = frappe.db.get_value(
                                "Project", se_item.project,
                                ["project_name", "custom_project_code"],
                                as_dict=True
                            )
                            if project_info:
                                project_name = project_info.project_name
                                project_code = project_info.custom_project_code

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

                        se_to_names = frappe.db.get_values(
                            "Stock Entry",
                            {"outgoing_stock_entry": se_header.name},
                            ["name"],
                            as_dict=False
                        )
                        se_to_names = [x[0] for x in se_to_names] if se_to_names else []

                        if se_to_names:
                            for se_to_name in se_to_names:
                                se_to_header = frappe.db.get_value(
                                    "Stock Entry",
                                    se_to_name,
                                    ["posting_date", "from_warehouse", "to_warehouse"],
                                    as_dict=True
                                )
                                se_to_header.name = se_to_name

                                se_to_items = frappe.db.get_values(
                                    "Stock Entry Detail",
                                    {"parent": se_to_name, "item_code": se_item.item_code},
                                    ["item_code", "item_name", "qty", "basic_rate", "amount", "project"],
                                    as_dict=True
                                )

                                for to_item in se_to_items:
                                    to_project_name, to_project_code = None, None
                                    if to_item.project:
                                        to_project_info = frappe.db.get_value(
                                            "Project", to_item.project,
                                            ["project_name", "custom_project_code"],
                                            as_dict=True
                                        )
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
                        else:
                            data.append(row)
            else:
                data.append(row_base)

    return data
