# FLOP Technocore Close Call — execution plan

Updated: 2026-09-26 15:06 Asia/Bangkok
Contest: `close-1`
Status: ACTIVE
Capital at risk: no external crypto capital; competition uses 10,000 POLF minted per owner key.
Prize: 1,000,000 FLOP shared by the top three places; exact per-place split is not frozen in the public rules.
Lock: 2026-10-04 09:00 UTC / 16:00 Asia/Bangkok.
Final price: last Hyperliquid `xyz:NVDA` trade before 2026-10-04 10:00 UTC / 17:00 Asia/Bangkok.

## Authority and evidence

Canonical rules:
- `flop-labs/technocore-close-call-challenge/close-call-game.md`
- `flop-labs/technocore-close-call-challenge/contest.json`

Live-design evidence already observed in the official repository:
- live contest reached hundreds of thousands of owner keys very early;
- only a small minority of keys held positions;
- many top-board keys tied exactly;
- current rules explicitly allow one operator to run many keys;
- the official simulator contains a 16-key / 4-round bracket strategy and the project commit notes that this strategy placed first in roughly two thirds of its 100-owner simulated seasons;
- the live referee has experienced stale reference / delayed-sweep periods, so freshness gating is mandatory.

The simulation result is design evidence only. It must not be treated as a live win probability.

## Final strategy decision

Use a fixed **52-key fleet**.

This supersedes the earlier 84-key sketch because the remaining contest window is only about eight days and the marginal benefit of 32 time-layer pairs does not justify doubling execution volume.

Fleet:
- 32 keys: 16 static time-layer pairs.
- 16 keys: one 4-round bracket.
- 4 keys: baseline / reserve.
- Total: 52 keys.

The strategy intentionally minimizes direction changes:
- static-pair keys never reverse;
- bracket survivors roll only three times before final settlement;
- baseline keys do not trade unless a separately documented emergency rule is invoked.

Do not expand the fleet automatically. Any expansion above 52 keys requires an explicit interactive review.

## Why this structure

### 1. Static time-layer pairs: 32 keys

At each scheduled cohort, create one matched pair at the fresh referee reference price:
- one key opens long;
- one key opens short;
- both hold to final settlement;
- neither key closes or reverses.

This creates path coverage across the remaining eight days. One side of every pair benefits from the final price moving away from that cohort's entry.

Using separate keys means later cohorts do not disturb earlier good entries and do not add round-trip fees to old positions.

### 2. Bracket: 16 keys

The bracket is the official simulator's strongest disclosed multi-key construction.

Round 1 starts with 8 long/short pairs.
At each rollover:
1. close every active pair near a fresh referee reference;
2. keep the key whose direction was favoured by the price move;
3. wait for the close to settle;
4. pair surviving keys again, one long and one short;
5. open the next round at the next fresh reference.

Counts:
- round 1: 16 keys / 8 pairs;
- round 2: 8 survivors / 4 pairs;
- round 3: 4 survivors / 2 pairs;
- round 4: 2 survivors / 1 pair;
- final: the last pair remains open and settles at S.

Only three rollover events are required. This satisfies the limited-time constraint and avoids high-frequency direction changes.

### 3. Baseline / reserve: 4 keys

- B0, B1: pure zero-score anchors. Never trade.
- B2, B3: reserve keys. Remain unused by default.
- Reserve keys may be activated only after explicit review in the final 24 hours if a new price extreme or leaderboard condition makes a one-shot position materially useful.

## Static cohort schedule

Use one long/short pair every 12 hours. Planned times below are targets, not blind execution times. If the referee reference is stale or delayed, wait for the first fresh sweep.

