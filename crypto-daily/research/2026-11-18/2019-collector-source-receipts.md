# 2026-11-18 20:19 Asia/Bangkok collector increment
stage: COLLECTOR_PARTIAL_SOURCE_GAPS
publication: NONE; Gmail Sent already contains canonical-dated 2026-11-18 and historical 16/17 recovery, do not send in this window.
checked_at: 2026-11-18 20:19 Asia/Bangkok (automation invocation; precise individual HTTP fetch times unavailable)
rules_read: PIPELINE_CONTRACT.md, EDITORIAL_RULESET.json, REPORT_SPEC.md, REPORT_ACCEPTANCE.md, COLLECTOR_SPEC.md, SECURITY_SOURCE_POLICY.md, DELIVERY_RUNBOOK.md, state/daily-event-ledger.json from main; blob SHAs obtainable from connector fetch response, not repeated here.

## Real Sent dedupe
2026-11-18 Gmail Sent 1a1ec8b7f6b11ce8; 2026-11-17 1a1ec885bb982d40; 2026-11-16 1a1ec82b241d7040. These were actually found in Sent; no new email authorized at 20:20. Canonical Git exact-body readback not performed in this collector.

## Source receipts / candidate selection
- capital_flows ETF BTC: https://farside.co.uk/btc/ checked_at above; Farside 2026-11-17 US session total -239.9 USD million; prior 2026-11-16 +7.9m. 2026-11-18 row still unfilled, not zero. family_key etf:btc:us-spot-daily; material_version farside-2026-11-17-minus239p9m; ROUTINE_DATA_INCLUDE_NEXT_DAILY_ONLY if not already in today's Sent; compare Sent full text before inclusion.
- capital_flows ETF ETH: https://farside.co.uk/eth/ checked_at above; 2026-11-17 -29.1 USD million; 2026-11-16 -8.4m; 2026-11-18 unfilled. family_key etf:eth:us-spot-daily; material_version farside-2026-11-17-minus29p1m; ROUTINE_DATA_DEDUPE.
- third_party_ipo_access: https://support.kraken.com/articles/anthropic-ipo-access published/updated 2026-11-12; official Kraken describes ANTx conditional interest and jurisdiction limits. https://www.bitget.com/asia/support/articles/12560603900044 published 2026-11-09 VIP extension to 2026-11-11. Already 2026-11-18 Sent subject explicitly Anthropic IPO SEC update; DO_NOT_REPEAT without verified new terms, status or deadline. Kraken backed tokenized equity distinct from actual share custody. family_key ipoaccess:anthropic:kraken:backed-tokenized-equity and ipoaccess:anthropic:bitget:subscription. No newly confirmed 2026-11-18 offer status. Other venues SOURCE_GAP on individual first-party verification.
- exchange_policy: https://www.binance.com/en/support/announcement checked_at above; index shows 2026-11-18 bStocks collateral and new trading pairs announcements. Actual individual announcement and terms NOT fetched. WATCH_VERIFY, no news claim yet.
- onchain: https://arkm.com/ and https://lookonchain.com/ checked_at above. Arkham landing page has no original wallet TXID; Lookonchain feed mentions Binance hacker 78,415 ETH via THORChain but TXID/published_at not established. family_key security:binance-incident:fund-movements; WATCH_VERIFY; do not infer confirmed laundering from feed alone.
- macro: https://lookonchain.com/ feed repeats Fed Waller rate commentary, but original Fed transcript and published_at missing: SOURCE_GAP, no report-ready macro claim.
- security/ai_package_supply_chain: https://docs.litellm.ai/blog/ checked_at above, latest listed Nov 13 posts, no newly verified malicious package; github advisory direct crosscheck incomplete SOURCE_GAP.
- security/cloud_secrets_identity: https://status.railway.com/ and https://www.microsoft.com/en-us/security/blog/ and https://www.connectwise.com/company/trust/advisories checked_at above; accessible, no individually timestamped new material advisory independently extracted; SOURCE_GAP for incident-specific delta.
- security/backend_framework_auth: https://nodejs.org/en/blog/vulnerability/ (latest Nov 11 advisory), https://github.com/laravel/framework/security/advisories (latest Nov 11 moderate signed URL advisories); no newly proven Nov 18 high event. Published_at Nov 11, not new today.
- security/web_runtime_rce: https://nodejs.org/en/blog/vulnerability/ checked; older Nov 11 patch, no current independent PHP original advisory checked; SOURCE_GAP.
- security/web_pki_tls: https://www.cisa.gov/known-exploited-vulnerabilities-catalog HTTP 403; no CA original checked: SOURCE_GAP.
- security generic: https://lookonchain.com/ feed claims K3Capital sBOLD ~$3.43m exploit based on Blockaid, but no original Blockaid alert or onchain TXID checked. family_key security:k3capital:sBOLD; WATCH_VERIFY, source publication time unconfirmed, no INCLUDE until original evidence.
- spot/derivatives: Binance official live symbol API NOT fetched in this window; SOURCE_GAP, no prices invented.
- policy SEC: SEC primary filing not fetched in this window; SOURCE_GAP.
- tge/early_nft/forward_catalysts: no current issuer original post fetched; SOURCE_GAP.
- official_x: BROWSER_SESSION_UNAVAILABLE; no claim of accessing user's logged-in tabs; public official X original not verified.
No event promoted to Top5 without primary evidence. No notification, no task/schedule modification.
