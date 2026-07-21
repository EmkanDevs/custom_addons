import frappe
from frappe import _
from frappe.model.document import Document


class MedicalInsuranceRequest(Document):
    pass


@frappe.whitelist()
def get_family_members(employee):
    employee_number = frappe.db.get_value("Employee", employee, "employee")

    if not employee_number:
        return []

    return frappe.get_all(
        "Medical Insurance Sheet",
        filters={
            "employee_number": employee_number,
            "relationship": ["!=", "Employee"]
        },
        fields=[
            "member_name",
            "relationship",
            "id_no",
			"member_effective_date"
        ],
        order_by="member_name"
    )


@frappe.whitelist()
def inform_medical_insurance(docname):
    doc = frappe.get_doc("Medical Insurance Request", docname)

    if doc.docstatus != 1:
        frappe.throw(_("Only submitted requests can be informed."))

    if not doc.inform_medical_insurance:
        frappe.throw(_("Please select a user in Inform Medical Insurance."))

    recipient = frappe.db.get_value(
        "User",
        doc.inform_medical_insurance,
        "email"
    )

    if not recipient:
        frappe.throw(_("The selected user does not have an email address."))

    frappe.sendmail(
		recipients=[recipient],
		subject=f"Medical Insurance Request Submitted - {doc.name}",
		message=f"""
		<p style="font-size:16px;">Dear <strong>{frappe.db.get_value("User", doc.inform_medical_insurance, "full_name") or "User"}</strong>,</p>

		<p style="font-size:15px;">
			A new <strong>Medical Insurance Request</strong> has been submitted and requires your attention.
		</p>

		<table
			cellpadding="10"
			cellspacing="0"
			border="1"
			width="100%"
			style="
				border-collapse:collapse;
				border:1px solid #d1d8dd;
				font-family:Arial, Helvetica, sans-serif;
				font-size:14px;
			"
		>
			<tr>
				<td width="40%" style="background:#f7fafc;font-weight:bold;border:1px solid #d1d8dd;">
					Request No.
				</td>
				<td width="60%" style="border:1px solid #d1d8dd;">
					<a href="https://incharge.emkan-dev.com/app/medical-insurance-request/{doc.name}">
						{doc.name}
					</a>
				</td>
			</tr>

			<tr>
				<td style="background:#f7fafc;font-weight:bold;border:1px solid #d1d8dd;">
					Request Type
				</td>
				<td style="border:1px solid #d1d8dd;">
					{doc.request_type}
				</td>
			</tr>

			<tr>
				<td style="background:#f7fafc;font-weight:bold;border:1px solid #d1d8dd;">
					Sponsor
				</td>
				<td style="border:1px solid #d1d8dd;">
					{doc.sponsor_name}
				</td>
			</tr>

			<tr>
				<td style="background:#f7fafc;font-weight:bold;border:1px solid #d1d8dd;">
					Employee ID
				</td>
				<td style="border:1px solid #d1d8dd;">
					{doc.sponsor}
				</td>
			</tr>

			<tr>
				<td style="background:#f7fafc;font-weight:bold;border:1px solid #d1d8dd;">
					Designation
				</td>
				<td style="border:1px solid #d1d8dd;">
					{doc.designation or "-"}
				</td>
			</tr>

			<tr>
				<td style="background:#f7fafc;font-weight:bold;border:1px solid #d1d8dd;">
					Effective Date
				</td>
				<td style="border:1px solid #d1d8dd;">
					{doc.effective_date or "-"}
				</td>
			</tr>

			<tr>
				<td style="background:#f7fafc;font-weight:bold;border:1px solid #d1d8dd;">
					Include Family
				</td>
				<td style="border:1px solid #d1d8dd;">
					{"Yes" if doc.include_family else "No"}
				</td>
			</tr>
		</table>

		<br>

		<p style="font-size:15px;">
			Please log in to ERPNext and review this request at your earliest convenience.
		</p>

		<br>

		<p>
			Thank you,<br>
			<strong>Incharge Company</strong>
		</p>
		""",
		now=True
	)

    return True