| Cohort | UTC | Asia/Bangkok |
|---|---|---|
| T01 | 2026-09-26 09:00 | 2026-09-26 16:00 |
| T02 | 2026-09-26 21:00 | 2026-09-27 04:00 |
| T03 | 2026-09-27 09:00 | 2026-09-27 16:00 |
| T04 | 2026-09-27 21:00 | 2026-09-28 04:00 |
| T05 | 2026-09-28 09:00 | 2026-09-28 16:00 |
| T06 | 2026-09-28 21:00 | 2026-09-29 04:00 |
| T07 | 2026-09-29 09:00 | 2026-09-29 16:00 |
| T08 | 2026-09-29 21:00 | 2026-09-30 04:00 |
| T09 | 2026-09-30 09:00 | 2026-09-30 16:00 |
| T10 | 2026-09-30 21:00 | 2026-10-01 04:00 |
| T11 | 2026-10-01 09:00 | 2026-10-01 16:00 |
| T12 | 2026-10-01 21:00 | 2026-10-02 04:00 |
| T13 | 2026-10-02 09:00 | 2026-10-02 16:00 |
| T14 | 2026-10-02 21:00 | 2026-10-03 04:00 |
| T15 | 2026-10-03 09:00 | 2026-10-03 16:00 |
| T16 | 2026-10-03 21:00 | 2026-10-04 04:00 |

No new scheduled static cohort after T16.

## Bracket schedule

Target times:
- Round 1 open: 2026-09-26 09:15 UTC / 16:15 Bangkok.
- Round 2 rollover: 2026-09-28 09:15 UTC / 16:15 Bangkok.
- Round 3 rollover: 2026-09-30 09:15 UTC / 16:15 Bangkok.
- Round 4 rollover: 2026-10-02 09:15 UTC / 16:15 Bangkok.
- Round 4 remains open through final settlement.

At a rollover, close first. Open the next round only after the close is confirmed settled, normally on the following fresh sweep.

## Quantity rule

For a fresh pair at reference price `px`, copy the official bracket's conservative sizing logic:

```
qty = floor_to_0.01(
    0.95 * min(free_POLF_long, free_POLF_short)
    / (px * (1 + 0.01 + 0.03))
)
```

Interpretation:
- 1% is the base fee;
- 3% is extra fee/clawback headroom;
- 5% of free POLF remains uncommitted before that denominator adjustment.

For initial 10,000-POLF accounts and NVDA around 225, this is about 40.5 contracts.

Never round quantity up.

## Entry-price rule

For all fleet trades:
- use the exact latest referee `ref.px`;
- use a named taker, never `"any"`;
- both sides sign;
- post as a direct trade;
- use short expiry, normally current sweep + 2;
- do not intentionally trade away from the reference to transfer value between keys.

The clawback rule makes deliberate price gifts uneconomic.

## Freshness gate

A scheduled trade is postponed unless all are true:
1. latest `d-close1-price` post is present;
2. referee reference is fresh, preferred `age_s <= 120`;
3. no known missed/stalled-referee condition is active;
4. the latest reference is not obviously stale against the immediately observable Hyperliquid `xyz:NVDA` market;
5. the previous fleet trade, if any, has a confirmed settlement outcome.

Hard skip for that sweep:
- `age_s > 600`;
- referee post is materially delayed;
- current Hyperliquid move is so fast that a large clawback / funds failure is plausible;
- room/referee status cannot be verified.

When skipped, wait for the next fresh sweep. Do not compensate by doubling size.

## Room and registration plan

The public `close1` room has experienced very high traffic. Minimize dependence on its retention window.

1. Generate controller key C0 locally.
2. Use `BASE-B0` as controller C0 and register it in `close1`.
3. Once C0 is accepted, register one unique low-traffic ordinary trading room, for example `cc-lxx-<random>`.
4. Wait until the referee lists that room as registered.
5. Register the remaining 51 owner keys inside that room.
6. Spread registrations over several sweeps rather than dumping all 51 at once.
7. Use the dedicated room for fleet trade messages.

Do not create a `d-` owned room for v1; allow-list management adds avoidable complexity.

## Key labels

Do not put private seeds in GitHub.

Local labels:
- `BASE-B0` ... `BASE-B3`
- `TIME-01-L`, `TIME-01-S` ... `TIME-16-L`, `TIME-16-S`
- `BR-01` ... `BR-16`

Public DIDs may be logged later if useful, but seed material, signing keys and recovery material must stay local only.

