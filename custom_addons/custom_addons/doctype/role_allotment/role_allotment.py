# Copyright (c) 2026, Administrator and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class RoleAllotment(Document):
	pass


def on_user_before_save(doc, method):
    old_doc = doc.get_doc_before_save()
    if not old_doc:
        return

    old_roles = {r.role for r in old_doc.roles}
    new_roles = {r.role for r in doc.roles}
    added_roles = new_roles - old_roles

    if not added_roles:
        return

    assigned_by = doc.modified_by or frappe.session.user
    assigned_by_name = (
        frappe.db.get_value("User", assigned_by, "full_name") or assigned_by
    )

    assigned_on = frappe.utils.format_datetime(
        frappe.utils.now_datetime()
    )

    for role_name in added_roles:
        # Get role owners ONLY from Role Allotment Details
        role_owners = get_role_owners_from_allotment(role_name)
        
        if not role_owners:
            # Skip if no role owners found in Role Allotment Details
            continue

        message = f"""
        <p>Dear Team,</p>

        <p>
        This is to inform you that the following role has been assigned in the system:
        </p>

        <table style="border-collapse: collapse;">
            <tr>
                <td style="padding: 4px 10px;"><b>Role</b></td>
                <td style="padding: 4px 10px;">{role_name}</td>
            </tr>
            <tr>
                <td style="padding: 4px 10px;"><b>Assigned To</b></td>
                <td style="padding: 4px 10px;">{doc.name}</td>
            </tr>
            <tr>
                <td style="padding: 4px 10px;"><b>Assigned By</b></td>
                <td style="padding: 4px 10px;">{assigned_by_name}</td>
            </tr>
            <tr>
                <td style="padding: 4px 10px;"><b>Assigned On</b></td>
                <td style="padding: 4px 10px;">{assigned_on}</td>
            </tr>
        </table>

        <p>
        If you have any questions regarding this role assignment, please contact the system administrator.
        </p>

        <p>
        Regards,<br>
        <b>ERPNext System</b>
        </p>
        """

        frappe.sendmail(
            recipients=role_owners,
            subject=f"Role Assignment Notification – {role_name}",
            message=message
        )


def get_role_owners_from_allotment(role_name):
    """
    Fetch role owners ONLY from Role Allotment Details child table
    Returns a list of email addresses
    """
    role_owners = []
    
    # Query Role Allotment Details for the specific role
    role_allotments = frappe.get_all(
        "Role Allotment Details",
        filters={"role": role_name},
        fields=["role_owner"]
    )
    
    for allotment in role_allotments:
        if allotment.role_owner:
            # Split by comma or newline and clean up email addresses
            emails = allotment.role_owner.replace('\n', ',').split(',')
            for email in emails:
                email = email.strip()
                if email and email not in role_owners:
                    role_owners.append(email)
    
    return role_owners
