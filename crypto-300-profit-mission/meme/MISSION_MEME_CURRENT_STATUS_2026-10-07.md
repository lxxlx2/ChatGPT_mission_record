# Mission Meme current status — 2026-10-07

Timezone: Asia/Bangkok

Status: `MAIN_MERGED / LOCAL_RUNTIME_PENDING_REFRESH / LIVE_NOTIFICATION_EXISTING_STACK / PRODUCTION_TRADING_NO_GO`

This file is the current operational handoff for the Frank/Meme lane. It supersedes older review-only wording for current runtime state, while older reports remain historical evidence.

## 1. Current production shape

Frank production remains the deterministic source of chain facts and frozen V1 pattern state.

```text
Frank production
  health.json
  forward.sqlite [READ ONLY to Mission Control]
        |
        v
Mission Control
  FrankReader
  Jupiter official /swap/v1/quote
  FOLLOW_POLICY_V1
        |
        +--> mission-control.sqlite
        +--> localhost Dashboard
        +--> macOS local notification
        +--> Gmail
```

No wallet signing, swap construction, transaction sending, or automatic trading is authorized.

`PRODUCTION_TRADING = NO_GO`.

## 2. Current live functions

Implemented and in main:

1. Frank runtime health/read-only production DB checks.
2. Frank `ACCUMULATION` and `MULTIPLE` episode/position reading.
3. `REENTRY_WATCH`: a confirmed CLOSED -> REENTRY episode enters observation immediately, but remains WAIT-only until the frozen signal model independently reaches ACCUMULATION/MULTIPLE.
4. Jupiter executable quote check using the official quote endpoint, keyless or keyed.
5. Deterministic follow decisions: `BUY / SMALL_BUY / WAIT / NO_BUY`.
6. Chinese localhost Dashboard.
7. Full CA display + copy, Solscan links, readable Frank actions and decision reasons.
8. Closed positions leave the primary candidate area and appear only in recent-ended UI history.
9. Separate `mission-control.sqlite` audit DB.
10. 60-day `follow_observations` retention.
11. Durable decision snapshots/events/outbox and Gmail delivery receipts.
12. Live macOS + Gmail notifications for notification-eligible fresh Decision transitions.
13. Historical backlog suppression; enabling live delivery does not replay stale alerts.
14. Gmail Sent readback / ambiguity handling / dedupe.
15. macOS LaunchAgents for Mission Control loop and Dashboard.
16. Approved policy SHA256 pinning.
17. LaunchAgent runtime policy is copied to `~/Library/Application Support/FrankMeme/follow_policy_v1.approved.json` to avoid macOS Documents/TCC denial.
18. Existing Frank production LaunchAgent remains separate and is not modified by Mission Control.

### 2A. Meme local tooling v2 — merged to main, local runtime refresh pending

Merge commit:
`2f83be332e2c20270a3f534e333f1a19ea8b6bc5`

The following functionality is now in `main`:

- independent forward outcome tracking with executable Jupiter entry/exit quotes;
- fixed T+5m / T+15m / T+1h / T+6h / T+24h horizons;
- 5-minute sampled MFE / MAE / max drawdown plus monthly grouped statistics and Ex-Top robustness;
- live SOL-quoted Frank normalization in a separate sidecar DB, while keeping production Frank read-only and the frozen Frank evaluator unchanged;
- a free local Solana wallet-cluster engine and a tabbed `CA 链上查询` view inside the same Dashboard;
- Chinese trading-oriented Mission Control notification content.

Pre-merge review is complete (`738 passed` on feature code head `b6f26499`). The code is now merged to `main`, but the user's Mac is still running the previously installed local checkout/LaunchAgents until it is explicitly synchronized and restarted. Do not claim the new CA-query/outcome/SOL-sidecar code is live before that local acceptance.

## 3. Current approved follow policy

Runtime policy:
`config/follow_policy_v1.approved.json`

Required live gate:
- `status = FROZEN_APPROVED`
- `live_delivery_approved = true`
- runtime CLI `--live-delivery`
- exact approved policy SHA256 match

Approved policy SHA256 observed in the 2026-10-07 local acceptance run:

`355336f2959e674939210b51be97d2df1d6e66f4ee3cca8acfe041dabb9e3ae8`

Key current thresholds:
- quote size: 30 USDC
- latest Frank buy max age: 600s
- BUY: MULTIPLE + deviation <=8% + impact <=1.5%
- SMALL_BUY: ACCUMULATION/MULTIPLE + deviation <=20% + impact <=3%
- observation retention: 5,184,000s = 60 days

These values must not be silently changed from accumulated live results.

## 4. Local acceptance evidence

User-run acceptance on 2026-10-07 confirmed:

- original live-notification acceptance baseline: `706 passed`
- independent review of feature head `fa01f7e`: `727 passed` (21 additional tests)
- independent re-review of remediation head `6c069ea`: `736 passed`; all nine previously reported issues were rechecked and no new blocker was found
- final independent review of feature head `b6f26499`: `738 passed`; report-age display, shared-infra localization and atomic report persistence verified; no new blocker found
- approved policy gate: PASS
- Gmail OAuth readiness: PASS
- recipient resolved successfully
- no test email was sent during preflight
- Mission Control health: `status = OK`
- `delivery_allowed = true`
- Dashboard HTTP: `200`
- LaunchAgent loop: `state = running`
- LaunchAgent dashboard: `state = running`
- runtime policy moved out of Documents to Application Support after the original macOS TCC failure
- production trading remained `NO_GO`

Observed PIDs are runtime evidence only and are not stable identifiers.

Important remaining runtime acceptance:
- the first post-enable real notification event has not yet been used to prove a real Gmail send + Sent readback in this new Mission Control path;
- reboot/login autostart is installed and running, but a physical Mac reboot/login recovery test is still pending.

## 5. Normal daily operation

No manual command is required while the Mac stays logged in and launchd is healthy.

Status check:

```bash
cd "/Users/jerson/Documents/ChatGPT/frank-meme-main/crypto-300-profit-mission/local-agent"
bash scripts/status_mission_meme_launchd.sh
```

Expected core state:
- loop `state = running`
- dashboard `state = running`
- Mission Control `status = OK`
- `delivery_allowed = true`
- Dashboard HTTP = 200

Dashboard:
`http://127.0.0.1:8766`

## 6. One-month acceptance plan

Target review window: approximately 30 days after live-notification enablement.

### A. Runtime reliability

PASS only if:
1. Frank production stayed healthy or outages are explicitly accounted for.
2. Mission Control loop recovered after normal process exits and, once tested, after Mac reboot/login.
3. Dashboard remained recoverable locally.
4. No recurring TCC/policy-path failure.
5. No unbounded Gmail ambiguity state.
6. No policy hash drift was silently accepted.

### B. Notification correctness

For every notification-eligible fresh Decision transition:
1. exactly one durable Decision event exists;
2. local notification has one delivery path;
3. Gmail has one durable delivery identity;
4. no duplicate Gmail exists for the same decision_id;
5. historical/stale episodes were not backfilled as fresh alerts;
6. BUY/SMALL_BUY invalidation transitions were not silently lost.

Record separately:
- eligible events;
- local delivered / failed;
- Gmail verified / pending / manual-review / failed;
- duplicate count;
- missed-notification count.

### C. Strategy usefulness

Separate engineering reliability from trading usefulness.

At minimum review:
- number of REENTRY_WATCH, ACCUMULATION and MULTIPLE episodes;
- number of BUY / SMALL_BUY / WAIT / NO_BUY decisions;
- fraction of Frank patterns that remained executable at 30 USDC;
- distribution of entry-price deviation and price impact;
- false-positive examples;
- missed followable opportunities;
- outcome concentration by token so one exceptional winner cannot dominate the conclusion.

Canonical followability horizons remain:
- T+5m
- T+15m
- T+1h
- T+6h
- T+24h

Do not call the strategy validated from raw Frank wallet PnL or one large winner.

### D. Main/live evaluation gap vs review-branch candidate

Current main/live Mission Control still has the historical gap described below: it stores 60-day observations plus immutable Decision transitions, but does not yet guarantee independent fixed-horizon capture after Frank exits.

`main` now contains the forward-only outcome tracker that records executable Jupiter entry inventory and T+5m/T+15m/T+1h/T+6h/T+24h exit observations, with `MISSED_WINDOW` instead of hindsight backfill.

Until the user's local checkout is synchronized to merge commit `2f83be33` (or a later main) and the Mission Meme LaunchAgents are restarted, the currently running local system must still be treated as having the old gap. Do not reconstruct missing horizon prices by guess.

## 7. Open validation items inside current Frank system

These are not blockers for normal notification use, but remain unclosed evidence gaps:

1. Real production SOL/WSOL-quoted Frank normalization remains unexercised. The review branch now has a live read-only sidecar candidate, but it still needs a real Frank SOL/WSOL trade acceptance before this gate is closed.
2. A real Jupiter `NO_ROUTE` fixture has not been observed; current no-route handling remains conservative.
3. Sustained Jupiter 429 handling still uses bounded blocking cooldown; a non-blocking cycle-level design remains preferable.
4. First real post-enable Mission Control Gmail send + Sent readback still needs live evidence.
5. Actual reboot/login recovery of both new LaunchAgents still needs one real reboot acceptance.

