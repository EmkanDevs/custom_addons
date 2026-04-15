# Copyright (c) 2025, Finbyz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta
from custom_addons.custom_addons.override import assign_to


class HelpdeskRequest(Document):
    def validate(self):
        for row in self.custom_user_details:
            if row.user and not frappe.get_all("ToDo", filters={"reference_type": "Helpdesk Request","reference_name": self.name,"status": "Open","allocated_to": row.user}):	
                assign_to.add(
                    dict(
                        assign_to=[row.user],
                        doctype="Helpdesk Request",
                        name=self.name,
                        priority= "Medium",
                        notify=True
                    ),
                    ignore_permissions=True,
                )
    def on_update(self):
        # Only set response date if transitioning TO "Waiting for User Feedback"
        prev_state = self._doc_before_save.workflow_state if self._doc_before_save else None
        
        if self.workflow_state == "Waiting for User Feedback" and prev_state != "Waiting for User Feedback":
            self.db_set("custom_it_response_date", frappe.utils.now_datetime())
        
        elif self.workflow_state == "Closed" and prev_state != "Closed":
            self.db_set("custom_closed_ticket_date", frappe.utils.now_datetime())

    def before_save(self):
        user_ids = [d.user or d.value for d in self.custom_user_details if (d.user or d.value)]
        if not user_ids:
            self.custom_assigned_user = ""
            return

        users = frappe.get_all("User", filters={"name": ["in", user_ids]}, fields=["name", "full_name"])
        user_map = {u.name: u.full_name or u.name for u in users}
        self.custom_assigned_user = ", ".join(user_map.get(uid, uid) for uid in user_ids)


@frappe.whitelist()
def check_and_close_timeout_tickets():
    """
    Check for tickets that have been in 'Waiting for User Feedback' state for more than 48 hours
    and automatically close them.
    This function can be called as a scheduled task or manually.
    """
    # Calculate the cutoff time (48 hours ago)
    cutoff_time = frappe.utils.now_datetime() - timedelta(hours=48)
    
    # Find all tickets in 'Waiting for User Feedback' state with custom_it_response_date older than 48 hours
    timeout_tickets = frappe.get_all(
        "Helpdesk Request",
        filters={
            "workflow_state": "Waiting for User Feedback",
            "custom_it_response_date": ["<", cutoff_time],
            "docstatus": 0  # Only draft documents
        },
        fields=["name", "custom_it_response_date"]
    )
    
    closed_count = 0
    for ticket in timeout_tickets:
        try:
            # Get the document
            doc = frappe.get_doc("Helpdesk Request", ticket.name)
            
            # Set workflow state to Closed
            doc.workflow_state = "Closed"
            
            # Set the closed date
            doc.custom_closed_ticket_date = frappe.utils.now_datetime()
            
            # Add a comment about automatic closure
            doc.add_comment(
                "Workflow",
                f"Ticket automatically closed due to 48-hour timeout from IT response date: {ticket.custom_it_response_date}"
            )
            
            # Save or submit depending on current status
            if doc.docstatus == 1:
                doc.save()
            else:
                doc.submit()
            
            closed_count += 1
            frappe.db.commit()
            
            frappe.logger().info(f"Auto-closed ticket {ticket.name} due to 48-hour timeout")
            
        except Exception as e:
            frappe.logger().error(f"Failed to auto-close ticket {ticket.name}: {str(e)}")
            frappe.db.rollback()
    
    return closed_count


