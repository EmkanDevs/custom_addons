frappe.ui.form.on("Medical Insurance Request", {

    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Inform User"), function () {
                frappe.call({
                    method: "custom_addons.custom_addons.doctype.medical_insurance_request.medical_insurance_request.inform_medical_insurance",
                    args: {
                        docname: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: __("Sending email..."),
                    callback(r) {
                        if (!r.exc) {
                            frappe.msgprint(__("Email sent successfully."));
                        }
                    }
                });
            });
        }
    },

    sponsor(frm) {
        fetch_family_members(frm);
    },

    include_family(frm) {
        if (frm.doc.include_family) {
            fetch_family_members(frm);
        } else {
            frm.clear_table("family_members");
            frm.refresh_field("family_members");
        }
    }
});

function fetch_family_members(frm) {
    if (!frm.doc.sponsor || !frm.doc.include_family) return;

    frappe.call({
        method: "custom_addons.custom_addons.doctype.medical_insurance_request.medical_insurance_request.get_family_members",
        args: {
            employee: frm.doc.sponsor
        },
        callback(r) {
            frm.clear_table("family_members");
    
            (r.message || []).forEach(member => {
                let row = frm.add_child("family_members");
    
                row.member_name = member.member_name;
                row.relationship = member.relationship;
                row.id_number = member.id_no;
                row.member_effective_date = member.member_effective_date;
            });
    
            frm.refresh_field("family_members");
        }
    });
}