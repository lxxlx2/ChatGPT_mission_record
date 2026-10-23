# Frank G2 entry — source-to-notice timing and minimal D-layer integration dependency audit

Date: 2026-10-19 Asia/Bangkok  
Status: **READ_ONLY_SOURCE_AUDIT / DEPENDENCY_MAPPING_COMPLETED / G2_CODE_NOT_STARTED / NO_DEPLOY**  
Owner: GPT (A/C2 observational audit + D integration dependency mapping); independent code review: Claude or third party.  
Main inspected: `4e2bf056438830cf69a171d30474fdf489dd93f0`.  
Architecture authority (approved **content**): `e4d61d1c8f246a7b04ea46ba674855346625a243`; G1 metadata-only freeze: `3072ebda80c98c1912447a704b3c29f227c3dd96`; user approval [PR #114 comment](https://github.com/lxxlx2/ChatGPT_mission_record/pull/114#issuecomment-6271276885). PR #114 remains Draft/unmerged; cite the approved content SHA rather than claiming that file is on main.

**Work performed**: exact-ref remote GitHub source inspection and existing checked-in JSON parsing only. This report is a *new audit and delivery dependency result*, not a runnable D1/D2/F01 integration, a live Mac timing experiment, a source completeness certificate, or a trading strategy GO. No RPC, Alchemy/Jupiter call, live database access, Git merge, new LaunchAgent, production config, email, user Mac, transaction or paid API operation.

## A. Verified runtime time-path; why poll=30s is not SLA=30s

**Existing chain of evidence**:

1. `local-agent/scripts/frank_local_signal_service.py` initializes one enabled Frank registry, durable `forward.sqlite`, scanner, Engine and local notifier. It reports `poll_interval_seconds=30`; this does not prove 30-second event-to-user notice.
2. `mission_agent/signals/scanner.py:23-62` loops finalized signatures from durable cursor; writes `signature_detections(wallet,signature,slot,block_time,seen_at,state)` with `RAW_PENDING`, persists fetched raw transactions, invokes frozen classifier and marks `CLASSIFIED_DURABLE`; cursor gaps fail closed.
3. `signals/store.py:32-37,116` has `signatures.block_time/seen_at/classified_at`, `trades`, `signals.created_at`, `outbox`. **Do not assume similarly named timestamps all reflect wall-clock processing time.**
4. `signals/engine.py:115-132`: `watch_tick(last)+3600` and `'HOURLY_29'` evaluate some MULTIPLE persistence by hourly ticks. `engine.py:134-178` also evaluates on actual recognized ACTIVE_TRADE events. **Hypothesis**, not observed result: eligible signal timing can be bounded by scheduled evaluation rather than scanner polling when no new ACTIVE event triggers an earlier decision. Frozen V1 engine/policy must not be retuned to “fix latency” before timing + value assessment.
5. `signals/engine.py:80-104` writes signal `triggered_at` and the `signals.created_at` value from the evaluation `at` clock (`INSERT INTO signals ... str(at)`). This is **not an independently captured actual signal computation wall-clock timestamp**; subtracting `block_time` from it must not be marketed as processor latency.
6. `signals/delivery.py:24-49,52-69` local OS notification receipt has `accepted_at` and `COMMAND_ACCEPTED`. That proves command acceptance, **not actual GUI arrival/read by user**. Mission Control local and Gmail are separate delivery authorities; `mission_control/db.py` and `mission_control/delivery.py` store their own decision created, outbox created, command acceptance or provider Sent/readback states. Gmail `SENT_VERIFIED` is provider proof, not inbox/display latency.
7. `mission_control/service.py:183-204,268-301` filters decision transitions before enqueue. Thus **source signal existence, derived decision, enqueue, OS command accepted, and verified Gmail Sent are distinct events** and must each be counted separately.

### Current timing verdict

| Metric | Existing source | Can we already claim it? |
|---|---|---|
| Finalized chain block time -> scanner first seen | raw `block_time`, `signature_detections.seen_at` | **Possible for existing recorded signatures**, but no live Mac DB was read this round; blockTime is chain timestamp with resolution/bias, not exact slot finalization time |
| First seen -> classified durable | `signatures.classified_at`, detection receipt where joined | **Potentially measurable**, needs timestamps and explicit join on wallet/signature |
| Classifier durable -> actual signal computation | `signals.created_at` is evaluation clock, not processing wall time | **NOT_VERIFIED**; never mislabel hourly evaluation timestamp as compute latency |
| Signal creation -> local command accepted | `outbox` + local receipt `accepted_at` | **Only partially observable** until signal computation wall time is captured; receipt may prove command acceptance |
| Source event -> actual visible Mac notification | OS UI observation required | **NOT_VERIFIED** |
| Source event -> Gmail Sent verified | Mission Control decision/outbox + Gmail readback | **Separate decision authority**, not equivalent to V1 local source signal or to user inbox visibility |

**Next scoped timing acceptance (not executed):** on user-approved Mac read-only evidence, exact wallet/signature/episode join for naturally occurring Frank events, capture chain slot/block_time, detection, local classified time, active/hourly evaluation type, signal/decision identifiers, local command-accept receipt and Gmail readback when already authorized. Report per-stage coverage and p50/p90 or individually observed lag **only if enough natural events exist**. Do not manufacture a “3 real trades” test, fake a notification, modify frozen engine, send new Gmail, change permission, or add a permanent process. If no fresh qualifying signal occurs, state `NO_REAL_SIGNAL_OBSERVED`, not false failure/pass. For actual on-screen arrival, an explicitly authorized finite Mac observation is required.

## B. D-layer source inventory (exact PR heads checked)

| Source | Fixed head | Actual reusable unit | Integration caveat |
|---|---|---|---|
| `main` Dashboard | `4e2bf056438830cf69a171d30474fdf489dd93f0` | Existing GET `/api/runtime`, `/api/candidates`, `/api/frank-observed-watchlist`, `/api/trades`, `/api/coverage`, `/api/review-activity`, `/api/decisions`, `/api/cluster-latest` | Source `server.py:854-894` contains **no** `GET /api/follow-opportunities`; earlier real Mac returned 404. HTTP 404 means **API not installed**, not zero opportunities. |
| PR #111 | `47278b621066f38279cea3feac00463becc24137` | `scripts/frank_d1_activity_ledger.py`: private searchable **standalone HTML** from real indexed `forward.sqlite` via `mode=ro`; exact wallet-signature trade join; tests | **Preferred D1 activity display basis under G1**, but not a current built-in Dashboard route or proof of unindexed/full-chain history. Preserve independently useful PR #109 2-BUY source-to-signal audit; do not develop a second competing activity ledger. |
| PR #110 | `57c2e0f02a559cc2ac9064ea36e3031442fa075f` | `scripts/frank_d2_dated_holdings_preview.py`: standalone searchable observation HTML, reconciles existing local watchlist GET with Oct11 32-mint dated evidence | **Preview, not fresh full-wallet holdings**; 32 dated verified cases do not imply current 937-token inventory verification. No automated balances or new RPC authorized. |
| PR #93 | `d14eb7c1a910c79f79cee216ca6f9aae47e3db02` | `follow_view.py` partition/same-source guard + actual GET F01 handler in `server.py` at ~953 | **Do not cherry-pick entire stacked PR**. Current F01 `_reason()` explicitly requires `decision` BUY/SMALL_BUY, an OK size-dependent quote, fresh quote timestamp and executable impact; incompatible with amount-unset #112 semantics without a deliberate product contract. |
| PR #101 | `e8bc450d836ac46df5224ce7b6fc048ea5720db0` | Static current-vs-history display partition and anti-stale guards | Built on stacked PR #94, which presumes fixed execution amount; reuse presentation idea only, not stale amount-dependent action badges or branch history. |
| PR #49 | `8898134a8a302e1187138f7fb3da87a554567e6d` | `mission_agent/meme/identity.py` read-only exact Mint, Token-2022 vs Metaplex metadata reconciliation, case-only label normalization, tests | `identity.py` **absent from main**; PR #49 is child of unmerged #47 and modifies server and app.js. Isolate *minimal* C02 identity dependency; no full chain/sidecar transplant. Any fresh CA RPC invocation needs approval under the applicable authorization. |
| PR #106 | `8a8b4fcc36242c0ba03b03170225f723d847fa53` | Degradation of `/api/decisions` GET to 503 should not mask 7 unrelated live widgets | This is a bounded UI correctness idea; unconfirmed server root cause must not block unrelated business features or trigger new screenshot loop. |
| PR #112 | `dc41f2c4178b656806bdb4bd992111d7db7588bd` | Removes **unapproved fixed $30** assumption in policy, quote, CA, UI and wording | **Release blocker**: `service.py:129` returns `SKIPPED/USER_ORDER_AMOUNT_NOT_SPECIFIED`, but `policy.py:109-119` quote-unavailable => `WAIT/CRITICAL_DATA_INCOMPLETE`, then `service.py:193-206` suppresses transient WAIT notification before `enqueue()`. Current V1 local source signal is separate, so **actual notification loss on Mac is not claimed**. Also `delivery.py:90` mislabels a genuine high-impact quoted decision as missing amount. Existing policy hash invalidated. |

### Minimal dependency graph and sequence

```text
Main current deployment (retain; no forced process merge)
  ├─ Source facts and C2 frozen signals (unchanged)
  ├─ D1: #111 source --> reusable read-only activity projection --> existing Dashboard
  ├─ D2: #110 reconciliation --> dated watchlist views --> existing Dashboard
  ├─ F01: #93 validated-source logic --> choose display-only current *source signals*
  │        vs genuine size-dependent *executable follow decision* as distinct states
  ├─ C02: #49 exact CA identity reconciliation --> reuse existing cluster/CA API
  └─ #112: independently correct size-dependent Decision/notification handling
             before any combined release
                   ↓
       One bounded integration regression and user-approved Mac acceptance
```

**Priority & separation**: PR #112 notification safety is a **blocking compatibility check before a combined live release**, not a reason to halt read-only D1/D2 development. Complete D1/D2 provenance-first integration where possible; scope F01 status semantics separately, retaining fail-closed against a fake “executable BUY”. Integrate C02 only after existing exact-Mint semantics/tests survive source extraction. Combine one final Mac read-only functional acceptance across D1/D2/F01/C02/notifications, not repetitive screenshot harnesses.

**F01 design decision that requires implementation specification, not a new strategy**:
- `SOURCE_SIGNAL_OBSERVED` can truthfully show a recent frozen Frank ACC/MULT event, with provenance and state, **without calling it an executable BUY or giving a trade amount**.
- `EXECUTION_ASSESSMENT_NOT_AVAILABLE` when amount-specific route/impact is not verified; `ELIGIBLE_EXECUTABLE` must remain unavailable unless independently justified with explicit user-defined parameters, source receipt and separate authority.
- `API_UNAVAILABLE` / `STALE` / `NO_SIGNAL` must be distinguishable; zero candidates is supported **only** by a successful fresh source query. Archived WAIT/NO_BUY cannot masquerade as live BUY.

This is a **proposed presentation contract**, not a claim that existing F01 code already implements it. No new signal threshold or recommendation is implied.

### Write-conflict map

The same production `mission_agent/mission_control/server.py` is touched by #49, #93 and #112; `static/app.js` by #49, #101, #106 and #112. Their stacked bases and implicit execution assumptions differ. **The full old branches cannot be merged together without reconciliation**.

Owner for A/B changes and D integration is GPT-controlled; only one writer edits a particular production path at once. Original #112 author may fix its existing PR and is not authorized to simultaneously change a new integrator branch. Independent reviewer is Claude / third party. Existing PRs stay Draft, open and unmodified in this mapping round. Approval of G1 did **not** authorize changing runtime configuration or size-assumption semantics.

## C. G0-A offline input handoff to Claude (not C1 implementation)

**G0 ownership remains Claude**. This section is only the bounded input/source list and unmet measurements for parallel execution—not an independent backtest or a second researcher overwriting Claude's files.

Checked-in `meme/evidence/frank-trade-coverage-sol-usdt-complex-2026-10-04.json` (blob SHA `a31a2bbcd1fe7c70951152f2a23edca6c934dc40`) parses as:
- 6,874 verified historical signatures, 2026-09-03–2026-09-30, `AVAILABLE_VERIFIED_SUBSET_NOT_WALLET_LIFETIME`; baseline J0 634 ACTIVE_TRADE, **including BUY+SELL**; passive 4,433, ATA 265, FAILED 900, UNKNOWN 642.
- The archived SOL-quote 9 ACTIVE transactions are SELL and **zero BUY**; baseline quote assets 625 USDC / 9 SOL. **USDC 625 is not the count of BUY events**.
- Archived M3 model has 653 ACTIVE (some recovered by research), **32 signal records = 22 ACC + 10 MULT**, across **22 episode IDs and 18 distinct Mint IDs**. Historical emitted ACC/MULT **signal records** are not 32 independent strategy trades or 32 actual sent notifications; the 22 observed signal episodes are not proof of complete wallet history.
- Existing SOL-USD Coinbase minute price receipts and earlier third-party GeckoTerminal/TWEETCRAFT pool proxy experiments cover only a small portion of followability. No verified all-event delayed-executable price series.
- **G0-A first deliverable**: exact unique `ACTIVE_BUY` count and `ACTIVE_SELL` count under J0 and M3, citing per-signature classified trade direction; episode map and group denominators; priced/missing coverage by mint/episode/delay/source; existing price source inventory; prior/OOS leakage and survivorship hazards. Do not infer BUY from aggregate 634/653 counts.
- **G0-A RPC permission gate**: first work from available verified raw/SQLite/archives and cached provider responses. Before **any new live chain RPC or third-party price API collection**, submit `provider + exact method/endpoint + maximum requests + retry ceiling + expected cost + stop condition + which missing data it will resolve` and receive user **collection-specific approval**. No automatic paid upgrade, hidden second API key or unbounded 429 retry.
- **G0-B**: after exploration, freeze separate numerical gates, episode-unit sampling, exit rules, price kinds, delay ladder and independent validation plan **before** its outcomes are seen. If no independent OOS data, verdict `NEED_MORE_DATA`, not forced GO.

**Task interface to Claude**: write its own G0-A exact-input/coverage report and any code only to **a separately owned main-based research branch/PR**; do not edit this D audit PR, `mission_control/server.py`, `signals/engine.py`, or #112. Cross-check source/model distinctions with the G1 approved content SHA.

## D. Next gated work, measurable exits

| Step | Owner | Output | Boundary |
|---|---|---|---|
| G0-A existing-evidence inventory | Claude | BUY/SELL and episode denominators, price/cache inventory, missing table, targeted RPC authorization proposal if truly needed | No new RPC without explicit per-pilot permission |
| D mapping/time-path audit | GPT | **This exact document**, verified main/PR paths, no assumed Mac performance | Completed source-only, no user Mac/P1+ code changed |
| D1/D2 read-only handoff | GPT + current PR author | Confirm #111/#110 outputs can be integrated with existing endpoints without inventing holdings/freshness | New code work must use G2-owned branch, focused tests, independent review; no runtime permission assumed |
| #112 decision/notice compatibility | Original author under GPT integration coordination | Correct absent-amount vs high-impact reasons, no valid source fact lost, release SHA + regression proof | Remains BLOCKED; no silent reauthorization of changed policy |
| F01 current-vs-executable contract | GPT | Minimal source-based API/presenter and explicit unavailable/stale/no-signal statuses | No $30 default; no false actionable BUY; source-proof tests required |
| Actual event-to-notice timing | GPT, user-approved Mac read | Natural-event source/detection/classification/evaluation/enqueue/command-accepted evidence; precision/coverage and clock limitations | Do not conflate synthetic tests with real UI arrival, no new notifier/mailer |

**G2-code, G3-deploy, G0-B strategy verdict, and product GO remain NOT_STARTED / NOT_APPROVED by this report.** Initial next step is owner-specific offline work, not user-side deployment.
