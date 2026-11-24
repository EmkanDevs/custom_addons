"""Who may see what. All checks run on the server; hiding a tab in JS is not security."""
import frappe
from frappe import _

TECHNICAL = "Technical Approver"
PROCUREMENT = "Procurement Approver"
FINANCE = "Finance Approver"
MANAGER = "Dashboard Manager"

# Pending state -> role that can act on it
GATE_ROLES = {
	"Pending Technical/Quality": TECHNICAL,
	"Pending Procurement": PROCUREMENT,
	"Pending Finance": FINANCE,
}
APPROVER_ROLES = list(GATE_ROLES.values())


def is_manager(user=None):
	roles = set(frappe.get_roles(user))
	return bool(roles & {MANAGER, "System Manager"})


def is_approver(user=None):
	return bool(set(frappe.get_roles(user)) & set(APPROVER_ROLES))


def require_view():
	if not (is_manager() or is_approver()):
		frappe.throw(_("You are not permitted to view the PO Amendment Insights Dashboard."), frappe.PermissionError)


def require_manager():
	if not is_manager():
		frappe.throw(_("Only the Dashboard Manager can use this."), frappe.PermissionError)


def default_approver():
	"""An approver who is not a manager starts on their own queue."""
	user = frappe.session.user
	return user if is_approver(user) and not is_manager(user) else None
