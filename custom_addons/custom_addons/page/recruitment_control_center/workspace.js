// Workspace tab: "Active Recruitment Pipeline" (15% / 25% / 60% columns).
//
//   15%  -> list of recruitment DocTypes
//   25%  -> records of the selected DocType
//   60%  -> form view of the selected record (currently implemented for Job Requisition)
//
// Inlined into the page entry script (recruitment_control_center.js) at load time.

frappe.provide("frappe.rcc");

// Pipeline sidebar configuration (order, group, title/description, icon + pastel colors).
// `icon` refers to a key in frappe.rcc.ICONS (see icons.js).
// `group` renders a section heading in the sidebar; consecutive entries sharing a
// group label are shown together (first two -> Planning, rest -> Hiring Pipeline).
frappe.rcc.PIPELINE_DOCTYPES = [
	{
		doctype: "Job Requisition",
		group: "Planning",
		title_field: "designation",
		description: "Request and approval",
		icon: "clipboard-list",
		color: "#2870FF",
		bg: "#E8F0FF",
	},
	{
		doctype: "Staffing Plan",
		group: "Planning",
		title_field: "name",
		description: "Headcount and budget",
		icon: "users-round",
		color: "#008F83",
		bg: "#E5F7F4",
	},
	{
		doctype: "Job Opening",
		group: "Hiring Pipeline",
		title_field: "job_title",
		description: "Vacancies and publishing",
		icon: "briefcase-business",
		color: "#D97706",
		bg: "#FFF0DF",
	},
	{
		doctype: "Job Applicant",
		group: "Hiring Pipeline",
		title_field: "applicant_name",
		description: "Candidate applications",
		icon: "user-round-search",
		color: "#8050E8",
		bg: "#F1EAFF",
	},
	{
		doctype: "Interview",
		group: "Hiring Pipeline",
		title_field: "job_applicant",
		description: "Rounds and schedules",
		icon: "messages-square",
		color: "#EA580C",
		bg: "#FFF0E4",
	},
	{
		doctype: "Interview Feedback",
		group: "Hiring Pipeline",
		title_field: "interviewer",
		description: "Skills and ratings",
		icon: "star",
		color: "#B77900",
		bg: "#FFF6D9",
	},
	{
		doctype: "Job Offer",
		group: "Hiring Pipeline",
		title_field: "applicant_name",
		description: "Terms and response",
		icon: "file-pen-line",
		color: "#E83E8C",
		bg: "#FCEAF1",
	},
	{
		doctype: "Appointment Letter",
		group: "Hiring Pipeline",
		title_field: "applicant_name",
		description: "Joining letter",
		icon: "mail-check",
		color: "#9333EA",
		bg: "#F2E8FF",
	},
	{
		doctype: "Employee Onboarding",
		group: "Hiring Pipeline",
		title_field: "employee_name",
		description: "Activities and tasks",
		icon: "list-checks",
		color: "#5B5CE2",
		bg: "#EDEFFF",
	},
	{
		doctype: "Employee",
		group: "Hiring Pipeline",
		title_field: "employee_name",
		description: "Converted hires",
		icon: "badge-check",
		color: "#168447",
		bg: "#E5F7EC",
	},
];

// DocTypes that already have a rendered form view in the 60% panel.
frappe.rcc.FORM_VIEW_DOCTYPES = [
	"Job Requisition",
	"Staffing Plan",
	"Job Opening",
	"Job Applicant",
	"Interview",
	"Interview Feedback",
	"Job Offer",
	"Appointment Letter",
	"Employee Onboarding",
	"Employee",
];

frappe.rcc.AMENDABLE_FORM_DOCTYPES = [
	"Staffing Plan",
	"Interview",
	"Interview Feedback",
	"Job Offer",
	"Employee Onboarding",
];

// Colour capsules for Job Requisition status values (fallback = neutral gray).
frappe.rcc.STATUS_COLORS = {
	"Pending": { color: "#b45309", bg: "#fef3c7", border: "#fde68a" },
	"Open & Approved": { color: "#15803d", bg: "#dcfce7", border: "#bbf7d0" },
	"Rejected": { color: "#b91c1c", bg: "#fee2e2", border: "#fecaca" },
	"Filled": { color: "#1d4ed8", bg: "#dbeafe", border: "#bfdbfe" },
	"On Hold": { color: "#7c3aed", bg: "#ede9fe", border: "#ddd6fe" },
	"Cancelled": { color: "#475569", bg: "#f1f5f9", border: "#e2e8f0" },
	"Open": { color: "#15803d", bg: "#dcfce7", border: "#bbf7d0" },
	"Closed": { color: "#475569", bg: "#f1f5f9", border: "#e2e8f0" },
	"Replied": { color: "#1d4ed8", bg: "#dbeafe", border: "#bfdbfe" },
	"Hold": { color: "#b45309", bg: "#fef3c7", border: "#fde68a" },
	"Accepted": { color: "#047857", bg: "#d1fae5", border: "#a7f3d0" },
	"Under Review": { color: "#1d4ed8", bg: "#dbeafe", border: "#bfdbfe" },
	"Cleared": { color: "#15803d", bg: "#dcfce7", border: "#bbf7d0" },
	"Awaiting Response": { color: "#b45309", bg: "#fef3c7", border: "#fde68a" },
	"In Process": { color: "#1d4ed8", bg: "#dbeafe", border: "#bfdbfe" },
	"Completed": { color: "#15803d", bg: "#dcfce7", border: "#bbf7d0" },
	"Active": { color: "#15803d", bg: "#dcfce7", border: "#bbf7d0" },
	"Inactive": { color: "#475569", bg: "#f1f5f9", border: "#e2e8f0" },
	"Suspended": { color: "#b45309", bg: "#fef3c7", border: "#fde68a" },
	"Left": { color: "#b91c1c", bg: "#fee2e2", border: "#fecaca" },
	"Working": { color: "#b45309", bg: "#fef3c7", border: "#fde68a" },
	"Overdue": { color: "#b91c1c", bg: "#fee2e2", border: "#fecaca" },
	"Pending Review": { color: "#b45309", bg: "#fef3c7", border: "#fde68a" },
	"Template": { color: "#1d4ed8", bg: "#dbeafe", border: "#bfdbfe" },
};

frappe.rcc.DOCTYPE_FILTER_FIELDS = {
	"Job Requisition": {
		company: "company",
		department: "department",
		designation: "designation",
		status: "status",
		date: "posting_date",
	},
	"Staffing Plan": {
		company: "company",
		department: "department",
	},
	"Job Opening": {
		company: "company",
		department: "department",
		designation: "designation",
		job_opening: "name",
		status: "status",
		date: "posted_on",
	},
	"Job Applicant": {
		designation: "designation",
		job_opening: "job_title",
		status: "status",
		date: "creation",
	},
	"Interview": {
		designation: "designation",
		job_opening: "job_opening",
		status: "status",
		date: "scheduled_on",
	},
	"Interview Feedback": {
		date: "creation",
	},
	"Job Offer": {
		company: "company",
		designation: "designation",
		status: "status",
		date: "offer_date",
	},
	"Appointment Letter": {
		company: "company",
		date: "appointment_date",
	},
	"Employee Onboarding": {
		company: "company",
		department: "department",
		designation: "designation",
		status: "boarding_status",
		date: "boarding_begins_on",
	},
	"Employee": {
		company: "company",
		department: "department",
		designation: "designation",
		status: "status",
		date: "date_of_joining",
	},
};

