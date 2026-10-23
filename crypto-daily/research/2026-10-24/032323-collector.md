# Crypto Daily 03:20 bounded collector

run_slot: 2026-10-24 03:20 Asia/Bangkok
checked_at_utc: 2026-10-23T20:24:02.828Z
automation_id: 6a8600b9d12481919bc43ebc800c9916
mode: ordinary_collection_no_email
status: PARTIAL_SOURCE_GAP
prior_collector: crypto-daily/research/2026-10-24/002406-collector.md
policy_blob_shas: PIPELINE_CONTRACT=5365fb29bb00f20101d4190737468da845b4a0e2; EDITORIAL_RULESET=ad3488769052a1cea5dda4bbf7fd6f1f9092046f; REPORT_SPEC=809a5c1cbcd6503d42305c842f37826b74a4741f; REPORT_ACCEPTANCE=37789b7274aec766e4ac4975111602bccc11a7d2; COLLECTOR_SPEC=834e0e3c05f5e894f31474a7b4d7fd0e90d8c08f; ledger=d7806bb407a95a9d1a5ba8e5d76a39cbf433c759.

## Verified Binance official market snapshot

Source: Binance public read-only Spot /api/v3/ticker/24hr and USD-M /fapi/v1/premiumIndex, /fapi/v1/openInterest; UTC API close approx 2026-10-23T20:22:42Z, 2026-10-24 03:22:42 Bangkok. Prices are venue-specific USDT quotes and 24h rolling windows.

| symbol | last USDT | 24h pct | 24h low/high USDT | 24h quote volume USDT | futures mark | last funding rate | futures open interest (base units) |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| BTCUSDT | 81335.43 | -0.029% | 81099.00 / 82060.88 | 939725837.11 | 81303.70 | 0.00007498 | 92343.606 BTC |
| ETHUSDT | 2395.46 | +0.521% | 2377.89 / 2417.77 | 613155741.09 | 2394.34 | 0.00004161 | 2319182.613 ETH |
| SOLUSDT | 103.51 | +0.058% | 103.06 / 105.24 | 145134519.24 | 103.47 | 0.00010000 | 8453210.37 SOL |

Open interest is contract base quantity at single venue/time; cannot infer net long or dollar inflow. The first multi-symbol API call returned HTTP 400 duplicate values; recovered with three separate valid per-symbol requests.

## Source discovery receipts (real checked_at; publication dates reflect source not search timestamp)

| lane | actual original URL or English query | result / source date | checked_at_utc |
| --- | --- | --- | --- |
| spot | https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT (and ETHUSDT/SOLUSDT) | LIVE_API; API close 2026-10-23T20:22:42Z | 2026-10-23T20:24:02.828Z |
| derivatives | https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT ; https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT (and ETHUSDT/SOLUSDT) | LIVE_API; API time 2026-10-23T20:22:48Z | 2026-10-23T20:24:02.828Z |
| capital_flows | https://farside.co.uk/btc/ | Oct22 BTC ETF net -635.6m USD; Oct23 all fund cells '-' so 0.0 displayed is NOT confirmed final zero. SOURCE_GAP Oct23 | 2026-10-23T20:24:02.828Z |
| onchain | https://info.arkm.com/research ; English indexed query site:info.arkm.com/research October 23 2026 Bitcoin Coinbase Prime BTC large transfer; site:x.com/lookonchain Oct 23 2026 BTC ETH whale deposit | PARTIAL_SOURCE_GAP: Arkham landing rendered featured Oct23 evergreen guides and 0 posts; indexed results old 2025/July2026; no fresh independently identified TXID; cannot infer zero large transfers | 2026-10-23T20:24:02.828Z |
| policy | https://www.sec.gov/newsroom/press-releases ; English searches Binance/Bybit/Bitget Oct23 source of funds AML HTX | SEC Oct23 examination priorities new but not yet proven crypto-specific; no verified new cross-venue HTX enforcement; Bybit EDD original last updated Mar30, old; SOURCE_GAP for direct recent venue support | 2026-10-23T20:24:02.828Z |
| infrastructure | https://www.sec.gov/newsroom/press-releases ; Reuters Oct23 OKXICE issuer objections query | WATCH_UNVERIFIED: Reuters Oct23 says 22 issuers objected to planned tokenized shares; original SEC objection filings not independently retrieved. Do not promote to first-party verified | 2026-10-23T20:24:02.828Z |
| tge | https://www.binance.com/en/support/announcement/detail/ab3a0eac9e614819b7b6fa0c03504b1f ; English site:coinlist.co/blog Oct23 2026 token sale | Binance original English indexed full text published Oct23 09:30 UTC: 7 Alpha featuring removals, withdrawal and selling remain available. Direct open returned internal error but Binance English indexed official text readable. No verified new CoinList TGE/claim | 2026-10-23T20:24:02.828Z |
| early_nft | https://opensea.io/blog/announcements ; English Oct23 2026 NFT mint/launch search | Latest indexed official OpenSea mobile Oct20; no new verified Oct23 primary mint, X/Reddit direct SOURCE_GAP. Do not assert no launches exist | 2026-10-23T20:24:02.828Z |
| security | https://www.connectwise.com/company/trust/advisories ; English wallet drain/crypto security source search | ConnectWise Oct23 14:00 UTC fresh operational update; wallet incident independent issuer/chain validation incomplete | 2026-10-23T20:24:02.828Z |
| web_runtime_rce | https://www.php.net/archive/2026.php | NEW official Oct23 advisory CVE-2026-115560 unusual session handler config; recommends session.upload_progress.enabled=0 pending future release, distinct delta from Oct21 CVE-2026-109618/109619 | 2026-10-23T20:24:02.828Z |
| web_pki_tls | https://blog.mozilla.org/security/2026/10/20/protecting-firefox-users-following-the-compromise-of-emudhra-intermediate-certificates/ | Official Oct20 + Oct21 Android follow-up already previously reported, no new Oct23 material version observed | 2026-10-23T20:24:02.828Z |
| ai_package_supply_chain | https://docs.litellm.ai/blog/security-incident-oct-21-2026 | Official Oct21 20:30 UTC last update; old LiteLLM 1.107.0 incident already delivered Oct23, no new version observed | 2026-10-23T20:24:02.828Z |
| cloud_secrets_identity | https://blog.railway.com/p/security-disclosure-recommendation-recover-failing-deploys ; https://blog.railway.com/p/preliminary-report-october-security-incident | NEW Oct23 recovery guide: deployments reenabled; Oct21 paused commits not queued; GitHub connection and CLI/CI tokens revoked. Oct22 report describes at most 1.85% workspaces potential environment variable compromise, preliminary, do not claim user's account impacted | 2026-10-23T20:24:02.828Z |
| cloud_secrets_identity | https://www.microsoft.com/en-us/security/blog/2026/10/21/storm-0940-uses-artex-agentic-ai-connectwise-supply-chain-compromise/ ; https://www.connectwise.com/company/trust/advisories | Microsoft Oct21 old already delivered; ConnectWise NEW Oct23 14:00 UTC says restoration validation by weekend, backups restoration access expected early next week; affected integrations remain disabled pending issuer instructions | 2026-10-23T20:24:02.828Z |
| backend_framework_auth | https://nodejs.org/en/blog/vulnerability/october-2026-security-releases ; https://github.com/laravel/framework/security/advisories/GHSA-f9x3-7vq9-cph6 | Node Oct21 and Laravel Oct19 original already delivered Oct23; no fresh new vendor update observed | 2026-10-23T20:24:02.828Z |
| macro | https://www.sec.gov/newsroom/press-releases/2026-109-sec-announces-fiscal-year-2027-examination-priorities ; Reuters Oct23 Wells Fargo/Intuit tokenized equity objection article | SEC Oct23 priorities confirmed publication; tokenized shares objections secondary Reuters, original filing SOURCE_GAP; Friday US close not independently exchange-confirmed in this round, carry 00 collector AP provisional | 2026-10-23T20:24:02.828Z |
| forward_catalysts | https://www.connectwise.com/company/trust/advisories | ConnectWise next status update scheduled 2026-10-24 14:00 UTC, FUTURE only, not yet published at this scan | 2026-10-23T20:24:02.828Z |

