frappe.ui.form.on("Supplier Scorecard Settings", {
        refresh(frm) {
                frm.add_custom_button(__("Load Sample Values"), () => {
                        frappe.confirm(__("Replace everything on this form with the sample values?"), () =>
                                frm.call("load_defaults").then(() => frm.dirty() || frm.refresh())
                        );
                });

                render_guide(frm);
        },
});

function render_guide(frm) {
        if (!frm.fields_dict.guide_html) return;
        const $wrapper = frm.fields_dict.guide_html.$wrapper;
        $wrapper.html(`
                <div class="spd-guide-container" style="padding: 15px 5px; font-size: 13px; color: var(--text-color); line-height: 1.6;">

                        <!-- Header banner -->
                        <div style="background: linear-gradient(135deg, #1e293b, #0f172a); color: #fff; padding: 24px; border-radius: 8px; margin-bottom: 24px;">
                                <h3 style="color: #fff; margin: 0 0 8px 0; font-size: 20px; font-weight: 700;">Supplier Performance Dashboard - Calculation & Operations Guide</h3>
                                <p style="margin: 0; color: #94a3b8; font-size: 13px; max-width: 900px;">
                                        This guide explains the automated data collection, mathematical scoring formulas, and business rules used by the Supplier Performance Dashboard. All evaluations are calculated live from operational ERPNext transactions (Purchase Orders, Receipts, and RFQs) without requiring manual scorecard entries.
                                </p>
                        </div>

                        <!-- Section 1: The 3-Step Scoring Formula -->
                        <div class="card" style="border: 1px solid var(--border-color); border-radius: 8px; padding: 20px; margin-bottom: 20px; background: var(--card-bg);">
                                <h4 style="margin: 0 0 16px 0; font-size: 16px; font-weight: 700; color: var(--text-color); display: flex; align-items: center; gap: 8px;">
                                        <span style="background: #3b82f6; color: #fff; width: 24px; height: 24px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 12px;">1</span>
                                        The 3-Step Scoring Formula
                                </h4>
                                <div class="row">
                                        <div class="col-md-4" style="margin-bottom: 15px;">
                                                <div style="background: var(--bg-light-gray); padding: 15px; border-radius: 6px; height: 100%; border: 1px solid var(--border-color);">
                                                        <strong style="display: block; margin-bottom: 6px; color: var(--text-color);">Step 1: Raw Fact Extraction</strong>
                                                        <p style="margin: 0; font-size: 12px; color: var(--text-muted);">
                                                                Raw performance metrics are computed directly from transactions (e.g. 50% on-time delivery, 100% accepted quality, 4.2 days quote turnaround).
                                                        </p>
                                                </div>
                                        </div>
                                        <div class="col-md-4" style="margin-bottom: 15px;">
                                                <div style="background: var(--bg-light-gray); padding: 15px; border-radius: 6px; height: 100%; border: 1px solid var(--border-color);">
                                                        <strong style="display: block; margin-bottom: 6px; color: var(--text-color);">Step 2: Rating (1 to 5 Stars)</strong>
                                                        <p style="margin: 0; font-size: 12px; color: var(--text-muted);">
                                                                Raw values are matched against the <strong>Rating Rules</strong> table configured in this DocType. Failing all rules automatically gives the floor rating of <strong>1</strong>.
                                                        </p>
                                                </div>
                                        </div>
                                        <div class="col-md-4" style="margin-bottom: 15px;">
                                                <div style="background: var(--bg-light-gray); padding: 15px; border-radius: 6px; height: 100%; border: 1px solid var(--border-color);">
                                                        <strong style="display: block; margin-bottom: 6px; color: var(--text-color);">Step 3: Weighted Points & Score</strong>
                                                        <p style="margin: 0; font-size: 12px; color: var(--text-muted);">
                                                                Points earned = <code>(Rating / 5) &times; Weight</code>.<br>
                                                                Overall Score (%) = <code>(Total Points / Evaluated Weight) &times; 100</code>.<br>
                                                                Weighted Score (/5) = <code>(Total Points / Evaluated Weight) &times; 5</code>.
                                                        </p>
                                                </div>
                                        </div>
                                </div>
                                <div style="background: #f8fafc; border-left: 4px solid #3b82f6; padding: 10px 14px; border-radius: 0 4px 4px 0; margin-top: 10px; font-size: 12px; color: #334155;">
                                        <strong>Fairness & N/A Rule:</strong> If a criterion has no source records in the evaluated month (or no ERP module exists, like HSE), its weight is automatically omitted from the denominator. Suppliers are never penalized for unmeasured categories.
                                </div>
                        </div>

                        <!-- Section 2: The 8 Criteria & Data Sources -->
                        <div class="card" style="border: 1px solid var(--border-color); border-radius: 8px; padding: 20px; margin-bottom: 20px; background: var(--card-bg);">
                                <h4 style="margin: 0 0 16px 0; font-size: 16px; font-weight: 700; color: var(--text-color); display: flex; align-items: center; gap: 8px;">
                                        <span style="background: #10b981; color: #fff; width: 24px; height: 24px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 12px;">2</span>
                                        Data Sources & Metric Calculations
                                </h4>
                                <div class="table-responsive">
                                        <table class="table table-bordered table-sm" style="font-size: 12px; margin-bottom: 0;">
                                                <thead style="background: var(--bg-light-gray);">
                                                        <tr>
                                                                <th style="width: 18%;">Criterion (Weight)</th>
                                                                <th style="width: 25%;">Source DocTypes</th>
                                                                <th style="width: 32%;">Calculation Logic</th>
                                                                <th style="width: 25%;">Rating Thresholds (5 to 2)</th>
                                                        </tr>
                                                </thead>
                                                <tbody>
                                                        <tr>
                                                                <td><strong>Delivery / Lead Time</strong><br><span class="text-muted">Weight: 20%</span></td>
                                                                <td><code>Purchase Order</code><br><code>Purchase Receipt</code><br><code>Item</code> (is_stock_item=1)</td>
                                                                <td>For stock PO lines scheduled in the month: checks if received on or before the committed <strong>Schedule Date</strong>.<br><em>Missed/overdue deliveries count as 0%.</em></td>
                                                                <td>5: &ge; 95%<br>4: &ge; 85%<br>3: &ge; 70%<br>2: &ge; 50%<br>1: &lt; 50%</td>
                                                        </tr>
                                                        <tr>
                                                                <td><strong>Quality & Defects</strong><br><span class="text-muted">Weight: 25%</span></td>
                                                                <td><code>Purchase Receipt Item</code></td>
                                                                <td><code>Accepted Qty / (Accepted Qty + Rejected Qty) &times; 100</code> on receipts posted in that month.</td>
                                                                <td>5: &ge; 99%<br>4: &ge; 97%<br>3: &ge; 93%<br>2: &ge; 85%<br>1: &lt; 85%</td>
                                                        </tr>
                                                        <tr>
                                                                <td><strong>Price / Commercial</strong><br><span class="text-muted">Weight: 20%</span></td>
                                                                <td><code>Supplier Quotation</code><br><code>Request for Quotation</code></td>
                                                                <td>Compares rate against the <strong>lowest competing quotation</strong> for the same RFQ item:<br><code>% Premium = (Rate / Lowest - 1) &times; 100</code>.<br><em>(Lower is better)</em></td>
                                                                <td>5: &le; 0% (cheapest)<br>4: &le; 5% premium<br>3: &le; 10% premium<br>2: &le; 20% premium<br>1: &gt; 20% premium</td>
                                                        </tr>
                                                        <tr>
                                                                <td><strong>Responsiveness</strong><br><span class="text-muted">Weight: 10%</span></td>
                                                                <td><code>Request for Quotation</code><br><code>Supplier Quotation</code></td>
                                                                <td>Turnaround days from <strong>RFQ Date</strong> to the supplier's first submitted quote.<br><em>Unanswered RFQs after 7 days are penalized with 15 days. (Lower is better)</em></td>
                                                                <td>5: &le; 2 days<br>4: &le; 5 days<br>3: &le; 7 days<br>2: &le; 10 days<br>1: &gt; 10 days / ignored</td>
                                                        </tr>
                                                        <tr>
                                                                <td><strong>Payment Terms</strong><br><span class="text-muted">Weight: 5%</span></td>
                                                                <td><code>Purchase Order</code> &rarr; <code>Payment Schedule</code></td>
                                                                <td>Weighted agreed credit period (days):<br><code>credit_days + (30 &times; credit_months)</code> on formal PO schedules.</td>
                                                                <td>5: &ge; 60 days credit<br>4: &ge; 45 days credit<br>3: &ge; 30 days credit<br>2: &ge; 15 days credit<br>1: &lt; 15 days (cash/advance)</td>
                                                        </tr>
                                                        <tr style="color: var(--text-muted); background: var(--bg-light-gray);">
                                                                <td><strong>HSE & Compliance (5%)<br>Documentation (10%)<br>Compliance (5%)</strong></td>
                                                                <td><em>No standard ERP table yet</em><br>(Data Source = <code>No source</code>)</td>
                                                                <td>Represent the client's corporate governance framework. Automatically treated as <strong>N/A</strong> and omitted from the evaluated denominator without score penalty.</td>
                                                                <td>Always <strong>N/A</strong> until a custom module (e.g. Vendor Safety Audit) is connected.</td>
                                                        </tr>
                                                </tbody>
                                        </table>
                                </div>
                        </div>

                                                <!-- Section 3: Step-by-Step Worked Example -->
                        <div class="card" style="border: 1px solid var(--border-color); border-radius: 8px; padding: 20px; margin-bottom: 20px; background: var(--card-bg);">
                                <h4 style="margin: 0 0 16px 0; font-size: 16px; font-weight: 700; color: var(--text-color); display: flex; align-items: center; gap: 8px;">
                                        <span style="background: #f59e0b; color: #fff; width: 24px; height: 24px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 12px;">3</span>
                                        Worked Example: Comprehensive Supplier Evaluation
                                </h4>
                                <p style="font-size: 12px; margin-bottom: 12px; color: var(--text-muted);">
                                        This worked example demonstrates how an overall score is computed when representative transactions are evaluated across all criteria. Delivery and Quality reflect live purchase order and receipt tracking, while other criteria illustrate standard operational calculations with general numbers.
                                </p>
                                <div class="table-responsive">
                                        <table class="table table-bordered table-sm" style="font-size: 12px; margin-bottom: 12px;">
                                                <thead style="background: var(--bg-light-gray);">
                                                        <tr>
                                                                <th style="width: 18%;">Criterion (Weight)</th>
                                                                <th style="width: 34%;">Operational Transaction Facts</th>
                                                                <th style="width: 18%;">Raw Measured Value</th>
                                                                <th style="width: 15%;">Rating Awarded</th>
                                                                <th style="width: 15%;">Points Earned</th>
                                                        </tr>
                                                </thead>
                                                <tbody>
                                                        <tr>
                                                                <td><strong>Delivery / Lead Time</strong><br><span class="text-muted">Weight: 20%</span></td>
                                                                <td>• PO Line 1: Promised on Day 2 &rarr; Received on Day 2 (100% on time)<br>• PO Line 2: Promised on Day 10 &rarr; 0 delivered by scheduled date (0% on time)</td>
                                                                <td>(100% + 0%) / 2 = <strong>50.0%</strong> on-time</td>
                                                                <td><span style="background: #ffedd5; color: #9a3412; padding: 2px 8px; border-radius: 99px; font-weight: 700;">Rating 2</span><br>(&ge; 50%)</td>
                                                                <td>(2 / 5) &times; 20% = <strong>8.0 points</strong></td>
                                                        </tr>
                                                        <tr>
                                                                <td><strong>Quality & Defects</strong><br><span class="text-muted">Weight: 25%</span></td>
                                                                <td>• Purchase Receipt: 100 units accepted, 0 units rejected</td>
                                                                <td>100 / (100 + 0) = <strong>100.0%</strong> accepted</td>
                                                                <td><span style="background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 99px; font-weight: 700;">Rating 5</span><br>(&ge; 99%)</td>
                                                                <td>(5 / 5) &times; 25% = <strong>25.0 points</strong></td>
                                                        </tr>
                                                        <tr>
                                                                <td><strong>Price / Commercial</strong><br><span class="text-muted">Weight: 20%</span></td>
                                                                <td>• RFQ Quote: Supplier quoted SAR 10,200<br>• Benchmark: Lowest competing quotation = SAR 10,000<br>• Premium = ((10,200 / 10,000) - 1) &times; 100 = +2.0%</td>
                                                                <td><strong>+2.0%</strong> premium over lowest</td>
                                                                <td><span style="background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 99px; font-weight: 700;">Rating 4</span><br>(&le; 5% premium)</td>
                                                                <td>(4 / 5) &times; 20% = <strong>16.0 points</strong></td>
                                                        </tr>
                                                        <tr>
                                                                <td><strong>Responsiveness</strong><br><span class="text-muted">Weight: 10%</span></td>
                                                                <td>• RFQ-1: Quoted in 3 business days<br>• RFQ-2: Quoted in 3 business days<br>• Average quote turnaround = 3.0 days</td>
                                                                <td><strong>3.0 days</strong> average response</td>
                                                                <td><span style="background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 99px; font-weight: 700;">Rating 4</span><br>(&le; 5 days)</td>
                                                                <td>(4 / 5) &times; 10% = <strong>8.0 points</strong></td>
                                                        </tr>
                                                        <tr>
                                                                <td><strong>Payment Terms</strong><br><span class="text-muted">Weight: 5%</span></td>
                                                                <td>• Purchase Order Payment Schedule: 45 Days Credit agreed on formal purchase contracts</td>
                                                                <td><strong>45 days</strong> credit terms</td>
                                                                <td><span style="background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 99px; font-weight: 700;">Rating 4</span><br>(&ge; 45 days credit)</td>
                                                                <td>(4 / 5) &times; 5% = <strong>4.0 points</strong></td>
                                                        </tr>
                                                        <tr>
                                                                <td><strong>HSE & Safety</strong><br><span class="text-muted">Weight: 5%</span></td>
                                                                <td>• Periodic Health, Safety & Environment inspection checklist: 95% compliance score</td>
                                                                <td><strong>95.0%</strong> safety compliance</td>
                                                                <td><span style="background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 99px; font-weight: 700;">Rating 5</span><br>(&ge; 95%)</td>
                                                                <td>(5 / 5) &times; 5% = <strong>5.0 points</strong></td>
                                                        </tr>
                                                        <tr>
                                                                <td><strong>Documentation</strong><br><span class="text-muted">Weight: 10%</span></td>
                                                                <td>• Required submittals & shipping dossiers: 9 out of 10 fully accurate and complete on initial submission</td>
                                                                <td>9 / 10 = <strong>90.0%</strong> accuracy</td>
                                                                <td><span style="background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 99px; font-weight: 700;">Rating 4</span><br>(&ge; 90%)</td>
                                                                <td>(4 / 5) &times; 10% = <strong>8.0 points</strong></td>
                                                        </tr>
                                                        <tr>
                                                                <td><strong>Compliance / Governance</strong><br><span class="text-muted">Weight: 5%</span></td>
                                                                <td>• Commercial Registration, VAT / Tax certificates, and regulatory licenses active and verified</td>
                                                                <td><strong>100.0%</strong> verified compliant</td>
                                                                <td><span style="background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 99px; font-weight: 700;">Rating 5</span><br>(100%)</td>
                                                                <td>(5 / 5) &times; 5% = <strong>5.0 points</strong></td>
                                                        </tr>
                                                        <tr style="background: var(--bg-light-gray); font-weight: 700;">
                                                                <td colspan="4" class="text-right">Total Points Earned (Sum of all 8 criteria):</td>
                                                                <td><strong>79.0 points</strong></td>
                                                        </tr>
                                                </tbody>
                                        </table>
                                </div>
                                <div class="row" style="margin-top: 10px;">
                                        <div class="col-md-4">
                                                <div style="background: var(--bg-light-gray); padding: 12px; border-radius: 6px; border: 1px solid var(--border-color); height: 100%;">
                                                        <strong>1. Overall Score %:</strong><br>
                                                        <code>(79.0 / 100.0) &times; 100 = 79.0%</code><br>
                                                        Standing: <span style="background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 99px; font-weight: 700;">Good Band</span> (&ge; 75%)
                                                </div>
                                        </div>
                                        <div class="col-md-4">
                                                <div style="background: var(--bg-light-gray); padding: 12px; border-radius: 6px; border: 1px solid var(--border-color); height: 100%;">
                                                        <strong>2. Weighted Rating (out of 5):</strong><br>
                                                        <code>(79.0 / 100.0) &times; 5 = 3.95 / 5.0</code><br>
                                                        Action: <em>Reliable vendor. Continue standard monitoring.</em>
                                                </div>
                                        </div>
                                        <div class="col-md-4">
                                                <div style="background: var(--bg-light-gray); padding: 12px; border-radius: 6px; border: 1px solid var(--border-color); height: 100%;">
                                                        <strong>3. Weak Rating Alert:</strong><br>
                                                        Delivery is rated <strong>2</strong> (&le; Weak Limit 3), generating: <strong style="color: #b45309;">"Review Delivery / Lead Time"</strong>.
                                                </div>
                                        </div>
                                </div>
                                <div style="margin-top: 14px; padding: 12px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; font-size: 12px; color: #166534;">
                                        <strong>Pro-Rated Handling for Unmeasured / N/A Criteria:</strong> If a supplier has transactions for only a subset of criteria in any period (for example, only Delivery 20% and Quality 25% with no RFQs), the system automatically deducts unmeasured weights from the 100% denominator. In that scenario, evaluated weight is 45%, so an earned 33.0 points becomes <code>(33.0 / 45.0) &times; 100 = 73.3%</code>. Suppliers are never unfairly penalized when specific criteria have no transaction activity.
                                </div>
                        </div>

                        <!-- Section 4: Performance Bands & Action Comments -->
                        <div class="card" style="border: 1px solid var(--border-color); border-radius: 8px; padding: 20px; background: var(--card-bg);">
                                <h4 style="margin: 0 0 16px 0; font-size: 16px; font-weight: 700; color: var(--text-color); display: flex; align-items: center; gap: 8px;">
                                        <span style="background: #8b5cf6; color: #fff; width: 24px; height: 24px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 12px;">4</span>
                                        Standing Bands & Action Comments
                                </h4>
                                <div class="table-responsive">
                                        <table class="table table-bordered table-sm" style="font-size: 12px; margin-bottom: 12px;">
                                                <thead style="background: var(--bg-light-gray);">
                                                        <tr>
                                                                <th>Overall Score %</th>
                                                                <th>Band Name</th>
                                                                <th>Needs Attention</th>
                                                                <th>Action Plan Generated on Dashboard</th>
                                                        </tr>
                                                </thead>
                                                <tbody>
                                                        <tr>
                                                                <td>&ge; 90%</td>
                                                                <td><span style="background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 99px; font-weight: 700;">Excellent</span></td>
                                                                <td>No</td>
                                                                <td>Preferred vendor. Prioritize for long-term agreements / higher order volumes.</td>
                                                        </tr>
                                                        <tr>
                                                                <td>&ge; 75%</td>
                                                                <td><span style="background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 99px; font-weight: 700;">Good</span></td>
                                                                <td>No</td>
                                                                <td>Reliable. Continue standard monitoring.</td>
                                                        </tr>
                                                        <tr>
                                                                <td>&ge; 60%</td>
                                                                <td><span style="background: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 99px; font-weight: 700;">Average</span></td>
                                                                <td><strong style="color: #d97706;">Yes</strong></td>
                                                                <td>Needs improvement. Issue a formal improvement plan.</td>
                                                        </tr>
                                                        <tr>
                                                                <td>&ge; 40%</td>
                                                                <td><span style="background: #ffedd5; color: #9a3412; padding: 2px 8px; border-radius: 99px; font-weight: 700;">Poor</span></td>
                                                                <td><strong style="color: #ea580c;">Yes</strong></td>
                                                                <td>Corrective action. Reduce reliance and increase inspection / oversight.</td>
                                                        </tr>
                                                        <tr>
                                                                <td>&ge; 0%</td>
                                                                <td><span style="background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 99px; font-weight: 700;">Critical</span></td>
                                                                <td><strong style="color: #dc2626;">Yes</strong></td>
                                                                <td>Consider suspension or termination from the approved vendor list, subject to review.</td>
                                                        </tr>
                                                </tbody>
                                        </table>
                                </div>
                                <p style="font-size: 12px; margin: 0; color: var(--text-muted);">
                                        <strong>How the Bold Review Heading is Generated:</strong> Any evaluated criterion with rating &le; <strong>Weak Rating Limit</strong> (3) is flagged for review. In our worked example above, Delivery was rated 2 (&le; 3), which automatically produced the heading: <strong>"Review Delivery / Lead Time"</strong>.
                                </p>
                        </div>
                </div>
        `);
}
