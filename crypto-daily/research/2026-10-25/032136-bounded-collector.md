# Crypto Daily bounded collector | 2026-10-25 03:20 Asia/Bangkok

status: PARTIAL_SOURCE_GAPS
automation_id: 6a8600b9d12481919bc43ebc800c9916
actual_started_at_bkk: 2026-10-25T03:21:36+07:00
source_checked_at_bkk: 2026-10-25T03:21:36..03:24:00+07:00 (bounded, approximate per page; precise Binance exchange times below)
planned_shard: 1 (fallback, last two persisted finals 2026-10-25/002017 and 2026-10-24/202149 both PARTIAL, no two complete deep shards)
executed_shard: 1 PARTIAL (ecosystem/RWA/TGE/PM)
email: NOT_DUE; app_notifications: NONE; no new monitor/cron/local daemon/paid API.
Git rules SHAs: PIPELINE 5365fb29bb00f20101d4190737468da845b4a0e2; EDITORIAL ad3488769052a1cea5dda4bbf7fd6f1f9092046f; REPORT_SPEC 809a5c1cbcd6503d42305c842f37826b74a4741f; REPORT_ACCEPTANCE 37789b7274aec766e4ac4975111602bccc11a7d2; COLLECTOR 834e0e3c05f5e894f31474a7b4d7fd0e90d8c08f; SECURITY 86b36f208220e90a52caa1cb8acaeec47add9628; RUNTIME 59318705a3a238e5798f5ee7a1c7098eb49ae514; DELIVERY 181c0448dddd2586e6082faaa1f51f7556eaa795; LEDGER b8f5c1fdf707e9217820e414c52e55c3f60bae21.

## Original Binance spot/derivatives data

Actual connected Binance official market API queries, each symbol separately because combined symbols request returned HTTP400 -1101 duplicate symbols; successful retry by single symbol (do not claim original batch succeeded). USD(T), rolling 24h, not global composite.

| pair | last USDT | 24h change | 24h high/low USDT | quote volume USDT | exchange closeTime UTC |
|---|---:|---:|---|---:|---|
| BTCUSDT | 80566.01 | -0.946% | 81500.00 / 79220.74 | 1036272103.26 | 2026-10-24T20:22:08.005Z |
| ETHUSDT | 2345.75 | -2.067% | 2405.22 / 2282.46 | 511193419.99 | 2026-10-24T20:22:10.976Z |
| SOLUSDT | 101.56 | -1.893% | 104.12 / 98.62 | 195053124.54 | 2026-10-24T20:22:10.577Z |
| BNBUSDT | 731.64 | -1.307% | 743.56 / 718.00 | 95703573.94 | 2026-10-24T20:22:11.037Z |
| HYPEUSDT | 76.37 | -1.101% | 78.05 / 74.45 | 21811380.10 | 2026-10-24T20:22:07.553Z |

Binance USD-M perpetual mark/index/lastFundingRate (2026-10-24T20:22:07-08Z): BTC 80531.4086 / 80566.7017 / +0.00004871; ETH 2344.6310 / 2345.8258 / -0.00005826; SOL 101.5051 / 101.5609 / -0.00005916. USD-M OI single point (2026-10-24T20:23:42Z): BTC 96129.495 BTC; ETH 2293142.304 ETH; SOL 8666330.63 SOL. Funding is most recently returned rate, not predicted future rate. One-point OI cannot establish 24h direction, position side or liquidations. Earlier 00:20 BTC=80222.88, ETH=2320.68, SOL=100.43; intraday difference is not a multi-day trend.

## Independently executed source receipts

Checked 2026-10-25 03:21-03:24 BKK. Each row reflects actual English official-page open or indexed English search. Publication time is publisher date when visible; UNKNOWN means no reliable date, not zero activity.

