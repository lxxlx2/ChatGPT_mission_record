# 2026-11-19 11:23 ICT recovery source and QA evidence

stage_entered: 11:20 RECOVERY
automation_id: 6a8600b9d12481919bc43ebc800c9916
checked_at: 2026-11-19 11:23–11:26 Asia/Bangkok
gmail_sent_prefix: Crypto Daily Brief｜2026-11-19
gmail_sent_matches: 0 (Gmail Sent search after 2026/11/17)
canonical: crypto-daily/reports/daily/2026/2026-11/2026-11-19.md NOT_FOUND
pending: crypto-daily/delivery-pending/2026-11-19.json NOT_FOUND
delivery_qa: crypto-daily/delivery-qa/2026-11-19.json NOT_FOUND
source_method: actual connected Binance spot single-symbol and USD-M open-interest; Farside original; SEC EDGAR original; Reuters dated article
rules_sha:
  PIPELINE_CONTRACT.md: 29ffbc1d32ca87a744d2990e8d55639ebb84a6f9
  EDITORIAL_RULESET.json: 2ed51528d230508ae4e0015762b1d60c9d72e299
  REPORT_SPEC.md: 2e70414c8fdb8d23a292cc3bf7797425a403e179
  REPORT_ACCEPTANCE.md: 28f5d9e8a54dd932223cc2a686466f1d12cf597f
  DELIVERY_RUNBOOK.md: cff301c7e15451972a415e24e1863f8d5e31360f

## Verified actual raw readings
Binance spot 24hr ticker closeTime Unix ms 1795062213013 BTCUSDT last 63366.55; change -1.844%; high 64952.92 low 62062.97; volume 19014.37005 BTC; futures OI 96359.750 BTC at 1795062206172.
ETHUSDT closeTime 1795062213008 last 1798.02; -0.529%; high 1819.65 low 1732.83; volume 304250.8276 ETH; futures OI 2464798.151 ETH at 1795062209020.
SOLUSDT closeTime 1795062213768 last 74.42; -0.760%; high 75.66 low 72.22; volume 2213089.233 SOL; futures OI 8399705 SOL at 1795062207199.
Farside original https://farside.co.uk/bitcoin-etf-flow-all-data/ last complete 2026-11-17 BTC total -239.9 USDm; 2026-11-18 issuer rows all blank, displayed 0.0 is NOT a completed zero.
SEC original https://www.sec.gov/Archives/edgar/data/2130357/000162828026074904/anthropic-sx1mef.htm filed 2026-11-18; Anthropic S-1MEF additional 178,250,000 Class A shares including 23,250,000 underwriter option; prior registration effective Nov18. This is issuer IPO filing, NOT confirmation of Kraken/Binance/Bitget/Bybit/Gate/OKX third-party allocation.
Reuters 2026-11-18 https://www.reuters.com/business/binance-says-it-has-court-order-get-back-crypto-frozen-after-63-billion-heist-2026-11-18/ ADGM court freezes assets at 18 firms linked to prior Binance theft, court procedural development; candidate security family binance_2026_oct29_heist, requires exact prior delivered material version comparison.
Reuters 2026-11-18 https://www.reuters.com/business/finance/after-63-billion-crypto-heist-binance-plans-foray-into-5-asian-markets-2026-11-18/ five prospective Asian markets, details expected Q1; source is reported company statement, not a confirmed license.

## QA
CODE_NOT_EXECUTED; CI_NOT_PROVEN; MANUAL_EQUIVALENT_ONLY incomplete.
Full seven-day Gmail body comparison, six security family original receipts, ETF ETH/SOL, original official X, whale txids, NFT/TGE original receipts and complete 13-chapter structured manifest were not completed. No full accurate 13-section candidate can be certified from these sources alone. QA_FAIL_NO_SEND. No Gmail attempted, no Sent ID. Do not claim delivered. This is a P0 unattended recovery failure; next original collector must continue rebuilding, never create a backup scheduler.
