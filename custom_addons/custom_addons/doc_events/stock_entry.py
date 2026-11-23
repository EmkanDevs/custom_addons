def validate(doc, method=None):
    set_material_request_references(doc)


def set_material_request_references(doc):
    # dict.fromkeys keeps first-seen order and removes duplicates
    mrs = dict.fromkeys(row.material_request for row in doc.items if row.material_request)
    doc.custom_material_request_references = "\n".join(mrs)