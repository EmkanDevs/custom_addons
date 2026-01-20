import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {"label": "Asset ID", "fieldname": "name", "fieldtype": "Link", "options": "IT Asset Management", "width": 150},
        {"label": "Parent Row", "fieldname": "parent_row", "fieldtype": "Data", "width": 100},
        {"label": "Date of Acquisition", "fieldname": "date_of_purchase_acquisition", "fieldtype": "Date", "width": 120},
        {"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 120},
        {"label": "Status", "fieldname": "current_status", "fieldtype": "Data", "width": 100},
        {"label": "RAM Size", "fieldname": "ram_size", "fieldtype": "Data", "width": 100},
        {"label": "Serial Number", "fieldname": "serial_number", "fieldtype": "Data", "width": 150},
        {"label": "Assigned ID", "fieldname": "assigned_id", "fieldtype": "Data", "width": 100},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
        {"label": "Employee Department", "fieldname": "employee_department", "fieldtype": "Data", "width": 130},
        {"label": "Designation", "fieldname": "designation", "fieldtype": "Data", "width": 120},
        {"label": "Child Project", "fieldname": "child_project", "fieldtype": "Link", "options": "Project", "width": 120},
        {"label": "From Date", "fieldname": "from_date", "fieldtype": "Date", "width": 100},
        {"label": "To Date", "fieldname": "to_date", "fieldtype": "Date", "width": 100},
    ]


def get_data(filters):
    result = []

    # Get all IT Asset Management entries
    assets = frappe.get_all("IT Asset Management",
        filters=filters,
        fields=[
            "name", "date_of_purchase_acquisition", "project", "current_status",
            "ram_size", "serial_number"
        ]
    )

    for asset in assets:
        # Fetch child table rows (Asset Assignment)
        child_rows = frappe.get_all("IT Asset Assigned User2",
            filters={"parent": asset.name, "parenttype": "IT Asset Management"},
            fields=["assigned_user", "name1 as employee_name", "department as employee_department", "designation", "project as child_project", "from_date", "to_date"]
        )

        if not child_rows:
            result.append({
                **asset,
                "parent_row": "Yes",  # Indicator for parent row
                "assigned_id": "",
                "employee_name": "",
                "employee_department": "",
                "designation": "",
                "child_project": "",
                "from_date": "",
                "to_date": ""
            })
        else:
            # Add parent row
            result.append({
                **asset,
                "parent_row": "Yes",
                "assigned_id": "",
                "employee_name": "",
                "employee_department": "",
                "designation": "",
                "child_project": "",
                "from_date": "",
                "to_date": ""
            })

            # Add each child row with indent style
            for child in child_rows:
                result.append({
                    "name": asset["name"],
                    "date_of_purchase_acquisition": "",
                    "project": "",
                    "current_status": "",
                    "ram_size": "",
                    "serial_number": "",
                    "parent_row": "→",  # Visual indent
                    **child
                })

    return result