## 8. Deferred / unfinished Mission features

### P0 — needed for rigorous monthly Frank strategy review

**Post-signal outcome tracker / monthly evaluator — MERGED TO MAIN, LOCAL RUNTIME REFRESH PENDING**

Review-branch implementation:
- forward-only registration for fresh REENTRY_WATCH / ACCUMULATION / MULTIPLE stages;
- executable Jupiter 30 USDC -> token entry inventory;
- same raw token inventory -> USDC exit quotes;
- T+5m/T+15m/T+1h/T+6h/T+24h;
- 5-minute sampled MFE/MAE/max drawdown;
- win rate, statistical median, mean return, profit factor;
- grouping by pattern and Decision;
- Ex-Top1 / Ex-Top3 24h robustness;
- `MISSED_WINDOW` rather than late-price backfill.

It still needs one final local full-suite rerun on merged `main`, LaunchAgent restart, and then real forward sampling.

### P1 — tracked-person expansion

**Reusable PERSON_PATTERN validation pipeline — NOT IMPLEMENTED**

Required flow:
wallet graph -> infrastructure exclusion -> raw finalized events -> market buy/sell/internal-transfer classification -> person-level ledger -> episodes -> causal signal time -> delayed replay -> robustness -> TRAIN/VALIDATION/HOLDOUT -> real FORWARD.

Current candidate states:
- Ethermonk: OBSERVE_ONLY / 0 validated patterns
- Point Farm: OBSERVE_ONLY / 0 validated patterns
- TheSolstice: OBSERVE_ONLY / 0 validated patterns

No production wallet registry or alerts are authorized for them yet.

### P1 — TOKEN_CONSENSUS

**Multi-person same-token consensus signal — DEFERRED**

The old design exists, but live authority is Frank-only. It requires at least two independently verified person_ids and must prove incremental edge over the one-person baseline before production use.

### P1 — wallet-cluster automation for CA research

**General wallet-cluster reconstruction engine — MERGED TO MAIN, LOCAL RUNTIME REFRESH PENDING**

Review-branch implementation:
- CA input in the same localhost Dashboard under `CA 链上查询`;
- Top20 token-account -> real owner resolution;
- bounded finalized Solana JSON-RPC history;
- direct target-token and SOL/USDC/WSOL relations;
- common funding / batch funding / common signer / consolidation evidence;
- synchronized buy/sell and distinctive-size behavior;
- public DEX/router/CEX/shared-infrastructure exclusion;
- confirmed relation vs probable control vs probable execution kept separate;
- strict concentration fields stay `UNRESOLVED` until special-address normalization is explicitly complete;
- persistent local reports + hashed RPC cache;
- quick / standard / deep presets;
- asynchronous single-worker execution to protect the free public RPC path.

The merged implementation still requires one real public-RPC CA acceptance run on the user's Mac before calling the feature locally accepted.

### P2 — MONSTER / 妖币 discovery

Status:
`RESEARCH_FROZEN / VALIDATION_NOT_PASSED`

- V3 TRAIN passed.
- Once-only 2024 validation failed ceiling / had insufficient target data.
- D2 blocked.
- D3 not started.
- No Monster LaunchAgent.
- No live Monster Gmail/scanner.
- No automatic V4 is authorized.

### P2 — NFT opportunity radar

Status:
`SPEC_PRESENT / RUNTIME_PAUSED`

Design is preserved, but no active Mission runtime/scheduler/Gmail currently provides NFT mint-opportunity coverage.

### P2 — CORE PRICE / overall-market trend monitor

Status:
`PAUSED`

BTC/ETH/SOL/HYPE/BNB price-abnormality / overall-market monitor is not running. Prior V2/V3 research remains historical; V3 is blocked by lack of a verifiably untouched hidden interval.

## 9. Intentionally excluded, not missing

The following are deliberate boundaries and should not be treated as unfinished bugs:

- automatic trading;
- wallet signing;
- swap construction/submission;
- GPT in Frank's real-time critical path;
- silent threshold tuning from live outcomes;
- new ChatGPT automation for this lane.

They require separate explicit authorization if ever reconsidered.


## 10. 2026-10-07 external review remediation on feature branch

Independent review of `fa01f7e` found three credibility-impacting defects plus several hardening issues. The branch now contains fixes for:

1. Public Jupiter/Raydium/PumpSwap/etc. DEX programs are recorded as `SHARED_INFRA`, not `SAME_EXECUTION_PROGRAM`; execution-only clusters no longer reduce unresolved material-holder share.
2. Funding-history `getTransaction = null` is recorded as unavailable evidence and skipped instead of aborting the CA job.
3. Even-sized outcome samples use the statistical midpoint median instead of the upper middle element.
4. Cluster POST body must be a JSON object.
5. Same CA is deduplicated only for the same scan preset; a requested deep scan is no longer silently replaced by an active quick scan.
6. Cluster POST requires `application/json` and rejects a non-loopback Origin while still allowing local CLI requests with no Origin.
7. Completed in-memory job metadata is bounded and full reports stay on disk; Dashboard reloads the last persisted CA report.
8. `DEV_LINKED_CLUSTER_PCT` includes wallets in a probable-control cluster containing a verified DEV/CREATOR/TREASURY wallet.
9. This status document now distinguishes current main/live authority from review-branch candidate functionality.

Independent review has now rerun the full local-agent suite on `b6f26499` with `738 passed` and found no new blocker. This is the accepted pre-merge feature-head evidence.


### Post-736 polish

After the `736 passed` review of `6c069ea`, three non-blocking polish items were implemented:

- persisted CA reports display exact observation time plus relative age after refresh, reducing the chance that an old holder snapshot is mistaken for current state;
- `SHARED_INFRA` / common-CEX evidence is localized in the Dashboard as public/shared infrastructure and explicitly says it does not imply common control;
- cluster report files, including `latest.json`, are written with temp-file + atomic replace semantics to avoid partial reads during same-CA refresh.

These commits were independently revalidated on `b6f26499`; the full local-agent suite passed `738` tests with no new blocker.


## 11. Merge record — 2026-10-07

Pull request #27 merged successfully into `main`.

- merge commit: `2f83be332e2c20270a3f534e333f1a19ea8b6bc5`
- accepted feature code head: `b6f26499`
- accepted feature full-suite result: `738 passed`
- final branch head before merge added acceptance/status documentation only
- production trading authority remains `NO_GO`

Main had advanced by 22 commits since the feature branch merge-base. Those commits touched airdrop/TGE, crypto-daily and US-stock-daily files and did not overlap the 23 Meme feature paths. GitHub reported PR #27 mergeable/clean and merged it normally.

### Required local post-merge acceptance

Before calling Meme local tooling v2 live on the user's Mac:

1. synchronize the local `frank-meme-main` checkout to current `origin/main`;
2. run the complete local-agent pytest suite on the merged main;
3. restart/reinstall the Mission Meme LaunchAgents so the loop and Dashboard load the merged code;
4. confirm policy gate, `delivery_allowed=true`, Dashboard HTTP 200 and both LaunchAgents running;
5. run one real CA query against Solana finalized RPC and verify Top20/coverage/cluster rendering;
6. confirm existing Frank signal view and Mac/Gmail notification path still remain healthy;
7. keep `PRODUCTION_TRADING = NO_GO`.

## 12. Local post-merge acceptance — 2026-10-07

User-local merged-main acceptance completed on `58a98faf`:

- local checkout synchronized to `origin/main` at `58a98faf`;
- complete local-agent suite: `738 passed` in 6.17s;
- policy gate: PASS;
- approved policy SHA256: `355336f2959e674939210b51be97d2df1d6e66f4ee3cca8acfe041dabb9e3ae8`;
- Gmail OAuth/config preflight: PASS, recipient `lxx.run688@gmail.com`, no email sent during preflight;
- Mission Meme loop LaunchAgent: running / active;
- Mission Meme dashboard LaunchAgent: running / active;
- Mission Control health: `status=OK`, `delivery_allowed=true`, `candidate_error_count=0`, `outcome_error_count=0`;
- SOL normalization sidecar: `status=OK`, with zero copied/resolved/unresolved rows in this acceptance cycle;
- Dashboard HTTP: 200 at localhost port 8766;
- AUTO-START: ON AFTER USER LOGIN;
- LIVE DELIVERY: policy-gated and enabled by approved policy;
- `PRODUCTION_TRADING = NO_GO`.

This closes the merged-main code/test/LaunchAgent startup acceptance gate.

Remaining runtime acceptance items:

1. run at least one real Solana CA through the new `CA 链上查询` page and verify Top20 owner / coverage / cluster rendering against live finalized RPC;
2. observe the first genuinely new forward outcome track and confirm T+5m/T+15m/T+1h/T+6h/T+24h persistence begins without historical backfill;
3. exercise a real SOL/WSOL-quoted Frank trade before declaring the SOL normalization path empirically exercised;
4. verify one actual Mission Control Gmail notification end-to-end, including Sent readback, when a real new eligible signal occurs;
5. after a future Mac reboot/login, verify both LaunchAgents automatically recover and Dashboard HTTP returns 200 without manual intervention.


