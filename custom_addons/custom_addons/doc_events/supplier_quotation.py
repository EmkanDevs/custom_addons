import frappe

def on_cancel(self, method):
    # if connected RFQ's bid tabulation discussion is created and docstatus is 1
    for row in self.items:
        if row.request_for_quotation:
            if frappe.db.exists("Bid Tabulation Discussion",{"request_for_quotation":row.request_for_quotation}):
                data = frappe.get_doc("Bid Tabulation Discussion",{"request_for_quotation":row.request_for_quotation})
                if data and data.docstatus == 1:
                    frappe.throw(f"You cannot cancel this Supplier Quotation because it is connect to Bid Tabulation Discussion {data.name}")