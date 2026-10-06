import frappe
from mkan_customization.mkan_customization.override.asset import get_asset_project

def set_target_project(doc, method=None):
    if doc.purpose != "Receipt":
        return
    for row in doc.assets:
        if row.asset and not row.custom_target_project:
            row.custom_target_project = frappe.db.get_value("Asset", row.asset, "custom_project")

def update_asset_project(doc, method=None):
    for row in doc.assets:
        if not row.asset:
            continue
        project = get_asset_project(row.asset)
        if project:
            frappe.db.set_value("Asset", row.asset, "custom_project", project, update_modified=False)