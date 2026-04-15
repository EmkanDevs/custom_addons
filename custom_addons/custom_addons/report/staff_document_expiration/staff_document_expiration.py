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
#             "options": "Staff Document Expiration",
#             "width": 180
#         },
#         {
#             "label": "Employee No",
#             "fieldname": "custom_employee_no",
#             "fieldtype": "Link",
#             "options": "Employee",
#             "width": 150
#         },
#         {
#             "label": "Employee Name",
#             "fieldname": "custom_employee_name_",
#             "fieldtype": "Link",
#             "options": "Customer",
#             "width": 150
#         },
#         {
#             "label": "Gov Document Type",
#             "fieldname": "gov_document_type",
#             "fieldtype": "Data",
#             "width": 180
#         },
#         {
#             "label": "Gov Document Type AR",
#             "fieldname": "gov_document_type_ar",
#             "fieldtype": "Data",
#             "width": 180
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
#             "label": "Expires in Days",
#             "fieldname": "expires_in_days",
#             "fieldtype": "Int",
#             "width": 120
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
#             "label": "Customer Name",
#             "fieldname": "customer_name",
#             "fieldtype": "Data",
#             "width": 180
#         },
#         {
#             "label": "Supplier",
#             "fieldname": "supplier",
#             "fieldtype": "Link",
#             "options": "Supplier",
#             "width": 120
#         },
#         {
#             "label": "Supplier Name",
#             "fieldname": "supplier_name",
#             "fieldtype": "Data",
#             "width": 180
#         },
#     ]

# def get_data(filters):
#     conditions = get_conditions(filters)

#     data = frappe.db.sql("""
#         SELECT
#             name,
#             custom_employee_no,
#             custom_employee_name_,
#             gov_document_type,
#             gov_document_type_ar,
#             issue_on,
#             expire_on,
#             expires_in_days,
#             renewal_status,
#             customer,
#             customer_name,
#             supplier,
#             supplier_name
#         FROM
#             `tabStaff Document Expiration`
#         WHERE
#             docstatus < 2
#             {conditions}
#         ORDER BY
#             expire_on ASC
#     """.format(conditions=conditions), filters, as_dict=1)

#     return data

# def get_conditions(filters):
#     conditions = ""

#     if filters.get("gov_document_type"):
#         conditions += " AND gov_document_type = %(gov_document_type)s"

#     if filters.get("employee"):
#         conditions += " AND employee = %(employee)s"

#     if filters.get("renewal_status"):
#         conditions += " AND renewal_status = %(renewal_status)s"

#     if filters.get("customer"):
#         conditions += " AND customer = %(customer)s"

#     if filters.get("supplier"):
#         conditions += " AND supplier = %(supplier)s"

#     if filters.get("from_date"):
#         conditions += " AND expire_on >= %(from_date)s"

#     if filters.get("to_date"):
#         conditions += " AND expire_on <= %(to_date)s"

#     if filters.get("customer"):
#         conditions += " AND customer = %(customer)s"

#     if filters.get("show_expired"):
#         # Show only records where expire_on is before today
#         conditions += " AND expire_on < CURDATE()"

#     elif filters.get("days_to_expire"):
#         # Show records expiring within the given number of days from today
#         conditions += " AND expire_on BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %(days_to_expire)s DAY)"

#     return conditions


# Copyright (c) 2026, Administrator and contributors
# For license information, please see license.txt

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
            "options": "Staff Document Expiration",
            "width": 180
        },
        {
            "label": "Employee No",
            "fieldname": "custom_employee_no",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150
        },
        {
            "label": "Employee Name",
            "fieldname": "custom_employee_name_",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": "Gov Document Type",
            "fieldname": "gov_document_type",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": "Gov Document Type AR",
            "fieldname": "gov_document_type_ar",
            "fieldtype": "Data",
            "width": 180
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
            "label": "Expires in Days",
            "fieldname": "expires_in_days",
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
            "fieldname": "customer_name",
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
            "fieldname": "supplier_name",
            "fieldtype": "Data",
            "width": 180
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)

    data = frappe.db.sql("""
        SELECT
            name,
            custom_employee_no,
            custom_employee_name_,
            gov_document_type,
            gov_document_type_ar,
            issue_on,
            expire_on,
            DATEDIFF(expire_on, CURDATE()) AS expires_in_days,
            renewal_status,
            customer,
            customer_name,
            supplier,
            supplier_name
        FROM
            `tabStaff Document Expiration`
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

    if filters.get("employee"):
        conditions += " AND custom_employee_no = %(employee)s"

    if filters.get("show_expired"):
        conditions += " AND expire_on < CURDATE()"

    elif filters.get("days_to_expire"):
        conditions += " AND expire_on BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %(days_to_expire)s DAY)"

    return conditions