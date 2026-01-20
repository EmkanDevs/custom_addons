# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta

class GovDocumentExpiration(Document):
	pass

def renewal_status():
	today = datetime.today().date()

	# Fetch all documents with the required filters
	docs = frappe.get_all(
		"Gov Document Expiration",
		filters={
			"renewal_status": "Renewed - تم التجديد",
			"expire_on": ["is", "set"],
			"reminder_in_days": ["is", "set"]
		},
		fields=["name", "expire_on", "reminder_in_days"]
	)

	# Filter documents based on the reminder logic
	filtered_docs = []
	for doc in docs:
		if doc.expire_on and doc.reminder_in_days is not None:
			reminder_days = int(doc.reminder_in_days)
			reminder_date = doc.expire_on - timedelta(days=reminder_days)
			if today >= reminder_date:
				filtered_docs.append(doc.name)
	
	for row in filtered_docs:
		doc = frappe.get_doc("Gov Document Expiration",row)
		doc.db_set("renewal_status","Under Renewal - تحت التجديد")


def send_expiration_reminders():
	docs = frappe.get_all("Gov Document Expiration",
		filters={"docstatus": 0, "renewal_status": "Under Renewal - تحت التجديد"},
		fields=["name", "expire_on", "reminder_in_days", "gov_document_type","issue_on","customer","latest_copy","prev_copy"])
	
	today = datetime.today().date()

	for doc in docs:
		if not doc.expire_on or not doc.reminder_in_days:
			continue

		expiry_date = doc.expire_on
		start_reminder_days = int(doc.reminder_in_days)
		interval = 7  # You can change this to any interval, say 5, 10, etc.

		# Generate reminder dates: 30, 23, 16, 9, 2 days before expiry
		reminder_days_list = [start_reminder_days - i * interval for i in range((start_reminder_days // interval) + 1)]
		
		# Check if today is one of the reminder days
		if (expiry_date - today).days in reminder_days_list:
			gov_doc_type = frappe.get_doc("Gov Document Type", doc.gov_document_type)
			role = gov_doc_type.remind_by_role
			
			if not role:
				continue

			user_emails = get_users_by_role(role)
			if user_emails:
				send_reminder_email(doc.name, doc.expire_on, user_emails,doc.customer,doc.gov_document_type,doc.issue_on,doc.latest_copy,doc.prev_copy)

def get_users_by_role(role):
	users = frappe.get_all("Has Role",
		filters={"role": role},
		fields=["parent as user"])
	
	email_list = []
	for u in users:
		if frappe.db.get_value("User", u.user, "enabled") == 1:
			email = frappe.db.get_value("User", u.user, "email")
			if email:
				email_list.append(email)
	
	return email_list
	
def send_reminder_email(doc_name, expire_on, recipients, customer, gov_document_type, issue_on, latest_copy, prev_copy):
	base_url = frappe.utils.get_url()
	document_name = "Gov Document Expiration"
	doc_link = f"{base_url}/app/{document_name.lower().replace(' ', '-')}/{doc_name}"

	subject = f"Reminder: Document {doc_name} is expiring on {expire_on}"
	message = f"""
	Dear User,<br><br>

	This is a reminder that the document '{doc_name}' is set to expire on {expire_on}.<br>
	<b>Document Type:</b> {gov_document_type}<br>
	<b>Customer:</b> {customer}<br>
	<b>Issue Date:</b> {issue_on}<br>
	
	<b>Document Link:</b> <a href="{doc_link}">{doc_name}</a><br><br>

	Please take the necessary action.<br><br>

	Regards,<br>
	System Notification
	"""

	attachments = []

	def get_attachment(file_url):
		if not file_url:
			return None
		try:
			file_doc = frappe.get_doc("File", {"file_url": file_url})
			if file_doc.is_private:
				file_path = frappe.get_site_path("private", file_doc.file_url.lstrip("/private/"))
			else:
				file_path = frappe.get_site_path("public", file_doc.file_url.lstrip("/"))
			with open(file_path, "rb") as f:
				return {
					"fname": file_doc.file_name,
					"fcontent": f.read()
				}
			# print(f"attachments: {file_doc}")

		except Exception as e:
			frappe.log_error(f"Failed to attach file {file_url}: {str(e)}")
			return None

	for file_url in [latest_copy, prev_copy]:
		attachment = get_attachment(file_url)
		if attachment:
			attachments.append(attachment)

	print(f"Sending email to: {recipients}")

	frappe.sendmail(
		recipients=recipients,
		subject=subject,
		message=message,
		attachments=attachments,
		now=frappe.flags.in_test,
	)
