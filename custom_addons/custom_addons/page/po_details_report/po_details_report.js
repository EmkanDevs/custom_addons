frappe.pages['po-details-report'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'PO Details Report',
		single_column: true,

		
	});

	// Add enhanced custom CSS
	frappe.dom.set_style(
		'.status-badge { display: inline-flex; align-items: center; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }' +
		'.doc-box { transition: all 0.3s ease; cursor: pointer; }' +
		'.doc-box:hover { transform: translateY(-2px); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }' +
		'.loading-spinner { border: 3px solid #f3f3f3; border-top: 3px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto; }' +
		'@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }' +
		'.po-report-container { padding: 20px; background: #f8f9fa; }' +
		'.po-card { margin-bottom: 20px !important; transition: all 0.3s ease; border-radius: 8px !important; }' +
		'.po-card:hover { box-shadow: 0 8px 16px rgba(0,0,0,0.1) !important; }' +
		'.card-header { cursor: pointer; padding: 16px 20px !important; }' +
		'.card-body { padding: 20px !important; }' +
		'.card-header h5 { margin: 0; }' +
		'.doc-flow-track { display: flex; overflow-x: auto; padding: 20px 0; gap: 15px; margin-bottom: 25px; }' +
		'.doc-flow-step { min-width: 150px; flex-shrink: 0; }' +
		'.step-number { width: 30px; height: 30px; background: #3498db; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-bottom: 10px; }' +
		'.step-title { font-weight: 600; margin-bottom: 15px; color: #2c3e50; }' +
		'.step-content { min-height: 100px; }' +
		'.flow-arrow {font-size: 22px;color: #95a5a6;display: flex;align-items: center;}' +
		'.status-draft { background-color: rgba(149, 165, 166, 0.15) !important; color: #7f8c8d !important; border-color: rgba(149, 165, 166, 0.4) !important; }' +
		'.status-pending { background-color: rgba(243, 156, 18, 0.15) !important; color: #d68910 !important; border-color: rgba(243, 156, 18, 0.4) !important; }' +
		'.status-approved { background-color: rgba(39, 174, 96, 0.15) !important; color: #27ae60 !important; border-color: rgba(39, 174, 96, 0.4) !important; }' +
		'.status-cancelled { background-color: rgba(231, 76, 60, 0.15) !important; color: #c0392b !important; border-color: rgba(231, 76, 60, 0.4) !important; }' +
		'.status-received { background-color: rgba(52, 152, 219, 0.15) !important; color: #2980b9 !important; border-color: rgba(52, 152, 219, 0.4) !important; }' +
		'.status-submitted { background-color: rgba(241, 196, 15, 0.15) !important; color: #f39c12 !important; border-color: rgba(241, 196, 15, 0.4) !important; }' +
		'.status-completed { background-color: rgba(46, 204, 113, 0.15) !important; color: #27ae60 !important; border-color: rgba(46, 204, 113, 0.4) !important; }' +
		'.status-paid { background-color: rgba(155, 89, 182, 0.15) !important; color: #8e44ad !important; border-color: rgba(155, 89, 182, 0.4) !important; }' +
		'.status-quotation { background-color: rgba(52, 152, 219, 0.15) !important; color: #2980b9 !important; border-color: rgba(52, 152, 219, 0.4) !important; }' +
		'.status-ordered { background-color: rgba(39, 174, 96, 0.15) !important; color: #27ae60 !important; border-color: rgba(39, 174, 96, 0.4) !important; }' +
		'.status-awarded { background-color: rgba(155, 89, 182, 0.15) !important; color: #8e44ad !important; border-color: rgba(155, 89, 182, 0.4) !important; }' +
		'.status-bid { background-color: rgba(230, 126, 34, 0.15) !important; color: #d35400 !important; border-color: rgba(230, 126, 34, 0.4) !important; }' +
		'.status-evaluated { background-color: rgba(142, 68, 173, 0.15) !important; color: #8e44ad !important; border-color: rgba(142, 68, 173, 0.4) !important; }' +
		'.border-draft { border-left: 5px solid rgba(149, 165, 166, 0.7) !important; }' +
		'.border-pending { border-left: 5px solid rgba(243, 156, 18, 0.7) !important; }' +
		'.border-approved { border-left: 5px solid rgba(39, 174, 96, 0.7) !important; }' +
		'.border-cancelled { border-left: 5px solid rgba(231, 76, 60, 0.7) !important; }' +
		'.border-received { border-left: 5px solid rgba(52, 152, 219, 0.7) !important; }' +
		'.workflow-states { display: flex; gap: 10px; flex-wrap: wrap; }' +
		'.workflow-state-item { background: #f8f9fa; border-radius: 4px; padding: 4px 8px; font-size: 12px; }' +
		'.workflow-state-label { color: #6c757d; }' +
		'.workflow-state-value { font-weight: 600; }' +
		'.count-badge { background-color: #e74c3c; color: white; border-radius: 10px; padding: 1px 6px; font-size: 11px; font-weight: bold; margin-left: 5px; }' +
		'.empty-doc { color: #95a5a6; font-style: italic; font-size: 0.9rem; padding: 10px; background: #f8f9fa; border-radius: 4px; }' +
		'.items-toggle { cursor: pointer; color: #3498db; font-weight: 600; display: flex; align-items: center; gap: 5px; }' +
		'.items-container { display: none; margin-top: 15px; }' +
		'.items-container.expanded { display: block; }' +
		'.mr-card { border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin-bottom: 15px; background: white; }' +
		'.mr-id { font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 8px; }' +
		'.mr-meta { color: #6c757d; font-size: 14px; margin-bottom: 10px; }' +
		'.mr-workflow-status { display: flex; gap: 20px; margin-top: 10px; }' +
		'.status-section { flex: 1; }' +
		'.status-label { font-size: 12px; color: #6c757d; margin-bottom: 4px; }' +
		'.status-value { font-weight: 600; }' +
		'.child-row { margin-left: 30px; border-left: 2px solid #dee2e6; padding-left: 15px; margin-top: 10px; }' +
		'.child-doc { font-size: 14px; color: #6c757d; }' +
		'.bid-section { background: linear-gradient(135deg, #fdfcfb 0%, #f5f7fa 100%); border: 1px solid #e3e8f0; border-radius: 6px; padding: 12px; margin-bottom: 10px; }' +
		'.bid-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }' +
		'.bid-title { font-weight: 600; color: #2d3748; font-size: 13px; }' +
		'.bid-status { font-size: 11px; }' +
		'.bid-docs { margin-top: 8px; }' +
		'.bid-doc-item { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; border-bottom: 1px dashed #e2e8f0; }' +
		'.bid-doc-item:last-child { border-bottom: none; }' +
		'.bid-doc-name { color: #4a5568; font-size: 12px; }' +
		'.bid-doc-status { font-size: 11px; }' +
		'.multi-doc-container { display: flex; flex-direction: column; gap: 8px; }' +
		'.multi-doc-item { display: flex; justify-content: space-between; align-items: center; padding: 8px; background: #f8fafc; border-radius: 4px; border: 1px solid #e2e8f0; }' +
		'.multi-doc-link { color: #3182ce; font-weight: 500; text-decoration: none; }' +
		'.multi-doc-link:hover { text-decoration: underline; }' +
		'.rfq-section { margin-bottom: 15px; }'
	);

	// Create HTML structure
	$(page.main).html(
		'<div class="po-report-container">' +
		'<div class="d-flex justify-content-between align-items-center mb-4">' +
		'<h3 style="margin: 0;">Purchase Order Details Report</h3>' +
		'<button id="btn-refresh" class="btn btn-success">' +
		'<i class="fa fa-refresh"></i> Refresh' +
		'</button>' +
		'</div>' +
		'<hr style="margin: 30px 0;">' +
		'<div class="card mb-4">' +
		'<div class="card-body">' +
		'<h5 class="card-title mb-3">Filters</h5>' +
		'<div class="row">' +
		'<div class="col-md-3 mb-3">' +
		'<label class="form-label">From Date</label>' +
		'<input type="date" id="filter-from-date" class="form-control">' +
		'</div>' +
		'<div class="col-md-3 mb-3">' +
		'<label class="form-label">To Date</label>' +
		'<input type="date" id="filter-to-date" class="form-control">' +
		'</div>' +
		'<div class="col-md-3 mb-3">' +
		'<label class="form-label">Purpose</label>' +
		'<select id="filter-purpose" class="form-control">' +
		'<option value="">All</option>' +
		'<option value="Purchase" selected>Purchase</option>' +
		'<option value="Material Transfer">Material Transfer</option>' +
		'<option value="Material Issue">Material Issue</option>' +
		'<option value="Manufacture">Manufacture</option>' +
		'<option value="Customer Provided">Customer Provided</option>' +
		'</select>' +
		'</div>' +
		'<div class="col-md-3 mb-3">' +
		'<label class="form-label">Material Request</label>' +
		'<input type="text" id="filter-material-request" class="form-control" placeholder="Search Material Request...">' +
		'</div>' +
		'</div>' +
		'<div class="row">' +
		'<div class="col-md-4 mb-3">' +
		'<div id="project-filter"></div>' +
		'</div> ' +
		'<div class="col-md-3 mb-3">' +
		'<div id="assigned-to-filter"></div>' +
		'</div>' +
		'<div class="col-md-8 mb-3">' +
		'<label class="form-label">&nbsp;</label>' +
		'<div style="padding-top: 8px;">' +
		'<button id="btn-fetch-data" class="btn btn-primary mr-2">' +
		'<i class="fa fa-search"></i> Fetch Report' +
		'</button>' +
		'<button id="btn-clear-filters" class="btn btn-secondary">' +
		'<i class="fa fa-times"></i> Clear Filters' +
		'</button>' +
		'</div>' +
		'</div>' +
		'</div>' +
		'</div>' +
		'</div>' +
		'<div class="card mb-4">' +
		'<div class="card-body">' +
		'<h5 class="card-title mb-3">Status</h5>' +
		'<div class="row">' +
		'<div class="col-md-2 mb-2">' +
		'<span class="status-badge status-draft">Draft</span>' +
		'</div>' +
		'<div class="col-md-2 mb-2">' +
		'<span class="status-badge status-pending">Pending</span>' +
		'</div>' +
		'<div class="col-md-2 mb-2">' +
		'<span class="status-badge status-approved">Approved</span>' +
		'</div>' +
		'<div class="col-md-2 mb-2">' +
		'<span class="status-badge status-cancelled">Cancelled</span>' +
		'</div>' +
		'<div class="col-md-2 mb-2">' +
		'<span class="status-badge status-quotation">Quotation</span>' +
		'</div>' +
		'<div class="col-md-2 mb-2">' +
		'<span class="status-badge status-awarded">Awarded</span>' +
		'</div>' +
		'</div>' +
		'</div>' +
		'</div>' +
		'<div id="loading" class="text-center py-5" style="display: none;">' +
		'<div class="loading-spinner"></div>' +
		'<p class="mt-3 text-muted">Loading data...</p>' +
		'</div>' +
		'<div id="report-data"></div>' +
		'</div>'
	);

	po_details_report.init(page);
};

