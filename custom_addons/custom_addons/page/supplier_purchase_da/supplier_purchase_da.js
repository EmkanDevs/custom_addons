// frappe.pages['supplier-purchase-da'].on_page_load = function (wrapper) {
//     new SupplierPurchaseDashboard(wrapper);
// };

// class SupplierPurchaseDashboard {

//     constructor(wrapper) {
//         this.wrapper = wrapper;
//         this.page = frappe.ui.make_app_page({
//             parent: wrapper,
//             title: "Supplier Purchase Dashboard",
//             single_column: true
//         });

//         this.render();
//         this.create_filters();
//         this.bind_events();
//         this.show_empty_state();
//     }

//     render() {
//         $(this.page.body).html(`
//             <style>
//                 /* Vertical x-axis labels so every PO ID fits */
//                 #chart-supplier svg .x-axis text,
//                 #chart-project svg .x-axis text {
//                     transform: rotate(-90deg);
//                     transform-origin: center top;
//                     text-anchor: end;
//                     font-size: 9px;
//                 }
//                 .chart-scroll-wrapper,
//                 .table-scroll-wrapper {
//                     overflow-x: auto;
//                     -webkit-overflow-scrolling: touch;
//                     border: 1px solid #ebebeb;
//                     border-radius: 4px;
//                     padding-bottom: 8px;
//                 }
//                 .chart-container {
//                     flex-shrink: 0;
//                     display: inline-block;
//                 }
//                 /* Force DataTable cells to not wrap so horizontal scroll appears */
//                 .table-scroll-wrapper .data-table .content {
//                     white-space: nowrap !important;
//                 }
//                 .table-scroll-wrapper .data-table {
//                     min-width: 1100px;
//                 }
//             </style>

//             <div class="container-fluid">

//                 <!-- Filters -->
//                 <div class="card mb-4">
//                     <div class="card-body">
//                         <h4 class="mb-3">Filters</h4>
//                         <div class="row" id="filter-area"></div>
//                     </div>
//                 </div>

//                 <!-- KPI Cards -->
//                 <div class="row mb-4">
//                     <div class="col-md-3">
//                         <div class="kpi-card">
//                             <div class="kpi-title">Total PO Value</div>
//                             <div class="kpi-value" id="total-po">SAR 0.00</div>
//                         </div>
//                     </div>
//                     <div class="col-md-3">
//                         <div class="kpi-card">
//                             <div class="kpi-title">PO Count</div>
//                             <div class="kpi-value" id="po-count">0</div>
//                         </div>
//                     </div>
//                     <div class="col-md-3">
//                         <div class="kpi-card">
//                             <div class="kpi-title">New Suppliers</div>
//                             <div class="kpi-value" id="supplier-count">0</div>
//                         </div>
//                     </div>
//                     <div class="col-md-3">
//                         <div class="kpi-card">
//                             <div class="kpi-title">Average PO</div>
//                             <div class="kpi-value" id="avg-po">SAR 0.00</div>
//                         </div>
//                     </div>
//                 </div>

//                 <!-- Supplier Chart -->
//                 <div class="card mb-4">
//                     <div class="card-body">
//                         <h4 class="mb-3">Purchase Analysis by Supplier</h4>
//                         <div class="chart-scroll-wrapper">
//                             <div id="chart-supplier" class="chart-container" style="height: 450px;"></div>
//                         </div>
//                         <div id="legend-supplier" class="mt-3"></div>
//                     </div>
//                 </div>

//                 <!-- Project Chart -->
//                 <div class="card mb-4">
//                     <div class="card-body">
//                         <h4 class="mb-3">Purchase Analysis by Project</h4>
//                         <div class="chart-scroll-wrapper">
//                             <div id="chart-project" class="chart-container" style="height: 450px;"></div>
//                         </div>
//                         <div id="legend-project" class="mt-3"></div>
//                     </div>
//                 </div>

//                 <!-- Bottom Tables -->
//                 <div class="row">
//                     <div class="col-md-4">
//                         <div class="card">
//                             <div class="card-body">
//                                 <h4>Team Summary</h4>
//                                 <div id="summary-table"></div>
//                             </div>
//                         </div>
//                     </div>
//                     <div class="col-md-8">
//                         <div class="card">
//                             <div class="card-body">
//                                 <h4>Purchase Orders</h4>
//                                 <div class="table-scroll-wrapper">
//                                     <div id="detail-table"></div>
//                                 </div>
//                             </div>
//                         </div>
//                     </div>
//                 </div>

//             </div>
//         `);
//     }

//     create_filters() {
//         this.filters = {};
//         const now = new Date();
//         const currentYear = now.getFullYear();
//         const currentMonth = now.getMonth() + 1;

//         const fields = [
//             {
//                 fieldname: "company",
//                 label: "Company",
//                 fieldtype: "Link",
//                 options: "Company",
//                 default: frappe.defaults.get_user_default("Company")
//             },
//             {
//                 fieldname: "year",
//                 label: "Year",
//                 fieldtype: "Select",
//                 options: `\n${currentYear - 1}\n${currentYear}\n${currentYear + 1}`,
//                 default: String(currentYear),
//                 reqd: 1
//             },
//             {
//                 fieldname: "month",
//                 label: "Month",
//                 fieldtype: "Select",
//                 options: "\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12",
//                 default: String(currentMonth),
//                 reqd: 1
//             },
//             {
//                 fieldname: "from_date",
//                 label: "From Date",
//                 fieldtype: "Date",
//                 default: frappe.datetime.month_start()
//             },
//             {
//                 fieldname: "to_date",
//                 label: "To Date",
//                 fieldtype: "Date",
//                 default: frappe.datetime.month_end()
//             },
//             {
//                 fieldname: "supplier",
//                 label: "Supplier",
//                 fieldtype: "Link",
//                 options: "Supplier"
//             },
//             {
//                 fieldname: "project",
//                 label: "Project",
//                 fieldtype: "Link",
//                 options: "Project"
//             },
//             {
//                 fieldname: "owner",
//                 label: "Created By",
//                 fieldtype: "Link",
//                 options: "User"
//             }
//         ];

//         fields.forEach(df => {
//             const col = $('<div class="col-md-2 mb-3"></div>')
//                 .appendTo($(this.page.body).find("#filter-area"));

//             this.filters[df.fieldname] = frappe.ui.form.make_control({
//                 parent: col,
//                 df: df,
//                 render_input: true
//             });

//             // Explicitly set default value — make_control does not auto-apply it
//             if (df.default) {
//                 this.filters[df.fieldname].set_value(df.default);
//             }
//         });
//     }

//     bind_events() {
//         this.page.set_primary_action("Refresh", () => {
//             if (!this.validate_filters()) return;
//             this.load_dashboard();
//         });
//     }

//     validate_filters() {
//         const mandatory = ['year', 'month'];
//         let missing = [];

//         mandatory.forEach(key => {
//             if (!this.filters[key].get_value()) {
//                 missing.push(this.filters[key].df.label);
//             }
//         });

//         if (missing.length) {
//             frappe.show_alert({
//                 message: __("Please fill mandatory filters: {0}", [missing.join(", ")]),
//                 indicator: "red"
//             });
//             return false;
//         }
//         return true;
//     }

//     show_empty_state() {
//         const msg = '<p class="text-muted text-center" style="padding-top:180px;">Select Year & Month, then click Refresh to load data</p>';
//         $(this.page.body).find("#chart-supplier").html(msg);
//         $(this.page.body).find("#chart-project").html(msg);
//         $(this.page.body).find("#summary-table").html('<p class="text-muted text-center">No data available</p>');
//         $(this.page.body).find("#detail-table").html('<p class="text-muted text-center">No data available</p>');
//     }

