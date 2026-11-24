"""Excel export: four sheets, same filters and permission scope as the screen."""
from io import BytesIO

import frappe
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from custom_addons.custom_addons.page.po_amendment_insights import approvals, overview, root_cause
from custom_addons.custom_addons.page.po_amendment_insights.filters import LOG, scoped, state_col

REGISTER = (
	"name", "log_date", "cancelled_po_number", "new_po_number", "original_supplier", "replacement_supplier",
	"project", "requested_by", "requesting_department", "amendment_type", "amendment_reason_category",
	"implementation_status", "total_value_difference", "comparison_value_status", "rate_benefit",
	"po_date_gap_days",
)
HEAD = PatternFill("solid", fgColor="1F3864")


def build(f):
	wb = Workbook()
	_summary(wb.active, f)
	_register(wb.create_sheet("Register"), f)
	_gates(wb.create_sheet("Approval Gates"), f)
	_impact(wb.create_sheet("Impact and Actions"), f)
	out = BytesIO()
	wb.save(out)
	name = f"CPC_PO_Amendment_Insights_{f['from_date']}_to_{f['to_date']}.xlsx"
	return name, out.getvalue()


def _sheet(ws, title, header, rows):
	ws.title = title
	ws.append(header)
	for cell in ws[1]:
		cell.font, cell.fill = Font(bold=True, color="FFFFFF"), HEAD
	for r in rows:
		ws.append(list(r))
	for col in ws.columns:
		ws.column_dimensions[col[0].column_letter].width = min(60, max(12, max(len(str(c.value or "")) for c in col[:50]) + 2))


def _summary(ws, f):
	c = overview.cards(f)
	rows = [
		("Total Amendments", c["total"]), ("Open / Active", c["open"]), ("Net Value Impact", c["net_value"]),
		("Value increased (logs)", c["increased"]), ("Value reduced (logs)", c["reduced"]),
		("Pending Approvals", c["pending"]), ("Slowest gate", c["slowest_gate"] or "-"),
		("Rate Benefit", c["rate_benefit"]), ("Avg Days to Replacement PO", c["avg_gap_days"]),
		("Period", f"{f['from_date']} to {f['to_date']}"),
	]
	_sheet(ws, "Summary", ["Measure", "Value"], rows)


def _register(ws, f):
	L, q = scoped(f)
	data = q.select(*[getattr(L, c) for c in REGISTER], state_col(L).as_("state")).orderby(L.log_date).orderby(L.name).run(as_dict=True)
	cols = list(REGISTER) + ["state"]
	_sheet(ws, "Register", [c.replace("_", " ").title() for c in cols], ([r.get(c) for c in cols] for r in data))


def _gates(ws, f):
	g = approvals.gate_stats(f)
	_sheet(ws, "Approval Gates", ["Gate", "Pending", "Approved", "Rejected", "Avg days"],
		((x["state"], x["pending"], x["approved"], x["rejected"], x["avg_days"]) for x in g))


def _impact(ws, f):
	rows = root_cause.impact_list(f, 100000, 0)["rows"]
	_sheet(ws, "Impact and Actions", ["Log", "Date", "Business Impact", "Risk / Impact Assessment", "Corrective / Preventive Action"],
		((r.name, r.log_date, r.business_impact, r.risk__impact_assessment, r.corrective__preventive_action) for r in rows))