frappe.pages['po-details-report'].on_page_show = function () {
	if (!po_details_report.page) {
		return;
	}

	if (po_details_report.apply_route_filters()) {
		po_details_report.fetch_report_data();
	}
};

var po_details_report = {
	page: null,
	reportData: [],

	STATUS_COLORS: {
		'Draft': 'status-draft',
		'Pending': 'status-pending',
		'Pending Approval': 'status-pending',
		'Approved': 'status-approved',
		'Cancelled': 'status-cancelled',
		'Submitted': 'status-submitted',
		'Received': 'status-received',
		'Completed': 'status-completed',
		'Paid': 'status-paid',
		'Initiated': 'status-pending',
		'Open': 'status-pending',
		'Closed': 'status-completed',
		'To Receive': 'status-pending',
		'To Bill': 'status-pending',
		'To Receive and Bill': 'status-pending',
		'Unpaid': 'status-pending',
		'Partially Paid': 'status-pending',
		'Return': 'status-cancelled',
		'Requested': 'status-pending',
		'Payment Ordered': 'status-approved',
		'Partially Ordered': 'status-pending',
		'Partially Received': 'status-pending',
		'Delivered': 'status-approved',
		'Partially Delivered': 'status-pending',
		'Stopped': 'status-cancelled',
		'Rejected': 'status-cancelled',
		'Transfer': 'status-approved',
		'Issue': 'status-cancelled',
		'Manufacture': 'status-pending',
		'Quotation': 'status-quotation',
		'Ordered': 'status-ordered',
		'Awarded': 'status-awarded',
		'Evaluated': 'status-evaluated',
		'Expired': 'status-cancelled',
		'Under Review': 'status-pending',
		'Bid Received': 'status-bid',
		'Bid Evaluated': 'status-evaluated',
		'Bid Awarded': 'status-awarded',
		'Unknown': 'status-pending'
	},

	WORKFLOW_BORDERS: {
		'Draft': 'border-draft',
		'Pending': 'border-pending',
		'Pending Approval': 'border-pending',
		'Approved': 'border-approved',
		'Cancelled': 'border-cancelled',
		'Received': 'border-received',
		'Open': 'border-pending',
		'Closed': 'border-approved',
		'Quotation': 'border-pending',
		'Awarded': 'border-approved',
		'Evaluated': 'border-approved'
	},

	init: function (page) {
		this.page = page;
		this.setup_events();
		this.setup_project_link();
		this.setup_assigned_to_link();
		this.set_default_dates();
		this.apply_route_filters();

		this.fetch_report_data();
	},

	setup_assigned_to_link: function () {
		this.assigned_to_control = frappe.ui.form.make_control({
			parent: $('#assigned-to-filter'),
			df: {
				fieldtype: 'Link',
				label: 'Assigned To',
				fieldname: 'assigned_to',
				options: 'User',
				placeholder: 'Select User'
			},
			render_input: true
		});
	},

	apply_route_filters: function () {
		let filters_applied = false;
		const route = frappe.get_route();
		const params = new URLSearchParams(window.location.search);

		if (route.length > 1 && route[0] === 'po-details-report') {
			const mrId = route[1];
			$('#filter-material-request').val(mrId);
			filters_applied = true;
		}

		if (params.get("assigned_to") && this.assigned_to_control) {
			this.assigned_to_control.set_value(params.get("assigned_to"));
			filters_applied = true;
		}

		if (frappe.route_options) {
			if (frappe.route_options.project && this.project_control) {
				this.project_control.set_value(frappe.route_options.project);
				filters_applied = true;
			}

			if (frappe.route_options.material_request) {
				$('#filter-material-request').val(frappe.route_options.material_request);
				filters_applied = true;
			}

			if (frappe.route_options.from_date) {
				$('#filter-from-date').val(frappe.route_options.from_date);
				filters_applied = true;
			}

			if (frappe.route_options.to_date) {
				$('#filter-to-date').val(frappe.route_options.to_date);
				filters_applied = true;
			}

			frappe.route_options = null;
		}

		return filters_applied;
	},

	setup_events: function () {
		const self = this;

		$('#btn-fetch-data').on('click', function () {
			self.fetch_report_data();
		});

		$('#btn-refresh').on('click', function () {
			self.fetch_report_data();
		});

		$('#btn-clear-filters').on('click', function () {
			self.clear_filters();
		});

		$('#filter-material-request').on('keyup', function (e) {
			self.apply_mr_search();
		});
	},

	setup_project_link: function () {
		this.project_control = frappe.ui.form.make_control({
			parent: $('#project-filter'),
			df: {
				fieldtype: 'Link',
				label: 'Project',
				fieldname: 'project',
				options: 'Project',
				placeholder: 'Select Project'
			},
			render_input: true
		});
	},

	set_default_dates: function () {
		const from_date = frappe.datetime.month_start();
		const to_date = frappe.datetime.month_end();
		$('#filter-from-date').val(from_date);
		$('#filter-to-date').val(to_date);
	},

	clear_filters: function () {
		$('#filter-material-request').val('');
		$('#filter-purpose').val('Purchase');
		if (this.project_control) {
			this.project_control.set_value('');
		}
		this.set_default_dates();
		this.apply_mr_search();
	},

	get_filters: function () {
		return {
			project: this.project_control ? (this.project_control.get_value() || null) : null,
			assigned_to: this.assigned_to_control ? (this.assigned_to_control.get_value() || "") : "",
			from_date: $('#filter-from-date').val() || null,
			to_date: $('#filter-to-date').val() || null,
			material_request_purpose: $('#filter-purpose').val() || 'Purchase'
		};
	},
	

	fetch_report_data: function () {
		const self = this;
		const filters = this.get_filters();

		$('#loading').show();
		$('#report-data').html('');

		frappe.call({
			method: 'frappe.desk.query_report.run',
			args: {
				report_name: 'Purchase Orde Details',
				filters: filters,
				ignore_prepared_report: 1
			},
			callback: function (r) {
				$('#loading').hide();

				if (r.message) {
					self.reportData = r.message.result || [];
					const processedData = self.process_data(self.reportData);
					self.render_report_data(processedData);
					self.apply_mr_search();
				} else {
					$('#report-data').html('<div class="alert alert-warning">No data found</div>');
				}
			},
			error: function (err) {
				$('#loading').hide();
				$('#report-data').html('<div class="alert alert-danger">Error loading report data</div>');
				console.error(err);
			}
		});
	},

	process_data: function (rows) {
		const groupedData = {};

		if (!rows || rows.length === 0) {
			return [];
		}

		// Group by material request
		rows.forEach(row => {
			if (row.indent === 0) {
				groupedData[row.material_request] = {
					materialRequest: row.material_request,
					mrStatus: row.mr_status,
					mrWorkflowState: row.mr_workflow_state,
					documents: {
						materialRequest: row.material_request,
						mrStatus: row.mr_status,
						requestForQuotation: null,
						rfqStatus: null,
						rfqWorkflowState: null,
						bidTabulation: null,
						btStatus: null,
						supplierQuotation: null,
						sqStatus: null,
						purchaseOrder: null,
						poStatus: null,
						poWorkflowState: null,
						poApprovalDate: null,
						poTransactionDate: null,
						purchaseReceipt: null,
						prStatus: null,
						prWorkflowState: null,
						purchaseInvoice: null,
						piStatus: null,
						piWorkflowState: null,
						paymentRequest: null,
						payreqStatus: null,
						payreqWorkflowState: null,
						paymentEntry: null,
						peStatus: null,
						peWorkflowState: null
					},
					rfqs: [],
					purchaseOrders: [],
					items: []
				};
			}
		});

		// Process child rows
		rows.forEach(row => {
			const mr = groupedData[row.material_request];
			if (!mr) return;

			if (row.indent === 1 && row.document_type === "Request for Quotation") {
				const rfqObj = {
					requestForQuotation: row.request_for_quotation,
					rfqStatus: row.rfq_status,
					rfqWorkflowState: row.rfq_workflow_state,
					bidTabulation: row.bid_tabulation,
					btStatus: row.bt_status,
					supplierQuotation: row.supplier_quotation,
					sqStatus: row.sq_status
				};

				mr.rfqs.push(rfqObj);

				// Update MR's document references with first RFQ
				if (!mr.documents.requestForQuotation) {
					mr.documents.requestForQuotation = row.request_for_quotation;
					mr.documents.rfqStatus = row.rfq_status;
					mr.documents.rfqWorkflowState = row.rfq_workflow_state;
				}

				// Set Bid Tabulation if exists
				if (row.bid_tabulation && row.bid_tabulation !== 'None' && row.bid_tabulation !== 'NULL') {
					mr.documents.bidTabulation = row.bid_tabulation;
					mr.documents.btStatus = row.bt_status;
				}

				// Set Supplier Quotation if exists
				if (row.supplier_quotation && row.supplier_quotation !== 'None' && row.supplier_quotation !== 'NULL') {
					mr.documents.supplierQuotation = row.supplier_quotation;
					mr.documents.sqStatus = row.sq_status;
				}
			} else if (row.indent === 1 && row.document_type === "Purchase Order") {
				const poObj = {
					purchaseOrder: row.purchase_order,
					poStatus: row.po_status,
					poWorkflowState: row.po_workflow_state,
					poApprovalDate: row.po_approval_date,
					poTransactionDate: row.po_transaction_date,
					requestForQuotation: row.request_for_quotation,
					rfqStatus: row.rfq_status,
					rfqWorkflowState: row.rfq_workflow_state,
					bidTabulation: row.bid_tabulation,
					btStatus: row.bt_status,
					supplierQuotation: row.supplier_quotation,
					sqStatus: row.sq_status,
					purchaseReceipt: row.purchase_receipt,
					prStatus: row.pr_status,
					prWorkflowState: row.pr_workflow_state,
					purchaseInvoice: row.purchase_invoice,
					piStatus: row.pi_status,
					piWorkflowState: row.pi_workflow_state,
					paymentRequest: row.payment_request,
					payreqStatus: row.payreq_status,
					payreqWorkflowState: row.payreq_workflow_state,
					paymentEntry: row.payment_entry,
					peStatus: row.pe_status,
					peWorkflowState: row.pe_workflow_state,
					items: []
				};

				mr.purchaseOrders.push(poObj);

				// Update MR's document references with first PO's downstream data
				if (!mr.documents.purchaseOrder) {
					mr.documents.purchaseOrder = row.purchase_order;
					mr.documents.poStatus = row.po_status;
					mr.documents.poWorkflowState = row.po_workflow_state;
					mr.documents.poApprovalDate = row.po_approval_date;
					mr.documents.poTransactionDate = row.po_transaction_date;

					// Set Purchase Receipt data
					mr.documents.purchaseReceipt = row.purchase_receipt;
					mr.documents.prStatus = row.pr_status;
					mr.documents.prWorkflowState = row.pr_workflow_state;

					// Set Purchase Invoice data
					mr.documents.purchaseInvoice = row.purchase_invoice;
					mr.documents.piStatus = row.pi_status;
					mr.documents.piWorkflowState = row.pi_workflow_state;

					// Set Payment Request data
					mr.documents.paymentRequest = row.payment_request;
					mr.documents.payreqStatus = row.payreq_status;
					mr.documents.payreqWorkflowState = row.payreq_workflow_state;

					// Set Payment Entry data
					mr.documents.paymentEntry = row.payment_entry;
					mr.documents.peStatus = row.pe_status;
					mr.documents.peWorkflowState = row.pe_workflow_state;
				}

				// Also set RFQ, BT, SQ if not already set
				if (row.request_for_quotation && !mr.documents.requestForQuotation) {
					mr.documents.requestForQuotation = row.request_for_quotation;
					mr.documents.rfqStatus = row.rfq_status;
					mr.documents.rfqWorkflowState = row.rfq_workflow_state;
				}

				if (row.bid_tabulation && !mr.documents.bidTabulation) {
					mr.documents.bidTabulation = row.bid_tabulation;
					mr.documents.btStatus = row.bt_status;
				}

				if (row.supplier_quotation && !mr.documents.supplierQuotation) {
					mr.documents.supplierQuotation = row.supplier_quotation;
					mr.documents.sqStatus = row.sq_status;
				}
			} else if (row.indent === 2 && row.document_type === "Purchase Order Item") {
				if (mr.purchaseOrders.length > 0) {
					const lastPO = mr.purchaseOrders[mr.purchaseOrders.length - 1];
					lastPO.items.push({
						itemCode: row.item_code,
						itemName: row.item_name,
						itemGroup: row.item_group,
						qty: row.qty,
						project: row.project,
						scheduleDate: row.schedule_date
					});

					mr.items.push({
						itemCode: row.item_code,
						itemName: row.item_name,
						itemGroup: row.item_group,
						qty: row.qty,
						project: row.project,
						scheduleDate: row.schedule_date
					});
				}
			}
		});

		return Object.values(groupedData);
	},

	render_report_data: function (data) {
		let html = '';

		if (data.length === 0) {
			html = '<div class="alert alert-info">No data found for the selected filters.</div>';
		} else {
			data.forEach((mr, index) => {
				const workflowClass = this.WORKFLOW_BORDERS[mr.mrWorkflowState] || 'border-pending';

				html += '<div class="mr-card ' + workflowClass + '">';
				html += '<div class="d-flex justify-content-between align-items-center mb-2">';
				html += '<div class="mr-id" style="margin-bottom:0;">' +
					'<a href="/app/material-request/' + encodeURIComponent(mr.materialRequest || '') + '" style="color: inherit; text-decoration: none;">' +
					frappe.utils.escape_html(String(mr.materialRequest || '')) + '</a></div>';

				html += '<div class="mr-workflow-status" style="margin-top:0;">';
				html += '<div class="status-section text-right mr-3">';
				html += '<div class="status-label">MR Workflow</div>';
				html += '<div class="status-value">' + this.create_status_badge(mr.mrWorkflowState) + '</div>';
				html += '</div>';
				html += '<div class="status-section text-right">';
				html += '<div class="status-label">MR Status</div>';
				html += '<div class="status-value">' + this.create_status_badge(mr.mrStatus) + '</div>';
				html += '</div>';
				html += '</div>';
				html += '</div>';

				html += '<h6 style="margin-bottom: 20px; font-weight:600; color:#6c757d; font-size: 14px;">DOCUMENT FLOW</h6>';
				html += '<div class="doc-flow-track">';

				// Material Request
				html += this.create_document_flow_step(1, 'Material Request', mr.materialRequest, mr.mrStatus, '#9b59b6', 'Material Request', mr.mrWorkflowState);
				html += '<div class="flow-arrow">→</div>';

				// RFQ
				html += this.create_document_flow_step(2, 'Request for Quotation', mr.documents.requestForQuotation, mr.documents.rfqStatus, '#3498db', 'Request for Quotation', mr.documents.rfqWorkflowState);
				html += '<div class="flow-arrow">→</div>';

				// Supplier Quotation - Separate card
				html += this.create_document_flow_step(3, 'Supplier Quotation', mr.documents.supplierQuotation, mr.documents.sqStatus, '#16a085', 'Supplier Quotation', null);
				html += '<div class="flow-arrow">→</div>';

				// Bid Tabulation - Separate card
				html += this.create_document_flow_step(3.5, 'Bid Tabulation', mr.documents.bidTabulation, mr.documents.btStatus, '#e67e22', 'Bid Tabulation Discussion', null);
				html += '<div class="flow-arrow">→</div>';

				// PO
				html += this.create_document_flow_step(4, 'Purchase Order', mr.documents.purchaseOrder, mr.documents.poStatus, '#e67e22', 'Purchase Order', mr.documents.poWorkflowState);
				html += '<div class="flow-arrow">→</div>';

				// PR
				html += this.create_document_flow_step(5, 'Purchase Receipt', mr.documents.purchaseReceipt, mr.documents.prStatus, '#8e44ad', 'Purchase Receipt', mr.documents.prWorkflowState);
				html += '<div class="flow-arrow">→</div>';

				// PI
				html += this.create_document_flow_step(6, 'Purchase Invoice', mr.documents.purchaseInvoice, mr.documents.piStatus, '#f39c12', 'Purchase Invoice', mr.documents.piWorkflowState);
				html += '<div class="flow-arrow">→</div>';

				// Payment Request
				html += this.create_document_flow_step(7, 'Payment Request', mr.documents.paymentRequest, mr.documents.payreqStatus, '#e74c3c', 'Payment Request', mr.documents.payreqWorkflowState);
				html += '<div class="flow-arrow">→</div>';

				// Payment Entry
				html += this.create_document_flow_step(8, 'Payment Entry', mr.documents.paymentEntry, mr.documents.peStatus, '#27ae60', 'Payment Entry', mr.documents.peWorkflowState);

				html += '</div>'; // End doc-flow-track

				// Show detailed RFQs, Supplier Quotations, and Bid Tabulations
				if (mr.rfqs.length > 0) {
					html += '<div style="margin-top: 20px;">';
					html += '<h6 style="font-weight:600; color:#6c757d; font-size: 14px;">QUOTATION DETAILS</h6>';

					mr.rfqs.forEach((rfq, rfqIndex) => {
						html += '<div class="rfq-section">';
						html += '<div class="bid-section">';

						// RFQ Header
						html += '<div class="bid-header">';
						html += '<div class="bid-title">';
						html += '<i class="fa fa-file-text-o text-primary mr-2"></i>';
						html += '<a href="/app/request-for-quotation/' + encodeURIComponent(rfq.requestForQuotation || '') + '" class="text-decoration-none font-weight-bold" style="color: #2c3e50;">' +
							frappe.utils.escape_html(String(rfq.requestForQuotation || '')) + '</a>';
						html += '</div>';
						html += '<div class="bid-status">' + this.create_status_badge(rfq.rfqStatus) + '</div>';
						html += '</div>';

						html += '<div class="bid-docs">';

						// Supplier Quotations
						if (rfq.supplierQuotation && rfq.supplierQuotation !== 'null' && rfq.supplierQuotation !== 'None') {
							const sqDocs = String(rfq.supplierQuotation).split(', ');
							sqDocs.forEach((sqDoc, idx) => {
								html += '<div class="bid-doc-item">';
								html += '<div class="bid-doc-name">';
								html += '<i class="fa fa-quote-right text-success mr-2"></i>';
								html += '<a href="/app/supplier-quotation/' + encodeURIComponent(sqDoc.trim()) + '" class="multi-doc-link">' +
									frappe.utils.escape_html(sqDoc.trim()) + '</a>';
								html += '</div>';
								html += '<div class="bid-doc-status">' + this.create_status_badge(rfq.sqStatus) + '</div>';
								html += '</div>';
							});
						}

						// Bid Tabulations
						if (rfq.bidTabulation && rfq.bidTabulation !== 'null' && rfq.bidTabulation !== 'None') {
							const btDocs = String(rfq.bidTabulation).split(', ');
							btDocs.forEach((btDoc, idx) => {
								html += '<div class="bid-doc-item">';
								html += '<div class="bid-doc-name">';
								html += '<i class="fa fa-gavel text-warning mr-2"></i>';
								html += '<a href="/app/bid-tabulation-discussion/' + encodeURIComponent(btDoc.trim()) + '" class="multi-doc-link">' +
									frappe.utils.escape_html(btDoc.trim()) + '</a>';
								html += '</div>';
								html += '<div class="bid-doc-status">' + this.create_status_badge(rfq.btStatus) + '</div>';
								html += '</div>';
							});
						}

						// If no supplier quotations or bid tabulations
						if ((!rfq.supplierQuotation || rfq.supplierQuotation === 'None') &&
							(!rfq.bidTabulation || rfq.bidTabulation === 'None')) {
							html += '<div class="bid-doc-item">';
							html += '<div class="bid-doc-name text-muted">';
							html += '<i class="fa fa-info-circle mr-2"></i>No quotations or bids received yet';
							html += '</div>';
							html += '</div>';
						}

						html += '</div>'; // End bid-docs
						html += '</div>'; // End bid-section
						html += '</div>'; // End rfq-section
					});
					html += '</div>'; // End container
				}

				// Purchase Order Items (Collapsible)
				if (mr.items.length > 0) {
					html += this.create_purchase_order_items(index, mr.items);
				}

				// Show all Purchase Orders for this MR
				if (mr.purchaseOrders.length > 0) {
					html += '<div style="margin-top: 20px; border-top: 1px dashed #dee2e6; padding-top: 15px;">';
					html += '<h6 style="font-weight:600; color:#6c757d; font-size: 14px;">PURCHASE ORDERS</h6>';

					mr.purchaseOrders.forEach((po, poIndex) => {
						html += '<div class="card mb-2" style="border-left: 4px solid #3498db;">';
						html += '<div class="card-body p-3">';
						html += '<div class="d-flex justify-content-between align-items-center">';
						html += '<div>';
						html += '<a href="/app/purchase-order/' + encodeURIComponent(po.purchaseOrder || '') + '" class="font-weight-bold" style="color: #2c3e50; text-decoration: none;">' + frappe.utils.escape_html(String(po.purchaseOrder || '')) + '</a>';
						html += '<div class="text-muted small mt-1">';
						html += 'Status: ' + this.create_status_badge(po.poStatus) + ' | ';
						html += 'Workflow: ' + frappe.utils.escape_html(String(po.poWorkflowState || '-')) + ' | ';
						html += 'Approval: ' + frappe.utils.escape_html(String(po.poApprovalDate || '-')) + ' | ';
						html += 'Items: ' + po.items.length;
						html += '</div>';
						html += '</div>';
						html += '<div>';
						if (po.purchaseReceipt) {
							html += '<div class="text-success small"><i class="fa fa-check-circle"></i> Receipt: ' + frappe.utils.escape_html(String(po.purchaseReceipt)) + '</div>';
						}
						if (po.purchaseInvoice) {
							html += '<div class="text-info small"><i class="fa fa-file-invoice"></i> Invoice: ' + frappe.utils.escape_html(String(po.purchaseInvoice)) + '</div>';
						}
						if (po.paymentRequest) {
							html += '<div class="text-warning small"><i class="fa fa-money"></i> PayReq: ' + frappe.utils.escape_html(String(po.paymentRequest)) + '</div>';
						}
						if (po.paymentEntry) {
							html += '<div class="text-success small"><i class="fa fa-check"></i> Payment: ' + frappe.utils.escape_html(String(po.paymentEntry)) + '</div>';
						}
						html += '</div>';
						html += '</div>';

						// Show associated Supplier Quotation and Bid Tabulation for this PO
						if ((po.supplierQuotation && po.supplierQuotation !== 'None') ||
							(po.bidTabulation && po.bidTabulation !== 'None')) {
							html += '<div class="mt-3 pt-3 border-top">';
							html += '<div class="text-muted small">';
							if (po.supplierQuotation && po.supplierQuotation !== 'None') {
								html += '<div><i class="fa fa-quote-right text-success mr-2"></i>Supplier Quote: ' +
									po.supplierQuotation + '</div>';
							}
							if (po.bidTabulation && po.bidTabulation !== 'None') {
								html += '<div><i class="fa fa-gavel text-warning mr-2"></i>Bid Tabulation: ' +
									po.bidTabulation + '</div>';
							}
							html += '</div>';
							html += '</div>';
						}

						html += '</div>';
						html += '</div>';
					});
					html += '</div>';
				}

				html += '</div>'; // End mr-card
			});
		}

		$('#report-data').html(html);
	},

	create_bid_quotation_step: function (mr, index) {
		const hasSupplierQuotation = mr.documents.supplierQuotation && mr.documents.supplierQuotation !== 'None';
		const hasBidTabulation = mr.documents.bidTabulation && mr.documents.bidTabulation !== 'None';

		let html = '<div class="doc-flow-step">';
		html += '<div class="step-title" style="text-align:center; font-size:12px; margin-bottom:5px;">Quotation/Bid</div>';

		if (!hasSupplierQuotation && !hasBidTabulation) {
			html += '<div class="doc-box p-3 text-center" style="border: 1px dashed #dee2e6; border-radius: 8px; background: #f8f9fa;">';
			html += '<div style="color: #dee2e6; font-size: 20px; margin-bottom: 5px;">📄</div>';
			html += '<div class="empty-doc">-</div>';
			html += '</div>';
		} else {
			const color = '#16a085';
			html += '<div class="doc-box p-3 text-center" style="border: 1px solid ' + color + '; border-radius: 8px; background: white;" ' +
				'onclick="po_details_report.toggleQuotationDetails(' + index + ')">';

			html += '<div style="color: ' + color + '; font-size: 20px; margin-bottom: 5px;">📄</div>';

			// Count documents
			const sqCount = hasSupplierQuotation ? String(mr.documents.supplierQuotation).split(', ').length : 0;
			const btCount = hasBidTabulation ? String(mr.documents.bidTabulation).split(', ').length : 0;
			const totalCount = sqCount + btCount;

			html += '<div style="font-weight: bold; font-size: 13px; margin-bottom: 5px;">';
			if (hasSupplierQuotation && hasBidTabulation) {
				html += 'Quotation + Bid';
			} else if (hasSupplierQuotation) {
				html += 'Supplier Quotation';
			} else if (hasBidTabulation) {
				html += 'Bid Tabulation';
			}
			if (totalCount > 1) {
				html += ' <span class="count-badge">' + totalCount + '</span>';
			}
			html += '</div>';

			// Show combined status or individual statuses
			if (hasSupplierQuotation && hasBidTabulation) {
				html += '<div style="margin-bottom: 5px;">' +
					this.create_status_badge(mr.documents.sqStatus || mr.documents.btStatus) +
					'</div>';
			} else if (hasSupplierQuotation) {
				html += '<div style="margin-bottom: 5px;">' +
					this.create_status_badge(mr.documents.sqStatus) +
					'</div>';
			} else if (hasBidTabulation) {
				html += '<div style="margin-bottom: 5px;">' +
					this.create_status_badge(mr.documents.btStatus) +
					'</div>';
			}

			html += '<div style="font-size: 11px; color: #3498db; cursor: pointer;">';
			html += '<i class="fa fa-list"></i> View Details';
			html += '</div>';

			html += '</div>';

			// Create a hidden details container
			html += '<div id="quotation-details-' + index + '" style="display: none; margin-top: 10px; background: #f8f9fa; border-radius: 6px; padding: 10px;">';
			if (hasSupplierQuotation) {
				const sqDocs = String(mr.documents.supplierQuotation).split(', ');
				html += '<div class="multi-doc-container">';
				sqDocs.forEach((doc, idx) => {
					html += '<div class="multi-doc-item">';
					html += '<a href="/app/supplier-quotation/' + doc.trim() + '" class="multi-doc-link">' +
						doc.trim() + '</a>';
					html += '<div>' + this.create_status_badge(mr.documents.sqStatus) + '</div>';
					html += '</div>';
				});
				html += '</div>';
			}
			if (hasBidTabulation) {
				const btDocs = String(mr.documents.bidTabulation).split(', ');
				html += '<div class="multi-doc-container">';
				btDocs.forEach((doc, idx) => {
					html += '<div class="multi-doc-item">';
					html += '<a href="/app/bid-tabulation-discussion/' + doc.trim() + '" class="multi-doc-link">' +
						doc.trim() + '</a>';
					html += '<div>' + this.create_status_badge(mr.documents.btStatus) + '</div>';
					html += '</div>';
				});
				html += '</div>';
			}
			html += '</div>';
		}

		html += '</div>';
		return html;
	},

	create_document_flow_step: function (stepNumber, title, docValue, status, color, docType, workflowState) {
		let html = '<div class="doc-flow-step">';
		html += '<div class="step-title" style="text-align:center; font-size:12px; margin-bottom:5px;">' + title + '</div>';

		if (!docValue || docValue === 'None' || docValue === 'NULL' || docValue === '-' || docValue === 'null') {
			html += '<div class="doc-box p-3 text-center" style="border: 1px dashed #dee2e6; border-radius: 8px; background: #f8f9fa;">';
			html += '<div style="color: #dee2e6; font-size: 20px; margin-bottom: 5px;">📄</div>';
			html += '<div class="empty-doc">-</div>';
			html += '</div>';
		} else {
			// Clean the status (remove HTML formatting from report)
			const cleanStatus = String(status || '').replace(/<[^>]*>/g, '').replace(/●\s*/g, '').trim();

			// Handle multiple docs (comma separated)
			const docs = String(docValue).split(', ');
			const mainDoc = docs[0].trim();
			const count = docs.length;

			html += '<div class="doc-box p-3 text-center" style="border: 1px solid ' + color + '; border-radius: 8px; background: white;" ' +
				'onclick="po_details_report.open_document(\'' + mainDoc + '\', \'' + (docType || title) + '\')">';

			html += '<div style="color: ' + color + '; font-size: 20px; margin-bottom: 5px;">📄</div>';

			html += '<div style="font-weight: bold; font-size: 13px; margin-bottom: 5px; word-break: break-all;">' +
				frappe.utils.escape_html(mainDoc) +
				(count > 1 ? ' <span class="count-badge">+' + (count - 1) + '</span>' : '') +
				'</div>';

			if (cleanStatus && cleanStatus !== 'null' && cleanStatus !== 'None') {
				html += '<div style="margin-bottom: 5px;">' + this.create_status_badge(cleanStatus) + '</div>';
			}

			html += '<div style="font-size: 11px; color: #3498db; cursor: pointer;">';
			html += '<i class="fa fa-external-link"></i> Click to open';
			html += '</div>';

			if (workflowState && workflowState !== 'None' && workflowState !== 'NULL' && workflowState !== 'null') {
				const cleanWorkflow = String(workflowState || '').replace(/<[^>]*>/g, '').trim();
				const cleanWorkflowShort = cleanWorkflow.split(',')[0].trim();
				html += '<div class="mt-1" style="font-size: 11px;">Workflow: ' + this.create_status_badge(cleanWorkflowShort) + '</div>';
			}

			html += '</div>';
		}

		html += '</div>';
		return html;
	},

	create_purchase_order_items: function (index, items) {
		if (!items || items.length === 0) return '';

		let html = '<div style="margin-top: 15px; border-top: 1px dashed #dee2e6; padding-top: 15px;">';
		html += '<div class="items-toggle" onclick="po_details_report.toggleItems(' + index + ')" style="font-size: 13px;">';
		html += '<span id="toggle-icon-' + index + '" style="margin-right: 5px;">▶</span>';
		html += '<span><strong>Purchase Order Items</strong> (' + items.length + ' items)</span>';
		html += '</div>';

		html += '<div class="items-container" id="items-container-' + index + '">';
		html += '<div class="table-responsive" style="margin-top: 10px;">';
		html += '<table class="table table-bordered table-sm" style="font-size: 12px;">';
		html += '<thead class="thead-light"><tr>';
		html += '<th>Item Code</th><th>Item Name</th><th>Item Group</th><th>Quantity</th><th>Project</th><th>Schedule Date</th>';
		html += '</tr></thead><tbody>';

		items.forEach((item, idx) => {
			html += '<tr>';
			html += '<td>' + frappe.utils.escape_html(String(item.itemCode || '-')) + '</td>';
			html += '<td>' + frappe.utils.escape_html(String(item.itemName || '-')) + '</td>';
			html += '<td>' + frappe.utils.escape_html(String(item.itemGroup || '-')) + '</td>';
			html += '<td>' + frappe.utils.escape_html(String(item.qty || '-')) + '</td>';
			html += '<td>' + frappe.utils.escape_html(String(item.project || '-')) + '</td>';
			html += '<td>' + frappe.utils.escape_html(String(item.scheduleDate || '-')) + '</td>';
			html += '</tr>';
		});

		html += '</tbody></table>';
		html += '</div></div></div>';

		return html;
	},

	create_status_badge: function (status) {
		if (!status || status === 'null' || status === 'None') return '-';

		// Extract the first status if there are multiple
		const firstStatus = String(status).split(',')[0].trim();
		const statusClass = this.STATUS_COLORS[firstStatus] || 'status-pending';

		return '<span class="status-badge ' + frappe.utils.escape_html(statusClass) + '">' +
			'<span style="margin-right:4px;">●</span>' + frappe.utils.escape_html(firstStatus) +
			'</span>';
	},

	toggleItems: function (index) {
		const container = $('#items-container-' + index);
		const icon = $('#toggle-icon-' + index);

		if (container.hasClass('expanded')) {
			container.removeClass('expanded');
			icon.text('▶');
		} else {
			container.addClass('expanded');
			icon.text('▼');
		}
	},

	toggleQuotationDetails: function (index) {
		const details = $('#quotation-details-' + index);
		details.toggle();
	},

	apply_mr_search: function () {
		const txt = $('#filter-material-request').val().toLowerCase();
		if (!txt) {
			$('.mr-card').show();
			return;
		}
		$('.mr-card').each(function () {
			const mrId = $(this).find('.mr-id a').text().toLowerCase();
			$(this).toggle(mrId.includes(txt));
		});
	},

	open_document: function (docId, docType) {
		if (docId && docId !== '-' && docId !== 'None' && docId !== 'NULL' && docId !== 'null') {
			frappe.set_route('Form', docType, docId);
		}
	}
};




