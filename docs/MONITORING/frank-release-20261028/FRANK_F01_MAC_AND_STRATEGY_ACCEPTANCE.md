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

## Final bounded live read-only trial proposal — separate authorization pending

### Pinned identity and refresh ordering

Preparation starts at PR232 `56d6d42b4b339dd99f8e1cc94d0ff680a37ae603`.
Use the subsequent race-only fix's exact final GitHub HEAD and static hashes,
recorded in its execution receipt. Old approval does not automatically cover new
bytes. Each refresh generation owns its DOM and timing writes only while latest:
old success after new 503 cannot resurrect signals, old 503 after new success
cannot erase them. A later genuinely new success may recover. This does not
make separate API reads an atomic database snapshot or cancel old HTTP requests;
existing source identity/freshness checks remain mandatory.

### Listener, control directory and fixed finish

Proposed listener `127.0.0.1:18767`, never 8766/8765. After separate approval,
check availability and STOP if occupied; do not kill another listener or silently
change port. Use fresh 0700 private control/log/browser directories outside all
production roots. Preserve exact source SHA and canonical paths locally only.

One observation, at most 30 minutes. The separate owner authorization must name
absolute end instant E in UTC and Bangkok. Start no earlier than E minus 30min,
refuse start at/after E, never extend E automatically. A foreground supervisor
owns/reaps the child process group, browser and listener using a monotonic
deadline no later than E. Interrupt/failure stops only these owned children.
No cron, launchd, recurring task or background monitor. An approval arriving too
late requires a new window. This plan has not started a live observation.

### Live input and DB/WAL/SHM boundaries

Derive existing production/control roots from fresh authorized runtime evidence,
not guessed paths. Use actual DashboardState GET functions and FrankReader with
live ledger/health and existing control SQLite/health. The trial harness sets
only control *read pointers* to existing inputs; construction and analysis scratch
stay in the new private control directory. Do not instantiate MissionMemeService,
ControlDB, Scanner, notifier, collector or worker. Do not copy/import D2 balances
for F01. Missing unrelated panels remain unavailable without fabricated data.

Source SQLite uses URI mode=ro, query_only=ON, existing busy timeout and bounded
request/process deadlines. Never use immutable=1 on a changing WAL database,
copy the main file alone, checkpoint, repair or create production sidecars.
mode=ro/query_only only prevent SQL writes; they are not complete proof against
SHM/read-mark/sidecar effects. Enforce macOS sandbox deny file-write* over the
ENTIRE verified canonical production and original control roots, including
forward.sqlite, WAL, SHM, health, policies, D2 and their parents. Only trial scratch
is writable. Minimal environment contains no RPC/provider/mail secrets; deny
outbound connections and permit the single loopback inbound listener. Verify
actual path resolution and policy before any live read. If a legitimate read
needs SHM initialization or the sandbox cannot enforce confinement, STOP; never
relax it or change production permissions.

Proof is OS denial, not unchanged mtime: the preparation's synthetic active-WAL
fixture read a committed WAL row, rejected SQL insert, denied O_WRONLY on main
DB/WAL/SHM, and denied new sidecar creation. Real roots/policy still need execution
preflight. Existing V1/Loop are legitimate writers, so changing production file
hashes/mtimes during observation are expected and cannot by themselves identify
trial writes. Do not assert global production immutability while producers run.

### GET-only port, CA explicitly disabled

Stock Handler cannot be exposed unchanged because it has functioning POST routes.
A trial-only wrapper delegates to real Handler.do_GET solely for exact reviewed
paths/queries needed by this page: root/static, runtime, control-health,
candidates, follow-opportunities, trades, coverage, decisions, review-activity,
and bounded indexed activity/watchlist reads. Deny all cluster-* GETs, unknown
paths and unreviewed query parameters. No CA job/status/report operation is in
scope. Preserve exact local Host/same-origin checks, no CORS.

Reject POST/PUT/PATCH/DELETE/CONNECT/TRACE/OPTIONS with 405 and connection close
BEFORE body parsing, stock dispatch or any worker lookup. Browser blocking of
non-GET/external requests is secondary defense; server rejection also protects
against a direct client. CA controls are visibly unavailable in the trial.
Synthetic Quick/Standard/Deep POST-shaped requests were independently tested
against this wrapper pattern: 405 each, zero worker delegation; they were fixture
requests, not real CA submissions. Full live allowlist wiring and outbound-denial
profile must be verified in a bounded synthetic preflight before authorization
is used; this document is not a completed production launcher.

### What the page can prove

Separate all locally indexed Frank BUY/ADD/REENTRY activity from F01's qualified
subset: Frank identity, verified frozen source signal, OPEN model state, allowed
pattern, newest BUY within 600s, LIVE runtime and matching cross-GET identities.
The bounded D1 recent activity is not a full-chain BUY denominator. OPEN does not
prove current wallet holdings. Nonqualified buys remain activity/history.
Execution eligibility stays zero/empty; no default amount, quote or tradeability.

Use actual page memory first-seen logic only for F01 identities first observed
after page opening and whose event time is after opening. Record private salted
event key, chain event time, first page time, window/age/remaining600s, errors,
clock uncertainty and tab suspension. No raw addresses/signatures on GitHub.
This is confirmation+indexing+polling+display delay, not measured ingest latency,
notification SLA or fill speed. It does not sample every Frank BUY. Reload resets
samples; never merge them as continuous. No new event is NOT_SCORABLE; a source
older than600s stays historical. No window relaxation, ROI or win-rate claim.

### End, cleanup and stop conditions

Stop at E, on user interruption, identity/source drift, stale required feed,
sandbox/read failure, forbidden request attempt or unsafe current-signal display.
No automatic scan/restart/repair. Close/reap only owned listener/browser/children;
verify trial port no longer listening and existing service identities/configs
untouched. Do not use DB mtime as a no-write proof. Remove temporary profile and
source-derived trial files, or retain private evidence0700/0600 under an explicit
retention decision. Cleanup uncertainty is UNVERIFIED and blocks another run.
Publish only source/policy hashes, counts, timing limits and errors. No deployment,
merge, real RPC, new scanner, notification or trading authorization follows.
