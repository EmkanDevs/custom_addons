frappe.pages['emloyee-custody-dash'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Employee Custody Dashboard',
        single_column: true
    });

    // 🔍 Employee Filter
    let employee = page.add_field({
        label: 'Employee',
        fieldtype: 'Link',
        fieldname: 'employee',
        options: 'Employee',

        get_query() {
            // 👇 Apply filter based on checkbox
            if (active_only && active_only.get_value()) {
                return {
                    filters: {
                        status: 'Active'
                    }
                };
            } else {
                return {};
            }
        },
        
        change() {
            const emp = employee.get_value();
        
            if (emp) {
                load_employee_details(emp);   
                load_all(emp); 
                load_equipment_tools(emp);        
            }
        }
    });

    let active_only = page.add_field({
        label: 'Active Only',
        fieldtype: 'Check',
        fieldname: 'active_only',
        default: 1,
    
        change() {
            const emp = employee.get_value();
            if (emp) {
                load_it_assets(emp);
                load_sim_cards(emp);
            }
        }
    });

    // ===========================
    // 🖨️ SHARED LETTERHEAD STYLES
    // ===========================
    const LETTERHEAD_HEADER_IMG = '/files/Incharge Logo.png';
    const LETTERHEAD_FOOTER_IMG = '/files/Incharge Logo.png';

    const LETTERHEAD_STYLES = `
        body {
            font-family: Arial, sans-serif;
            padding: 0;
            margin: 0;
            color: #333;
        }
        .page-wrapper {
            padding: 20px 30px;
        }
        .letterhead-header {
            width: 45%;
            display: block;
            margin-bottom: 0;
        }
        .letterhead-header img {
            width: 45%;
            max-width: 220px;
            display: block;
            margin: 10px 20px;
        }
        .letterhead-footer {
            width: 45%;
            display: block;
            margin-top: 30px;
            position: fixed;
            bottom: 0;
            left: 0;
        }
        .letterhead-footer img {
            width: 45%;
            display: block;                                                                                 
        }
        .print-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 12px;
            margin-bottom: 16px;
            margin-top: 10px;
        }
        .print-header h2 {
            margin: 0 0 4px 0;
            color: #222;
        }
        .print-header .meta {
            font-size: 13px;
            color: #555;
            line-height: 1.6;
        }
        .print-header .date {
            font-size: 12px;
            color: #888;
            text-align: right;
        }
        .tab-title {
            font-size: 15px;
            font-weight: 600;
            color: #4CAF50;
            margin-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        th {
            background: #f0f4f0;
            padding: 8px 10px;
            text-align: left;
            border: 1px solid #ddd;
            font-weight: 600;
        }
        td {
            padding: 7px 10px;
            border: 1px solid #ddd;
        }
        tr:nth-child(even) td {
            background: #fafafa;
        }
        .badge {
            padding: 3px 8px;
            border-radius: 10px;
            color: white;
            font-size: 12px;
            display: inline-block;
        }
        a {
            color: #333;
            text-decoration: none;
        }
        @media print {
            body { padding: 0; margin: 0; }
            .badge, span[style] {
                color: #000 !important;
                background: transparent !important;
                -webkit-print-color-adjust: exact;
            }
            .letterhead-footer {
                position: fixed;
                bottom: 0;
                left: 0;
            }
        }
    `;

    const ALL_SECTIONS_STYLES = `
        body {
            font-family: Arial, sans-serif;
            padding: 0;
            margin: 0;
            color: #333;
            font-size: 13px;
        }
        .page-wrapper {
            padding: 20px 30px;
            padding-bottom: 120px;
        }
        .letterhead-header {
            width: 35%;
            display: block;
        }
        .letterhead-header img {
            width: 35%;
            display: block;
        }
        .letterhead-footer {
            width: 35%;
            display: block;
            position: fixed;
            bottom: 0;
            left: 0;
        }
        .letterhead-footer img {
            width: 35%;
            display: block;
        }
        .print-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 12px;
            margin-bottom: 20px;
            margin-top: 10px;
        }
        .print-header h2 {
            margin: 0 0 4px 0;
            color: #222;
            font-size: 18px;
        }
        .print-header .meta {
            font-size: 13px;
            color: #555;
            line-height: 1.8;
        }
        .print-header .date {
            font-size: 12px;
            color: #888;
            text-align: right;
        }
        .section {
            margin-bottom: 28px;
            page-break-inside: avoid;
        }
        .section-title {
            font-size: 14px;
            font-weight: 700;
            color: #4CAF50;
            border-left: 4px solid #4CAF50;
            padding-left: 8px;
            margin-bottom: 8px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }
        th {
            background: #f0f4f0;
            padding: 7px 9px;
            text-align: left;
            border: 1px solid #ddd;
            font-weight: 600;
        }
        td {
            padding: 6px 9px;
            border: 1px solid #ddd;
            vertical-align: top;
        }
        tr:nth-child(even) td {
            background: #fafafa;
        }
        a {
            color: #333;
            text-decoration: none;
        }
        .badge, span[style] {
            font-size: 11px;
            font-weight: 600;
        }
        @media print {
            body { padding: 0; margin: 0; }
            .section { page-break-inside: avoid; }
            .letterhead-footer {
                position: fixed;
                bottom: 0;
                left: 0;
            }
            .badge, span[style] {
                color: #000 !important;
                background: transparent !important;
                padding: 2px 6px;
                border-radius: 4px;
            }
        }
    `;

    page.add_button('Print', function() {
        const active_tab = $('.custody-tab.active').data('tab');
        const tab_title = $('.custody-tab.active').text().trim();
        const content = $('#' + active_tab).html();

        const emp_name = $('#emp_name').text();
        const emp_dept = $('#emp_dept').text();
        const emp_desig = $('#emp_desig').text();
        const emp_id = employee.get_value();

        const print_window = window.open('', '_blank');
        print_window.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>${tab_title} - ${emp_name}</title>
                <style>${LETTERHEAD_STYLES}</style>
            </head>
            <body>
                <div class="letterhead-header">
                    <img src="${LETTERHEAD_HEADER_IMG}" alt="Letterhead Header" />
                </div>

                <div class="page-wrapper">
                    <div class="print-header">
                        <div>
                            <h2>Employee Custody Dashboard</h2>
                            <div class="meta">
                                <strong>Employee ID:</strong> ${emp_id}<br>
                                <strong>Name:</strong> ${emp_name}<br>
                                <strong>Department:</strong> ${emp_dept} &nbsp;|&nbsp;
                                <strong>Designation:</strong> ${emp_desig}
                            </div>
                        </div>
                        <div class="date">
                            Printed on: ${frappe.datetime.now_datetime()}
                        </div>
                    </div>

                    <div class="tab-title">${tab_title}</div>

                    ${content}
                </div>

                <div class="letterhead-footer">
                    <img src="${LETTERHEAD_FOOTER_IMG}" alt="Letterhead Footer" />
                </div>

                <script>
                    window.onload = function() {
                        window.print();
                        window.onafterprint = function() { window.close(); };
                    };
                <\/script>
            </body>
            </html>
        `);
        print_window.document.close();
    }, 'btn-default');

    page.add_button('Print All Custodies', function() {
        const emp_name = $('#emp_name').text();
        const emp_dept = $('#emp_dept').text();
        const emp_desig = $('#emp_desig').text();
        const emp_id = employee.get_value();

        if (!emp_id) {
            frappe.msgprint('Please select an employee first.');
            return;
        }

        const tabs = [
            { id: 'it_assets',         title: 'IT Assets' },
            { id: 'sim_cards',         title: 'SIM Cards' },
            { id: 'vehicles',          title: 'Vehicles' },
            { id: 'employee_custody',  title: 'Employee Advance' },
            { id: 'medical_insurance', title: 'Medical Insurance' }
        ];

        let all_content = '';
        tabs.forEach(tab => {
            all_content += `
                <div class="section">
                    <div class="section-title">${tab.title}</div>
                    ${$('#' + tab.id).html()}
                </div>
            `;
        });

        const print_window = window.open('', '_blank');
        print_window.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>All Custodies - ${emp_name}</title>
                <style>${ALL_SECTIONS_STYLES}</style>
            </head>
            <body>
                <div class="letterhead-header">
                    <img src="${LETTERHEAD_HEADER_IMG}" alt="Letterhead Header" />
                </div>

                <div class="page-wrapper">
                    <div class="print-header">
                        <div>
                            <h2>Employee Custody Report</h2>
                            <div class="meta">
                                <strong>Employee ID:</strong> ${emp_id}<br>
                                <strong>Name:</strong> ${emp_name}<br>
                                <strong>Department:</strong> ${emp_dept} &nbsp;|&nbsp;
                                <strong>Designation:</strong> ${emp_desig}
                            </div>
                        </div>
                        <div class="date">
                            Printed on:<br>${frappe.datetime.now_datetime()}
                        </div>
                    </div>

                    ${all_content}
                </div>

                <div class="letterhead-footer">
                    <img src="${LETTERHEAD_FOOTER_IMG}" alt="Letterhead Footer" />
                </div>

                <script>
                    window.onload = function() {
                        window.print();
                        window.onafterprint = function() { window.close(); };
                    };
                <\/script>
            </body>
            </html>
        `);
        print_window.document.close();
    }, 'btn-primary');

    // ✅ AUTO SET EMPLOYEE (SESSION USER)
    frappe.db.get_value('Employee', {
        user_id: frappe.session.user
    }, 'name').then(r => {

        if (r.message && r.message.name) {
            const emp = r.message.name;

            employee.set_value(emp);

            load_employee_details(emp);
            load_all(emp);
        }
    });

    const route = frappe.get_route();
    const route_options = frappe.route_options;

    if (route_options && route_options.employee) {
        employee.set_value(route_options.employee);

        load_employee_details(route_options.employee);
        load_all(route_options.employee);
    }

    const employee_info_html = `
    <div id="employee_info" style="display:none; margin-top:15px;">
        <div style="
            display:flex;
            gap:15px;
            padding:12px;
            background: linear-gradient(90deg, #f8f9fa, #eef2f7);
            border-radius:10px;
            border-left: 5px solid #4CAF50;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        ">
            <div style="flex:1;">
                <div style="font-size:12px; color:#777;">Employee Name</div>
                <div id="emp_name" style="font-size:16px; font-weight:600;"></div>
            </div>

            <div style="flex:1;">
                <div style="font-size:12px; color:#777;">Department</div>
                <div id="emp_dept" style="font-size:15px; font-weight:500;"></div>
            </div>

            <div style="flex:1;">
                <div style="font-size:12px; color:#777;">Designation</div>
                <div id="emp_desig" style="font-size:15px; font-weight:500;"></div>
            </div>
        </div>
    </div>
`;