| lane | original source URL / exact query family | publisher date | observed result / gap |
|---|---|---|---|
| spot | connected Binance official GET /api/v3/ticker/24hr per BTCUSDT ETHUSDT SOLUSDT BNBUSDT HYPEUSDT | rolling 24h, exchange closeTimes above | PASS real prices |
| derivatives | connected Binance USD-M premiumIndex and openInterest BTCUSDT ETHUSDT SOLUSDT | live timestamps above | PARTIAL no historical OI/liq |
| capital_flows | https://farside.co.uk/btc/ ; https://farside.co.uk/eth/ ; https://farside.co.uk/sol/ | US session Oct23 | PARTIAL BTC -137.9m with HODL dash; ETH +4.4m with ETHV dash; SOL 0.0m with VSOL dash. Do not treat these as full issuer-complete totals |
| onchain | https://info.arkm.com/research ; searches 'site:info.arkm.com/research 2026 October 24 Bitcoin transfer whale', 'site:lookonchain.com 2026 October 24 25 BTC whale exchange deposit' | Arkham index latest Oct23; secondary Lookonchain rotation report Oct24 | SOURCE_GAP no new raw TXID/original tagged flow; index does not cover all chain activity |
| cex_account_security | https://www.binance.com/en/support/announcement ; https://www.bitget.com/support ; https://www.bybit.com/en/help-center ; query 'crypto exchange Binance Bybit Bitget Kraken hack withdrawals freeze source of funds AML October 24 25 2026' | Binance visible Oct23 Alpha removals, others no date | PARTIAL no new specific venue AML HTX rule proven; generic help-center not proof of no updates |
| wallet_user_loss | https://www.scamsniffer.io/ ; https://www.slowmist.com/ ; English search 'October 24 2026 crypto security incident new exploit wallet bridge chain halted' | no dated incident in directly opened homepages | PARTIAL specialist original X/incident feed unavailable, no global negative claim |
| chain_protocol_security | https://status.initia.xyz/ ; https://www.electrum.org/ | Initia status last Oct24 20:04 UTC; Electrum current 4.8.3 release page undated | PARTIAL Initia now operational, alleged earlier MoveVM incident not resolved by status page; Electrum version verified but release advisory time not established |
| web_runtime_rce | https://www.php.net/archive/2026.php ; English search site:php.net/archive/2026.php October 24 25 2026 | Oct23 PHP session-upload mitigation, Oct21 critical patch | CHECKED old published event; no new material version evidenced |
| web_pki_tls | https://blog.mozilla.org/security/2026/10/20/protecting-firefox-users-following-the-compromise-of-emudhra-intermediate-certificates/ ; English search Oct24-25 TLS CA | Oct20 original, Oct21 Android update | CHECKED old published event; no new material version evidenced |
| ai_package_supply_chain | https://docs.litellm.ai/blog ; https://docs.litellm.ai/blog/security-incident-oct-21-2026-attack-chain ; search Oct24-25 LiteLLM PyPI Docker | Oct23 root cause; Oct24 OpenCode Go provider blog (not security advisory) | CHECKED historical malicious 1.107.0; no new malicious release proven |
| cloud_secrets_identity | https://status.railway.com/ ; https://www.connectwise.com/company/trust/advisories ; https://www.microsoft.com/en-us/security/blog/2026/10/21/storm-0940-uses-artex-agentic-ai-connectwise-supply-chain-compromise/ ; https://dash-new.zeabur.com/blogs/october-2026-security-incident | Railway Oct24 13:57 UTC, ConnectWise Oct24 14:00 UTC, Microsoft Oct21, Zeabur Oct19 | VERIFIED lifecycle candidates Railway and ConnectWise already in 00:20; NEW BACKFILL Zeabur independent incident |
| backend_framework_auth | https://nodejs.org/en/blog/vulnerability/october-2026-security-releases ; https://github.com/laravel/framework/security/advisories | Node Oct21; Laravel Oct19 | CHECKED old versions, no newer official advisory proven |
| policy | https://www.binance.com/en/support/announcement ; https://www.bybit.com/en/help-center ; search exchange restricted counterparties Oct24/25; site:sec.gov OR site:federalreserve.gov Oct24 2026 | no new dated primary in returned result | PARTIAL source search not comprehensive |
| infrastructure | https://www.about.hsbc.com.hk/news-and-media/hsbc-redcoin-launches-today ; search site:circle.com/blog 'cirBTC' 'EURC' October 23 2026 | HSBC Oct23; Circle Oct23 | VERIFIED carry-over original issuer facts; Circle direct open blocked but original English indexed page content retrieved |
| tge | https://t.me/s/extended_updates ; Binance announcement; English 'StandX DUSD eligibility October 26 2026 official' and 'Pharos PROS claim deadline October 25 2026 official' | Extended visible posts without reliable dates; secondary StandX Oct15, Pharos conflicting secondary dates Oct25 vs Oct31 | SOURCE_GAP no fresh primary new rights; no claim link or invented eligibility |
| early_nft | https://opensea.io/blog ; English search Oct24/25 Jack Butcher NFT drop mint | OpenSea latest announcement Oct20 | PARTIAL X/social drop sources inaccessible, cannot assert none |
| macro | search 'US equity funds post inflows for a second straight week Reuters October 23 2026', 'site:sec.gov OR site:federalreserve.gov October 24 2026 digital assets markets rates' | Reuters Oct23 weekly flows, Fed index older | PARTIAL no new independently verified Oct24 policy/rate release |
| forward_catalysts | https://www.connectwise.com/company/trust/advisories ; Zeabur official shutdown; StandX secondary date search | ConnectWise Oct24 says next Oct25 14:00 UTC; Zeabur Oct17 December wind-down; StandX Oct15 original inaccessible | WATCH; dates need issuer primary for StandX; no separate user alert |

