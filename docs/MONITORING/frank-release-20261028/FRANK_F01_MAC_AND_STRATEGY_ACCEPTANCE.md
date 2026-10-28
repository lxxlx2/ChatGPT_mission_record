# Frank F01: actual Mac acceptance and profit-research boundary (2026-10-28)

Status: CODE_ONLY. No authorization for production change, launchctl, runner/plist change, new cron, RPC, private GET, mail, CA POST or trading.

## Frozen authority

- G1 architecture PR #114; F01 candidate PR #232 based on approved product PR #220. Changed HEAD requires fresh independent code review.
- This is a source-only local read UI: no default investment size, executable route assessment, trading entitlement, auto-follow, or guaranteed current on-chain holdings. eligible_count remains 0.
- G0-B research, live observation/notification changes and F3/V1 legacy provenance adaptation require separate owner approval.
- Do not replace the old 446-file Mac product with this branch alone; first build a precise combined product source set and independently verify F2/F3 release/restore binding to new product and protected legacy V1.

## Source clocks

- latest_buy_at and latest_at originate from Solana blockTime and mean event time (UTC epoch seconds), NOT index-ingest time.
- source_window_seconds is 600, based on chain event time. Any newly indexed BUY older than 600 seconds remains historical/unverified; never promote it just because the browser saw it for the first time.
- Existing FrankReader candidates do not include verified first-indexing timestamps. API returns index_ingest_timestamp_status UNAVAILABLE_IN_EXISTING_CANDIDATE_SCHEMA and index_ingest_latency_seconds null.
- Browser event-to-first-observation sample is recorded in ephemeral page memory ONLY when browser started before the source event. It includes confirmation/indexing/polling/display delay, not pure index delay, notification latency, or fill speed. Refresh resets the sample. Preexisting events are excluded as left-censored.
- If no new event appears during the observation window, timing performance is NOT_SCORABLE, never zero-latency or known-good.

## Actual Mac acceptance (separate isolated READ-ONLY authorization required)

1. Pin the reviewed product SHA and exact source file set. Validate separate F2/F3/restore plans; do not change current services without specific owner authorization and rollback.
2. In an isolated read-only environment verify F01 schema2 GET endpoint, eligible empty/zero, no default quote/RPC, and production SQLite opened only read-only.
3. In an isolated browser, verify latest signed BUY with valid Frank frozen signal and LIVE model state appears as observation only; historical BUY/WAIT, SELL/EXIT, CLOSED, missing signal, overlay and stale events remain in history. Negative/cross-GET mismatches remain fail-closed.
4. Preserve D1 ledger, D2 provenance, existing watchlist and CA research independently; ensure no duplicate CA POST, new notification or trade.
5. With an already-open observation page, capture real post-open Frank BUY block time/signature and first page observation time. Record event age, 600-second window remainder, any first-seen older than 600s and local clock health. No invented full-chain denominator.
6. If measured first observation exceeds 600 seconds, declare freshness failure and diagnose separately authorized indexing/performance instrumentation. Do NOT loosen 600s simply to show a recent signal.
7. Do not infer ingestion time without a reliable persisted ingest timestamp and specific authorization for adding it. One sampled episode is not an SLA; multiple independent episodes are needed.
8. Release gate rejects false actionable BUY, unsafe error messages, stale source promotion, unverified model balance displayed as confirmed on-chain, broken secondary panels, notification regression, unsupported runner/product identity or missing recovery evidence.

## Profitability research is a separate G0-B / G4 gate

- Product read-only release is not conditional on a positive trading PnL; strategy remains NEED_MORE_DATA without independently verifiable follower outcome.
- Preregister the success criteria, fees/impact assumptions and entry/exit rules BEFORE independent outcomes, and count episodes as independent units, NOT raw BUY transactions.
- Use delay ladder 30/120/300/900/3600s with executable entry/exit evidence, actual liquidity, price source coverage, fees, impact, failed routes, exit latency, outliers and sensitivity bounds. Historical Frank payment price and OHLCV are not assured executable follower quotes.
- No lookahead, no post-hoc threshold selection, no unapproved amount defaults, no unsupported out-of-sample label, and no paper-PnL claim from unverified fill proxies.
- New RPC/market-data collection, notification, longer monitoring or trading require separate consent and resource budget.
