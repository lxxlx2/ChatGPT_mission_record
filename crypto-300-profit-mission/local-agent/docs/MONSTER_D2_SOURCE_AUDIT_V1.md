# Monster D2 official source audit — FM3

Audit is source capability evidence, not a D2 performance PASS. All calls were public read-only Binance endpoints; no account or trade endpoint was used. Raw responses and official SHA256 sidecars are private.

Actual probes returned data for current open interest, recent OI history, taker ratio, global ratio, top-account ratio and top-position ratio. BTCUSDT REST requests targeting January2021 returned four funding records and two mark/index bars each. A successful BTC probe does not establish coverage for every historical candidate. Five REST statistical probes explicitly targeting2021 (OI, taker, global, top-account, top-position) each returnedHTTP400; the error receipts are preserved separately from successful archive evidence.

The current official REST documentation specifies short rolling retention for statistical endpoints including basis and OI statistics. These REST routes are therefore FORWARD_ONLY for the2021–2024 study; archived equivalents need separate coverage checks. [Official USD-M market-data documentation](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data).

| Evidence | Actual official archive probe | Classification |
|---|---|---|
| OI, OI delta | BTCUSDT daily metrics2021-01-01 and2024-01-01 checksum verified | HISTORICAL_CAPABLE through archives; coverage audit required |
| Global/top account/top position ratios and taker ratio | Those fields present in both verified metrics ZIP headers | HISTORICAL_CAPABLE through metrics; REST short-history route remains FORWARD_ONLY |
| Funding and funding delta | BTCUSDT monthly fundingRate January2021 checksum verified, header plus93 records; targeted REST also returns2021 records | HISTORICAL_CAPABLE for verified intervals |
| Mark/index basis | BTCUSDT monthly markPriceKlines and indexPriceKlines January2021:744 bars each, checksum verified | HISTORICAL_CAPABLE via aligned actual bars; current REST basis is FORWARD_ONLY |
| Spot/futures divergence | Separate official1h candles in expanded universe | HISTORICAL_CAPABLE only with verified same-entity and aligned venue bars |
| Path count, persistence, quote volume, prior observed spikes, verified age | Frozen causal features and lifecycle | HISTORICAL_CAPABLE, no derivatives retention dependency |
| Current order-book liquidity / current-only snapshots | No historical order-book dataset audited here | FORWARD_ONLY; hourly quote volume is only a liquidity proxy |

Metrics2021 sample contains576 rows at288 timestamps:288 duplicate rows are byte-equivalent field records, with zero conflicting timestamps. Exact duplicates may collapse once; conflicts must reject. The2024 sample has288 unique timestamps. Timestamp availability alone does not establish when a metric was published: any historical enrichment must use a conservative completed-period observation boundary and document it. No2026 timestamp convention is projected backwards without verification.

Official public-data files support monthly/daily archives and accompanying checksums; that publication mechanism was verified by actual ZIP reads. [Binance public-data repository](https://github.com/binance/binance-public-data). OI/ratio archives therefore cannot be declared unavailable merely because the corresponding REST route has limited retention. Conversely, a single successful archive sample is not full-universe coverage proof.

D2 shortlist search and D3 remain conditional on D1 V2 gates. Priority scores describe anomaly evidence only, never buying probability or investment merit.
