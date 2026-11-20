# 2026-11-20 12:20 Asia/Bangkok bounded source snapshot
Status: PARTIAL_SOURCE_GAPS; collector only; no Gmail attempted. No claim of complete 13-section QA. 
Checked at: 2026-11-20 12:20 Asia/Bangkok. Binance ticker closeTime 1795152026xxx and futures time 1795152030001 UTC milliseconds.

## Section-ready verified market paragraphs
§2 BTC/USDT Binance Spot last 61,600.18, rolling 24h -2.846%, range 61,290.58–64,080.80, volume 21,965.65216 BTC. ETH/USDT 1,726.21, -3.912%, range 1,717.82–1,817.57, volume 350,836.1038 ETH. SOL/USDT 72.06, -3.275%, range 71.59–75.65, volume 2,431,525.843 SOL. BNB/USDT 567.38, -3.250%; HYPE/USDT 64.78, -4.186%. These are rolling Binance 24-hour statistics, not calendar-day close or a directional forecast.
§3 Binance USD-M mark prices: BTC 61,566.10, ETH 1,725.05, SOL 72.01472972 USDT; last funding rates BTC -0.00000926, ETH +0.00003564, SOL +0.00001774 (decimal fraction per funding interval). No multi-period trend claim from one snapshot.
§13 Core risk checkpoint: BTC/ETH/SOL all down in the observed rolling 24h window; avoid interpreting mark price and spot divergence or funding alone as proof of liquidation cascade.

Official connector methods: Binance get_spot_24hr_ticker_price_change_statistics single symbols BTCUSDT ETHUSDT SOLUSDT BNBUSDT HYPEUSDT; get_futures_usds_mark_price single symbols BTCUSDT ETHUSDT SOLUSDT.
Source URLs: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints and https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Mark-Price
Gmail Sent checked via connected life account query in:sent after:2026/11/19 before:2026/11/22 subject:Crypto; only Nov19 manually delivered ID 1a1f2334a183ecdb returned, no Nov20 match in this query. This is not exhaustive all-subject dedupe.
Git current rules fetched: PIPELINE_CONTRACT.md, EDITORIAL_RULESET.json, REPORT_SPEC.md, REPORT_ACCEPTANCE.md, COLLECTOR_SPEC.md, SECURITY_SOURCE_POLICY.md, DELIVERY_RUNBOOK.md, state/daily-event-ledger.json.
Source receipts NOT COMPLETED this round: ETF/Farside, institutional/onchain/Arkham, policy, infrastructure, TGE, Early/NFT, security six lanes, macro, forward catalysts, official_x, third_party_ipo_access. Mark SOURCE_GAP/NOT_CHECKED, never no-news. No new event_key or material_version claimed.
Delivery: no Gmail; existing 09:20 daily publisher is sole formal delivery window; 12:20 is collector-only. This snapshot is research, not final QA or sent proof.