## 13. 2026-10-08 CA V3 integration: review FAIL and remediation in isolated PR #29

**Branch:** `review/meme-ca-v3-integrate-main-20261008`.
**PR:** https://github.com/lxxlx2/ChatGPT_mission_record/pull/29
**Authority:** REVIEW_ONLY / NOT_MERGED / NOT_DEPLOYED / PRODUCTION_TRADING_NO_GO.

An external AI review of integrated HEAD `7014589e` reported **FAIL**, with 804 passing pytest cases on that pre-remediation head. This test count **does not cover subsequent fixes**. Main branch and installed Mac services remain separate.

Remediation applied on PR #29 only, with these explicit controls:

- **B1:** frozen policy `temporary_sol_conversion_allowed=false` wins. SOL normalization sidecar now records audit price equivalence without `for_model=True`; synthesized SOL USD predicates cannot count as known USDC and shadow candidates are not merged into Mission Control live decisions, observation/outbox or notifications. Any future strategy-authority change would require separate user approval, policy SHA approval and actual replay.
- **H1:** report diagnostics use `PRIMARY`/`FALLBACK_N` labels only for configured authenticated RPC URLs. No credential-bearing URL should be persisted in report/latest.json or returned through cluster APIs.
- **H2:** CEX/public/unresolved batch payouts are excluded from strong `BATCH_FUNDING` evidence, even with synchronized buys; EOA/verified-control-funder evidence remains separately evaluated.
- **H4:** installed LaunchAgent installer refuses to run without explicit `CONFIRM_MISSION_LOOP_RESTART=1`, before any installer writes or restarts. Do not use this flag in review; existing non-restarting runner patch remains the safe route.
- **M1:** SOL sidecar source rows, source/mirror signals and candidate states are restricted to `person_id='frank'`.
- **M2:** replay uses before/after read-only file SHA256 comparisons and explicit runtime failure for non-dry-run outbox; isolated CA acceptance checks `forward.sqlite`, `health.json`, and the two LaunchAgent plists. Snapshot hashes cannot establish the provenance of an unobserved live deployment.
- **M3:** `route_intermediate_assets=None` and `route_intermediate_evidence_status=UNVERIFIED` no longer pretend that an unknown route is proven simple. SOL normalization fails closed for explicitly unverified intermediate routing.

**Remaining gates, NOT YET PASSED:**

1. Other AI independent re-review on the exact updated PR HEAD plus a fresh full local-agent test run. Pre-fix 804 passes are historical.
2. **H3:** expanding Frank classifier quote identity to USDT, DEX programs and parser v8 remains a potentially behavior-changing production classifier update. Requires real production `forward.sqlite` + associated raw signature evidence, exact baseline/candidate replay, review of state/episode/amount/email deltas and explicit separate approval before merge or deployment. USDT must not satisfy direct-known-USDC thresholds.
3. **M5:** RARI residual-intermediate incident is a research lead in earlier source handoff, not a validated fixture in this integration. Do not claim RARI was replayed; obtain original signed transaction/raw fixture to validate, or explicitly exclude it from acceptance scope. Unproven routes remain `UNKNOWN_NEEDS_REVIEW`.
4. Real CA integrated-head acceptance and Mac reboot/re-login persistence are still pending. Prior isolated 3-CA test was on source branch and is historical.
5. One genuine post-enable Gmail Sent readback remains pending; tests must not send real notification or change live outbox.

**Forbidden during review:** main merge, local installer invocation, LaunchAgent kickstart, production `forward.sqlite` writes, historical migration/backfill, strategy threshold changes, sending Gmail, new automation, live trading.

**Review standard:** FAIL until H3 replay and all new patch tests/independent review pass; only then can a separate controlled merge/deploy be considered.


## 14. 2026-10-08 second review FAIL: X1-X8 repair in PR #29 only

An independent second review of `a51517b8` reported **814 collected, 813 passed, 1 failed**, plus HIGH/MEDIUM safety gaps. This is evidence for that **older head only**, not the current remediation branch. The reviewer confirmed the previous fixes caught 9 pre-fix failures. H3 historical classifier replay and M5 RARI fixture remain missing.

Subsequent review-branch changes:

- **X1/X2:** Actual classifier now assigns `NO_INTERMEDIATE_TRANSFER_OBSERVED` only when parser flow data is present and contains no unrelated mint, permitting SOL/USD equivalent **for read-only research only**. Absent flow evidence or additional intermediate mint remains `UNVERIFIED`, with no synthetic gate promotion. All historical SOL-quote V1 gates remain direct-USDC-only. Routed USDC gross input with extra intermediate flow also becomes `UNDETERMINED`.
- **X3:** Isolated CA acceptance checks a stable DB schema and SHA256 of the **existing immutable signatures prefix**, allowing new rows from the separately running live scanner. Health compares stable content after excluding known heartbeat fields; LaunchAgent plists are hashed. A fake-PROD integrity-only shell harness and behavioral tests are added. These are **selected invariant checks, not full production immutability proof**.
- **X4:** `store._known_usdc_trade` now reuses `evaluator.known_usdc_event`; synthetic `SOL_EVENT_TIME_USDC_VERIFIED` is not known USDC in either frozen gate or position accounting.
- **X5:** Unresolved common funders, signers and consolidation edges prevent the categorical `NO_MATERIAL_CONTROL_CLUSTER_FOUND` conclusion even with otherwise normalized metrics.
- **X6:** Only valid `https://` RPC endpoints without embedded userinfo or whitespace are accepted; invalid endpoints fail with a generic exception. Dashboard job error messages are constant redacted strings, not untrusted exception text.
- **X7/X8:** Behavioral tests added for sidecar isolation, default installer refusal, outbox guard, fake-prod acceptance and input integrity. Replay transition counts compare signal-relevant semantic fields; complete audit metadata diffs remain separately visible.

**Remaining blocking gates:** independent pytest / compileall / shell syntax run for current HEAD, source-vs-candidate historical replay on copied real `forward.sqlite` plus raw transactions, H3 user approval for altered USDT/DEX classifications, and RARI-specific inclusion/exclusion determination. No reviewed historical signal transition may be approved from synthetic fixtures alone.

**No merge, no local deployment, no new monitoring/automation, no live trades, no sending Gmail, no LaunchAgent restart.** `PRODUCTION_TRADING=NO_GO`.


## 15. 2026-10-08 fourth remediation after independent third Review FAIL

Review of `1865fd7c` was **FAIL** despite an actual independent **826 passed, 0 failed, 0 skipped** suite on that **older** HEAD. Root cause was actual Frank writer health keys missed by CA acceptance integrity comparison. Reviewer also identified route provenance, semantic replay, NULL outbox, coverage descriptions and test strength. A separate reviewer's *uncommitted local remediation prototype* reportedly had 830 passes; this is **not acceptance evidence** for the current review branch, and that prototype patch was not mounted here.

