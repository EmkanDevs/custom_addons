// Onboarding Tasks tab.
// Inlined into the page entry script (recruitment_control_center.js) at load time.

frappe.provide("frappe.rcc");

frappe.rcc.OnboardingTasksTab = class OnboardingTasksTab {
	constructor(controller) {
		this.ctrl = controller;
		this.data = null;
		this.view_mode = "hr_overview"; // "my_tasks" or "hr_overview"
		this.selected_task_id = null;
		this.filters = {
			search: "",
			status: "",
			assignee: "",
			employee: "",
			project: "",
		};
		this.collapsed_projects = {};
		this.is_saving = false;
		this.pending_project_filter = null;
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

		// View mode toggle (My Tasks / HR Overview)
		$(wrapper).on("click", ".rcc-ot-toggle-btn", function () {
			const view = $(this).attr("data-ot-view");
			if (view === self.view_mode) return;
			self.view_mode = view;
			$(wrapper).find(".rcc-ot-toggle-btn").removeClass("active");
			$(this).addClass("active");
			self.apply_filters_and_render();
		});

		// KPI Card Filter click
		$(wrapper).on("click", ".rcc-ot-kpi-card", function () {
			const target_status = $(this).attr("data-ot-status") ?? "";
			if (self.filters.status === target_status && target_status !== "") {
				// Toggle off if already selected
				self.filters.status = "";
			} else {
				self.filters.status = target_status;
			}
			$(wrapper).find("#rcc-ot-filter-status").val(self.filters.status);
			self.apply_filters_and_render();
		});

		// Filters
		$(wrapper).on("input", "#rcc-ot-filter-search", function () {
			self.filters.search = ($(this).val() || "").trim().toLowerCase();
			self.apply_filters_and_render();
		});

		$(wrapper).on("change", "#rcc-ot-filter-status", function () {
			self.filters.status = $(this).val();
			self.apply_filters_and_render();
		});

		$(wrapper).on("change", "#rcc-ot-filter-assignee", function () {
			self.filters.assignee = $(this).val();
			self.apply_filters_and_render();
		});

		$(wrapper).on("change", "#rcc-ot-filter-employee", function () {
			self.filters.employee = $(this).val();
			self.apply_filters_and_render();
		});

		// Filter reset
		$(wrapper).on("click", "#rcc-ot-filter-reset", function () {
			self.reset_filters();
		});

		// Clear active project filter
		$(wrapper).on("click", "#rcc-ot-clear-project-filter", function () {
			self.filters.project = "";
			self.pending_project_filter = null;
			self.apply_filters_and_render();
		});

		// Task selection in tree
		$(wrapper).on("click", ".rcc-ot-task-item", function () {
			const taskId = $(this).attr("data-task-id");
			self.select_task(taskId);
		});

		// Collapsible Connections section toggle
		$(wrapper).on("click", "[data-ot-connections-toggle]", function () {
			const $section = $(this).closest("[data-ot-connections]");
			const $body = $section.find("[data-ot-connections-body]");
			const expanded = $section.toggleClass("is-open").hasClass("is-open");
			$(this)
				.attr("aria-expanded", expanded ? "true" : "false")
				.find(".rcc-xform-connections-chevron")
				.html(frappe.rcc.icon(expanded ? "chevron-down" : "chevron-right", 14));
			$body.slideToggle(120);
			if (expanded && !$section.attr("data-loaded") && self.selected_task_id) {
				$section.attr("data-loaded", "1");
				self.render_task_connections("Task", self.selected_task_id);
			}
		});

		$(wrapper).on("keydown", "[data-ot-connections-toggle]", function (e) {
			if (e.key === "Enter" || e.key === " ") {
				e.preventDefault();
				$(this).trigger("click");
			}
		});

		$(wrapper).on("click", "[data-ot-conn-doctype]", function (e) {
			e.stopPropagation();
			self.open_task_connection(
				$(this).attr("data-ot-conn-doctype"),
				$(this).attr("data-ot-conn-task") || self.selected_task_id
			);
		});

		$(wrapper).on("click", "[data-ot-conn-add]", function (e) {
			e.stopPropagation();
			self.create_connected_record(
				$(this).attr("data-ot-conn-add"),
				$(this).attr("data-ot-conn-task") || self.selected_task_id
			);
		});

		// Accordion collapse/expand
		$(wrapper).on("click", ".rcc-ot-group-head", function (e) {
			if ($(e.target).closest(".rcc-ot-group-count").length) return;
			const groupKey = $(this).attr("data-group-key");
			self.collapsed_projects[groupKey] = !self.collapsed_projects[groupKey];
			self.update_group_collapse(groupKey);
		});

		// Save Task button
		$(wrapper).on("click", "#rcc-ot-btn-save-task", function () {
			self.save_current_task();
		});

		// Dependencies child table: add / remove rows
		$(wrapper).on("click", ".rcc-ot-child-add", function () {
			self.add_dependency_row();
		});
		$(wrapper).on("click", ".rcc-ot-child-del", function () {
			self.remove_dependency_row(cint($(this).closest(".rcc-ot-child-row").attr("data-index")));
		});

		// Open Original button
		$(wrapper).on("click", "#rcc-ot-btn-open-original", function () {
			if (self.selected_task_id) {
				frappe.set_route("Form", "Task", self.selected_task_id);
			}
		});

		// Color picker sync
		$(wrapper).on("input", "#rcc-ot-color-picker", function () {
			const val = $(this).val();
			$(wrapper).find("#rcc-ot-input-color").val(val);
			$(wrapper).find("#rcc-ot-color-preview").css("background-color", val);
		});

		$(wrapper).on("input", "#rcc-ot-input-color", function () {
			const val = $(this).val();
			$(wrapper).find("#rcc-ot-color-picker").val(val);
			$(wrapper).find("#rcc-ot-color-preview").css("background-color", val);
		});

		// Auto-populate completed details when marking completed
		$(wrapper).on("change", "#rcc-ot-form-status", function () {
			if ($(this).val() === "Completed") {
				const $completedBy = $(wrapper).find("#rcc-ot-form-completed-by");
				const $completedOn = $(wrapper).find("#rcc-ot-form-completed-on");
				const $progress = $(wrapper).find("#rcc-ot-form-progress");
				if (!$completedBy.val()) {
					$completedBy.val(frappe.session.user);
				}
				if (!$completedOn.val()) {
					$completedOn.val(frappe.datetime.get_today());
				}
				if (!$progress.val() || flt($progress.val()) < 100) {
					$progress.val(100);
				}
			}
		});
	}

	render() {
		this.$content.html(`
			<div class="rcc-ot-container">
				<!-- Header Row: Title & Subtitle + View Mode Switcher -->
				<div class="rcc-ot-header-row">
					<div>
						<h2 class="rcc-ot-title">${__("Employee Onboarding Tasks")}</h2>
						<div class="rcc-ot-subtitle">${__("Complete assigned work and monitor every employee onboarding project.")}</div>
					</div>
					<div class="rcc-ot-view-toggle">
						<button type="button" class="rcc-ot-toggle-btn ${this.view_mode === "my_tasks" ? "active" : ""}" data-ot-view="my_tasks">
							${__("My Tasks")}
						</button>
						<button type="button" class="rcc-ot-toggle-btn ${this.view_mode === "hr_overview" ? "active" : ""}" data-ot-view="hr_overview">
							${__("HR Overview")}
						</button>
					</div>
				</div>

				<!-- KPI Summary Cards (6 Cards) -->
				<div class="rcc-ot-kpi-grid">
					<div class="rcc-ot-kpi-card rcc-ot-card-blue ${!this.filters.status ? "active" : ""}" data-ot-status="" title="${__("All Tasks")}">
						<div class="rcc-ot-kpi-title">${__("TOTAL TASKS")}</div>
						<div class="rcc-ot-kpi-val" id="rcc-ot-kpi-total">-</div>
						<div class="rcc-ot-kpi-sub" id="rcc-ot-kpi-total-sub">${this.view_mode === "my_tasks" ? __("Assigned to you") : __("All onboarding tasks")}</div>
					</div>
					<div class="rcc-ot-kpi-card rcc-ot-card-slate ${this.filters.status === "Open" ? "active" : ""}" data-ot-status="Open" title="${__("Filter by: Open")}">
						<div class="rcc-ot-kpi-title">${__("OPEN")}</div>
						<div class="rcc-ot-kpi-val" id="rcc-ot-kpi-open">-</div>
						<div class="rcc-ot-kpi-sub">${__("Not started")}</div>
					</div>
					<div class="rcc-ot-kpi-card rcc-ot-card-cyan ${this.filters.status === "Working" ? "active" : ""}" data-ot-status="Working" title="${__("Filter by: Working")}">
						<div class="rcc-ot-kpi-title">${__("WORKING")}</div>
						<div class="rcc-ot-kpi-val" id="rcc-ot-kpi-working">-</div>
						<div class="rcc-ot-kpi-sub">${__("Currently active")}</div>
					</div>
					<div class="rcc-ot-kpi-card rcc-ot-card-purple ${this.filters.status === "Pending Review" ? "active" : ""}" data-ot-status="Pending Review" title="${__("Filter by: Pending Review")}">
						<div class="rcc-ot-kpi-title">${__("PENDING REVIEW")}</div>
						<div class="rcc-ot-kpi-val" id="rcc-ot-kpi-pending">-</div>
						<div class="rcc-ot-kpi-sub">${__("Awaiting approval")}</div>
					</div>
					<div class="rcc-ot-kpi-card rcc-ot-card-red ${this.filters.status === "Overdue" ? "active" : ""}" data-ot-status="Overdue" title="${__("Filter by: Overdue")}">
						<div class="rcc-ot-kpi-title">${__("OVERDUE")}</div>
						<div class="rcc-ot-kpi-val" id="rcc-ot-kpi-overdue">-</div>
						<div class="rcc-ot-kpi-sub">${__("Past due date")}</div>
					</div>
					<div class="rcc-ot-kpi-card rcc-ot-card-green ${this.filters.status === "Completed" ? "active" : ""}" data-ot-status="Completed" title="${__("Filter by: Completed")}">
						<div class="rcc-ot-kpi-title">${__("COMPLETED")}</div>
						<div class="rcc-ot-kpi-val" id="rcc-ot-kpi-completed">-</div>
						<div class="rcc-ot-kpi-sub">${__("Finished tasks")}</div>
					</div>
				</div>

				<!-- Filter Bar -->
				<div class="rcc-ot-filter-bar">
					<div class="rcc-ot-filter-group rcc-ot-filter-search-group">
						<label class="rcc-ot-filter-label">${__("SEARCH")}</label>
						<div class="rcc-ot-input-with-icon">
							<span class="rcc-ot-input-icon">${frappe.rcc.icon("search", 13)}</span>
							<input type="text" class="rcc-ot-input" id="rcc-ot-filter-search" placeholder="${__("Search task, employee or project")}" autocomplete="off" />
						</div>
					</div>

					<div class="rcc-ot-filter-group">
						<label class="rcc-ot-filter-label">${__("STATUS")}</label>
						<div class="rcc-select-wrapper">
							<select class="rcc-select" id="rcc-ot-filter-status">
								<option value="">${__("All Statuses")}</option>
								<option value="Open">${__("Open")}</option>
								<option value="Working">${__("Working")}</option>
								<option value="Pending Review">${__("Pending Review")}</option>
								<option value="Overdue">${__("Overdue")}</option>
								<option value="Completed">${__("Completed")}</option>
								<option value="Cancelled">${__("Cancelled")}</option>
							</select>
						</div>
					</div>

					<div class="rcc-ot-filter-group">
						<label class="rcc-ot-filter-label">${__("ASSIGNED TO")}</label>
						<div class="rcc-select-wrapper">
							<select class="rcc-select" id="rcc-ot-filter-assignee">
								<option value="">${__("All Assignees")}</option>
							</select>
						</div>
					</div>

					<div class="rcc-ot-filter-group">
						<label class="rcc-ot-filter-label">${__("EMPLOYEE")}</label>
						<div class="rcc-select-wrapper">
							<select class="rcc-select" id="rcc-ot-filter-employee">
								<option value="">${__("All Employees")}</option>
							</select>
						</div>
					</div>

					<button type="button" class="rcc-btn-reset rcc-ot-btn-reset" id="rcc-ot-filter-reset">
						${frappe.rcc.icon("rotate-ccw", 13)}
						<span>${__("Reset")}</span>
					</button>
				</div>

				<!-- Active Project Filter Bar -->
				<div class="rcc-ot-active-filter-bar" id="rcc-ot-active-filter-bar" style="display: none;">
					<span class="rcc-ot-active-filter-label">${__("Filtered by:")}</span>
					<span class="rcc-ot-filter-pill" id="rcc-ot-project-pill">
						<span class="rcc-ot-filter-pill-text"></span>
						<button type="button" class="rcc-ot-filter-pill-clear" id="rcc-ot-clear-project-filter" title="${__("Clear project filter")}">✕</button>
					</span>
				</div>

				<!-- Main Split View -->
				<div class="rcc-ot-main-split">
					<!-- Left Column: Projects & Tasks Tree -->
					<div class="rcc-ot-left-panel">
						<div class="rcc-ot-tree-head">
							<span>${__("Projects & Tasks")}</span>
							<span class="rcc-col-count" id="rcc-ot-tree-count">0 tasks</span>
						</div>
						<div class="rcc-ot-tree-body" id="rcc-ot-tree-body">
							<div class="rcc-loading">Loading tasks…</div>
						</div>
					</div>

					<!-- Right Column: Task Form Details -->
					<div class="rcc-ot-right-panel" id="rcc-ot-right-panel">
						<div class="rcc-placeholder">
							<div class="rcc-placeholder-icon">📋</div>
							<div class="rcc-placeholder-text">${__("Select an onboarding task to view and edit.")}</div>
						</div>
					</div>
				</div>
			</div>
		`);

		this.load_data();
	}

	load_data() {
		const self = this;
		frappe.call({
			method: "custom_addons.custom_addons.page.recruitment_control_center.recruitment_control_center.get_onboarding_tasks_data",
			callback: function (r) {
				if (r && r.message) {
					self.data = r.message;
					self.populate_filter_options();
					if (self.pending_project_filter) {
						self.filters.project = self.pending_project_filter;
						self.collapsed_projects[self.pending_project_filter] = false;
					}
					self.apply_filters_and_render();
				} else {
					self.$content.find("#rcc-ot-tree-body").html(
						frappe.rcc.placeholder("Unable to load onboarding tasks.")
					);
				}
			},
			error: function () {
				self.$content.find("#rcc-ot-tree-body").html(
					frappe.rcc.placeholder("Failed to fetch onboarding tasks.")
				);
			},
		});
	}

	populate_filter_options() {
		if (!this.data) return;

		// Assignees
		const $assignee = this.$content.find("#rcc-ot-filter-assignee");
		$assignee.find("option:not(:first)").remove();
		(this.data.assignees || []).forEach((a) => {
			$assignee.append(`<option value="${frappe.utils.escape_html(a)}">${frappe.utils.escape_html(a)}</option>`);
		});

		// Employees
		const $emp = this.$content.find("#rcc-ot-filter-employee");
		$emp.find("option:not(:first)").remove();
		(this.data.employees || []).forEach((e) => {
			$emp.append(`<option value="${frappe.utils.escape_html(e)}">${frappe.utils.escape_html(e)}</option>`);
		});
	}

	reset_filters() {
		this.filters = {
			search: "",
			status: "",
			assignee: "",
			employee: "",
			project: "",
		};
		this.pending_project_filter = null;
		const $c = this.$content;
		$c.find("#rcc-ot-filter-search").val("");
		$c.find("#rcc-ot-filter-status").val("");
		$c.find("#rcc-ot-filter-assignee").val("");
		$c.find("#rcc-ot-filter-employee").val("");
		this.apply_filters_and_render();
	}

	filter_by_project(project) {
		if (!project) return;
		this.pending_project_filter = project;
		this.filters.project = project;
		this.filters.search = "";
		this.filters.status = "";
		this.filters.assignee = "";
		this.filters.employee = "";
		this.view_mode = "hr_overview";

		const $c = this.$content;
		if ($c && $c.length) {
			$c.find(".rcc-ot-toggle-btn").removeClass("active");
			$c.find('.rcc-ot-toggle-btn[data-ot-view="hr_overview"]').addClass("active");
			$c.find("#rcc-ot-filter-search").val("");
			$c.find("#rcc-ot-filter-status").val("");
			$c.find("#rcc-ot-filter-assignee").val("");
			$c.find("#rcc-ot-filter-employee").val("");
		}

		// Ensure this project is expanded in tree
		this.collapsed_projects[project] = false;

		if (this.data && this.data.tasks) {
			this.apply_filters_and_render();
		}
	}

	get_filtered_tasks(ignore_status = false) {
		if (!this.data || !this.data.tasks) return [];
		const self = this;
		const user = this.data.current_user;

		return this.data.tasks.filter((t) => {
			// View mode filter (My Tasks)
			if (self.view_mode === "my_tasks") {
				const is_assigned = (t.assignees && t.assignees.indexOf(user) !== -1)
					|| (t.completed_by && t.completed_by === user);
				if (!is_assigned) return false;
			}

			// Text search
			if (self.filters.search) {
				const q = self.filters.search;
				const subj = (t.subject || "").toLowerCase();
				const emp = (t.employee_name || "").toLowerCase();
				const proj = (t.project_name || t.project || "").toLowerCase();
				const tid = (t.name || "").toLowerCase();
				if (!subj.includes(q) && !emp.includes(q) && !proj.includes(q) && !tid.includes(q)) {
					return false;
				}
			}

			// Status filter
			if (!ignore_status && self.filters.status) {
				if (self.filters.status === "Overdue") {
					if (!t.is_overdue) return false;
				} else if (t.status !== self.filters.status) {
					return false;
				}
			}

			// Assignee filter
			if (self.filters.assignee) {
				if (!t.assignees || t.assignees.indexOf(self.filters.assignee) === -1) {
					return false;
				}
			}

			// Employee filter
			if (self.filters.employee) {
				if (t.employee_name !== self.filters.employee) {
					return false;
				}
			}

			// Project filter
			if (self.filters.project) {
				const p = (self.filters.project + "").toLowerCase();
				const proj = (t.project || "").toLowerCase();
				const proj_name = (t.project_name || "").toLowerCase();
				if (proj !== p && proj_name !== p) {
					return false;
				}
			}

			return true;
		});
	}

	apply_filters_and_render() {
		const tasks_for_kpis = this.get_filtered_tasks(true);
		const filtered_tasks = this.get_filtered_tasks(false);
		this.update_kpis(tasks_for_kpis);
		this.render_tree(filtered_tasks);

		const $filterBar = this.$content.find("#rcc-ot-active-filter-bar");
		if (this.filters.project) {
			let projTitle = this.filters.project;
			if (this.data && this.data.tasks) {
				const match = this.data.tasks.find(
					(t) =>
						(t.project || "").toLowerCase() === (this.filters.project || "").toLowerCase() ||
						(t.project_name || "").toLowerCase() === (this.filters.project || "").toLowerCase()
				);
				if (match && match.project_name) {
					projTitle = match.project_name;
				}
			}
			$filterBar.find(".rcc-ot-filter-pill-text").text(__("Project: {0}", [projTitle]));
			$filterBar.show();
		} else {
			$filterBar.hide();
		}

		// Maintain selected task or pick first
		if (filtered_tasks.length > 0) {
			const exists = filtered_tasks.some((t) => t.name === this.selected_task_id);
			if (!exists || !this.selected_task_id) {
				this.selected_task_id = filtered_tasks[0].name;
			}
			const selectedTask = filtered_tasks.find((t) => t.name === this.selected_task_id);
			this.render_detail(selectedTask);
		} else {
			this.selected_task_id = null;
			this.render_empty_detail();
		}
	}

	update_kpis(tasks) {
		const $c = this.$content;
		let total = tasks.length;
		let open = 0;
		let working = 0;
		let pending = 0;
		let overdue = 0;
		let completed = 0;

		tasks.forEach((t) => {
			if (t.status === "Open") open++;
			else if (t.status === "Working") working++;
			else if (t.status === "Pending Review") pending++;
			else if (t.status === "Completed") completed++;

			if (t.is_overdue) overdue++;
		});

		$c.find("#rcc-ot-kpi-total").text(total);
		$c.find("#rcc-ot-kpi-total-sub").text(
			this.view_mode === "my_tasks" ? __("Assigned to you") : __("All onboarding tasks")
		);
		$c.find("#rcc-ot-kpi-open").text(open);
		$c.find("#rcc-ot-kpi-working").text(working);
		$c.find("#rcc-ot-kpi-pending").text(pending);
		$c.find("#rcc-ot-kpi-overdue").text(overdue);
		$c.find("#rcc-ot-kpi-completed").text(completed);

		// Highlight active card
		$c.find(".rcc-ot-kpi-card").removeClass("active");
		const current_status = this.filters.status || "";
		$c.find(`.rcc-ot-kpi-card[data-ot-status="${current_status}"]`).addClass("active");

		const tree_count = this.get_filtered_tasks(false).length;
		$c.find("#rcc-ot-tree-count").text(`${tree_count} ${tree_count === 1 ? __("task") : __("tasks")}`);
	}

	render_tree(tasks) {
		const $tree = this.$content.find("#rcc-ot-tree-body");

		if (!tasks || tasks.length === 0) {
			const empty_msg =
				this.view_mode === "my_tasks"
					? __("No tasks assigned to you.")
					: __("No onboarding tasks found matching filters.");
			$tree.html(
				`<div class="rcc-empty-state" style="padding: 30px 16px; text-align: center; color: #94a3b8; font-size: 13px;">` +
					`<div style="font-size: 24px; margin-bottom: 6px;">📂</div>` +
					`<div>${frappe.utils.escape_html(empty_msg)}</div>` +
				`</div>`
			);
			return;
		}

		// Group tasks by project
		const groups = {};
		tasks.forEach((t) => {
			const key = t.project || "other";
			if (!groups[key]) {
				groups[key] = {
					key: key,
					title: t.project_name || t.project || __("Employee Onboarding"),
					tasks: [],
				};
			}
			groups[key].tasks.push(t);
		});

		let html = "";
		const self = this;

		Object.values(groups).forEach((g) => {
			const is_collapsed = !!self.collapsed_projects[g.key];
			const count = g.tasks.length;
			const arrowIcon = is_collapsed
				? frappe.rcc.icon("chevron-right", 12)
				: frappe.rcc.icon("chevron-down", 12);

			html += `
				<div class="rcc-ot-group" data-group-wrap="${frappe.utils.escape_html(g.key)}">
					<div class="rcc-ot-group-head" data-group-key="${frappe.utils.escape_html(g.key)}">
						<div class="rcc-ot-group-title-wrap">
							<span class="rcc-ot-group-arrow">${arrowIcon}</span>
							<span class="rcc-ot-group-title" title="${frappe.utils.escape_html(g.title)}">${frappe.utils.escape_html(g.title)}</span>
						</div>
						<span class="rcc-ot-group-count">${count} ${count === 1 ? __("task") : __("tasks")}</span>
					</div>
					<div class="rcc-ot-group-items" style="${is_collapsed ? "display: none;" : ""}">
			`;

			g.tasks.forEach((t) => {
				const is_active = t.name === self.selected_task_id;
				const status_badge = t.is_overdue
					? `<span class="rcc-ot-badge rcc-ot-badge-overdue">${__("Overdue")}</span>`
					: `<span class="rcc-ot-badge rcc-ot-badge-status">${frappe.utils.escape_html(t.status)}</span>`;

				// Icon based on status / overdue
				let icon_html = "";
				if (t.is_overdue) {
					icon_html = `<span class="rcc-ot-task-icon rcc-ot-icon-overdue">${frappe.rcc.icon("triangle-alert", 13)}</span>`;
				} else if (t.status === "Completed") {
					icon_html = `<span class="rcc-ot-task-icon rcc-ot-icon-completed">${frappe.rcc.icon("check-circle", 13)}</span>`;
				} else {
					icon_html = `<span class="rcc-ot-task-icon rcc-ot-icon-normal">${frappe.rcc.icon("clipboard-list", 13)}</span>`;
				}

				html += `
					<div class="rcc-ot-task-item ${is_active ? "active" : ""}" data-task-id="${frappe.utils.escape_html(t.name)}">
						<div class="rcc-ot-task-top">
							<div class="rcc-ot-task-main">
								${icon_html}
								<div class="rcc-ot-task-title" title="${frappe.utils.escape_html(t.subject)}">
									${frappe.utils.escape_html(t.subject)}
								</div>
							</div>
							${status_badge}
						</div>
						<div class="rcc-ot-task-sub">
							<span>${frappe.utils.escape_html(t.status)}</span>
							<span class="rcc-ot-bullet">·</span>
							<span>${Math.round(t.progress || 0)}%</span>
							<span class="rcc-ot-bullet">·</span>
							<span class="rcc-ot-task-emp">${frappe.utils.escape_html(t.employee_name)}</span>
						</div>
					</div>
				`;
			});

			html += `
					</div>
				</div>
			`;
		});

		$tree.html(html);
	}

	update_group_collapse(groupKey) {
		const $c = this.$content;
		const $wrap = $c.find(`[data-group-wrap="${groupKey}"]`);
		const is_collapsed = !!this.collapsed_projects[groupKey];
		$wrap.find(".rcc-ot-group-items").slideToggle(150);
		$wrap
			.find(".rcc-ot-group-arrow")
			.html(
				is_collapsed
					? frappe.rcc.icon("chevron-right", 12)
					: frappe.rcc.icon("chevron-down", 12)
			);
	}

	select_task(taskId) {
		if (!this.data || !this.data.tasks) return;
		this.selected_task_id = taskId;
		this.$content.find(".rcc-ot-task-item").removeClass("active");
		this.$content.find(`.rcc-ot-task-item[data-task-id="${taskId}"]`).addClass("active");

		const task = this.data.tasks.find((t) => t.name === taskId);
		if (task) {
			this.render_detail(task);
		}
	}

	render_empty_detail() {
		this.$content.find("#rcc-ot-right-panel").html(`
			<div class="rcc-placeholder">
				<div class="rcc-placeholder-icon">📋</div>
				<div class="rcc-placeholder-text">${__("No task selected or matching current filter criteria.")}</div>
			</div>
		`);
	}

	// Collapsible Connections section shown above the task fields.
	connections_markup(task) {
		if (!task || !task.name) return "";
		return `
			<div class="rcc-xform-connections" data-ot-connections style="flex-shrink: 0;">
				<div class="rcc-xform-connections-head" data-ot-connections-toggle role="button" tabindex="0" aria-expanded="false">
					<span class="rcc-xform-connections-chevron">${frappe.rcc.icon("chevron-right", 14)}</span>
					<span class="rcc-xform-connections-title">${__("Connections")}</span>
					<span class="rcc-xform-connections-count" data-ot-connections-count>0</span>
				</div>
				<div class="rcc-xform-connections-body" data-ot-connections-body style="display: none;">
					<div data-ot-connections-transactions>
						<div class="rcc-xform-connections-loading">${__("Loading…")}</div>
					</div>
				</div>
			</div>`;
	}

	render_detail(task) {
		if (!task) {
			this.render_empty_detail();
			return;
		}

		const $right = this.$content.find("#rcc-ot-right-panel");

		// Status pill color — use the shared palette (matches ERP Task indicators).
		const status_color =
			frappe.rcc.STATUS_COLORS[task.status] || {
				color: "#475569",
				bg: "#f1f5f9",
				border: "#e2e8f0",
			};
		const status_pill = `<span class="rcc-status-pill" style="color:${status_color.color};background:${status_color.bg};border-color:${status_color.border};">${frappe.utils.escape_html(__(task.status || "—"))}</span>`;

		const overdue_tag = task.is_overdue
			? `<span class="rcc-ot-badge rcc-ot-badge-overdue" style="margin-left: 6px;">${__("Overdue")}</span>`
			: "";

		const exp_end_display = task.exp_end_date
			? frappe.datetime.str_to_user(task.exp_end_date)
			: __("Not Set");

		$right.html(`
			<!-- Detail Header -->
			<div class="rcc-ot-detail-head">
				<div class="rcc-ot-detail-head-left">
					<div class="rcc-ot-detail-title-row">
						<h3 class="rcc-ot-detail-title">${frappe.utils.escape_html(task.subject)}</h3>
						${status_pill}
						${overdue_tag}
					</div>
					<div class="rcc-ot-detail-id-row">
						<a href="/app/task/${frappe.utils.escape_html(task.name)}" class="rcc-ot-task-id-link" target="_blank">
							${frappe.utils.escape_html(task.name)}
						</a>
					</div>
				</div>
				<div class="rcc-ot-detail-head-right">
					<button type="button" class="btn btn-default btn-xs" id="rcc-ot-btn-open-original">
						${frappe.rcc.icon("external-link", 13)} <span>${__("Open Original")}</span>
					</button>
					<button type="button" class="btn btn-primary btn-xs" id="rcc-ot-btn-save-task">
						${frappe.rcc.icon("save", 13)} <span>${__("Save Task")}</span>
					</button>
				</div>
			</div>

			<!-- Detail Body -->
			<div class="rcc-ot-detail-body">
				<!-- Section 1: Overview (summary cards, matching the workspace tab) -->
				<div class="rcc-summary-cards rcc-ot-summary-cards">
					<div class="rcc-summary-card">
						<div class="rcc-summary-label">${__("Employee")}</div>
						<div class="rcc-summary-value">${frappe.utils.escape_html(task.employee_name || "Candidate")}</div>
					</div>
					<div class="rcc-summary-card">
						<div class="rcc-summary-label">${__("Employee Onboarding")}</div>
						<div class="rcc-summary-value">
							${
								task.onboarding_id
									? `<a href="/app/employee-onboarding/${frappe.utils.escape_html(task.onboarding_id)}" target="_blank" class="rcc-ot-link">${frappe.utils.escape_html(task.onboarding_id)}</a>`
									: `<span class="rcc-summary-empty">—</span>`
							}
						</div>
					</div>
					<div class="rcc-summary-card">
						<div class="rcc-summary-label">${__("Project")}</div>
						<div class="rcc-summary-value">
							${
								task.project
									? `<a href="/app/project/${frappe.utils.escape_html(task.project)}" target="_blank" class="rcc-ot-link" title="${frappe.utils.escape_html(task.project_name)}">${frappe.utils.escape_html(task.project_name)}</a>`
									: `<span class="rcc-summary-empty">—</span>`
							}
						</div>
					</div>
					<div class="rcc-summary-card">
						<div class="rcc-summary-label">${__("Expected End Date")}</div>
						<div class="rcc-summary-value ${task.is_overdue ? "rcc-ot-val-overdue" : ""}">
							${
								task.exp_end_date
									? frappe.utils.escape_html(exp_end_display)
									: `<span class="rcc-summary-empty">—</span>`
							}
						</div>
					</div>
				</div>

				${this.connections_markup(task)}

				<!-- Section 2: Basic Details -->
				<div class="rcc-ot-section">
					<div class="rcc-ot-section-heading">
						${__("Details")}
					</div>
					<div class="rcc-ot-form-grid">
						<div class="rcc-ot-field full-width">
							<label class="rcc-ot-label">${__("Subject")} <span class="text-danger">*</span></label>
							<input type="text" class="rcc-ot-form-input" id="rcc-ot-form-subject" value="${frappe.utils.escape_html(task.subject)}" />
						</div>

						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Project")}</label>
							<input type="text" class="rcc-ot-form-input" id="rcc-ot-form-project" value="${frappe.utils.escape_html(task.project_name)}" readonly disabled />
						</div>
						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Issue")}</label>
							<input type="text" class="rcc-ot-form-input" id="rcc-ot-form-issue" value="${frappe.utils.escape_html(task.issue || "")}" placeholder="${__("Issue link")}" />
						</div>

						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Type")}</label>
							<input type="text" class="rcc-ot-form-input" id="rcc-ot-form-type" value="${frappe.utils.escape_html(task.type || "")}" placeholder="${__("Task Type")}" />
						</div>
						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Color")}</label>
							<div class="rcc-ot-color-input-wrap">
								<input type="color" class="rcc-ot-color-picker" id="rcc-ot-color-picker" value="${task.color || "#dbeafe"}" />
								<input type="text" class="rcc-ot-form-input" id="rcc-ot-input-color" value="${frappe.utils.escape_html(task.color || "#dbeafe")}" />
							</div>
						</div>

						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Status")}</label>
							<select class="rcc-select" id="rcc-ot-form-status">
								<option value="Open" ${task.status === "Open" ? "selected" : ""}>Open</option>
								<option value="Working" ${task.status === "Working" ? "selected" : ""}>Working</option>
								<option value="Pending Review" ${task.status === "Pending Review" ? "selected" : ""}>Pending Review</option>
								<option value="Overdue" ${task.status === "Overdue" ? "selected" : ""}>Overdue</option>
								<option value="Template" ${task.status === "Template" ? "selected" : ""}>Template</option>
								<option value="Completed" ${task.status === "Completed" ? "selected" : ""}>Completed</option>
								<option value="Cancelled" ${task.status === "Cancelled" ? "selected" : ""}>Cancelled</option>
							</select>
						</div>
						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Priority")}</label>
							<select class="rcc-select" id="rcc-ot-form-priority">
								<option value="Low" ${task.priority === "Low" ? "selected" : ""}>Low</option>
								<option value="Medium" ${task.priority === "Medium" ? "selected" : ""}>Medium</option>
								<option value="High" ${task.priority === "High" ? "selected" : ""}>High</option>
								<option value="Urgent" ${task.priority === "Urgent" ? "selected" : ""}>Urgent</option>
							</select>
						</div>

						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Parent Task")}</label>
							<input type="text" class="rcc-ot-form-input" id="rcc-ot-form-parent" value="${frappe.utils.escape_html(task.parent_task || "")}" placeholder="${__("Not Set")}" />
						</div>
						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Is Group")}</label>
							<label class="rcc-ot-checkbox">
								<input type="checkbox" id="rcc-ot-form-is-group" ${task.is_group ? "checked" : ""} />
								<span>${__("Is Group")}</span>
							</label>
						</div>
					</div>
				</div>

				<!-- Section 3: Timeline -->
				<div class="rcc-ot-section">
					<div class="rcc-ot-section-heading">
						${__("Timeline")}
					</div>
					<div class="rcc-ot-form-grid">
						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Expected Start Date")}</label>
							<input type="date" class="rcc-date-input" id="rcc-ot-form-exp-start" value="${task.exp_start_date || ""}" />
						</div>
						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Expected End Date")}</label>
							<input type="date" class="rcc-date-input" id="rcc-ot-form-exp-end" value="${task.exp_end_date || ""}" />
						</div>

						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Expected Time (in hours)")}</label>
							<input type="number" class="rcc-ot-form-input" id="rcc-ot-form-expected-time" value="${task.expected_time || 0}" step="any" min="0" />
						</div>
						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Weight")}</label>
							<input type="number" class="rcc-ot-form-input" id="rcc-ot-form-weight" value="${task.weight || 0}" step="any" />
						</div>

						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Progress (%)")}</label>
							<input type="number" min="0" max="100" class="rcc-ot-form-input" id="rcc-ot-form-progress" value="${task.progress || 0}" />
						</div>
						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Is Milestone")}</label>
							<label class="rcc-ot-checkbox">
								<input type="checkbox" id="rcc-ot-form-is-milestone" ${task.is_milestone ? "checked" : ""} />
								<span>${__("Is Milestone")}</span>
							</label>
						</div>
					</div>
				</div>

				<!-- Section 4: Task Description -->
				<div class="rcc-ot-section">
					<div class="rcc-ot-section-heading">
						${__("Task Description")}
					</div>
					<div class="rcc-ot-form-grid">
						<div class="rcc-ot-field full-width">
							<textarea class="rcc-ot-form-textarea" id="rcc-ot-form-description" rows="4" placeholder="${__("Add notes or task instructions...")}">${frappe.utils.escape_html(task.description || "")}</textarea>
						</div>
					</div>
				</div>

				<!-- Section 4: Dependencies -->
				<div class="rcc-ot-section">
					<div class="rcc-ot-section-heading">
						${__("Dependencies")}
					</div>
					<div class="rcc-ot-child-table" data-child-table="depends_on">
						<table class="rcc-ot-child-grid">
							<thead>
								<tr>
									<th class="rcc-ot-child-col-task">${__("Task")}</th>
									<th class="rcc-ot-child-col-subject">${__("Subject")}</th>
									<th class="rcc-ot-child-col-project">${__("Project")}</th>
									<th class="rcc-ot-child-col-action"></th>
								</tr>
							</thead>
							<tbody class="rcc-ot-child-rows"></tbody>
						</table>
						<div class="rcc-ot-child-empty">${__("No dependencies.")}</div>
						<div class="rcc-ot-child-foot">
							<button type="button" class="btn btn-xs btn-default rcc-ot-child-add">${frappe.rcc.icon("plus", 12)} ${__("Add Row")}</button>
						</div>
					</div>
				</div>

				<!-- Section 5: Actual (via Timesheet) -->
				<div class="rcc-ot-section">
					<div class="rcc-ot-section-heading">
						${__("Actual (via Timesheet)")}
					</div>
					<div class="rcc-ot-form-grid">
						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Actual Start Date")}</label>
							<input type="text" class="rcc-ot-form-input" value="${frappe.utils.escape_html(task.act_start_date || "")}" readonly disabled />
						</div>
						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Actual End Date")}</label>
							<input type="text" class="rcc-ot-form-input" value="${frappe.utils.escape_html(task.act_end_date || "")}" readonly disabled />
						</div>
						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Actual Time in Hours")}</label>
							<input type="text" class="rcc-ot-form-input" value="${task.actual_time || 0}" readonly disabled />
						</div>
					</div>
				</div>

				<!-- Section 6: Costing -->
				<div class="rcc-ot-section">
					<div class="rcc-ot-section-heading">
						${__("Costing")}
					</div>
					<div class="rcc-ot-form-grid">
						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Total Costing Amount (via Timesheet)")}</label>
							<input type="text" class="rcc-ot-form-input" value="${task.total_costing_amount || 0}" readonly disabled />
						</div>
						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Total Billable Amount (via Timesheet)")}</label>
							<input type="text" class="rcc-ot-form-input" value="${task.total_billing_amount || 0}" readonly disabled />
						</div>
					</div>
				</div>

				<!-- Section 7: More Info -->
				<div class="rcc-ot-section">
					<div class="rcc-ot-section-heading">
						${__("More Info")}
					</div>
					<div class="rcc-ot-form-grid">
						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Review Date")}</label>
							<input type="date" class="rcc-date-input" id="rcc-ot-form-review-date" value="${task.review_date || ""}" />
						</div>
						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Closing Date")}</label>
							<input type="date" class="rcc-date-input" id="rcc-ot-form-closing-date" value="${task.closing_date || ""}" />
						</div>

						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Company")}</label>
							<input type="text" class="rcc-ot-form-input" id="rcc-ot-form-company" value="${frappe.utils.escape_html(task.company || "")}" />
						</div>
						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Department")}</label>
							<input type="text" class="rcc-ot-form-input" id="rcc-ot-form-department" value="${frappe.utils.escape_html(task.department || "")}" />
						</div>

						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Completed By")}</label>
							<input type="text" class="rcc-ot-form-input" id="rcc-ot-form-completed-by" value="${frappe.utils.escape_html(task.completed_by || "")}" />
						</div>
						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Completed On")}</label>
							<input type="date" class="rcc-date-input" id="rcc-ot-form-completed-on" value="${task.completed_on || ""}" />
						</div>

						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Is Template")}</label>
							<label class="rcc-ot-checkbox">
								<input type="checkbox" id="rcc-ot-form-is-template" ${task.is_template ? "checked" : ""} />
								<span>${__("Is Template")}</span>
							</label>
						</div>
						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Begin On (Days)")}</label>
							<input type="number" class="rcc-ot-form-input" id="rcc-ot-form-start" value="${task.start || 0}" min="0" />
						</div>

						<div class="rcc-ot-field">
							<label class="rcc-ot-label">${__("Duration (Days)")}</label>
							<input type="number" class="rcc-ot-form-input" id="rcc-ot-form-duration" value="${task.duration || 0}" min="0" />
						</div>
					</div>
				</div>

			</div>
		`);

		this.render_dependencies(task);
		$right.find("[data-ot-connections]").attr("data-loaded", "1");
		this.render_task_connections("Task", task.name);
	}

	// Dependencies child table (Task Depends On): editable rows of dependency tasks.
	render_dependencies(task) {
		const rows = task.depends_on || [];
		this.depends_on_rows = rows.map((r) => ({
			task: r.task || "",
			subject: r.subject || "",
			project: r.project || "",
		}));
		this.refresh_dependency_rows();
	}

	refresh_dependency_rows() {
		const $wrap = this.$content.find('[data-child-table="depends_on"]');
		if (!$wrap.length) return;
		const rows = this.depends_on_rows || [];
		const $rows = $wrap.find(".rcc-ot-child-rows");
		$rows.empty();
		this.depends_on_controls = [];

		if (!rows.length) {
			$wrap.find(".rcc-ot-child-empty").show();
			return;
		}
		$wrap.find(".rcc-ot-child-empty").hide();

		rows.forEach((row, i) => {
			const $row = $(`
				<tr class="rcc-ot-child-row" data-index="${i}">
					<td class="rcc-ot-child-col-task"><div class="rcc-ot-dep-task-control"></div></td>
					<td class="rcc-ot-child-col-subject"><span class="rcc-ot-dep-readonly rcc-ot-dep-subject">${frappe.utils.escape_html(row.subject || "")}</span></td>
					<td class="rcc-ot-child-col-project"><span class="rcc-ot-dep-readonly rcc-ot-dep-project">${frappe.utils.escape_html(row.project || "")}</span></td>
					<td class="rcc-ot-child-col-action">
						<button type="button" class="btn btn-xs btn-default rcc-ot-child-del" title="${__("Remove")}">${frappe.rcc.icon("trash-2", 12)}</button>
					</td>
				</tr>
			`);
			$rows.append($row);
			this.make_dependency_link_control($row, row, i);
		});
	}

	// Task link field inside a dependency row (Link → Task, matching the desk grid).
	make_dependency_link_control($row, row, index) {
		const self = this;
		const $host = $row.find(".rcc-ot-dep-task-control");
		const df = {
			fieldname: "task",
			fieldtype: "Link",
			options: "Task",
			label: __("Task"),
			placeholder: __("Task"),
			reqd: 1,
			onchange: function () {
				self.on_dependency_task_change(index, this.get_value ? this.get_value() : this.value);
			},
		};
		frappe.model.with_doctype("Task", function () {
			if (!$host.length || !$host.closest("body").length) return;
			const control = frappe.ui.form.make_control({
				df: df,
				parent: $host,
				render_input: true,
			});
			if (control) {
				self.depends_on_controls[index] = control;
				self.position_dependency_dropdown(control);
				if (row.task) control.set_value(row.task);
			}
		});
	}

	// The row/table and scroll container clip the absolutely-positioned
	// autocomplete list, so fly it out with position:fixed while open.
	position_dependency_dropdown(control) {
		const $input = control.$input;
		if (!$input || !$input.length) return;
		const reposition = () => {
			const dropdown = control.awesomplete && control.awesomplete.ul;
			if (!dropdown) return;
			const rect = $input[0].getBoundingClientRect();
			dropdown.style.position = "fixed";
			dropdown.style.top = rect.bottom + 2 + "px";
			dropdown.style.left = rect.left + "px";
			dropdown.style.width = Math.max(rect.width, 240) + "px";
			dropdown.style.zIndex = "1060";
		};
		$input.on("awesomplete-open", reposition);
		$input.on("input", function () {
			if (control.autocomplete_open) reposition();
		});
	}

	// Fetch subject + project for the selected dependency task and fill read-only cells.
	on_dependency_task_change(index, task_name) {
		const self = this;
		const $row = this.$content.find(
			`[data-child-table="depends_on"] .rcc-ot-child-row[data-index="${index}"]`
		);
		if (!$row.length) return;

		if (this.depends_on_rows[index]) {
			this.depends_on_rows[index].task = task_name || "";
		}

		if (!task_name) {
			$row.find(".rcc-ot-dep-subject").text("");
			$row.find(".rcc-ot-dep-project").text("");
			if (this.depends_on_rows[index]) {
				this.depends_on_rows[index].subject = "";
				this.depends_on_rows[index].project = "";
			}
			return;
		}

		frappe.db.get_value("Task", task_name, ["subject", "project"]).then(function (r) {
			const d = (r && r.message) || {};
			$row.find(".rcc-ot-dep-subject").text(d.subject || "");
			$row.find(".rcc-ot-dep-project").text(d.project || "");
			if (self.depends_on_rows[index]) {
				self.depends_on_rows[index].subject = d.subject || "";
				self.depends_on_rows[index].project = d.project || "";
			}
		});
	}

	collect_dependency_rows() {
		const rows = [];
		const self = this;
		this.$content.find('[data-child-table="depends_on"] .rcc-ot-child-row').each(function () {
			const index = cint($(this).attr("data-index"));
			const control = self.depends_on_controls[index];
			const task = (control && control.get_value ? control.get_value() : "") || "";
			rows.push({
				doctype: "Task Depends On",
				task: task,
				subject: ($(this).find(".rcc-ot-dep-subject").text() || "").trim(),
				project: ($(this).find(".rcc-ot-dep-project").text() || "").trim(),
			});
		});
		return rows;
	}

	add_dependency_row() {
		this.depends_on_rows = this.collect_dependency_rows();
		this.depends_on_rows.push({ task: "", subject: "", project: "" });
		this.refresh_dependency_rows();
	}

	remove_dependency_row(index) {
		this.depends_on_rows = this.collect_dependency_rows();
		this.depends_on_rows.splice(index, 1);
		this.refresh_dependency_rows();
	}

	save_current_task() {
		if (!this.selected_task_id || this.is_saving) return;

		const $c = this.$content;
		const subject = ($c.find("#rcc-ot-form-subject").val() || "").trim();
		if (!subject) {
			frappe.msgprint(__("Subject is required."));
			return;
		}

		const values = {
			subject: subject,
			issue: ($c.find("#rcc-ot-form-issue").val() || "").trim(),
			type: $c.find("#rcc-ot-form-type").val(),
			color: $c.find("#rcc-ot-input-color").val(),
			status: $c.find("#rcc-ot-form-status").val(),
			priority: $c.find("#rcc-ot-form-priority").val(),
			weight: flt($c.find("#rcc-ot-form-weight").val()),
			parent_task: ($c.find("#rcc-ot-form-parent").val() || "").trim(),
			progress: flt($c.find("#rcc-ot-form-progress").val()),
			exp_start_date: $c.find("#rcc-ot-form-exp-start").val(),
			exp_end_date: $c.find("#rcc-ot-form-exp-end").val(),
			expected_time: flt($c.find("#rcc-ot-form-expected-time").val()),
			is_group: $c.find("#rcc-ot-form-is-group").is(":checked") ? 1 : 0,
			is_milestone: $c.find("#rcc-ot-form-is-milestone").is(":checked") ? 1 : 0,
			review_date: $c.find("#rcc-ot-form-review-date").val(),
			closing_date: $c.find("#rcc-ot-form-closing-date").val(),
			company: ($c.find("#rcc-ot-form-company").val() || "").trim(),
			department: ($c.find("#rcc-ot-form-department").val() || "").trim(),
			completed_by: ($c.find("#rcc-ot-form-completed-by").val() || "").trim(),
			completed_on: $c.find("#rcc-ot-form-completed-on").val(),
			is_template: $c.find("#rcc-ot-form-is-template").is(":checked") ? 1 : 0,
			start: cint($c.find("#rcc-ot-form-start").val()),
			duration: cint($c.find("#rcc-ot-form-duration").val()),
			description: $c.find("#rcc-ot-form-description").val(),
			depends_on: this.collect_dependency_rows(),
		};

		const self = this;
		this.is_saving = true;
		const $btn = $c.find("#rcc-ot-btn-save-task");
		const original_text = $btn.html();
		$btn.prop("disabled", true).text(__("Saving…"));

		frappe.call({
			method: "custom_addons.custom_addons.page.recruitment_control_center.recruitment_control_center.save_onboarding_task",
			args: {
				task_id: self.selected_task_id,
				values: values,
			},
			callback: function (r) {
				self.is_saving = false;
				$btn.prop("disabled", false).html(original_text);

				if (r && r.message && r.message.success) {
					frappe.show_alert({
						message: __("Task saved successfully"),
						indicator: "green",
					});

					// Update local task in memory
					if (self.data && self.data.tasks) {
						const task = self.data.tasks.find((t) => t.name === self.selected_task_id);
						if (task) {
							Object.assign(task, values);
							if (r.message && r.message.completed_by) {
								task.completed_by = r.message.completed_by;
							}
							if (r.message && r.message.completed_on) {
								task.completed_on = r.message.completed_on;
							}
							if (r.message && r.message.progress !== undefined) {
								task.progress = r.message.progress;
							}
							if (task.completed_by) {
								task.assignees = task.assignees || [];
								if (task.assignees.indexOf(task.completed_by) === -1) {
									task.assignees.push(task.completed_by);
								}
							}
							const today = self.data.today || frappe.datetime.get_today();
							task.is_overdue = Boolean(
								task.exp_end_date &&
									task.exp_end_date < today &&
									task.status !== "Completed" &&
									task.status !== "Cancelled"
							);
						}
					}

					// Refresh view
					self.apply_filters_and_render();
				}
			},
			error: function () {
				self.is_saving = false;
				$btn.prop("disabled", false).html(original_text);
				frappe.msgprint(__("Failed to save task."));
			},
		});

	}
	connection_groups(doctype) {
		const meta = frappe.get_meta(doctype || "Task");
		const dash = (meta && meta.__dashboard) || {};
		let transactions = dash.transactions || [];

		if (!transactions.length && meta && meta.links && meta.links.length) {
			const by_group = {};
			meta.links.forEach((link) => {
				if (link.hidden || link.is_child_table || !link.link_doctype) return;
				const group = link.group || "";
				by_group[group] = by_group[group] || { label: group, items: [] };
				if (by_group[group].items.indexOf(link.link_doctype) === -1) {
					by_group[group].items.push(link.link_doctype);
				}
			});
			transactions = Object.keys(by_group).map((k) => by_group[k]);
		}

		// Fallback for Task (mirrors ERPNext projects/task_dashboard.py and HRMS)
		if (!transactions.length) {
			transactions = [
				{ label: __("Activity"), items: ["Timesheet"] },
				{ label: __("Claims"), items: ["Expense Claim"] },
				{ label: __("Tasks"), items: ["Task"] },
			];
		}

		// Filter out DocTypes that the user cannot read
		const permitted = [];
		transactions.forEach((group) => {
			const items = (group.items || []).filter((dt) => {
				return frappe.model.can_read ? frappe.model.can_read(dt) : true;
			});
			if (items.length) {
				permitted.push({ label: group.label, items: items });
			}
		});

		return permitted;
	}

	// Related fieldname used to filter a linked DocType back to Task.
	connection_fieldname(doctype, linked_doctype) {
		const dash = (frappe.get_meta(doctype || "Task") && frappe.get_meta(doctype || "Task").__dashboard) || {};
		if (dash.non_standard_fieldnames && dash.non_standard_fieldnames[linked_doctype]) {
			return dash.non_standard_fieldnames[linked_doctype];
		}
		if (linked_doctype === "Task") return "parent_task";
		if (linked_doctype === "Timesheet") return "task";
		if (linked_doctype === "Expense Claim") return "task";
		return dash.fieldname || "task";
	}

	// Load & render the connection links (with counts) into the section body.
	render_task_connections(doctype, docname) {
		const self = this;
		const $section = this.$content.find("[data-ot-connections]");
		if (!$section.length) return;
		const $txn = $section.find("[data-ot-connections-transactions]");
		if (!$txn.length) return;
		const $total = $section.find("[data-ot-connections-count]");

		const transactions = this.connection_groups(doctype || "Task");
		const items = [];
		transactions.forEach((group) => {
			(group.items || []).forEach((linked) => {
				if (items.indexOf(linked) === -1) items.push(linked);
			});
		});

		if (!items.length) {
			$txn.html(`<div class="rcc-xform-connections-empty" style="font-size: 11px; color: #94a3b8; padding: 4px 0;">${__("No linked transactions")}</div>`);
			return;
		}

		// Build the link markup first (counts fill in progressively).
		const html = transactions
			.map((group) => {
				if (!group.items || !group.items.length) return "";
				const rows = group.items
					.map((linked) => {
						const can_create = frappe.model.can_create(linked);
						return `
							<div class="rcc-conn-item">
								<div class="rcc-conn-link" data-ot-conn-doctype="${frappe.utils.escape_html(linked)}" data-ot-conn-task="${frappe.utils.escape_html(docname)}" title="${frappe.utils.escape_html(__("Open {0}", [linked]))}">
									<span class="rcc-conn-link-icon">${frappe.rcc.icon("link-2", 14)}</span>
									<span class="rcc-conn-link-label">${frappe.utils.escape_html(__(linked))}</span>
									<span class="rcc-conn-link-count" data-ot-conn-count="${frappe.utils.escape_html(linked)}">–</span>
								</div>
								${
									can_create
										? `<button type="button" class="rcc-conn-btn-add" data-ot-conn-add="${frappe.utils.escape_html(linked)}" data-ot-conn-task="${frappe.utils.escape_html(docname)}" title="${frappe.utils.escape_html(__("Create new {0}", [linked]))}">
											${frappe.rcc.icon("plus", 12)}
										</button>`
										: ""
								}
							</div>`;
					})
					.join("");
				return `
					<div class="rcc-conn-group" style="margin-top: 6px;">
						${group.label ? `<div class="rcc-conn-group-title">${frappe.utils.escape_html(__(group.label))}</div>` : ""}
						<div class="rcc-conn-links">${rows}</div>
					</div>`;
			})
			.join("");
		$txn.html(html);

		// Fetch all counts using the desk's own connection counter
		frappe
			.xcall("frappe.desk.notifications.get_open_count", {
				doctype: doctype || "Task",
				name: docname,
			})
			.then((r) => {
				if (self.selected_task_id !== docname) return;
				const count = (r && r.count) || {};
				const found = []
					.concat(count.external_links_found || [])
					.concat(count.internal_links_found || []);
				const by_doctype = {};
				found.forEach((row) => {
					if (row && row.doctype) by_doctype[row.doctype] = cint(row.count);
				});

				items.forEach((linked) => {
					const n = by_doctype[linked] || 0;
					self.set_conn_count(linked, n);
				});
				$total.text(String(items.reduce((total, linked) => total + (by_doctype[linked] || 0), 0)));

				// If Task (sub-tasks) is an item and not returned by get_open_count, query count
				if (items.indexOf("Task") !== -1 && by_doctype["Task"] === undefined) {
					frappe.db.count("Task", { filters: { parent_task: docname } }).then((sub_cnt) => {
						if (self.selected_task_id !== docname) return;
						const n = cint(sub_cnt);
						by_doctype.Task = n;
						self.set_conn_count("Task", n);
						$total.text(String(items.reduce((total, linked) => total + (by_doctype[linked] || 0), 0)));
					});
				}
			})
			.catch(() => {
				if (self.selected_task_id !== docname) return;
				items.forEach((linked) => self.set_conn_count(linked, 0));
				$total.text("0");
			});
	}

	set_conn_count(linked, count) {
		const $section = this.$content.find("[data-ot-connections]");
		$section.find(`[data-ot-conn-count="${linked}"]`).text(String(count));
		$section
			.find(`.rcc-conn-link[data-ot-conn-doctype="${linked}"]`)
			.toggleClass("is-empty", !count);
	}

	open_task_connection(linked_doctype, task_name) {
		const tname = task_name || this.selected_task_id;
		if (!tname) return;
		const fieldname = this.connection_fieldname("Task", linked_doctype);
		const filters = fieldname ? { [fieldname]: tname } : {};
		frappe.route_options = filters;
		frappe.set_route("List", linked_doctype, "List");
	}

	create_connected_record(linked_doctype, task_id) {
		const task = this.data && this.data.tasks
			? this.data.tasks.find((t) => t.name === task_id)
			: { name: task_id };

		if (!frappe.model.can_create(linked_doctype)) {
			frappe.show_alert({
				message: __("You do not have permission to create {0}.", [__(linked_doctype)]),
				indicator: "red",
			});
			return;
		}

		frappe.model.with_doctype(linked_doctype, () => {
			const defaults = {};
			const fieldname = this.connection_fieldname("Task", linked_doctype);
			if (fieldname) {
				defaults[fieldname] = task_id;
			} else if (frappe.get_meta(linked_doctype)) {
				const matching_df = (frappe.get_meta(linked_doctype).fields || []).find(
					(df) => df.fieldtype === "Link" && df.options === "Task"
				);
				if (matching_df) {
					defaults[matching_df.fieldname] = task_id;
				}
			}
			if (task && task.project) {
				const meta = frappe.get_meta(linked_doctype);
				if (meta && meta.fields && meta.fields.some((f) => f.fieldname === "project")) {
					defaults["project"] = task.project;
				}
			}

			// Check if linked_doctype is available in Workspace tab
			const workspace_tab = this.controller && this.controller.tabs && this.controller.tabs["Workspace"];
			const pipeline_doctypes = (workspace_tab && workspace_tab.form_view_doctypes) || frappe.rcc.FORM_VIEW_DOCTYPES || [];

			if (pipeline_doctypes.includes(linked_doctype)) {
				this.controller.switch_tab("Workspace");
				if (workspace_tab) {
					workspace_tab.select_doctype(linked_doctype);
					workspace_tab.new_record(linked_doctype, defaults);
				}
			} else {
				// Outside the pipeline: redirect to original Frappe doctype
				frappe.new_doc(linked_doctype, defaults);
			}
		});
	}

	new_task() {
		const current_task = this.data && this.data.tasks
			? this.data.tasks.find((t) => t.name === this.selected_task_id)
			: null;
		const proj = current_task ? current_task.project : "";
		frappe.new_doc("Task", {
			project: proj,
			type: "Onboarding",
		});
	}
};
