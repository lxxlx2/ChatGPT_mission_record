# Frank D2 Dashboard-only predeploy preparation — BLOCKED / R2 COVERAGE_LIMIT

Authority: [PR178 R1/R2 handoff](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6382980574). Full fixed plan read: [plan-only42ccc55d](https://github.com/lxxlx2/ChatGPT_mission_record/blob/42ccc55da850b701be395df2f62e2aaa5fadc901/docs/MONITORING/frank-release-20261024/FRANK_D2_DASHBOARD_ONLY_RELEASE_READINESS_20261024.md).

**Outcome: R1_PASS / R2_COVERAGE_LIMIT_BLOCKED / DEPLOYMENT_NOT_AUTHORIZED.** No product-source defect demonstrated by this browser-launch failure; no readiness PASS or cutover performed.

## Fixed source and full candidate package — R1 PASS

- Product source: **`914e9e47fed2e60bc24690fcb083413a64d4e681`**, not the plan-only SHA. Original PR178 remains `ea9a7715beb4d2a55ae956bf993828cbddcb50e5`; PR60/174 HEADs checked against frozen references. Candidate research branch HEAD matched. Clean isolated detached source, no main workspace branch switch.
- Exact installed PR168→candidate range independently confirmed **43 stacked commits /17 changed files**. Five runtime files: server.py, app.js, index.html, wallet_d2_ingress.py, wallet_owner_at_slot.py. CLI entry, generic installer and styles.css blobs unchanged. Runtime old/new blobs recorded in r1-result.json. Installer was **not run**; it would affect Loop as well as Dashboard and is prohibited here.
- Exported full Git local-agent tree into a **separate temporary, read-only446-file package**, not production release root. Every filename/content hash and executable bit verified. Git executable bits retained; file modes deliberately readonly0444 or0555, directories0555.
- Complete manifest contains sorted relative filename→{sha256,git_mode}. Canonical JSON is UTF8/json.dumps(sort_keys=True,separators=(',',':')). **Manifest SHA256 `9a06f5f29fce05ccade8caa2b90d6d6c0c4248d2e6ab4e45aa26fa9d3f401062`**. This is neither tar hash nor the old437-file manifest. Package all446 bytes/executable bits/read-only modes rechecked unchanged after the attempted browser stage.
- With the **existing actual runner virtualenv Python3.14.7**, import-only loaded packaged server/reader and CLI entry under macOS process-level network denial, all writes denied and `-I -B`. Verified `server.query_d2 is wallet_d2_ingress.query_d2`, approved `SOURCE_SUBDIR=frank-d2-private`, filename, and CLI serve binding. No DashboardState, FrankReader, ClusterJobManager, scanner, Worker, SQLite or service instance constructed. No new daemon/dependency installed.
- Current Dashboard runner, live cwd/args and unique8766 listener independently matched installed PR168 `656ed2c96f4210d106d7b1129ec6cf8d7c4586f3`; all437 installed files and approved runner hash matched. Current protected Dashboard/Loop/V1 identities were captured privately and compared again at closeout: unchanged.
- Existing imported data was accessed **only through stat/hash**, not parsed/copied/replayed: shared0755/child0700/file0600,893189bytes, SHA256 `d24d73d13a5ab9740eed7d1f06a6226aa9650004ccd756458b579c9e2ee2e284`. Hash/modes unchanged again at closeout. No exporter or original Oct23 raw receipt access.

## Browser/source smoke — R2 BLOCKED before page creation

A single fresh isolated Chrome-profile launch was attempted. Planned harness used original readonly static assets, a synthetic private-child source and original Handler.do_GET via stdin/stdout pipe, with browser request interception rather than any HTTP listener. Python bridge disabled socket bind/connect; Chrome was launched through the following hard-deny wrapper:

```sh
sandbox-exec -p '(version 1)(allow default)(deny network*)' [existing Chrome executable] [Playwright args]
```

**First failing gate `R2_BROWSER_LAUNCH`: `CHROME_UNIX_SINGLETON_BIND_DENIED`.** The existing Chrome executable aborted with exit21 because macOS denied `bind()` for its ProcessSingleton **Unix-domain socket**. Playwright's generic “profile already in use” title was misleading here: profile was newly created, and the underlying actual error was `Operation not permitted` at Unix SingletonSocket bind. Private transient paths/PIDs/full command log are deliberately not uploaded.

This was Chrome's own local IPC socket requirement, **not** a new TCP HTTP port. No test HTTP server/proxy/listener was created. Request-interception transport could not be exercised because the browser exited before a page existed.

Per the fixed plan, **COVERAGE_LIMIT and STOP**: did not weaken sandbox to permit Unix sockets, relaunch Chrome, start a temporary HTTP fixture, or replace product functions to manufacture PASS. No retry and no socket/port fallback.

|R2 case|This run|
|---|---|
|Manual click / initial D2GET0|NOT_TESTED: no page created|
|Page0 / page41 / previous|NOT_TESTED|
|Exact Mint / observed zero vs absent / invalid Mint|NOT_TESTED|
|Oct23 Bangkok timestamp / both slots / non-atomic labels|NOT_TESTED|
|Late request race|NOT_TESTED|
|Missing/corrupt source / HTTP and JSON errors|NOT_TESTED|
|Original signal/intelligence / CA Quick/Standard/Deep controls|NOT_TESTED|
|Original Handler→synthetic reader bridge requests|0; bridge initialized synthetic source only, no request dispatched|

No screenshot or DOM evidence exists for this run. Empty console/page-error lists do **not** prove browser success because no page was created. Historical55Python+6JS tests remain prior unchanged-code evidence only; none rerun here. Existing CA faults or full CA accuracy are not claimed fixed.

## Closeout, release limitation and next decision

Fresh profile removed; isolated Chrome exited and no matching test Chrome remained; pipe bridge exited, synthetic directory removed. Temporary readonly package and clean detached/evidence checkouts removed after reporting; full scalar/hash manifest retained. Original private imported source retained unchanged; services/runner/plists/ports not modified. No production GET, browser, SQLite, private raw/exporter or actual source JSON ingestion. No new PR or product-source edits.

`PROD_WRITES=0 / NEW_TCP_LISTENERS=0 / NEW_TEST_HTTP_PORTS=0 / NEW_RPC=0 / PROD_HTTP_GET=0 / EXPORTER=0 / RESTARTS=0 / DEPLOYS=0 / MERGES=0 / NOTIFICATIONS=0 / TRADES=0 / PORT_CHANGES=0`.

`G03B_INTERPRETER_ORIGIN=UNRESOLVED` remains a **future release qualification**, not converted to production binary identity PASS by import-only success. The local custom-header/Host guard is a browser barrier, not authentication against arbitrary local processes. Existing installed PR168 still does not expose D2 UI/route; no deployment consent exists.

This run stops with **MAC_D2_PREDEPLOY_READINESS_BLOCKED / R1_PASS / R2_COVERAGE_LIMIT**. Remaining proof is bounded real-browser candidate rendering under an independently accepted **no-TCP-listener** sandbox/IPC arrangement. That arrangement must explicitly address Chrome's Unix-domain singleton requirement without enabling external traffic or changing product source. It was **not** attempted or assumed approved in this run. Real production HTTP/UI and a future single Dashboard-only restart still require separate owner release authorization; no automatic continuation.

Attempt ended UTC: `2026-10-24T10:20:39.568Z`.
