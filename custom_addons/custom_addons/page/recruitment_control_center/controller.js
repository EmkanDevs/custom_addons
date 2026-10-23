// Recruitment Control Center - main controller / orchestration.
// The four main tabs are implemented in their own files and registered here:
//   - workspace.js        -> "Workspace" tab (Active Recruitment Pipeline)
//   - onboarding_tasks.js -> "Onboarding Tasks" tab
//   - analytics.js        -> "Analytics" tab
//   - reports.js          -> "Reports" tab
//   - shared.js           -> shared UI helpers
//
// Inlined into the page entry script (recruitment_control_center.js) at load time.

frappe.provide("frappe.rcc");

frappe.rcc.RecruitmentControlCenter = class RecruitmentControlCenter {
	constructor(page, wrapper) {
		this.page = page;
		this.wrapper = wrapper;

		this.filters = {
			company: "",
			department: "",
			designation: "",
			job_opening: "",
			status: "",
			from_date: "",
			to_date: "",
		};
		this.active_tab = "Workspace";

		this.tabs = {
			Workspace: new frappe.rcc.WorkspaceTab(this),
			"Onboarding Tasks": new frappe.rcc.OnboardingTasksTab(this),
			Analytics: new frappe.rcc.AnalyticsTab(this),
			Reports: new frappe.rcc.ReportsTab(this),
		};
	}

	init() {
		this.render_skeleton();
		this.bind_events();
		this.switch_tab("Workspace");
		this.load_filter_options();
		this.load_kpi_counts();
	}

	$content() {
		return $(this.wrapper).find("#rcc-tab-dynamic-content");
	}

	render_skeleton() {
		const html = `
			<div class="rcc-container">
				<!-- TOP HEADER BAR -->
				<div class="rcc-header-bar">
					<div style="display: flex; align-items: center;">
						<div class="rcc-header-left">
							<h1 class="rcc-page-title">Recruitment Control Center</h1>
							<div class="rcc-page-subtitle" id="rcc-company-subtitle">Emkan Holding Company · Authorized HR User</div>
						</div>

						<!-- NAVIGATION TABS -->
						<div class="rcc-tabs-container">
							<button class="rcc-tab-btn active" data-tab="Workspace">Workspace</button>
							<button class="rcc-tab-btn" data-tab="Onboarding Tasks">Onboarding Tasks</button>
							<button class="rcc-tab-btn" data-tab="Analytics">Analytics</button>
							<button class="rcc-tab-btn" data-tab="Reports">Reports</button>
						</div>
					</div>

					<!-- ACTIONS RIGHT -->
					<div class="rcc-header-right">
						<button class="rcc-icon-btn" id="rcc-btn-fullscreen" title="Toggle Fullscreen">
							<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
								<path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
							</svg>
						</button>
					</div>
				</div>

				<!-- FILTER BAR -->
				<div class="rcc-filter-card">
					<div class="rcc-filter-group">
						<label class="rcc-filter-label">COMPANY</label>
						<div class="rcc-select-wrapper">
							<select class="rcc-select" id="rcc-filter-company">
								<option value="">All Companies</option>
							</select>
						</div>
					</div>

					<div class="rcc-filter-group">
						<label class="rcc-filter-label">DEPARTMENT</label>
						<div class="rcc-select-wrapper">
							<select class="rcc-select" id="rcc-filter-department">
								<option value="">All Departments</option>
							</select>
						</div>
					</div>

					<div class="rcc-filter-group">
						<label class="rcc-filter-label">DESIGNATION</label>
						<div class="rcc-select-wrapper">
							<select class="rcc-select" id="rcc-filter-designation">
								<option value="">All Designations</option>
							</select>
						</div>
					</div>

					<div class="rcc-filter-group">
						<label class="rcc-filter-label">JOB OPENING</label>
						<div class="rcc-select-wrapper">
							<select class="rcc-select" id="rcc-filter-job-opening">
								<option value="">All Job Openings</option>
							</select>
						</div>
					</div>

					<div class="rcc-filter-group">
						<label class="rcc-filter-label">STATUS</label>
						<div class="rcc-select-wrapper">
							<select class="rcc-select" id="rcc-filter-status">
								<option value="">All Statuses</option>
								<option value="Open">Open</option>
								<option value="Pending">Pending</option>
								<option value="Closed">Closed</option>
								<option value="Filled">Filled</option>
								<option value="Cancelled">Cancelled</option>
							</select>
						</div>
					</div>

					<div class="rcc-filter-group date-group">
						<label class="rcc-filter-label">FROM DATE</label>
						<div class="rcc-date-wrapper">
							<input type="date" class="rcc-date-input" id="rcc-filter-from-date">
						</div>
					</div>

					<div class="rcc-filter-group date-group">
						<label class="rcc-filter-label">TO DATE</label>
						<div class="rcc-date-wrapper">
							<input type="date" class="rcc-date-input" id="rcc-filter-to-date">
						</div>
					</div>

					<button class="rcc-btn-reset" id="rcc-btn-reset">
						<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
							<path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"></path>
						</svg>
						<span>Reset</span>
					</button>
				</div>

				<!-- KPI SUMMARY CARDS (10 CARDS) -->
				<div class="rcc-kpi-grid">
					<div class="rcc-kpi-card rcc-card-blue" id="kpi-pending-requisitions" title="View Pending Requisitions">
						<div class="rcc-kpi-title">PENDING REQUISITIONS</div>
						<div class="rcc-kpi-value" id="val-pending-requisitions">-</div>
						<div class="rcc-kpi-subtitle">Awaiting approval</div>
					</div>

					<div class="rcc-kpi-card rcc-card-teal" id="kpi-planned-vacancies" title="View Staffing Plans">
						<div class="rcc-kpi-title">PLANNED VACANCIES</div>
						<div class="rcc-kpi-value" id="val-planned-vacancies">-</div>
						<div class="rcc-kpi-subtitle">Across active plans</div>
					</div>

					<div class="rcc-kpi-card rcc-card-amber" id="kpi-open-openings" title="View Open Job Openings">
						<div class="rcc-kpi-title">OPEN OPENINGS</div>
						<div class="rcc-kpi-value" id="val-open-openings">-</div>
						<div class="rcc-kpi-subtitle">Active vacancies</div>
					</div>

					<div class="rcc-kpi-card rcc-card-cyan" id="kpi-published" title="View Published Openings">
						<div class="rcc-kpi-title">PUBLISHED</div>
						<div class="rcc-kpi-value" id="val-published">-</div>
						<div class="rcc-kpi-subtitle">Visible on website</div>
					</div>

					<div class="rcc-kpi-card rcc-card-purple" id="kpi-applicants" title="View Job Applicants">
						<div class="rcc-kpi-title">APPLICANTS</div>
						<div class="rcc-kpi-value" id="val-applicants">-</div>
						<div class="rcc-kpi-subtitle">All applications</div>
					</div>

					<div class="rcc-kpi-card rcc-card-brown" id="kpi-interviews" title="View Scheduled Interviews">
						<div class="rcc-kpi-title">INTERVIEWS</div>
						<div class="rcc-kpi-value" id="val-interviews">-</div>
						<div class="rcc-kpi-subtitle">Scheduled / reviewed</div>
					</div>

					<div class="rcc-kpi-card rcc-card-yellow" id="kpi-feedback-pending" title="View Pending Feedbacks">
						<div class="rcc-kpi-title">FEEDBACK PENDING</div>
						<div class="rcc-kpi-value" id="val-feedback-pending">-</div>
						<div class="rcc-kpi-subtitle">Awaiting feedback</div>
					</div>

					<div class="rcc-kpi-card rcc-card-pink" id="kpi-awaiting-response" title="View Job Offers">
						<div class="rcc-kpi-title">AWAITING RESPONSE</div>
						<div class="rcc-kpi-value" id="val-awaiting-response">-</div>
						<div class="rcc-kpi-subtitle">Candidate response</div>
					</div>

					<div class="rcc-kpi-card rcc-card-indigo" id="kpi-onboarding-active" title="View Active Onboardings">
						<div class="rcc-kpi-title">ONBOARDING ACTIVE</div>
						<div class="rcc-kpi-value" id="val-onboarding-active">-</div>
						<div class="rcc-kpi-subtitle">Pending / in process</div>
					</div>

					<div class="rcc-kpi-card rcc-card-green" id="kpi-employees-hired" title="View Employees in Workspace">
						<div class="rcc-kpi-title">EMPLOYEES HIRED</div>
						<div class="rcc-kpi-value" id="val-employees-hired">-</div>
						<div class="rcc-kpi-subtitle">Converted applicants</div>
					</div>
				</div>

				<!-- MAIN TAB CONTENT CONTAINER -->
				<div class="rcc-content-body" id="rcc-content-body">
					<div class="rcc-workspace-view">
						<div id="rcc-tab-dynamic-content"></div>
					</div>
				</div>
			</div>
		`;

		this.page.main.html(html);
	}

	bind_events() {
		const self = this;

		// Tabs
		$(this.wrapper).on("click", ".rcc-tab-btn", function () {
			self.switch_tab($(this).data("tab"));
		});

		// Fullscreen toggle
		$(this.wrapper).on("click", "#rcc-btn-fullscreen", function () {
			self.toggle_fullscreen();
		});

		// Reset filters
		$(this.wrapper).on("click", "#rcc-btn-reset", function () {
			self.reset_filters();
		});

		// Filter changes
		$(this.wrapper).on(
			"change",
			"#rcc-filter-company, #rcc-filter-department, #rcc-filter-designation, #rcc-filter-job-opening, #rcc-filter-status, #rcc-filter-from-date, #rcc-filter-to-date",
			function () {
				self.update_filters_and_reload();
			}
		);

		// Open the matching inline Workspace section when a KPI card is clicked.
		const kpi_doctypes = {
			"kpi-pending-requisitions": "Job Requisition",
			"kpi-planned-vacancies": "Staffing Plan",
			"kpi-open-openings": "Job Opening",
			"kpi-published": "Job Opening",
			"kpi-applicants": "Job Applicant",
			"kpi-interviews": "Interview",
			"kpi-feedback-pending": "Interview Feedback",
			"kpi-awaiting-response": "Job Offer",
			"kpi-onboarding-active": "Employee Onboarding",
			"kpi-employees-hired": "Employee",
		};
		$(this.wrapper).on("click", ".rcc-kpi-card", function () {
			const doctype = kpi_doctypes[this.id];
			if (!doctype) return;
			if (self.active_tab !== "Workspace") self.switch_tab("Workspace");
			self.tabs.Workspace.select_doctype(doctype);
		});

		// Let each tab register its own delegated handlers (once).
		Object.values(this.tabs).forEach((tab) => tab.bind_events && tab.bind_events());
	}

	switch_tab(tab_name) {
		this.active_tab = tab_name;
		$(this.wrapper).find(".rcc-tab-btn").removeClass("active");
		$(this.wrapper).find(`.rcc-tab-btn[data-tab="${tab_name}"]`).addClass("active");

		if (tab_name === "Workspace") {
			$(this.wrapper).find(".rcc-filter-card, .rcc-kpi-grid").show();
			$(this.wrapper).find(".rcc-workspace-view").removeClass("rcc-transparent-view");
		} else if (tab_name === "Onboarding Tasks") {
			$(this.wrapper).find(".rcc-filter-card, .rcc-kpi-grid").hide();
			$(this.wrapper).find(".rcc-workspace-view").addClass("rcc-transparent-view");
		} else {
			$(this.wrapper).find(".rcc-filter-card, .rcc-kpi-grid").hide();
			$(this.wrapper).find(".rcc-workspace-view").addClass("rcc-transparent-view");
		}

		const tab = this.tabs[tab_name];
		if (tab) tab.render();
	}

	toggle_fullscreen() {
		if (!document.fullscreenElement) {
			document.documentElement.requestFullscreen().catch((err) => {
				console.warn("Fullscreen request error:", err);
			});
			$("body").addClass("rcc-immersive-mode");
		} else {
			if (document.exitFullscreen) {
				document.exitFullscreen();
			}
			$("body").removeClass("rcc-immersive-mode");
		}
	}

	load_filter_options() {
		frappe.call({
			method: "custom_addons.custom_addons.page.recruitment_control_center.recruitment_control_center.get_filter_options",
			callback: function (r) {
				if (r && r.message) {
					const data = r.message;

					if (data.default_company) {
						$("#rcc-company-subtitle").text(`${data.default_company} · Authorized HR User`);
					}

					const company_select = $("#rcc-filter-company");
					company_select.empty().append('<option value="">All Companies</option>');
					(data.companies || []).forEach((c) => {
						company_select.append(
							`<option value="${frappe.utils.escape_html(c)}">${frappe.utils.escape_html(c)}</option>`
						);
					});

					const dept_select = $("#rcc-filter-department");
					dept_select.empty().append('<option value="">All Departments</option>');
					(data.departments || []).forEach((d) => {
						dept_select.append(
							`<option value="${frappe.utils.escape_html(d)}">${frappe.utils.escape_html(d)}</option>`
						);
					});

					const desig_select = $("#rcc-filter-designation");
					desig_select.empty().append('<option value="">All Designations</option>');
					(data.designations || []).forEach((d) => {
						desig_select.append(
							`<option value="${frappe.utils.escape_html(d)}">${frappe.utils.escape_html(d)}</option>`
						);
					});

					const jo_select = $("#rcc-filter-job-opening");
					jo_select.empty().append('<option value="">All Job Openings</option>');
					(data.job_openings || []).forEach((jo) => {
						jo_select.append(
							`<option value="${frappe.utils.escape_html(jo.name)}">${frappe.utils.escape_html(jo.title)}</option>`
						);
					});
				}
			},
		});
	}

	update_filters_and_reload() {
		this.filters.company = $("#rcc-filter-company").val() || "";
		this.filters.department = $("#rcc-filter-department").val() || "";
		this.filters.designation = $("#rcc-filter-designation").val() || "";
		this.filters.job_opening = $("#rcc-filter-job-opening").val() || "";
		this.filters.status = $("#rcc-filter-status").val() || "";
		this.filters.from_date = $("#rcc-filter-from-date").val() || "";
		this.filters.to_date = $("#rcc-filter-to-date").val() || "";

		this.load_kpi_counts();

		// Notify Workspace tab so doctype counts and record list reflect the new filters
		if (this.tabs && this.tabs.Workspace && this.tabs.Workspace.on_global_filter_change) {
			this.tabs.Workspace.on_global_filter_change();
		}
	}

	reset_filters() {
		$("#rcc-filter-company").val("");
		$("#rcc-filter-department").val("");
		$("#rcc-filter-designation").val("");
		$("#rcc-filter-job-opening").val("");
		$("#rcc-filter-status").val("");
		$("#rcc-filter-from-date").val("");
		$("#rcc-filter-to-date").val("");

		this.filters = {
			company: "",
			department: "",
			designation: "",
			job_opening: "",
			status: "",
			from_date: "",
			to_date: "",
		};

		this.load_kpi_counts();

		// Notify Workspace tab so doctype counts and record list reset
		if (this.tabs && this.tabs.Workspace && this.tabs.Workspace.on_global_filter_change) {
			this.tabs.Workspace.on_global_filter_change();
		}
	}

	load_kpi_counts() {
		frappe.call({
			method: "custom_addons.custom_addons.page.recruitment_control_center.recruitment_control_center.get_kpi_counts",
			args: this.filters,
			callback: function (r) {
				if (r && r.message) {
					const counts = r.message;
					$("#val-pending-requisitions").text(counts.pending_requisitions ?? 0);
					$("#val-planned-vacancies").text(counts.planned_vacancies ?? 0);
					$("#val-open-openings").text(counts.open_openings ?? 0);
					$("#val-published").text(counts.published_openings ?? 0);
					$("#val-applicants").text(counts.applicants ?? 0);
					$("#val-interviews").text(counts.interviews ?? 0);
					$("#val-feedback-pending").text(counts.feedback_pending ?? 0);
					$("#val-awaiting-response").text(counts.awaiting_response ?? 0);
					$("#val-onboarding-active").text(counts.onboarding_active ?? 0);
					$("#val-employees-hired").text(counts.employees_hired ?? 0);
				}
			},
		});
	}
};
