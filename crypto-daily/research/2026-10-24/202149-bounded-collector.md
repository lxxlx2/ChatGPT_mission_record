# 20:20 bounded source discovery, 2026-10-24

checked_at: 2026-10-24T20:21:49+07:00
mode: ordinary collector, no outgoing email
coverage: PARTIAL (onchain individual TX, early/NFT, macro and exact original Initia exploit statement gaps)
existing official daily: Gmail Sent 1a16bba1e9212873, exact canonical Git body verified. DO NOT resend.

## Verified official market facts
- Binance spot 24hr REST via connected Binance API: BTCUSDT 80725.21, -1.194%, high 82060.88, low 80451.18, quote volume 897811353.17415990 USDT, closeTime 1792848024002; ETHUSDT 2367.05, -1.405%, high 2417.77, low 2351.55, closeTime 1792848023004; SOLUSDT 101.35, -2.959%, high 105.24, low 101.14, closeTime 1792848023556. Rolling 24h snapshots, not official close.
- Binance USDS-M BTCUSDT openInterest 94581.266 BTC at 1792848021178. One instant OI cannot prove long/short trend.
- Farside source checked: https://farside.co.uk/btc/ ; https://farside.co.uk/eth/ ; https://farside.co.uk/sol/ . Latest US Oct23 partial rows; no complete 23 Oct flow asserted.

## Material candidate decisions
1. event_key=bitget:usdc-bsc:withdrawal-resumed:2026-10-24; material_version=bitget-official-2026-10-24-0324; PRIMARY=policy/exchange-access; severity=MEDIUM; INCLUDE_IN_NEXT_DAILY_IF_STILL_MATERIAL (after next-day dedupe). Original: https://www.bitget.com/support/articles/12560603898714 ; official article shows 2026-10-24 03:24 (page timezone not explicitly verified), states USDC-BSC withdrawals resumed. Distinct later lifecycle update after Oct24 morning daily's suspension; do not repeat suspension as current status.
2. event_key=electrum:security-release:4.8.3:2026-10-23; material_version=official-release-notes-4.8.3; PRIMARY=security; severity=HIGH candidate; INCLUDE_PENDING_DEDUP_CHECK. Official https://electrum.org/ and https://github.com/spesmilo/electrum/blob/master/RELEASE-NOTES ; 4.8.3 published Oct23 marked security update with security fixes, details not fully disclosed. No proof user runs Electrum, no asserted exploit or loss; verify original signature, avoid fake download links.
3. event_key=initia:movevm-incident:2026-10-23; material_version=secondary-lookonchain-2026-10-24; PRIMARY=security; severity=HIGH candidate; WATCH_UNVERIFIED/SOURCE_GAP. https://lookonchain.com/ currently relays alleged $2.7m MoveVM incident; https://status.initia.xyz/ shows mainnet Operational as of Oct24 13:06 UTC; https://blog.initia.xyz/ inaccessible. A green status does not refute earlier attack. Seek original issuer post and TX evidence before reporting definitive loss. Oct24 morning daily already included a preliminary Initia candidate, so suppress without verified new delta.

## Source receipts (all checked in this run, UTC times from fetched pages when stated)
- spot: Binance connected official 24h API, timestamps above, OK.
- derivatives: Binance connected USDS-M openInterest API, OK; no historical trend.
- capital_flows: Farside BTC/ETH/SOL pages above, OK/PARTIAL latest US session.
- onchain: https://info.arkm.com/research (featured Oct23 guides, dynamic 0 posts), https://lookonchain.com/ (feed); no TX proof, SOURCE_GAP.
- policy: https://www.binance.com/en/support/announcement ; https://www.bitget.com/support/articles/12560603898707 and /12560603898714 ; resumed withdrawal verified.
- infrastructure: https://status.initia.xyz/ ; mainnet operational current, historic exploit issuer original SOURCE_GAP.
- tge: Binance announcements and English search for CoinList/Kraken, no new verified TGE from bounded check; not proof of absence.
- early_nft: English bounded search plus Lookonchain; no original new NFT/claim verified; SOURCE_GAP.
- security: https://www.php.net/archive/2026.php ; Oct23 session-upload advisory previously reported, no fresh material version established.
- web_runtime_rce: https://nodejs.org/en/blog/vulnerability/october-2026-security-releases ; published Oct21; no fresh official material version established.
- web_pki_tls: https://blog.mozilla.org/security/2026/10/20/protecting-firefox-users-following-the-compromise-of-emudhra-intermediate-certificates/ ; published Oct20; no fresh official delta.
- ai_package_supply_chain: https://docs.litellm.ai/blog/security-incident-oct-21-2026-attack-chain ; published Oct23; already delivered Oct24.
- cloud_secrets_identity: https://blog.railway.com/p/preliminary-report-october-security-incident ; Oct22; https://www.connectwise.com/company/trust/advisories ; Oct24 update not yet published at check, no verified delta.
- backend_framework_auth: https://github.com/laravel/framework/security/advisories/GHSA-f9x3-7vq9-cph6 ; prior advisory, no new official delta.
- macro: bounded official sec.gov/federalreserve.gov/bls.gov English search, no original new actionable macro claim established; PARTIAL.
- forward_catalysts: bounded Binance and official release source review; no verified future event, PARTIAL.

## Delivery / dedupe
Gmail Sent 1a16bba1e9212873 for 2026-10-24 read with complete body (6507 chars), to lxx.run688@gmail.com; Git crypto-daily/reports/daily/2026/2026-10/2026-10-24.md canonical blob 85f11dd7076fcaf81ffea3e68948817f7ad00121; exact-body match. CI delivery-qa/2026-10-24.json status EDITORIAL_QA_PASS, manifest SHA 4a4b93a31b8abadcb2646778355a8ee8cc66ae7d, rules SHA ad3488769052a1cea5dda4bbf7fd6f1f9092046f. Ordinary collector sends no Gmail.
