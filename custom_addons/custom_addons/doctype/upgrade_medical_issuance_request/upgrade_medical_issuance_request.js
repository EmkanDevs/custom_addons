// Copyright (c) 2026, Administrator and contributors
// For license information, please see license.txt

frappe.ui.form.on("Upgrade Medical Issuance request", {

    refresh(frm) {
        // Set start date if empty
        if (!frm.doc.starting_from) {
            frm.set_value("starting_from", frappe.datetime.get_today());
        }

        // Set ending date
        set_dates(frm);
    },

    payment_type(frm) {
        calculate_each_payment(frm);
        set_dates(frm);
    },

    amount(frm) {
        calculate_each_payment(frm);
    },

    starting_from(frm) {
        set_dates(frm);
    }
});

function calculate_each_payment(frm) {
    let amount = frm.doc.amount || 0;
    let type = frm.doc.payment_type;

    if (!amount || !type) {
        frm.set_value("each_payment", 0);
        return;
    }

    let divisor = 1;

    if (type === "Monthly") divisor = 12;
    else if (type === "Quarterly") divisor = 4;
    else if (type === "Half Year") divisor = 2;
    else if (type === "Yearly") divisor = 1;

    let each_payment = flt(amount / divisor, 2);
    frm.set_value("each_payment", each_payment);
}

function set_dates(frm) {
    let start_date = frm.doc.starting_from;
    let type = frm.doc.payment_type;

    // Auto set start date if empty
    if (!start_date) {
        start_date = frappe.datetime.get_today();
        frm.set_value("starting_from", start_date);
    }

    if (!type) return;

    // All plans = 1 year duration
    let months_to_add = 12;

    let end_date = frappe.datetime.add_months(start_date, months_to_add);
    end_date = frappe.datetime.add_days(end_date, -1); // inclusive

    frm.set_value("ending_at", end_date);
}