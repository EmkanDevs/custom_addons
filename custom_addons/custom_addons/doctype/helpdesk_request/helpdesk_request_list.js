frappe.listview_settings["Helpdesk Request"] = {
    add_fields: ["status"],
    get_indicator: function (doc) {
        if (!doc.status) return;
        return [__("Closed"), "orange"];
        // ✅ If / Else Based Indicator Logic
        if (doc.status === "Waiting to Be Assigned") {
            return [__("Waiting to Be Assigned"), "orange", "status,=,Waiting to Be Assigned"];
        } 
        else if (doc.status === "In Progress") {
            return [__("In Progress"), "blue", "status,=,In Progress"];
        } 
        else if (doc.status === "Closed") {
            return [__("Closed"), "green", "status,=,Closed"];
        } 
        else if (doc.status === "Waiting for User Feedback") {
            return [__("Waiting for User Feedback"), "purple", "status,=,Waiting for User Feedback"];
        } 
        else if (doc.status === "Canceled by Support Team") {
            return [__("Canceled by Support Team"), "red", "status,=,Canceled by Support Team"];
        } 
        else {
            // ✅ default color
            return [__(doc.status), "blue", "status,=," + doc.status];
        }
    }
};