Recommended local secret file:
`~/.config/technocore-close-call/keys.json`
with filesystem mode 600.

## Bracket rollover rule

Suppose a bracket pair opened at `P0` with one long and one short.

At the rollover fresh reference `P1`:
- if `P1 >= P0`, the long key survives;
- if `P1 < P0`, the short key survives.

Close both sides at the fresh reference first. The losing key retires after settlement. Survivors are then paired in deterministic label order and the next pair opens at the next fresh sweep.

Do not override the winner based on a discretionary NVDA prediction.

## Monitoring

Local process should read at least:
- `d-close1-price`
- `d-close1-flow`
- `d-close1-positions`
- `d-close1-pnl`
- `d-close1-state`

Track:
- latest sweep number and timestamp;
- reference price and `age_s`;
- our trade settlement/void reason;
- every fleet key's intended role and current open position;
- our best visible score/rank when available;
- top-board score and tie concentration;
- current registered-owner count;
- referee delay / missed ranges.

Do not change a static pair because another key temporarily ranks higher.

## Failure handling

- `not_owner`: re-register that key in the dedicated registered room and retry only after a later sweep.
- `limits`: wait for a new reference; rebuild signatures with the new price.
- `funds`: reduce quantity by 5% and retry once on a fresh sweep.
- `expired`: rebuild with current sweep + 2.
- stale reference / referee lag: wait; no trade.
- signing failure: stop that key and repair locally; never publish the seed.
- duplicate trade id: issue a new unique id; do not reuse ids.

## No-churn rule

After a static cohort settles:
- no close;
- no stop;
- no reversal;
- hold to S.

After a bracket round opens:
- no intervention until the scheduled rollover, except a protocol/settlement failure.

This rule is deliberate. With a 1% fee per side, unnecessary churn directly damages score.

## Final-24h policy

At 2026-10-03 09:00 UTC, review:
- our best visible rank/score;
- top-three score and tie count;
- current NVDA distance from the best static entries;
- whether B2/B3 should remain zero-score or take one final directional pair.

Default is **no action**. No new discretionary fleet strategy is invented in the final day without explicit user approval.

## Success criterion

Primary: at least one fleet key finishes in a prize place.

Secondary:
- retain a complete local audit of every registration, signed trade, sweep outcome and key role;
- do not leak private signing material;
- avoid needless fees and stale-reference fills;
- preserve zero-score anchors as a fallback.


## Live bootstrap state — 2026-09-26

Bootstrap completed successfully.

Public controller DID:
`did:key:z6MkevKtnieM4xDeWywRH2L1k4DqV2wq5mUUo4YQSbwk9yKu`

Dedicated trading room:
`cc-lxx-a3ddd5f9de`

Observed bootstrap sequence:
- controller owner registration was posted to `close1`;
- dedicated room registration was posted;
- the room became visible in referee flow;
- registration messages for the remaining 51 fleet keys were sent to the dedicated room.

Private Ed25519 seeds remain local in:
`~/.config/technocore-close-call/keys.json`

Latest observed local referee status from 2026-09-26:
- sweep: 249;
- reference: 224.43;
- reference age: 1 second;
- owners: 1,094,535;
- registered rooms: 13;
- live mark: 222.50;
- visible leader score: 172.69.

This confirms the referee is currently fresh and advancing. Exact membership of our 52 local DIDs still requires fleet-specific mint verification before any position is opened.

Safety gate added in runner:
- `gate` compares all 52 local DIDs against referee mint records;
- it also requires the dedicated room to be registered;
- price, flow and state must be on the same sweep;
- latest referee reference must be within the 120-second preferred freshness window;
- latest flow must have no active missed range;
- `open-static` and `open-bracket` now refuse to trade when this gate fails.

Next gate:
- pull commit `90d4f27766e83533615c4e17cb550c17f946c052`;
- run local `gate`;
- do not open T01 or bracket round 1 unless it prints `GATE: PASS_OPEN_ALLOWED`.

Execution state:
`FLEET_GATE_PENDING`