## Candidate ledger / material version decisions

1. event_key=zeabur:oct14-15-2026:cloud-secrets-breach; family_key=cloud:zeabur:security; material_version=zeabur-official-preliminary-2026-10-19; source_published_at=2026-10-19; first_seen_at_bkk=2026-10-25T03:22+07:00; source=https://dash-new.zeabur.com/blogs/october-2026-security-incident; tier=ISSUER_PRIMARY; status=VERIFIED_BACKFILL; materiality=HIGH; primary_section=9; disposition=INCLUDE_CANDIDATE_FOR_NEXT_FULL_EDITORIAL if no prior delivery. Official says Oct14-15 unauthorized access to shared clusters/GCP dedicated and platform env variables, recommends rotation. Some read operations confirmed; do not infer each customer compromised. Search Gmail Sent Oct18-24 for 'Zeabur' returned no results. Need still inspect Git last seven days for cross-report match before publication.
2. event_key=zeabur:service-wind-down:2026-10-17; family_key=cloud:zeabur:shutdown; material_version=zeabur-official-2026-10-17-shutdown-deadlines; source_published_at=2026-10-17; first_seen_at_bkk=2026-10-25T03:22+07:00; source=https://zeabur.com/blogs/zeabur-is-shutting-down; tier=ISSUER_PRIMARY; status=VERIFIED_BACKFILL; materiality=HIGH; primary_section=6 (shutdown) with security breach in §9 as separate distinct action; disposition=INCLUDE_CANDIDATE_FOR_NEXT_FULL_EDITORIAL if unreported. December 1 service changes; December 31 dedicated/shared clusters shut down. User usage NOT established. Old date must be labeled backfill, not breaking Oct25.
3. event_key=hsbc:redcoin:payme-launch:2026-10-23; material_version=hsbc-official-launch-2026-10-23; published=2026-10-23; source=https://www.about.hsbc.com.hk/news-and-media/hsbc-redcoin-launches-today; tier=ISSUER_PRIMARY; status=VERIFIED_CARRIED; materiality=HIGH; primary_section=6; issuer says HKD stablecoin RCHKD launched through PayMe and 3.3m PayMe users can activate; does NOT prove 3.3m holders or user eligibility. Carry from Oct24 16:20.
4. event_key=circle:gateway:cirbtc-eurc-expansion:2026-10-23; material_version=circle-official-2026-10-23-cirbtc-eurc; published=2026-10-23; source=https://www.circle.com/blog/circle-gateway-now-supports-cirbtc-and-eurc; tier=ISSUER_INDEXED_ORIGINAL_DIRECT_FETCH_GAP; status=VERIFIED_ISSUER_TEXT_INDEXED; materiality=MEDIUM; primary_section=6; no unsupported crosschain guarantees.
5. event_key=railway:api-key-revocation-clarification:2026-10-24; material_version=railway-status-2026-10-24T13:57Z; source=https://status.railway.com/; tier=ISSUER_PRIMARY; status=VERIFIED_CARRIED_FROM_00:20; materiality=HIGH; primary_section=9; no new version after 00:20, do not create second story.
6. event_key=connectwise:cloud-backup-2026-10-24-restoration-plan; material_version=connectwise-official-2026-10-24T14:00Z-monday-restore-target; source=https://www.connectwise.com/company/trust/advisories; tier=ISSUER_PRIMARY; status=VERIFIED_CARRIED_FROM_00:20; materiality=HIGH; primary_section=9; no new version after 00:20. Next update scheduled Oct25 14:00 UTC, not due at this run.
7. event_key=etf:btc-eth-sol:2026-10-23; material_version=farside-us-session-2026-10-23-partial-issuer-columns; source=https://farside.co.uk/btc/; tier=ORIGINAL_AGGREGATOR; status=VERIFYING_CARRIED; materiality=MEDIUM; primary_section=5; explicitly partial issuer columns; cannot claim complete net flows.
8. event_key=pharos:pros:claim-deadline:2026-10; material_version=secondary-conflict-2026-10-25-vs-31; source=https://cryptoticker.io/en/pharos-airdrop-claim-deadline/ and https://usethebitcoin.com/airdrop/pharos-airdrop-guide/; tier=SECONDARY_CONFLICTING; status=VERIFYING_SOURCE_GAP; materiality=HIGH_IF_VALID; primary_section=7; no official Pharos claim FAQ retrieved. DO NOT publish exact cutoff or link or assert user eligibility until official proof.
9. event_key=standx:dusd:eligibility-checker:2026-10-26; material_version=old-oct15-issuer-announcement-secondary-2026-10-26-checker; source=https://crypto.news/standx-to-shut-down-perpetual-futures-exchange-cancels-planned-token-launch/; tier=SECONDARY; status=WATCH_NO_NEW_DELTA; primary_section=7; old StandX notice already delivered across monitors. Future checker not yet open; do not reissue old notice or invent link.

## Dedupe and gaps
- Existing event ledger SHA b8f5c1... and 2026-10-24 delivered canonical report checked; Oct23/24 previous security incidents not recycled.
- Gmail Sent query Oct18-Oct25 returned 9+ real daily messages; separate Sent Zeabur query returned 0. Does not alone prove Git reports never mentioned Zeabur; publisher must check canonical Git history.
- PHP Oct21/23, eMudhra Oct20/22, LiteLLM Oct21/23, Railway Oct22/23, ConnectWise Oct23, Node Oct21, Laravel Oct19 old versions suppressed. Railway/ConnectWise Oct24 are distinct and carried once.
- Onchain original TX-level and Arkham real-time transaction coverage remain PARTIAL; no sale inferred from wallet movement. Live X/Reddit, current official StandX/Pharos claim rules, complete Oct23 ETF issuer rows, and full NFT discovery remain SOURCE_GAP.
- No report draft, editorial QA, CI receipt, Gmail send or user notification is due in ordinary collector mode.
