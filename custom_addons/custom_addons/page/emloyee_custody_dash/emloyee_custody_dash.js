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
        </div>

        <div class="custody-tabs">
            <div class="custody-tab active" data-tab="it_assets">IT Asset</div>
            <div class="custody-tab" data-tab="sim_cards">SIM Card</div>
            <div class="custody-tab" data-tab="vehicles">Vehicles</div>
            <div class="custody-tab" data-tab="employee_custody">Employee Advance</div>
        </div>

        <div id="it_assets" class="tab-content"></div>
        <div id="sim_cards" class="tab-content" style="display:none;"></div>
        <div id="vehicles" class="tab-content" style="display:none;"></div>
        <div id="employee_custody" class="tab-content" style="display:none;"></div>
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
            // Updated colspan to 6 to match the new columns
            html += `<tr><td colspan="6" class="text-center">No Records Found</td></tr>`;
        } else {
            data.forEach(row => {
                // Logic: If pending_amount > 0, they owe money (Yellow/Red)
                // If pending_amount < 0, they have spent more than advanced (Green)
                const is_pending = row.pending_amount > 0;
                const color = is_pending ? '#d9534f' : '#28a745'; // Red for debt, Green for credit
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
};

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