# Copyright (c) 2026, Administrator and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe import _
from frappe.model.document import Document


class UserDeactivateAccess(Document):
	def validate(self):
		self.validate_employee()
		self.validate_current_approver()

	def validate_employee(self):
		if not self.employee_id:
			employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
			if employee:
				self.employee_id = employee
				

	def validate_current_approver(self):
		if self.workflow_state == "Resolved":
			if frappe.session.user != self.approver:
				frappe.throw(
					_("Only the selected approver ({0}) can approve or reject this request.")
					.format(self.approver)
				)

	def on_update(self):
		"""
		Trigger actions based on workflow state transitions.
		"""
		doc_before_save = self.get_doc_before_save()
		old_state = doc_before_save.get("workflow_state") if doc_before_save else None
		
		if self.workflow_state != old_state:
			if self.workflow_state == "Approved":
				self.validate_approver_permissions()
			self.handle_workflow_transition()

	
	def handle_workflow_transition(self):
		state = self.workflow_state
		
		if state == "Send for Approval":
			self.send_approval_email()
		elif state == "Approved":
			self.send_system_manager_notification()
		elif state == "Resolved":
			self.complete_deactivation()
		elif state == "Rejected":
			# Rejection notification (optional, assuming handled by workflow notification or specific request)
			pass

	@frappe.whitelist()
	def send_approval_email(doc):
		import json
		if isinstance(doc, str):
			doc = json.loads(doc)
		
		doc = frappe.get_doc(doc)

		if not doc.approver:
			return

		requestor_name = frappe.utils.get_fullname(doc.owner)
		subject = _("Action Required: User Role Request for {0}").format(doc.employee_name)
		
		message = frappe.render_template("""
			<div style="font-family: Arial, sans-serif; color: #333;">
				<p>Dear Approver,</p>
				
				<p>A new <b>User Role Request</b> has been submitted for your review and approval.</p>

				<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
					<tr>
						<td style="padding: 8px; border-bottom: 1px solid #ddd; width: 150px; font-weight: bold;">Requested By:</td>
						<td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ requestor_name }}</td>
					</tr>
					<tr>
						<td style="padding: 8px; border-bottom: 1px solid #ddd; font-weight: bold;">Employee:</td>
						<td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ doc.employee_name }} ({{ doc.employee_id }})</td>
					</tr>
					<tr>
						<td style="padding: 8px; border-bottom: 1px solid #ddd; font-weight: bold;">Department:</td>
						<td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ doc.department }}</td>
					</tr>
					<tr>
						<td style="padding: 8px; border-bottom: 1px solid #ddd; font-weight: bold;">Designation:</td>
						<td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ doc.designation }}</td>
					</tr>
					<tr>
						<td style="padding: 8px; border-bottom: 1px solid #ddd; font-weight: bold;">Priority:</td>
						<td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ doc.priority }}</td>
					</tr>
				</table>

				<p><b>Requested Roles:</b></p>
				<ul>
				{% for row in doc.role_request_details %}
					<li>{{ row.requested_role }}</li>
				{% endfor %}
				</ul>

				<br>
				<p>
					<a href="{{ link }}" style="display: inline-block; background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold;">
						👉 Review and Approve
					</a>
				</p>
				
				<br>
				<p style="font-size: 12px; color: #777;">This is an automated message. Please do not reply directly to this email.</p>
			</div>
		""", {
			"doc": doc,
			"requestor_name": requestor_name,
			"link": frappe.utils.get_url_to_form(doc.doctype, doc.name)
		})

		frappe.sendmail(
			recipients=doc.approver,
			subject=subject,
			message=message
		)

	def send_system_manager_notification(self):
		send_system_manager_approval_email(self)

	def complete_deactivation(self):
		# Verify permissions or automate if system_user logic allows
		# Since this is triggered by workflow, we assume the transition logic (Allowed Roles) handled permission.
		complete_request_logic(self)

@frappe.whitelist()
def approve_request(docname):
	# Deprecated: Handled via Workflow
	pass

@frappe.whitelist()
def reject_request(docname, reason):
	# Deprecated: Handled via Workflow
	pass

@frappe.whitelist()
def complete_request(docname):
	# Deprecated: Handled via Workflow
	pass

def complete_request_logic(doc):
	"""
	Internal logic to deactivate user.
	"""
	# Deactivate the user
	if doc.employee_id:
		user_id = frappe.db.get_value("Employee", doc.employee_id, "user_id")
		if user_id:
			user_doc = frappe.get_doc("User", user_id)
			if user_doc.enabled:
				user_doc.enabled = 0
				user_doc.save(ignore_permissions=True)
				doc.add_comment("Info", _("User {0} has been deactivated.").format(user_id))
			else:
				doc.add_comment("Info", _("User {0} was already deactivated.").format(user_id))
	
	send_broadcast_notification(doc)


@frappe.whitelist()
def send_broadcast_notification(doc):
	if isinstance(doc, str):
		doc = json.loads(doc)

	if not isinstance(doc, Document):
		doc = frappe.get_doc(doc)

	# Fetch all enabled users with System Manager role except Administrator
	system_managers = frappe.get_all("Has Role", filters={"role": "System Manager", "parenttype": "User"}, pluck="parent")
	
	if not system_managers:
		return

	users = frappe.db.get_all(
		"User",
		filters={
			"name": ["in", system_managers],
			"enabled": 1,
			"name": ["!=", "Administrator"]
		},
		pluck="name"
	)
	
	if not users:
		return

	requestor_name = frappe.utils.get_fullname(doc.owner)
	
	subject = _("Notice: User Deactivation - {0}").format(doc.employee_name)
	
	message = frappe.render_template("""
		<div style="font-family: Arial, sans-serif; color: #333;">
			<p>Hello Team,</p>
			
			<p>Please be informed that the user access for <b>{{ doc.employee_name }}</b> ({{ doc.designation }}) has been deactivated.</p>

			<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
				<tr>
					<td style="padding: 8px; border-bottom: 1px solid #ddd; width: 150px; font-weight: bold;">Employee:</td>
					<td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ doc.employee_name }}</td>
				</tr>
				<tr>
					<td style="padding: 8px; border-bottom: 1px solid #ddd; font-weight: bold;">Department:</td>
					<td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ doc.department }}</td>
				</tr>
			</table>
			
			<br>
			<p style="font-size: 12px; color: #777;">This is an automated system notification.</p>
		</div>
	""", {
		"doc": doc
	})

	frappe.sendmail(
		recipients=users,
		subject=subject,
		message=message,
		delayed=False
	)

	
