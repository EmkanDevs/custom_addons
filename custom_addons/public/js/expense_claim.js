frappe.ui.form.on("Expense Claim", {
	setup: function (frm) {

		frm.set_query("custom_account_head", "expenses", function () {
			return {
				filters: [
					["company", "=", frm.doc.company],
					[
						"account_type",
						"in",
						["Tax", "Chargeable", "Income Account", "Expenses Included In Valuation"],
					],
				],
			};
		});

	},
	refresh:function(frm){
		frm.set_query("project", "expenses", function () {
			return {
				filters: [
					["name", "=", frm.doc.project],
					
				],
			};
		});
	},
	project: function (frm) {
        if (frm.doc.project) {
            (frm.doc.expenses || []).forEach(row => {
                frappe.model.set_value(row.doctype, row.name, "project", frm.doc.project);
            });
        }
    }
});
