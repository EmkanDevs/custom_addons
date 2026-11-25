frappe.query_reports["Purchaser Assigned Material Requests"] = {

    onload: function(report) {

		report.page.add_inner_button("Open PO Detail Page", function() {

			let filters = report.get_values();

			let route_options = {
				// project: filters.project || "",
				// material_request: filters.material_request || "",
				// from_date: filters.from_date || "",
				// to_date: filters.to_date || "",
				assigned_to: filters.assigned_to || ""
			};

			let url = "/app/po-details-report?" + $.param(route_options);

			window.open(url, "_blank");

		}).addClass("btn-primary");

	},
    
    filters: [
        {
            fieldname: "assigned_to",
            label: __("Assigned To"),
            fieldtype: "Link",
            options: "User",
            default: frappe.session.user
        },


		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project"
		},
		
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date"
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date"
        },
        {
            fieldname: "material_request",
            label: __("Material Request"),
            fieldtype: "Link",
            options: "Material Request"
        },
        {
            fieldname: "purpose",
            label: __("Purpose"),
            fieldtype: "Select",
            options: "Purchase\nMaterial Transfer\nManufacture\nCustomer Provided",
            default: "Purchase"
        },

        {
            fieldname: "due_po",
            label: __("Due PO"),
            fieldtype: "Check",
            default: 1
        },
    ]
};
