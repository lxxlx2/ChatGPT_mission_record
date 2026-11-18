# 2026-11-18 16:20 Asia/Bangkok bounded collector
stage: COLLECTOR_PARTIAL_SOURCE_GAPS
delivery: NO_EMAIL_COLLECTOR_SLOT
code_gate: CODE_NOT_EXECUTED
official_x: BROWSER_SESSION_UNAVAILABLE
rules_sha: PIPELINE_CONTRACT=29ffbc1d32ca87a744d2990e8d55639ebb84a6f9; EDITORIAL_RULESET=2ed51528d230508ae4e0015762b1d60c9d72e299; DELIVERY_RUNBOOK=cff301c7e15451972a415e24e1863f8d5e31360f
ledger_sha: 58b824f0c31d69cb341b28d51dc465f61e0b14e1
checked_at: 2026-11-18T16:18-16:20+07:00

## Real connected Binance single-symbol API receipts
Source endpoints https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT ; same ETHUSDT/SOLUSDT; https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT ; same ETHUSDT/SOLUSDT; https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT ; same ETHUSDT/SOLUSDT.
API closeTime 1794993528001 BTC, 1794993530978 ETH, 1794993531771 SOL. All 24h rolling, NOT daily close.
BTC 64682.00 USDT, +0.738%, low 63336, high 65447, quote volume 1478656763.66 USDT; mark 64649.7673, last funding 0.00000346, OI 91817.429 BTC.
ETH 1811.45 USDT, +0.066%, low 1751.39, high 1836, quote volume 639668869.34 USDT; mark 1810.4979, last funding 0.00003501, OI 2374522.817 ETH.
SOL 74.85 USDT, +3.728%, low 71.07, high 75.78, quote volume 215629107.10 USDT; mark 74.80, last funding -0.00013852, OI 8438343.46 SOL.
market family_key=market:binance-spot-official-rolling24h; material_version=2026-11-18T16:18+07; routine update.

## Fund flow
Farside https://farside.co.uk/btc/ checked 2026-11-18T16:19+07; published_at for row: trading date 2026-11-17, source dynamic (no explicit publication timestamp). BTC US spot ETF 2026-11-17 total -239.9 USD million, IBIT -209.5; 2026-11-16 +7.9 USD million. Aggregator may revise. family_key=etf:bitcoin-us-spot-daily; material_version=2026-11-17-preliminary. Source https://farside.co.uk/bitcoin-etf-flow-all-data/ has cached table only through Nov 16; do not treat it as contradiction until refreshed.

## Exchange / security originals
Binance English https://www.binance.com/en/support/announcement checked 2026-11-18T16:19+07: latest listed includes Binance Will Add 7 bStocks Tokenized Securities as Collateral Asset (2026-11-18), Binance Exchange Adds New bStocks Trading Pairs (2026-11-18), and Binance Stock Options Trading API Is Now Live. Exact article detail/terms not independently opened; candidate WATCH not INCLUDE, cannot infer Anthropic equity access.
Node.js original https://nodejs.org/en/blog/vulnerability/november-2026-security-releases/ checked 2026-11-18T16:19+07, published 2026-11-11. Official fixes for high-severity HTTP/2, HTTPS memory leak and TLS auth vulnerabilities; family_key=security:nodejs-2026-11-11-batch, no novelty proof against previous Sent yet, EXCLUDE pending seven-day body check.
Laravel original https://github.com/laravel/framework/security/advisories checked 2026-11-18T16:19+07; two moderate temporary signed URL expiration bypass advisories published 2026-11-11, old critical TokenGuard bypass 2026-10-19; no novelty proof, EXCLUDE.
Other security lanes security, web_runtime_rce, web_pki_tls, ai_package_supply_chain, cloud_secrets_identity: SOURCE_GAP this cycle, not cleared. Official X SOURCE_GAP; Arkham/Lookonchain TXIDs SOURCE_GAP; SEC/issuer/Anthropic IPO venue-specific terms SOURCE_GAP; TGE/Early/NFT primary source SOURCE_GAP; macro primary SOURCE_GAP. No claim of exhaustive discovery.

## Actual Sent dedupe
Gmail Sent search after 2026-11-11 checked 2026-11-18T16:18+07: 2026-11-18 report already Sent ID 1a1ec8b7f6b11ce8 (02:45:27 UTC); 2026-11-17 backfill Sent ID 1a1ec885bb982d40 (02:42:01 UTC); 2026-11-16 backfill Sent ID 1a1ec82b241d7040 (02:35:50 UTC). Therefore do NOT send again for any of these dates. Exact Gmail bodies and canonical equality NOT checked this collector; archive verification remains pending.
