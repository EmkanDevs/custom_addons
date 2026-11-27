"""Who may see what. All checks run on the server; the page only hides things."""
import frappe
from frappe import _
from frappe.core.doctype.user_permission.user_permission import get_user_permissions


def require_view():
        page_roles = set(
                frappe.get_all(
                        "Has Role",
                        filters={"parent": "supplier-performance", "parenttype": "Page"},
                        pluck="role",
                )
        )
        if page_roles and not (set(frappe.get_roles()) & page_roles):
                frappe.throw(_("You are not permitted to view the Supplier Performance Dashboard."), frappe.PermissionError)
        if not frappe.has_permission("Purchase Order", "read"):
                frappe.throw(_("You need read access to Purchase Orders to view supplier performance."), frappe.PermissionError)


def allowed_suppliers():
        """Suppliers the user may see, or None when no user permission restricts them."""
        if not get_user_permissions().get("Supplier"):
                return None
        return set(frappe.get_list("Supplier", pluck="name", limit_page_length=0))
