# 2026-11-23 06:20 Asia/Bangkok collector — PARTIAL_SOURCE_GAPS

Status: COLLECTOR_PARTIAL; no email in 06:20 collector window; no QA or delivery claim. Official data checked around 2026-11-23 06:19:23 +07 (Binance response closeTime 1795389569xxx). Source discovery and editorial selection separate.

## Git rules SHA read from main
PIPELINE_CONTRACT 29ffbc1d32ca87a744d2990e8d55639ebb84a6f9
REPORT_SPEC 2e70414c8fdb8d23a292cc3bf7797425a403e179
Other rules EDITORIAL_RULESET.json, REPORT_ACCEPTANCE.md, COLLECTOR_SPEC.md, SECURITY_SOURCE_POLICY.md, DELIVERY_RUNBOOK.md and state/daily-event-ledger.json fetched successfully this run; full individual SHA not persisted in this short receipt. Re-read at 08:20.

## Binance official spot ticker, rolling 24h
Source: Binance connector get_spot_24hr_ticker_price_change_statistics(symbol), endpoint https://api.binance.com/api/v3/ticker/24hr ; checked_at 2026-11-23 06:19 +07; quote closeTime ~1795389569000 ms UTC.
BTCUSDT last 61090.00; 24h +1.361%; high 61669.99 low 58768.51, quoteVolume 1208412814.95 USDT.
ETHUSDT last 1723.74; +2.340%; high 1732.52 low 1648.35, quoteVolume 394592897.29.
SOLUSDT last 70.59; +0.398%; high 71.43 low 68.74, quoteVolume 135575737.80.
BNBUSDT last 558.38; +1.692%; high 560.57 low 536.85, quoteVolume 51334649.45.
HYPEUSDT last 62.73; +2.400%; high 63.37 low 59.57, quoteVolume 23597529.51.
Binance USD-M markPrice source https://fapi.binance.com/fapi/v1/premiumIndex; checked same time: BTC 61043.50 funding 0.00003552; ETH 1722.39 funding 0.00003899; SOL 70.53387441 funding 0.00002451. Mark/index are distinct from spot.

## Farside source receipts
https://farside.co.uk/btc/ checked 2026-11-23 ~06:20 +07, latest US session shown Nov20 2026 BTC net -124.5 USDm but IBIT cell missing (dash), therefore PARTIAL, NOT final full issuer flow. Nov19 total -582.3 USDm.
https://farside.co.uk/ethereum-etf-flow-all-data/ checked same time, Nov20 ETH total -13.2 USDm but several issuer cells missing; PARTIAL.
SOL ETF issuer/day data not independently validated: SOURCE_GAP.

## Legacy platform / security / other
Galxe original https://help.galxe.com/en/articles/18361711-galxe-is-integrating-into-gravity-what-you-need-to-know checked 2026-11-23 ~06:20 +07; original announcement Nov9 2026; Quest campaign participation Dec5, reward claim Dec15; Gravity L1 and G unaffected per issuer. Already sent separately and no new material_version confirmed; EXCLUDE repeated notification.
Laravel official https://github.com/laravel/framework/security/advisories checked same time; most recent visible Nov11 2026 two moderate signed URL advisories. No verified Nov23 delta, do not infer no vulnerabilities.
GitHub advisory documentation https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/fix-reported-vulnerabilities/browse-advisory-database checked same time; general guidance, NOT a sufficient independent six-family scan. Mark individual security families SOURCE_GAP pending original vendor checks.
Arkham https://info.arkm.com/research/ and Lookonchain https://lookonchain.com/ queried via public search around 06:20; results stale/irrelevant; onchain original TX and 24h completeness SOURCE_GAP. Exchange policy, SEC/Fed, Anthropic IPO venue official, ACTIVE mainnet, TGE, Early/NFT and security vendor six-family current-day verification incomplete SOURCE_GAP. X Browser authenticated session NOT VERIFIED; do not claim X scanned.
Cross-day dedupe: Gmail Sent search 2026-11-16 through Nov23 found Nov16-22 delivered reports; Nov22 ID 1a2034b8ca694f60, Nov21 ID 1a1fc4aa5080c3cf, Nov20 corrected ID 1a1f9b7f90744f4e. These are subject/ID evidence only; full body not read this collector turn. No repeat of Galxe Nov9, USDT Nov18 S&P same version, or Chainflip Nov21 without novel proof.
Candidates: routine market samples and ETF session update for 08:20; no independently verified new high-impact narrative candidate this bounded pass. INCLUDE routine market data; WATCH ETF incomplete; EXCLUDE Galxe duplicate. No claim of comprehensive source coverage.