## Candidate ledger, all INTERNAL, no email

- event_key=php:session-upload-progress:2026-10-23; family=php:session-upload-progress; material_version=issuer_2026-10-23_CVE-2026-115560; HIGH; verified official; INCLUDE_CANDIDATE §9 for next 08:20 review. Distinct from previously delivered PHP2Shell 2 CVEs. Official says highly specific config and mitigation until next regular release, not evidence of exploitation.
- event_key=railway:incident:2026-10-21; family=cloud:railway:secrets; material_version=issuer_recovery_2026-10-23_redeploy_guide; HIGH; verified official; INCLUDE_CANDIDATE §9. Specific new action for actual Railway deploy users; Oct21 original compromise old already delivered.
- event_key=connectwise:cloud-backup:2026-10-16; family=oauth:connectwise:storm0940; material_version=issuer_restoration_2026-10-23T14:00Z; HIGH; verified official; INCLUDE_CANDIDATE §9; phased restoration is forecast not completed, keep affected connections disabled.
- event_key=etf:btc-us-spot:2026-10-22; family=etf:btc-us-spot; material_version=farside_final_2026-10-22_-635.6m; HIGH; verified data aggregator; INCLUDE_CANDIDATE §5. Oct23 ETF figures incomplete.
- event_key=binance:alpha:removal:2026-10-23; family=binance:alpha:featuring; material_version=official_2026-10-23T09:30Z_7tokens; MEDIUM; official English indexed; INCLUDE_CANDIDATE §7 with direct-open caveat. Alpha feature removal not all trading delisted.
- event_key=macro:us-equities-oil:2026-10-23; family=macro:us-equities-oil; material_version=AP_2026-10-23_us_close; MEDIUM; provisional from 00 collector, VERIFY_REQUIRED before §10.
- event_key=rwa:okxice:issuer-objections:2026-10-23; family=rwa:okxice:issuer-objections; material_version=Reuters_2026-10-23_22_objections; MEDIUM; SECONDARY_ONLY, WATCH/SOURCE_GAP original regulatory filing. Possible §4 or §6 per latest editorial routing, no first-party confirmation this round.

## Explicit non-claims and workflow

- Gmail Sent last 7 days checked. 2026-10-23 official delivered ID 1a1671914359ade4 and body read back; contains Oct21 Railway secret incident + Oct22 credential reset, not Oct23 unqueued deploys guide. Oct24 formal publication is NOT DUE in 03:20 slot. No Gmail sent or attempted.
- Previous ledger d7806bb407a95a9d1a5ba8e5d76a39cbf433c759 suppresses old LiteLLM/Railway initial/ConnectWise initial/Node/Laravel/PHP2Shell/eMudhra, Space/Surf/StandX/NeoSoul old versions.
- Six security families were checked independently; no claim of exhaustive source coverage. Arkham TXID, X/Reddit, new NFT social, venue policy first-party and Friday close remain PARTIAL_SOURCE_GAP. No formal editorial QA, no READY, no pending file.
- No new monitor, paid API, Mac process, GitHub cron, asset watch, App alert or health email.
