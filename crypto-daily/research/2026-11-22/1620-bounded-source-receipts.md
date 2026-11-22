# 2026-11-22 16:20 Asia/Bangkok bounded collector
status: PARTIAL_SOURCE_GAPS
stage: COLLECT_ONLY_NO_EMAIL
code_gate: CODE_NOT_EXECUTED

## Current Git rule blob SHAs (read main this run)
PIPELINE_CONTRACT.md 29ffbc1d32ca87a744d2990e8d55639ebb84a6f9
EDITORIAL_RULESET.json 2ed51528d230508ae4e0015762b1d60c9d72e299
state/daily-event-ledger.json 58b824f0c31d69cb341b28d51dc465f61e0b14e1
Other REPORT_SPEC, REPORT_ACCEPTANCE, COLLECTOR_SPEC, SECURITY_SOURCE_POLICY, DELIVERY_RUNBOOK were fetched in same run; retain exact SHA in tool evidence. No CI invoked.

## Gmail Sent history
Actual Sent search 2026-11-15 through 2026-11-22 matched Crypto formal mail for 2026-11-15 through 2026-11-21, most recent Nov21 message 1a1fc4aa5080c3cf. No Nov22 Crypto Sent found in this search. Search returned metadata only; complete 7-day bodies not yet read, hence historical dedupe PARTIAL.

## Bounded source receipts
Checked 2026-11-22 ~16:20 Asia/Bangkok, web search public English unless noted:
- capital_flows: https://farside.co.uk/btc/ checked; 2026-11-20 BTC ETF total displayed -124.5 USD million with IBIT dash (incomplete issuer). Cannot treat as finalized full total. published_at: rolling live page, unknown.
- exchange_policy: https://www.binance.com/en/support/announcement checked; Binance Earn USDC/USDT 5% APR announcement dated 2026-11-22; routine marketing, EXCLUDE global Top5, verify terms before any actionable claim.
- third_party_ipo_access: https://www.sec.gov/Archives/edgar/data/2130357/000162828026074937/anthropicpbc-fwppricing.htm checked, published 2026-11-18; issuer-priced IPO $83 and Nasdaq ANT trading from Nov19. This is issuer IPO, not proof of any exchange IPO allocation. No verified Kraken/Binance/Bitget/Bybit/Gate/OKX new subscription access this sweep; SOURCE_GAP for venue-by-venue check. Do not repeat previously reported issuer pricing without novelty.
- legacy_quest: https://help.galxe.com/en/articles/18361711-galxe-is-integrating-into-gravity-what-you-need-to-know checked, announcement Nov9; Quest campaign cutoff Dec5 and rewards claim Dec15; known delivered TGE email 1a1f9a770fcb1c29, EXCLUDE no new version.
- backend_framework_auth: https://github.com/laravel/framework/security/advisories checked; Nov11 two moderate signed-URL advisories and older Oct19 TokenGuard critical; candidate requires comparison with actual Sent before inclusion.
- web_runtime_rce: https://nodejs.org/en/blog/vulnerability/november-2026-security-releases source surfaced via Chinese locale /zh-cn/ and dated Nov11, new fixes 22.23.5/24.22.3/26.13.1; do not treat as new Nov22 event. English URL needs direct check. SOURCE_GAP.
- ai_package_supply_chain: https://github.com/advisories searched, no comprehensive fresh LiteLLM/PyPI/Docker original receipts; SOURCE_GAP.
- cloud_secrets_identity: https://status.railway.com/ and Microsoft/ConnectWise searched, no authoritative fresh update obtained; SOURCE_GAP.
- web_pki_tls: no fresh original advisory independently retrieved; SOURCE_GAP.
- spot/derivatives: no direct Binance official quote or derivative API sampling in this execution; SOURCE_GAP, no price invented.
- onchain: Lookonchain search attempted, no verified TXID; SOURCE_GAP.
- tge/early_nft: Galxe official source only, other active project checks incomplete; SOURCE_GAP.
- macro: SEC issuer FWP above, broader Fed/equities not completed; SOURCE_GAP.
- official_x: BROWSER_SESSION_UNAVAILABLE; public original X access not verified, SOURCE_GAP.
- stablecoin_reserves: USDT/Tether/Circle original latest reserve and depeg cross-check incomplete; SOURCE_GAP. Previously delivered S&P Nov18 weak-5 unchanged and 28% exposure must not be repeated without delta.

## Disposition
This 16:20 window is collection only. No Gmail send or app notification. Candidate novelty not proven; no INCLUDE high-severity news asserted. Subsequent 08:20/09:20 must use actual official receipts and 7-day Sent bodies. Preserve existing task configuration and no new monitoring resources.
