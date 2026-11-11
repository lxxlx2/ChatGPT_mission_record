# 2026-11-11 09:17 Asia/Bangkok publisher preflight
status: QA_FAIL_PENDING_NOT_READY
run_mode: publisher_preflight
checked_at: 2026-11-11T09:17:50+07:00
gmail_attempted: false
gmail_sent: false
source: Gmail Sent actual query in:sent after:2026/11/10 before:2026/11/12 subject:Crypto
sent_result: only 2026-11-10 ID 1a1c5322efda837e; no 2026-11-11 daily returned at preflight
git_pending_2026-11-11: NOT_FOUND
git_canonical_2026-11-11: NOT_FOUND
git_research_available: 002142.md, 031509.md, 0619-source-receipt.md, 0822-prebuild-source-gap.md
prebuild_status: QA_FAIL_INCOMPLETE_SOURCE_COVERAGE_AND_NO_FULL_13_SECTION_DRAFT
rule_sha:
  PIPELINE_CONTRACT: 29ffbc1d32ca87a744d2990e8d55639ebb84a6f9
  REPORT_SPEC: 2e70414c8fdb8d23a292cc3bf7797425a403e179
  REPORT_ACCEPTANCE: 17c90d91e9d0c56a8f27c3af10d5284cc2f863db
  COLLECTOR_SPEC: 76e50b322ca551baff0922ca4e4fc721ad422184
  DELIVERY_RUNBOOK: e4d01309bcf0df9c1ca00b6777d5af5141ee20c3
  ledger: 409ed863261e56f80a85f5594a99ea6ae71f8e37
action_required: At 09:20 first requery Sent. Assemble complete 13 sections from the four research shards, verify current original prices and source coverage, independently QA novelty and actual sources, send only if passes; if QA fails record exact reasons and retry within existing 10:20/11:20 recovery. No premature send and no duplicate.
known_candidates: Reuters Nov10 US CPI +0.4% month-on-month vs +0.3% consensus, core +0.3%, still requires BLS original confirmation; Binance Nov10 transactions-with-certain-platforms notice requires original bulletin and prior7 comparison.
market_shard: 06:19 Binance BTC 73734.01, ETH 2051.60, SOL 83.00, BNB 677.40, HYPE 72.34 USDT, with source closeTime timestamps in 0619-source-receipt.md. These are historical morning samples, not live 09:20.
source_gaps: six security lanes, ETF issuer finalization, original TXID, X authenticated, IPO venue, TGE/Early/NFT, full prior7 Gmail bodies, fresh derivatives.
monthly_october: historical Sent 1a1a496a0bdc257d, never resend.
