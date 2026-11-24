"""Create the PO Amendment roles and rebuild the 3-gate approval workflow.

Safe to re-run: roles and master records are checked first, and the
workflow is updated in place.
"""
import frappe

DOCTYPE = "PO Amendment Log"
WORKFLOW = "PO Amendment Log Approval"

REQUESTER = "PO Amendment Requester"
TECHNICAL = "Technical Approver"
PROCUREMENT = "Procurement Approver"
FINANCE = "Finance Approver"
ROLES = [REQUESTER, TECHNICAL, PROCUREMENT, FINANCE, "Dashboard Manager"]

# (state, docstatus, style, allow_edit, implementation_status set on entry)
STATES = [
    ("Draft", 0, "", REQUESTER, None),
    ("Pending Technical/Quality", 0, "Warning", TECHNICAL, None),
    ("Pending Procurement", 0, "Warning", PROCUREMENT, None),
    ("Pending Finance", 0, "Warning", FINANCE, None),
    # Buyers keep updating Implementation Status after approval
    ("Approved", 1, "Success", REQUESTER, "Approved"),
    ("Rejected", 0, "Danger", REQUESTER, "Rejected"),
]

# (from, action, to, role, allow_self_approval)
TRANSITIONS = [
    ("Draft", "Submit for Approval", "Pending Technical/Quality", REQUESTER, 1),
    ("Draft", "Submit for Approval", "Pending Technical/Quality", "System Manager", 1),
    ("Pending Technical/Quality", "Approve", "Pending Procurement", TECHNICAL, 0),
    ("Pending Technical/Quality", "Approve", "Pending Procurement", "System Manager", 0),
    ("Pending Technical/Quality", "Reject", "Rejected", TECHNICAL, 0),
    ("Pending Technical/Quality", "Reject", "Rejected", "System Manager", 0),
    ("Pending Procurement", "Approve", "Pending Finance", PROCUREMENT, 0),
    ("Pending Procurement", "Approve", "Pending Finance", "System Manager", 0),
    ("Pending Procurement", "Reject", "Rejected", PROCUREMENT, 0),
    ("Pending Procurement", "Reject", "Rejected", "System Manager", 0),
    ("Pending Finance", "Approve", "Approved", FINANCE, 0),
    ("Pending Finance", "Approve", "Approved", "System Manager", 0),
    ("Pending Finance", "Reject", "Rejected", FINANCE, 0),
    ("Pending Finance", "Reject", "Rejected", "System Manager", 0),
]


def execute():
    create_roles()
    create_masters()
    build_workflow()
    remap_old_states()


def create_roles():
    for role in ROLES:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)


def create_masters():
    for state, _, style, _, _ in STATES:
        if not frappe.db.exists("Workflow State", state):
            frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state, "style": style}).insert(ignore_permissions=True)
    for action in {t[1] for t in TRANSITIONS}:
        if not frappe.db.exists("Workflow Action Master", action):
            frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(ignore_permissions=True)


def build_workflow():
    if frappe.db.exists("Workflow", WORKFLOW):
        wf = frappe.get_doc("Workflow", WORKFLOW)
        wf.set("states", [])
        wf.set("transitions", [])
    else:
        wf = frappe.new_doc("Workflow")
        wf.workflow_name = WORKFLOW
    wf.document_type = DOCTYPE
    wf.workflow_state_field = "workflow_state"
    wf.is_active = 1
    wf.override_status = 0
    wf.send_email_alert = 0
    wf.track_state_transitions = 1  # needed by the Progress tab
    add_states(wf)
    add_transitions(wf)
    wf.save(ignore_permissions=True)


def add_states(wf):
    for state, docstatus, _, role, impl in STATES:
        row = {"state": state, "doc_status": str(docstatus), "allow_edit": role}
        if impl:
            row.update(update_field="implementation_status", update_value=impl)
        wf.append("states", row)


def add_transitions(wf):
    for src, action, dst, role, self_ok in TRANSITIONS:
        wf.append("transitions", {
            "state": src, "action": action, "next_state": dst,
            "allowed": role, "allow_self_approval": self_ok,
        })


def remap_old_states():
    # The old single gate is now the first gate
    frappe.db.set_value(
        DOCTYPE, {"workflow_state": "Pending Approval"}, "workflow_state",
        "Pending Technical/Quality", update_modified=False,
    )
