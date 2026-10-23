try {
	delete localStorage["_page:recruitment-control-center"];
} catch (e) {}

// Recruitment Control Center - page entry point.
//
// All tab implementations live in this same folder and are inlined at load time
// through Frappe's native page include directive (resolved by Page.load_assets on
// the server). No bundling / build step is required.

{% include "custom_addons/custom_addons/page/recruitment_control_center/shared.js" %}
{% include "custom_addons/custom_addons/page/recruitment_control_center/icons.js" %}
{% include "custom_addons/custom_addons/page/recruitment_control_center/workspace.js" %}
{% include "custom_addons/custom_addons/page/recruitment_control_center/onboarding_tasks.js" %}
{% include "custom_addons/custom_addons/page/recruitment_control_center/analytics.js" %}
{% include "custom_addons/custom_addons/page/recruitment_control_center/reports.js" %}
{% include "custom_addons/custom_addons/page/recruitment_control_center/controller.js" %}

frappe.pages['recruitment-control-center'].on_page_load = function (wrapper) {
	try {
		delete localStorage["_page:recruitment-control-center"];
	} catch (e) {}

	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Recruitment Control Center',
		single_column: true
	});

	// Hide default standard Frappe page-head to achieve full screen UI custom header
	$(wrapper).find('.page-head').hide();

	const rcc = new frappe.rcc.RecruitmentControlCenter(page, wrapper);
	rcc.init();
};
