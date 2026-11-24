"""Workflow state names shared by the PO Amendment Log controller, reports and the dashboard."""

# Every state that means "waiting for an approver". The first one is kept for logs made before the gates.
PENDING_STATES = (
	"Pending Approval",
	"Pending Technical/Quality",
	"Pending Procurement",
	"Pending Finance",
)
CLOSED_STATES = ("Approved", "Rejected")
# The approval gates of the current workflow, in order. The dashboard draws one box per gate.
GATE_STATES = PENDING_STATES[1:]
