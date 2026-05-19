let tables = {};
let currentData = {};

frappe.pages['project-expenses-per'].on_page_load = function(wrapper) {

	// ---------------------------------------------------------
	// PAGE INIT
	// ---------------------------------------------------------

    let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Project Expense Analysis',
		single_column: true
	});

	let $body = $(page.body);

	// ---------------------------------------------------------
	// PAGE ACTIONS
	// ---------------------------------------------------------

	let export_btn;
	let print_btn;

	// Refresh Button (Primary)
	// page.set_primary_action(
	// 	__('Refresh'),
	// 	() => {
	// 		$body.find('#expense-refresh-btn').trigger('click');
	// 	},
	// 	'refresh'
	// );

	// Export Excel Action
	export_btn = page.add_action_item(
		__('Export Excel'),
		() => {

			let cfg = export_config[active_tab];

			let data = (currentData[active_tab] || []).filter(r =>
				!r.is_total_row
				&& r.project !== 'Total'
				&& r.project !== ''
				&& r.project != null
			);

			if (!data.length) {
				frappe.msgprint(__('No data to export.'));
				return;
			}

			export_to_excel(cfg, data);
		}
	);

	// Print Action
	print_btn = page.add_action_item(
		__('Print'),
		() => {

			let cfg = print_config[active_tab];

			let data = (currentData[active_tab] || []).filter(r =>
				!r.is_total_row
				&& r.project !== 'Total'
				&& r.project !== ''
				&& r.project != null
			);

			if (!data.length) {
				frappe.msgprint(__('No data to print.'));
				return;
			}

			print_report(cfg, data);
		}
	);

	// Disable initially
	$(export_btn).addClass('disabled');
	$(print_btn).addClass('disabled');

	// ---------------------------------------------------------
	// PAGE STRUCTURE
	// ---------------------------------------------------------

	$body.html(`
		<div class="expense-filters-row" id="expense-filters">

			<div class="filter-fields"
				style="
					display:flex;
					flex-wrap:wrap;
					gap:10px;
					width:100%;
				">
			</div>

			<div style="margin-top:14px;">
	<button class="expense-refresh-btn" id="expense-refresh-btn">
		↻ Refresh
	</button>
        </div>

		</div>

		<div class="expense-stats-bar" id="expense-stats-bar" style="display:none;">

			<div class="expense-stat-card" id="stat-employee_timesheet">
				<div class="stat-label">Employee Timesheet</div>
				<div class="stat-value">—</div>
				<div class="stat-sub">0 records</div>
			</div>

			<div class="expense-stat-card" id="stat-equipment_timesheet">
				<div class="stat-label">Equipment Timesheet</div>
				<div class="stat-value">—</div>
				<div class="stat-sub">0 records</div>
			</div>

			<div class="expense-stat-card" id="stat-purchase_order">
				<div class="stat-label">Purchase Orders</div>
				<div class="stat-value">—</div>
				<div class="stat-sub">0 records</div>
			</div>

			<div class="expense-stat-card" id="stat-expense_claim">
				<div class="stat-label">Expense Claims</div>
				<div class="stat-value">—</div>
				<div class="stat-sub">0 records</div>
			</div>

			<div class="expense-stat-card" id="stat-purchase_invoice">
				<div class="stat-label">Purchase Invoices</div>
				<div class="stat-value">—</div>
				<div class="stat-sub">0 records</div>
			</div>

		</div>

		<div class="expense-tab-nav" id="expense-tabs">

			<button class="tab-btn active" data-tab="employee_timesheet">
				Employee Timesheet
				<span class="tab-badge" id="badge-employee_timesheet">0</span>
			</button>

			<button class="tab-btn" data-tab="equipment_timesheet">
				Equipment Timesheet
				<span class="tab-badge" id="badge-equipment_timesheet">0</span>
			</button>

			<button class="tab-btn" data-tab="purchase_order">
				Purchase Order
				<span class="tab-badge" id="badge-purchase_order">0</span>
			</button>

			<button class="tab-btn" data-tab="expense_claim">
				Expense Claim
				<span class="tab-badge" id="badge-expense_claim">0</span>
			</button>

			<button class="tab-btn" data-tab="purchase_invoice">
				Purchase Invoice
				<span class="tab-badge" id="badge-purchase_invoice">0</span>
			</button>

		</div>

		<div class="expense-tab-panel" id="expense-tab-panel">

			<div id="employee_timesheet" class="expense-tab-content">
				<div class="datatable-wrapper"></div>
			</div>

			<div id="equipment_timesheet"
				class="expense-tab-content"
				style="display:none;">
				<div class="datatable-wrapper"></div>
			</div>

			<div id="purchase_order"
				class="expense-tab-content"
				style="display:none;">
				<div class="datatable-wrapper"></div>
			</div>

			<div id="expense_claim"
				class="expense-tab-content"
				style="display:none;">
				<div class="datatable-wrapper"></div>
			</div>

			<div id="purchase_invoice"
				class="expense-tab-content"
				style="display:none;">
				<div class="datatable-wrapper"></div>
			</div>

		</div>
	`);

	// ---------------------------------------------------------
	// FILTERS
	// ---------------------------------------------------------

	let $filter_fields = $body.find('.filter-fields');

	function make_field(opts) {
		let field = frappe.ui.form.make_control({
			parent: $('<div>').appendTo($filter_fields)[0],
			df: opts,
			render_input: true
		});
		field.refresh();
		return field;
	}

	let project   = make_field({ fieldtype: 'Link', label: 'Project',   fieldname: 'project',   options: 'Project' });
	let from_date = make_field({ fieldtype: 'Date', label: 'From Date', fieldname: 'from_date' });
	let to_date   = make_field({ fieldtype: 'Date', label: 'To Date',   fieldname: 'to_date' });
	let supplier  = make_field({ fieldtype: 'Link', label: 'Supplier',  fieldname: 'supplier',  options: 'Supplier' });
	let stand_by  = make_field({ fieldtype: 'Data', label: 'Stand By',  fieldname: 'stand_by' });
	let branch    = make_field({ fieldtype: 'Link', label: 'Branch',    fieldname: 'branch',    options: 'Branch' });

	from_date.set_value(frappe.datetime.month_start());
	to_date.set_value(frappe.datetime.month_end());

	// ---------------------------------------------------------
	// TAB SWITCHING
	// ---------------------------------------------------------

	let active_tab = 'employee_timesheet';

	$body.on('click', '.tab-btn', function() {
		let tab = $(this).data('tab');
		if (tab === active_tab) return;

		$body.find('.tab-btn').removeClass('active');
		$(this).addClass('active');

		$body.find('.expense-tab-content').hide();
		$body.find(`#${tab}`).show();

		active_tab = tab;
	});

	// ---------------------------------------------------------
	// LOADING STATE
	// ---------------------------------------------------------

    function show_loading() {

		let $panel = $body.find('#expense-tab-panel');

		if ($panel.find('.expense-loading-overlay').length) return;

		$panel.append(`
			<div class="expense-loading-overlay">
				<div class="expense-spinner"></div>
				Fetching data…
			</div>
		`);

		let $btn = $body.find('#expense-refresh-btn');

		$btn
			.prop('disabled', true)
			.addClass('loading');
	}

    function hide_loading() {

		$body.find('.expense-loading-overlay').remove();

		let $btn = $body.find('#expense-refresh-btn');

		$btn
			.prop('disabled', false)
			.removeClass('loading');
	}

	// ---------------------------------------------------------
	// CURRENCY FORMATTER
	// ---------------------------------------------------------

	function format_currency(val) {
		if (!val && val !== 0) return '—';
		let raw = frappe.format(val, { fieldtype: 'Currency' });
		return $('<div>').html(raw).text().trim();
	}

	// ---------------------------------------------------------
	// STATS BAR
	// ---------------------------------------------------------

	function update_stats(data) {

		const tabs = {
			employee_timesheet:  { amount_keys: ['working_amount', 'ot_amount'] },
			equipment_timesheet: { amount_key: 'total_amount' },
			purchase_order:      { amount_key: 'grand_total' },
			expense_claim:       { amount_key: 'total_amount' },
			purchase_invoice:    { amount_key: 'grand_total' }
		};

		Object.entries(tabs).forEach(([tab, cfg]) => {

			// Filter out grand total / summary rows
			let rows = (data[tab] || []).filter(r =>
				!r.is_total_row
				&& r.project !== 'Total'
				&& r.project !== ''
				&& r.project != null
			);

			let count = rows.length;

			$body.find(`#badge-${tab}`).text(count);

			let $card = $body.find(`#stat-${tab}`);
			if (!$card.length) return;

			let total = 0;

			if (cfg.amount_keys) {
				cfg.amount_keys.forEach(key => {
					total += rows.reduce((sum, r) => sum + (parseFloat(r[key]) || 0), 0);
				});
			} else if (cfg.amount_key) {
				total = rows.reduce((sum, r) => sum + (parseFloat(r[cfg.amount_key]) || 0), 0);
			}

			$card.find('.stat-value').text(format_currency(total));
			$card.find('.stat-sub').text(`${count} record${count !== 1 ? 's' : ''}`);
		});

		$body.find('#expense-stats-bar').show();
	}

	// ---------------------------------------------------------
	// EMPTY STATE
	// ---------------------------------------------------------

	function empty_state() {
		return `
			<div class="expense-empty-state">
				<div class="empty-icon">📋</div>
				<p>No data found for the selected filters.</p>
			</div>
		`;
	}

	// ---------------------------------------------------------
	// REFRESH
	// ---------------------------------------------------------

	$body.on('click', '#expense-refresh-btn', function() {

		show_loading();

		frappe.call({
			method: 'custom_addons.custom_addons.page.project_expenses_per.project_expenses_per.get_data',

			args: {
				filters: {
					project:   project.get_value(),
					from_date: from_date.get_value(),
					to_date:   to_date.get_value(),
					supplier:  supplier.get_value(),
					stand_by:  stand_by.get_value(),
					branch:    branch.get_value()
				}
			},

			callback: function(r) {
				hide_loading();

				if (!r.message) {
					frappe.msgprint(__('No data returned. Check your filters.'));
					return;
				}

				currentData = r.message;

				$(export_btn).removeClass('disabled');
                $(print_btn).removeClass('disabled');

				update_stats(currentData);

				render_employee_timesheet(currentData.employee_timesheet);
				render_equipment_timesheet(currentData.equipment_timesheet);
				render_purchase_order(currentData.purchase_order);
				render_expense_claim(currentData.expense_claim);
				render_purchase_invoice(currentData.purchase_invoice);
			},

			error: function() {
				hide_loading();
				frappe.msgprint(__('Failed to fetch data. Please try again.'));
			}
		});
	});

	// ---------------------------------------------------------
	// DATATABLE HELPERS
	// ---------------------------------------------------------

	function destroy_table(tab_id) {
		if (tables[tab_id]) {
			try { tables[tab_id].destroy(); } catch(e) {}
			tables[tab_id] = null;
		}
		$body.find(`#${tab_id}`).html('<div class="datatable-wrapper"></div>');
	}

	function get_dt_wrapper(tab_id) {
		return $body.find(`#${tab_id} .datatable-wrapper`)[0];
	}

	function dt_options(columns, data) {
		return {
			columns,
			data: data && data.length ? data : [],
			layout: 'fixed',
			serialNoColumn: true,
			inlineFilters: false,
			cellHeight: 38,
			noDataMessage: empty_state()
		};
	}

	const currency_fmt = value => frappe.format(value, { fieldtype: 'Currency' });

	// ---------------------------------------------------------
	// RENDER — EMPLOYEE TIMESHEET
	// ---------------------------------------------------------

	function render_employee_timesheet(data) {
		destroy_table('employee_timesheet');

		tables['employee_timesheet'] = new frappe.DataTable(
			get_dt_wrapper('employee_timesheet'),
			dt_options([
				{ name: 'Project Code',       id: 'project',        width: 160 },
				{ name: 'Project Name',        id: 'project_name',   width: 220 },
				{ name: 'Department',          id: 'department',     width: 200 },
				{ name: 'Stand By',            id: 'stand_by',       width: 110 },
				{ name: 'Branch',              id: 'branch',         width: 160 },
				{ name: 'Month–Year',          id: 'month_year',     width: 120 },
				{ name: 'Working Hrs Amount',  id: 'working_amount', width: 170, align: 'right', format: currency_fmt },
				{ name: 'OT Hrs Amount',       id: 'ot_amount',      width: 150, align: 'right', format: currency_fmt }
			], data)
		);
	}

	// ---------------------------------------------------------
	// RENDER — EQUIPMENT TIMESHEET
	// ---------------------------------------------------------

	function render_equipment_timesheet(data) {
		destroy_table('equipment_timesheet');

		tables['equipment_timesheet'] = new frappe.DataTable(
			get_dt_wrapper('equipment_timesheet'),
			dt_options([
				{ name: 'Project Code',  id: 'project',       width: 160 },
				{ name: 'Project Name',  id: 'project_name',  width: 220 },
				{ name: 'Supplier Code', id: 'supplier',      width: 140 },
				{ name: 'Supplier Name', id: 'supplier_name', width: 300 },
				{ name: 'Month–Year',    id: 'month_year',    width: 120 },
				{ name: 'Total Hours',   id: 'total_hours',   width: 120, align: 'right' },
				{ name: 'Total Amount',  id: 'total_amount',  width: 150, align: 'right', format: currency_fmt }
			], data)
		);
	}

	// ---------------------------------------------------------
	// RENDER — PURCHASE ORDER
	// ---------------------------------------------------------

	function render_purchase_order(data) {
		destroy_table('purchase_order');

		tables['purchase_order'] = new frappe.DataTable(
			get_dt_wrapper('purchase_order'),
			dt_options([
				{ name: 'Project Code',  id: 'project',        width: 160 },
				{ name: 'Project Name',  id: 'project_name',   width: 200 },
				{ name: 'Supplier Code', id: 'supplier',       width: 140 },
				{ name: 'Supplier Name', id: 'supplier_name',  width: 260 },
				{ name: 'Status',        id: 'workflow_state', width: 140 },
				{ name: 'Month–Year',    id: 'month_year',     width: 120 },
				{ name: '% Billed',      id: 'per_billed',     width: 110, align: 'right' },
				{ name: '% Received',    id: 'per_received',   width: 110, align: 'right' },
				{ name: 'Grand Total',   id: 'grand_total',    width: 150, align: 'right', format: currency_fmt }
			], data)
		);
	}

	// ---------------------------------------------------------
	// RENDER — EXPENSE CLAIM
	// ---------------------------------------------------------

	function render_expense_claim(data) {
		destroy_table('expense_claim');

		tables['expense_claim'] = new frappe.DataTable(
			get_dt_wrapper('expense_claim'),
			dt_options([
				{ name: 'Project Code',  id: 'project',       width: 160 },
				{ name: 'Project Name',  id: 'project_name',  width: 220 },
				{ name: 'Employee No.',  id: 'employee',      width: 150 },
				{ name: 'Employee Name', id: 'employee_name', width: 240 },
				{ name: 'Month–Year',    id: 'month_year',    width: 120 },
				{ name: 'Total Amount',  id: 'total_amount',  width: 150, align: 'right', format: currency_fmt }
			], data)
		);
	}

	// ---------------------------------------------------------
	// RENDER — PURCHASE INVOICE
	// ---------------------------------------------------------

	function render_purchase_invoice(data) {
		destroy_table('purchase_invoice');

		tables['purchase_invoice'] = new frappe.DataTable(
			get_dt_wrapper('purchase_invoice'),
			dt_options([
				{ name: 'Project Code',  id: 'project',        width: 160 },
				{ name: 'Project Name',  id: 'project_name',   width: 200 },
				{ name: 'Supplier Code', id: 'supplier',       width: 140 },
				{ name: 'Supplier Name', id: 'supplier_name',  width: 280 },
				{ name: 'Status',        id: 'workflow_state', width: 140 },
				{ name: 'Month–Year',    id: 'month_year',     width: 120 },
				{ name: 'Grand Total',   id: 'grand_total',    width: 150, align: 'right', format: currency_fmt }
			], data)
		);
	}

	// ---------------------------------------------------------
	// EXCEL EXPORT CONFIG
	// ---------------------------------------------------------

	const export_config = {
		employee_timesheet: {
			sheet_name: 'Employee Timesheet',
			columns: [
				{ label: 'Project Code',       key: 'project' },
				{ label: 'Project Name',        key: 'project_name' },
				{ label: 'Department',          key: 'department' },
				{ label: 'Stand By',            key: 'stand_by' },
				{ label: 'Branch',              key: 'branch' },
				{ label: 'Month-Year',          key: 'month_year' },
				{ label: 'Working Hrs Amount',  key: 'working_amount', type: 'currency' },
				{ label: 'OT Hrs Amount',       key: 'ot_amount',      type: 'currency' }
			]
		},
		equipment_timesheet: {
			sheet_name: 'Equipment Timesheet',
			columns: [
				{ label: 'Project Code',  key: 'project' },
				{ label: 'Project Name',  key: 'project_name' },
				{ label: 'Supplier Code', key: 'supplier' },
				{ label: 'Supplier Name', key: 'supplier_name' },
				{ label: 'Month-Year',    key: 'month_year' },
				{ label: 'Total Hours',   key: 'total_hours',  type: 'number' },
				{ label: 'Total Amount',  key: 'total_amount', type: 'currency' }
			]
		},
		purchase_order: {
			sheet_name: 'Purchase Order',
			columns: [
				{ label: 'Project Code',  key: 'project' },
				{ label: 'Project Name',  key: 'project_name' },
				{ label: 'Supplier Code', key: 'supplier' },
				{ label: 'Supplier Name', key: 'supplier_name' },
				{ label: 'Status',        key: 'workflow_state' },
				{ label: 'Month-Year',    key: 'month_year' },
				{ label: '% Billed',      key: 'per_billed',   type: 'number' },
				{ label: '% Received',    key: 'per_received',  type: 'number' },
				{ label: 'Grand Total',   key: 'grand_total',  type: 'currency' }
			]
		},
		expense_claim: {
			sheet_name: 'Expense Claim',
			columns: [
				{ label: 'Project Code',  key: 'project' },
				{ label: 'Project Name',  key: 'project_name' },
				{ label: 'Employee No.',  key: 'employee' },
				{ label: 'Employee Name', key: 'employee_name' },
				{ label: 'Month-Year',    key: 'month_year' },
				{ label: 'Total Amount',  key: 'total_amount', type: 'currency' }
			]
		},
		purchase_invoice: {
			sheet_name: 'Purchase Invoice',
			columns: [
				{ label: 'Project Code',  key: 'project' },
				{ label: 'Project Name',  key: 'project_name' },
				{ label: 'Supplier Code', key: 'supplier' },
				{ label: 'Supplier Name', key: 'supplier_name' },
				{ label: 'Status',        key: 'workflow_state' },
				{ label: 'Month-Year',    key: 'month_year' },
				{ label: 'Grand Total',   key: 'grand_total',  type: 'currency' }
			]
		}
	};

	// ---------------------------------------------------------
	// EXPORT BUTTON CLICK
	// ---------------------------------------------------------

	$body.on('click', '#expense-export-btn', function() {

		let cfg = export_config[active_tab];

		let data = (currentData[active_tab] || []).filter(r =>
			!r.is_total_row
			&& r.project !== 'Total'
			&& r.project !== ''
			&& r.project != null
		);

		if (!data.length) {
			frappe.msgprint(__('No data to export.'));
			return;
		}

		export_to_excel(cfg, data);
	});

    	// ---------------------------------------------------------
	// PRINT BUTTON CLICK
	// ---------------------------------------------------------

	$body.on('click', '#expense-print-btn', function() {

		let cfg = print_config[active_tab];

		let data = (currentData[active_tab] || []).filter(r =>
			!r.is_total_row
			&& r.project !== 'Total'
			&& r.project !== ''
			&& r.project != null
		);

		if (!data.length) {
			frappe.msgprint(__('No data to print.'));
			return;
		}

		print_report(cfg, data);
	});


		// ---------------------------------------------------------
	// EXPORT TO EXCEL (REAL XLSX FORMAT)
	// ---------------------------------------------------------

	function export_to_excel(cfg, data) {

		if (typeof XLSX === "undefined") {
			frappe.msgprint(__('XLSX library not loaded.'));
			return;
		}

		// -----------------------------------------
		// PREPARE FILTER SUMMARY
		// -----------------------------------------

		let filter_info = [
			`Project: ${project.get_value() || 'All'}`,
			`From: ${from_date.get_value() || '—'}`,
			`To: ${to_date.get_value() || '—'}`,
			`Supplier: ${supplier.get_value() || 'All'}`,
			`Branch: ${branch.get_value() || 'All'}`
		].join('   |   ');

		// -----------------------------------------
		// BUILD EXCEL DATA
		// -----------------------------------------

		let excel_data = [];

		// Title
		excel_data.push([`Project Expense Analysis — ${cfg.sheet_name}`]);

		// Filters
		excel_data.push([filter_info]);

		// Empty row
		excel_data.push([]);

		// Header row
		excel_data.push([
			'#',
			...cfg.columns.map(col => col.label)
		]);

		// Data rows
		data.forEach((row, idx) => {

			let row_data = [idx + 1];

			cfg.columns.forEach(col => {

				let val = row[col.key];

				if (col.type === 'currency' || col.type === 'number') {
					row_data.push(parseFloat(val) || 0);
				} else {
					row_data.push(val || '');
				}
			});

			excel_data.push(row_data);
		});

		// -----------------------------------------
		// CREATE WORKBOOK
		// -----------------------------------------

		let wb = XLSX.utils.book_new();

		let ws = XLSX.utils.aoa_to_sheet(excel_data);

		// -----------------------------------------
		// COLUMN WIDTHS
		// -----------------------------------------

		ws['!cols'] = [
			{ wch: 8 },
			...cfg.columns.map(col => ({
				wch: Math.max(col.label.length + 5, 18)
			}))
		];

		// -----------------------------------------
		// FREEZE HEADER
		// -----------------------------------------

		ws['!freeze'] = {
			xSplit: 0,
			ySplit: 4
		};

		// -----------------------------------------
		// AUTO FILTER
		// -----------------------------------------

		let total_cols = cfg.columns.length + 1;

		ws['!autofilter'] = {
			ref: `A4:${col_to_letter(total_cols - 1)}${excel_data.length}`
		};

		// -----------------------------------------
		// APPEND SHEET
		// -----------------------------------------

		XLSX.utils.book_append_sheet(
			wb,
			ws,
			cfg.sheet_name.substring(0, 31)
		);

		// -----------------------------------------
		// EXPORT FILE
		// -----------------------------------------

		let file_name =
			`${cfg.sheet_name.replace(/\s+/g, '_')}_${frappe.datetime.now_date()}.xlsx`;

		XLSX.writeFile(wb, file_name);

		frappe.show_alert({
			message: `Exported ${data.length} records to ${file_name}`,
			indicator: 'green'
		});
	}

    function col_to_letter(col_idx) {
        let letter = '';
        let n = col_idx + 1;
    
        while (n > 0) {
            let rem = (n - 1) % 26;
            letter = String.fromCharCode(65 + rem) + letter;
            n = Math.floor((n - 1) / 26);
        }
    
        return letter;
    }

    	// ---------------------------------------------------------
	// PRINT CONFIG
	// ---------------------------------------------------------

	const print_config = export_config;

    	// ---------------------------------------------------------
	// PRINT REPORT
	// ---------------------------------------------------------

    function print_report(cfg, data) {

		// ---------------------------------------------------------
		// FILTER SUMMARY
		// ---------------------------------------------------------

		let filter_info = [
			{ label: 'Project', value: project.get_value() || 'All' },
			{ label: 'From Date', value: from_date.get_value() || '—' },
			{ label: 'To Date', value: to_date.get_value() || '—' },
			{ label: 'Supplier', value: supplier.get_value() || 'All' },
			{ label: 'Branch', value: branch.get_value() || 'All' }
		];

		// ---------------------------------------------------------
		// TABLE HEADER
		// ---------------------------------------------------------

		let thead = `
			<tr>
				<th style="width:50px;">#</th>

				${cfg.columns.map(col => `
					<th class="${col.type ? 'text-right' : ''}">
						${col.label}
					</th>
				`).join('')}
			</tr>
		`;

		// ---------------------------------------------------------
		// TABLE BODY
		// ---------------------------------------------------------

		let tbody = '';

		data.forEach((row, idx) => {

			tbody += `
				<tr>

					<td class="text-center">
						${idx + 1}
					</td>

					${cfg.columns.map(col => {

						let val = row[col.key];

						if (col.type === 'currency') {
							val = format_currency(val);
						}

						return `
							<td class="${col.type ? 'text-right' : ''}">
								${val ?? ''}
							</td>
						`;

					}).join('')}

				</tr>
			`;
		});

		// ---------------------------------------------------------
		// TOTALS
		// ---------------------------------------------------------

		let grand_total = 0;

		cfg.columns.forEach(col => {

			if (col.type === 'currency') {

				grand_total += data.reduce((sum, r) => {
					return sum + (parseFloat(r[col.key]) || 0);
				}, 0);
			}
		});

		// ---------------------------------------------------------
		// REPORT HTML
		// ---------------------------------------------------------

		let html = `

			<html>

			<head>

				<title>${cfg.sheet_name}</title>

				<style>

					@page {
						size: landscape;
						margin: 14mm;
					}

					* {
						box-sizing: border-box;
					}

					body {

						font-family:
							Inter,
							Arial,
							sans-serif;

						color: #1f2937;

						font-size: 12px;

						margin: 0;
						padding: 0;

						background: white;
					}

					/* =====================================================
					   HEADER
					===================================================== */

					.report-header {

						display: flex;
						justify-content: space-between;
						align-items: flex-start;

						margin-bottom: 18px;
						padding-bottom: 14px;

						border-bottom:
							2px solid #e5e7eb;
					}

					.report-title-section h1 {

						margin: 0;
						font-size: 26px;
						font-weight: 700;

						color: #111827;
					}

					.report-title-section .subtitle {

						margin-top: 4px;

						font-size: 14px;
						color: #6b7280;
					}

					.report-meta {

						text-align: right;
						font-size: 11px;
						color: #6b7280;
						line-height: 1.7;
					}

					/* =====================================================
					   FILTER GRID
					===================================================== */

					.filter-grid {

						display: grid;

						grid-template-columns:
							repeat(5, 1fr);

						gap: 12px;

						margin-bottom: 20px;
					}

					.filter-card {

						border:
							1px solid #e5e7eb;

						border-radius: 10px;

						padding: 10px 12px;

						background: #f9fafb;
					}

					.filter-label {

						font-size: 10px;
						font-weight: 600;

						text-transform: uppercase;
						letter-spacing: 0.4px;

						color: #6b7280;

						margin-bottom: 4px;
					}

					.filter-value {

						font-size: 13px;
						font-weight: 600;

						color: #111827;
					}

					/* =====================================================
					   SUMMARY
					===================================================== */

					.summary-bar {

						display: flex;
						gap: 14px;

						margin-bottom: 18px;
					}

					.summary-card {

						flex: 1;

						border:
							1px solid #dbeafe;

						background:
							#eff6ff;

						border-radius: 10px;

						padding: 14px;
					}

					.summary-label {

						font-size: 11px;
						font-weight: 600;

						color: #2563eb;

						text-transform: uppercase;
					}

					.summary-value {

						margin-top: 4px;

						font-size: 22px;
						font-weight: 700;

						color: #111827;
					}

					/* =====================================================
					   TABLE
					===================================================== */

					table {

						width: 100%;
						border-collapse: collapse;

						font-size: 11px;
					}

					thead th {

						background: #1f2937;

						color: white;

						padding: 10px 12px;

						border:
							1px solid #374151;

						font-weight: 600;

						text-align: left;

						white-space: nowrap;
					}

					tbody td {

						padding: 9px 12px;

						border:
							1px solid #e5e7eb;

						vertical-align: middle;
					}

					tbody tr:nth-child(even) {
						background: #f9fafb;
					}

					.text-right {
						text-align: right;
					}

					.text-center {
						text-align: center;
					}

					/* =====================================================
					   FOOTER
					===================================================== */

					.report-footer {

						margin-top: 18px;

						display: flex;
						justify-content: space-between;
						align-items: center;

						font-size: 11px;

						color: #6b7280;

						border-top:
							1px solid #e5e7eb;

						padding-top: 10px;
					}

					/* =====================================================
					   PRINT
					===================================================== */

					@media print {

						body {
							-webkit-print-color-adjust: exact;
							print-color-adjust: exact;
						}

						tr {
							page-break-inside: avoid;
						}

						table {
							page-break-inside: auto;
						}
					}

				</style>

			</head>

			<body>

				<!-- =====================================================
				     HEADER
				===================================================== -->

				<div class="report-header">

					<div class="report-title-section">

						<h1>
							Project Expense Analysis
						</h1>

						<div class="subtitle">
							${cfg.sheet_name}
						</div>

					</div>

					<div class="report-meta">

						<div>
							Printed On:
							${frappe.datetime.now_datetime()}
						</div>

						<div>
							Generated By:
							${frappe.session.user}
						</div>

					</div>

				</div>

				<!-- =====================================================
				     FILTERS
				===================================================== -->

				<div class="filter-grid">

					${filter_info.map(f => `
						<div class="filter-card">

							<div class="filter-label">
								${f.label}
							</div>

							<div class="filter-value">
								${f.value}
							</div>

						</div>
					`).join('')}

				</div>

				<!-- =====================================================
				     SUMMARY
				===================================================== -->

				<div class="summary-bar">

					<div class="summary-card">

						<div class="summary-label">
							Total Records
						</div>

						<div class="summary-value">
							${data.length}
						</div>

					</div>

					<div class="summary-card">

						<div class="summary-label">
							Grand Total
						</div>

						<div class="summary-value">
							${format_currency(grand_total)}
						</div>

					</div>

				</div>

				<!-- =====================================================
				     TABLE
				===================================================== -->

				<table>

					<thead>
						${thead}
					</thead>

					<tbody>
						${tbody}
					</tbody>

				</table>

				<!-- =====================================================
				     FOOTER
				===================================================== -->

				<div class="report-footer">

					<div>
						INCHARGE ERP
					</div>

					<div>
						Page 1
					</div>

				</div>

				<script>

					window.onload = function() {
						window.print();
					}

				<\/script>

			</body>

			</html>
		`;

		// ---------------------------------------------------------
		// OPEN WINDOW
		// ---------------------------------------------------------

		let print_window = window.open('', '_blank');

		print_window.document.open();
		print_window.document.write(html);
		print_window.document.close();
	}



};