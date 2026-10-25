# Crypto Daily 2026-10-25 12:20 bounded source receipts and candidate research

- scheduled_slot_bkk: 2026-10-25 12:20
- observed_collection_window_bkk: 2026-10-25 12:20:11–12:21:02 +07:00
- research_persisted_at_utc: 2026-10-25T05:21:33.484Z
- mode: ORDINARY_BOUNDED_COLLECTOR; no Gmail, no App notice
- prior_authoritative_sent: Gmail ID 1a170e1f82549e41, subject Crypto Daily Brief｜2026-10-25; SENT/readback 5478 chars EXACTLY equals canonical Git report body, Git blob fcb290616c0268b5323c9322923681b504523df7. Rechecked 2026-10-25T05:21:02Z.
- latest_7d_sent_subjects_checked: 2026-10-18,19,20,21 (two),22 (two),23,24,25; current daily already delivered, NO second email.
- source_contract_blobs: PIPELINE=5365fb29bb00f20101d4190737468da845b4a0e2; EDITORIAL=ad3488769052a1cea5dda4bbf7fd6f1f9092046f; REPORT_SPEC=809a5c1cbcd6503d42305c842f37826b74a4741f; ACCEPTANCE=37789b7274aec766e4ac4975111602bccc11a7d2; COLLECTOR=834e0e3c05f5e894f31474a7b4d7fd0e90d8c08f; SECURITY=86b36f208220e90a52caa1cb8acaeec47add9628; DELIVERY=181c0448dddd2586e6082faaa1f51f7556eaa795; RUNTIME=59318705a3a238e5798f5ee7a1c7098eb49ae514; LEDGER=b8f5c1fdf707e9217820e414c52e55c3f60bae21.
- last_two_collector_finals: 2026-10-25/032136-final.md (PARTIAL, shard1), 2026-10-25/062218-final.md (PARTIAL, shard2); neither proves FULL deep-shard completion; planned_shard=0 fallback, executed_shard=0 PARTIAL; backlog_shards=0,1,2 not proven complete.

## Official Binance market API (actual read-only connected API calls)
- checked_at_bkk: 2026-10-25 12:20:19–12:20:22. Initial multi-symbol ticker request returned HTTP400 -1101 "Duplicate values for parameter symbols"; all five per-symbol retries succeeded. Binance 24hr rolling, USDT pair quotes, NOT global composite.
- BTCUSDT last 80898.00, 24h +0.071%, high 81033.69, low 79220.74, quoteVolume 886868419.891 USDT; official closeTime 1792905621004; https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT
- ETHUSDT last 2366.83, 24h -0.523%, high 2384.28, low 2282.46, quoteVolume 461216243.865 USDT; closeTime 1792905621014; https://api.binance.com/api/v3/ticker/24hr?symbol=ETHUSDT
- SOLUSDT last 102.55, 24h +0.146%, high 102.77, low 98.62, quoteVolume 163404676.681 USDT; closeTime 1792905620747; https://api.binance.com/api/v3/ticker/24hr?symbol=SOLUSDT
- BNBUSDT last 747.84, 24h +1.193%, closeTime 1792905619523; HYPEUSDT last 76.77, 24h -0.299%, closeTime 1792905613214. Same Binance ticker endpoint per symbol.
- USDⓈ-M single-point OI as-of API time 1792905608551 BTC 93978.624 BTC; 1792905614533 ETH 2273794.240 ETH; 1792905612646 SOL 8498832.14 SOL. https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT (equivalent ETH/SOL).
- USDⓈ-M last settled funding at 1792886400000 UTC ms: BTC 0.00009409 (0.009409%), ETH 0.00003746 (0.003746%), SOL 0.00006698 (0.006698%). https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT (equivalent ETH/SOL). No continuous OI trend or liquidation verified.
- event_key market:btc-eth-sol:2026-10-25:122021; material_version binance-closeTime-1792905621004; verified API observation; decision CARRY §2 next daily if current quote, not duplicate as historical breaking news.

## Mandatory independent domain/source receipts (all checked 2026-10-25 12:20–12:21 Asia/Bangkok)
Each line lists original checked URL, source's original date, outcome. No claim of comprehensive global recall.

