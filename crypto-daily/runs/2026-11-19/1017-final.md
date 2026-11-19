# Crypto Daily recovery audit 2026-11-19 10:17 Asia/Bangkok
stage: RECOVERY_REBUILD_ATTEMPT
status: QA_FAIL_NO_SEND
sent_check: Gmail Sent after 2026-11-18, no Crypto Daily Brief｜2026-11-19 found; prior 2026-11-16/17/18 recovery messages exist (IDs 1a1ec82b241d7040, 1a1ec885bb982d40, 1a1ec8b7f6b11ce8). No resend for those dates.
git_pending: NOT_FOUND (crypto-daily/delivery-pending/2026-11-19.json)
git_canonical: NOT_FOUND (crypto-daily/reports/daily/2026/2026-11/2026-11-19.md)
rules_blob_shas: PIPELINE_CONTRACT=29ffbc1d32ca87a744d2990e8d55639ebb84a6f9; EDITORIAL_RULESET=2ed51528d230508ae4e0015762b1d60c9d72e299; REPORT_SPEC=2e70414c8fdb8d23a292cc3bf7797425a403e179; REPORT_ACCEPTANCE=28f5d9e8a54dd932223cc2a686466f1d12cf597f; COLLECTOR_SPEC=76e50b322ca551baff0922ca4e4fc721ad422184; DELIVERY_RUNBOOK=cff301c7e15451972a415e24e1863f8d5e31360f; ledger=58b824f0c31d69cb341b28d51dc465f61e0b14e1.
source_receipts:
- capital_flows: https://farside.co.uk/btc/ checked 2026-11-19 ~10:18 BKK; 2026-11-18 provisional aggregate -157.8 USDm, IBIT missing; DO NOT call complete or final; 2026-11-17 -239.9 USDm.
- spot: https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT checked 2026-11-19 ~10:18 BKK HTTP 451; no validated official BTC/ETH/SOL market_core, hard QA block.
- security: https://www.reuters.com/business/binance-says-it-has-court-order-get-back-crypto-frozen-after-63-billion-heist-2026-11-18/ indexed 2026-11-19; court freeze is potential material delta from prior Binance theft, needs source verification and novelty comparison against last seven real sent bodies.
- ipo: https://www.reuters.com/legal/transactional/anthropic-prices-blockbuster-ipo-83-share-source-says-2026-11-18/ indexed 2026-11-19; reports $83 IPO pricing, $81.31bn offering. This is issuer IPO, NOT exchange third-party allocation; venue official access remains UNCONFIRMED_MONITORING.
- macro: https://marketbriefer.com/crypto-pulse-november-18-2026/ secondary only; no primary macro receipt yet.
- onchain: SOURCE_GAP (Arkham/Lookonchain original tx not verified).
- official_x: BROWSER_SESSION_UNAVAILABLE; indexed public search only, no authenticated X session checked.
- security six lanes: SOURCE_GAP (not individually completed in this partial recovery attempt).
- tge, early_nft, derivatives, exchange_policy, forward_catalysts: SOURCE_GAP; not sufficient receipts.
qa: QA_FAIL_NO_SEND; no full verified 13-section body, no manifest, no real Node gate executed (CODE_NOT_EXECUTED), no CI receipt. Gmail not attempted. Preserve existing automation enabled and schedule. Next authorized 10:20/11:20 recovery must rebuild rather than reuse missing pending; check Sent again.
