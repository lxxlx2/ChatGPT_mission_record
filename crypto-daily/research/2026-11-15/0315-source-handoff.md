# 2026-11-15 03:15 ICT source handoff (03:20 collection window)
status: PARTIAL_SOURCE_GAPS
stage_entered: COLLECTOR
sent_today: NOT_CHECKED_FOR_PUBLICATION (collector; no send authorized)
draft_exists: false
qa_status: NOT_A_COMPLETE_13_SECTION_PREBUILD
code_gate: CODE_NOT_EXECUTED
source_method: Connected Binance official spot API, public English official pages via web search/readback, Gmail Sent search, Git main fetch
checked_at: 2026-11-15 03:15-03:20 Asia/Bangkok (approximate execution window)

## §2 market paragraph (ready to incorporate with as-of, refresh at 06/08/09)
Official Binance spot 24h ticker single-symbol responses, closeTime 1794687367006-1794687367781 Unix ms: BTCUSDT 65520.45, -5.173%, high 69118.02 low 65000, quoteVolume 1731242721.30 USDT; ETHUSDT 1826.58, -6.524%, high 1955.99 low 1811.29, quoteVolume 673610468.40; SOLUSDT 71.77, -10.701%, high 80.50 low 71.67, quoteVolume 301447154.39; BNBUSDT 586.66, -8.142%, high 639.29 low 583.17; HYPEUSDT 64.62, -11.382%, high 73.06 low 64.48. These are rolling 24h exchange snapshots, not daily close. Original API endpoint per symbol: https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT etc. Connected tool readback succeeded despite multi-symbol call failing with duplicate symbols parameter. Refetch before publication.
family_key: market:binance:spot:2026-11-15; material_version: closeTime-1794687367xxx; routine intraday update; INCLUDE §2 only at final as-of.

## §7 IPO Access: high priority NEW source, verify novelty before publication
Kraken official English article https://support.kraken.com/articles/anthropic-ipo-access updated 2026-11-12, actually read 2026-11-15. Explicit Anthropic IPO Access via xStocks ANTx: eligible verified accounts can submit conditional offers/preorders through Kraken Launch, funds reserved not debited until allocation, cancel before deadline, 5% spread/fee on allocated amount, underwriters determine allocation, unused reserved funds refunded after listing, no lockup on listed token. ANTx is a 1:1 backed tokenized price exposure, NOT direct share ownership/voting rights. Kraken says eligible in EEA and most other countries with exclusions US/UK/Canada/Japan/Australia/NZ and sanctioned jurisdictions, account-specific verification required. Official support article does not supply exact IPO date, submission close, final offer price or guaranteed allocation. Do not infer Thai account eligibility or confirmed active logged-in button from public article. 
family_key: ipoaccess:anthropic:kraken:backed_tokenized_equity; material_version: kraken-ipo-access-support-updated-2026-11-12-ANTx-conditional-offer; event_key: ipoaccess-anthropic-kraken-antx-official-20261112; candidate INCLUDE §7 subject to checking last seven delivered bodies and actual logged-out vs authenticated availability. novelty_proof: previous_material_version=UNCONFIRMED_MONITORING; changed_field=official_venue_status; old_value=no confirmed Anthropic IPO venue offer; new_value=Kraken official Anthropic ANTx conditional interest instructions published; evidence_url=https://support.kraken.com/articles/anthropic-ipo-access; evidence_published_at=2026-11-12 (page updated). No separate email at collector stage.
Kraken official 2026-11-11 derivative promo https://blog.kraken.com/product/promotions/the-anthropic-pre-ipo-challenge-nov-2026 covers PF_ANTHROPICXUSD 10x perpetual, NOT IPO shares or ANTx; EXCLUDE as IPO equity access, do not conflate.

## §9 security source receipts
backend_framework_auth: https://github.com/laravel/framework/security/advisories (read 2026-11-15): two moderate signed-URL expiration bypass advisories published 2026-11-11; GHSA-v5ch-g375-82r6 affects <12.72.0 and >=13.0.0 <13.41.0, patched 12.72.0/13.41.0. Candidate WATCH pending seven-day sent dedupe, not auto HIGH. family_key security:laravel:temporary-signed-url-expiration-20261111.
web_runtime_rce/web_pki_tls: https://nodejs.org/en/blog (read 2026-11-15), Nov11 security releases 22/24/26, already disclosed; no independently confirmed newer material version, EXCLUDE repeat. web_pki_tls broader CA source not independently checked: SOURCE_GAP.
cloud_secrets_identity: https://www.connectwise.com/company/trust/advisories read 2026-11-15; Nov12 ScreenConnect RMM+ extension incident initial statement (approx 400 environments with extension installed, NOT confirmed compromised); compare Nov14 report and prior Sent before considering new version; older Cloud Backup incident EXCLUDE repeat.
client_message_renderer_security: prior Telegram research https://github.com/bikini/telejam and https://github.com/davtur19/tg-widget-rce referenced in source policy; current independent original readback NOT done: CLIENT_MESSAGE_RENDERER_SECURITY_SOURCE_GAP; do not replay Nov13 delivered version.
ai_package_supply_chain: https://github.com/advisories discovery search attempted, no bounded fresh package-specific original readback: SOURCE_GAP.
security generic / chain advisory: no fresh official direct readback: SOURCE_GAP.

## Remaining mandatory lanes / gaps
official_x: Browser logged-in session not accessed; BROWSER_SESSION_UNAVAILABLE; public search fallback only. third_party_ipo_access: Kraken English official original accessed; other venues NOT exhaustively checked, PARTIAL.
Arkham/Lookonchain raw transactions, ETF Farside latest finalized rows, macro/SEC new developments, TGE and Early/NFT primary original checks, derivatives funding/OI, exchange policy: NOT YET CHECKED in this run; SOURCE_GAP, no invented no-news conclusion. Carry to 06:20 and 08:20. No Gmail sent and no new scheduler.