1. spot: Binance five per-symbol 24hr official API URLs above; published_at API closeTime above; CHECKED, live verified.
2. derivatives: Binance OI/funding official API URLs above; published_at API times above; CHECKED single-point, liquidation SOURCE_GAP.
3. capital_flows: https://farside.co.uk/btc/ https://farside.co.uk/eth/ https://farside.co.uk/sol/ ; US session 2026-10-23 is latest row, BTC displayed -137.9m USD but HODL blank, ETH +4.4m but ETHV blank, SOL 0.0m but VSOL blank; CHECKED PARTIAL issuer completeness, same version delivered 09:20, no new total claimed.
4. onchain: https://info.arkm.com/research (index shows Oct23 generic articles, not full transaction coverage); https://lookonchain.com/feeds and /feeds/78528 /feeds/78531; CHECKED attributed posts; underlying raw transaction/position state SOURCE_GAP.
5. policy/venue: https://www.binance.com/en/support/announcement (latest shown 2026-10-23 Alpha removals); https://www.bitget.com/support (latest 2026-10-24 withdrawals resumption); https://www.bybit.com/en/help-center (index only). English queries "Binance Bybit Bitget restricted counterparty HTX deposits withdrawals Oct24 Oct25", "crypto sanctions exchange source-of-funds Oct25". No new first-party Oct25 counterparty material version established; direct article-level exhaustive coverage SOURCE_GAP. No personal account affected inferred.
6. infrastructure: https://www.sec.gov/newsroom/press-releases (visible latest Oct20, not evidence no Oct25 global regulation); https://www.circle.com/blog/circle-gateway-now-supports-cirbtc-and-eurc (issuer Oct23, already delivered). CHECKED INDEX/PARTIAL.
7. tge: English queries "October 25 2026 crypto airdrop TGE claim official project announcement", "StandX NeoSoul community compensation new Oct25"; no independently confirmed new official eligible action in retrieved sources; SOURCE_GAP on issuer X/direct primary; old Space/Surf/StandX/NeoSoul suppressed unless new material_version.
8. early_nft: https://opensea.io/blog (latest visible official Oct20 mobile launch, older); https://www.reddit.com/r/NFT/new/ (latest visible post 9d old, not proof real-time); https://lookonchain.com/feeds/78524 (new Pump.fun Monad USDC buy feature attributed to issuer social, exact original post inaccessible); direct X SOURCE_GAP. No independently verified new mint/claim.
9. security (crypto specialists): https://www.certik.com/blog (latest research Oct20 PaperTrade, old); https://www.scamsniffer.io/ (live example blocklist, no per-case audited user loss); English searches for SlowMist, Blockaid, SEAL, wallet drain Oct25; X/Reddit source recency PARTIAL. No "all clear" inference.
10. web_runtime_rce: https://www.php.net/archive/2026.php (PHP2Shell official Oct21, already delivered Oct22); https://nodejs.org/en/blog/vulnerability/october-2026-security-releases (Oct21). CHECKED old versions, no verified new 25th disclosure in retrieved originals.
11. web_pki_tls: https://blog.mozilla.org/security/2026/10/20/protecting-firefox-users-following-the-compromise-of-emudhra-intermediate-certificates/ (Mozilla Oct20, previously delivered); Node Oct21 CA/TLS notes. CHECKED old versions; no new verified delta.
12. ai_package_supply_chain: https://docs.litellm.ai/blog/ (Oct24 nonsecurity provider article, Oct23 official attack-chain root cause); https://docs.litellm.ai/blog/security-incident-oct-21-2026-attack-chain (Oct23, already delivered); https://github.com/advisories (index, not exhaustive PyPI/Docker monitoring). CHECKED, no new issuer security delta established.
13. cloud_secrets_identity: https://blog.railway.com/p/preliminary-report-october-security-incident (Oct22); https://status.railway.com/ (Oct24 replacement key clarification, delivered today); https://www.connectwise.com/company/trust/advisories (latest Oct24 14:00 UTC, next update due Oct25 14:00 UTC, which is AFTER current Bangkok 12:20); https://www.microsoft.com/en-us/security/blog/ (index). CHECKED; do not pre-claim a future vendor update.
14. backend_framework_auth: https://github.com/laravel/framework/security/advisories (Laravel Oct19 issues); https://nodejs.org/en/blog/vulnerability/october-2026-security-releases (Oct21 official patch train); CHECKED, old versions. No evidence of fresh Oct25 Laravel/Node disclosure.
15. macro: English search "October 25 2026 macro markets Federal Reserve regulation stablecoin ETF Reuters" and https://www.sec.gov/newsroom/press-releases; older Iran-US risk and Friday market close already in 09:20 report; weekend source freshness PARTIAL, no unsupported causal assertion.
16. forward_catalysts: ConnectWise https://www.connectwise.com/company/trust/advisories Oct24 14:00Z says next daily update by Oct25 14:00Z; this is 21:00 Bangkok, FUTURE at this collector. No claim service restored; status pending official follow-up.

