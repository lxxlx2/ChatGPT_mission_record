# Mission Meme current status — 2026-10-07

Timezone: Asia/Bangkok

Status: `LIVE_NOTIFICATION / OBSERVATION_ACTIVE / PRODUCTION_TRADING_NO_GO`

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

### 2A. Review-branch additions — not yet main/live

Branch:
`feature/meme-local-tooling-v2-20261007`

The branch currently adds, pending re-review + local rerun + merge:

- independent forward outcome tracking with executable Jupiter entry/exit quotes;
- fixed T+5m / T+15m / T+1h / T+6h / T+24h horizons;
- 5-minute sampled MFE / MAE / max drawdown plus monthly grouped statistics and Ex-Top robustness;
- live SOL-quoted Frank normalization in a separate sidecar DB, while keeping production Frank read-only and the frozen Frank evaluator unchanged;
- a free local Solana wallet-cluster engine and a tabbed `CA 链上查询` view inside the same Dashboard;
- Chinese trading-oriented Mission Control notification content.

These additions are **not operational authority** until the branch is revalidated, synchronized with current main, merged, and the local LaunchAgents are restarted on the merged main.

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
- subsequent review-fix commits after `fa01f7e` still require a fresh full local rerun before merge
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

The review branch now contains a forward-only outcome tracker that records executable Jupiter entry inventory and T+5m/T+15m/T+1h/T+6h/T+24h exit observations, with `MISSED_WINDOW` instead of hindsight backfill.

Until that branch is revalidated, merged and restarted locally, the live system must still be treated as having the old gap. Do not reconstruct missing horizon prices by guess.

## 7. Open validation items inside current Frank system

These are not blockers for normal notification use, but remain unclosed evidence gaps:

1. Real production SOL/WSOL-quoted Frank normalization remains unexercised. The review branch now has a live read-only sidecar candidate, but it still needs a real Frank SOL/WSOL trade acceptance before this gate is closed.
2. A real Jupiter `NO_ROUTE` fixture has not been observed; current no-route handling remains conservative.
3. Sustained Jupiter 429 handling still uses bounded blocking cooldown; a non-blocking cycle-level design remains preferable.
4. First real post-enable Mission Control Gmail send + Sent readback still needs live evidence.
5. Actual reboot/login recovery of both new LaunchAgents still needs one real reboot acceptance.

## 8. Deferred / unfinished Mission features

### P0 — needed for rigorous monthly Frank strategy review

**Post-signal outcome tracker / monthly evaluator — IMPLEMENTED IN REVIEW BRANCH, NOT YET MAIN/LIVE**

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

It still needs current-head full-suite rerun and live forward sampling after merge.

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

**General wallet-cluster reconstruction engine — IMPLEMENTED IN REVIEW BRANCH, NOT YET MAIN/LIVE**

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

The current branch still requires one real public-RPC CA acceptance run on the user's Mac before merge.

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

A fresh full local-agent test run is required after these remediation commits; do not reuse the earlier `727 passed` as proof for the new head.