$(page.body).append(employee_info_html);

    // =========================
    // 🎨 GOOGLE STYLE TABS + SUMMARY
    // =========================
    const html = `
        <style>
            .custody-tabs {
                display: flex;
                gap: 20px;
                border-bottom: 2px solid #eee;
                margin-top: 15px;
            }

            .custody-tab {
                padding: 10px 5px;
                cursor: pointer;
                font-weight: 500;
                color: #666;
                position: relative;
            }

            .custody-tab.active {
                color: #000;
            }

            .custody-tab.active::after {
                content: "";
                position: absolute;
                bottom: -2px;
                left: 0;
                width: 100%;
                height: 3px;
                background: #4CAF50;
                border-radius: 2px;
            }

            .summary-cards {
                display: flex;
                gap: 15px;
                margin: 15px 0;
            }

            .summary-card {
                flex: 1;
                padding: 12px;
                border-radius: 10px;
                background: #f8f9fa;
                text-align: center;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }

            .summary-card h3 {
                margin: 5px 0;
            }

            .badge {
                padding: 4px 8px;
                border-radius: 10px;
                color: white;
                font-size: 12px;
            }

            .loading {
                text-align: center;
                padding: 20px;
                color: #888;
            }
        </style>

        <div class="summary-cards">
            <div class="summary-card">
                <small>Assets</small>
                <h3 id="total_assets">0</h3>
            </div>
            <div class="summary-card">
                <small>SIM Cards</small>
                <h3 id="total_sims">0</h3>
            </div>
            <div class="summary-card">
                <small>Vehicles</small>
                <h3 id="total_vehicles">0</h3>
            </div>
            <div class="summary-card">
                <small>Pending Amount</small>
                <h3 id="total_pending">0</h3>
            </div>
            <div class="summary-card">
                <small>Insurance Members</small>
                <h3 id="total_insurance">0</h3>
            </div>
        </div>

        <div class="custody-tabs">
            <div class="custody-tab active" data-tab="it_assets">IT Asset</div>
            <div class="custody-tab" data-tab="sim_cards">SIM Card</div>
            <div class="custody-tab" data-tab="vehicles">Vehicles</div>
            <div class="custody-tab" data-tab="employee_custody">Employee Advance</div>
            <div class="custody-tab" data-tab="medical_insurance">Medical Insurance</div>
            <div class="custody-tab" data-tab="equipment_tools">Equipment's & Tools</div>
        </div>

        <div id="it_assets" class="tab-content"></div>
        <div id="sim_cards" class="tab-content" style="display:none;"></div>
        <div id="vehicles" class="tab-content" style="display:none;"></div>
        <div id="employee_custody" class="tab-content" style="display:none;"></div>
        <div id="medical_insurance" class="tab-content" style="display:none;"></div>
        <div id="equipment_tools" class="tab-content" style="display:none;"></div>
        
    `;

    $(page.body).append(html);

    // =========================
    // 🔁 TAB SWITCH
    // =========================
    $(document).on('click', '.custody-tab', function() {
        const tab = $(this).data('tab');

        $('.custody-tab').removeClass('active');
        $(this).addClass('active');

        $('.tab-content').hide();
        $('#' + tab).show();
    });

    function show_loading(target) {
        $(target).html(`<div class="loading">Loading...</div>`);
    }

    function badge(text, color) {
        return `<span class="badge" style="background:${color}">${text}</span>`;
    }

    function get_status_color(status) {
        switch (status) {
            case 'In Use': return 'green';
            case 'In Storage': return 'blue';
            case 'On Hold': return 'orange';
            case 'Cancelled': return 'red';
            case 'Suspended': return 'gray';
            default: return 'black';
        }
    }
    

    // =========================
    // 🔄 LOAD ALL
    // =========================
    function load_all(emp) {
        load_it_assets(emp);
        load_sim_cards(emp);
        load_vehicles(emp);
        load_employee_custody(emp);
        load_medical_insurance(emp);
        load_equipment_tools(emp);
    }

    // =========================
    // IT ASSETS
    // =========================
    function load_it_assets(emp) {
        show_loading('#it_assets');

        frappe.call({
            method: 'custom_addons.custom_addons.page.emloyee_custody_dash.employee_custody_dash.get_it_assets',
            args: { employee: emp ,
                    active_only: active_only.get_value()
                 },
            callback: r => {
                $('#total_assets').text(r.message.length);
                render_it_assets(r.message || []);
            }
        });
    }

    function render_it_assets(data) {
		let html = `
			<table class="table table-bordered">
				<thead>
					<tr>
						<th>Asset ID</th>
						<th>Item</th>
						<th>Item Name</th>
						<th>Item Group</th>
						<th>Manufacturer</th>
						<th>From Date</th>
						<th>To Date</th>
					</tr>
				</thead>
				<tbody>
		`;
	
		if (!data.length) {
			html += `<tr><td colspan="8" class="text-center">No Records Found</td></tr>`;
		} else {
			data.forEach(row => {
				html += `
					<tr>
						<td>
							<a href="/app/it-asset-management/${row.asset_id}" target="_blank">
								${row.asset_id}
							</a>
						</td>
						<td>${row.item || ''}</td>
						<td>${row.item_name || ''}</td>
						<td>${row.item_group || ''}</td>
						<td>${row.manufacturer || ''}</td>
						<td>${row.from_date || ''}</td>
						<td>${row.to_date || ''}</td>
					</tr>
				`;
			});
		}
	
		html += `</tbody></table>`;
		$('#it_assets').html(html);
	}

    // =========================
    // SIM
    // =========================
    function load_sim_cards(emp) {
        show_loading('#sim_cards');

        frappe.call({
            method: 'custom_addons.custom_addons.page.emloyee_custody_dash.employee_custody_dash.get_sim_cards',
            args: { employee: emp ,
                    active_only: active_only.get_value()
                },
            callback: r => {
                $('#total_sims').text(r.message.length);
                render_sim_cards(r.message || []);
            }
        });
    }

    function render_sim_cards(data) {
		let html = `
			<table class="table table-bordered">
				<thead>
					<tr>
						<th>SIM ID</th>
						<th>Service No</th>
						<th>Serial Number</th>
						<th>Reason</th>
						<th>Provider</th>
						<th>From Date</th>
						<th>To Date</th>
						<th>Status</th>
					</tr>
				</thead>
				<tbody>
		`;
	
		if (!data.length) {
			html += `<tr><td colspan="8" class="text-center">No Records Found</td></tr>`;
		} else {
			data.forEach(row => {
				html += `
					<tr>
						<td>
							<a href="/app/sim-management/${row.sim_id}" target="_blank">
								${row.sim_id}
							</a>
						</td>
						<td>${row.service_no || ''}</td>
						<td>${row.serial_number || ''}</td>
						<td>${row.reason_of_purchase || ''}</td>
						<td>${row.sim_provider || ''}</td>
						<td>${row.from_date || ''}</td>
						<td>${row.to_date || ''}</td>
						<td>${badge(row.status, get_status_color(row.status))}</td>
					</tr>
				`;
			});
		}
	
		html += `</tbody></table>`;
		$('#sim_cards').html(html);
	}

    // =========================
    // VEHICLES
    // =========================
    function load_vehicles(emp) {
        show_loading('#vehicles');

        frappe.call({
            method: 'custom_addons.custom_addons.page.emloyee_custody_dash.employee_custody_dash.get_vehicles',
            args: { employee: emp },
            callback: r => {
                $('#total_vehicles').text(r.message.length);
                render_vehicles(r.message || []);
            }
        });
    }

    function render_vehicles(data) {
		let html = `
			<table class="table table-bordered">
				<thead>
					<tr>
						<th>Vehicle ID</th>
						<th>License Plate</th>
						<th>Door Number</th>
						<th>Vehicle Type</th>
						<th>Model Year</th>
					</tr>
				</thead>
				<tbody>
		`;
	
		if (!data.length) {
			html += `<tr><td colspan="6" class="text-center">No Records Found</td></tr>`;
		} else {
			data.forEach(row => {
				html += `
					<tr>
						<td>
							<a href="/app/vehicles/${row.vehicle_id}" target="_blank">
								${row.vehicle_id}
							</a>
						</td>
						<td>${row.license_plate || ''}</td>
						<td>${row.door_number || ''}</td>
						<td>${row.vehicle_types || ''}</td>
						<td>${row.model_year || ''}</td>
					</tr>
				`;
			});
		}
	
		html += `</tbody></table>`;
		$('#vehicles').html(html);
	}

    // =========================
    // EMPLOYEE ADVANCE
    // =========================
    function load_employee_custody(emp) {
        show_loading('#employee_custody');

        frappe.call({
            method: 'custom_addons.custom_addons.page.emloyee_custody_dash.employee_custody_dash.get_employee_custody',
            args: { employee: emp },
            callback: r => {
                let total = 0;
                r.message.forEach(d => total += d.pending_amount || 0);
                $('#total_pending').text(format_currency(total));

                render_employee_custody(r.message || []);
            }
        });
    }

    function load_equipment_tools(emp) {

        show_loading('#equipment_tools');
    
        frappe.call({
            method: 'custom_addons.custom_addons.page.emloyee_custody_dash.employee_custody_dash.get_equipment_tools',
    
            args: {
                employee: emp,
                active_only: active_only.get_value()
            },
    
            callback: r => {

                let total_balance = 0;
            
                (r.message || []).forEach(d => {
                    total_balance += (d.balance_qty || 0);
                });
            
                $('#total_equipment_balance').text(total_balance);
            
                render_equipment_tools(r.message || []);
            }
        });
    }

    function render_employee_custody(data) {
        let html = `
            <table class="table table-bordered" style="background-color: white;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th>Employee ID</th>
                        <th>Name</th>
                        <th>Department</th>
                        <th class="text-right">Expense Claim</th>
                        <th class="text-right">Purchase Invoice</th>
                        <th class="text-right">Pending Amount</th>
                    </tr>
                </thead>
                <tbody>
        `;
    
        if (!data.length) {
            html += `<tr><td colspan="6" class="text-center">No Records Found</td></tr>`;
        } else {
            data.forEach(row => {
                const is_pending = row.pending_amount > 0;
                const color = is_pending ? '#d9534f' : '#28a745';
                const bg_color = is_pending ? '#fff3cd' : '#ffffff';
    
                html += `
                    <tr style="background: ${bg_color};">
                        <td>
                            <a href="/app/employee/${row.employee}" target="_blank" style="font-weight:bold;">
                                ${row.employee}
                            </a>
                        </td>
                        <td>${row.employee_name}</td>
                        <td>${row.department || ''}</td>
                        <td class="text-right">${format_currency(row.total_expense_claim || 0)}</td>
                        <td class="text-right">${format_currency(row.total_purchase_invoice || 0)}</td>
                        <td class="text-right" style="font-weight:bold; color:${color}">
                            ${format_currency(row.pending_amount)}
                        </td>
                    </tr>
                `;
            });
        }
    
        html += `</tbody></table>`;
        $('#employee_custody').html(html);
    }

    // =========================
    // MEDICAL INSURANCE
    // =========================
    function load_medical_insurance(emp) {
        show_loading('#medical_insurance');

        frappe.call({
            method: 'custom_addons.custom_addons.page.emloyee_custody_dash.employee_custody_dash.get_medical_insurance',
            args: { employee: emp },
            callback: r => {
                if (r.message) {
                    $('#total_insurance').text(r.message.length);
                    render_medical_insurance(r.message);
                }
            }
        });
    }

    function render_medical_insurance(data) {
        let html = `
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Bupa ID</th>
                        <th>Employee ID</th> 
                        <th>Member Name</th>
                        <th>Relationship</th>
                        <th>Main Membership No</th>
                        <th>Main Membership ID</th>
                        <th>CCHI Status</th>
                        <th>Reject Reason</th>
                    </tr>
                </thead>
                <tbody>
        `;

        if (!data.length) {
            html += `<tr><td colspan="8" class="text-center">No Records Found</td></tr>`;
        } else {
            data.forEach(row => {
                const status_color = row.member_cchi_status === 'Approved' ? '#28a745'
                    : row.member_cchi_status === 'Rejected' ? '#d9534f'
                    : '#f0ad4e';

                html += `
                    <tr>
                        <td>
                            <a href="/app/medical-insurance-sheet/${row.bupa_id}" target="_blank">
                                ${row.bupa_id || ''}
                            </a>
                        </td>
                        <td>${row.employee_number || ''}</td> 
                        <td>${row.member_name || ''}</td>
                        <td>${row.relationship || ''}</td>
                        <td>${row.main_membership_no || ''}</td>
                        <td>${row.main_member_id || ''}</td>
                        <td>
                            <span class="badge" style="background:${status_color}">
                                ${row.member_cchi_status || ''}
                            </span>
                        </td>
                        <td>${row.member_reject_reason || '—'}</td>
                    </tr>
                `;
            });
        }

        html += `</tbody></table>`;
        $('#medical_insurance').html(html);
    }

}; 


