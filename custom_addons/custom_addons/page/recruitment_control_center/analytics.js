// Analytics Tab: Recruitment Analytics Dashboard.
// Inlined into the page entry script (recruitment_control_center.js) at load time.

frappe.provide("frappe.rcc");

frappe.rcc.AnalyticsTab = class AnalyticsTab {
	constructor(controller) {
		this.ctrl = controller;
		this.data = null;
		this.is_loading = false;
	}

	get $content() {
		return this.ctrl.$content();
	}

	get wrapper() {
		return this.ctrl.wrapper;
	}

	open_in_workspace(doctype, filters = null, label = null) {
		if (!doctype) return;
		if (!frappe.model.can_read(doctype)) {
			frappe.show_alert({
				message: __("You do not have permission to view {0}.", [__(doctype)]),
				indicator: "red",
			});
			return;
		}

		const ctrl = this.ctrl;
		if (ctrl && ctrl.switch_tab) {
			const ws = ctrl.tabs && ctrl.tabs["Workspace"];
			const has_filters = filters && typeof filters === "object" && Object.keys(filters).length > 0;
			const connection_filter = {
				filters: has_filters ? filters : {},
				label: label || (has_filters ? Object.entries(filters).map(([k, v]) => `${frappe.model.unscrub(k)}: ${v}`).join(", ") : ""),
				auto_select: true,
			};

			if (ws) {
				ws.active_doctype = doctype;
				ws.connection_filter = connection_filter;
			}

			ctrl.switch_tab("Workspace");

			if (ws && ws.select_doctype) {
				ws.select_doctype(doctype, connection_filter);
			}
		}
	}

	bind_events() {
		const self = this;
		const wrapper = this.wrapper;

		// KPI Card Routing (opens Workspace tab with corresponding doctype form)
		$(wrapper).on("click", "#akpi-open-requisitions", function () {
			self.open_in_workspace("Job Requisition");
		});

		$(wrapper).on("click", "#akpi-open-job-openings", function () {
			self.open_in_workspace("Job Opening", { status: "Open" }, __("Status: Open"));
		});

		$(wrapper).on("click", "#akpi-applicants", function () {
			self.open_in_workspace("Job Applicant");
		});

		$(wrapper).on("click", "#akpi-interviews-pending", function () {
			self.open_in_workspace("Interview");
		});

		$(wrapper).on("click", "#akpi-offers-awaiting", function () {
			self.open_in_workspace("Job Offer", { status: "Awaiting Response" }, __("Status: Awaiting Response"));
		});

		$(wrapper).on("click", "#akpi-onboarding-overdue", function () {
			self.open_in_workspace("Employee Onboarding");
		});

		// Needs Attention Item Click (opens Workspace tab with filtered doctype form)
		$(wrapper).on("click", ".rcc-attention-item", function () {
			const dt = $(this).attr("data-route-doctype");
			const raw_filters = $(this).attr("data-route-filters");
			let filters = {};
			try {
				if (raw_filters) filters = JSON.parse(raw_filters);
			} catch (e) {
				console.error("Filter parse error:", e);
			}
			if (dt) {
				self.open_in_workspace(dt, filters);
			}
		});
	}

	render() {
		if (this.data) {
			this.render_dashboard(this.data);
		} else {
			this.render_skeleton();
		}
		this.load_data();
	}

	render_skeleton() {
		this.$content.html(`
			<div class="rcc-analytics-container">
				<div class="rcc-analytics-head">
					<div>
						<h2 class="rcc-analytics-title">Recruitment Analytics</h2>
						<div class="rcc-analytics-subtitle">Operational hiring activity and items that need HR attention.</div>
					</div>
					<div class="rcc-analytics-date">
						${frappe.rcc.icon("calendar", 14)}
						<span>Loading...</span>
					</div>
				</div>
				<div class="rcc-loading" style="background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; padding: 60px 20px;">
					Loading analytics dashboard...
				</div>
			</div>
		`);
	}

	load_data() {
		if (this.is_loading) return;
		this.is_loading = true;

		const self = this;
		frappe.call({
			method: "custom_addons.custom_addons.page.recruitment_control_center.recruitment_control_center.get_analytics_data",
			callback: function (r) {
				self.is_loading = false;
				if (r && r.message) {
					self.data = r.message;
					if (self.ctrl.active_tab === "Analytics") {
						self.render_dashboard(self.data);
					}
				}
			},
			error: function () {
				self.is_loading = false;
			},
		});
	}

	render_dashboard(data) {
		const kpis = data.kpis || {};
		const funnel = data.hiring_funnel || [];
		const demand = data.hiring_demand || [];
		const app_statuses = data.applicants_by_status || [];
		const offer_statuses = data.offer_status || [];
		const attention = data.needs_attention || [];

		// Max values for horizontal bar widths
		const max_funnel = Math.max(...funnel.map((d) => flt(d.count)), 1);
		const max_demand = Math.max(...demand.map((d) => flt(d.count)), 1);
		const max_app = Math.max(...app_statuses.map((d) => flt(d.count)), 1);
		const max_offer = Math.max(...offer_statuses.map((d) => flt(d.count)), 1);

		const html = `
			<div class="rcc-analytics-container">
				<!-- HEADER ROW -->
				<div class="rcc-analytics-head">
					<div>
						<h2 class="rcc-analytics-title">Recruitment Analytics</h2>
						<div class="rcc-analytics-subtitle">Operational hiring activity and items that need HR attention.</div>
					</div>
					<div class="rcc-analytics-date">
						${frappe.rcc.icon("calendar", 14)}
						<span>As of ${frappe.utils.escape_html(data.as_of_date || "")}</span>
					</div>
				</div>

				<!-- 6 TOP KPI CARDS -->
				<div class="rcc-analytics-kpis">
					<!-- 1. Open Requisitions -->
					<div class="rcc-akpi-card rcc-akpi-blue" id="akpi-open-requisitions" title="View Requisitions">
						<div class="rcc-akpi-label">OPEN REQUISITIONS</div>
						<div class="rcc-akpi-val">${kpis.open_requisitions ?? 0}</div>
						<div class="rcc-akpi-sub">${kpis.pending_requisitions ?? 0} pending approval</div>
					</div>

					<!-- 2. Open Job Openings -->
					<div class="rcc-akpi-card rcc-akpi-teal" id="akpi-open-job-openings" title="View Open Job Openings">
						<div class="rcc-akpi-label">OPEN JOB OPENINGS</div>
						<div class="rcc-akpi-val">${kpis.open_job_openings ?? 0}</div>
						<div class="rcc-akpi-sub">${kpis.published_openings ?? 0} published</div>
					</div>

					<!-- 3. Applicants -->
					<div class="rcc-akpi-card rcc-akpi-purple" id="akpi-applicants" title="View Applicants">
						<div class="rcc-akpi-label">APPLICANTS</div>
						<div class="rcc-akpi-val">${kpis.applicants ?? 0}</div>
						<div class="rcc-akpi-sub">${kpis.accepted_applicants ?? 0} accepted</div>
					</div>

					<!-- 4. Interviews Pending -->
					<div class="rcc-akpi-card rcc-akpi-amber" id="akpi-interviews-pending" title="View Interviews">
						<div class="rcc-akpi-label">INTERVIEWS PENDING</div>
						<div class="rcc-akpi-val">${kpis.interviews_pending ?? 0}</div>
						<div class="rcc-akpi-sub">Require follow-up</div>
					</div>

					<!-- 5. Offers Awaiting -->
					<div class="rcc-akpi-card rcc-akpi-pink" id="akpi-offers-awaiting" title="View Job Offers">
						<div class="rcc-akpi-label">OFFERS AWAITING</div>
						<div class="rcc-akpi-val">${kpis.offers_awaiting ?? 0}</div>
						<div class="rcc-akpi-sub">Candidate response</div>
					</div>

					<!-- 6. Onboarding Overdue -->
					<div class="rcc-akpi-card rcc-akpi-red" id="akpi-onboarding-overdue" title="View Onboardings">
						<div class="rcc-akpi-label">ONBOARDING OVERDUE</div>
						<div class="rcc-akpi-val">${kpis.onboarding_overdue ?? 0}</div>
						<div class="rcc-akpi-sub">${kpis.active_onboarding ?? 0} active onboarding</div>
					</div>
				</div>

				<!-- 2-COLUMN MAIN DASHBOARD -->
				<div class="rcc-analytics-grid">
					<!-- LEFT COLUMN -->
					<div class="rcc-analytics-col">
						<!-- Hiring Funnel -->
						<div class="rcc-analytics-card">
							<h3 class="rcc-acard-title">Hiring Funnel</h3>
							<div class="rcc-hbar-list">
								${funnel
									.map((row) => {
										const pct = ((flt(row.count) / max_funnel) * 100).toFixed(1);
										return `
											<div class="rcc-hbar-row">
												<span class="rcc-hbar-label" title="${frappe.utils.escape_html(row.stage)}">${frappe.utils.escape_html(row.stage)}</span>
												<div class="rcc-hbar-track">
													<div class="rcc-hbar-fill rcc-fill-blue" style="width: ${pct}%;"></div>
												</div>
												<span class="rcc-hbar-val">${row.count}</span>
											</div>
										`;
									})
									.join("")}
							</div>
						</div>

						<!-- Hiring Demand by Department -->
						<div class="rcc-analytics-card">
							<h3 class="rcc-acard-title">Hiring Demand by Department</h3>
							<div class="rcc-hbar-list">
								${demand
									.map((row) => {
										const pct = ((flt(row.count) / max_demand) * 100).toFixed(1);
										return `
											<div class="rcc-hbar-row">
												<span class="rcc-hbar-label" title="${frappe.utils.escape_html(row.department)}">${frappe.utils.escape_html(row.department)}</span>
												<div class="rcc-hbar-track">
													<div class="rcc-hbar-fill rcc-fill-teal" style="width: ${pct}%;"></div>
												</div>
												<span class="rcc-hbar-val">${row.count}</span>
											</div>
										`;
									})
									.join("")}
							</div>
						</div>
					</div>

					<!-- RIGHT COLUMN -->
					<div class="rcc-analytics-col">
						<!-- Top Subgrid: Applicants by Status & Offer Status -->
						<div class="rcc-analytics-split">
							<!-- Applicants by Status -->
							<div class="rcc-analytics-card">
								<h3 class="rcc-acard-title">Applicants by Status</h3>
								<div class="rcc-hbar-list">
									${app_statuses
										.map((row) => {
											const pct = row.count > 0 ? ((flt(row.count) / max_app) * 100).toFixed(1) : 0;
											return `
												<div class="rcc-hbar-row">
													<span class="rcc-hbar-label" style="min-width: 65px;" title="${frappe.utils.escape_html(row.status)}">${frappe.utils.escape_html(row.status)}</span>
													<div class="rcc-hbar-track" style="margin: 0 12px;">
														<div class="rcc-hbar-fill rcc-fill-purple" style="width: ${pct}%;"></div>
													</div>
													<span class="rcc-hbar-val">${row.count}</span>
												</div>
											`;
										})
										.join("")}
								</div>
							</div>

							<!-- Offer Status -->
							<div class="rcc-analytics-card">
								<h3 class="rcc-acard-title">Offer Status</h3>
								<div class="rcc-hbar-list">
									${offer_statuses
										.map((row) => {
											const pct = row.count > 0 ? ((flt(row.count) / max_offer) * 100).toFixed(1) : 0;
											return `
												<div class="rcc-hbar-row">
													<span class="rcc-hbar-label" style="min-width: 105px;" title="${frappe.utils.escape_html(row.status)}">${frappe.utils.escape_html(row.status)}</span>
													<div class="rcc-hbar-track" style="margin: 0 12px;">
														<div class="rcc-hbar-fill rcc-fill-wine" style="width: ${pct}%;"></div>
													</div>
													<span class="rcc-hbar-val">${row.count}</span>
												</div>
											`;
										})
										.join("")}
								</div>
							</div>
						</div>

						<!-- Needs Attention Section -->
						<div class="rcc-analytics-card">
							<h3 class="rcc-acard-title">Needs Attention</h3>
							<div class="rcc-attention-list">
								${attention
									.map((item) => {
										const filter_json = frappe.utils.escape_html(
											JSON.stringify(item.route_filters || {})
										);
										return `
											<div class="rcc-attention-item"
												data-route-doctype="${frappe.utils.escape_html(item.route_doctype || "")}"
												data-route-filters="${filter_json}"
												title="Click to view records">
												<div class="rcc-attention-left">
													<div class="rcc-attention-icon" style="background-color: ${item.bg}; color: ${item.color};">
														${frappe.rcc.icon(item.icon, 18)}
													</div>
													<div class="rcc-attention-info">
														<div class="rcc-attention-title">${frappe.utils.escape_html(item.title)}</div>
														<div class="rcc-attention-desc">${frappe.utils.escape_html(item.subtitle)}</div>
													</div>
												</div>
												<div class="rcc-attention-badge" style="color: ${item.badge_color};">
													${frappe.utils.escape_html(item.badge_text)}
												</div>
											</div>
										`;
									})
									.join("")}
							</div>
						</div>
					</div>
				</div>
			</div>
		`;

		this.$content.html(html);
	}
};
