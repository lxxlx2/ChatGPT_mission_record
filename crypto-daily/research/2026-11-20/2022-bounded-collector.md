# 2026-11-20 20:22 ICT bounded collector / delivery reconciliation
status: PARTIAL_SOURCE_GAPS
phase: COLLECTOR_ONLY; NO_EMAIL
checked_at: 2026-11-20T20:22:11+07:00
rules_main_blobs:
  PIPELINE_CONTRACT.md: 29ffbc1d32ca87a744d2990e8d55639ebb84a6f9
  EDITORIAL_RULESET.json: 2ed51528d230508ae4e0015762b1d60c9d72e299
  state/daily-event-ledger.json: 58b824f0c31d69cb341b28d51dc465f61e0b14e1
canonical: crypto-daily/reports/daily/2026/2026-11/2026-11-20.md
canonical_blob: 5cff968874c8a43497fbb07a9a222e2cd2b6a3c9
gmail_sent_id: 1a1f85e52d29b3c0
gmail_subject: Crypto Daily Brief｜2026-11-20｜漏发补发（BTC ETF流出、Binance ANTB退款空投及SEC反诈）
delivery: EXISTING_SENT_NO_RESEND
code_gate: CODE_NOT_EXECUTED
ci: CI_NOT_PROVEN
browser_official_x: BROWSER_SESSION_UNAVAILABLE
collector_note: Prior 16:22 verified Binance official BTC/ETH/SOL/BNB/HYPE spot and perpetual snapshot retained at research/2026-11-20/162240.md. No new 20:22 official quote obtained, so no fabricated update.

## Actual bounded source receipts
- capital_flows / ETF: https://farside.co.uk/BTC/ ; checked_at 2026-11-20 20:22 ICT; last completed listed 2026-11-19 BTC -582.3 USDm, already delivered today; INCLUDE=NO, family etf:btc:daily:2026-11-19, unchanged.
- policy / SEC: https://www.sec.gov/newsroom/press-releases/2026-115-sec-eight-entities-used-fake-crypto-asset-trading-platforms-steal-more-37-million-us-investors ; published_at 2026-11-19; checked_at 2026-11-20 20:22 ICT; existing Nov20 report includes SEC anti-fraud, EXCLUDE duplicate family.
- exchange_policy / official: https://www.binance.com/en/support/announcement/ ; checked_at 2026-11-20 20:22 ICT; listings show 2026-11-20 monitoring-tag changes and TradFi perpetual launch; individual announcement/terms not read, VERIFYING not promoted.
- web_runtime_rce / backend_framework_auth: https://nodejs.org/en/blog/vulnerability/november-2026-security-releases/ ; published_at 2026-11-11; checked_at 2026-11-20 20:22 ICT; high TLS/HTTP2 advisories, existing family requires seven-day novelty proof; EXCLUDE no new material version.
- backend_framework_auth / Laravel: https://github.com/laravel/framework/security/advisories ; checked_at 2026-11-20 20:22 ICT; listed Nov11 moderate signed URL advisories and Oct19 critical token guard bypass; EXCLUDE stale no new delta.
- web_pki_tls: Node TLS advisory above checked; CA-specific new trust update SOURCE_GAP.
- spot / derivatives: official Binance 16:22 snapshot in earlier research, not rechecked now; SOURCE_GAP_CURRENT_20_22.
- onchain: Lookonchain/Arkham 20:22 search did not yield independently validated TXID; SOURCE_GAP.
- ai_package_supply_chain: GitHub advisory index search did not establish fresh official package notice; SOURCE_GAP.
- cloud_secrets_identity: Railway/Microsoft/ConnectWise current original updates not successfully checked; SOURCE_GAP.
- infrastructure / macro / forward_catalysts: no new primary verified material update in bounded pass; SOURCE_GAP.
- tge / early_nft: original project posts not verified this pass; SOURCE_GAP.
- third_party_ipo_access: prior 16:22 Kraken first-party terms https://support.kraken.com/in/articles/anthropic-ipo-access ; new executable venue window not verified this pass; UNCONFIRMED_MONITORING for other venues; no alert.
- official_x: browser session not available; BROWSER_SESSION_UNAVAILABLE, not claimed checked.

## Final action
20:20 is collector-only, no second Gmail. Nov20 already Sent and canonical present. Existing 13-section report remains immutable; no claim that scheduled 09:20 delivery worked. No new task, local process, paid API, GitHub timer, or App notification.