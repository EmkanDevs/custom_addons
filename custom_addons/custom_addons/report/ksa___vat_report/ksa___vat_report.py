import frappe


def execute(filters=None):
    filters = frappe._dict(filters or {})

    validate_filters(filters)

    columns = get_columns()
    data = get_data(filters)

    for idx, row in enumerate(data, start=1):
        row["sr_no"] = idx

    return columns, data


def validate_filters(filters):
    if not filters.get("from_date"):
        frappe.throw("From Date is required.")

    if not filters.get("to_date"):
        frappe.throw("To Date is required.")

    if filters.from_date > filters.to_date:
        frappe.throw("From Date cannot be greater than To Date.")


def get_columns():
    return [
        # {
        #     "label": "Sr No",
        #     "fieldname": "sr_no",
        #     "fieldtype": "Int",
        #     "width": 70,
        # },
        {
            "label": "Type",
            "fieldname": "type",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": "Invoice Number",
            "fieldname": "invoice_number",
            "fieldtype": "Dynamic Link",
            "options": "doctype",
            "width": 150,
        },
        {
            "label": "Year",
            "fieldname": "year",
            "fieldtype": "Int",
            "width": 80,
        },
        {
            "label": "Quarter Name",
            "fieldname": "quarter_name",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Month Number",
            "fieldname": "month_number",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Month Name",
            "fieldname": "month_name",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": "Date",
            "fieldname": "date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": "Customer/Supplier",
            "fieldname": "customer_supplier",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": "Tax Account",
            "fieldname": "tax_account",
            "fieldtype": "Link",
            "options": "Account",
            "width": 200,
        },
        {
            "label": "Root Type",
            "fieldname": "root_type",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Source",
            "fieldname": "source",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": "Tax ID (TRN)",
            "fieldname": "tax_id",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": "Tax Template",
            "fieldname": "tax_template",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": "Taxable Amount",
            "fieldname": "taxable_amount",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": "VAT Amount",
            "fieldname": "vat_amount",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": "Total Amount",
            "fieldname": "total_amount",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": "Document Type",
            "fieldname": "doctype",
            "fieldtype": "Data",
            "hidden": 1,
        },
    ]


