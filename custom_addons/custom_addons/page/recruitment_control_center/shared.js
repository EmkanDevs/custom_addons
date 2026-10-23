// Recruitment Control Center - shared UI helpers.
// Inlined into the page entry script (recruitment_control_center.js) at load time.

frappe.provide("frappe.rcc");

frappe.rcc.placeholder = function (message, icon) {
	return `<div class="rcc-placeholder">
		<div class="rcc-placeholder-icon">${icon || "📋"}</div>
		<div class="rcc-placeholder-text">${frappe.utils.escape_html(__(message))}</div>
	</div>`;
};