**Current review branch only:** `review/meme-ca-v3-integrate-main-20261008` (see PR #29 for exact rolling HEAD).
- **B1 / CA integrity:** Stable-health allowlist now follows actual `scripts/frank_shadow_service.py` stable writer keys rather than excluding an incomplete list of heartbeat counters. A regression changes `last_poll_at`, `candidate_duplicate_count`, request/rate/error/retry counts, transport status and `poll_seconds`, and then separately tampers `production_writes`. It must accept the former and reject the latter. This checks a *signature identity prefix* (wallet, signature, person, slot, block time, raw hash/reference), schema, stable-health allowlist and LaunchAgent plist hashes. It **does not** prove immutable historical `body`/alert state or untouched unrelated DB tables. Normal live DB appends are allowed; this is a scoped invariant check and not a full production snapshot.
- **H1 / quote provenance:** For a single-target USDC trade whose `wallet_token_transfer_flows` is missing, `route_intermediate_evidence_status=UNVERIFIED` forces `amount_predicate=UNDETERMINED` and reason `ROUTE_EVIDENCE_UNVERIFIED`. Additional intermediate mints remain `ROUTED_RESIDUAL_ASSETS` and fail-closed.
- **M1 / dry-run outbox:** Both replay scripts now use SQLite `status IS NOT 'DRY_RUN_AUDIT'` so NULL status fails closed.
- **M2 / classifier replay:** `semantic_classification` includes derived SOL route eligibility via `_simple_sol_quote_eligible`, without treating benign new audit keys as transitions. All H3 baseline evidence must be generated anew with this definition.
- **M3 / accurate integrity scope:** Updated helper docstring, report scope and CA acceptance output to state that only existing signature **identity columns** are checked, not mutable historical bodies or full DB state.
- **M4 / sidecar tests:** Added cycle-level test that injects a fabricated SOL shadow candidate into `sync()` output and confirms it creates no decision/DB candidate/outbox. Earlier test that replaced `candidates()` remains as a secondary defense.
- **L1 / exception secrecy:** Generic fixed errors replace `str(exc)` in Mission Control loop, SOL sidecar and Dashboard request-validation paths, while retaining exception class for diagnostics. Added simulated secret-bearing RPC/candidate exception checks.
- **L2 / authorized installer path:** Isolated HOME/worktree and mock `launchctl`, `python`, `curl`, `sleep` simulate the explicit `CONFIRM_MISSION_LOOP_RESTART=1` path with zero real launchd/OAuth/HTTP impact. This does **not** authorize or prove actual Mac installer safety and does not replace a separate deployment review.
- **H2 low-priority parser ambiguity:** Unknown-owner transfer-flow hardening remains deferred because it may alter frozen classifier behavior; require validated transaction evidence and H3 review before changing production parser semantics.

**Evidence state on this fourth remediation HEAD:** Git commit/push verified; **pytest/compileall/bash-n = NOT_RUN on current HEAD**, no CI result, historical production replay **NOT_RUN**, RARI-specific raw fixture **NOT_RUN**, authenticated real-CA integrated-head acceptance **NOT_RUN**, actual Mac live/reboot checks **NOT_RUN**.

**Authority:** PR #29 DRAFT and `REVIEW_ONLY`. `CODE_REVIEW=FAIL_PENDING_NEW_INDEPENDENT_CHECK`; `READY_FOR_CONTROLLED_MERGE=NO`; `DEPLOY=NO`; `PRODUCTION_TRADING=NO_GO`. No main merge, service restart, production DB mutation, new automation or Gmail send is authorized.


## 16. 2026-10-08 fifth remediation after independent fourth Review FAIL

**Review evidence:** reviewer tested former HEAD `8d137bcac3fc759dd76314850697582d5e7f8ec6` and reported **834 pytest passes**, all compile/shell syntax passes, but **CODE_REVIEW=FAIL**. Reviewer verified a **separate unpushed 837-pass prototype**, which has **not been adopted as executed evidence for this branch**. The local patch path was not available in the author's container; equivalent changes have been authored against the GitHub review branch.

### Writer provenance and integrity authority

Repository inspection: `accept_meme_ca_v3.sh` and `install_mission_meme_launchd.sh` both use `live-v1` as PROD; the Mission loop reads `forward.sqlite` V1 signal tables from that root. The relevant writer schema/health is `Ledger` / `scripts/frank_local_signal_service.py`. `scripts/frank_shadow_service.py` writes a different Repository-style schema, and **must not** be used as sole authority for live-v1 health invariants. **The actual Mac LaunchAgent or invoking process has not been read**; repository wiring alone does not prove the installed writer's current CLI args.

**B-1:** `meme_acceptance_integrity.py` `STABLE_HEALTH_KEYS` now includes both known writer profiles. The real Ledger writer's stable configuration values `system`, `policy`, `policy_hash`, `code_commit`, `loaded_source_sha256`, `delivery_authority`, `gpt_in_critical_path`, `production_trading`, `other_persons`, `new_automation`, and `poll_interval_seconds` are checked when present. Volatile RPC/scan counters, signatures, poll timestamps, state and health summary updates are excluded. A new isolated regression uses the actual `Ledger` database schema, seven synthetic RUNNING/RETRY health ticks and new signature rows, plus six individually parameterized stable-key tamper checks. An additional synthetic `frank_shadow_service` health profile checks cross-writer compatibility.

**Integrity claim remains SCOPED** to the existing signature identity prefix, schema, configured stable-health fields and LaunchAgent file hashes. Mutable `signatures.body`, alert state, other DB tables and unknown health fields are **not verified**. The Ledger writer's full process-level RUNNING harness was exercised in the *reviewer's separate sandbox only*. The newly committed regression simulates writer health ticks and uses the authentic Ledger schema; it is **not an author-executed full service harness**.

### Additional remediation

- **M-1:** Added behavioral `frank_v1_replay.report` NULL-outbox test: a NULL status must fail with `HISTORICAL_DELIVERY_MUST_BE_DISABLED`, while `DRY_RUN_AUDIT` remains allowed. Production Gmail/outbox untouched.
- **H-2:** Added an opt-in installer safety test which executes the actual inline Python policy gate against a `REVIEW_ONLY` policy in an isolated temporary HOME/worktree. The Python shim refuses later OAuth preflight, and a fake `launchctl` tracks unwanted calls. Deleting the policy assertion should cause the test to FAIL instead of reporting a false PASS. This is not an authorized install.
- **M-2:** Removed `referenced_pre_raw` and `referenced_post_raw` from historical replay's semantic transition projection; they remain in complete evidence diffs. Direct quote quantity, classification and derived SOL route eligibility still define semantic transitions. Added regression to differentiate harmless reference changes from quote amount changes.
- **M-3:** Tightened Mission Control fake sidecar test to require exactly two outbox entries and the expected Frank mint only. Previously loose `outbox<=2` is gone. Older source-inspection tests remain supplementary, not authority.

**Deferred:** low-priority exception text in legacy Frank writing paths and unknown-owner parser hardening need separate provenance/safety evaluation. Avoid modifying frozen Frank production semantics as a cosmetic follow-up.

### Independent acceptance remains pending

This new PR head has **NOT_RUN** author pytest, compileall, shell syntax or full Ledger RUNNING harness. Current edits are **SUBMITTED_TO_GIT** and await **fifth independent review** of the exact HEAD with real test output. The old 834 and unpushed prototype 837 results must never be copied forward as a PASS for new code.

Still NOT_RUN: H3 production copied-history baseline/candidate replay and genuine RAW-gz coverage; RARI raw transaction-specific acceptance; authenticated real CA integrated-head acceptance; Mac reboot/login LaunchAgent recovery; live Gmail Sent readback.

**Production state and permissions:** PR #29 remains Draft/REVIEW_ONLY; `CAN_MERGE=NO`, `CAN_DEPLOY=NO`, `PRODUCTION_TRADING=NO_GO`. No code was merged to main; no production service, alert, automation, policy, or database was changed.


## 17. 2026-10-08 sixth remediation after fifth independent Review FAIL

**Independent fifth review:** source HEAD `1bf6490cda4d7bb95751f88a2b1355fe77c40cb1`, **845 passed, 0 failed, 0 skipped**, `CODE_REVIEW=FAIL` (the full test count is from that older HEAD). Verified blocking installation authority-chain vulnerability: the installer wrote the runtime policy and self-generated approved hash *before* its validation. A rejected policy could be accepted by Mission Loop after a KeepAlive restart. Reviewer also reproduced empty-health-profile integrity PASS, `source_drift` not checked, and false-negative policy guard mutation tests.

**Current PR-only remediation (never deployed):**

1. **B-1 policy authorization:** `mission_agent/mission_control/policy.py` exports one shared `live_delivery_policy_authorized()` predicate. Both installer preflight and Mission Loop call the same function, checking an independently supplied exact lowercase SHA256, schema, `status=FROZEN_APPROVED`, `live_delivery_approved=True`, and `observation_retention_seconds=5184000`. The installer now explicitly requires externally supplied `APPROVED_POLICY_SHA256`; it MUST NOT be calculated by the installer from its own candidate policy as the trust anchor. A missing/incorrect hash fails before any installed state writes.
2. **Preflight-before-write:** `install_mission_meme_launchd.sh` validates policy, authenticated RPC availability and Gmail readiness before creating any Application Support directories or overwriting old policy/hash/RPC/runner/plist state. Approved runtime files are written using per-file temp+rename; a crash between policy/hash updates produces a mismatch (fail closed). Rejected installer requests cannot alter existing approved files. **This changes future installer prerequisites; it does not authorize anyone to run it.**
3. **Loop defense:** `MissionMemeService.delivery_allowed` enforces the same retention/approval predicate independently at startup, so an otherwise self-hashed but rejected policy cannot trigger LIVE Gmail delivery even after KeepAlive restarts.
4. **Health writer profiles:** `scripts/meme_acceptance_integrity.py` now requires all mandatory stable health keys for either recognized writer profile and rejects unknown/mismatched profiles. For Ledger `FRANK_ONLY`, the exact approved frozen Frank `policy_hash` is compared to the canonical `signals.policy.POLICY_SHA256` value; `production_trading=NO_GO`, `source_drift=False`, frozen poll interval/authority and no additional automation are required at capture **and** verify. Other Ledger identity values are checked for stability across the acceptance window. Live counter/heartbeats/signature appends remain allowed.
5. **Tests:** Added mutation-oriented negative tests covering each installer gate, byte-identical original approved state on rejection (including RPC secret), actual inline Python policy gate positive case (mocked OAuth/launchctl/curl only), Mission Loop's independent acceptance/rejection and an A-approved/B-rejected lifecycle, missing key/profile/frozen policy/source-drift checks, and real Ledger schema fixtures. A prior test that skipped the inline policy check with `cat >/dev/null` was replaced.
6. **Replay:** Previous direct-USDC and outbox protections remain; H3 historical replay and RARI original-signature fixture still missing. No parser, frozen signal thresholds or production trading behavior was authorized.

**Integrity scope remains limited:** the health validator checks explicit stable configuration keys, original signature identity prefix, schema and LaunchAgent plist hashes. It does NOT establish immutable `signatures.body`, `v1_states`, `v1_evaluations`, complete DB snapshots or real production delivery state. Literal `production_trading=NO_GO` in health records reflects a code-level declaration, not independent proof that production trading is disabled. Repository wiring suggests `frank_local_signal_service.py` writes the `live-v1` Ledger, but Mac installed runtime LaunchAgent was not inspected: `UNVERIFIED_PRODUCTION_LAUNCHAGENT`.

**Critical evidence limitation:** Current review-branch changes are committed via GitHub connector only; **no fresh author-executed pytest, shell syntax, standalone Ledger RUNNING harness, or production replay on the exact new HEAD has been performed**. No GitHub CI run is known. Fifth-review 845 passes do NOT transfer to this code.

**Authority:** PR #29 `DRAFT/REVIEW_ONLY`; `CODE_REVIEW=FAIL_PENDING_SIXTH_INDEPENDENT_REVIEW`; `CAN_MERGE=NO`, `CAN_DEPLOY=NO`, `PRODUCTION_TRADING=NO_GO`. No restart, Gmail send, live CA, raw-history replay, backfill or production change.


## 18. 2026-10-08 final targeted cleanup after sixth conditional-PASS review

**Independent sixth review evidence, exact older HEAD `3065d14af57392695e4f154acbe4aa82a95f45be`:** `CODE_REVIEW=PASS (CONDITIONAL)`, 862 pytest passed / 0 failed / 0 skipped, compileall and tracked shell syntax passed; real Ledger RUNNING/RETRY harness 7 checks passed, 9 negative controls detected. **These are verified review results for the old HEAD only**, not an automatic PASS for the later cleanup commits.

The user requested to **finish the outstanding code cleanup without expanding the Frank/Dashboard feature scope**. All modifications below are restricted to the existing PR #29 review branch; **no changes to main or deployed Mac runtime**.

**Final cleanup scope:**

- **L-1: health↔database schema binding.** `scripts/meme_acceptance_integrity.py` now validates health profile against the SQLite schema *within the same read-only database snapshot*: `LEDGER_FRANK_LOCAL` requires an Engine-owned `v1_states` table; `REPOSITORY_FRANK_SHADOW` must not contain that table. This prevents a complete shadow health JSON from being accepted alongside the live Ledger's DB. It is a narrow identity binding, not proof of all Repository migration tables.
- **T-1: pre-capture identifier test.** A baseline already containing the wrong Ledger `identifier` must be rejected, in addition to existing tests for post-baseline tampering.
- **R-1: installer candidate TOCTOU.** The candidate policy is snapshotted once to a private temp file before the actual policy gate and Gmail OAuth readiness check. The approved bytes are taken from that same snapshot during installation, never reread from the original `POLICY` after preflight delay. After atomic copy, `shasum -a 256` must match the external `APPROVED_POLICY_SHA256`. If this check fails, the previous runtime policy bytes are restored (or the newly created runtime policy is removed); no new approved hash, RPC credential, plist, runner or launchctl mutations are permitted by this failure path.
- **Targeted tests:** Real Ledger schema fixtures include the Engine-owned `v1_states`; shadow fixtures are schema-distinct; complete shadow-health + Ledger DB must fail; wrong Ledger identifier at capture fails; an OAuth-stage edit to the original candidate must not affect installed bytes; forced bad postcopy hash must preserve the previously approved runtime state.
- **No other functionality changed.** Frozen Frank signals, parser, SOL/USD research, local Mission Control decisions, Gmail routing and trade state remain as before. The previously documented limits on immutable signature body, alert states and arbitrary unrelated tables remain.
- **Residual trust model:** A process with the same user's ability to modify installed policy+approval files (and executable code) can fabricate its own local authority. Files are 0600 but this is *not* an independently rooted credential; should not be represented as one. Installer Gmail preflight may perform OAuth/profile network operations after policy authorization; it does not send Gmail in the tested path.
- **Mac LaunchAgent writer launch provenance remains `UNVERIFIED_PRODUCTION_LAUNCHAGENT`.** The repo supports an inference about Ledger `live-v1` ownership but actual installed launch arguments have not been read.

**Current-HEAD evidence:** Git branch updates verified via GitHub; the full pytest, compileall, shell lint and real Ledger harness have **NOT been executed against these last cleanup commits** in the author's environment. Keep code acceptance **PENDING_FINAL_TARGETED_REGRESSION**, not PASS. Do not restate 862 passes as current HEAD's test count.

**Hard gates unchanged:** H3 real source-vs-candidate replay on isolated copies of production `forward.sqlite` plus *all* bound raw gz = `NOT_RUN`; RARI signed raw evidence = `NOT_RUN`; authenticated CA, post-login Mac durability, Gmail Sent readback = `NOT_RUN`. Separate explicit approvals required for accessing/using production data, merging or deploying. `CAN_MERGE=NO`, `CAN_DEPLOY=NO`, `PRODUCTION_TRADING=NO_GO`. No more discretionary features should be added to this PR while finishing validation.

## 19. 2026-10-09 fixed-window root/Token-2022 signed-data audit

**Status: independently executed on operator's Mac, read-only; evidence is for this one held token and time window only.** The existing review-branch diagnostic `scripts/reconcile_frank_owned_token_account.py` was run from exact commit `90dceedea9f7569ec63a39f86be202880f1fca75`, with its own saved JSON. Operator supplied the verbatim terminal summary. This is an observation, not a signal, scanner-completeness certificate, or production rollout.

- Wallet: `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`.
- Mint: `HzYCHqAN2uoHGRnL9v2ChCfFQX3bvJuJd5zu2Hd5MZQy` (Tweetcraft).
- Fixed interval **2026-10-07 22:20:54 through 2026-10-08 22:20:54 Asia/Bangkok** (`1791386454..1791472854` UTC epoch).
- Root-address signatures: 173. Current owner Token-2022 account `7qujRSPgfbgiwMhBSc1znjaQoHM9jt6HQVw6TgxnLAsG`: three distinct signatures. One also in root index, two absent from root index.
- Slot `454400785`, sig `4sP6iSpctgnnbKsLcGRn1YvaPB7TF9EGc1A6KL4G7gGwLKdP1Jm6LfEH3fs9UhQLMFNPwJ6tmS4FaEAaGT9XCC9S`: root signed, FOMO cosigned, wallet received raw `4732220716414` target units (six decimals), wallet paid raw `6715734492` USDC units (six decimals); **`OPPOSING_FLOWS_REVIEW_REQUIRED`** and `trade_confirmed=false` in the independent research script.
- Slots `454400786` and `454400788`, signatures `31eUPZfB1QGmZqfmLsjzByy2eqkLy9vX3Ds5rtbDfAcfJKWqt9FkvD56vVBmQnQ3gE88NARUYaS7KWdQr6ZxUmLU` and `5YinrWMXytncTAPZZfZZH8TBspVy3UoBMWwLCYyFUWVA4t6kDBnbLi6s1UdkWtV68RidVX1DoQpubb2VYEJBXtrS`: current owner token account referenced but root not indexed/referenced/signer, FOMO not cosigner; **zero net change of target mint belonging to the root owner** and no owned quote changes. Both `NO_OWNER_MINT_DELTA`. These are **not evidence of additional Frank BUY/SELL**.
- Specific conclusion: The missing two signatures on this **one current** token account do **not** explain the suspected gap between an indexed single 24h BUY and larger GMGN per-position trade counts. They must not be added to local BUY/SELL totals or signal episodes.
- Comparison scope mismatch: GMGN token-position buy/sell totals and 7d/30d stats must be matched by **same wallet + same 24h time bounds + unique tx hash** before declaring an omission. Previously observed local 7d and 30d counts should not be compared directly to fixed-window 24h one-BUY counts.
- Remaining **UNVERIFIED**: prior closed/recreated owner token accounts, other current mint accounts, owner-level DFlow/FOMO routes not referencing the root, whether the main classifier misses historical legitimate fills, GMGN independent exact-window activity, source-to-signal replay, live alert timeliness.
- Correct next validation priority: **time-aligned independent GMGN wallet activity** (official API, authenticated when available) versus root-indexed transactions and on-chain DFlow `Trade.Account.Owner` transaction hashes; separate chain movement, failed or infrastructure-only tx from BUY/SELL. Review discrepancy examples first; revise parser only against demonstrated misses, followed by frozen policy regression before any deployment. Do not turn ambiguous or missing input into a positive follow signal.

**Release gate:** `PERSON_SIGNAL_COVERAGE=UNVERIFIED`, `MAC_GMAIL_ELIGIBLE_ALERT_TIMELINESS=UNVERIFIED`, `CAN_DEPLOY=NO`, `PRODUCTION_TRADING=NO_GO`. No scheduler, notification, email, production service, or main changes from this finding.

## 20. 2026-10-09 GMGN API rejected; switch to native Solana owner-account evidence

**User explicit decision:** GMGN Free API requires >=$100 retained in the account and has unsuitable call limits. User does not trust that custody exposure; no top-up, subscription, API key, wallet connection, or paid GMGN requirement is authorized. `audit_frank_gmgn_activity.py` remains a never-executed research artifact and must **NOT** be used as a required acceptance/deployment gate or suggested again. Manual GMGN portfolio screenshot is contextual/qualitative only, not a canonical historical fill feed.

**Current replacement:** `local-agent/scripts/audit_frank_native_owner_coverage.py` compares original operator-validated fixed 24-hour root signature history and cached finalized JSON-parsed transactions against all token accounts *observed as root-owned in the pre/post balance records*, then queries the historical signatures of those accounts from the existing configured Solana RPC. Reuses the original `frank-fomo-fixed-20261009-054846.json` and `frank-fomo-rpc-cache`. Reads existing `live-v1/forward.sqlite` through SQLite URI `mode=ro` and `query_only` for same-window root signature and trade counts. It reports root-signed, paired token-quote and unilateral transfer group counts; account-only signatures and their complete raw balance deltas are reviewed, never promoted automatically to BUY or follow signal.

**Evidence boundary:** only historical accounts actually referenced in the root snapshot can be discovered this way, including accounts that were subsequently closed. Accounts never referenced in root, historical undiscovered owner ATAs, delegated execution wallets, GMGN UI historical position totals, native SOL rent/fee cash legs and transient gross routed swaps remain `UNVERIFIED`. If the snapshot or RPC window is incomplete, returns `UNVERIFIED` and does not claim zero missing fills or root-perfect persona coverage.

**Verification:** review-source branch commit `c19798372d0f19054ab32b20dbc4fa33c5856093` GitHub CI run `37890315910`: targeted 46 passed, full 920 passed, compile, shell and JS syntax checks pass. These are **offline regression results**. Real Mac RPC historical account scan and comparisons are still **NOT_RUN**. Production signals, thresholds, live monitoring, LaunchAgent, email, and CA production UI untouched. `CAN_DEPLOY=NO`, `PRODUCTION_TRADING=NO_GO`.

**Next operator action:** execute this one Git-hosted read-only historical account audit in a detached worktree using existing RPC/cache/database; verify source inventory and classification gap counts; if evidence identifies a true overlooked economic fill, manually validate the tx then propose one minimal classifier fix with frozen replay tests. Do not add new fallback monitors or a new market-data provider.

## 22. 2026-10-09 Alchemy rate-limit incident and zero-RPC evidence gate

**Mac incident observed:** the operator's latest invocation of commit `6fe0b010a2eaef249271ea3b1cad983942423bf9` failed at `TOKEN_ACCOUNT_SIGNATURES` with `RPC_HTTP_429` after **18 of 30 observed historical token accounts** were fully scanned, and **1 account** had been classified as high-volume/incomplete. The other 11 accounts were **not fully scanned** in this run. Operator also supplied a received Alchemy throughput warning showing more than 10% of recent requests rate-limited. It is **not verified** that this research process alone caused the team's overall rate-limit incidence: Alchemy enforces throughput at account level across apps. This is a **FAILED / UNVERIFIED** Mac acceptance; no output proving extra Frank buys, no confirmed full trade coverage.

**Code finding:** historical `solana_signatures` retries and re-requests every token account when the audit restarts. Its memory-only `account_counts`, `joined`, `deferred_signatures` are discarded on `RPC_HTTP_429`; there is no durable resume checkpoint. Single-account 1,000 signature and extra-decode 300 signature bounds are valid and MUST remain unchanged. Repeated full retries are wasteful while 429s exist.

**Immediate containment:** stop re-running the full-window native account scanner, stop upgrading CU capacity for this investigation, and do not create fallback monitors or alternate Alchemy keys. New `local-agent/scripts/audit_frank_root_offline.py` uses the existing fixed-window source report, 173 cached finalized root transactions, and read-only local forward ledger, without any RPC or third-party calls. It verifies cached transaction identities, slot, time window, original root count, wallet-owned pre/post balances, local indexed signatures and classifications; outputs:
- observed token account inventory and mint counts;
- root-signature token/quote opposing net-flow **candidates** with evidence hash/slot;
- separately counted unmatched ledger signatures and observed grouping;
- `rpc_requests=0`, `can_conclude_complete_frank_trades=false`, `token_account_signature_coverage_checked=false`.
Only scoped root-cache agreement is possible. A signed net-flow candidate is not a confirmed trade, especially if routing/counterparty cannot be proven.

**Future network design gate:** before any more full scans, implement source-hash-bound, per-account **durable checkpoint** for completed signature lists, separate decoded-tx receipts, query budgets per explicit run, and stop-on-429 without replaying prior accounts. Preserve incomplete-account causes and scope, never infer zero trades from missing RPC. Do not silently switch the paid source or widen thresholds. No network resume implementation or live replay authorized/completed in this commit.

**Status:** PR #29 remains **DRAFT / REVIEW_ONLY**, production Frank signal/mail/launchd/CA unaffected, `NO_GO` remains. Next task is **offline Mac evidence review**, then targeted source-gap analysis. Real alert/coverage proof and production deployment remain **NOT_VERIFIED / NOT_EXECUTED**.

## 23. 2026-10-09 Frank 173-root offline reconciliation and 148 unsigned movement follow-up

**Operator-provided actual Mac offline result:** Immutable review SHA `9339f07d6601cbb8fc2892cd9d110312cf09f762` ran `scripts/audit_frank_root_offline.py` using locally cached finalized root transactions and read-only Mission SQLite. Result `OFFLINE_ROOT_CACHE_RECONCILED_SCOPE_LIMITED` at `1791386454..1791472854`: source root report **173**, cache **173**, Mission root signatures **173**, missing on either side **0**; local trade signatures **1**; **30** token accounts observed in cached root transaction balance vectors (29 non-USDC mints plus USDC observed by this run). Source SHA-256 `030d8cbce0c506a277c5883855b8397996cc1bc02d253884076c376257154d88`.

**Signed wallet and economic net-flow classifications from this run:**
- `ROOT_NOT_SIGNER:NO_TOKEN_NET=22`
- `ROOT_NOT_SIGNER:QUOTE_ONLY=1`
- `ROOT_NOT_SIGNER:TARGET_ONLY=148`
- `ROOT_SIGNED:OPPOSING=1`
- `ROOT_SIGNED:QUOTE_ONLY=1`

Only signed paired net-flow candidate sig `4sP6iSpctgnnbKsLcGRn1YvaPB7TF9EGc1A6KL4G7gGwLKdP1Jm6LfEH3fs9UhQLMFNPwJ6tmS4FaEAaGT9XCC9S`, Tweetcraft mint `HzYCHqAN2uoHGRnL9v2ChCfFQX3bvJuJd5zu2Hd5MZQy`, matching existing Mission classified signature; `trade_confirmed=false` at this research evidence layer.

**Interpretation:** 148 unsigned/one-sided owner token balance changes are **not established buys or sells**. They may be passive token receipts, transfers, or sponsored execution legs. Historical FOMO wallet trades can have fee payers and token owners distinct, so a root-only signer requirement is a **hypothesis for missed fills, not proof**. The 173 signature agreement establishes only **root-address-referenced coverage**. It cannot prove token-account-only or FOMO owner-indexed coverage. Current native token-account scan ended `RPC_HTTP_429` after 18/30 accounts and one incomplete high-activity account; there is no trustworthy all-account conclusion. Production signal count `1` cannot be interpreted as Frank's full actual trades.

**New offline evidence review code:** Existing `scripts/audit_frank_root_offline.py` in PR #29 now outputs `unsigned_target_only_events`, signer/FOMO co-signer/router combinations, parser mechanical classification, per-mint counts, timeline and per-transaction receipt/authority evidence from the **same cached data only**. No added RPC/API. It deliberately keeps `unsigned_target_only_trade_count_confirmed=0` and never upgrades FOMO/router presence to a BUY or follow signal. GitHub CI run `37907296297` passed **60 targeted / 934 full tests**. This code has **NOT** been executed on the operator's Mac; its actual 148-event breakdown remains unverified until that one offline replay.

**Release:** no main merge, runtime rollout, launchd change, extra monitoring, Gmail, trade execution or threshold change. `CAN_DEPLOY=NO`; `PRODUCTION_TRADING=NO_GO`.

## 24. 2026-10-09 Frank 148 unsigned events: real offline replay outcome

**Operator Mac result actually executed and supplied**: immutable checkout `ed3fb910b2eace0be061d488b045f73abf562225` reran `scripts/audit_frank_root_offline.py` with `rpc_requests=0`, `external_indexer_requests=0`, `production_db_writes=0`, `emails_sent=0`, `signals_changed=false`. Output remained `OFFLINE_ROOT_CACHE_RECONCILED_SCOPE_LIMITED`, source SHA-256 `030d8cbce0c506a277c5883855b8397996cc1bc02d253884076c376257154d88`, root source/cache/local ledger 173/173/173, one local classified trade, 30 observed token accounts, root paired flow candidate 1.

The follow-up offline classification conclusively reports within the **173 root-address-referenced cached transactions**, **148 unsigned one-sided owner-token movements**, with these observed attributes:
- All 148 `direction=IN`, `fomo_cosigned=false`, `known_router_present=false`, `parser_classification=PASSIVE_RECEIPT_LIKE`.
- `unsigned_target_only_trade_count_confirmed=0`, `can_conclude_complete_frank_trades=false`, `token_account_signature_coverage_checked=false`.
- Distribution of **transaction counts** (do not confuse with token quantities, holders or trades): 114 involve mint `A7bdiYdS5GjqGFtxf17ppRHtDKPkkRqbKtR27dxvQXaS`, 26 involve `pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn`, and eight other mints have 1 each. The first two mints therefore explain 140/148 of these receipt-like events.
- In the first **20-sample** displayed transaction evidence, repeated fee payers and incoming `decoded_owned_transfer_legs=1` are visible, with neither FOMO cosigning, a recognized router, nor wallet authority detected. Sample does not establish the identity or motive of external token senders for all 148.
- Independent wallet buy evidence `4sP6iSpctgnnbKsLcGRn1YvaPB7TF9EGc1A6KL4G7gGwLKdP1Jm6LfEH3fs9UhQLMFNPwJ6tmS4FaEAaGT9XCC9S` remains the single paired opposite-flow root candidate and existing local classified signature; the research layer still flags `trade_confirmed=false` until independent instruction-level qualification.

**Investigation update:** The original hypothesis that 148 missing BUY/SELL events were hidden among the root-referenced `TOKEN_MOVEMENT` rows is **not supported by this sample and classifier evidence**. Retain them as **PASSIVE_RECEIPT_LIKE / UNVERIFIED_SENDER_OR_PURPOSE**; do not create signals or count them as Frank active buys or sells. Do not upgrade their cause to proven dust/scam/airdrop or attribute to any particular organization without sender/source evidence.

**Still open:** sponsored FOMO/DFlow owner-matched fills **outside** root-referenced transactions and historic/current token accounts outside the completed RPC scan. Alchemy returned `RPC_HTTP_429` after 18/30 full account scans and one high-volume incomplete account; the account-level scans are not persisted and must **not** be repeated until bounded resumable checkpointing has been designed/tested and resource availability reviewed. No GMGN paid API, no custody top-ups. This source-limited result does **not** prove that Frank made only one buy in the full 24h window. No production alert eligibility or historical accumulation thresholds are changed.

**State:** `ROOT_CACHE_AGREEMENT=CONFIRMED`; `PASSIVE_148_CLASSIFICATION=OBSERVED`; `PERSON_TRADE_COMPLETENESS=UNVERIFIED`; `ALERT_DELIVERY_ACCURACY=UNVERIFIED`; `CAN_DEPLOY=NO`; `PRODUCTION_TRADING=NO_GO`. Existing PR #29 is review-only; no main merge, monitoring, mail, LaunchAgent, local runtime, or trading changes from this update.

## 25. 2026-10-09 durable bounded owner-account audit V1 (review-only)

**Reason for development:** Mac auditor repeatedly re-read old token accounts after reaching the existing single-account 1,000 signature cap or receiving `RPC_HTTP_429`. Alchemy account throughput warning also appeared. The previously successful 18/30-account progress was memory-only and **cannot be recovered from logs alone**. No claim is made that it has been migrated into the new checkpoint format.

**Implementation on PR #29:** `local-agent/scripts/audit_frank_native_resume.py` is a new research-only command. It is **not** wired to the original production Frank scanner, the existing 8766 Dashboard, any LaunchAgent, price alert, Gmail, or automations. It has a zero-network default (`--phase plan`); online signature scan or transaction decode requires an explicit `--allow-network --phase signatures|decode` and a call-count budget. It connects only to the **first existing configured private Solana RPC** (no new keys, retries, failovers, GMGN, RH chain, or storage funds).

Hard safety constraints:
- Separate durable per-owned-token-account JSON signature checkpoints and per-extra-signature decoded transaction receipts, written atomically 0600 outside `live-v1`, with full canonical SHA-256 readback, symlink/file size/permission checks.
- Immutable checkpoint context binds exact wallet, start/end, finalized commitment, source report SHA-256, digest of all cached root transactions, sorted `account→mint` inventory and original caps. Context mismatch is an error; do not blindly reuse another window's results.
- Per-account query uses 250-signature pages and the original **1,000 signatures/account** limit (unchanged), original `MAX_SOL_PAGES`, and original 300-extra-transaction decode cap. When this bound is reached the account is `CAPPED/INCOMPLETE`, not `COMPLETE`. Signatures of uncapped completed accounts are deduplicated by tx hash.
- Per-process maximum **8 physical RPC attempts**, default **3** when explicitly enabled; minimum **1 second** between attempts within the same run. A 429 or rate-limit JSON RPC error immediately terminates that run, without the prior client's automatic retries, and leaves all previously saved pages/receipts reusable. No network request takes place in default plan mode.
- Signature detection and transaction decoding are separate phases; receipts are reused when the same immutable context is run again; no BUY classification or active follow signals can be generated by this review-only tool. Full Frank trading coverage remains unknown even if all observed accounts become complete.
- Concurrency of live research runs blocked by a local filesystem advisory lock.

**Validation gates:** GitHub Actions run `37923488300` at review code SHA `b2a6227446acfa8c4d93d4b8aba8dc999e6c1f35` verified **71 targeted / 945 full tests passed**, including no-network plan, persisted page cursor across stop/restart, HTTP and JSON-RPC 429 single-attempt stop, one-second pacing, original caps, checkpoint corruption rejection, source change refusal, request budget, slot/time validation, and stable decoded receipt re-use. This is offline evidence / development testing, **not actual Mac historical RPC validation**. Do not advise a network resume while the observed Alchemy 429 is unresolved without a new controlled resource review.

**Approval state:** `RESEARCH_CODE=REVIEW_ONLY`; `ACTUAL_MAC_PLAN=NOT_RUN`; `ONCHAIN_RESUME=NOT_RUN`; `PERSON_TRADE_COMPLETENESS=UNVERIFIED`; `SIGNALS_CHANGED=NO`; `CAN_DEPLOY=NO`; `PRODUCTION_TRADING=NO_GO`.

## 26. 2026-10-09 Mac zero-RPC resume plan acceptance (real local output)

**Operator executed and supplied verbatim local output:** checkout `15cb8c94bd03a3ffe0213eb2dfb6649275def5a2`, command `scripts/audit_frank_native_resume.py --phase plan`. Returned `status=OBSERVED_SCOPE_PARTIAL`, `wallet=498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`, `start=1791386454`, `end=1791472854`, source SHA-256 `030d8cbce0c506a277c5883855b8397996cc1bc02d253884076c376257154d88`, immutable context SHA-256 `7d3401ef45781d3a7af5d8d832e686fa71a5bd8618e723aded6db24416452458`, `historical_root_count=173`, `local_classified_count=1`, `accounts_total=30`, `accounts_complete=0`, `accounts_capped={}`, and **all 30 accounts `PENDING` with zero saved pages/signatures**. `rpc_attempts=0`, `new_signature_pages=0`, `new_receipts=0`, `production_db_writes=0`, `signals_changed=false`, `emails_sent=0`. It neither claimed trade confirmation nor complete persona coverage.

**Meaning:** the Mac local source/configuration and offline evidence binding work as expected in default plan mode. Because plan mode does not create a checkpoint directory, this invocation does **not** initialize durable network checkpoints or recover the previous memory-only 18/30 high-activity-account scan. No real onchain network resume has been tested, and the old Alchemy 429 condition has not been proven cleared. Respect the existing explicit stop on live validation. Do not ask the operator to start `--allow-network` until a fresh separate review/authorization.

**Follow-up static review:** On review branch PR #29, scanner now validates semantic chronology across consecutive pages and checkpoint readback, rejects mismatched cross-account signature timestamps, checks stored decoded receipt Slot and essential evidence structure, and adds deterministic corruption/time-boundary tests. This is *development-only* test coverage; do not label it a Mac production deployment. Frozen Frank classifier, threshold, live monitors, Gmail and Dashboard unchanged.

**Current gates:** `MAC_OFFLINE_PLAN=PASS`, `HISTORIC_OWNER_SIGNATURE_SCAN=NOT_RUN_IN_RESUMABLE_V1`, `PERSON_TRADE_COVERAGE=UNVERIFIED`, `REAL_ALERT_DELIVERY=UNVERIFIED`, `CAN_DEPLOY=NO`, `PRODUCTION_TRADING=NO_GO`.

## 27. 2026-10-09 user authorizes scoped Frank Solana history validation

**Clarified user intent**: The user corrected an earlier incorrect assistant assumption: the 2026-09-30 ETH 58.33% Phase-3 live-validation pause was **for a different price-alert module**, not for Frank's Solana/FOMO historical study. Alchemy 429 and email `Your requests are being rate limited` arrived **2026-10-09**, with the user's intent to fix request frequency/efficiency, not to permanently forbid Frank history validation. The user expressly requested to begin Frank verification (`开始啊`). Scope authorized here is **historical read-only**, no wallet signing, monitor rollout, Gmail changes, or production enablement.

**Bounded first real Mac probe**: PR #29 review-only script `scripts/audit_frank_native_resume.py` now supports `--account` (only an account in the immutable root-observed inventory), allowing one real signature RPC request without advancing all 30 accounts in order. Initial probe shall use only Tweetcraft's already-root-observed token account `7qujRSPgfbgiwMhBSc1znjaQoHM9jt6HQVw6TgxnLAsG`, fixed Bangkok 2026-10-07 22:20:54 to 2026-10-08 22:20:54 historical window, `--phase signatures --allow-network --max-rpc-calls 1`. Only account signature checkpoint receipts within a research directory may be written. The original 1,000/account cap, 300 extra decoded tx cap and 1 second intra-run minimum remain unchanged. The script stops on 429 (HTTP or JSON RPC) and never retries or switches API credentials.

**Verification**: GitHub Actions run `37928599733` verified `76 targeted / 950 full tests PASSED` at code SHA `7eb7a716a255aad261ffa6c75356cc78d77a41f8`, including selected-account allow-list and no-scan of unrelated accounts. This is OFFLINE CI, not proof of actual RPC success. First Mac query has **NOT_RUN** status pending local operator execution. No user authority for automated batch scan beyond this first explicitly controlled run; choose next account only after reviewing first result. `CAN_DEPLOY=NO`; `PRODUCTION_TRADING=NO_GO`.

## 28. 2026-10-09 Frank first real resumable Solana account RPC success

**Operator-supplied REAL Mac invocation**: Review SHA `97889e6746971301f3f14c18b17aaf9b8cb62e12`, `scripts/audit_frank_native_resume.py --phase signatures --allow-network --max-rpc-calls 1 --account 7qujRSPgfbgiwMhBSc1znjaQoHM9jt6HQVw6TgxnLAsG`. The JSON output unequivocally records **one actual RPC attempt** and **one signature page checkpoint**, with no stop reason, no observed HTTP 429, and no production writes.

Evidence values supplied:
- `status=OBSERVED_SCOPE_PARTIAL`, `wallet=498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`, `start=1791386454`, `end=1791472854`.
- `source_sha256=030d8cbce0c506a277c5883855b8397996cc1bc02d253884076c376257154d88`; `context_sha256=7d3401ef45781d3a7af5d8d832e686fa71a5bd8618e723aded6db24416452458`.
- `historical_root_count=173`, `local_classified_count=1`, `accounts_total=30`, `accounts_complete=1`; remaining **29 accounts PENDING**, 0 capped.
- `extra_signature_candidates_from_completed_accounts=2`, `decode_receipts_pending=2`, `decode_receipts_complete=0`, `decoded_opposing_flow_review_candidates=0` (**zero is not evidence of no swaps because no receipts have been decoded**).
- `rpc_attempts=1`, `new_signature_pages=1`, `new_receipts=0`, `stop_reason=null`, `selected_account=7qujRSPgfbgiwMhBSc1znjaQoHM9jt6HQVw6TgxnLAsG`.
- `signals_changed=false`, `production_db_writes=0`, `emails_sent=0`, `trade_confirmed_by_audit=false`, `full_person_trade_coverage=false`.

**Interpretation**: Real RPC with one selected owned-token account successfully created a resumable checkpoint on the operator's Mac. Two token-account-referenced signatures outside the already-indexed 173 root signatures require instruction-level decode; they are **not confirmed Frank buys or sells** and may correspond to previously observed Tweetcraft associated-token-only events. Exact hash identity and ownership must be verified before assuming equivalence to previous evidence.

**Next narrow gate**: Repeat unchanged source context from pinned review code, `--phase decode --allow-network --max-rpc-calls 2`, which uses the two persisted signatures and writes per-signature evidence receipts. A response `OBSERVED_SCOPE_PARTIAL` and process exit 2 remain expected because 29 other observed accounts are incomplete. Once decoded, prioritize the Frank-owned **USDC token account** `6kD22oUQrV8tVpE2hkQzkoobwCQAy2iiZcipWn8AD5jF` for new limited read-only history. No unsolicited broad 30-account scans.

**Release gates unchanged:** GitHub PR #29 remains draft, no merges, no production alert/email changes, no auto-trading. `PERSON_TRADE_COVERAGE=UNVERIFIED`, `CAN_DEPLOY=NO`, `PRODUCTION_TRADING=NO_GO`.

## 29. 2026-10-09 Mac two-extra-signature decoded result and USDC priority

**ACTUAL Mac result supplied by operator**: Checked out review SHA `85340176f5595c2ab01ade62fdc64e4b9b5602dc`. Ran the read-only two-receipt resume decoder, `--phase decode --allow-network --max-rpc-calls 2`. JSON output: `status=OBSERVED_SCOPE_PARTIAL`; `context_sha256=7d3401ef45781d3a7af5d8d832e686fa71a5bd8618e723aded6db24416452458` (same immutable historical evidence context); `historical_root_count=173`, `local_classified_count=1`; `accounts_total=30`, `accounts_complete=1`, 29 pending, 0 capped; `extra_signature_candidates_from_completed_accounts=2`, `decode_receipts_complete=2`, `decode_receipts_pending=0`; `decoded_opposing_flow_review_candidates=0`, `decoded_review_sample=[]`, `rpc_attempts=2`, `new_signature_pages=0`, `new_receipts=2`, `stop_reason=null`, `trade_confirmed_by_audit=false`, `full_person_trade_coverage=false`, and no production DB changes, email or signals.

**Interpretation**: REAL end-to-end getSignaturesForAddress + 2 getTransaction calls and two durable hash-bound receipts are now validated without observed 429. `decoded_opposing_flow_review_candidates=0` proves only absence of straightforward opposed quote/target net flows for **those two transactions under the parser's existing rules**, **not** that they are definitely nontrades or that Frank did no other swaps. The existing console report prints detailed candidates only when `opposing_flow=true`, so the two decoded nonopposing transaction signatures and `fomo_cosigned`, `root_referenced`, target/quote mints have not yet been independently inspected by this chat. Do **not** invent their IDs or attribution. New code revision adds a capped `decoded_receipt_sample` to the default zero-RPC `--phase plan` response, so the existing two local receipts can be inspected without another RPC query.

**Next bounded history scan**: Priority account from operator's fixed root inventory is the Frank-owned **USDC token account** `6kD22oUQrV8tVpE2hkQzkoobwCQAy2iiZcipWn8AD5jF` for mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`. Recommend **one explicit read-only signature query**, `--phase signatures --allow-network --max-rpc-calls 1 --account 6kD22oUQrV8tVpE2hkQzkoobwCQAy2iiZcipWn8AD5jF`, then examine before any more fetches. One page may be `ACTIVE`/incomplete when high-volume; it is never proof of no signatures/trades. Do not scan remaining 28+ accounts or decode more than the explicit budget automatically.

**Operational gates**: two source-specific receipts are already persisted and can be reused. Research remains DRAFT/REVIEW_ONLY, not merged to main. Production signals, thresholds, launchd, Dashboard, Gmail, wallets and autotrading not changed. `CAN_DEPLOY=NO`, `PRODUCTION_TRADING=NO_GO`.

## 30. 2026-10-09 confirmed two benign-shaped ATA receipts and high-volume USDC cursor

**Operator-provided Mac output** at pinned code SHA `e82aa705a7740edfd7052edbfb24bdc49f354dc9`. The new research report has resolved the two extra signatures previously found in the Tweetcraft-owned token account, both already persisted with zero added RPC:
- `31eUPZfB1QGmZqfmLsjzByy2eqkLy9vX3Ds5rtbDfAcfJKWqt9FkvD56vVBmQnQ3gE88NARUYaS7KWdQr6ZxUmLU` slot `454400786`.
- `5YinrWMXytncTAPZZfZZH8TBspVy3UoBMWwLCYyFUWVA4t6kDBnbLi6s1UdkWtV68RidVX1DoQpubb2VYEJBXtrS` slot `454400788`.
- For both, `root_referenced=false`, `opposing_flow=false`, `fomo_cosigned=false`, `target_mints=[]`, `quote_mints=[]`. These are **non-opposing, no-owner-net-delta as measured by current logic**; **do not classify them as Frank trades** without new evidence. Their exact instruction purposes (e.g. account lifecycle) are NOT independently determined.

**First USDC token-account query** for address `6kD22oUQrV8tVpE2hkQzkoobwCQAy2iiZcipWn8AD5jF` / USDC mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`: `rpc_attempts=1`, `new_signature_pages=1`, `stop_reason=REQUEST_BUDGET_EXHAUSTED`, `status=OBSERVED_SCOPE_PARTIAL`, `accounts_complete=1/30`, USDC account `status=ACTIVE`, `saved_pages=1`, `saved_signatures=0`. The budget was deliberately **one** RPC request; this is a **NORMAL BUDGET STOP**, not a new Alchemy 429 and not failed checkpoint persistence.

**Key interpretation and proposed next gate**: `getSignaturesForAddress` walks newest-to-oldest. A full first USDC page with **zero in-window signatures** is most consistent with signatures newer than the fixed 2026-10-07/08 window; it does NOT establish zero Frank swaps. The time span of the first page was not preserved in the old checkpoint schema, and cannot be inferred from `saved_signatures=0` alone. A backwards page may contain only pre-window signatures in principle; either way current account state is unfinished. Review-only V1 has now been amended to store `last_page_newest_block_time`, `last_page_oldest_block_time`, and `last_page_size` on each **subsequent** page; old checkpoint schema remains reusable, immutable context unchanged, no recomputation of past pages or requery. Next local run should scope only USDC account and cap requests at 2–3, inspect resulting page times, then decide if further crawling is worth the RPC cost; `CAPPED` must remain incomplete and must not promote a zero-trade conclusion.

No main merge, production monitor, threshold, wallet, transaction, launchd, dashboard or Gmail changes. `PRODUCTION_TRADING=NO_GO`, `PERSON_TRADE_COVERAGE=UNVERIFIED`.
