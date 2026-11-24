import frappe

# Link fields that point to the documents a Stock Entry was made from or against.
ITEM_REFERENCE_FIELDS = (
    "material_request",
    "custom_material_request",
    "against_stock_entry",
    "reference_purchase_receipt",
)
PARENT_REFERENCE_FIELDS = (
    "outgoing_stock_entry",
    "custom_return_material_ref_doc",
    "work_order",
    "purchase_order",
    "subcontracting_order",
    "pick_list",
    "delivery_note_no",
    "purchase_receipt_no",
    "sales_invoice_no",
    "job_card",
    "asset_repair",
)


def validate(doc, method=None):
    set_material_request_references(doc)
    set_reference_documents(doc)


def set_material_request_references(doc):
    # dict.fromkeys keeps first-seen order and removes duplicates
    mrs = dict.fromkeys(row.get("custom_material_request") for row in doc.items if row.get("custom_material_request"))
    doc.custom_material_request_references = "\n".join(mrs)


def set_reference_documents(doc):
    doc.custom_reference_documents = get_reference_documents(doc)


def get_reference_documents(doc):
    """Return one "Document Type: Name" line per unique document, Items first, then the form."""
    references = dict.fromkeys(
        [
            *_get_references(doc.get("items") or [], "Stock Entry Detail", ITEM_REFERENCE_FIELDS),
            *_get_references([doc], "Stock Entry", PARENT_REFERENCE_FIELDS),
        ]
    )
    return "\n".join(f"{doctype}: {name}" for doctype, name in references)


def _get_references(rows, doctype, fieldnames):
    meta = frappe.get_meta(doctype)
    link_fields = [
        (fieldname, df.options)
        for fieldname in fieldnames
        if (df := meta.get_field(fieldname)) and df.fieldtype == "Link"
    ]
    for row in rows:
        for fieldname, link_doctype in link_fields:
            if name := row.get(fieldname):
                yield link_doctype, name
