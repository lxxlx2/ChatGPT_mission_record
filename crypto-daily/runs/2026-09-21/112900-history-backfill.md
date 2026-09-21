---
run_time: "2026-09-21T11:29:00+07:00"
automation_id: "6a8600b9d12481919bc43ebc800c9916"
run_status: success
task: historical_report_backfill
source: Gmail Sent
dates_checked:
  - 2026-09-17
  - 2026-09-18
  - 2026-09-19
  - 2026-09-20
gmail_message_ids:
  2026-09-17: "1a0ad1a7648ead7b"
  2026-09-18: "1a0b23dbb9dcc10e"
  2026-09-19: "1a0b76545a2201b5"
  2026-09-20: "1a0bc8dcb0c2f262"
github_readback_verification: "passed: all four report paths exist after backfill and each contains the matching Gmail message id and original report subject/body"
gmail_sent_during_backfill: false
note: "Historical bodies were archived verbatim from Gmail Sent. Their legacy visible numbering is preserved as audit history; current automation now requires fullwidth （n） numbering."
---