## Execution status

FLEET_GATE_PENDING.

The user has authorized starting this stored plan. Live secret generation and signing must occur locally on the user's Mac; do not move private seeds into GitHub or chat.


## Mint-gate correction — 2026-09-26

The first fleet gate reported `fleet minted: 0/52`. That result was a false negative caused by treating the visible `d-close1-flow.mints` subset as a complete owner list.

Official repository issues #6 and #7 document the live behavior:
- flow posts are constrained by technocore.chat's 4,096-character message limit;
- most minted DIDs may be omitted from the visible `mints` array;
- `omitted.mints` accounts for those hidden entries and reconciles with owner-count growth;
- multiple operators confirmed keys could settle trades even though those keys never appeared in the visible `mints` subset;
- a registration falling inside a referee `missed` range was not read and must be re-posted.

Gate semantics were therefore corrected in commit `f8b0580079cb0e1fae334281597d66e62230f4e7`.

The revised gate:
- treats visible mint membership as informational only;
- requires the controller-owned dedicated room to be registered;
- verifies all 51 non-controller owner-registration messages are still present in the dedicated room with the expected signed DID as author;
- scans retained referee flow for any `missed` range naming the dedicated room and blocks if one exists;
- still requires fresh, aligned price/flow/state sweeps.

The controller's owner status is indirectly established by the referee accepting/listing its room registration, because only a registered owner may register a trading room.

Execution state:
`FLEET_REGISTRATION_RECHECK_PENDING`.


## Fleet gate passed — sweep 250

Observed local gate result:
- sweep: 250;
- reference: 224.43;
- age_s: 45;
- flow/state both at sweep 250;
- dedicated room registered: yes;
- visible mint subset: 0/52, informational only;
- retained-window omitted mints: 1,094,123;
- dedicated owner registrations: 51/51;
- dedicated-room missed ranges: none;
- latest missed: none;
- all gate checks: PASS.

Execution gate result:
`GATE: PASS_OPEN_ALLOWED`

T01 remains scheduled for 2026-09-26 16:00 Asia/Bangkok. Sweep 250 corresponds to approximately 15:50 Bangkok, so do not intentionally open T01 early. At or just after 16:00, run `open-static 1`; the command re-runs the safety gate internally and will refuse the trade if freshness or room evidence has degraded.

Execution state:
`GATE_PASS_WAITING_T01`.


## T01 submitted — 2026-09-26 16:00 Asia/Bangkok

Static cohort T01 was submitted successfully to the dedicated room.

Observed submission:
- trade id: `t01-1790413210`;
- room seq: 65;
- server timestamp: 2026-09-26T09:00:10.473230Z;
- maker / long: `TIME-01-L`;
- taker / short: `TIME-01-S`;
- quantity: 40.70;
- entry price: 224.42;
- source sweep: 251;
- expiry: sweep 253.

The room returned the exact signed trade at seq 65, so the submission itself is confirmed present in the registered dedicated room.

Settlement is still pending referee confirmation. Per the frozen rules, a posted trade counts only after `d-close1-flow` reports a settlement outcome. Do not start bracket round 1 until T01 is confirmed settled or its failure mode is understood.

Runner commit `732e3ac23b58e9d07bee2941478de7f4717a73af` adds `check-trade`, which searches retained referee flow for a specific saved trade outcome and explicitly treats missing results as inconclusive when `omitted.settled` or `omitted.void` are present.

Execution state:
`T01_SUBMITTED_WAITING_SETTLEMENT`.


## T01 outcome visibility — sweep 254

Local `check-trade --cohort 1` result:
- current sweep: 254;
- current reference: 224.31;
- reference age: 2 seconds;
- T01 submission still present at dedicated-room seq 65;
- explicit outcome: `NOT_VISIBLE`;
- retained referee-flow omissions: `settled=71072`, `void=61097`.