//     get_filters() {
//         let filters = {};
//         Object.keys(this.filters).forEach(key => {
//             filters[key] = this.filters[key].get_value();
//         });
//         return filters;
//     }

//     load_dashboard() {
//         frappe.call({
//             method: "custom_addons.custom_addons.page.supplier_purchase_da.supplier_purchase_da.get_dashboard_data",
//             args: {
//                 filters: this.get_filters()
//             },
//             callback: (r) => {
//                 if (!r.message) return;

//                 // ── KPIs ──
//                 $("#total-po").html(
//                     format_currency(
//                         r.message.kpis.total_po || 0,
//                         frappe.defaults.get_default("currency")
//                     )
//                 );
//                 $("#po-count").html(r.message.kpis.po_count || 0);
//                 $("#supplier-count").html(r.message.kpis.new_suppliers || 0);
//                 $("#avg-po").html(
//                     format_currency(
//                         r.message.kpis.average_po || 0,
//                         frappe.defaults.get_default("currency")
//                     )
//                 );

//                 // ── Charts ──
//                 this.render_bar_chart({
//                     chart_id: "chart-supplier",
//                     legend_id: "legend-supplier",
//                     chart_data: r.message.supplier_chart,
//                     color_key: "supplier",
//                     color_array_key: "suppliers"
//                 });

//                 this.render_bar_chart({
//                     chart_id: "chart-project",
//                     legend_id: "legend-project",
//                     chart_data: r.message.project_chart,
//                     color_key: "project",
//                     color_array_key: "projects"
//                 });

//                 // ── Tables ──
//                 this.render_team_summary(r.message.team_summary);
//                 this.render_detail_table(r.message.purchase_orders);
//             }
//         });
//     }

//     render_bar_chart({ chart_id, legend_id, chart_data, color_key, color_array_key }) {
//         const $chart = $(this.page.body).find("#" + chart_id);
//         const $legend = $(this.page.body).find("#" + legend_id);

//         $chart.empty();
//         $legend.empty();

//         if (!chart_data || !chart_data.labels || !chart_data.labels.length) {
//             $chart.html('<p class="text-muted text-center" style="padding-top:180px;">No data available</p>');
//             $chart.css("width", "100%");
//             return;
//         }

//         const barWidth = 55;
//         const calculatedWidth = Math.max(chart_data.labels.length * barWidth, 800);
//         const chartEl = document.getElementById(chart_id);
//         chartEl.style.width = calculatedWidth + "px";
//         chartEl.style.height = "450px";
//         chartEl.style.flexShrink = "0";
//         chartEl.style.display = "inline-block";
//         void chartEl.offsetWidth;

//         const meta = {};
//         chart_data.labels.forEach((label, i) => {
//             meta[label] = {
//                 created_by: chart_data.creators ? chart_data.creators[i] : '',
//                 color_value: chart_data[color_array_key] ? chart_data[color_array_key][i] : ''
//             };
//         });

//         const colorMap = chart_data[color_key + "_colors"] || {};

//         new frappe.Chart("#" + chart_id, {
//             data: {
//                 labels: chart_data.labels,
//                 datasets: [{ name: "PO Value", values: chart_data.values }]
//             },
//             type: 'bar',
//             height: 450,
//             colors: ['#cccccc'],
//             axisOptions: {
//                 xAxisMode: 'tick',
//                 xIsSeries: true
//             },
//             barOptions: {
//                 spaceRatio: 0.25
//             },
//             valuesOverPoints: true,
//             tooltipOptions: {
//                 formatTooltipX: (d) => {
//                     const m = meta[d] || {};
//                     return `${d}  |  ${m.created_by || 'Unknown'}  |  ${m.color_value || ''}`;
//                 },
//                 formatTooltipY: (d) => format_currency(d, frappe.defaults.get_default("currency"))
//             }
//         });

//         const paintBars = (attempt = 1) => {
//             const svg = chartEl.querySelector('svg');
//             if (!svg) {
//                 if (attempt < 20) setTimeout(() => paintBars(attempt + 1), 250);
//                 return;
//             }

//             const bars = svg.querySelectorAll('rect.bar');
//             if (!bars.length && attempt < 20) {
//                 setTimeout(() => paintBars(attempt + 1), 250);
//                 return;
//             }

//             let painted = 0;
//             bars.forEach((bar, i) => {
//                 const key = chart_data[color_array_key][i];
//                 if (key && colorMap[key]) {
//                     bar.style.fill = colorMap[key];
//                     bar.style.stroke = colorMap[key];
//                     bar.setAttribute('fill', colorMap[key]);
//                     painted++;
//                 }
//             });

//             if (painted < chart_data.labels.length && attempt < 20) {
//                 setTimeout(() => paintBars(attempt + 1), 300);
//             }
//         };

//         [200, 500, 800, 1200].forEach(d => setTimeout(paintBars, d));
//         this.render_legend(legend_id, colorMap);
//     }

//     render_legend(legend_id, color_map) {
//         const $legend = $(this.page.body).find("#" + legend_id);
//         const keys = Object.keys(color_map);
//         if (!keys.length) return;

//         let html = '<div class="d-flex flex-wrap justify-content-center" style="gap: 14px;">';
//         keys.forEach(key => {
//             html += `
//                 <div class="d-flex align-items-center" style="font-size: 12px; color: #555;">
//                     <span style="display:inline-block;width:12px;height:12px;background:${color_map[key]};border-radius:2px;margin-right:6px;flex-shrink:0;"></span>
//                     <span>${key}</span>
//                 </div>
//             `;
//         });
//         html += '</div>';
//         $legend.html(html);
//     }

//     render_team_summary(data) {
//         const $table = $(this.page.body).find("#summary-table");
//         $table.empty();

//         if (!data || !data.length) {
//             $table.html('<p class="text-muted text-center">No data available</p>');
//             return;
//         }

//         this.summary_table = new frappe.DataTable($table[0], {
//             columns: [
//                 { name: "Team Member", id: "team_member", width: 180 },
//                 { name: "POs Issued", id: "po_count", width: 120, align: "right" }
//             ],
//             data: data,
//             layout: "fluid",
//             noDataMessage: "No data available"
//         });
//     }

//     render_detail_table(data) {
//         const $table = $(this.page.body).find("#detail-table");
//         $table.empty();

//         if (!data || !data.length) {
//             $table.html('<p class="text-muted text-center">No data available</p>');
//             return;
//         }

//         this.detail_table = new frappe.DataTable($table[0], {
//             columns: [
//                 {
//                     name: "PO Number",
//                     id: "po_number",
//                     width: 150,
//                     format: (value) => `<a href="/app/purchase-order/${value}" target="_blank">${value}</a>`
//                 },
//                 { name: "Date", id: "date", width: 120 },
//                 { name: "Supplier", id: "supplier_name", width: 260 },
//                 { name: "Project", id: "project_name", width: 220 },
//                 { name: "Created By", id: "created_by", width: 180 },
//                 {
//                     name: "Total",
//                     id: "grand_total",
//                     width: 150,
//                     align: "right",
//                     format: (value) => format_currency(value, frappe.defaults.get_default("currency"))
//                 }
//             ],
//             data: data,
//             layout: "fluid",
//             noDataMessage: "No data available"
//         });
//     }
// }

/////////////////////////////////////////////////////////////////////////////////////////////////////

frappe.pages['supplier-purchase-da'].on_page_load = function (wrapper) {
    new SupplierPurchaseDashboard(wrapper);
};

class SupplierPurchaseDashboard {

