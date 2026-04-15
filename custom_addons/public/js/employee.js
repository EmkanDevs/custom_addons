frappe.ui.form.on('Employee', {
    refresh(frm) {
        if (!frm.is_new()) {

            const btn = frm.add_custom_button(
                __('Custody Dashboard →'),
                () => {
                    // ✅ Correct routing (prevents caching issue)
                    frappe.set_route('emloyee-custody-dash');
                    frappe.route_options = {
                        employee: frm.doc.name
                    };
                }
            );

            // 🎨 Dark Grey Styling (safe)
            $(btn).css({
                "background-color": "#343a40",
                "color": "#fff",
                "border": "none",
                "font-weight": "500"
            });

            // 🔥 Optional hover effect (safe)
            $(btn).hover(
                function() {
                    $(this).css("background-color", "#23272b");
                },
                function() {
                    $(this).css("background-color", "#343a40");
                }
            );
        }
    }
});