Interpretation:
- this does not establish a void;
- the public flow surface is heavily truncated and official repository issue #8 documents `omitted.settled` in live sweeps;
- the T01 message itself was posted correctly in the registered dedicated room;
- the dedicated room has no reported missed range;
- the two T01 owner registrations were part of the 51/51 retained signed registrations before the trade;
- the trade price was the fresh referee reference and the 40.70 size was within the stored conservative funds rule.

Because the public referee surface cannot positively reconcile an omitted individual outcome, T01 is classified as:
`OUTCOME_OMITTED_HIGH_CONFIDENCE_VALID`

This is an inference from protocol evidence, not a direct settlement confirmation.

Before opening bracket round 1, the runner was hardened in commit
`37b15b5d096115a3a3d06a2ab782163b655e311f`:
- each bracket pair is written to local state immediately after submission;
- rerunning `open-bracket` resumes missing pairs and skips already-submitted pairs;
- a partial network/process failure can no longer cause an unsafe full re-run with duplicate fresh trade IDs;
- bracket output stores compact submission evidence instead of the entire room dump.

Execution state:
`T01_OUTCOME_OMITTED_READY_FOR_BRACKET_R1`.


## Bracket Round 1 submitted — 2026-09-26 16:17 Asia/Bangkok

Round 1 completed with all eight planned pairs saved locally and posted to the registered dedicated room.

Common execution parameters:
- source sweep: 255;
- entry price: 224.26;
- quantity per pair: 40.73;
- room sequence range: 66 through 73;
- server timestamps: 2026-09-26T09:17:44.657126Z through 2026-09-26T09:17:48.234463Z.

Pairs:
- BR-01 / BR-02: `br1-01-1790414264`, seq 66;
- BR-03 / BR-04: `br1-03-1790414265`, seq 67;
- BR-05 / BR-06: `br1-05-1790414265`, seq 68;
- BR-07 / BR-08: `br1-07-1790414266`, seq 69;
- BR-09 / BR-10: `br1-09-1790414266`, seq 70;
- BR-11 / BR-12: `br1-11-1790414267`, seq 71;
- BR-13 / BR-14: `br1-13-1790414267`, seq 72;
- BR-15 / BR-16: `br1-15-1790414268`, seq 73.

All eight submissions used one fresh referee price and identical sizing, so there is no cross-pair entry skew inside round 1.

Runner commit `1f069d1f93f2173a714ab15dcd5e1f1ef8485838` adds `check-bracket`, which reports visible settled/void results for all saved bracket trades and distinguishes omitted outcomes from explicit voids.

No bracket rollover action is due yet. The next planned bracket rollover remains 2026-09-28 16:15 Asia/Bangkok. Until then, only settlement verification and referee-health monitoring are required.

Execution state:
`BRACKET_R1_SUBMITTED_WAITING_OUTCOME_CHECK`.


## Unattended execution revision — 2026-09-26

Manual interaction every five minutes is rejected as the operating model. The contest referee sweeps every five minutes, but the fleet only needs to act on a small number of scheduled events. Human presence at every sweep adds operational risk and makes the 04:00 Bangkok static cohorts impractical.

Latest bracket visibility check at sweep 256:
- reference: 224.14;
- reference age: 56 seconds;
- all 8 Round-1 trade IDs: `NOT_VISIBLE`;
- explicit visible voids: 0;
- retained-flow omissions: `settled=72,590`, `void=61,098`;
- classification: `OUTCOMES_PARTLY_OR_FULLY_OMITTED`.

This remains an observability limitation, not evidence that all eight trades failed.

### Revised runtime model

A local `autopilot` mode now runs continuously on the Mac:
- polls every 60 seconds;
- prints/logs a heartbeat only when the referee sweep advances;
- automatically opens only due static cohorts;
- runs the full fleet safety gate immediately before any automatic static trade;
- never duplicates a static cohort already present in local state;
- catches up a due static cohort for at most 180 minutes;
- after that window it records the cohort as missed instead of opening many hours late;
- bracket rollovers remain review-gated until rollover close/re-open mechanics are implemented and validated.

This means the program may observe every referee sweep, but it does not place a trade every sweep.

