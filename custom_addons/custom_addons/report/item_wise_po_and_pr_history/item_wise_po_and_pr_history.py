import frappe
from frappe.utils import flt
from frappe.query_builder import DocType
from frappe.utils.nestedset import get_descendants_of

def execute(filters=None):
    filters = frappe._dict(filters or {})
    if filters.get("from_date") and filters.get("to_date"):
        if filters.from_date > filters.to_date:
            frappe.throw("From Date cannot be greater than To Date")

    columns = get_columns()
    data = get_data(filters)
    chart_data = get_chart_data(data)
    return columns, data, None, chart_data


# -------------------------------------------------------------------
# Columns
# -------------------------------------------------------------------
def get_columns():
    return [
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 140},
        {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 120},
        {"label": "Description", "fieldname": "description", "fieldtype": "Data", "width": 140},
        {"label": "Quantity", "fieldname": "quantity", "fieldtype": "Float", "width": 120},
        {"label": "UOM", "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 90},
        {"label": "Rate", "fieldname": "rate", "fieldtype": "Currency", "width": 120},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": "Latest Rate", "fieldname": "latest_rate", "fieldtype": "Currency", "width": 120},
        {"label": "PR / PO", "fieldname": "transaction_name", "fieldtype": "Dynamic Link", "options": "transaction_type", "width": 140},
        {"label": "Transaction Type", "fieldname": "transaction_type", "fieldtype": "Data", "width": 130},
        {"label": "Transaction Date", "fieldname": "transaction_date", "fieldtype": "Date", "width": 110},
        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 100},
        {"label": "Supplier Name", "fieldname": "supplier_name", "fieldtype": "Data", "width": 140},
        {"label": "Supplier Group", "fieldname": "supplier_group", "fieldtype": "Link", "options": "Supplier Group", "width": 120},
        {"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 100},
        {"label": "Project Name", "fieldname": "project_name", "fieldtype": "Data", "width": 140},
        {"label": "Is Petty Cash", "fieldname": "is_petty_cash", "fieldtype": "Check", "width": 120},
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Data", "width": 140},
        {"label": "Received Quantity", "fieldname": "received_qty", "fieldtype": "Float", "width": 150},
        {"label": "Billed Amount", "fieldname": "billed_amt", "fieldtype": "Currency", "width": 120},
        {"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 100},
        {"label": "Currency", "fieldname": "currency", "fieldtype": "Link", "options": "Currency", "hidden": 1},
    ]

def get_project_details():
    projects = frappe.get_all("Project", fields=["name", "project_name"])
    return {p.name: p.project_name for p in projects}


# -------------------------------------------------------------------
# Data fetcher
# -------------------------------------------------------------------
def get_data(filters):
    company_list = get_descendants_of("Company", filters.get("company")) if filters.get("company") else []
    if filters.get("company"):
        company_list.append(filters.get("company"))

    supplier_details = get_supplier_details()
    item_details = get_item_details()
    latest_rate_map = get_latest_item_rates(company_list)
    project_details = get_project_details()

    records = []

    transaction_type = filters.get("transaction_type")

    # ----------------------------------------------------------------
    # Purchase Orders
    # ----------------------------------------------------------------
    if transaction_type in (None, "", "Purchase Order"):
        po_records = get_purchase_order_details(company_list, filters)

        for r in po_records:
            if filters.get("project") and r.get("project") != filters.get("project"):
                continue

            supplier_record = supplier_details.get(r.supplier)
            item_record = item_details.get(r.item_code)

            row = map_record_to_row(
                r, supplier_record, item_record, latest_rate_map,
                transaction_type="Purchase Order",
                project_details=project_details
            )
            records.append(row)

    # ----------------------------------------------------------------
    # Purchase Receipts
    # ----------------------------------------------------------------
    if transaction_type in (None, "", "Purchase Receipt"):
        pr_records = get_purchase_receipt_details(company_list, filters)

        for r in pr_records:
            if filters.get("project") and r.get("project") != filters.get("project"):
                continue

            supplier_record = supplier_details.get(r.supplier)
            item_record = item_details.get(r.item_code)

            row = map_record_to_row(
                r, supplier_record, item_record, latest_rate_map,
                transaction_type="Purchase Receipt",
                project_details=project_details
            )
            records.append(row)

    # Sort combined records by latest creation
    records.sort(key=lambda r: r.get("creation", r.get("transaction_date")), reverse=True)

    return records


# -------------------------------------------------------------------
# Map PO / PR rows into report rows + petty cash logic
# -------------------------------------------------------------------
def map_record_to_row(record, supplier_record, item_record, latest_rate_map, transaction_type, project_details):

    # EMPLOYEE LOGIC
    employee = None
    if transaction_type == "Purchase Order":
        if record.get("custom_petty_cash"):
            employee = record.get("employee")

    elif transaction_type == "Purchase Receipt":
        if record.get("is_petty_cash"):
            employee = record.get("custom_petty_cash_holder")

    # IS PETTY CASH LOGIC
    is_petty_cash = 0
    if transaction_type == "Purchase Order":
        is_petty_cash = 1 if record.get("custom_petty_cash") else 0
    elif transaction_type == "Purchase Receipt":
        is_petty_cash = 1 if record.get("is_petty_cash") else 0

    return {
        "item_code": record.get("item_code"),
        "item_name": item_record.get("item_name") if item_record else None,
        "item_group": item_record.get("item_group") if item_record else None,
        "description": record.get("description"),
        "quantity": record.get("qty"),
        "uom": record.get("uom"),
        "rate": record.get("base_rate"),
        "amount": record.get("base_amount"),
        "latest_rate": latest_rate_map.get(record.get("item_code")),
        "transaction_name": record.get("name"),
        "transaction_type": transaction_type,
        "transaction_date": record.get("transaction_date"),
        "supplier": record.get("supplier"),
        "supplier_name": supplier_record.get("supplier_name") if supplier_record else None,
        "supplier_group": supplier_record.get("supplier_group") if supplier_record else None,
        "project": record.get("project"),
        "project_name": project_details.get(record.get("project")),
        "employee": employee,

        # NEW FIELD
        "is_petty_cash": is_petty_cash,

        "received_qty": flt(record.get("received_qty")),
        "billed_amt": flt(record.get("billed_amt")),
        "company": record.get("company"),
        "currency": frappe.get_cached_value("Company", record.get("company"), "default_currency")
    }

# -------------------------------------------------------------------
# Supplier / Item Helpers
# -------------------------------------------------------------------
def get_supplier_details():
    details = frappe.get_all("Supplier", fields=["name", "supplier_name", "supplier_group"])
    return {d.name: frappe._dict({"supplier_name": d.supplier_name, "supplier_group": d.supplier_group}) for d in details}

def get_item_details():
    details = frappe.db.get_all("Item", fields=["name", "item_name", "item_group"])
    return {d.name: frappe._dict({"item_name": d.item_name, "item_group": d.item_group}) for d in details}


# -------------------------------------------------------------------
# Purchase Order Query
# -------------------------------------------------------------------
def get_purchase_order_details(company_list, filters):
    PO = DocType("Purchase Order")
    PO_Item = DocType("Purchase Order Item")

    query = (
        frappe.qb.from_(PO)
        .inner_join(PO_Item)
        .on(PO_Item.parent == PO.name)
        .select(
            PO.name,
            PO.supplier,
            PO.transaction_date,
            PO.project,
            PO.company,
            PO.custom_petty_cash,
            PO.employee,
            PO_Item.item_code,
            PO_Item.description,
            PO_Item.qty,
            PO_Item.uom,
            PO_Item.base_rate,
            PO_Item.base_amount,
            PO_Item.received_qty,
            (PO_Item.billed_amt * PO.conversion_rate).as_("billed_amt"),
        )
        .where(PO.docstatus == 1)
        .where(PO.company.isin(tuple(company_list)))
    )

    if filters.get("from_date"):
        query = query.where(PO.transaction_date >= filters.get("from_date"))
    if filters.get("to_date"):
        query = query.where(PO.transaction_date <= filters.get("to_date"))
    if filters.get("supplier"):
        query = query.where(PO.supplier == filters.get("supplier"))
    if filters.get("item_code"):
        query = query.where(PO_Item.item_code == filters.get("item_code"))

    # PETTY CASH FILTER
    if filters.get("is_petty_cash"):
        query = query.where(PO.custom_petty_cash == 1)

    query = query.orderby(PO.creation, descending=True)

    return query.run(as_dict=1)


# -------------------------------------------------------------------
# Purchase Receipt Query
# -------------------------------------------------------------------
def get_purchase_receipt_details(company_list, filters):
    PR = DocType("Purchase Receipt")
    PR_Item = DocType("Purchase Receipt Item")

    query = (
        frappe.qb.from_(PR)
        .inner_join(PR_Item)
        .on(PR_Item.parent == PR.name)
        .select(
            PR.name,
            PR.supplier,
            PR.posting_date.as_("transaction_date"),
            PR.project,
            PR.company,
            PR.is_petty_cash,
            PR.custom_petty_cash_holder,
            PR_Item.item_code,
            PR_Item.description,
            PR_Item.qty,
            PR_Item.uom,
            PR_Item.base_rate,
            PR_Item.base_amount,
            PR_Item.qty.as_("received_qty"),
            PR_Item.base_amount.as_("billed_amt"),
        )
        .where(PR.docstatus == 1)
        .where(PR.company.isin(tuple(company_list)))
    )

    if filters.get("from_date"):
        query = query.where(PR.posting_date >= filters.get("from_date"))
    if filters.get("to_date"):
        query = query.where(PR.posting_date <= filters.get("to_date"))
    if filters.get("supplier"):
        query = query.where(PR.supplier == filters.get("supplier"))
    if filters.get("item_code"):
        query = query.where(PR_Item.item_code == filters.get("item_code"))

    # PETTY CASH FILTER
    if filters.get("is_petty_cash"):
        query = query.where(PR.is_petty_cash == 1)

    query = query.orderby(PR.creation, descending=True)

    records = query.run(as_dict=1)
    for r in records:
        r["received_qty"] = flt(r.get("received_qty"))
        r["billed_amt"] = flt(r.get("billed_amt"))

    return records


# -------------------------------------------------------------------
# Latest Price Helper
# -------------------------------------------------------------------
def get_latest_item_rates(company_list):
    result = frappe.db.sql(
        """
        SELECT poi.item_code, poi.rate
        FROM `tabPurchase Order Item` poi
        INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
        WHERE po.docstatus = 1 AND po.company IN %(companies)s
        AND poi.item_code IS NOT NULL
        AND po.transaction_date = (
            SELECT MAX(po2.transaction_date)
            FROM `tabPurchase Order` po2
            INNER JOIN `tabPurchase Order Item` poi2 ON poi2.parent = po2.name
            WHERE po2.docstatus = 1
            AND poi2.item_code = poi.item_code
            AND po2.company IN %(companies)s
        )
        """,
        {"companies": tuple(company_list)},
        as_dict=1,
    )
    return {r.item_code: flt(r.rate) for r in result}


# -------------------------------------------------------------------
# Chart Data
# -------------------------------------------------------------------
def get_chart_data(data):
    item_wise_purchase_map = {}
    labels, datapoints = [], []

    for row in data:
        item_key = row.get("item_code")
        item_wise_purchase_map[item_key] = flt(item_wise_purchase_map.get(item_key, 0)) + flt(row.get("amount"))

    item_wise_purchase_map = dict(sorted(item_wise_purchase_map.items(), key=lambda i: i[1], reverse=True))

    for key in item_wise_purchase_map:
        labels.append(key)
        datapoints.append(item_wise_purchase_map[key])

    return {
        "data": {
            "labels": labels[:30],
            "datasets": [{"name": "Total Purchase Amount", "values": datapoints[:30]}],
        },
        "type": "bar",
        "fieldtype": "Currency",
    }