## New/changed candidate accounting since today's verified Sent
- event_key: onchain:lookonchain:eth-whale-93184-margin:2026-10-25
  family_key: onchain:eth-perp-whale-93184; material_version: lookonchain-feed-78531-margin-added-5.67m
  published_at: displayed "2 hours ago" at 12:20 BKK; exact minute UNKNOWN; first_seen_at_bkk: 2026-10-25T12:20:xx+07:00
  source_url: https://lookonchain.com/feeds/78531 ; source_tier: ORIGINAL_ATTRIBUTED_ANALYTICS
  claim: Lookonchain says 93,184 ETH long position added 5.67m USDC margin, revised liquidation thresholds 2181.69/2177.79 USD; positions and tx not independently read.
  materiality: HIGH_REVIEW due size and new margin action; status: VERIFYING; decision: CARRY for next §5/§3 candidate if confirmed; today's report already referenced the same whale in an earlier material version, so ONLY new margin action may qualify; NO repeat mail now.
- event_key: onchain:lookonchain:arthur-hayes-sales:2026-10-25
  family_key: onchain:arthur-hayes:token-transfers; material_version: lookonchain-feed-78528-28.8m-sales-claimed
  published_at: displayed "3 hours ago" at 12:20 BKK; exact minute UNKNOWN; first_seen_at_bkk: 2026-10-25T12:20:xx+07:00
  source_url: https://lookonchain.com/feeds/78528 ; source_tier: ORIGINAL_ATTRIBUTED_ANALYTICS
  claim: Lookonchain says ~28.8m USD token sales in 24h and ~6.65m profit; underlying wallets, sale fills and profit accounting not independently verified.
  materiality: HIGH_REVIEW; status: VERIFYING; decision: CARRY §5 after raw tx and source-time validation; no proven realized sale/profit in this audit.
- event_key: early:pumpfun:monad-usdc-purchase:2026-10-25
  family_key: early:pumpfun:monad-support; material_version: lookonchain-feed-78524-feature-claim
  published_at: displayed "3 hours ago"; exact issuer timestamp UNKNOWN
  source_url: https://lookonchain.com/feeds/78524 ; source_tier: SECONDARY_ATTRIBUTED_ISSUER_SOCIAL
  claim: feed says Pump.fun added Monad ecosystem token purchases with USDC; official original X post could not be opened (Internal Error); no execution/asset or supported contract verified.
  materiality: MEDIUM; status: VERIFYING; decision: CARRY §8/§6 only after official primary proof, no added monitored project.
- event_key: market:btc-eth-sol:2026-10-25:122021; verified rolling API observation only, not a standalone alert.
- EXCLUDE NO_NEW_MATERIAL_VERSION: PHP2Shell, eMudhra, LiteLLM compromised package, Railway Oct24 replacement keys, ConnectWise Oct24 phased restoration, Node Oct21, Laravel Oct19 TokenGuard, old NeoSoul/StandX/Space/Surf and already delivered 09:20 events. Preserve prior ledger material versions.
- SOURCE_GAP: no raw X readback for above social posts, no onchain TX/position proof, no exhaustive Arkham entity feed, incomplete ETF issuer rows, no verified current NFT mint/rights, no newly proven CEX counterparty policy.

## Execution boundary
This is an ordinary collector after today's one authorized 09:20 delivery. No pending manifest or report rebuild, no Gmail send, no TGE alert, no App notice, no task modification, no local process, no paid API. Persist one research artifact and one terminal final; do not call this a full editorial QA or complete all-lane coverage.
