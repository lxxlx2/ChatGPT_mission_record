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

- full local-agent suite: `706 passed`
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

### D. Known evaluation gap

Mission Control currently stores 60-day observations while an episode is being evaluated, plus immutable Decision transitions. It does **not** yet guarantee an independent fixed-horizon market-price capture for every signal after Frank exits/closes the position.

Therefore a rigorous one-month T+5m/T+15m/T+1h/T+6h/T+24h return table requires the dedicated post-signal outcome tracker listed in the backlog below, or a separately verified historical reconstruction. Do not fabricate missing horizon prices.

## 7. Open validation items inside current Frank system

These are not blockers for normal notification use, but remain unclosed evidence gaps:

1. `SOL_NORMALIZATION = IMPLEMENTED_BUT_NOT_EXERCISED` on a real production SOL/WSOL-quoted Frank trade.
2. A real Jupiter `NO_ROUTE` fixture has not been observed; current no-route handling remains conservative.
3. Sustained Jupiter 429 handling still uses bounded blocking cooldown; a non-blocking cycle-level design remains preferable.
4. First real post-enable Mission Control Gmail send + Sent readback still needs live evidence.
5. Actual reboot/login recovery of both new LaunchAgents still needs one real reboot acceptance.

## 8. Deferred / unfinished Mission features

### P0 — needed for rigorous monthly Frank strategy review

**Post-signal outcome tracker / monthly evaluator — NOT IMPLEMENTED**

Purpose:
- continue independent market-price observation after a signal even if Frank exits;
- persist fixed horizons T+5m/T+15m/T+1h/T+6h/T+24h;
- calculate executable return, MFE/MAE, drawdown, win rate, median return, profit factor and concentration;
- compare BUY vs SMALL_BUY vs REENTRY_WATCH/WAIT baselines;
- support Ex-Top1 / Ex-Top3 robustness.

This is the main missing piece if the goal is to judge strategy effectiveness after one month without reconstructing missing prices later.

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

**General wallet-cluster reconstruction engine — SPEC PRESENT, GENERAL AUTOMATION NOT ESTABLISHED**

The analysis rule is mandatory for serious Meme CA research, but there is no general live production service that automatically resolves holder ownership/control/execution clusters and emits cluster-adjusted concentration for every token.

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
