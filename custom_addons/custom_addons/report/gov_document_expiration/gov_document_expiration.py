# # Copyright (c) 2026, Administrator and contributors
# # For license information, please see license.txt

# import frappe


# def execute(filters=None):
#     columns = get_columns()
#     data = get_data(filters)
#     return columns, data


# def get_columns():
#     return [
#         {
#             "label": "Document Name",
#             "fieldname": "name",
#             "fieldtype": "Link",
#             "options": "Gov Document Expiration",
#             "width": 180
#         },
#         {
#             "label": "Gov Document Type",
#             "fieldname": "gov_document_type",
#             "fieldtype": "Data",
#             "width": 200
#         },
#         {
#             "label": "Gov Document Type AR",
#             "fieldname": "gov_document_type_ar",
#             "fieldtype": "Data",
#             "width": 200
#         },
#         {
#             "label": "Issue On",
#             "fieldname": "issue_on",
#             "fieldtype": "Date",
#             "width": 120
#         },
#         {
#             "label": "Expire On",
#             "fieldname": "expire_on",
#             "fieldtype": "Date",
#             "width": 120
#         },
#         {
#             "label": "Expire in Days",
#             "fieldname": "expire_in_days",
#             "fieldtype": "Int",
#             "width": 130
#         },
#         {
#             "label": "Renewal Status",
#             "fieldname": "renewal_status",
#             "fieldtype": "Data",
#             "width": 150
#         },
#         {
#             "label": "Customer",
#             "fieldname": "customer",
#             "fieldtype": "Link",
#             "options": "Customer",
#             "width": 150
#         },
#         {
#             "label": "Supplier",
#             "fieldname": "supplier",
#             "fieldtype": "Link",
#             "options": "Supplier",
#             "width": 120
#         },
#     ]


# def get_data(filters):
#     conditions = get_conditions(filters)

#     data = frappe.db.sql("""
#         SELECT
#             name,
#             gov_document_type,
#             gov_document_type_ar,
#             issue_on,
#             expire_on,
#             DATEDIFF(expire_on, CURDATE()) AS expire_in_days,
#             renewal_status,
#             customer,
#             supplier
#         FROM
#             `tabGov Document Expiration`
#         WHERE
#             docstatus < 2
#             {conditions}
#         ORDER BY
#             expire_on ASC
#     """.format(conditions=conditions), filters, as_dict=1)

#     return data


# def get_conditions(filters):
#     conditions = ""

#     if filters.get("customer"):
#         conditions += " AND customer = %(customer)s"
    
#     if filters.get("supplier"):
#         conditions += " AND supplier = %(supplier)s"

#     if filters.get("show_expired"):
#         conditions += " AND expire_on < CURDATE()"

#     elif filters.get("days_to_expire"):
#         conditions += " AND expire_on BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %(days_to_expire)s DAY)"

#     return conditions



import frappe


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": "Document Name",
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Gov Document Expiration",
            "width": 180
        },
        {
            "label": "Gov Document Type",
            "fieldname": "gov_document_type",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Gov Document Type AR",
            "fieldname": "gov_document_type_ar",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Issue On",
            "fieldname": "issue_on",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": "Expire On",
            "fieldname": "expire_on",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": "Expire in Days",
            "fieldname": "expire_in_days",
            "fieldtype": "Int",
            "width": 130
        },
        {
            "label": "Renewal Status",
            "fieldname": "renewal_status",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": "Customer",
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 150
        },
        {
            "label": "Customer Name",
            "fieldname": "custom_customer_name",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": "Supplier",
            "fieldname": "supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 120
        },
        {
            "label": "Supplier Name",
            "fieldname": "custom_supplier_name",
            "fieldtype": "Data",
            "width": 180
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)

    data = frappe.db.sql("""
        SELECT
            name,
            gov_document_type,
            gov_document_type_ar,
            issue_on,
            expire_on,
            DATEDIFF(expire_on, CURDATE()) AS expire_in_days,
            renewal_status,
            customer,
            custom_customer_name,
            supplier,
            custom_supplier_name
        FROM
            `tabGov Document Expiration`
        WHERE
            docstatus < 2
            {conditions}
        ORDER BY
            expire_on ASC
    """.format(conditions=conditions), filters, as_dict=1)

    return data


def get_conditions(filters):
    conditions = ""

    if filters.get("customer"):
        conditions += " AND customer = %(customer)s"

    if filters.get("show_expired"):
        conditions += " AND expire_on < CURDATE()"

    elif filters.get("days_to_expire"):
        conditions += " AND expire_on BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %(days_to_expire)s DAY)"

    return conditions