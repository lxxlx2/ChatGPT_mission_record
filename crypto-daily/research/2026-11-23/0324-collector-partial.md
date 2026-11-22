# Crypto Daily 2026-11-23 03:20 collector receipt (PARTIAL_SOURCE_GAPS)

Run checked around 2026-11-23 03:24-03:27 Asia/Bangkok. No Gmail send in collector slot. No task/schedule change.

Git main blob SHA: PIPELINE_CONTRACT 29ffbc1d32ca87a744d2990e8d55639ebb84a6f9; EDITORIAL_RULESET 2ed51528d230508ae4e0015762b1d60c9d72e299; ledger 0b4acf861b4a8a755759b5c6ab3d2cf5469609b1. Other required rules fetched in same invocation; consult latest main again at prebuild.

Gmail Sent search after 2026-11-15 returned Nov16-Nov22 editions. Same-day 2026-11-23 title-prefix search returned zero. Most recent Nov22 Sent 1a2034b8ca694f60. Seven-day full body comparison NOT COMPLETED in this collector round: SOURCE_GAP, do not claim dedupe passed.

Binance official spot /api/v3/ticker/24hr single-symbol connector samples closeTime around 2026-11-22T20:24:17Z (03:24:17 Bangkok Nov23), USDT pairs:
BTC 60605.19, 24h +0.336%, high 61669.99 low 58768.51;
ETH 1712.81, +1.488%, high 1732.52 low 1648.35;
SOL 70.00, -0.920%, high 71.43 low 68.74;
BNB 555.08, +1.001%; HYPE 62.41, +1.381%.
Binance futures /fapi/v1/premiumIndex same minute: BTC mark 60585.83413793 funding 0.00002780; ETH mark 1712.18626704 funding 0.00005072; SOL mark 69.97000000 funding 0.00002485. These are snapshot funding rates, not APR. Source tier OFFICIAL_EXCHANGE_API. Batch spot request failed -1101 duplicate values; single-symbol fallback succeeded.

Source receipts (actual fetched; checked_at 2026-11-23 ~03:25 Asia/Bangkok unless otherwise stated):
- capital_flows BTC ETF https://farside.co.uk/btc/ page accessed; latest final trading-day totals need separate table parsing before use.
- capital_flows ETH ETF https://farside.co.uk/eth/ accessed, latest final-day parsing pending.
- capital_flows SOL ETF https://farside.co.uk/sol/ accessed, latest final-day parsing pending.
- policy https://www.sec.gov/newsroom accessed; 2026-11-20 SEC announcements present; no specific novel actionable crypto event verified in this pass.
- exchange https://www.binance.com/en/support/announcement accessed, latest 2026-11-20/22 listings. Do not treat user-generated Binance Square commentary as official.
- onchain https://info.arkm.com/research/ searched; results predominantly historical, no new TXID verified; Lookonchain original source SOURCE_GAP.
- ai_package_supply_chain https://docs.litellm.ai/blog/ accessed, latest listed Nov17; no new security delta established; PyPI/Docker integrity independent checks SOURCE_GAP.
- cloud_secrets_identity https://status.railway.com/ accessed, current status operational; not proof historical secrets issue resolved. https://www.connectwise.com/company/trust/advisories accessed; novel incident delta unverified. Microsoft identity advisories SOURCE_GAP.
- backend_framework_auth https://github.com/laravel/framework/security/advisories accessed; latest signed URL Nov11 moderate, prior Oct19 TokenGuard critical already delivered. No new Nov23 auth bypass verified.
- web_runtime_rce https://nodejs.org/en/blog/vulnerability/november-2026-security-releases accessed: original published 2026-11-11, high HTTP/2 unauthenticated abort CVE-2026-123863, HTTPS heap read CVE-2026-123864, HTTP/2 resource leak CVE-2026-123865. POTENTIAL HIGH CANDIDATE, family_key runtime:node:2026-11-security, material_version official-2026-11-11-security-release; check Nov16-Nov22 actual Sent bodies for novelty BEFORE inclusion; no user deployment assumed.
- web_pki_tls: Node HTTPS issue above is not a substitute for independent CA/TLS lane; SOURCE_GAP for Mozilla/CA sources.
- security general https://github.com/advisories searched; no comprehensive coverage established.
- macro SEC newsroom accessed; Fed and geopolitical fresh originals SOURCE_GAP.
- TGE, early_nft, active_project, legacy_quest_shutdown, third_party_ipo_access, official_x: SOURCE_GAP; no authenticated browser session verified; do not say clear or announce Anthropic IPO allocation.

Candidate classification: Node November advisory is a source-verified historical advisory, INCLUDE_AS_CANDIDATE_FOR_DEDUPE_REVIEW, not yet eligible for report without seven-day Gmail comparison and distinct material novelty. No new action email. Galxe Nov9 shutdown and USDT S&P Nov18 assessment already reported; exclude same material versions. Source coverage incomplete, state PARTIAL_SOURCE_GAPS; no editorial QA or CI claimed.
