---
run_date: 2026-11-23
timezone: Asia/Bangkok
report_type: us_stock_daily
status: DELIVERED_MANUAL_RECOVERY
original_0740_status: QA_FAIL_NO_SEND
original_0840_status: QA_FAIL_NO_SEND
gmail_sent_id: "1a206fd2ccd55bfb"
recipient: "lxx.run688@gmail.com"
mail_sent_utc: "2026-11-23T05:59:44Z"
git_canonical_path: us-stock-daily/reports/daily/2026/2026-11/2026-11-23.md
git_report_commit: "81002e72b3a7ab290e388f5657c20995391ffaff"
git_report_blob: "8d89d56b9a8ab3b8090ab344dd882dfc932e6052"
gmail_sent_and_full_readback: true
full_body_and_git_exact: true
chapter_count: 12
code_gate: CODE_NOT_EXECUTED
ci_gate: NOT_PROVEN
qa_mode: MANUAL_SOURCE_AND_7DAY_GMAIL_BODY_NOVELTY_REVIEW
unattended_production_verified: false
---

# Actual Nov23 stock recovery audit

Original final us-stock-daily/runs/2026-11-23/083630-final.md was QA_FAIL_NO_SEND; no original Gmail or canonical. Original pending draft existed but reused Nov20 Friday closing figures, Anthropic IPO, and already-announced Analog/Dell results dates without enough material 2026-11-23 original source discovery. This was a failure of today's substantive story selection and full semantic QA.

Verified new evidence in Reuters Nov23 https://www.reuters.com/world/china/global-markets-view-europe-2026-11-23/ and AP Nov23 https://apnews.com/article/stocks-markets-rates-technology-ai-anthropic-49ba1beba78fa4ed2bd5898029f79c91 : Asia tech drawdown while US stock futures bounced. NYSE https://www.nyse.com/trade/hours-calendars confirms Thursday Nov26 closure and Friday Nov27 13:00 ET early close. Company ADI and Dell official IR are cited as previously announced upcoming dates, not fresh first publication. US cash market had not opened at mailing time. Seven actual Nov16-22 Gmail Sent full bodies were read and compared for event novelty. Full 12-heading report was reviewed manually; X, options and some original local Asian policy remain SOURCE_GAP; CODE_NOT_EXECUTED and no fake CI success.

Gmail send returned 1a206fd2ccd55bfb, verified SENT label, recipient, subject, all 12 headings and actual readback. Git canonical was created from returned exact Gmail body, reread byte-for-byte after frontmatter, commit 81002e72b3a7ab290e388f5657c20995391ffaff, blob 8d89d56b9a8ab3b8090ab344dd882dfc932e6052. Manual recovery proves today's delivery only, not future unattended success.

Existing us-stock-daily/AUTOMATION_RUNTIME.md source/discovery-prep corrective change committed f11118109138974fc604881016fe8f2eea73728a; original task prompt updated in-place, same schedule and recipient, no other monitor or App notification. Do not send Nov23 again unless genuine material verified correction needs explicit supersession.