function render_equipment_tools(data) {

    let html = `
        <table class="table table-bordered">
            <thead>
                <tr>
                    <th>Item Code</th>
                    <th>Item Name</th>
                    <th>Item Group</th>
                    <th>Stock/Asset</th>
                    <th>Project Code</th>
                    <th>Project Name</th>
                    <th>Balance Qty</th>
                </tr>
            </thead>
            <tbody>
    `;

    if (!data.length) {

        html += `
            <tr>
                <td colspan="7" class="text-center">
                    No Records Found
                </td>
            </tr>
        `;

    } else {

        data.forEach(row => {

            html += `
                <tr>

                    <td>${row.item_code || ''}</td>

                    <td>${row.item_name || ''}</td>

                    <td>${row.item_group || ''}</td>

                    <td>${row.stock_asset || ''}</td>

                    <td>${row.project || ''}</td>

                    <td>${row.project_name || ''}</td>

                    <td style="font-weight:bold;">
                        ${row.balance_qty || 0}
                    </td>

                </tr>
            `;
        });
    }

    html += `</tbody></table>`;

    $('#equipment_tools').html(html);
}


function load_employee_details(emp) {
    frappe.db.get_value('Employee', emp, [
        'employee_name',
        'department',
        'designation'
    ]).then(r => {
        if (r.message) {
            $('#emp_name').text(r.message.employee_name || '');
            $('#emp_dept').text(r.message.department || '');
            $('#emp_desig').text(r.message.designation || '');

            $('#employee_info').show();
        }
    });
}

frappe.pages['emloyee-custody-dash'].on_page_show = function(wrapper) {
    const route_options = frappe.route_options;

    if (route_options && route_options.employee) {
        const emp = route_options.employee;

        wrapper.page.fields_dict.employee.set_value(emp);

        load_employee_details(emp);
        load_all(emp);

        frappe.route_options = null; // ✅ VERY IMPORTANT
    }
};