    constructor(wrapper) {
        this.wrapper = wrapper;
        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: "Supplier Purchase Dashboard",
            single_column: true
        });

        this.charts = {};
        this.detail_rows = [];
        this.currentPage = 0;
        this.pageLength = 50;
        this.totalRecords = 0;

        this.load_dependencies(() => {
            this.render();
            this.create_filters();
            this.bind_events();
            this.show_empty_state();
        });
    }

    load_dependencies(done) {
        if (!document.getElementById("spd-fontawesome")) {
            const fa = document.createElement("link");
            fa.id = "spd-fontawesome";
            fa.rel = "stylesheet";
            fa.href = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css";
            document.head.appendChild(fa);
        }

        if (!document.getElementById("spd-inter-font")) {
            const font = document.createElement("link");
            font.id = "spd-inter-font";
            font.rel = "stylesheet";
            font.href = "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap";
            document.head.appendChild(font);
        }

        if (window.Chart) {
            done();
            return;
        }

        if (document.getElementById("spd-chartjs")) {
            const wait = setInterval(() => {
                if (window.Chart) {
                    clearInterval(wait);
                    done();
                }
            }, 50);
            return;
        }

        const script = document.createElement("script");
        script.id = "spd-chartjs";
        script.src = "https://cdn.jsdelivr.net/npm/chart.js";
        script.onload = done;
        document.head.appendChild(script);
    }

    render() {
        $(this.page.body).html(`
            <style>
                .spd-dashboard {
                    --coral-flame: #d94e34;
                    --coral-soft: #f7d6c8;
                    --navy-primary: #0b4c80;
                    --navy-soft: #cce0f0;
                    --bg-body: #f8fafc;
                    --card-bg: #ffffff;
                    --text-main: #0f172a;
                    --text-muted: #64748b;
                    --border-color: #e2e8f0;
                    --shadow-sm: 0 1px 3px rgba(0,0,0,0.04);
                    --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.06), 0 2px 4px -1px rgba(0,0,0,0.03);
                    --radius-sm: 6px;
                    --radius-md: 10px;
                    --radius-lg: 14px;
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                    color: var(--text-main);
                    font-size: 13.5px;
                    line-height: 1.5;
                }

                .spd-dashboard * { box-sizing: border-box; }

                .spd-card {
                    background: var(--card-bg);
                    border: 1px solid var(--border-color);
                    border-radius: var(--radius-md);
                    box-shadow: var(--shadow-sm);
                    margin-bottom: 16px;
                    overflow: hidden;
                }

                .spd-card-header {
                    padding: 8px 14px;
                    border-bottom: 1px solid var(--border-color);
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    background: #ffffff;
                    flex-wrap: wrap;
                    gap: 8px;
                }

                .spd-card-header h2 {
                    font-size: 14px;
                    font-weight: 600;
                    color: var(--text-main);
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    margin: 0;
                }

                .spd-card-body { padding: 14px 16px; }
                .spd-p-0 { padding: 0 !important; }

                .spd-badge-coral { background: #fdf2f0; color: var(--coral-flame); padding: 4px 8px; border-radius: 5px; }
                .spd-badge-navy { background: #edf4fa; color: var(--navy-primary); padding: 4px 8px; border-radius: 5px; }

                .spd-btn {
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    padding: 7px 14px;
                    font-size: 12.5px;
                    font-weight: 500;
                    border-radius: var(--radius-sm);
                    border: 1px solid transparent;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .spd-btn-primary { background: var(--navy-primary); color: white; }
                .spd-btn-primary:hover { background: #083c66; }
                .spd-btn-outline { background: white; border-color: var(--border-color); color: var(--text-main); }
                .spd-btn-outline:hover { background: #f8fafc; }
                .spd-download-chart { padding: 4px 8px !important; font-size: 11px; }

                .spd-filters-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
                    gap: 12px;
                    align-items: end;
                }
                .spd-filter-group { 
                    display: flex; 
                    flex-direction: column; 
                    gap: 0px; 
                    margin: 0 !important; 
                    padding: 0 !important; 
                }
                /* Force ALL labels to identical height and alignment - match Petty Cash */
                .spd-filter-group label,
                .spd-filter-group .control-label,
                #filter-area label,
                #filter-area .control-label {
                    font-size: 12px !important; 
                    font-weight: 500 !important; 
                    color: #4b5563 !important; 
                    margin: 0 0 4px 0 !important; 
                    padding: 0 !important;
                    line-height: 16px !important;
                    height: 16px !important;
                    display: block !important;
                    overflow: hidden !important;
                    white-space: nowrap !important;
                    text-overflow: ellipsis !important;
                }
                /* Hide reqd asterisk to prevent misalignment */
                .spd-filter-group .reqd,
                #filter-area .reqd,
                .spd-filter-group .control-label .reqd {
                    display: none !important;
                }
                /* Remove ALL margins from Frappe wrappers */
                .spd-filter-group .form-group,
                #filter-area .form-group { 
                    margin: 0 !important; 
                    padding: 0 !important;
                }
                .spd-filter-group .frappe-control,
                #filter-area .frappe-control { 
                    margin: 0 !important; 
                    padding: 0 !important;
                }
                .spd-filter-group .control-input,
                #filter-area .control-input { 
                    margin: 0 !important; 
                    padding: 0 !important;
                }
                .spd-filter-group .control-value,
                #filter-area .control-value { 
                    margin: 0 !important; 
                    padding: 0 !important;
                }
                .spd-filter-group .clearfix,
                #filter-area .clearfix { 
                    margin: 0 !important; 
                    padding: 0 !important;
                    display: none !important;
                }
                /* Input styling */
                .spd-filter-group input, 
                .spd-filter-group select, 
                .spd-filter-group .form-control,
                .spd-filter-group .like-disabled-input,
                #filter-area input, 
                #filter-area select, 
                #filter-area .form-control,
                #filter-area .like-disabled-input { 
                    padding: 6px 10px !important; 
                    height: 36px !important; 
                    min-height: 36px !important;
                    font-size: 13px !important;
                    border-radius: 6px !important;
                    border: 1px solid #d1d5db !important;
                    background: #ffffff !important;
                    color: #1f2937 !important;
                    margin: 0 !important;
                    box-sizing: border-box !important;
                }
                .spd-filter-group input:focus, 
                .spd-filter-group select:focus { 
                    border-color: #0b4c80 !important; 
                    outline: none !important;
                    box-shadow: 0 0 0 2px rgba(11,76,128,0.08) !important;
                }
                .spd-filter-group .select-icon { 
                    right: 10px !important; 
                    top: 50% !important; 
                    transform: translateY(-50%) !important;
                    color: #6b7280 !important;
                }
                /* Z-index fix for dropdowns - prevent chart overlap */
                .spd-filter-group .awesomplete,
                #filter-area .awesomplete {
                    position: relative !important;
                    z-index: 100 !important;
                }
                .spd-filter-group .awesomplete > ul,
                #filter-area .awesomplete > ul { 
                    margin-top: 2px !important; 
                    z-index: 99999 !important;
                    position: absolute !important; 
                    width: 100% !important;
                    background: white !important;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
                }
                .spd-filter-group .link-field,
                #filter-area .link-field {
                    position: relative !important;
                    z-index: 100 !important;
                }
                .spd-filter-group .link-field .btn-open { 
                    padding: 3px 6px !important; 
                    height: 30px !important; 
                    top: 3px !important;
                    right: 3px !important;
                }
                .spd-card-body { padding: 14px 16px !important; }
                #filter-area .help-box { display: none !important; }
                #filter-area .like-disabled-input { padding: 6px 10px !important; min-height: 36px !important; }
                /* Fix dropdown overlap issues */
                #spd-filters-card {
                    position: relative;
                    z-index: 1000 !important;
                    overflow: visible !important;
                }
                #spd-filters-card .spd-card-body {
                    overflow: visible !important;
                }
                #filter-area {
                    position: relative;
                    z-index: 1000 !important;
                }
                .spd-filter-group .awesomplete,
                #filter-area .awesomplete {
                    position: relative !important;
                    z-index: 10000 !important;
                }
                .spd-filter-group .awesomplete > ul,
                #filter-area .awesomplete > ul {
                    z-index: 100000 !important;
                    position: absolute !important;
                    top: 100% !important;
                    left: 0 !important;
                    right: 0 !important;
                    margin-top: 2px !important;
                    background: white !important;
                    box-shadow: 0 8px 24px rgba(0,0,0,0.15) !important;
                    border: 1px solid #e2e8f0 !important;
                    border-radius: 6px !important;
                    max-height: 250px !important;
                    overflow-y: auto !important;
                }
                .spd-filter-group .link-field,
                #filter-area .link-field {
                    position: relative !important;
                    z-index: 10000 !important;
                }
                .spd-filter-group .link-field .awesomplete > ul,
                #filter-area .link-field .awesomplete > ul {
                    z-index: 100000 !important;
                }
                .spd-kpi-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 14px;
                    margin-bottom: 16px;
                }
                .spd-kpi-card {
                    background: white;
                    border: 1px solid var(--border-color);
                    border-radius: var(--radius-md);
                    padding: 14px 16px;
                    position: relative;
                    overflow: hidden;
                    box-shadow: var(--shadow-sm);
                    transition: transform 0.2s, box-shadow 0.2s;
                }
                .spd-kpi-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
                .spd-kpi-card::before {
                    content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%;
                }
                .spd-kpi-coral::before { background: var(--coral-flame); }
                .spd-kpi-navy::before { background: var(--navy-primary); }
                .spd-kpi-slate::before { background: #475569; }
                .spd-kpi-label {
                    font-size: 11px; font-weight: 600; text-transform: uppercase;
                    letter-spacing: 0.5px; color: var(--text-muted); margin-bottom: 6px;
                    display: flex; align-items: center; justify-content: space-between;
                }
                .spd-kpi-value {
                    font-size: 22px; font-weight: 700; color: var(--text-main);
                    letter-spacing: -0.5px; margin-bottom: 2px;
                }
                .spd-kpi-subtext { font-size: 11px; color: var(--text-muted); }

                .spd-dashboard-grid {
                    display: grid;
                    grid-template-columns: repeat(12, 1fr);
                    gap: 16px;
                    margin-bottom: 16px;
                }
                .spd-col-4 { grid-column: span 4; }
                .spd-col-6 { grid-column: span 6; }
                .spd-col-8 { grid-column: span 8; }
                .spd-col-12 { grid-column: span 12; }
                @media (max-width: 1200px) {
                    .spd-col-4, .spd-col-6, .spd-col-8 { grid-column: span 12; }
                }

                .spd-chart-container { position: relative; height: 220px; width: 100%; }

                .spd-tab-switcher {
                    display: flex; background: #f1f5f9; padding: 2px;
                    border-radius: var(--radius-sm); gap: 2px;
                }
                .spd-tab-btn {
                    padding: 4px 10px; font-size: 11.5px; font-weight: 600;
                    border-radius: 4px; border: none; background: transparent;
                    cursor: pointer; color: var(--text-muted); transition: all 0.2s;
                }
                .spd-tab-btn.active { background: white; color: var(--navy-primary); box-shadow: var(--shadow-sm); }

                .spd-custom-table-wrapper { overflow-x: auto; }
                table.spd-custom-table {
                    width: 100%; border-collapse: collapse; font-size: 12.5px; text-align: left;
                }
                table.spd-custom-table th {
                    background: #f8fafc; color: var(--text-muted); font-weight: 600;
                    font-size: 11.5px; padding: 9px 12px; border-bottom: 2px solid var(--border-color);
                    text-transform: uppercase; letter-spacing: 0.3px; white-space: nowrap;
                }
                table.spd-custom-table td {
                    padding: 9px 12px; border-bottom: 1px solid var(--border-color); color: var(--text-main);
                }
                table.spd-custom-table tr:hover { background: #f1f5f9; }
                table.spd-custom-table tr.spd-total-row {
                    font-weight: 700; background: #f8fafc; border-top: 2px solid var(--border-color);
                }
                .spd-text-right { text-align: right; }
                .spd-text-center { text-align: center; }
                .spd-text-muted { color: var(--text-muted); }

                .spd-status-pill {
                    display: inline-flex; align-items: center; gap: 4px;
                    padding: 2px 7px; border-radius: 10px; font-size: 10.5px; font-weight: 600;
                }
                .spd-pill-approved { background: #dcfce7; color: #15803d; }
                .spd-pill-draft { background: #f1f5f9; color: #475569; }
                .spd-pill-pending { background: #fef3c7; color: #d97706; }
                .spd-pill-cancelled { background: #f1f5f9; color: #94a3b8; }

                .spd-search-box { position: relative; width: 240px; max-width: 100%; }
                .spd-search-box input {
                    width: 100%; padding: 7px 12px 7px 34px;
                    border: 1px solid var(--border-color); border-radius: var(--radius-sm);
                    background: #f1f5f9; font-size: 12.5px;
                }
                .spd-search-box i {
                    position: absolute; left: 11px; top: 50%; transform: translateY(-50%);
                    color: var(--text-muted);
                }

                .spd-empty { color: var(--text-muted); text-align: center; padding: 60px 0; }

                /* Pagination Styles */
                .spd-pagination {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    padding: 12px 16px;
                    border-top: 1px solid var(--border-color);
                    flex-wrap: wrap;
                }
                .spd-pagination button {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    padding: 6px 10px;
                    font-size: 12px;
                    font-weight: 500;
                    border: 1px solid #d1d5db;
                    border-radius: 6px;
                    background: white;
                    color: #374151;
                    cursor: pointer;
                    transition: all 0.2s;
                    min-width: 32px;
                    height: 32px;
                }
                .spd-pagination button:hover:not(:disabled) {
                    background: #f3f4f6;
                    border-color: #9ca3af;
                }
                .spd-pagination button:disabled {
                    opacity: 0.4;
                    cursor: not-allowed;
                }
                .spd-pagination input[type="number"] {
                    width: 50px;
                    padding: 5px 8px;
                    font-size: 12px;
                    border: 1px solid #d1d5db;
                    border-radius: 6px;
                    text-align: center;
                    height: 32px;
                }
                .spd-pagination select {
                    padding: 5px 8px;
                    font-size: 12px;
                    border: 1px solid #d1d5db;
                    border-radius: 6px;
                    background: white;
                    height: 32px;
                    cursor: pointer;
                }
                .spd-pagination span {
                    font-size: 12px;
                    color: #6b7280;
                }
            </style>

            <div class="spd-dashboard">

                <!-- Filters -->
                <div class="spd-card" id="spd-filters-card">
                    <div class="spd-card-header" style="padding: 10px 16px;">
                        <h2 style="font-size: 13px;"><span class="spd-badge-navy"><i class="fa-solid fa-sliders"></i></span> Dashboard Filters</h2>
                        <button class="spd-btn spd-btn-outline" id="spd-reset-filters" style="font-size: 12px; padding: 5px 12px;">
                            <i class="fa-solid fa-rotate-left"></i> Reset
                        </button>
                    </div>
                    <div class="spd-card-body" style="padding: 12px 16px !important;">
                        <div class="spd-filters-grid" id="filter-area"></div>
                    </div>
                </div>

                <!-- KPI Cards -->
                <div class="spd-kpi-grid">
                    <div class="spd-kpi-card spd-kpi-coral">
                        <div class="spd-kpi-label"><span>Total PO Value</span><i class="fa-solid fa-receipt"></i></div>
                        <div class="spd-kpi-value" id="total-po">SAR 0.00</div>
                    </div>
                    <div class="spd-kpi-card spd-kpi-navy">
                        <div class="spd-kpi-label"><span>PO Count</span><i class="fa-solid fa-file-contract"></i></div>
                        <div class="spd-kpi-value" id="po-count">0</div>
                    </div>
                    <div class="spd-kpi-card spd-kpi-coral">
                        <div class="spd-kpi-label"><span>New Suppliers</span><i class="fa-solid fa-truck-field"></i></div>
                        <div class="spd-kpi-value" id="supplier-count">0</div>
                    </div>
                    <div class="spd-kpi-card spd-kpi-navy">
                        <div class="spd-kpi-label"><span>Average PO</span><i class="fa-solid fa-calculator"></i></div>
                        <div class="spd-kpi-value" id="avg-po">SAR 0.00</div>
                    </div>
                    <div class="spd-kpi-card spd-kpi-slate">
                        <div class="spd-kpi-label"><span>Pending Approval POs</span><i class="fa-solid fa-clock"></i></div>
                        <div class="spd-kpi-value" id="pending-po-count">0 Orders</div>
                        <div class="spd-kpi-subtext" id="pending-po-value">SAR 0.00 awaiting approval</div>
                    </div>
                </div>

                <!-- Supplier + Project charts -->
                <div class="spd-dashboard-grid">
                    <div class="spd-card spd-col-6" style="margin-bottom:0;">
                        <div class="spd-card-header">
                            <h2><i class="fa-solid fa-chart-column" style="color:#d94e34;"></i> Purchase Analysis by Supplier</h2>
                            <div style="display:flex;align-items:center;gap:8px;">
                                <button class="spd-btn spd-btn-outline spd-download-chart" data-chart="supplierChart" data-title="Purchase Analysis by Supplier" title="Download Chart">
                                    <i class="fa-solid fa-download"></i>
                                </button>
                                <div class="spd-tab-switcher" data-card="supplier">
                                <button class="spd-tab-btn active" data-view="chart">
                                    <i class="fa-solid fa-chart-simple"></i> Chart
                                </button>
                                <button class="spd-tab-btn" data-view="table">
                                    <i class="fa-solid fa-table"></i> Table
                                </button>
                            </div>
                            </div>
                        </div>
                        <div class="spd-card-body">
                            <div id="supplier-chart-view" class="spd-chart-container">
                                <canvas id="supplierChart"></canvas>
                            </div>
                            <div id="supplier-table-view" class="spd-custom-table-wrapper" style="display:none;">
                                <table class="spd-custom-table">
                                    <thead>
                                        <tr>
                                            <th>Supplier Name</th>
                                            <th>Supplier Code</th>
                                            <th class="spd-text-right">Total PO Value</th>
                                        </tr>
                                    </thead>
                                    <tbody id="supplier-table-body"></tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    <div class="spd-card spd-col-6" style="margin-bottom:0;">
                        <div class="spd-card-header">
                            <h2><i class="fa-solid fa-building" style="color:#0b4c80;"></i> Purchase Analysis by Project</h2>
                            <div style="display:flex;align-items:center;gap:8px;">
                                <button class="spd-btn spd-btn-outline spd-download-chart" data-chart="projectChart" data-title="Purchase Analysis by Project" title="Download Chart">
                                    <i class="fa-solid fa-download"></i>
                                </button>
                                <div class="spd-tab-switcher" data-card="project">
                                <button class="spd-tab-btn active" data-view="chart">
                                    <i class="fa-solid fa-chart-simple"></i> Chart
                                </button>
                                <button class="spd-tab-btn" data-view="table">
                                    <i class="fa-solid fa-table"></i> Table
                                </button>
                            </div>
                            </div>
                        </div>
                        <div class="spd-card-body">
                            <div id="project-chart-view" class="spd-chart-container">
                                <canvas id="projectChart"></canvas>
                            </div>
                            <div id="project-table-view" class="spd-custom-table-wrapper" style="display:none;">
                                <table class="spd-custom-table">
                                    <thead>
                                        <tr>
                                            <th>Project</th>
                                            <th class="spd-text-right">Total PO Value</th>
                                        </tr>
                                    </thead>
                                    <tbody id="project-table-body"></tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Team Summary + Approval pipeline -->
                <div class="spd-dashboard-grid">
                    <div class="spd-card spd-col-4" style="margin-bottom:0;">
                        <div class="spd-card-header">
                            <h2><i class="fa-solid fa-users-gear spd-badge-coral"></i> Team Summary</h2>
                        </div>
                        <div class="spd-card-body spd-p-0">
                            <div class="spd-custom-table-wrapper">
                                <table class="spd-custom-table">
                                    <thead>
                                        <tr>
                                            <th class="spd-text-center">#</th>
                                            <th>Team Member</th>
                                            <th class="spd-text-right">POs Issued</th>
                                        </tr>
                                    </thead>
                                    <tbody id="summary-table-body"></tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    <div class="spd-card spd-col-8" style="margin-bottom:0;">
                        <div class="spd-card-header">
                            <h2><i class="fa-solid fa-chart-pie spd-badge-navy"></i> PO Approval & Workflow Pipeline</h2>
                            <button class="spd-btn spd-btn-outline spd-download-chart" data-chart="approvalPieChart" data-title="PO Approval & Workflow Pipeline" title="Download Chart">
                                <i class="fa-solid fa-download"></i>
                            </button>
                        </div>
                        <div class="spd-card-body">
                            <div class="spd-chart-container" style="height: 180px;">
                                <canvas id="approvalPieChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Purchase Orders Log -->
                <div class="spd-card">
                    <div class="spd-card-header">
                        <h2><i class="fa-solid fa-file-invoice-dollar spd-badge-navy"></i> Purchase Orders Log
                            <span style="font-size: 11px; font-weight: normal; color: var(--text-muted); margin-left: 8px;"></span>
                        </h2>
                        <div style="display:flex;gap:8px;align-items:center;">
                            <div class="spd-search-box">
                                <i class="fa-solid fa-magnifying-glass"></i>
                                <input type="text" id="spd-global-search" placeholder="Search PO, MR, supplier...">
                            </div>
                            <span style="font-size:12px;color:#64748b;" id="spd-grid-count">Showing 0 of 0 Records</span>
                        </div>
                    </div>
                    <div class="spd-card-body spd-p-0">
                        <div class="spd-custom-table-wrapper">
                            <table class="spd-custom-table" id="poGrid">
                                <thead>
                                    <tr>
                                        <th class="spd-text-center" style="width:40px;">#</th>
                                        <th>PO Number</th>
                                        <th>Date</th>
                                        <th>MR No. (Material Req)</th>
                                        <th>MR Date</th>
                                        <th>Supplier</th>
                                        <th>Project</th>
                                        <th>Created By</th>
                                        <th class="spd-text-right">Total</th>
                                        <th class="spd-text-center">Workflow State</th>
                                    </tr>
                                </thead>
                                <tbody id="detail-table-body"></tbody>
                            </table>
                        </div>
                        <div class="spd-pagination" id="spd-pagination"></div>
                    </div>
                </div>

            </div>
        `);
    }

    create_filters() {
        this.filters = {};
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1;

        const fields = [
            { fieldname: "company", label: "Company", fieldtype: "Link", options: "Company", default: frappe.defaults.get_user_default("Company") },
            { fieldname: "year", label: "Year ", fieldtype: "Select", options: `\n${currentYear - 1}\n${currentYear}\n${currentYear + 1}`, default: String(currentYear), reqd: 1 },
            { fieldname: "month", label: "Month ", fieldtype: "Select", options: "\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12", default: String(currentMonth), reqd: 1 },
            { fieldname: "from_date", label: "From Date", fieldtype: "Date", default: frappe.datetime.month_start() },
            { fieldname: "to_date", label: "To Date", fieldtype: "Date", default: frappe.datetime.month_end() },
            { fieldname: "supplier", label: "Supplier", fieldtype: "Link", options: "Supplier" },
            { fieldname: "project", label: "Project", fieldtype: "Link", options: "Project" },
            { fieldname: "owner", label: "Created By", fieldtype: "Link", options: "User" }
        ];

        fields.forEach(df => {
            const col = $('<div class="spd-filter-group"></div>')
                .appendTo($(this.page.body).find("#filter-area"));
            $(`<label>${df.label}</label>`).appendTo(col);

            this.filters[df.fieldname] = frappe.ui.form.make_control({
                parent: col,
                df: { ...df, label: null },
                render_input: true
            });

            if (df.default) {
                this.filters[df.fieldname].set_value(df.default);
            }
        });
    }

    bind_events() {
        this.page.add_inner_button(__("Refresh"), () => {
            if (!this.validate_filters()) return;
            this.load_dashboard();
        });
        this.page.add_inner_button(__("Print"), () => this.printGrid());
        this.page.add_inner_button(__("Excel"), () => this.exportGridToExcel());

        // Style all buttons to match Petty Cash Executive Dashboard (all white/outline style)
        const $toolbar = $(this.page.inner_toolbar);
        const $refreshBtn = $toolbar.find('.btn-inner:contains("Refresh")');
        const $printBtn = $toolbar.find('.btn-inner:contains("Print")');
        const $excelBtn = $toolbar.find('.btn-inner:contains("Excel")');

        [$refreshBtn, $printBtn, $excelBtn].forEach($btn => {
            if ($btn && $btn.length) {
                $btn.css({
                    'background': '#ffffff',
                    'color': '#374151',
                    'border': '1px solid #d1d5db',
                    'font-weight': '500'
                });
            }
        });

        if ($refreshBtn.length) $refreshBtn.html('<i class="fa fa-refresh"></i> ' + __("Refresh"));
        if ($printBtn.length) $printBtn.html('<i class="fa fa-print"></i> ' + __("Print"));
        if ($excelBtn.length) $excelBtn.html('<i class="fa fa-file-excel-o"></i> ' + __("Excel"));

        $(this.page.body).on("click", ".spd-tab-switcher .spd-tab-btn", (e) => {
            const $btn = $(e.currentTarget);
            const $switcher = $btn.closest(".spd-tab-switcher");
            const card = $switcher.data("card");
            const view = $btn.data("view");
            this.switch_tab(card, view);
        });

        $(this.page.body).on("click", ".spd-download-chart", (e) => {
            const $btn = $(e.currentTarget);
            const chartKey = $btn.data("chart");
            const title = $btn.data("title");
            this.download_chart(chartKey, title);
        });

        $(this.page.body).on("click", "#spd-reset-filters", () => {
            this.reset_filters();
        });

        $(this.page.body).on("keyup", "#spd-global-search", (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.currentPage = 0;
                this.load_grid_page(0);
            }, 400);
        });

        // Pagination events
        $(this.page.body).on("click", "#spd-pagination button[data-start]", (e) => {
            const start = parseInt($(e.currentTarget).data("start"), 10);
            if (!isNaN(start)) this.load_grid_page(start);
        });

        $(this.page.body).on("change", "#spd-page-input", (e) => {
            const totalPages = Math.max(1, Math.ceil(this.totalRecords / this.pageLength));
            let v = parseInt($(e.currentTarget).val() || 1, 10);
            if (isNaN(v) || v < 1) v = 1;
            if (v > totalPages) v = totalPages;
            this.load_grid_page((v - 1) * this.pageLength);
        });

        $(this.page.body).on("keypress", "#spd-page-input", (e) => {
            if (e.key === "Enter") $(e.currentTarget).trigger("change");
        });

        $(this.page.body).on("change", "#spd-page-length", (e) => {
            this.pageLength = parseInt($(e.currentTarget).val(), 10) || 50;
            this.currentPage = 0;
            this.load_grid_page(0);
        });

        // Auto-refresh on filter change (like Petty Cash Executive Dashboard)
        let filterTimeout;
        const queueDashboardRefresh = () => {
            clearTimeout(filterTimeout);
            filterTimeout = setTimeout(() => {
                if (this.validate_filters()) {
                    this.load_dashboard();
                }
            }, 400);
        };

        // Bind change events to all filter fields for auto-refresh
        if (this.filters.year) {
            this.filters.year.$input.on("change", () => {
                this.sync_date_range_from_year_month();
                queueDashboardRefresh();
            });
        }
        if (this.filters.month) {
            this.filters.month.$input.on("change", () => {
                this.sync_date_range_from_year_month();
                queueDashboardRefresh();
            });
        }
        if (this.filters.company) {
            this.filters.company.$input.on("change", queueDashboardRefresh);
        }
        if (this.filters.from_date) {
            this.filters.from_date.$input.on("change", queueDashboardRefresh);
        }
        if (this.filters.to_date) {
            this.filters.to_date.$input.on("change", queueDashboardRefresh);
        }
        if (this.filters.supplier) {
            this.filters.supplier.$input.on("change", queueDashboardRefresh);
        }
        if (this.filters.project) {
            this.filters.project.$input.on("change", queueDashboardRefresh);
        }
        if (this.filters.owner) {
            this.filters.owner.$input.on("change", queueDashboardRefresh);
        }
    }

    reset_filters() {
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1;

        if (this.filters.company) this.filters.company.set_value(frappe.defaults.get_user_default("Company"));
        if (this.filters.year) this.filters.year.set_value(String(currentYear));
        if (this.filters.month) this.filters.month.set_value(String(currentMonth));
        if (this.filters.from_date) this.filters.from_date.set_value(frappe.datetime.month_start());
        if (this.filters.to_date) this.filters.to_date.set_value(frappe.datetime.month_end());
        if (this.filters.supplier) this.filters.supplier.set_value("");
        if (this.filters.project) this.filters.project.set_value("");
        if (this.filters.owner) this.filters.owner.set_value("");

        // Auto-refresh after reset
        setTimeout(() => {
            if (this.validate_filters()) {
                this.load_dashboard();
            }
        }, 100);
    }

    sync_date_range_from_year_month() {
        const year = this.filters.year ? this.filters.year.get_value() : null;
        const month = this.filters.month ? this.filters.month.get_value() : null;

        if (year && month && month !== "") {
            const monthNum = parseInt(month, 10);
            const lastDay = new Date(year, monthNum, 0).getDate();
            const fromDate = `${year}-${String(monthNum).padStart(2, '0')}-01`;
            const toDate = `${year}-${String(monthNum).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;

            if (this.filters.from_date) this.filters.from_date.set_value(fromDate);
            if (this.filters.to_date) this.filters.to_date.set_value(toDate);
        }
    }

    printGrid() {
        const tableHtml = document.querySelector('#poGrid').outerHTML;
        const title = __("Purchase Orders Log");
        const styles = `
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
                th { background: #f3f4f6; }
            </style>`;
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`<!DOCTYPE html><html><head><title>${title}</title>${styles}</head><body><h1>${title}</h1>${tableHtml}</body></html>`);
        printWindow.document.close();
        printWindow.focus();
        printWindow.print();
    }

    exportGridToExcel() {
        const tableHtml = document.querySelector('#poGrid').outerHTML;
        const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>${tableHtml}</body></html>`;
        const blob = new Blob([html], { type: 'application/vnd.ms-excel;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'purchase_orders_log.xls';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
    }

    download_chart(chartKey, title) {
        const chart = this.charts[chartKey];
        if (!chart) {
            frappe.show_alert({ message: __("Chart not available"), indicator: "orange" });
            return;
        }
        const link = document.createElement("a");
        link.download = `${title.replace(/\s+/g, "_")}.png`;
        link.href = chart.toBase64Image();
        link.click();
    }

    switch_tab(card, view) {
        const $chartView = $(this.page.body).find(`#${card}-chart-view`);
        const $tableView = $(this.page.body).find(`#${card}-table-view`);
        const $btns = $(this.page.body).find(`.spd-tab-switcher[data-card="${card}"] .spd-tab-btn`);

        $btns.removeClass("active");
        $btns.filter(`[data-view="${view}"]`).addClass("active");

        if (view === "chart") {
            $chartView.show();
            $tableView.hide();
        } else {
            $chartView.hide();
            $tableView.show();
        }
    }

    validate_filters() {
        const mandatory = ['year', 'month'];
        let missing = [];

        mandatory.forEach(key => {
            if (!this.filters[key].get_value()) {
                missing.push(this.filters[key].df.label || key);
            }
        });

        if (missing.length) {
            frappe.show_alert({
                message: __("Please fill mandatory filters: {0}", [missing.join(", ")]),
                indicator: "red"
            });
            return false;
        }
        return true;
    }

    show_empty_state() {
        const msg = '<p class="spd-empty">Select Year & Month, then click Refresh to load data</p>';
        $(this.page.body).find("#supplier-chart-view").html(msg);
        $(this.page.body).find("#project-chart-view").html(msg);
        $(this.page.body).find(".spd-chart-container canvas").each(function () { $(this).remove(); });
    }

    get_filters() {
        let filters = {};
        Object.keys(this.filters).forEach(key => {
            filters[key] = this.filters[key].get_value();
        });
        return filters;
    }

    fmt_currency(value) {
        return format_currency(value || 0, frappe.defaults.get_default("currency"));
    }

    load_dashboard() {
        const filters = this.get_filters();

        frappe.call({
            method: "custom_addons.custom_addons.page.supplier_purchase_da.supplier_purchase_da.get_dashboard_data",
            args: { filters: JSON.stringify(filters) },
            callback: (r) => {
                if (!r.message) return;

                $("#total-po").html(this.fmt_currency(r.message.kpis.total_po));
                $("#po-count").html(r.message.kpis.po_count || 0);
                $("#supplier-count").html(r.message.kpis.new_suppliers || 0);
                $("#avg-po").html(this.fmt_currency(r.message.kpis.average_po));
                $("#pending-po-count").html(`${r.message.kpis.pending_po_count || 0} Orders`);
                $("#pending-po-value").html(`${this.fmt_currency(r.message.kpis.pending_po_value)} awaiting approval`);

                this.render_bar_chart({
                    canvas_id: "supplierChart",
                    view_id: "supplier-chart-view",
                    chart_key: "supplierChart",
                    chart_data: r.message.supplier_chart,
                    base_color: "#d94e34"
                });
                this.render_supplier_table(r.message.supplier_chart.table);

                this.render_bar_chart({
                    canvas_id: "projectChart",
                    view_id: "project-chart-view",
                    chart_key: "projectChart",
                    chart_data: r.message.project_chart,
                    base_color: "#0b4c80"
                });
                this.render_project_table(r.message.project_chart.table);

                this.render_pie_chart(r.message.approval_pipeline);

                this.render_team_summary(r.message.team_summary);

                // Store all rows for client-side pagination
                this.all_detail_rows = r.message.purchase_orders || [];
                this.totalRecords = this.all_detail_rows.length;
                this.currentPage = 0;
                this.load_grid_page(0);
            }
        });
    }

    load_grid_page(start) {
        this.currentPage = start;
        const searchTerm = $("#spd-global-search").val() || "";

        // Filter rows based on search
        let filteredRows = this.all_detail_rows;
        if (searchTerm) {
            const term = searchTerm.toLowerCase();
            filteredRows = this.all_detail_rows.filter(row => {
                const text = `${row.po_number || ""} ${row.mr_no || ""} ${row.supplier_name || ""} ${row.project_name || ""} ${row.created_by || ""}`.toLowerCase();
                return text.includes(term);
            });
        }

        this.totalRecords = filteredRows.length;
        const end = Math.min(start + this.pageLength, this.totalRecords);
        const pageRows = filteredRows.slice(start, end);

        this.render_detail_table(pageRows);
        this.render_pagination(start, this.totalRecords);
    }

    render_pagination(start, total) {
        const pageLength = this.pageLength;
        const end = Math.min(start + pageLength, total);
        $("#spd-grid-count").text(__("Showing {0}–{1} of {2} Records", [total ? start + 1 : 0, end, total]));

        const totalPages = Math.max(1, Math.ceil(total / pageLength));
        const currentPageNum = Math.floor(start / pageLength) + 1;

        let html = '<div style="display:flex;gap:8px;align-items:center;justify-content:center;flex-wrap:wrap;">';

        // First page
        html += `<button data-start="0" ${start === 0 ? 'disabled' : ''} title="${__("First")}"><i class="fa-solid fa-angles-left"></i></button>`;

        // Previous page
        html += `<button data-start="${Math.max(0, start - pageLength)}" ${start === 0 ? 'disabled' : ''} title="${__("Previous")}"><i class="fa-solid fa-chevron-left"></i></button>`;

        // Page input
        html += `<span style="display:flex;gap:8px;align-items:center;">${__("Page")} <input id="spd-page-input" type="number" min="1" max="${totalPages}" value="${currentPageNum}" style="width:50px;padding:5px 8px;border:1px solid #d1d5db;border-radius:6px;text-align:center;height:32px;"> ${__("of")} ${totalPages}</span>`;

        // Next page
        html += `<button data-start="${Math.min((totalPages - 1) * pageLength, start + pageLength)}" ${end >= total ? 'disabled' : ''} title="${__("Next")}"><i class="fa-solid fa-chevron-right"></i></button>`;

        // Last page
        html += `<button data-start="${Math.max(0, (totalPages - 1) * pageLength)}" ${end >= total ? 'disabled' : ''} title="${__("Last")}"><i class="fa-solid fa-angles-right"></i></button>`;

        // Page length selector
        html += '<select id="spd-page-length" style="padding:5px 8px;border:1px solid #d1d5db;border-radius:6px;background:white;height:32px;cursor:pointer;">';
        [10, 25, 50, 100].forEach(l => {
            html += `<option value="${l}" ${l === pageLength ? 'selected' : ''}>${l} / ${__("page")}</option>`;
        });
        html += '</select></div>';

        $("#spd-pagination").html(html);
    }

    ensure_canvas(view_id, canvas_id) {
        const $view = $(this.page.body).find("#" + view_id);
        if (!$view.find("#" + canvas_id).length) {
            $view.html(`<canvas id="${canvas_id}"></canvas>`);
        }
        return document.getElementById(canvas_id);
    }

    render_bar_chart({ canvas_id, view_id, chart_key, chart_data, base_color }) {
        if (this.charts[chart_key]) {
            this.charts[chart_key].destroy();
            this.charts[chart_key] = null;
        }

        if (!chart_data || !chart_data.labels || !chart_data.labels.length) {
            $(this.page.body).find("#" + view_id).html('<p class="spd-empty">No data available</p>');
            return;
        }

        const canvas = this.ensure_canvas(view_id, canvas_id);
        const ctx = canvas.getContext("2d");
        const currency = frappe.defaults.get_default("currency") || "SAR";

        // Generate gradient colors - first bar is darkest, subsequent bars fade
        const colors = this.generate_bar_colors(chart_data.values.length, base_color);

        this.charts[chart_key] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chart_data.labels,
                datasets: [{
                    label: `Total PO Value (${currency})`,
                    data: chart_data.values,
                    backgroundColor: colors,
                    borderRadius: { topLeft: 6, topRight: 6, bottomLeft: 0, bottomRight: 0 },
                    borderSkipped: false,
                    barPercentage: 0.55,
                    categoryPercentage: 0.65
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ' ' + this.fmt_currency(ctx.parsed.y)
                        }
                    }
                },
                scales: {
                    y: { grid: { color: '#f1f5f9' }, ticks: { font: { family: 'Inter', size: 10.5 }, color: '#64748b' } },
                    x: { 
                        grid: { display: false }, 
                        ticks: { 
                            font: { family: 'Inter', size: 10.5, weight: '500' }, 
                            color: '#475569',
                            maxRotation: 0,
                            minRotation: 0,
                            autoSkip: false,
                            callback: function(value, index, values) {
                                const label = this.getLabelForValue(value);
                                if (label.length > 18) {
                                    return label.substring(0, 18) + '...';
                                }
                                return label;
                            }
                        } 
                    }
                }
            }
        });
    }

    generate_bar_colors(count, baseColor) {
        // Parse base color to RGB
        const hex = baseColor.replace('#', '');
        const r = parseInt(hex.substring(0, 2), 16);
        const g = parseInt(hex.substring(2, 4), 16);
        const b = parseInt(hex.substring(4, 6), 16);

        const colors = [];
        for (let i = 0; i < count; i++) {
            // First bar is full opacity, subsequent bars fade
            const opacity = i === 0 ? 1 : Math.max(0.15, 1 - (i * 0.25));
            colors.push(`rgba(${r}, ${g}, ${b}, ${opacity})`);
        }
        return colors;
    }

    render_pie_chart(chart_data) {
        if (this.charts.approvalPieChart) {
            this.charts.approvalPieChart.destroy();
            this.charts.approvalPieChart = null;
        }

        const $container = $(this.page.body).find("#approvalPieChart").length
            ? $(this.page.body).find("#approvalPieChart").closest(".spd-chart-container")
            : $(this.page.body).find(".spd-card-header:contains('Approval')").closest(".spd-card").find(".spd-chart-container");

        if (!chart_data || !chart_data.labels || !chart_data.labels.length) {
            $container.html('<p class="spd-empty">No data available</p>');
            return;
        }

        if (!$container.find("#approvalPieChart").length) {
            $container.html('<canvas id="approvalPieChart"></canvas>');
        }
        const ctx = document.getElementById("approvalPieChart").getContext("2d");

        this.charts.approvalPieChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: chart_data.labels,
                datasets: [{
                    data: chart_data.values,
                    backgroundColor: chart_data.colors,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { boxWidth: 12, font: { family: 'Inter', size: 11 } } },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `${ctx.label}: ${ctx.parsed} PO${ctx.parsed === 1 ? '' : 's'}`
                        }
                    }
                }
            }
        });
    }

    render_supplier_table(rows) {
        const $tbody = $(this.page.body).find("#supplier-table-body");
        $tbody.empty();

        if (!rows || !rows.length) {
            $tbody.html('<tr><td colspan="3" class="spd-empty">No data available</td></tr>');
            return;
        }

        let total = 0;
        rows.forEach(r => {
            total += r.total;
            $tbody.append(`
                <tr>
                    <td>${frappe.utils.escape_html(r.supplier_name)}</td>
                    <td>${frappe.utils.escape_html(r.supplier_code)}</td>
                    <td class="spd-text-right">${this.fmt_currency(r.total)}</td>
                </tr>
            `);
        });
        $tbody.append(`
            <tr class="spd-total-row">
                <td>Total</td><td>-</td>
                <td class="spd-text-right">${this.fmt_currency(total)}</td>
            </tr>
        `);
    }

    render_project_table(rows) {
        const $tbody = $(this.page.body).find("#project-table-body");
        $tbody.empty();

        if (!rows || !rows.length) {
            $tbody.html('<tr><td colspan="2" class="spd-empty">No data available</td></tr>');
            return;
        }

        let total = 0;
        rows.forEach(r => {
            total += r.total;
            $tbody.append(`
                <tr>
                    <td>${frappe.utils.escape_html(r.project_name)}</td>
                    <td class="spd-text-right">${this.fmt_currency(r.total)}</td>
                </tr>
            `);
        });
        $tbody.append(`
            <tr class="spd-total-row">
                <td>Total</td>
                <td class="spd-text-right">${this.fmt_currency(total)}</td>
            </tr>
        `);
    }

    render_team_summary(data) {
        const $tbody = $(this.page.body).find("#summary-table-body");
        $tbody.empty();

        if (!data || !data.length) {
            $tbody.html('<tr><td colspan="3" class="spd-empty">No data available</td></tr>');
            return;
        }

        data.forEach((row, i) => {
            $tbody.append(`
                <tr>
                    <td class="spd-text-center spd-text-muted">${i + 1}</td>
                    <td>${frappe.utils.escape_html(row.team_member)}</td>
                    <td class="spd-text-right" style="font-weight:700; color:var(--coral-flame);">${row.po_count}</td>
                </tr>
            `);
        });
    }

    status_class(value) {
        const label = (value || "").toLowerCase();
        if (label.includes("cancel")) return "spd-pill-cancelled";
        if (label.includes("pending") || label.includes("review") || label.includes("awaiting")) return "spd-pill-pending";
        if (label.includes("draft")) return "spd-pill-draft";
        if (label.includes("approved") || label.includes("complete")) return "spd-pill-approved";
        return "spd-pill-draft";
    }

    render_detail_table(data) {
        const $tbody = $(this.page.body).find("#detail-table-body");
        $tbody.empty();

        if (!data || !data.length) {
            $tbody.html('<tr><td colspan="10" class="spd-empty">No data available</td></tr>');
            return;
        }

        data.forEach((row, i) => {
            $tbody.append(`
                <tr>
                    <td class="spd-text-center spd-text-muted">${i + 1}</td>
                    <td><a href="/app/purchase-order/${row.po_number}" target="_blank" style="color: var(--navy-primary); font-weight:600;">${row.po_number}</a></td>
                    <td>${row.date || '-'}</td>
                    <td>${row.mr_no
                        ? `<a href="/app/material-request/${row.mr_no}" target="_blank" style="color: var(--coral-flame); font-weight:600;">${row.mr_no}</a>`
                        : '<span class="spd-text-muted">-</span>'}</td>
                    <td>${row.mr_date || '<span class="spd-text-muted">-</span>'}</td>
                    <td>${frappe.utils.escape_html(row.supplier_name || '')}</td>
                    <td>${frappe.utils.escape_html(row.project_name || '-')}</td>
                    <td>${frappe.utils.escape_html(row.created_by || '')}</td>
                    <td class="spd-text-right" style="font-weight:600;">${this.fmt_currency(row.grand_total)}</td>
                    <td class="spd-text-center"><span class="spd-status-pill ${this.status_class(row.workflow_status)}">${frappe.utils.escape_html(row.workflow_status || 'Draft')}</span></td>
                </tr>
            `);
        });
    }

    filter_detail_table(term) {
        term = (term || "").toLowerCase();
        const $rows = $(this.page.body).find("#detail-table-body tr");
        $rows.each(function () {
            const text = $(this).text().toLowerCase();
            $(this).toggle(text.includes(term));
        });
    }
}