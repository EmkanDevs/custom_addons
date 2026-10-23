// Reports Tab: Recruitment Reports Directory.
// Inlined into the page entry script (recruitment_control_center.js) at load time.

frappe.provide("frappe.rcc");

frappe.rcc.REPORTS_LIST = [
	{
		title: "Recruitment Analytics",
		description: "Staffing Plan, Job Opening, Applicant and Offer tree",
		icon: "trending-up",
		report_name: "Recruitment Analytics",
		route: ["query-report", "Recruitment Analytics"],
	},
	{
		title: "Job Requisition Time to Fill",
		description: "Request approval and filling duration",
		icon: "timer",
		report_name: "Job Requisition Time to Fill",
		route: ["query-report", "Job Requisition Time to Fill"],
	},
	{
		title: "Staffing Plan Variance",
		description: "Planned positions, current count and vacancies",
		icon: "users-round",
		report_name: "Staffing Plan Variance",
		route: ["query-report", "Staffing Plan Variance"],
	},
	{
		title: "Job Opening Status",
		description: "Open, closed, published and closing dates",
		icon: "briefcase-business",
		report_name: "Job Opening Status",
		route: ["query-report", "Job Opening Status"],
	},
	{
		title: "Interview and Feedback",
		description: "Schedules, ratings and pending feedback",
		icon: "messages-square",
		report_name: "Interview and Feedback",
		route: ["query-report", "Interview and Feedback"],
	},
	{
		title: "Offer and Onboarding",
		description: "Offer response, joining and activity progress",
		icon: "sliders-horizontal",
		report_name: "Offer and Onboarding",
		route: ["query-report", "Offer and Onboarding"],
	},
	{
		title: "Onboarding Task Progress",
		description: "Completed, ongoing and pending tasks by employee",
		icon: "bar-chart-2",
		report_name: "Onboarding Task Progress",
		route: ["query-report", "Onboarding Task Progress"],
	},
	{
		title: "Overdue Onboarding Tasks",
		description: "Past-due tasks, assignees and expected completion dates",
		icon: "triangle-alert",
		report_name: "Overdue Onboarding Tasks",
		route: ["query-report", "Overdue Onboarding Tasks"],
	},
];

frappe.rcc.ReportsTab = class ReportsTab {
	constructor(controller) {
		this.ctrl = controller;
		this.reports = frappe.rcc.REPORTS_LIST;
	}

	get $content() {
		return this.ctrl.$content();
	}

	get wrapper() {
		return this.ctrl.wrapper;
	}

	bind_events() {
		const self = this;
		const wrapper = this.wrapper;

		$(wrapper).on("click", ".rcc-report-card, .rcc-report-btn", function (e) {
			e.stopPropagation();
			const card = $(this).closest(".rcc-report-card");
			const report_name = card.attr("data-report");
			if (report_name) {
				frappe.set_route("query-report", report_name);
			}
		});
	}

	render() {
		const html = `
			<div class="rcc-reports-view">
				<h2 class="rcc-reports-title">Recruitment Reports</h2>
				<div class="rcc-reports-grid">
					${this.reports
						.map((r) => {
							return `
								<div class="rcc-report-card" data-report="${frappe.utils.escape_html(r.report_name)}" title="Open ${frappe.utils.escape_html(r.title)}">
									<div class="rcc-report-left">
										<div class="rcc-report-icon">
											${frappe.rcc.icon(r.icon, 18)}
										</div>
										<div class="rcc-report-info">
											<div class="rcc-report-title">${frappe.utils.escape_html(r.title)}</div>
											<div class="rcc-report-desc" title="${frappe.utils.escape_html(r.description)}">${frappe.utils.escape_html(r.description)}</div>
										</div>
									</div>
									<button class="rcc-report-btn" type="button">Open Report</button>
								</div>
							`;
						})
						.join("")}
				</div>
			</div>
		`;

		this.$content.html(html);
	}
};