def get_data(filters):
    conditions = get_common_conditions(filters)

    query = """
        SELECT
            'Output VAT (Sales)' AS type,
            si.name AS invoice_number,
            YEAR(si.posting_date) AS year,
            CONCAT('Q', QUARTER(si.posting_date)) AS quarter_name,
            MONTH(si.posting_date) AS month_number,
            MONTHNAME(si.posting_date) AS month_name,
            si.posting_date AS date,
            si.customer_name AS customer_supplier,

            tax_data.tax_account AS tax_account,
            tax_data.root_type AS root_type,

            'Sales Invoice' AS source,

            si.tax_id AS tax_id,
            si.taxes_and_charges AS tax_template,

            si.base_net_total AS taxable_amount,

            IFNULL(tax_data.vat_amount, 0) AS vat_amount,

            si.base_grand_total AS total_amount,

            'Sales Invoice' AS doctype

        FROM `tabSales Invoice` si

        LEFT JOIN (
            SELECT
                stc.parent,
                stc.account_head AS tax_account,
                account.root_type,
                SUM(
                    CASE
                        WHEN stc.rate > 0
                        THEN stc.tax_amount
                        ELSE 0
                    END
                ) AS vat_amount

            FROM `tabSales Taxes and Charges` stc

            LEFT JOIN `tabAccount` account
                ON account.name = stc.account_head

            GROUP BY
                stc.parent,
                stc.account_head,
                account.root_type
        ) tax_data
            ON tax_data.parent = si.name

        WHERE
            si.docstatus = 1
            AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            {sales_conditions}


        UNION ALL


        SELECT
            'Input VAT (Purchases)' AS type,
            pi.name AS invoice_number,
            YEAR(pi.posting_date) AS year,
            CONCAT('Q', QUARTER(pi.posting_date)) AS quarter_name,
            MONTH(pi.posting_date) AS month_number,
            MONTHNAME(pi.posting_date) AS month_name,
            pi.posting_date AS date,
            pi.supplier_name AS customer_supplier,

            tax_data.tax_account AS tax_account,
            tax_data.root_type AS root_type,

            'Purchase Invoice' AS source,

            pi.tax_id AS tax_id,
            pi.taxes_and_charges AS tax_template,

            pi.base_net_total AS taxable_amount,

            IFNULL(tax_data.vat_amount, 0) AS vat_amount,

            pi.base_grand_total AS total_amount,

            'Purchase Invoice' AS doctype

        FROM `tabPurchase Invoice` pi

        LEFT JOIN (
            SELECT
                ptc.parent,
                ptc.account_head AS tax_account,
                account.root_type,
                SUM(
                    CASE
                        WHEN ptc.rate > 0
                        THEN ptc.tax_amount
                        ELSE 0
                    END
                ) AS vat_amount

            FROM `tabPurchase Taxes and Charges` ptc

            LEFT JOIN `tabAccount` account
                ON account.name = ptc.account_head

            GROUP BY
                ptc.parent,
                ptc.account_head,
                account.root_type
        ) tax_data
            ON tax_data.parent = pi.name

        WHERE
            pi.docstatus = 1
            AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
            {purchase_conditions}


        UNION ALL


        SELECT
            'Payment Entry' AS type,
            pe.name AS invoice_number,
            YEAR(pe.posting_date) AS year,
            CONCAT('Q', QUARTER(pe.posting_date)) AS quarter_name,
            MONTH(pe.posting_date) AS month_number,
            MONTHNAME(pe.posting_date) AS month_name,
            pe.posting_date AS date,
            pe.party_name AS customer_supplier,

            tax_data.tax_account AS tax_account,
            tax_data.root_type AS root_type,

            'Payment Entry' AS source,

            NULL AS tax_id,
            NULL AS tax_template,

            (
                IFNULL(pe.base_paid_amount, 0)
                + IFNULL(pe.base_received_amount, 0)
            ) AS taxable_amount,

            IFNULL(tax_data.vat_amount, 0) AS vat_amount,

            (
                IFNULL(pe.base_paid_amount, 0)
                + IFNULL(pe.base_received_amount, 0)
            ) AS total_amount,

            'Payment Entry' AS doctype

        FROM `tabPayment Entry` pe

        LEFT JOIN (
            SELECT
                atc.parent,
                atc.account_head AS tax_account,
                account.root_type,
                SUM(
                    IFNULL(atc.tax_amount, 0)
                ) AS vat_amount

            FROM `tabAdvance Taxes and Charges` atc

            LEFT JOIN `tabAccount` account
                ON account.name = atc.account_head

            GROUP BY
                atc.parent,
                atc.account_head,
                account.root_type
        ) tax_data
            ON tax_data.parent = pe.name

        WHERE
            pe.docstatus = 1
            AND pe.posting_date BETWEEN %(from_date)s AND %(to_date)s
            {payment_conditions}


        UNION ALL


        SELECT
            'Journal Entry' AS type,
            je.name AS invoice_number,
            YEAR(je.posting_date) AS year,
            CONCAT('Q', QUARTER(je.posting_date)) AS quarter_name,
            MONTH(je.posting_date) AS month_number,
            MONTHNAME(je.posting_date) AS month_name,
            je.posting_date AS date,
            je.pay_to_recd_from AS customer_supplier,

            tax_data.tax_account AS tax_account,
            tax_data.root_type AS root_type,

            'Journal Entry' AS source,

            NULL AS tax_id,
            NULL AS tax_template,

            je.total_amount AS taxable_amount,

            IFNULL(tax_data.vat_amount, 0) AS vat_amount,

            je.total_amount AS total_amount,

            'Journal Entry' AS doctype

        FROM `tabJournal Entry` je

        LEFT JOIN (
            SELECT
                jea.parent,
                jea.account AS tax_account,
                account.root_type,
                SUM(
                    IFNULL(jea.debit, 0)
                    + IFNULL(jea.credit, 0)
                ) AS vat_amount

            FROM `tabJournal Entry Account` jea

            INNER JOIN `tabAccount` account
                ON account.name = jea.account

            WHERE
                account.account_type IN ('Tax', 'Charge')

            GROUP BY
                jea.parent,
                jea.account,
                account.root_type
        ) tax_data
            ON tax_data.parent = je.name

        WHERE
            je.docstatus = 1
            AND je.posting_date BETWEEN %(from_date)s AND %(to_date)s
            {journal_conditions}

        ORDER BY
            type,
            year,
            month_number,
            date
    """.format(
        sales_conditions=conditions["sales"],
        purchase_conditions=conditions["purchase"],
        payment_conditions=conditions["payment"],
        journal_conditions=conditions["journal"],
    )

    return frappe.db.sql(
        query,
        {
            "from_date": filters.get("from_date"),
            "to_date": filters.get("to_date"),
            "root_type": filters.get("root_type"),
            "customer_supplier": filters.get("customer_supplier"),
        },
        as_dict=True,
    )


def get_common_conditions(filters):
    sales = []
    purchase = []
    payment = []
    journal = []

    root_type = filters.get("root_type")
    customer_supplier = filters.get("customer_supplier")
    source = filters.get("source")

    if root_type:
        sales.append("AND tax_data.root_type = %(root_type)s")
        purchase.append("AND tax_data.root_type = %(root_type)s")
        payment.append("AND tax_data.root_type = %(root_type)s")
        journal.append("AND tax_data.root_type = %(root_type)s")

    if customer_supplier:
        sales.append(
            "AND si.customer_name LIKE CONCAT('%%', %(customer_supplier)s, '%%')"
        )

        purchase.append(
            "AND pi.supplier_name LIKE CONCAT('%%', %(customer_supplier)s, '%%')"
        )

        payment.append(
            "AND pe.party_name LIKE CONCAT('%%', %(customer_supplier)s, '%%')"
        )

        journal.append(
            "AND je.pay_to_recd_from LIKE CONCAT('%%', %(customer_supplier)s, '%%')"
        )

    if source:
        if source != "Sales Invoice":
            sales.append("AND 1 = 0")

        if source != "Purchase Invoice":
            purchase.append("AND 1 = 0")

        if source != "Payment Entry":
            payment.append("AND 1 = 0")

        if source != "Journal Entry":
            journal.append("AND 1 = 0")

    return {
        "sales": "\n".join(sales),
        "purchase": "\n".join(purchase),
        "payment": "\n".join(payment),
        "journal": "\n".join(journal),
    }