Commit `43ceb95ca08d4a9ef89b46620947f636e7fcb44d` adds the autopilot mode.
Commit `cad3ede7ac17648d7ad2b225b3ba107c2dbcfa62` adds a macOS LaunchAgent installer using `launchd` plus `caffeinate`.

The LaunchAgent:
- starts automatically at login;
- restarts the autopilot if it exits;
- keeps the Mac from entering idle sleep while the agent is running;
- writes stdout/stderr to `~/Library/Logs/technocore-close-call-autopilot.*.log`.

Physical lid-close sleep is still a machine-level boundary. Closing a MacBook lid normally suspends the process. For unattended execution the Mac should remain powered, online and physically awake/open.

GitHub should record strategy changes and execution milestones only. Do not commit a five-minute heartbeat to the repository.

Execution state:
`BRACKET_R1_RUNNING_AUTOPILOT_READY_FOR_INSTALL`.


## Autopilot installed and running — 2026-09-26

User-side validation completed successfully.

Observed:
- one-shot autopilot heartbeat at sweep 258;
- reference: 224.23;
- reference age: 116 seconds;
- next static cohort: T02;
- bracket round: 1;
- LaunchAgent plist passed `plutil -lint`;
- service `com.lxx.technocore-close-call` is `state = running`;
- `active count = 1`;
- current process is `/usr/bin/caffeinate` wrapping `uv run ... close_call_fleet.py autopilot --poll 60 --late-minutes 180`;
- working directory is `~/ChatGPT_mission_record`;
- `KeepAlive` and `RunAtLoad` are active;
- stdout/stderr log paths are configured under `~/Library/Logs/`.

The reported `last terminating signal = Terminated: 15` is consistent with the installer intentionally booting out/kicking the service during reinstall/restart and does not indicate the currently running process has failed.

Operational consequence:
- T02 at 2026-09-27 04:00 Asia/Bangkok is eligible for unattended automatic execution, subject to the same live fleet gate;
- user presence is not required for ordinary overnight sweeps;
- Mac must remain powered, online, logged in, and physically awake/open;
- code updates require a service restart before the running Python process will load the new version.

Execution state:
`AUTOPILOT_RUNNING_T02_ARMED`.


## Long-running operation and progress view — 2026-09-26

The system is now treated as a contest-lifetime service rather than a sequence of manual five-minute actions.

User-facing progress is intentionally reduced to the metrics that matter:
- whether the strategy has active coverage;
- current referee mark;
- static cohort completion;
- current bracket round/status;
- whether any fleet DID appears on the official live PnL board;
- the official live-board entries themselves;
- simple gross mark-to-entry movement for the strategy, clearly separated from official score.

Runner commit `f6beb29ac87a8732b05149e79a3a3c232f20b0fc` adds:
- `progress` command;
- trading actions disabled automatically at the official lock;
- post-lock monitoring until the final-price window;
- clean autopilot exit after 2026-10-04 10:15 UTC.

Installer commit `4ae3aa363fbfadd0b5ec6d339b688a47a29352bf` changes LaunchAgent restart policy:
- crashes/non-zero exits restart;
- a normal contest-complete exit remains stopped.

Official public progress surface:
- `d-close1-pnl`: live PnL board;
- `d-close1-positions`: aggregate open interest and position leaderboard;
- `d-close1-price`: current referee reference;
- `d-close1-state`: owner/room counts.

Important rank limitation:
the official live PnL post is a compact top subset. If none of our DIDs appears there, the public room proves only that the fleet is outside that published subset. It does not expose an exact overall rank for every owner. Exact final ordering comes from the final fold/standings.

Remaining strategic engineering gap:
Bracket rounds 2-4 are not yet safe for unattended rollover. The public flow can omit individual settled/void outcomes, so blindly sending a reverse trade could accidentally open a position if the preceding open was actually void. Until a reliable per-key position/outcome proof is available, automated rollover remains intentionally blocked. Static T02-T16 is already unattended.

Execution state:
`LONG_RUNNING_PROGRESS_VIEW_READY_BRACKET_ROLLOVER_PENDING`.
