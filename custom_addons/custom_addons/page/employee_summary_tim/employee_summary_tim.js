frappe.pages['employee-summary-tim'].on_page_load = function(wrapper) {

    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Employee Summary Timesheet',
        single_column: true
    });

    let from_date = page.add_field({
        label: 'From Date',
        fieldtype: 'Date',
        fieldname: 'from_date',
        default: frappe.datetime.month_start(),
        change: load_data
    });

    let to_date = page.add_field({
        label: 'To Date',
        fieldtype: 'Date',
        fieldname: 'to_date',
        default: frappe.datetime.month_end(),
        change: load_data
    });

    let employee = page.add_field({
        label: 'Employee',
        fieldtype: 'Link',
        options: 'Employee',
        fieldname: 'employee',
        change: load_data
    });

	let branch = page.add_field({
		label: 'Branch',
		fieldtype: 'Link',
		options: 'Branch',
		fieldname: 'branch',
		change: load_data
	});
	
	let employment_type = page.add_field({
		label: 'Employment Type',
		fieldtype: 'Link',
		options: 'Employment Type',
		fieldname: 'employment_type',
		change: load_data
	});

	let employee_category = page.add_field({
        label: 'Employee Category',
        fieldtype: 'Select',
        fieldname: 'employee_category',
        options: [
            '',
            'Company Employee',
            'Non-Company'
        ]
    });


	 // =====================================
    // BUTTONS
    // =====================================

    page.set_primary_action(
        'Refresh Report',
        () => load_data(),
        'refresh'
    );

	page.set_secondary_action(
        'Download Excel',
        () => download_excel()
    );

    // page.add_menu_item(
    //     'Download Excel',
    //     () => download_excel()
    // );

    let body = $(`
        <div style="overflow:auto;">
            <table class="table table-bordered custom-timesheet-table">
            </table>
        </div>
    `);

    $(page.body).append(body);

    load_data();

    function load_data() {

        frappe.call({
            method: "custom_addons.custom_addons.page.employee_summary_tim.employee_summary_tim.get_timesheet_data",

            args: {
                from_date: from_date.get_value(),
                to_date: to_date.get_value(),
                employee: employee.get_value(),
                branch: branch.get_value(),
                employment_type: employment_type.get_value(),
                employee_category: employee_category.get_value()
            },

            callback(r) {

                render_table(r.message);

            }
        });

    }

    function render_table(res) {

		let columns = res.columns;
		let data = res.data;
	
		let table = $(".custom-timesheet-table");
	
		table.empty();
	
		let fixedColumns = columns.slice(0, 12);
		let dynamicColumns = columns.slice(12);
	
		// ===============================
		// TABLE STYLE
		// ===============================
	
		table.css({
			"border-collapse": "collapse",
			"width": "max-content",
			"min-width": "100%",
			"font-size": "12px",
			"table-layout": "fixed",
			"font-family": "Inter, sans-serif",
			"background": "#fff"
		});
	
		// ===============================
		// HEADER
		// ===============================
	
		let thead = `<thead>`;

// ======================================
// GROUP DYNAMIC COLUMNS BY DATE
// ======================================

let groupedDates = {};

dynamicColumns.forEach(col => {

    if (!groupedDates[col.label]) {
        groupedDates[col.label] = {
            day: col.day,
            cols: []
        };
    }

    groupedDates[col.label].cols.push(col);

});

// ======================================
// ROW 1 : DAY
// ======================================

thead += `<tr>`;

// Fixed columns
fixedColumns.forEach((col, idx) => {

    thead += `
        <th rowspan="3"
            style="
                min-width:${idx === 2 ? '220px' : '150px'};
                background:#e2e8f0;
				color:#334155;
                border:1px solid #d1d5db;
                text-align:center;
                vertical-align:middle;
                padding:14px 12px;
				ont-weight:700;
				font-size:13px;
				letter-spacing:0.3px;
                position:sticky;
                top:0;
                z-index:2;
            ">
            ${col.label}
        </th>
    `;
});

// Dynamic grouped
Object.keys(groupedDates).forEach(date => {

    let group = groupedDates[date];

    let isFriday = group.day === "Fri";

    thead += `
        <th colspan="${group.cols.length}"
            style="
                background:${isFriday ? '#fca5a5' : '#bfdbfe'};
				color:${isFriday ? '#7f1d1d' : '#1e3a8a'};
                border:1px solid #d1d5db;
                text-align:center;
                padding:10px;
                font-weight:700;
                position:sticky;
                top:0;
                z-index:1;
            ">
            ${group.day}
        </th>
    `;
});

thead += `</tr>`;

// ======================================
// ROW 2 : DATE
// ======================================

thead += `<tr>`;

Object.keys(groupedDates).forEach(date => {

    let group = groupedDates[date];

    let isFriday = group.day === "Fri";

    thead += `
        <th colspan="${group.cols.length}"
            style="
                background:${isFriday ? '#fee2e2' : '#eff6ff'};
                color:${isFriday ? '#b91c1c' : '#334155'};
                border:1px solid #d1d5db;
                text-align:center;
                padding:8px;
                font-weight:700;
                position:sticky;
                top:42px;
                z-index:1;
            ">
            ${date}
        </th>
    `;
});

thead += `</tr>`;

// ======================================
// ROW 3 : NH / OT
// ======================================

thead += `<tr>`;

dynamicColumns.forEach(col => {

    let isOT = col.type === "OT";

    thead += `
        <th
            style="
                background:${isOT ? '#fef3c7' : '#ecfdf5'};
                color:${isOT ? '#92400e' : '#065f46'};
                border:1px solid #d1d5db;
                text-align:center;
                padding:8px 4px;
                min-width:70px;
                font-weight:700;
                position:sticky;
                top:82px;
                z-index:1;
            ">
            ${col.type}
        </th>
    `;
});

	
		thead += `</tr>`;
	
		thead += `</thead>`;
	
		table.append(thead);
	
		// ===============================
		// BODY
		// ===============================
	
		let tbody = `<tbody>`;
	
		data.forEach((row, rowIndex) => {
	
			tbody += `
				<tr style="
					background:${rowIndex % 2 === 0 ? '#ffffff' : '#f9fafb'};
					transition:0.2s;
				"
				onmouseover="this.style.background='#eef2ff'"
				onmouseout="this.style.background='${rowIndex % 2 === 0 ? '#ffffff' : '#f9fafb'}'"
				>
			`;
	
			columns.forEach((col, index) => {
	
				let value = row[col.fieldname];
	
				if (
					value === undefined ||
					value === null ||
					value === ""
				) {
					value = "";
				}
	
				let isDynamic = index >= 12;
	
				let isOT = col.type === "OT";
	
				tbody += `
					<td
						style="
							border:1px solid #e5e7eb;
							padding:8px 6px;
							text-align:center;
							white-space:nowrap;
							min-width:${isDynamic ? '70px' : '150px'};
							background:${isOT ? '#fffaf0' : 'white'};
							color:${isOT ? '#92400e' : '#111827'};
							font-weight:${isOT ? '600' : '400'};
						"
					>
						${value}
					</td>
				`;
			});
	
			tbody += `</tr>`;
		});
	
		tbody += `</tbody>`;
	
		table.append(tbody);
	
		// ===============================
		// WRAPPER STYLE
		// ===============================
	
		$(".custom-timesheet-table").wrap(`
			<div style="
				overflow:auto;
				max-height:75vh;
				
				
				box-shadow:0 4px 12px rgba(0,0,0,0.06);
				background:white;
			"></div>
		`);
	
	}

	 // =====================================
    // DOWNLOAD EXCEL
    // =====================================

    function download_excel() {

        let table = document.querySelector(
            ".custom-timesheet-table"
        );

        let wb = XLSX.utils.table_to_book(table);

        XLSX.writeFile(
            wb,
            "Employee Summary Timesheet.xlsx"
        );
    }
};