frappe.rcc.WorkspaceTab = class WorkspaceTab {
	constructor(controller) {
		this.ctrl = controller;
		this.pipeline_doctypes = frappe.rcc.PIPELINE_DOCTYPES;
		this.form_view_doctypes = frappe.rcc.FORM_VIEW_DOCTYPES;
		this.active_doctype = null;
		this.current_doc = null;
		this.form_controls = {};
		this.child_tables = {};
		this.is_new_record = false;
		this.is_submittable = false;
		this.needs_name = false;
		this.current_records = [];
		this.current_search_query = "";
		this.connection_filter = null;
	}

	get wrapper() {
		return this.ctrl.wrapper;
	}

	get $content() {
		return this.ctrl.$content();
	}

	bind_events() {
		const self = this;
		const wrapper = this.wrapper;

		// DocType selection (15% column)
		$(wrapper).on("click", ".rcc-doctype-item", function () {
			self.select_doctype($(this).attr("data-doctype"));
		});

		// Record selection (25% column)
		$(wrapper).on("click", ".rcc-record-item", function () {
			self.open_record(self.active_doctype, $(this).attr("data-name"));
		});

		// Load the next page of records into the 25% list
		$(wrapper).on("click", "[data-load-more]", function () {
			self.load_more_records(self.active_doctype);
		});

		// New record button (25% column header) — opens a blank inline form
		$(wrapper).on("click", "#rcc-btn-new", function () {
			self.new_record(self.active_doctype);
		});

		// Collapsible Connections section (loads links lazily on first expand)
		$(wrapper).on("click", "[data-connections-toggle]", function () {
			const $section = $(this).closest("[data-connections]");
			const $body = $section.find("[data-connections-body]");
			const expanded = $section.toggleClass("is-open").hasClass("is-open");
			$(this)
				.find(".rcc-xform-connections-chevron")
				.html(frappe.rcc.icon(expanded ? "chevron-down" : "chevron-right", 14));
			$body.toggle(expanded);
			if (expanded && !$section.attr("data-loaded") && self.current_doc) {
				$section.attr("data-loaded", "1");
				self.render_connections(self.active_doctype, self.current_doc.name);
			}
		});

		// Show linked records in the Workspace middle column.
		$(wrapper).on("click", "[data-conn-doctype]", function (e) {
			e.stopPropagation();
			self.open_connection($(this).attr("data-conn-doctype"));
		});

		// Create a new linked record from connection section (+)
		$(wrapper).on("click", "[data-conn-add]", function (e) {
			e.stopPropagation();
			self.create_connected_record($(this).attr("data-conn-add"));
		});

		$(wrapper).on("click", "#rcc-clear-connection-filter", function () {
			self.select_doctype(self.active_doctype);
		});

		// Intercept click on "project" link field in Employee Onboarding form to navigate to Onboarding Tasks tab
		const domWrapper = $(wrapper)[0] || wrapper;
		if (domWrapper && domWrapper.addEventListener) {
			domWrapper.addEventListener(
				"click",
				function (e) {
					if (self.active_doctype !== "Employee Onboarding") return;
					const linkTarget = e.target.closest(
						'.rcc-xform-field[data-fieldname="project"] .btn-open, ' +
						'.rcc-xform-field[data-fieldname="project"] a, ' +
						'.rcc-xform-field[data-fieldname="project"] [data-doctype="Project"]'
					);
					if (linkTarget) {
						e.preventDefault();
						e.stopPropagation();
						e.stopImmediatePropagation();
						const project =
							(self.current_doc && self.current_doc.project) ||
							$(linkTarget).closest('.rcc-xform-field[data-fieldname="project"]').find("input").val() ||
							$(linkTarget).text().trim() ||
							"";
						if (project) {
							self.open_project_in_onboarding_tasks(project);
						}
					}
				},
				true // Capture phase to prevent Frappe router from navigating away
			);
		}

		$(wrapper).on(
			"click",
			'.rcc-xform-field[data-fieldname="project"] .btn-open, .rcc-xform-field[data-fieldname="project"] a',
			function (e) {
				if (self.active_doctype === "Employee Onboarding") {
					e.preventDefault();
					e.stopPropagation();
					const project =
						(self.current_doc && self.current_doc.project) ||
						$(this).closest('.rcc-xform-field[data-fieldname="project"]').find("input").val() ||
						"";
					if (project) {
						self.open_project_in_onboarding_tasks(project);
					}
				}
			}
		);


		// Collapsible Recruitment Journey section toggle
		$(wrapper).on("click", "[data-journey-toggle]", function () {
			const $section = $(this).closest("[data-journey]");
			const $body = $section.find("[data-journey-body]");
			const expanded = $section.toggleClass("is-open").hasClass("is-open");
			$(this)
				.find(".rcc-journey-chevron")
				.html(frappe.rcc.icon(expanded ? "chevron-up" : "chevron-down", 14));
			$body.slideToggle(120);
		});

		$(wrapper).on("keydown", "[data-journey-toggle]", function (e) {
			if (e.key === "Enter" || e.key === " ") {
				e.preventDefault();
				$(this).trigger("click");
			}
		});

		// Switch to a stage in the Recruitment Journey when clicked
		$(wrapper).on("click", "[data-journey-doctype]", function () {
			const dt = $(this).attr("data-journey-doctype");
			if (dt && dt !== self.active_doctype) {
				self.select_doctype(dt);
			}
		});

		// Collapsible Interview Summary section toggle (Job Applicant form)
		$(wrapper).on("click", "[data-interview-summary-toggle]", function (e) {
			if ($(e.target).closest("[data-schedule-interview]").length) return;
			const $section = $(this).closest("[data-interview-summary]");
			const $body = $section.find("[data-interview-summary-body]");
			const expanded = $section.toggleClass("is-open").hasClass("is-open");
			$(this)
				.find(".rcc-interview-summary-chevron")
				.html(frappe.rcc.icon(expanded ? "chevron-up" : "chevron-down", 14));
			$body.slideToggle(120);
		});

		$(wrapper).on("keydown", "[data-interview-summary-toggle]", function (e) {
			if ($(e.target).closest("[data-schedule-interview]").length) return;
			if (e.key === "Enter" || e.key === " ") {
				e.preventDefault();
				$(this).trigger("click");
			}
		});


		// Schedule Interview button in Interview Summary
		$(wrapper).on("click", "[data-schedule-interview]", function (e) {
			e.stopPropagation();
			self.show_schedule_interview_dialog();
		});

		// Collapsible Section Break toggle
		$(wrapper).on("click", "[data-section-toggle]", function () {
			const $section = $(this).closest(".rcc-xform-section");
			const $cols = $section.find(".rcc-xform-cols");
			const collapsed = $section.toggleClass("is-collapsed").hasClass("is-collapsed");
			$(this)
				.find(".rcc-xform-section-chevron")
				.html(frappe.rcc.icon(collapsed ? "chevron-right" : "chevron-up", 14));
			$cols.slideToggle(120);
		});

		$(wrapper).on("keydown", "[data-section-toggle]", function (e) {
			if (e.key === "Enter" || e.key === " ") {
				e.preventDefault();
				$(this).trigger("click");
			}
		});

		// New record action in the empty detail panel
		$(wrapper).on("click", "[data-new-record]", function () {
			self.new_record(self.active_doctype);
		});

		// Open the full Frappe form of the currently previewed record
		$(wrapper).on("click", "[data-open-full-form]", function () {
			frappe.set_route("Form", self.active_doctype, $(this).attr("data-open-full-form"));
		});

		// Save the inline form (writes back only editable fields, server-validated)
		$(wrapper).on("click", "[data-save-form]", function () {
			if (self.current_doc) {
				self.save_record_form(self.active_doctype, self.current_doc.name);
			}
		});

		// Submit / Cancel for submittable DocTypes
		$(wrapper).on("click", "[data-submit-form]", function () {
			if (self.current_doc) {
				self.submit_record_form(self.active_doctype, self.current_doc.name);
			}
		});
		$(wrapper).on("click", "[data-cancel-form]", function () {
			if (self.current_doc) {
				self.cancel_record_form(self.active_doctype, self.current_doc.name);
			}
		});
		$(wrapper).on("click", "[data-amend-form]", function () {
			if (self.current_doc) {
				self.amend_record_form(self.active_doctype, self.current_doc);
			}
		});

		// Live field change listener: sync model and refresh field dependencies
		$(wrapper).on(
			"change input click",
			".rcc-xform-body input, .rcc-xform-body select, .rcc-xform-body textarea",
			function () {
				const $field = $(this).closest(".rcc-xform-field");
				const fieldname = $field.attr("data-fieldname");
				if (!fieldname || !self.current_doc) return;
				const ctrl = self.form_controls[fieldname];
				if (ctrl) {
					const val = ctrl.get_value();
					if (self.current_doc[fieldname] !== val) {
						self.current_doc[fieldname] = val;
						self.refresh_dependency();
						self.on_field_change(self.active_doctype, fieldname, ctrl);
					}
				}
			}
		);

		// Inline form tab switching (Tab Break layout in the detail form)
		$(wrapper).on("click", ".rcc-xform-tab", function () {
			const idx = $(this).attr("data-form-tab");
			self
				.$content.find(".rcc-xform-tab")
				.removeClass("active")
				.filter(`[data-form-tab="${idx}"]`)
				.addClass("active");
			self
				.$content.find(".rcc-xform-pane")
				.removeClass("active")
				.filter(`[data-form-pane="${idx}"]`)
				.addClass("active");
		});

		// Inline child table: add / remove rows
		$(wrapper).on("click", ".rcc-child-add", function () {
			self.add_child_row($(this).closest(".rcc-child-table").attr("data-fieldname"));
		});
		$(wrapper).on("click", ".rcc-child-del", function () {
			self.remove_child_row(
				$(this).closest(".rcc-child-table").attr("data-fieldname"),
				cint($(this).attr("data-index"))
			);
		});
		$(wrapper).on("click", ".rcc-child-edit", function () {
			self.edit_child_row(
				$(this).closest(".rcc-child-table").attr("data-fieldname"),
				cint($(this).attr("data-index"))
			);
		});

		// Search in record list
		$(wrapper).on("input", "#rcc-record-search", function () {
			const query = ($(this).val() || "").trim().toLowerCase();
			self.$content.find("#rcc-record-search-clear").toggle(query.length > 0);
			self.filter_records(query);
		});

		// Clear search
		$(wrapper).on("click", "#rcc-record-search-clear", function () {
			self.$content.find("#rcc-record-search").val("").focus();
			$(this).hide();
			self.filter_records("");
		});
	}

	render() {
		// Filter pipeline to only DocTypes the current user can read.
		this.visible_doctypes = this.pipeline_doctypes.filter(
			(d) => frappe.model.can_read(d.doctype)
		);

		this.$content.html(`
			<div class="rcc-pipeline">
				<div class="rcc-pipeline-col rcc-col-doctypes">
					<div class="rcc-col-head"><span>Recruitment Journey</span></div>
					<div class="rcc-col-body" id="rcc-doctype-list"></div>
				</div>
				<div class="rcc-pipeline-col rcc-col-records">
					<div class="rcc-col-head rcc-col-head-records">
						<div class="rcc-list-head-row">
							<div class="rcc-list-title-wrap">
								<span id="rcc-list-title">Records</span>
								<span class="rcc-col-count" id="rcc-list-count"></span>
							</div>
							<button type="button" class="rcc-new-btn rcc-new-btn-compact" id="rcc-btn-new">
								${frappe.rcc.icon("plus", 12)} <span id="rcc-btn-new-text">${__("New")}</span>
							</button>
						</div>
						<div class="rcc-record-search-wrap">
							<span class="rcc-search-icon">${frappe.rcc.icon("search", 13)}</span>
							<input type="text" class="rcc-record-search-input" id="rcc-record-search" placeholder="${__("Search...")}" autocomplete="off" />
							<button type="button" class="rcc-search-clear" id="rcc-record-search-clear" title="${__("Clear")}" style="display: none;">&times;</button>
						</div>
						<div class="rcc-connection-filter" id="rcc-connection-filter" style="display: none;"></div>
					</div>
					<div class="rcc-col-body" id="rcc-record-list"></div>
				</div>
				<div class="rcc-pipeline-col rcc-col-detail">
					<div class="rcc-col-head rcc-col-head-detail">
						<div id="rcc-detail-head" class="rcc-detail-head">
							<span class="rcc-detail-head-title">Details</span>
						</div>
					</div>
					<div class="rcc-col-body" id="rcc-detail-panel"></div>
				</div>
			</div>
		`);

		this.render_doctype_list();
		this.load_doctype_counts();
		const first_visible = this.visible_doctypes[0];
		this.select_doctype(
			(this.active_doctype && frappe.model.can_read(this.active_doctype)
				? this.active_doctype
				: null) || (first_visible ? first_visible.doctype : null),
			this.connection_filter
		);
	}

	refresh() {
		this.select_doctype(this.active_doctype || this.pipeline_doctypes[0].doctype);
	}

	render_doctype_list() {
		let html = "";
		let current_group = null;
		// Only render DocTypes the current user can read.
		const visible = this.visible_doctypes || this.pipeline_doctypes.filter(
			(d) => frappe.model.can_read(d.doctype)
		);

		if (!visible.length) {
			this.$content.find("#rcc-doctype-list").html(
				`<div class="rcc-placeholder" style="padding:24px 12px;text-align:center;color:#94a3b8;font-size:12px;">` +
				`${__("You do not have permission to view any recruitment records.")}</div>`
			);
			return;
		}

		visible.forEach((d) => {
			if (d.group !== current_group) {
				if (current_group !== null) html += "</div>";
				current_group = d.group;
				const heading = current_group
					? `<div class="rcc-doctype-group-head">${frappe.utils.escape_html(__(current_group))}</div>`
					: "";
				html += `<div class="rcc-doctype-group">${heading}`;
			}
			html += this.render_doctype_item(d);
		});

		if (current_group !== null) html += "</div>";

		this.$content.find("#rcc-doctype-list").html(html);
	}

	render_doctype_item(d) {
		const dt = frappe.utils.escape_html(d.doctype);
		const color = d.color || "#2563eb";
		const bg = d.bg || "#eff6ff";
		const description = d.description
			? `<div class="rcc-doctype-desc">${frappe.utils.escape_html(__(d.description))}</div>`
			: "";
		return `<div class="rcc-doctype-item" data-doctype="${dt}" title="${frappe.utils.escape_html(__(d.doctype))}">
			<span class="rcc-doctype-icon" style="color:${color};background:${bg};">${frappe.rcc.icon(d.icon)}</span>
			<div class="rcc-doctype-info">
				<div class="rcc-doctype-name">${frappe.utils.escape_html(__(d.doctype))}</div>
				${description}
			</div>
			<span class="rcc-doctype-count" data-count-for="${dt}"></span>
		</div>`;
	}

	// Resolve all applicable filters for a DocType by combining global top filters and connection filters.
	get_doctype_filters(doctype, extra_filters = null) {
		const gf = (this.ctrl && this.ctrl.filters) || {};
		const filters = {};
		const map = (frappe.rcc.DOCTYPE_FILTER_FIELDS && frappe.rcc.DOCTYPE_FILTER_FIELDS[doctype]) || {};

		// 1. Company
		if (gf.company) {
			const fn = map.company || (frappe.meta && frappe.meta.has_field && frappe.meta.has_field(doctype, "company") ? "company" : null);
			if (fn) filters[fn] = gf.company;
		}

		// 2. Department
		if (gf.department) {
			const fn = map.department || (frappe.meta && frappe.meta.has_field && frappe.meta.has_field(doctype, "department") ? "department" : null);
			if (fn) filters[fn] = gf.department;
		}

		// 3. Designation
		if (gf.designation) {
			const fn = map.designation || (frappe.meta && frappe.meta.has_field && frappe.meta.has_field(doctype, "designation") ? "designation" : null);
			if (fn) filters[fn] = gf.designation;
		}

		// 4. Job Opening
		if (gf.job_opening) {
			const fn = map.job_opening ||
				(doctype === "Job Opening" ? "name" :
				 (frappe.meta && frappe.meta.has_field && frappe.meta.has_field(doctype, "job_opening")) ? "job_opening" :
				 (frappe.meta && frappe.meta.has_field && frappe.meta.has_field(doctype, "job_title")) ? "job_title" : null);
			if (fn) filters[fn] = gf.job_opening;
		}

		// 5. Status
		if (gf.status && gf.status !== "All Statuses") {
			const fn = map.status || this.pick_field(doctype, ["status", "boarding_status", "result"]);
			if (fn) {
				const df = frappe.meta && frappe.meta.get_docfield && frappe.meta.get_docfield(doctype, fn);
				const options = (df && df.options) ? df.options.split("\n").map((s) => s.trim()) : [];
				if (!options.length || options.includes(gf.status)) {
					filters[fn] = gf.status;
				} else {
					const match = options.find((opt) => opt.toLowerCase().startsWith(gf.status.toLowerCase()));
					if (match) {
						filters[fn] = match;
					}
				}
			}
		}

		// 6. Dates (from_date, to_date)
		if (gf.from_date || gf.to_date) {
			if (doctype === "Staffing Plan") {
				if (gf.from_date) filters["to_date"] = [">=", gf.from_date];
				if (gf.to_date) filters["from_date"] = ["<=", gf.to_date];
			} else {
				const fn = map.date || this.pick_field(doctype, [
					"posting_date",
					"posted_on",
					"scheduled_on",
					"offer_date",
					"appointment_date",
					"date_of_joining",
					"boarding_begins_on",
					"from_date",
					"creation",
				]);
				if (fn) {
					if (gf.from_date && gf.to_date) {
						filters[fn] = ["between", [gf.from_date, gf.to_date]];
					} else if (gf.from_date) {
						filters[fn] = [">=", gf.from_date];
					} else if (gf.to_date) {
						filters[fn] = ["<=", gf.to_date];
					}
				}
			}
		}

		// Merge extra/connection filters if present
		if (extra_filters) {
			Object.assign(filters, extra_filters);
		}

		return filters;
	}

	// Triggered whenever top filter bar changes or resets
	on_global_filter_change() {
		this.load_doctype_counts();
		if (this.active_doctype) {
			this.load_records(this.active_doctype);
		}
	}

	// Per-DocType record-count badge in the 15% column (respects active top filters).
	// Only fetches counts for DocTypes the user can read.
	load_doctype_counts() {
		const self = this;
		const visible = this.visible_doctypes || this.pipeline_doctypes.filter(
			(d) => frappe.model.can_read(d.doctype)
		);
		visible.forEach((d) => {
			const filters = self.get_doctype_filters(d.doctype);
			frappe.db
				.count(d.doctype, { filters: filters })
				.then((count) => {
					const $badge = self.$content.find(
						`.rcc-doctype-count[data-count-for="${d.doctype}"]`
					);
					if (!$badge.length) return;
					$badge.text(count > 999 ? "999+" : String(count));
					$badge.toggleClass("is-empty", !count);
				})
				.catch(() => {});
		});
	}

	select_doctype(doctype, connection_filter = null) {
		if (!doctype) return;
		// Guard: do not load a DocType the user cannot read.
		if (!frappe.model.can_read(doctype)) {
			frappe.show_alert({ message: __("You do not have permission to view {0}.", [__(doctype)]), indicator: "red" });
			return;
		}
		this.active_doctype = doctype;
		this.connection_filter = connection_filter;
		this.current_doc = null;

		const $c = this.$content;
		const $connection_filter = $c.find("#rcc-connection-filter");
		if (connection_filter && connection_filter.filters && Object.keys(connection_filter.filters).length) {
			let label = "";
			if (connection_filter.source_doctype) {
				label = __("Linked to {0}: {1}", [connection_filter.source_doctype, connection_filter.source_name]);
			} else if (connection_filter.label) {
				label = connection_filter.label;
			} else {
				label = Object.entries(connection_filter.filters)
					.map(([k, v]) => `${frappe.model.unscrub(k)}: ${v}`)
					.join(", ");
			}
			$connection_filter.html(
				`<span>${frappe.utils.escape_html(label)}</span>` +
				`<button type="button" id="rcc-clear-connection-filter" title="${__("Show all records")}">&times;</button>`
			).show();
		} else {
			$connection_filter.hide().empty();
		}
		$c.find(".rcc-doctype-item").removeClass("active");
		$c.find(`.rcc-doctype-item[data-doctype="${doctype}"]`).addClass("active");

		$c.find("#rcc-list-title").text(__(doctype));
		// Show/hide the New button based on create permission.
		const can_create = frappe.model.can_create(doctype);
		const $new_btn = $c.find("#rcc-btn-new");
		$new_btn.html(
			`${frappe.rcc.icon("plus", 12)} <span id="rcc-btn-new-text">${__("New")} ${frappe.utils.escape_html(__(doctype))}</span>`
		);
		$new_btn.toggle(can_create);
		$c.find("#rcc-record-search")
			.val("")
			.attr("placeholder", `${__("Search")} ${frappe.utils.escape_html(__(doctype))}...`);
		$c.find("#rcc-record-search-clear").hide();
		this.current_search_query = "";
		this.current_records = [];
		this.current_total = null;
		this.list_page_length = 50;
		this.loading_more = false;

		$c.find("#rcc-detail-head").html(
			`<span class="rcc-detail-head-title">${frappe.utils.escape_html(__(doctype))}</span>`
		);
		$c.find("#rcc-detail-panel").html(this.detail_placeholder(doctype));

		this.load_records(doctype);
	}

	// Empty detail panel: prompt + a "New <DocType>" action (only when user has create permission).
	detail_placeholder(doctype) {
		const can_create = frappe.model.can_create(doctype);
		return `<div class="rcc-placeholder">
			<div class="rcc-placeholder-icon">📋</div>
			<div class="rcc-placeholder-text">${frappe.utils.escape_html(
				__("Select a record to preview its form here.")
			)}</div>
			${can_create ? `<button type="button" class="btn btn-primary btn-sm rcc-new-btn rcc-empty-new-btn" data-new-record>
				${frappe.rcc.icon("plus", 13)} ${__("New")} ${frappe.utils.escape_html(__(doctype))}
			</button>` : ""}
		</div>`;
	}

	load_records(doctype) {
		const self = this;
		const connection_filter = this.connection_filter;
		frappe.model.with_doctype(doctype, function () {
			if (self.active_doctype !== doctype || self.connection_filter !== connection_filter) return;
			self.load_records_now(doctype);
		});
	}

	// The columns fetched for the 25% list, plus the fields used for display.
	list_query_fields(doctype) {
		const cfg = this.pipeline_doctypes.find((d) => d.doctype === doctype) || {};
		const title_field =
			cfg.title_field && cfg.title_field !== "name" ? cfg.title_field : "name";

		const fields = ["name"];
		if (title_field !== "name") fields.push(title_field);
		fields.push("modified");
		// A representative date column per doctype (posting_date, else posted_on, else from_date).
		const date_field = this.pick_field(doctype, ["posting_date", "posted_on", "from_date"]);
		if (date_field) fields.push(date_field);
		// Some doctypes expose state as `status`, others (e.g. Interview Feedback) as `result`.
		const status_field = this.pick_field(doctype, [
			"status",
			"result",
			"boarding_status",
		]);
		if (status_field) {
			fields.push(status_field);
		} else if (frappe.get_meta(doctype).is_submittable) {
			// No status field (e.g. Staffing Plan) — fall back to the docstatus
			// so the list can still show a state capsule.
			fields.push("docstatus");
		}

		return { fields, title_field, date_field, status_field };
	}

	// First fieldname out of `names` that exists on the doctype.
	pick_field(doctype, names) {
		let found = null;
		names.some(function (fn) {
			if (frappe.meta.has_field(doctype, fn)) {
				found = fn;
				return true;
			}
			return false;
		});
		return found;
	}

	load_records_now(doctype) {
		const self = this;
		const connection_filter = this.connection_filter;
		const extra_filters = connection_filter ? connection_filter.filters : null;
		const filters = this.get_doctype_filters(doctype, extra_filters);
		const page_length = this.list_page_length || 50;
		const { fields } = this.list_query_fields(doctype);

		const $c = this.$content;
		const list_el = $c.find("#rcc-record-list");
		$c.find("#rcc-list-count").text("");
		list_el.html('<div class="rcc-loading">Loading…</div>');

		this.current_records = [];
		this.current_total = null;
		this.loading_more = false;

		// The middle-column total respects active filters.
		frappe.db
			.count(doctype, { filters: filters })
			.then(function (count) {
				if (self.active_doctype !== doctype || self.connection_filter !== connection_filter) return;
				self.current_total = count;
				self.filter_records(self.current_search_query || "");
			})
			.catch(function () {});

		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: doctype,
				filters: filters,
				fields: fields,
				limit_start: 0,
				limit_page_length: page_length,
				order_by: "modified desc",
			},
			callback: function (r) {
				if (self.active_doctype !== doctype || self.connection_filter !== connection_filter) return;
				self.current_records = (r && r.message) || [];
				self.filter_records(self.current_search_query || "");
				const viewing_new =
					self.current_doc &&
					self.current_doc.__islocal &&
					self.current_doc.doctype === doctype;
				if (self.current_records.length > 0) {
					if (
						!viewing_new &&
						((connection_filter && connection_filter.auto_select) ||
							!self.current_doc ||
							self.current_doc.doctype !== doctype ||
							!self.current_records.some((rec) => rec.name === self.current_doc.name))
					) {
						self.open_record(doctype, self.current_records[0].name);
					}
				} else {
					self.current_doc = null;
					$c.find("#rcc-detail-panel").html(self.detail_placeholder(doctype));
					$c.find("#rcc-detail-head").html(
						`<span class="rcc-detail-head-title">${frappe.utils.escape_html(__(doctype))}</span>`
					);
				}
			},
			error: function () {
				if (self.active_doctype !== doctype || self.connection_filter !== connection_filter) return;
				list_el.html(frappe.rcc.placeholder("Unable to load records for this doctype."));
			},
		});
	}

	// Append the next page of records to the 25% list.
	load_more_records(doctype) {
		const self = this;
		const connection_filter = this.connection_filter;
		const extra_filters = connection_filter ? connection_filter.filters : null;
		const filters = this.get_doctype_filters(doctype, extra_filters);
		if (this.loading_more || this.active_doctype !== doctype) return;
		if (this.current_total != null && this.current_records.length >= this.current_total) return;
		this.loading_more = true;

		const { fields } = this.list_query_fields(doctype);
		this.$content.find("[data-load-more]").text(__("Loading…"));

		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: doctype,
				filters: filters,
				fields: fields,
				limit_start: this.current_records.length,
				limit_page_length: this.list_page_length || 50,
				order_by: "modified desc",
			},
			callback: function (r) {
				if (self.active_doctype !== doctype || self.connection_filter !== connection_filter) return;
				self.loading_more = false;
				self.current_records = self.current_records.concat((r && r.message) || []);
				self.filter_records(self.current_search_query || "");
			},
			error: function () {
				if (self.active_doctype !== doctype || self.connection_filter !== connection_filter) return;
				self.loading_more = false;
				self.filter_records(self.current_search_query || "");
			},
		});
	}

	filter_records(query) {
		this.current_search_query = query || "";
		const q = (query || "").trim().toLowerCase();
		const cfg = this.pipeline_doctypes.find((d) => d.doctype === this.active_doctype) || {};
		const title_field =
			cfg.title_field && cfg.title_field !== "name" ? cfg.title_field : "name";

		let filtered = this.current_records || [];
		if (q) {
			filtered = filtered.filter((row) => {
				const name_val = (row.name || "").toLowerCase();
				const title_val = ((row[title_field] || "") + "").toLowerCase();
				const status_val = (
					(row.status || row.result || row.boarding_status || "") + ""
				).toLowerCase();
				return name_val.includes(q) || title_val.includes(q) || status_val.includes(q);
			});
		}

		// Show the true total (same as the 15% badge); fall back to loaded rows until known.
		const count =
			!q && this.current_total != null ? this.current_total : filtered.length;
		this.$content.find("#rcc-list-count").text(count);
		this.render_records_items(filtered, q);
	}

	render_records_items(rows, query) {
		const self = this;
		const doctype = this.active_doctype;
		const { title_field, date_field, status_field } = this.list_query_fields(doctype);
		const show_id = title_field !== "name";

		const list_el = this.$content.find("#rcc-record-list");

		if (!rows || !rows.length) {
			if (query) {
				list_el.html(
					`<div class="rcc-empty-state" style="padding: 24px 16px; text-align: center; color: #94a3b8; font-size: 12px;">` +
						`No records matching "<strong>${frappe.utils.escape_html(query)}</strong>"` +
					`</div>`
				);
			} else {
				list_el.html(frappe.rcc.placeholder("No records found."));
			}
			return;
		}

		const active_name = this.current_doc ? this.current_doc.name : null;

		list_el.html(
			rows
				.map(function (row) {
					const title =
						title_field === "name"
							? row.name
							: row[title_field] || row.name;
					const date_str = date_field && row[date_field]
						? frappe.datetime.str_to_user(row[date_field])
						: "";
					const status_html = status_field && row[status_field]
						? self.status_pill(row[status_field])
						: row.docstatus !== undefined
							? self.docstatus_pill(row.docstatus)
							: "";
					const is_active = active_name && active_name === row.name ? " active" : "";
					return `<div class="rcc-record-item${is_active}" data-name="${frappe.utils.escape_html(row.name)}">
						<div class="rcc-record-top">
							<div class="rcc-record-title">${frappe.utils.escape_html(title)}</div>
							${status_html}
						</div>
						<div class="rcc-record-sub">
							${
								show_id
									? `<span class="rcc-record-id">${frappe.utils.escape_html(row.name)}</span>`
									: ""
							}
							${
								date_str
									? `<span class="rcc-record-date">${frappe.rcc.icon("calendar", 12)} ${frappe.utils.escape_html(date_str)}</span>`
									: ""
							}
						</div>
					</div>`;
				})
				.join("")
		);

		// Offer to load the remainder when more records exist than are shown.
		if (
			!query &&
			this.current_total != null &&
			this.current_records.length < this.current_total
		) {
			const remaining = this.current_total - this.current_records.length;
			list_el.append(
				`<button type="button" class="rcc-load-more" data-load-more>${__("Load more")} <span class="rcc-load-more-count">${remaining}</span></button>`
			);
		}
	}

	open_record(doctype, name) {
		if (!doctype || !name) return;
		// Guard: ensure the user can read this DocType before loading the form.
		if (!frappe.model.can_read(doctype)) {
			frappe.show_alert({ message: __("You do not have permission to view {0}.", [__(doctype)]), indicator: "red" });
			return;
		}
		const self = this;
		const $c = this.$content;

		$c.find(".rcc-record-item").removeClass("active");
		$c.find(`.rcc-record-item[data-name="${name}"]`).addClass("active");

		$c.find("#rcc-detail-head").html(
			`<span class="rcc-detail-head-title">${frappe.utils.escape_html(__(doctype))} · ${frappe.utils.escape_html(name)}</span>`
		);
		const panel = $c.find("#rcc-detail-panel");
		panel.html('<div class="rcc-loading">Loading…</div>');

		// Full inline form is available only for a subset of DocTypes
		if (this.form_view_doctypes.indexOf(doctype) === -1) {
			panel.html(frappe.rcc.placeholder(`Form view for ${__(doctype)} is coming soon.`, "🚧"));
			return;
		}

		frappe.model.with_doctype(doctype, function () {
			frappe.call({
				method: "frappe.client.get",
				args: { doctype: doctype, name: name },
				callback: function (r) {
					if (self.active_doctype !== doctype) return;
					if (r && r.message) {
						self.render_record_form(r.message, doctype);
					} else {
						panel.html(frappe.rcc.placeholder("Record not found."));
					}
				},
				error: function () {
					panel.html(frappe.rcc.placeholder("Unable to load this record."));
				},
			});
		});
	}

	// Open a blank inline form in the 60% column so the user can create a record.
	new_record(doctype, defaults = null) {
		if (!doctype) return;
		// Guard: do not allow creation without create permission.
		if (!frappe.model.can_create(doctype)) {
			frappe.show_alert({ message: __("You do not have permission to create {0}.", [__(doctype)]), indicator: "red" });
			return;
		}
		const self = this;
		const $c = this.$content;

		$c.find(".rcc-record-item").removeClass("active");

		// Only Job Requisition has the inline form; others fall back to the desk.
		if (this.form_view_doctypes.indexOf(doctype) === -1) {
			frappe.new_doc(doctype, defaults);
			return;
		}

		frappe.model.with_doctype(doctype, function () {
			if (self.active_doctype !== doctype) return;
			const doc = frappe.model.get_new_doc(doctype);
			if (defaults) {
				Object.keys(defaults).forEach((k) => {
					if (defaults[k] !== undefined) {
						doc[k] = defaults[k];
					}
				});
			}
			self.render_record_form(doc, doctype);
		});
	}

	render_record_form(doc, doctype) {
		this.current_doc = doc;
		this.is_new_record = !!doc.__islocal;
		this.form_controls = {};
		this.child_tables = {};

		const meta = frappe.get_meta(doctype);
		this.is_submittable = !!(meta && meta.is_submittable);
		// "prompt" / "Set by user" naming needs a name supplied before saving.
		this.needs_name = this.is_new_record && meta && meta.autoname === "prompt";

		const tabs = this.build_form_tabs(doctype);
		const has_tabs = tabs.length > 1;
		const $panel = this.$content.find("#rcc-detail-panel");

		this.render_detail_head(doc, doctype);

		$panel.html(`
			<div class="rcc-xform">
				${this.summary_cards(doc)}
				${
					this.needs_name
						? `<div class="rcc-xform-field rcc-xform-name-field">
							<label class="control-label" for="rcc-new-name">${__("Name")} <span class="rcc-reqd">*</span></label>
							<input type="text" id="rcc-new-name" class="form-control" autocomplete="off">
						</div>`
						: ""
				}
				${this.connections_markup(doc, doctype)}
				${this.journey_markup(doc, doctype)}
				${this.interview_summary_markup(doc, doctype)}
				${has_tabs ? `<div class="rcc-xform-tabbar"></div>` : ""}
				<div class="rcc-xform-body"></div>
			</div>
		`);

		const $body = $panel.find(".rcc-xform-body");

		if (doctype === "Job Applicant" && !this.is_new_record) {
			this.load_interview_summary(doc.name);
		}

		if (!tabs.length) {
			$body.html(frappe.rcc.placeholder("No fields to display."));
			return;
		}

		if (!has_tabs) {
			this.render_form_sections(tabs[0].sections, $body);
			this.refresh_dependency();
			this.load_job_requisition_requester(doc, doctype);
			return;
		}

		const $tabbar = $panel.find(".rcc-xform-tabbar");
		const $panes = $('<div class="rcc-xform-panes"></div>').appendTo($body);
		tabs.forEach((tab, index) => {
			const active = index === 0;
			const $tab_btn = $(
				`<button type="button" class="rcc-xform-tab${active ? " active" : ""}" data-form-tab="${index}">${frappe.utils.escape_html(__(tab.label || "Details"))}</button>`
			).appendTo($tabbar);
			if (tab.df && tab.df.depends_on) {
				$tab_btn.attr("data-depends-on", tab.df.depends_on);
			}
			const $pane = $(
				`<div class="rcc-xform-pane${active ? " active" : ""}" data-form-pane="${index}"></div>`
			).appendTo($panes);
			if (tab.df && tab.df.depends_on) {
				$pane.attr("data-depends-on", tab.df.depends_on);
			}
			this.render_form_sections(tab.sections, $pane);
		});

		this.refresh_dependency();
		this.load_job_requisition_requester(doc, doctype);
	}

	load_job_requisition_requester(doc, doctype) {
		if (
			doctype === "Job Requisition" &&
			doc.requested_by &&
			["requested_by_name", "requested_by_dept", "requested_by_designation"].some(
				(fieldname) => !doc[fieldname]
			)
		) {
			this.jr_on_requested_by(doc, false);
		}
	}

	// Collapsible "Connections" section shown above the fields (mirrors the desk
	// form's dashboard links). Only rendered for saved records.
	connections_markup(doc, doctype) {
		if (!doc || !doc.name || doc.__islocal) return "";
		let initial_count = "";
		if (doctype === "Employee Onboarding" && doc.project) {
			initial_count = "1";
		}
		return `
			<div class="rcc-xform-connections" data-connections>
				<div class="rcc-xform-connections-head" data-connections-toggle role="button" tabindex="0">
					<span class="rcc-xform-connections-chevron">${frappe.rcc.icon("chevron-right", 14)}</span>
					<span class="rcc-xform-connections-title">${__("Connections")}</span>
					<span class="rcc-xform-connections-count" data-connections-count>${initial_count}</span>
				</div>
				<div class="rcc-xform-connections-body" data-connections-body style="display: none;">
					<div class="rcc-xform-connections-loading">${__("Loading…")}</div>
				</div>
			</div>
		`;
	}

	// Collapsible "Recruitment Journey" section shown below connections in Hiring Pipeline forms.
	journey_markup(doc, doctype) {
		const steps = [
			{ doctype: "Job Opening", label: "Opening", icon: "briefcase-business" },
			{ doctype: "Job Applicant", label: "Applicant", icon: "user-round-search" },
			{ doctype: "Interview", label: "Interview", icon: "messages-square" },
			{ doctype: "Interview Feedback", label: "Feedback", icon: "star" },
			{ doctype: "Job Offer", label: "Offer", icon: "file-pen-line" },
			{ doctype: "Appointment Letter", label: "Appointment", icon: "mail-check" },
			{ doctype: "Employee Onboarding", label: "Onboarding", icon: "list-checks" },
			{ doctype: "Employee", label: "Employee", icon: "badge-check" },
		];

		const current_index = steps.findIndex((s) => s.doctype === doctype);
		if (current_index === -1) return "";

		const cards_html = steps
			.map((step, index) => {
				let state_class = "is-future";
				let icon_markup = frappe.rcc.icon(step.icon, 16);

				if (index < current_index) {
					state_class = "is-completed";
					icon_markup = `<span class="rcc-journey-check">${frappe.rcc.icon("check", 15)}</span>`;
				} else if (index === current_index) {
					state_class = "is-current";
					icon_markup = frappe.rcc.icon(step.icon, 16);
				}

				return `
					<div class="rcc-journey-step ${state_class}" data-journey-doctype="${frappe.utils.escape_html(step.doctype)}" role="button" tabindex="0" title="${frappe.utils.escape_html(__("Switch to {0}", [step.doctype]))}">
						<div class="rcc-journey-step-icon">${icon_markup}</div>
						<div class="rcc-journey-step-label">${frappe.utils.escape_html(__(step.label))}</div>
					</div>
				`;
			})
			.join("");

		return `
			<div class="rcc-journey-card is-open" data-journey>
				<div class="rcc-journey-head" data-journey-toggle role="button" tabindex="0" title="${__("Click to collapse / expand")}">
					<div class="rcc-journey-title-wrap">
						<span class="rcc-journey-icon">${frappe.rcc.icon("journey", 16)}</span>
						<span class="rcc-journey-title">${__("Recruitment Journey")}</span>
					</div>
					<span class="rcc-journey-chevron">${frappe.rcc.icon("chevron-up", 14)}</span>
				</div>
				<div class="rcc-journey-body" data-journey-body style="display: block;">
					<div class="rcc-journey-steps">
						${cards_html}
					</div>
				</div>
			</div>
		`;
	}

	// Collapsible "Interview Summary" section shown for Job Applicant forms.
	interview_summary_markup(doc, doctype) {
		if (doctype !== "Job Applicant" || !doc || !doc.name || doc.__islocal) return "";
		const can_create_interview = frappe.model.can_create("Interview");
		return `
			<div class="rcc-interview-summary-card" data-interview-summary>
				<div class="rcc-interview-summary-head" data-interview-summary-toggle role="button" tabindex="0" title="${__("Click to collapse / expand")}">
					<div class="rcc-interview-summary-title-wrap">
						<span class="rcc-interview-summary-icon">${frappe.rcc.icon("messages-square", 15)}</span>
						<span class="rcc-interview-summary-title">${__("Interview Summary")}</span>
						<span class="rcc-interview-summary-count" data-interview-summary-count></span>
					</div>
					<div class="rcc-interview-summary-head-actions">
						${
							can_create_interview
								? `<button type="button" class="btn btn-default btn-xs rcc-btn-schedule-interview" data-schedule-interview title="${__("Schedule an interview for this applicant")}">
									${frappe.rcc.icon("plus", 12)} <span>${__("Schedule Interview")}</span>
								</button>`
								: ""
						}
						<span class="rcc-interview-summary-chevron">${frappe.rcc.icon("chevron-down", 14)}</span>
					</div>
				</div>
				<div class="rcc-interview-summary-body" data-interview-summary-body style="display: none;">
					<div class="rcc-interview-summary-loading">${__("Loading Interview Summary…")}</div>
				</div>
			</div>
		`;
	}

	load_interview_summary(docname) {
		const self = this;
		const $card = this.$content.find("[data-interview-summary]");
		if (!$card.length) return;
		const $body = $card.find("[data-interview-summary-body]");
		const $count = $card.find("[data-interview-summary-count]");

		frappe.call({
			method: "hrms.hr.doctype.job_applicant.job_applicant.get_interview_details",
			args: {
				job_applicant: docname,
			},
			callback: function (r) {
				if (!r || !r.message) {
					$count.text("0");
					$body.html(`<div class="rcc-interview-summary-empty"><p>${__("No Interview has been scheduled.")}</p></div>`);
					return;
				}
				const interviews = r.message.interviews || {};
				const entries = Object.entries(interviews);
				const stars = r.message.stars || 5;

				$count.text(entries.length ? String(entries.length) : "0");

				if (!entries.length) {
					$body.html(`
						<div class="rcc-interview-summary-empty">
							<span class="rcc-interview-empty-icon">${frappe.rcc.icon("messages-square", 20)}</span>
							<p>${__("No Interview has been scheduled.")}</p>
						</div>
					`);
					return;
				}

				const rows_html = entries
					.map(([key, item]) => {
						const date_formatted = item.scheduled_on
							? frappe.datetime.str_to_user(item.scheduled_on)
							: "—";
						const rating_html = self.render_interview_stars(item.average_rating, stars);
						const status_html = self.interview_status_pill(item.status);

						return `
							<tr>
								<td class="rcc-is-cell-id">
									<span class="rcc-is-id-text">${frappe.utils.escape_html(key)}</span>
								</td>
								<td class="rcc-is-cell-round">${frappe.utils.escape_html(item.interview_round || "—")}</td>
								<td class="rcc-is-cell-date">${frappe.utils.escape_html(date_formatted)}</td>
								<td class="rcc-is-cell-status">${status_html}</td>
								<td class="rcc-is-cell-rating">${rating_html}</td>
							</tr>
						`;
					})
					.join("");

				$body.html(`
					<div class="rcc-interview-summary-table-wrap">
						<table class="table table-bordered rcc-interview-summary-table">
							<thead>
								<tr>
									<th style="width: 25%;">${__("Interview")}</th>
									<th style="width: 27%;">${__("Interview Round")}</th>
									<th style="width: 18%;">${__("Date")}</th>
									<th style="width: 15%;">${__("Status")}</th>
									<th style="width: 15%;">${__("Rating")}</th>
								</tr>
							</thead>
							<tbody>
								${rows_html}
							</tbody>
						</table>
					</div>
				`);
			},
			error: function () {
				$count.text("0");
				$body.html(`<div class="rcc-interview-summary-empty text-muted"><p>${__("Unable to load interview details.")}</p></div>`);
			},
		});
	}

	render_interview_stars(rating, max_stars) {
		max_stars = max_stars || 5;
		rating = flt(rating) || 0;

		let stars_html = "";
		for (let i = 1; i <= max_stars; i++) {
			if (i <= rating) {
				stars_html += `<span class="rcc-star-icon is-full" title="${rating.toFixed(2)} / ${max_stars}">
					<svg viewBox="0 0 24 24" width="13" height="13" fill="#f59e0b" stroke="#f59e0b">
						<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
					</svg>
				</span>`;
			} else if (i - 0.5 <= rating) {
				const grad_id = `rcc-half-star-${Math.random().toString(36).substr(2, 6)}`;
				stars_html += `<span class="rcc-star-icon is-half" title="${rating.toFixed(2)} / ${max_stars}">
					<svg viewBox="0 0 24 24" width="13" height="13">
						<defs>
							<linearGradient id="${grad_id}">
								<stop offset="50%" stop-color="#f59e0b"/>
								<stop offset="50%" stop-color="#e2e8f0"/>
							</linearGradient>
						</defs>
						<path fill="url(#${grad_id})" stroke="#cbd5e1" d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
					</svg>
				</span>`;
			} else {
				stars_html += `<span class="rcc-star-icon is-empty" title="${rating.toFixed(2)} / ${max_stars}">
					<svg viewBox="0 0 24 24" width="13" height="13" fill="#f8fafc" stroke="#cbd5e1">
						<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
					</svg>
				</span>`;
			}
		}

		return `<div class="rcc-interview-stars">${stars_html}</div>`;
	}

	interview_status_pill(status) {
		if (!status) return "—";
		const map = {
			Cleared: { bg: "#dcfce7", color: "#15803d", border: "#bbf7d0" },
			Rejected: { bg: "#fee2e2", color: "#b91c1c", border: "#fecaca" },
			Pending: { bg: "#fef3c7", color: "#b45309", border: "#fde68a" },
			"Under Review": { bg: "#e0f2fe", color: "#0369a1", border: "#bae6fd" },
		};
		const style = map[status] || { bg: "#f1f5f9", color: "#475569", border: "#e2e8f0" };
		return `<span class="rcc-status-pill" style="background:${style.bg};color:${style.color};border:1px solid ${style.border};font-size:11px;padding:2px 8px;border-radius:999px;font-weight:600;">${frappe.utils.escape_html(__(status))}</span>`;
	}

	show_schedule_interview_dialog() {
		const self = this;
		if (!this.current_doc || !this.current_doc.name) return;

		const d = new frappe.ui.Dialog({
			title: __("Schedule Interview"),
			fields: [
				{
					label: __("Interview Round"),
					fieldname: "interview_round",
					fieldtype: "Link",
					options: "Interview Round",
					reqd: 1,
				},
			],
			primary_action_label: __("Create Interview"),
			primary_action(values) {
				d.hide();
				frappe.call({
					method: "hrms.hr.doctype.job_applicant.job_applicant.create_interview",
					args: {
						doc: self.current_doc,
						interview_round: values.interview_round,
					},
					freeze: true,
					freeze_message: __("Creating Interview…"),
					callback: function (r) {
						frappe.show_alert({
							message: __("Interview created successfully"),
							indicator: "green",
						});
						self.load_interview_summary(self.current_doc.name);
					},
				});
			},
		});
		d.show();
	}

	// Resolve the grouped connection definitions for a DocType from meta.
	connection_groups(doctype) {
		const meta = frappe.get_meta(doctype);
		const dash = (meta && meta.__dashboard) || {};
		let transactions = dash.transactions || [];

		if (!transactions.length && meta && meta.links && meta.links.length) {
			const by_group = {};
			meta.links.forEach((link) => {
				if (link.hidden || link.is_child_table) return;
				if (!link.link_doctype) return;
				const group = link.group || "";
				by_group[group] = by_group[group] || { label: group, items: [], fields: {} };
				if (by_group[group].items.indexOf(link.link_doctype) === -1) {
					by_group[group].items.push(link.link_doctype);
				}
				by_group[group].fields[link.link_doctype] = link.link_fieldname;
			});
			transactions = Object.keys(by_group).map((k) => by_group[k]);
		}

		// Ensure Project connection is available for Employee Onboarding
		if (doctype === "Employee Onboarding") {
			const has_project = transactions.some((g) => (g.items || []).includes("Project"));
			if (!has_project) {
				transactions = [
					{
						label: __("Connections"),
						items: ["Project"],
					},
					...transactions,
				];
			}
		}

		return transactions;
	}

	// The related fieldname used to filter a linked DocType back to this doc.
	connection_fieldname(doctype, linked_doctype) {
		const meta = frappe.get_meta(doctype) || {};
		const dash = meta.__dashboard || {};
		const link = (meta.links || []).find(
			(item) => item.link_doctype === linked_doctype && !item.hidden && !item.is_child_table
		);
		return (dash.non_standard_fieldnames && dash.non_standard_fieldnames[linked_doctype]) ||
			(link && link.link_fieldname) ||
			dash.fieldname ||
			null;
	}

	// Load & render the connection links (with counts) into the section body.
	render_connections(doctype, docname) {
		const self = this;
		const $section = this.$content.find("[data-connections]");
		if (!$section.length) return;
		const $body = $section.find("[data-connections-body]");

		const transactions = this.connection_groups(doctype);
		const items = [];
		transactions.forEach((group) => {
			(group.items || []).forEach((linked) => {
				if (items.indexOf(linked) === -1) items.push(linked);
			});
		});

		if (!items.length) {
			$body.html(`<div class="rcc-xform-connections-empty">${__("No connections")}</div>`);
			$section.find("[data-connections-count]").text("0");
			return;
		}

		// Build the link markup first (counts fill in progressively).
		const html = transactions
			.map((group) => {
				if (!group.items || !group.items.length) return "";
				const rows = group.items
					.map((linked) => {
						const can_create = frappe.model.can_create(linked);
						let label = __(linked);
						if (doctype === "Employee Onboarding" && linked === "Project") {
							const proj = (self.current_doc && self.current_doc.project) || "";
							if (proj) {
								label = `${__("Project")}: ${proj}`;
							}
						}
						return `
							<div class="rcc-conn-item">
								<div class="rcc-conn-link" data-conn-doctype="${frappe.utils.escape_html(linked)}" title="${frappe.utils.escape_html(__("Open {0}", [linked]))}">
									<span class="rcc-conn-link-icon">${frappe.rcc.icon(linked === "Project" ? "clipboard-list" : "link-2", 14)}</span>
									<span class="rcc-conn-link-label">${frappe.utils.escape_html(label)}</span>
									<span class="rcc-conn-link-count" data-conn-count="${frappe.utils.escape_html(linked)}">–</span>
								</div>
								${
									can_create
										? `<button type="button" class="rcc-conn-btn-add" data-conn-add="${frappe.utils.escape_html(linked)}" title="${frappe.utils.escape_html(__("Create new {0}", [linked]))}">
											${frappe.rcc.icon("plus", 12)}
										</button>`
										: ""
								}
							</div>`;
					})
					.join("");
				return `
					<div class="rcc-conn-group">
						${group.label ? `<div class="rcc-conn-group-title">${frappe.utils.escape_html(__(group.label))}</div>` : ""}
						<div class="rcc-conn-links">${rows}</div>
					</div>`;
			})
			.join("");
		$body.html(html);

		// Immediately set local counts if Employee Onboarding
		if (doctype === "Employee Onboarding") {
			const pCount = (self.current_doc && self.current_doc.project) ? 1 : 0;
			self.set_conn_count("Project", pCount);
		}

		// Fetch all counts in one call using the desk's own connection counter,
		// which handles internal/child links, permissions, and non-standard
		// fieldnames (and never throws "Field not permitted in query").
		frappe.xcall("frappe.desk.notifications.get_open_count", {
			doctype: doctype,
			name: docname,
		})
			.then((r) => {
				const count = (r && r.count) || {};
				const found = []
					.concat(count.external_links_found || [])
					.concat(count.internal_links_found || []);
				const by_doctype = {};
				found.forEach((row) => {
					if (row && row.doctype) by_doctype[row.doctype] = cint(row.count);
				});
				let total = 0;
				items.forEach((linked) => {
					let n = by_doctype[linked] || 0;
					if (doctype === "Employee Onboarding" && linked === "Project") {
						n = (self.current_doc && self.current_doc.project) ? 1 : 0;
					}
					self.set_conn_count(linked, n);
					total += n;
				});
				$section.find("[data-connections-count]").text(String(total));
			})
			.catch(() => {
				let total = 0;
				items.forEach((linked) => {
					let n = 0;
					if (doctype === "Employee Onboarding" && linked === "Project") {
						n = (self.current_doc && self.current_doc.project) ? 1 : 0;
					}
					self.set_conn_count(linked, n);
					total += n;
				});
				$section.find("[data-connections-count]").text(String(total));
			});
	}

	set_conn_count(linked, count) {
		const $section = this.$content.find("[data-connections]");
		$section.find(`[data-conn-count="${linked}"]`).text(String(count));
		$section
			.find(`.rcc-conn-link[data-conn-doctype="${linked}"]`)
			.toggleClass("is-empty", !count);
	}

	// Open a linked DocType and filter its middle-column records to this document.
	open_connection(linked_doctype) {
		const doctype = this.active_doctype;
		const doc = this.current_doc;
		if (!doc || !doc.name || !linked_doctype) return;

		// If viewing Employee Onboarding and clicking Project or Task connection, route directly to Onboarding Tasks
		if (doctype === "Employee Onboarding" && (linked_doctype === "Project" || linked_doctype === "Task")) {
			const project =
				(doc && doc.project) ||
				this.$content.find('.rcc-xform-field[data-fieldname="project"] input').val() ||
				"";
			if (project) {
				this.open_project_in_onboarding_tasks(project);
				return;
			} else {
				frappe.show_alert({
					message: __("No Project linked to this onboarding record."),
					indicator: "orange",
				});
				return;
			}
		}

		const fieldname = this.connection_fieldname(doctype, linked_doctype);
		if (!fieldname) {
			frappe.show_alert({ message: __("Unable to find the link field for {0}.", [__(linked_doctype)]), indicator: "red" });
			return;
		}
		this.select_doctype(linked_doctype, {
			source_doctype: doctype,
			source_name: doc.name,
			filters: { [fieldname]: doc.name },
		});
	}

	open_project_in_onboarding_tasks(project) {
		if (!project) return;
		const ctrl = this.ctrl || this.controller;
		if (ctrl && ctrl.switch_tab) {
			const ot_tab = ctrl.tabs && ctrl.tabs["Onboarding Tasks"];
			if (ot_tab) {
				ot_tab.pending_project_filter = project;
				ot_tab.filters.project = project;
				ot_tab.collapsed_projects[project] = false;
			}
			ctrl.switch_tab("Onboarding Tasks");
			if (ot_tab && ot_tab.filter_by_project) {
				ot_tab.filter_by_project(project);
			}
		}
	}

	// Create a new linked record from connection section (+)
	create_connected_record(linked_doctype) {
		const source_doctype = this.active_doctype;
		const source_doc = this.current_doc;
		if (!source_doc || !source_doc.name || !linked_doctype) return;

		if (!frappe.model.can_create(linked_doctype)) {
			frappe.show_alert({
				message: __("You do not have permission to create {0}.", [__(linked_doctype)]),
				indicator: "red",
			});
			return;
		}

		frappe.model.with_doctype(linked_doctype, () => {
			const defaults = this.get_connection_defaults(source_doctype, source_doc, linked_doctype);

			// If linked_doctype is one of the pipeline DocTypes available in this page
			if (this.form_view_doctypes && this.form_view_doctypes.includes(linked_doctype)) {
				this.select_doctype(linked_doctype);
				this.new_record(linked_doctype, defaults);
			} else if (linked_doctype === "Task" && this.controller && this.controller.tabs["Onboarding Tasks"]) {
				this.controller.switch_tab("Onboarding Tasks");
				const ot_tab = this.controller.tabs["Onboarding Tasks"];
				if (ot_tab && ot_tab.new_task) {
					ot_tab.new_task();
				}
			} else {
				// Outside the pipeline: redirect to original Frappe desk form with pre-populated values
				frappe.new_doc(linked_doctype, defaults);
			}
		});
	}

	get_connection_defaults(source_doctype, source_doc, target_doctype) {
		if (!source_doc || !source_doc.name) return {};
		const defaults = {};

		// 1. Try finding link field via dashboard definition
		let link_field = this.connection_fieldname(source_doctype, target_doctype);

		// 2. If not found, inspect target_doctype meta fields for Link to source_doctype
		if (!link_field && frappe.get_meta(target_doctype)) {
			const target_meta = frappe.get_meta(target_doctype);
			const matching_df = (target_meta.fields || []).find(
				(df) => df.fieldtype === "Link" && df.options === source_doctype
			);
			if (matching_df) {
				link_field = matching_df.fieldname;
			}
		}

		if (link_field) {
			defaults[link_field] = source_doc.name;
		}

		// 3. Inherit common contextual fields if target has them
		const target_meta = frappe.get_meta(target_doctype);
		if (target_meta && target_meta.fields) {
			const target_fields = target_meta.fields.map((f) => f.fieldname);
			["company", "department", "designation", "job_title"].forEach((f) => {
				if (target_fields.includes(f) && source_doc[f] && !defaults[f]) {
					defaults[f] = source_doc[f];
				}
			});
			if (source_doctype === "Job Opening") {
				if (target_fields.includes("job_title") && !defaults["job_title"]) {
					defaults["job_title"] = source_doc.name;
				}
				if (target_fields.includes("designation") && source_doc.designation) {
					defaults["designation"] = source_doc.designation;
				}
			}
			if (source_doctype === "Job Applicant") {
				if (target_fields.includes("job_applicant") && !defaults["job_applicant"]) {
					defaults["job_applicant"] = source_doc.name;
				}
				if (target_fields.includes("applicant_name") && source_doc.applicant_name) {
					defaults["applicant_name"] = source_doc.applicant_name;
				}
				if (target_fields.includes("job_opening") && source_doc.job_title) {
					defaults["job_opening"] = source_doc.job_title;
				}
			}
		}

		return defaults;
	}

	// Render a DocType's sections (with their column layout) into a container.
	render_form_sections(sections, $body) {
		sections.forEach((section) => {
			const $section = $('<div class="rcc-xform-section"></div>').appendTo($body);
			if (section.df && section.df.fieldname) {
				$section.attr("data-section-fieldname", section.df.fieldname);
			}
			if (section.df && section.df.depends_on) {
				$section.attr("data-depends-on", section.df.depends_on);
			}
			if (section.df && section.df.collapsible) {
				$section.addClass("is-collapsible");
				const is_collapsed = !!section.df.collapsed;
				if (is_collapsed) $section.addClass("is-collapsed");
				$section.append(`
					<div class="rcc-xform-section-head" data-section-toggle role="button" tabindex="0">
						<span class="rcc-xform-section-title">${frappe.utils.escape_html(__(section.label || "Details"))}</span>
						<span class="rcc-xform-section-chevron">${frappe.rcc.icon(is_collapsed ? "chevron-right" : "chevron-up", 14)}</span>
					</div>
				`);
			} else if (section.label) {
				$section.append(
					`<div class="rcc-xform-section-title">${frappe.utils.escape_html(__(section.label))}</div>`
				);
			}
			const $cols = $('<div class="rcc-xform-cols"></div>').appendTo($section);
			section.columns.forEach((col_fields) => {
				const $col = $('<div class="rcc-xform-col"></div>').appendTo($cols);
				col_fields.forEach((df) => {
					if (df.fieldtype === "Table") {
						this.render_child_table(df, $col);
						return;
					}
					const $field = $('<div class="rcc-xform-field"></div>').appendTo($col);
					$field.attr("data-fieldname", df.fieldname);
					if (df.depends_on) {
						$field.attr("data-depends-on", df.depends_on);
					} else if (
						this.current_doc &&
						this.current_doc.doctype === "Job Requisition" &&
						["requested_by_name", "requested_by_dept", "requested_by_designation"].includes(
							df.fieldname
						)
					) {
						$field.attr("data-depends-on", "requested_by");
					} else if (
						this.current_doc &&
						this.current_doc.doctype === "Interview" &&
						["job_opening", "designation"].includes(df.fieldname)
					) {
						$field.attr("data-depends-on", df.fieldname);
					}
					if (df.mandatory_depends_on) {
						$field.attr("data-mandatory-depends-on", df.mandatory_depends_on);
					}
					if (df.read_only_depends_on) {
						$field.attr("data-read-only-depends-on", df.read_only_depends_on);
					}
					this.make_field_control(df, $field);
				});
			});
		});
	}

	// Evaluate a DocField "depends_on" expression against the current doc.
	// Supports eval:... expressions and bare fieldnames (like "publish").
	evaluate_depends_on_value(expression, doc) {
		if (!expression) return true;
		if (!doc) doc = this.current_doc || {};

		let out = null;
		let parent = doc;

		if (typeof expression === "boolean") {
			return expression;
		}
		if (typeof expression === "function") {
			return expression(doc);
		}

		if (typeof expression === "string") {
			const trimmed = expression.trim();
			if (trimmed.startsWith("eval:")) {
				const code = trimmed.slice(5).trim();
				try {
					out = frappe.utils.eval(code, { doc, parent });
				} catch (e) {
					try {
						const fn = new Function("doc", "parent", "frappe", "return (" + code + ");");
						out = fn(doc, parent, frappe);
					} catch (err) {
						out = false;
					}
				}
				return !!out;
			}

			// Bare fieldname or negated fieldname (e.g. "publish", "!publish", "job_requisition")
			let fieldname = trimmed;
			let negate = false;
			if (fieldname.startsWith("!")) {
				negate = true;
				fieldname = fieldname.slice(1).trim();
			}

			const value = doc[fieldname];
			if (Array.isArray(value)) {
				out = !!value.length;
			} else if (value === null || value === undefined || value === "") {
				out = false;
			} else if (value === 0 || value === "0") {
				out = false;
			} else {
				out = !!value;
			}

			return negate ? !out : out;
		}

		return true;
	}

	// Show/hide fields, sections, tabs, and columns based on depends_on conditions.
	refresh_dependency() {
		const self = this;
		const doc = this.current_doc || {};

		// 1. Field-level depends_on
		this.$content.find(".rcc-xform-field[data-depends-on]").each(function () {
			const $field = $(this);
			const expr = $field.attr("data-depends-on");
			const visible = self.evaluate_depends_on_value(expr, doc);
			$field.toggle(visible);
		});

		// mandatory_depends_on
		this.$content.find(".rcc-xform-field[data-mandatory-depends-on]").each(function () {
			const $field = $(this);
			const fn = $field.attr("data-fieldname");
			const expr = $field.attr("data-mandatory-depends-on");
			const reqd = self.evaluate_depends_on_value(expr, doc);
			const ctrl = self.form_controls[fn];
			if (ctrl && ctrl.df) {
				ctrl.df.reqd = reqd ? 1 : 0;
				if (ctrl.refresh) ctrl.refresh();
			}
			$field.find("label.control-label .rcc-reqd").toggle(reqd);
		});

		// read_only_depends_on
		this.$content.find(".rcc-xform-field[data-read-only-depends-on]").each(function () {
			const $field = $(this);
			const fn = $field.attr("data-fieldname");
			const expr = $field.attr("data-read-only-depends-on");
			const read_only = self.evaluate_depends_on_value(expr, doc);
			const ctrl = self.form_controls[fn];
			if (ctrl && ctrl.df) {
				ctrl.df.read_only = read_only ? 1 : 0;
				if (ctrl.refresh) ctrl.refresh();
			}
		});

		// 2. Section-level depends_on
		this.$content.find(".rcc-xform-section[data-depends-on]").each(function () {
			const $sec = $(this);
			const expr = $sec.attr("data-depends-on");
			const visible = self.evaluate_depends_on_value(expr, doc);
			$sec.toggle(visible);
		});

		// 3. Tab-level depends_on
		this.$content.find(".rcc-xform-tab[data-depends-on]").each(function () {
			const $tab_btn = $(this);
			const expr = $tab_btn.attr("data-depends-on");
			const idx = $tab_btn.attr("data-form-tab");
			const visible = self.evaluate_depends_on_value(expr, doc);
			$tab_btn.toggle(visible);
			self.$content.find(`.rcc-xform-pane[data-form-pane="${idx}"]`).toggle(visible);
		});

		// 4. Hide section if all contained fields & tables are hidden *by an
		// explicit depends_on toggle*. NB: don't use jQuery ":visible" here — the
		// fields inside inactive tab panes (display:none) would all report hidden
		// and permanently collapse the whole section.
		const self_hidden = (el) => el.style && el.style.display === "none";
		this.$content.find(".rcc-xform-section").each(function () {
			const $sec = $(this);
			if ($sec.attr("data-depends-on") && self_hidden(this)) return;
			const items = $sec.find(".rcc-xform-field, .rcc-child-table").toArray();
			if (items.length > 0) {
				const has_visible = items.some((el) => !self_hidden(el));
				$sec.toggle(has_visible);
			}
		});

		// 5. Hide empty columns
		this.$content.find(".rcc-xform-col").each(function () {
			const $col = $(this);
			const items = $col
				.children(".rcc-xform-field, .rcc-child-table")
				.toArray();
			if (items.length) {
				const has_visible = items.some((el) => !self_hidden(el));
				$col.toggle(has_visible);
			}
		});
	}

	// Detail column heading: record title (prominent) + record id + state + actions.
	render_detail_head(doc, doctype) {
		const is_new = this.is_new_record;
		const meta = frappe.get_meta(doctype);
		const title_field = meta && meta.title_field;
		const title =
			(title_field && doc[title_field]) ||
			doc.designation ||
			doc.applicant_name ||
			doc.job_applicant ||
			doc.employee_name ||
			doc.name ||
			"";
		const primary = is_new ? `${__("New")} ${__(doctype)}` : title || __("Untitled");
		const secondary = is_new ? __("Unsaved") : title && title !== doc.name ? doc.name : "";

		const pills = [];
		const state = doc.status || doc.boarding_status;
		if (state) pills.push(this.status_pill(state));
		if (this.is_submittable && !is_new) pills.push(this.docstatus_pill(doc.docstatus));

		// Check write/create/cancel permissions before building action buttons.
		const can_write = frappe.model.can_write(doctype);
		const can_create = frappe.model.can_create(doctype);
		const can_cancel = frappe.model.can_cancel ? frappe.model.can_cancel(doctype) : can_write;

		const buttons = [];
		if (!is_new) {
			buttons.push(
				`<button class="btn btn-default btn-xs" data-open-full-form="${frappe.utils.escape_html(doc.name)}">${__("Open Original")}</button>`
			);
		}
		if (is_new && can_create) {
			buttons.push(`<button class="btn btn-primary btn-xs" data-save-form>${__("Create")}</button>`);
		} else if (!is_new && doc.docstatus === 0 && can_write) {
			buttons.push(`<button class="btn btn-primary btn-xs" data-save-form>${__("Save")}</button>`);
			if (this.is_submittable) {
				buttons.push(`<button class="btn btn-primary btn-xs" data-submit-form>${__("Submit")}</button>`);
			}
		} else if (!is_new && doc.docstatus === 1 && this.is_submittable && can_cancel) {
			buttons.push(`<button class="btn btn-danger btn-xs" data-cancel-form>${__("Cancel")}</button>`);
		} else if (
			!is_new &&
			frappe.rcc.AMENDABLE_FORM_DOCTYPES.includes(doctype) &&
			doc.docstatus === 2 &&
			can_create &&
			frappe.perm.has_perm(doctype, 0, "amend", doc)
		) {
			buttons.push(`<button class="btn btn-primary btn-xs" data-amend-form>${__("Amend")}</button>`);
		}

		this.$content.find("#rcc-detail-head").html(`
			<div class="rcc-detail-head-text">
				<span class="rcc-detail-head-designation">${frappe.utils.escape_html(primary)}</span>
				${
					secondary
						? `<span class="rcc-detail-head-name">${frappe.utils.escape_html(secondary)}</span>`
						: ""
				}
			</div>
			<div class="rcc-detail-head-actions">${pills.join("")}${buttons.join("")}</div>
		`);
	}

	// Draft / Submitted / Cancelled capsule for submittable DocTypes.
	docstatus_pill(docstatus) {
		const map = {
			0: { label: __("Draft"), color: "#b45309", bg: "#fef3c7", border: "#fde68a" },
			1: { label: __("Submitted"), color: "#15803d", bg: "#dcfce7", border: "#bbf7d0" },
			2: { label: __("Cancelled"), color: "#b91c1c", bg: "#fee2e2", border: "#fecaca" },
		};
		const c = map[docstatus] || map[0];
		return `<span class="rcc-status-pill" style="color:${c.color};background:${c.bg};border-color:${c.border};">${c.label}</span>`;
	}

	// Coloured status capsule.
	status_pill(status) {
		const key = status || "";
		const c = frappe.rcc.STATUS_COLORS[key] || {
			color: "#475569",
			bg: "#f1f5f9",
			border: "#e2e8f0",
		};
		return `<span class="rcc-status-pill" style="color:${c.color};background:${c.bg};border-color:${c.border};">${frappe.utils.escape_html(__(key || "—"))}</span>`;
	}

	// Four quick-glance cards shown above the form fields (per-DocType, with a default).
	summary_cards(doc) {
		const by_doctype = {
			"Job Opening": [
				{ label: "Job Title", value: doc.job_title },
				{ label: "Designation", value: doc.designation },
				{ label: "Company", value: doc.company },
				{ label: "Location", value: doc.location },
			],
			"Job Applicant": [
				{ label: "Applicant", value: doc.applicant_name },
				{ label: "Status", value: doc.status },
				{ label: "Job Opening", value: doc.job_title },
				{ label: "Source", value: doc.source },
			],
			"Interview": [
				{ label: "Job Applicant", value: doc.job_applicant },
				{ label: "Interview Round", value: doc.interview_round },
				{ label: "Scheduled On", value: doc.scheduled_on },
				{ label: "Status", value: doc.status },
			],
			"Interview Feedback": [
				{ label: "Interviewer", value: doc.interviewer },
				{ label: "Interview", value: doc.interview },
				{ label: "Result", value: doc.result },
				{ label: "Average Rating", value: doc.average_rating },
			],
			"Job Offer": [
				{ label: "Applicant", value: doc.applicant_name },
				{ label: "Designation", value: doc.designation },
				{ label: "Company", value: doc.company },
				{ label: "Status", value: doc.status },
			],
			"Appointment Letter": [
				{ label: "Applicant", value: doc.applicant_name },
				{ label: "Appointment Date", value: doc.appointment_date },
				{ label: "Company", value: doc.company },
				{ label: "Job Applicant", value: doc.job_applicant },
			],
			"Employee Onboarding": [
				{ label: "Employee Name", value: doc.employee_name },
				{ label: "Job Applicant", value: doc.job_applicant },
				{ label: "Date of Joining", value: doc.date_of_joining },
				{ label: "Boarding Status", value: doc.boarding_status },
			],
			"Employee": [
				{ label: "Employee Name", value: doc.employee_name },
				{ label: "Designation", value: doc.designation },
				{ label: "Department", value: doc.department },
				{ label: "Status", value: doc.status },
			],
		};
		const cards = by_doctype[doc.doctype] || [
			{ label: "Company", value: doc.company },
			{ label: "Department", value: doc.department },
			{ label: "Designation", value: doc.designation },
			{ label: "Owner", value: doc.owner ? frappe.user.full_name(doc.owner) : "" },
		];
		const html = cards
			.map(
				(c) => `<div class="rcc-summary-card">
					<div class="rcc-summary-label">${frappe.utils.escape_html(__(c.label))}</div>
					<div class="rcc-summary-value">${
						c.value
							? frappe.utils.escape_html(String(c.value))
							: '<span class="rcc-summary-empty">—</span>'
					}</div>
				</div>`
			)
			.join("");
		return `<div class="rcc-summary-cards">${html}</div>`;
	}

	// Build the field layout from DocType meta, honouring Section / Column / Tab
	// breaks so the inline form mirrors the real form's structure.
	build_form_tabs(doctype) {
		const meta = frappe.get_meta(doctype);
		const skip_types = [
			"HTML",
			"Button",
			"Image",
			"Heading",
			"Fold",
			"Table MultiSelect",
			"Code",
			"Geolocation",
		];
		const tabs = [];
		let tab = null;
		let section = null;
		let column = null;

		const start_tab = (label, tab_df) => {
			tab = { label: label || "", df: tab_df, sections: [] };
			tabs.push(tab);
			section = null;
			column = null;
		};
		const start_section = (label, sec_df) => {
			if (!tab) start_tab(__("Details"));
			section = { label: label || "", df: sec_df, columns: [] };
			tab.sections.push(section);
			column = null;
		};
		const start_column = () => {
			if (!section) start_section("");
			column = [];
			section.columns.push(column);
		};

		meta.fields.forEach((df) => {
			if (df.fieldtype === "Tab Break") {
				start_tab(df.label, df);
				return;
			}
			if (df.fieldtype === "Section Break") {
				start_section(df.label, df);
				return;
			}
			if (df.fieldtype === "Column Break") {
				start_column();
				return;
			}
			if (!tab) start_tab(__("Details"));
			if (!section) start_section("");
			if (!column) start_column();
			if (df.hidden || skip_types.indexOf(df.fieldtype) !== -1) return;
			column.push(df);
		});

		return tabs
			.map((t) => ({
				label: t.label,
				df: t.df,
				sections: t.sections
					.map((s) => ({
						label: s.label,
						df: s.df,
						columns: s.columns.filter((c) => c.length),
					}))
					.filter((s) => s.columns.length),
			}))
			.filter((t) => t.sections.length);
	}

	// Render a single field using a real Frappe form control so inputs, links,
	// date pickers, selects, etc. behave and look exactly like the desk form.
	make_field_control(df, $parent) {
		const self = this;
		// Clone the df so we can attach a per-field change hook without mutating meta.
		const field_df = $.extend({}, df);
		if (
			this.current_doc &&
			this.current_doc.doctype === "Job Requisition" &&
			["requested_by_name", "requested_by_dept", "requested_by_designation"].includes(df.fieldname)
		) {
			field_df.read_only = 1;
		}
		const original_change = field_df.change || field_df.onchange;
		field_df.change = function (e) {
			if (self.current_doc && df.fieldname) {
				self.current_doc[df.fieldname] = this.get_value();
			}
			if (original_change) original_change.apply(this, [e]);
			self.on_field_change(this.doc && this.doc.doctype, df.fieldname, this);
			self.refresh_dependency();
		};

		const control = frappe.ui.form.make_control({
			df: field_df,
			parent: $parent,
			doc: this.current_doc,
			render_input: true,
		});
		if (control) {
			this.form_controls[df.fieldname] = control;
			if (
				df.fieldname === "project" &&
				this.current_doc &&
				this.current_doc.doctype === "Employee Onboarding"
			) {
				if (control.$btn_open) {
					control.$btn_open.off("click").on("click", function (e) {
						e.preventDefault();
						e.stopPropagation();
						const val = control.get_value() || (self.current_doc && self.current_doc.project);
						if (val) {
							self.open_project_in_onboarding_tasks(val);
						}
					});
				}
			}
		}
	}

	// Reactive, per-DocType field behaviours (mirrors the desk form client scripts).
	on_field_change(doctype, fieldname, control) {
		if (doctype === "Job Requisition" && fieldname === "requested_by") {
			return this.jr_on_requested_by(control.doc);
		}
		if (doctype === "Job Opening") {
			if (fieldname === "designation" || fieldname === "company")
				return this.job_on_designation(control.doc);
			if (fieldname === "job_opening_template")
				return this.job_on_template(control.doc);
		}
		if (doctype === "Interview Feedback") {
			if (fieldname === "interview") return this.if_on_interview(control.doc);
			if (fieldname === "interview_round") return this.if_on_interview_round(control.doc);
		}
		if (doctype === "Job Offer") {
			if (fieldname === "job_applicant") return this.jo_on_applicant(control.doc);
			if (fieldname === "select_terms") return this.jo_on_select_terms(control.doc);
			if (fieldname === "job_offer_term_template") return this.jo_on_template(control.doc);
		}
		if (doctype === "Appointment Letter") {
			if (fieldname === "job_applicant") return this.al_on_applicant(control.doc);
			if (fieldname === "appointment_letter_template")
				return this.al_on_template(control.doc);
		}
		if (doctype === "Employee Onboarding") {
			if (fieldname === "job_applicant") return this.eo_on_applicant(control.doc);
			if (fieldname === "employee_onboarding_template")
				return this.eo_on_template(control.doc);
			if (fieldname === "project") {
				const val = (control && control.get_value()) || "";
				const $conn = this.$content.find('.rcc-conn-link[data-conn-doctype="Project"]');
				if ($conn.length) {
					$conn.find(".rcc-conn-link-label").text(val ? `${__("Project")}: ${val}` : __("Project"));
					this.set_conn_count("Project", val ? 1 : 0);
				}
			}
		}
		if (doctype === "Employee") {
			if (["first_name", "middle_name", "last_name"].indexOf(fieldname) !== -1)
				return this.emp_on_name(control.doc);
			if (
				["prefered_contact_email", "personal_email", "company_email", "user_id"].indexOf(
					fieldname
				) !== -1
			)
				return this.emp_on_contact(control.doc);
		}
	}

	set_job_requisition_requester_fields(doc, employee) {
		const fields = {
			requested_by_name: "employee_name",
			requested_by_dept: "department",
			requested_by_designation: "designation",
		};
		for (const [fieldname, employee_field] of Object.entries(fields)) {
			if (this.current_doc !== doc) return;
			const value = (employee && employee[employee_field]) || "";
			doc[fieldname] = value;
			const control = this.form_controls[fieldname];
			if (control && control.set_input) control.set_input(value);
			if (control && control.refresh) control.refresh();
		}
		this.refresh_dependency();
	}

	async jr_on_requested_by(doc, clear_existing = true) {
		if (!doc) return;
		const employee_name = doc.requested_by;
		if (clear_existing) this.set_job_requisition_requester_fields(doc, null);
		if (!employee_name || this.current_doc !== doc || doc.requested_by !== employee_name) return;

		try {
			const response = await frappe.db.get_value("Employee", employee_name, [
				"employee_name", "department", "designation",
			]);
			if (this.current_doc !== doc || doc.requested_by !== employee_name) return;
			this.set_job_requisition_requester_fields(doc, response && response.message);
		} catch (error) {
			if (this.current_doc === doc && doc.requested_by === employee_name) {
				frappe.show_alert({ message: __("Unable to load employee details."), indicator: "red" });
			}
		}
	}

	// Interview Feedback: pull round + applicant from the chosen Interview.
	if_on_interview(doc) {
		if (!doc || !doc.interview) return;
		const self = this;
		return frappe.db.get_doc("Interview", doc.interview).then(function (interview) {
			self.set_form_value("interview_round", interview.interview_round);
			self.set_form_value("job_applicant", interview.job_applicant);
		});
	}

	// Interview Feedback: seed the skill grid from the round's expected skills.
	if_on_interview_round(doc) {
		if (!doc || !doc.interview_round) return;
		const self = this;
		frappe.call({
			method: "hrms.hr.doctype.interview.interview.get_expected_skill_set",
			args: { interview_round: doc.interview_round },
			callback: function (r) {
				if (r && r.message) self.set_child_rows("skill_assessment", r.message);
			},
		});
	}

	// Job Offer: copy applicant details from the chosen Job Applicant.
	jo_on_applicant(doc) {
		if (!doc || !doc.job_applicant) return;
		const self = this;
		return frappe.db.get_doc("Job Applicant", doc.job_applicant).then(function (app) {
			self.set_form_value("applicant_name", app.applicant_name);
			self.set_form_value("applicant_email", app.email_id);
			self.set_form_value("designation", app.designation);
		});
	}

	// Job Offer: pull the text of the selected Terms and Conditions.
	jo_on_select_terms(doc) {
		if (!doc || !doc.select_terms) return;
		const self = this;
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Terms and Conditions",
				filters: { name: doc.select_terms },
				fieldname: "terms",
			},
			callback: function (r) {
				if (r && r.message && r.message.terms) self.set_form_value("terms", r.message.terms);
			},
		});
	}

	// Job Offer: seed the terms grid from a Job Offer Term Template.
	jo_on_template(doc) {
		if (!doc || !doc.job_offer_term_template) return;
		const self = this;
		return frappe.db
			.get_doc("Job Offer Term Template", doc.job_offer_term_template)
			.then(function (tpl) {
				self.set_child_rows("offer_terms", tpl.offer_terms || []);
			});
	}

	// Appointment Letter: copy the applicant name from the chosen Job Applicant.
	al_on_applicant(doc) {
		if (!doc || !doc.job_applicant) return;
		const self = this;
		return frappe.db.get_doc("Job Applicant", doc.job_applicant).then(function (app) {
			self.set_form_value("applicant_name", app.applicant_name);
		});
	}

	// Appointment Letter: load introduction / closing notes / terms from a template.
	al_on_template(doc) {
		if (!doc || !doc.appointment_letter_template) return;
		const self = this;
		frappe.call({
			method: "hrms.hr.doctype.appointment_letter.appointment_letter.get_appointment_letter_details",
			args: { template: doc.appointment_letter_template },
			callback: function (r) {
				const body = r && r.message;
				if (!body) return;
				self.set_form_value("introduction", body[0].introduction);
				self.set_form_value("closing_notes", body[0].closing_notes);
				self.set_child_rows("terms", (body[1] && body[1].description) || []);
			},
		});
	}

	// Employee Onboarding: sync employee name + linked Employee record.
	eo_on_applicant(doc) {
		if (!doc || !doc.job_applicant) {
			this.set_form_value("employee", "");
			return;
		}
		const self = this;
		frappe.db.get_doc("Job Applicant", doc.job_applicant).then(function (app) {
			self.set_form_value("employee_name", app.applicant_name);
		});
		frappe.db.get_value("Employee", { job_applicant: doc.job_applicant }, "name", function (r) {
			self.set_form_value("employee", (r && r.name) || "");
		});
	}

	// Employee Onboarding: pull department details + activities from a template.
	eo_on_template(doc) {
		if (!doc || !doc.employee_onboarding_template) return;
		const self = this;
		frappe.db
			.get_doc("Employee Onboarding Template", doc.employee_onboarding_template)
			.then(function (tpl) {
				self.set_form_value("company", tpl.company);
				self.set_form_value("department", tpl.department);
				self.set_form_value("designation", tpl.designation);
				self.set_form_value("employee_grade", tpl.employee_grade);
			});
		frappe.call({
			method: "hrms.controllers.employee_boarding_controller.get_onboarding_details",
			args: {
				parent: doc.employee_onboarding_template,
				parenttype: "Employee Onboarding Template",
			},
			callback: function (r) {
				if (r && r.message) self.set_child_rows("activities", r.message);
			},
		});
	}

	// Employee: keep the read-only full name in sync with the name parts.
	emp_on_name(doc) {
		const parts = [doc.first_name, doc.middle_name, doc.last_name].filter(Boolean);
		this.set_form_value("employee_name", parts.join(" "));
	}

	// Employee: mirror the preferred email based on the selected contact source.
	emp_on_contact(doc) {
		const key = frappe.model.scrub(doc.prefered_contact_email) || "user_id";
		this.set_form_value("prefered_email", doc[key] || "");
	}

	// Job Opening: fetch active staffing plan details for designation & company.
	job_on_designation(doc) {
		if (!doc) return;
		const self = this;
		if (doc.designation && doc.company) {
			frappe.call({
				method: "hrms.hr.doctype.staffing_plan.staffing_plan.get_active_staffing_plan_details",
				args: {
					company: doc.company,
					designation: doc.designation,
					date: frappe.datetime.now_date(),
				},
				callback: function (data) {
					if (data && data.message && data.message.length) {
						self.set_form_value("staffing_plan", data.message[0].name);
						self.set_form_value("planned_vacancies", data.message[0].vacancies);
					} else {
						self.set_form_value("staffing_plan", "");
						self.set_form_value("planned_vacancies", 0);
					}
				},
			});
		} else {
			self.set_form_value("staffing_plan", "");
			self.set_form_value("planned_vacancies", 0);
		}
	}

	job_on_company(doc) {
		this.set_form_value("designation", "");
	}

	// Job Opening: apply template defaults.
	job_on_template(doc) {
		if (!doc || !doc.job_opening_template) return;
		const self = this;
		frappe.db.get_doc("Job Opening Template", doc.job_opening_template).then((t) => {
			if (t.department) self.set_form_value("department", t.department);
			if (t.employment_type) self.set_form_value("employment_type", t.employment_type);
			if (t.location) self.set_form_value("location", t.location);
			if (t.description) self.set_form_value("description", t.description);
		});
	}

	// Set a scalar field's control (falls back to the model object).
	set_form_value(fieldname, value) {
		const control = this.form_controls[fieldname];
		if (control && control.set_value) {
			control.set_value(value);
		}
		if (this.current_doc) {
			this.current_doc[fieldname] = value;
		}
		this.refresh_dependency();
	}

	// Replace all rows of a rendered child table.
	set_child_rows(fieldname, rows) {
		const state = this.child_tables[fieldname];
		if (!state) return;
		state.rows = (rows || []).map((r) => $.extend({ doctype: state.doctype }, r));
		this.refresh_child_rows(fieldname);
	}

	// ---- Child tables -------------------------------------------------------

	// Render a Table field as a lightweight, bordered, editable grid (no desk frm needed).
	render_child_table(df, $parent) {
		const self = this;
		const child_doctype = df.options;
		const fieldname = df.fieldname;

		const state = { doctype: child_doctype, columns: [], rows: [] };
		this.child_tables[fieldname] = state;

		const existing = (this.current_doc && this.current_doc[fieldname]) || [];
		existing.forEach((row) => {
			state.rows.push($.extend({ doctype: child_doctype }, row));
		});

		const $wrap = $(`
			<div class="rcc-child-table" data-fieldname="${frappe.utils.escape_html(fieldname)}">
				<table class="rcc-child-grid">
					<thead class="rcc-child-cols"></thead>
					<tbody class="rcc-child-rows"></tbody>
				</table>
				<div class="rcc-child-empty">${__("No rows yet.")}</div>
				<div class="rcc-child-foot">
					<button type="button" class="btn btn-xs btn-default rcc-child-add">${frappe.rcc.icon("plus", 12)} ${__("Add Row")}</button>
				</div>
			</div>
		`).appendTo($parent);

		frappe.model.with_doctype(child_doctype, function () {
			const child_meta = frappe.get_meta(child_doctype);
			state.columns = ((child_meta && child_meta.fields) || []).filter(
				(f) =>
					f.in_list_view &&
					["Section Break", "Column Break", "Button", "HTML", "Heading"].indexOf(
						f.fieldtype
					) === -1
			);
			self.render_child_rows(fieldname, $wrap);
		});
	}

	// Grid cells render multi-line text fields as a single-line input (like the
	// desk grid does) so a long Description does not blow up the row height.
	make_child_cell_control(cdf, $cell, row) {
		const multiline = ["Text", "Small Text", "Long Text", "Text Editor", "Code"];
		if (
			multiline.indexOf(cdf.fieldtype) !== -1 ||
			(cdf.fieldtype === "Data" && cdf.options === "Text")
		) {
			return this.make_single_line_text_control(cdf, $cell, row);
		}
		return frappe.ui.form.make_control({
			df: cdf,
			parent: $cell,
			doc: row,
			render_input: true,
			only_input: true,
		});
	}

	// A lightweight single-line control shim with the same interface used by
	// capture_child_values / get_table_values (get_value + get_status).
	make_single_line_text_control(cdf, $cell, row) {
		const value = row[cdf.fieldname];
		const $input = $(
			`<input type="text" class="form-control rcc-child-line-input">`
		).appendTo($cell);
		if (value !== undefined && value !== null) {
			$input.val(value);
		}
		return {
			$input: $input,
			get_value() {
				return $input.val();
			},
			get_status() {
				return "Write";
			},
		};
	}

	render_child_rows(fieldname, $wrap) {
		const state = this.child_tables[fieldname];
		if (!state || !$wrap || !$wrap.length) return;

		const $cols = $wrap.find(".rcc-child-cols");
		const $rows = $wrap.find(".rcc-child-rows");
		$cols.empty();
		$rows.empty();

		const $head = $("<tr></tr>").appendTo($cols);
		state.columns.forEach((c) => {
			$(`<th>${frappe.utils.escape_html(__(c.label))}</th>`).appendTo($head);
		});
		$('<th class="rcc-child-col-action"></th>').appendTo($head);

		state.rows.forEach((row, index) => {
			row.__controls = {};
			const $row = $('<tr class="rcc-child-row"></tr>').appendTo($rows);
			state.columns.forEach((cdf) => {
				const $cell = $('<td></td>').appendTo($row);
				const control = this.make_child_cell_control(cdf, $cell, row);
				if (control) row.__controls[cdf.fieldname] = control;
			});
			const $action = $('<td class="rcc-child-col-action"></td>').appendTo($row);
			$(
				`<button type="button" class="rcc-child-edit" data-index="${index}" title="${__(
					"Edit"
				)}">${frappe.rcc.icon("pencil", 13)}</button>`
			).appendTo($action);
			$(
				`<button type="button" class="rcc-child-del" data-index="${index}" title="${__(
					"Remove"
				)}">${frappe.rcc.icon("trash-2", 12)}</button>`
			).appendTo($action);
		});

		$wrap.find(".rcc-child-empty").toggle(state.rows.length === 0);
	}

	// Open a modal with every remaining (non in_list_view) field of a child row,
	// mirroring the desk grid's expand/edit dialog.
	edit_child_row(fieldname, index) {
		const state = this.child_tables[fieldname];
		if (!state) return;
		this.capture_child_values(fieldname);
		const row = state.rows[index];
		if (!row) return;

		const self = this;
		frappe.model.with_doctype(state.doctype, function () {
			const child_meta = frappe.get_meta(state.doctype);
			const skip = ["Section Break", "Column Break", "Button", "HTML", "Heading", "Table"];
			const fields = ((child_meta && child_meta.fields) || []).filter(
				(f) => skip.indexOf(f.fieldtype) === -1 && !f.hidden
			);
			if (!fields.length) return;

			const d = new frappe.ui.Dialog({
				title: __("{0} — {1}", [__(state.doctype), index + 1]),
				size: "large",
				fields: fields.map((f) => $.extend({}, f)),
				primary_action_label: __("Update"),
				primary_action: function (values) {
					Object.keys(values).forEach((fn) => {
						row[fn] = values[fn];
					});
					d.hide();
					self.refresh_child_rows(fieldname);
				},
			});

			fields.forEach((f) => {
				if (row[f.fieldname] !== undefined) {
					d.set_value(f.fieldname, row[f.fieldname]);
				}
			});
			d.show();
		});
	}

	capture_child_values(fieldname) {
		const state = this.child_tables[fieldname];
		if (!state) return;
		state.rows.forEach((row) => {
			Object.keys(row.__controls || {}).forEach((fn) => {
				const control = row.__controls[fn];
				if (control && control.get_value) {
					row[fn] = control.get_value();
				}
			});
		});
	}

	add_child_row(fieldname) {
		const state = this.child_tables[fieldname];
		if (!state) return;
		this.capture_child_values(fieldname);
		state.rows.push({ doctype: state.doctype });
		this.refresh_child_rows(fieldname);
	}

	remove_child_row(fieldname, index) {
		const state = this.child_tables[fieldname];
		if (!state) return;
		this.capture_child_values(fieldname);
		state.rows.splice(index, 1);
		this.refresh_child_rows(fieldname);
	}

	refresh_child_rows(fieldname) {
		const $wrap = this.$content.find(`.rcc-child-table[data-fieldname="${fieldname}"]`);
		this.render_child_rows(fieldname, $wrap);
	}

	get_table_values(fieldname) {
		const state = this.child_tables[fieldname];
		if (!state) return [];
		return state.rows.map((row) => {
			const out = { doctype: state.doctype };
			const controls = row.__controls || {};
			Object.keys(controls).forEach((fn) => {
				const control = controls[fn];
				const status = control.get_status ? control.get_status() : "Write";
				const value = control.get_value();
				if (status === "Read" && (value === undefined || value === null || value === "")) {
					return;
				}
				if (value !== undefined) out[fn] = value;
			});
			if (row.name && String(row.name).indexOf("new-") !== 0) out.name = row.name;
			return out;
		});
	}

	// Scalar + child-table values currently entered in the form.
	collect_values() {
		const self = this;
		const values = {};
		Object.keys(this.form_controls).forEach((fieldname) => {
			const control = self.form_controls[fieldname];
			const status = control.get_status ? control.get_status() : "Write";
			const value = control.get_value();
			if (status === "Read") {
				// Read-only fields are usually computed server-side, but required
				// read-only fields (e.g. fetched links) still must be sent.
				if (value !== undefined && value !== null && value !== "") {
					values[fieldname] = value;
				}
				return;
			}
			if (value !== undefined) values[fieldname] = value;
		});
		Object.keys(this.child_tables).forEach((fieldname) => {
			values[fieldname] = self.get_table_values(fieldname);
		});
		return values;
	}

	// Persist only the editable controls; validation and permissions are enforced
	// server-side by frappe.client.set_value.
	save_record_form(doctype, name) {
		if (this.is_new_record) {
			return this.create_record_form(doctype);
		}

		const self = this;
		const values = this.collect_values();

		frappe.call({
			method: "frappe.client.set_value",
			args: { doctype: doctype, name: name, fieldname: values },
			freeze: true,
			freeze_message: __("Saving…"),
			callback: function (r) {
				if (r && r.message) {
					frappe.show_alert({ message: __("Saved"), indicator: "green" }, 3);
					self.current_doc = r.message;
					self.render_record_form(r.message, doctype);
					self.load_records(doctype);
					self.load_doctype_counts();
				}
			},
		});
	}

	// Insert a new record from the inline form; validations run server-side.
	create_record_form(doctype) {
		const self = this;
		const doc = this.collect_values();
		doc.doctype = doctype;
		if (
			frappe.rcc.AMENDABLE_FORM_DOCTYPES.includes(doctype) &&
			this.current_doc.amended_from
		) {
			doc.amended_from = this.current_doc.amended_from;
		}

		if (this.needs_name) {
			const name = (this.$content.find("#rcc-new-name").val() || "").trim();
			if (!name) {
				frappe.msgprint(__("Please enter a Name before saving."));
				return;
			}
			doc.__newname = name;
		}

		frappe.call({
			method: "frappe.client.insert",
			args: { doc: doc },
			freeze: true,
			freeze_message: __("Creating…"),
			callback: function (r) {
				if (r && r.message) {
					frappe.show_alert({ message: __("Created"), indicator: "green" }, 3);
					self.is_new_record = false;
					self.current_doc = r.message;
					self.render_record_form(r.message, doctype);
					self.load_records(doctype);
					self.load_doctype_counts();
				}
			},
		});
	}

	// Submit a saved (draft) submittable document; pending edits are saved first.
	submit_record_form(doctype, name) {
		const self = this;
		frappe.confirm(__("Submit this {0}?", [__(doctype)]), function () {
			const values = self.collect_values();
			frappe.call({
				method: "frappe.client.set_value",
				args: { doctype: doctype, name: name, fieldname: values },
				freeze: true,
				freeze_message: __("Submitting…"),
				callback: function (saved) {
					if (!saved || !saved.message) return;
					frappe.call({
						method: "frappe.client.submit",
						args: { doc: saved.message },
						freeze: true,
						freeze_message: __("Submitting…"),
						callback: function (r) {
							if (r && r.message) {
								frappe.show_alert({ message: __("Submitted"), indicator: "green" }, 3);
								self.current_doc = r.message;
								self.render_record_form(r.message, doctype);
								self.load_records(doctype);
							}
						},
					});
				},
			});
		});
	}

	// Cancel a submitted document.
	cancel_record_form(doctype, name) {
		const self = this;
		frappe.confirm(
			__("Cancel this {0}? This cannot be undone.", [__(doctype)]),
			function () {
				frappe.call({
					method: "frappe.client.cancel",
					args: { doctype: doctype, name: name },
					freeze: true,
					freeze_message: __("Cancelling…"),
					callback: function (r) {
						if (r && r.message) {
							frappe.show_alert({ message: __("Cancelled"), indicator: "orange" }, 3);
							self.current_doc = r.message;
							self.render_record_form(r.message, doctype);
							self.load_records(doctype);
						}
					},
				});
			}
		);
	}

	// Start an amended draft, preserving the original document's details and origin.
	amend_record_form(doctype, doc) {
		if (!frappe.rcc.AMENDABLE_FORM_DOCTYPES.includes(doctype) || !doc || doc.docstatus !== 2) return;
		if (!frappe.model.can_create(doctype) || !frappe.perm.has_perm(doctype, 0, "amend", doc)) return;

		const self = this;
		frappe.call({
			method: "frappe.client.is_document_amended",
			args: { doctype: doctype, docname: doc.name },
			callback: function (r) {
				if (self.current_doc !== doc || self.active_doctype !== doctype) return;
				if (r && r.message) {
					frappe.msgprint(__("This document has already been amended."));
					return;
				}
				const amended = frappe.model.copy_doc(doc, true);
				amended.amended_from = doc.name;
				self.$content.find(".rcc-record-item").removeClass("active");
				self.render_record_form(amended, doctype);
				if (self.needs_name) {
					const amendment_name = doc.amended_from && /-\d+$/.test(doc.name)
						? doc.name.replace(/-(\d+)$/, (_match, number) => `-${Number(number) + 1}`)
						: `${doc.name}-1`;
					self.$content.find("#rcc-new-name").val(amendment_name);
				}
			},
		});
	}
};
