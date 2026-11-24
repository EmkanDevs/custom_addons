// List view: Workflow Status is the one status column, so the standard Status indicator is dropped.
const POAL_STATUS_COLOUR = {
	Draft: "gray",
	Approved: "green",
	Rejected: "red",
	Cancelled: "red",
};
frappe.listview_settings["PO Amendment Log"] = {
	onload(listview) {
		// Frappe has no setting to hide the Status column of a submittable doctype, so filter it out.
		const setup_columns = listview.setup_columns.bind(listview);
		listview.setup_columns = () => {
			setup_columns();
			listview.columns = listview.columns.filter((col) => col.type !== "Status");
		};
		listview.setup_columns();
		listview.refresh(true);
	},

	formatters: {
		workflow_status(value) {
			if (!value) return "";
			const colour = POAL_STATUS_COLOUR[value] || "orange"; // every Pending state is orange
			const label = frappe.utils.escape_html(__(value));
			return `<span class="indicator-pill ${colour} ellipsis"><span class="ellipsis">${label}</span></span>`;
		},
	},
};
