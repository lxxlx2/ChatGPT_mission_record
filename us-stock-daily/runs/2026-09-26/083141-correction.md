run_time: 2026-09-26 08:31:41 Asia/Bangkok
run_status: success
run_type: correction_and_recovery
report_window: US market 2026-09-25 close and verifiable post-market developments
root_cause: previous workflow treated full-matrix/history completeness as blocking dependencies; incomplete data handling caused degraded report and earlier 08:00 delivery failure
fix_applied: daily Gmail delivery prioritized; noncritical source/history failures degrade locally; GitHub failure no longer blocks Gmail; same-day missing official report triggers recovery
sources: Reuters; SEC; Akamai IR; Cboe; English-language market data cross-checks
mover_investigation_channels: official IR/SEC; Reuters; English market reporting
sector_scan_performed: true
sector_universe_checked: GICS sectors plus AI software/infrastructure, semiconductors, energy, rate-sensitive sectors and IPO pipeline
sector_1d_5d_20d_checked: partial with verified 1D/recent trends; unsupported exact matrices omitted locally rather than blocking delivery
sector_breadth_checked: partial
sector_relative_strength_checked: true
cross_asset_confirmation_checked: true
structural_theme_triggers: AI contract monetization and capex; 10Y Treasury above 5%; oil/diplomacy transmission
missed_theme_review: execution failure and data-source fallback logic corrected
qa_performed: true
qa_issues_found: prior official report incorrectly stated Sept 25 close data could not be obtained
qa_corrections: regenerated report using verified Sept 25 Reuters/official market data and superseded prior email/report
numbering_self_check: passed
structure_self_check: passed
gmail_readback_verification: passed
github_readback_verification: passed
daily_status: official corrected
monthly_status: not_due
github_report_path: us-stock-daily/reports/daily/2026/2026-09/2026-09-26.md
gmail_attempted: true
gmail_sent: true
gmail_subject: 美股每日晨报｜2026-09-26｜AI合同驱动反弹，10年美债5.17%，Akamai获Anthropic 116亿美元承诺
gmail_message_id: 1a0db56ed2412782
gmail_error: none
superseded_message_id: 1a0db5240693e439
github_commit: 4dc15dedb88a7dfb7802fb11c35285f2a6601d8f
tool_exceptions: GitHub create returned 422 because an earlier report already existed; fetched current SHA and replaced it with corrected official report
