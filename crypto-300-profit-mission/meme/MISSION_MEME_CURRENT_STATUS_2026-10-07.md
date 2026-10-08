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
