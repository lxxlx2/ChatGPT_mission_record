# Close Call strategy activity record

Date: 2026-09-26
Project: FLOP Technocore Close Call
Contest: `close-1`
Status: ACTIVE

## Activity purpose

Record the strategy design and operating model used for the Close Call contest so the full decision path can be audited after the event.

The key design change was moving away from manual five-minute interaction and treating the contest as a long-running, stateful trading service that operates continuously until the official final window.

## Strategy objective

Primary objective:
- get at least one fleet DID into one of the three final prize places.

The live Top board is used only as an indicator of competitiveness. The actual success condition is the final fold output assigning one of our DIDs a prize place.

## Fleet design

Fixed fleet size: 52 owner keys.

Allocation:
- 32 keys: 16 static long/short time-layer pairs;
- 16 keys: four-round bracket strategy;
- 4 keys: baseline / reserve.

The fleet is deliberately capped. Expansion above 52 keys is not automatic.

### Static time-layer idea

Every scheduled cohort creates one long key and one short key at the same fresh referee reference.

Purpose:
- cover different entry points across the remaining contest window;
- allow whichever side is favoured by the final price to retain the upside;
- avoid repeatedly disturbing earlier good entries;
- avoid unnecessary churn and additional fees.

Static keys hold through final settlement after opening.

### Bracket idea

Round 1:
- 16 keys form 8 matched long/short pairs.

At each rollover:
- close the current pairs near a fresh referee reference;
- the price-favoured member of each pair survives;
- survivors are paired again;
- open the next round at the next fresh reference.

Counts:
- R1: 16 keys / 8 pairs;
- R2: 8 survivors / 4 pairs;
- R3: 4 survivors / 2 pairs;
- R4: 2 survivors / 1 pair;
- R4 is held through final.

Survivor rule follows the official simulator:
- if rollover price >= round opening price, keep the long member;
- otherwise keep the short member.

## Runtime model

Manual five-minute clicking is intentionally rejected.

The Mac runs a persistent local service:
- `launchd` starts it at login;
- `caffeinate` prevents idle sleep while the machine is open;
- the process polls live referee state every 60 seconds;
- it reacts to scheduled strategy events, not every sweep;
- crashes are restarted automatically;
- clean contest-complete exit remains stopped.

The machine still needs to remain powered, online, logged in and physically awake/open.

## Safety gates

Before automatic trading:
- referee price must be fresh;
- price / flow / state must be aligned;
- dedicated trading room must be registered;
- all retained owner registrations must be valid;
- the dedicated room must have no referee missed range;
- duplicate static cohorts are refused;
- bracket rollover state is saved after every completed step.

This makes restarts resumable and prevents a full re-run from duplicating already-submitted trades.

## Referee observability limitation

The public `d-close1-flow` feed is truncated.

Consequences:
- many individual `settled` and `void` outcomes are omitted;
- absence of a trade ID from the visible flow cannot prove failure;
- explicit visible voids are treated as hard blockers;
- omitted outcomes are handled using retained signed submission evidence plus the dedicated-room no-missed condition.

This remains an inference model. It is weaker than direct per-key settlement proof, but it is the strongest reliable operating model available from the public referee surface.

## User-facing monitoring

The raw Technocore rooms are machine-oriented JSON and are not used as the main human interface.

Primary user view:
`http://127.0.0.1:8765`

Dashboard shows:
- whether any of our DIDs are on the official live board;
- our published tied rank when visible;
- otherwise `Top N 外`;
- leader score;
- current prize-zone score line;
- static strategy completion;
- bracket round and status;
- estimated best strategy score;
- current sweep / ref / mark health.

The dashboard automatically maps public DIDs back to local labels such as:
- `TIME-01-L`;
- `TIME-01-S`;
- `BR-07`.

Private seeds are never exposed or committed.

## Ranking interpretation

Official `d-close1-pnl` publishes only a compact Top subset.

Therefore:
- if one of our DIDs is visible, the dashboard can identify its public tied rank;
- if none is visible, the only defensible statement is `Top N 外`;
- exact live global rank below the published subset cannot be derived from current public data.

The dashboard marks rows occupying prize places 1-3, including ties that span those places.

Final truth comes from the official final fold standings, not from the live board.

## Current activity snapshot

At the time this record was created:
- Static completed: 1 / 16;
- Bracket: Round 1 submitted;
- Bracket pairs: 8;
- strategy wallets submitted: 18;
- current public status: outside the published Top 25;
- no manual action is currently required after the latest autopilot restart.

## Operating principle

Human attention should focus on:
- whether the strategy enters the prize zone;
- whether the estimated score is improving;
- whether the autopilot becomes blocked by an explicit error.

Routine sweep details, raw flow omissions and low-level room traffic are implementation diagnostics and do not need regular manual review.

## Related implementation commits

Key strategy / runtime commits include:
- `43ceb95ca08d4a9ef89b46620947f636e7fcb44d` unattended static autopilot;
- `e372809b2cbc1361dfb68a6dc9e6c1891a660cdb` resumable bracket rollovers;
- `159280fa651cca0dfd48aad77417da868fcee216` local dashboard;
- `19127f7912a5e4351c23a60a7f9b4438716916a7` prize-zone dashboard;
- `0993f7ec97bbadd38fb51f3f8206a69fc9096495` estimated score view.

This file is an activity record. The canonical operating plan remains:
`crypto-300-profit-mission/positions/flop-close-call.md`.


## 2026-09-27 04:00 Asia/Bangkok — T02 unattended execution proof

Local LaunchAgent status supplied by the operator:
- autopilot: `state = running`, PID 15723;
- dashboard: `state = running`, PID 21579;
- dashboard previous exit code 143 is consistent with an intentional kickstart/restart;
- autopilot stderr was empty.

Autopilot log proof:
- sweep 395 observed before the scheduled T02 action;
- at 2026-09-26T21:00:21Z the service emitted `event=static_action`;
- cohort: `02`;
- result: `submitted`;
- trade id: `t02-1790456420`;
- long: `TIME-02-L`;
- short: `TIME-02-S`;
- quantity: `40.70`;
- submitted price: `224.39`;
- dedicated room sequence: `74`;
- next heartbeat at 2026-09-26T21:01:21Z advanced `next_static` to `03`.

This is direct proof that the unattended Static scheduler executed T02 on schedule without manual trade submission.

### Freshness hardening discovered during T02 review

The live log review exposed a subtle implementation issue in `fresh_price()`: the referee's posted `age_s` value was being treated as if it continued to age after the post. In practice the field is a snapshot value carried in the message, so the local gate could understate wall-clock staleness until a new price post arrived.

Fix:
- commit `ce1316dc73c5e6bc195ff89feaf61f7a76dfd538`;
- derive wall-clock age from `ref.time` on every read;
- effective age is now the maximum of referee-reported age and locally derived age;
- the 120-second trading freshness gate therefore blocks stale references even when the embedded `age_s` remains small.

Dashboard follow-up:
- commit `ad61b96e5bde346e89e7ca9b0c1400cd5ddf0b2a`;
- the user-facing status bar now shows the latest completed automatic action, so routine health checks do not require terminal log inspection.

Operational conclusion:
- T02 submission automation is proven working;
- the process and LaunchAgents are alive;
- no stderr error was present;
- future scheduled trades should use the hardened dynamic freshness check after the local service is restarted onto the latest code.


## 2026-09-27 — Competitive-strategy diagnosis after live-board review

A material flaw was found in the initial 52-key strategy after comparing the live board shape with the official rules, official simulator and issue #8 measurements.

### What the live board is showing

The user observed the recurring pattern:
- one account alone in first;
- most or all of the remaining published Top 25 tied at one identical score;
- our best key outside the published Top 25 despite holding both long and short tickets.

This pattern closely matches the read-only measurements published in official repository issue #8. At sweep 370 the measurement reported:
- 1,763,029 owner keys;
- 417,304 keys holding positions;
- one leader at 196.60;
- 24 published keys tied at 189.14;
- top position-size accounts at approximately the maximum size.

Issue #8 explicitly notes that under the frozen identity rule, one operator can hold both sides across every sweep and therefore own the best long and best short entry; tie handling then makes fleet size and entry timing dominant.

### Core mistake in our initial design

The initial design optimized robust directional coverage:
- exact-ref long/short pairs;
- static entries every 12 hours;
- only 52 total keys;
- conservative quantity sizing;
- bracket rollovers.

That is sensible for a capped-player trading game, but close-1 does not cap owner keys and ranks every key independently.

The actual objective is the maximum individual-key score, not combined fleet PnL.

### Fee/clawback asymmetry we underused

The frozen fold charges each side:
- base fee = 1% of trade value;
- but a side receiving a price better than the sweep close pays the favorable price gap instead when that gap is larger.

This means a favored key can be paired with a sacrificial feeder at an off-market price inside the 5% band so that:
- the favored key's nominal price advantage is exactly clawed back;
- its economic effective entry becomes the sweep close;
- it avoids paying an additional 1% base fee on top of that effective entry;
- the feeder absorbs the unfavorable side/base-fee economics.

This exact behavior is discussed in issue #8 comments as a way operators manufacture many identical max-size entries every sweep. The official fold test `test_the_harvest_nets_nothing` separately confirms that buying at the bottom and selling at the top cannot create net value for one flat account; the useful fleet effect is concentrating ticket quality on favored keys while sacrificing other keys, not creating value from nothing.

### Why our current keys trail

Our exact-ref pair starts approximately one base fee behind:
- around 91 POLF of fee for a 40.7-contract ticket near NVDA 224;
- a manufactured favored ticket can make its effective entry approximately the sweep close without that extra base-fee handicap;
- our 12-hour spacing also misses many locally superior long/short entry times;
- our quantity is conservative relative to the approximately max-sized positions observed near the top.

Therefore “we have both long and short” only protects direction. It does not guarantee competitive score because the contest rewards the single best key and competitors can create long and short tickets at far more timestamps.

### Current execution implication

No trade is changed by this note. T01 and T02 remain valid lottery tickets.

However, the current plan for T03-T16 exact-ref static entries and later bracket churn is now considered strategically under review. Before the next scheduled unused-key deployment, the preferred redesign is:
- stop treating 52 keys as an arbitrary hard competitive cap;
- optimize for best-key order statistics rather than total fleet robustness;
- use fee/clawback-aware favored/feeder constructions;
- increase timing density substantially;
- reassess whether bracket rollovers add enough value after repeated fees.

Execution state:
`STRATEGY_REVIEW_REQUIRED_BEFORE_T03`.


## 2026-09-27 — Dense favored-ticket redesign implemented

Following the live-board diagnosis, the runtime now supports an optional replacement strategy that targets the contest's actual scoring objective: maximize the best individual owner-key score.

Implementation commits:
- `f2269415f5d934050e0655a24db2e5b576030793`: dense sweep-ticket strategy;
- `fa5b3da49a6c2d5c7d502df4e93f32a00605305f`: dashboard support for dense mode.

### Dense construction

When enabled, the legacy future Static schedule and Bracket rollovers are frozen. Existing T01/T02/Bracket-R1 positions are left untouched and remain valid tickets.

For each fresh referee sweep the dense pipeline creates three fresh local keys:
- one favored long target;
- one favored short target;
- one sacrificial feeder.

Registration is pipelined one sweep before trading. Once a registration batch has had a later aligned referee sweep with no dedicated-room miss, the next ticket pair is submitted from the current fresh reference.

Prices:
- favored long target receives a buy at approximately `ref × 0.98`;
- favored short target receives a sell at approximately `ref × 1.02`;
- both trades remain inside the frozen ±5% price window.

The same feeder is used for both trades in deterministic order:
1. feeder sells low to the long target;
2. short target sells high to the feeder.

The feeder therefore opens and closes inside the pair while the two target keys retain the long and short tickets.

Quantity:
- calculated with a conservative funds factor of 1.05;
- includes room for the high-side target's favorable-price clawback and a modest close-vs-reference move;
- current formula is `0.995 × 10000 / (ref × 1.05)`, floored to 0.01.

### Why this is better aligned with close-1

Under the frozen fold, the favored side pays the larger of:
- 1% base fee; or
- its favorable price gap versus the sweep close.

At a sufficiently off-market but still valid price, the gap/clawback becomes the fee. The favored target's effective economic entry approaches the sweep close without an additional 1% base-fee handicap.

The feeder absorbs the unfavorable economics and is disposable.

Two fresh targets are created per sweep so both final directions remain covered. Over many sweeps this converts the strategy from sparse 12-hour directional coverage into dense order-statistic coverage.

### Safety / operational constraints

- dense mode is opt-in;
- hard local safety cap: 8,000 dynamic keys;
- private seeds stay only in the existing local 0600 state file;
- one batch is processed at most once per referee sweep;
- registration batches are persistent and resumable;
- public flow/state must align before using a registered batch;
- a dedicated-room missed range pauses the batch;
- dynamic referee freshness remains capped at 120 seconds;
- contest lock still stops trading;
- existing positions are never automatically closed by enabling dense mode.

### Commands

Enable after updating and restarting the runner:

```bash
uv run crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py enable-dense
bash crypto-300-profit-mission/tools/technocore-close-call/install_autopilot_macos.sh
```

Read-only status:

```bash
uv run crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py dense-status
```

Emergency stop for new dense ticket creation:

```bash
uv run crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py disable-dense
```

Execution state:
`DENSE_MODE_IMPLEMENTED_OPT_IN_REQUIRED`.


Follow-up safety commit:
- `0009f71c721b17af99baeb40eff0ac097936ad80`: once dense mode is enabled, the old Static/Bracket automation remains frozen even if dense mode is later disabled. Disabling dense therefore stops new dense ticket creation without silently resuming the superseded strategy.


## 2026-09-27 — Dense startup readiness fix

Live dashboard review showed Dense mode enabled with zero submitted sets while the referee reference was stale.

The original Dense loop checked trading freshness before creating the first pending batch. That was unnecessarily conservative because owner registration itself does not depend on the trading reference. It could waste the first future fresh sweep on registration instead of trading.

Fix commit:
- `1fa7a253878e71c1906588ef522ba0f4ca579d67`

New behavior:
- keep one Dense batch pre-registered even while the referee trading reference is stale;
- continue to block the actual favored-ticket trades until effective ref age <= 120 seconds;
- once a fresh sweep arrives and the registration has had at least one later sweep, the pending pair can submit immediately;
- `dense-status` now prints the current ref sweep, effective age, trade-freshness boolean, pending batch index/status and ready-after sweep.

This preserves the freshness safety gate while improving first-ticket readiness.


## 2026-09-27 — Dense first-fresh-sweep retry hardening

Live status reached:
- `ref_sweep: 405`;
- `effective_ref_age_s: 110`;
- `fresh_for_trade: True`;
- pending Dense batch #1 registered and ready;
- `submitted_sets: 0`.

Review found a retry edge case: if the first autopilot poll on a fresh sweep saw price sweep 405 before flow/state had both caught up to 405, the loop returned `dense_wait_alignment` but had already marked sweep 405 as seen. A later poll on the same sweep would then emit a heartbeat instead of retrying the ready pending batch.

Fixes:
- `8f3f7157b2638d674b16a6a3c64d9daffc33b3cf`: retry a ready Dense pending batch repeatedly within the same fresh sweep until flow/state align or the ref ages out;
- `1e2213701d92ace43be609782ae7ce3e89dde97f`: reduce LaunchAgent polling interval from 60 seconds to 30 seconds so the 120-second freshness window gets more attempts.

Execution state:
`DENSE_BATCH_1_READY_FRESH_SWEEP_RETRY_HARDENED`.


## 2026-09-27 — Dense batch #1 submitted; dashboard estimate gap fixed

Observed runtime proof:
- Dense batch #1 submitted on sweep 405;
- long target: `DENSE-00001-L`;
- short target: `DENSE-00001-S`;
- feeder: `DENSE-00001-F`;
- ref: `224.46`;
- low/high prices: `219.97 / 228.94`;
- qty: `42.21`;
- batch #2 was immediately pre-registered and is waiting for a fresh tradable reference.

The next observed referee state was sweep 406 with effective ref age above the 120-second trading threshold, so batch #2 correctly remained pending.

A dashboard defect was found at this point: estimated best-score logic still considered only legacy Static and Bracket tickets. Dense tickets could therefore be the strongest local candidates while the dashboard continued displaying a legacy ticket such as T01.

Fixes:
- `ea6944965f6c30ccd1629954e810e71989ce8522`: include submitted Dense tickets in local best-score and prize-target estimates. Dense estimates use the ticket ref as a transparent proxy for effective entry because the exact sweep close/clawback may be omitted publicly.
- `3941a1ebb8d0d58c2623ce8445cc607cb06f6377`: `dense-status` now also reports visible settlement/void status for the latest Dense long and short trades, or reports NOT_VISIBLE together with public omitted outcome counts.

Important distinction:
`dense_ticket_submitted` proves the signed trade messages were posted. It does not by itself prove referee settlement. Settlement status is now surfaced separately.


## 2026-09-27 — Active-room gate added after first Dense batch

Runtime status after Dense batch #1:
- `submitted_sets: 1`;
- batch #2 registered and waiting;
- latest Dense long/short outcomes were `NOT_VISIBLE`;
- public flow reported very large omitted settlement and void counts, so absence from the compact flow is inconclusive.

During review, official issue #8 was rechecked. Its later measurement notes that the active registered-room count fell sharply because technocore.chat rooms can disappear from the referee's current room list. Rule 5 also states that a deleted room leaves the list.

The previous Dense submit path verified flow/state alignment and no missed range, but did not require the dedicated room to be present in the *latest* flow room list. A historically registered room could therefore theoretically receive locally acknowledged posts after it had ceased to be an active referee room.

Fix:
- `52eff376b31a296d4e841330d1717d63486b047f`
- Dense submissions now require the dedicated room to be listed in the latest aligned flow;
- if absent, the controller re-posts the room registration in `close1` once for that sweep and waits for a later sweep to list it;
- `dense-status` now prints `room_active_in_latest_flow` and `latest_flow_sweep`;
- the general fleet gate now treats room registration as a current-state condition rather than historical-ever-seen evidence.

Important: this hardening protects future Dense batches. It does not retroactively prove batch #1 settlement. Batch #1 remains `submitted, outcome not publicly visible` until stronger evidence appears.


## 2026-09-27 — Dense batch #2 submitted; room-health visibility corrected

Observed runtime:
- `submitted_sets: 2`;
- Dense #2 submitted on sweep 408 with ref `224.39`, qty `42.23`;
- Dense #3 is already registered with `ready_after_sweep: 409`;
- current ref at the captured check was sweep 408, effective age 120 seconds, so #3 correctly waits for sweep 409 or later;
- latest #2 long/short compact-flow outcomes remain `NOT_VISIBLE`, with large omitted settled/void counts, so public compact flow is inconclusive.

Because #2 was submitted after the active-room gate was deployed, the current-room check necessarily passed at submission time.

A visibility bug was also found: `room_active_in_latest_flow` had accidentally been printed from the Dense registration helper instead of `dense-status`, so the read-only status command did not show the field even though the trading gate itself was enforcing it.

Fixes:
- `1c21f29e73dec09f0ce54db45517986a3ab18781`: move active-room reporting into `dense-status`;
- `dac977ee75d17c3b457b4efa9fe03d6159cd833b`: dashboard now explicitly surfaces room re-registration/health state.


## 2026-09-27 — Pending-owner recovery after room expiry

Live status reached:
- `submitted_sets: 2`;
- Dense #3 registered and waiting;
- latest flow sweep 409;
- `room_active_in_latest_flow: False`;
- current reference was fresh enough to trade.

This exposed a second-order room-expiry risk. Even though the runtime already blocked trades and auto-reposted the room registration, a pending Dense batch's owner-registration messages may have been posted while the room later disappeared before the referee consumed them. Re-registering only the room would not positively guarantee those pending owner messages were read.

Fix:
- `ac3a0a8368f41d01c071370e7bf01e0786e567b0`

New recovery sequence:
1. if the dedicated trading room is absent from the latest aligned flow, mark the pending Dense batch as requiring owner re-registration and re-post the room registration in `close1`;
2. wait until a later flow lists the room again;
3. re-post all three pending owner registrations inside the now-active room;
4. set `ready_after_sweep` to one sweep later;
5. only then allow the long/short favored-ticket trades.

Duplicate owner registrations are harmless under frozen rule 3, so this favors positive safety over assuming an earlier pending owner message survived room expiry.

`dense-status` now also reports:
- `pending_needs_owner_reregister`;
- `pending_owner_reregister_count`.


## 2026-09-27 — Room recovery moved ahead of price freshness gate

Observed runtime after room recovery:
- `room_active_in_latest_flow: True` at sweep 410;
- pending Dense #3 still had `pending_owner_reregister_count: 0`;
- current ref was stale (`effective_ref_age_s: 345`), so trading correctly remained blocked.

This exposed an efficiency gap in the previous recovery sequence: owner re-registration after a room recovery lived inside the trade-submission path, which only ran after the ref freshness gate. A recovered room could therefore sit idle with stale price data even though owner re-registration itself does not depend on price freshness.

Fix:
- `1d8a1c5d36f78a07c013c612ee280862564655ee`

New order:
1. maintain/re-register the room if absent;
2. if the room has returned, re-post the pending batch's owner registrations immediately, even with a stale ref;
3. move `ready_after_sweep` to one later sweep;
4. only after these non-price prerequisites are healthy apply the <=120s trading freshness gate.

This should let the next genuinely fresh sweep be used for trading rather than for administrative recovery.


## 2026-09-27 — Corrected flow.rooms interpretation

Live status showed:
- `room_active_in_latest_flow: False` at sweep 413;
- a room-registration re-post had just been issued;
- the same room had appeared in sweep 410 and then disappeared again from later compact flow posts.

Review of the frozen protocol showed the earlier health interpretation was too strong. The per-sweep `flow.rooms` field is a registration/event list for that sweep, not a durable full membership list that every later flow must repeat. Rule 5 says a room counts from the sweep that lists it; absence from a later flow post does not by itself prove deregistration. The state room count can fall when technocore.chat deletes an idle room, but our dedicated room is continuously written while the autopilot runs.

Fixes:
- `b65f85de44d349039417ee9cdca2d39770e502a2`: persist room-registration confirmation locally once observed, stop treating absence from the latest flow post as room inactivity, expose recent room activity age, and keep `flow.rooms` only as a per-sweep registration-event diagnostic.
- `659aa1a72027839346dfe0467d6855e9beb4856a`: dashboard now uses persistent room-registration confirmation instead of the misleading latest-flow membership test.

The pending Dense #3 batch had been marked for owner re-registration by the old false-positive room check. The corrected runtime keeps that harmless safety re-post path for this one pending batch, then returns to normal persistent-room semantics.


## 2026-09-27 — Dense #3 recovery completed; waiting only on fresh reference

Operator status after the room-semantics correction:
- `submitted_sets: 2`;
- `room_registration_confirmed: True`;
- dedicated room recent activity age: 8 seconds;
- latest flow sweep: 415;
- `room_listed_in_latest_flow_registration_events: False`, which is informational only under the corrected per-sweep registration-event interpretation;
- pending Dense #3 is registered;
- owner re-registration recovery completed once: `pending_owner_reregister_count: 1`;
- `pending_needs_owner_reregister: False`;
- `pending_ready_after_sweep: 415`;
- current reference sweep 415 had effective age 126 seconds, so `fresh_for_trade: False`.

Conclusion: the administrative recovery path is complete. Dense #3 is eligible by sweep number and owner-registration state; the only active gate at this snapshot is the <=120-second reference freshness requirement. No manual intervention is required.


## 2026-09-27 — Stable leaderboard gap diagnosis and competitor scan added

Observed dashboard snapshots repeatedly showed an almost constant gap between our best estimated Dense score and the public prize cutoff:
- 73.45 vs 156.07 -> 82.62 POLF gap;
- 66.69 vs 149.52 -> 82.83;
- 54.45 vs 137.44 -> 82.99;
- 42.21 vs 125.09 -> 82.88;
- 6.75 vs 85.54 -> 78.79.

Because Close Call score is approximately linear in mark for a fixed one-sided position, an almost parallel score gap strongly suggests the leading/prize-line tickets have similar directional exposure but a materially better historical effective entry, rather than a newly changing live tactic. At our ~42.2 contract size, an ~82 POLF intercept gap corresponds to roughly $1.9-$2.0 of effective entry advantage.

Official-repo issue #8 independently measured the same structural pattern: fleets spanning both sides across every sweep, large tie groups, and near-max-size positions. It also documents that operators can manufacture many identical favored entries in one sweep, so multiplicity remains a separate prize-sharing disadvantage even if our best score eventually matches the same sweep.

A new read-only diagnostic command was added:
- commit `5bfca6f8c6f8136b4cd7acc38f6df81513d4c89d`;
- command: `competitor-scan`;
- reads only public referee/close1 rooms;
- reports recent PnL tie structure, top positions, recent trade-template concentration, and large-qty price deviations;
- performs no signing and does not modify local strategy state.

This is intended to distinguish a genuinely new competitor construction from the already-known dense/multiplicity strategy before changing live execution parameters.


## 2026-09-27 — Competitor scan confirms historical-entry gap + live multiplicity

Read-only competitor scan at sweep 460 produced a much clearer diagnosis.

### Public leaderboard geometry

Across sweeps 449-460 the public board repeatedly showed:
- one leader;
- 24 visible keys tied at the same second score;
- the second-score group moved almost perfectly linearly against mark.

Linear fit from the scan:
- leader score slope ≈ -41.65 POLF per $1 mark move;
- 24-way tie score slope ≈ -41.82;
- implied effective short entry ≈ 226.65 for the leader;
- implied effective short entry ≈ 226.45 for the tied prize-line fleet.

Our current Dense quantity is about 42.21 and our best recent effective entry is around 224.46. The implied historical-entry gap is therefore about $1.99, worth roughly 82-84 POLF at ~42 contracts, matching the dashboard's observed stable ~79-83 POLF deficit.

Conclusion: the stable gap is overwhelmingly explained by an older, better short entry. It is not evidence that the current Dense tickets are paying an extra hidden fee.

### Quantity conclusion

The top *score* group is inferred at only ~41.8 contracts, while our Dense tickets are ~42.2. Therefore the 44.87 values seen in the separate top-position-size board should not be treated as the score benchmark. Chasing 44.87 solely because it appears in d-close1-positions would be a category error.

### Current competitor templates

The latest 400-message close1 sample contained coordinated templates:
- 8 makers: buy 222.25, qty 42.00, until 2556;
- 8 makers: sell 226.75, qty 41.00, until 2556;
- with ref 224.50 these are approximately -1% / +1%;
- other large-quantity activity clustered near -2% and +1.3%.

This is concrete evidence that at least one active fleet is currently duplicating same-sweep entries across multiple owner keys, and that ±1% constructions are actively used alongside ±2% variants.

Official issue #8 independently reports:
- 24 visible tied rows;
- an estimated ~115 keys in the tied group at sweep 436;
- same visible tie leaders persisting since sweep 19;
- hundreds of identical favored entries can be manufactured per sweep under the frozen clawback rules.

### Strategic implication

Current Dense timing coverage is directionally correct. The remaining competitive gap has two components:
1. historical entry advantage, which cannot be retroactively manufactured because clawback collapses favorable trade prices toward the current sweep close;
2. multiplicity / tie-share disadvantage, which *can* still be improved by cloning future favored entries across more keys.

The scan does not justify increasing qty solely to 44.87. It does justify evaluating:
- reducing the favored offset from ±2% toward ±1% for lower feeder burden while preserving approximately sweep-close effective entry;
- multiple copies per fresh sweep, or adaptive copies on new reference extrema, to improve prize sharing if a future sweep becomes the winning entry.

No live execution parameter was changed by this note.


## 2026-09-27 — Dense V2 implemented after competitor-template scan

The user approved the V2 redesign after the public competitor scan showed:
- persistent ~80 POLF historical-entry disadvantage;
- coordinated same-sweep copy templates;
- active ±1% constructions around the current reference;
- prize-line position slope around 41.8 contracts, so increasing quantity toward 44.87 was not justified by the score board.

Implementation:
- `e115a28fed7b1da020aa5e0094aaaca7d5763a8a`: Dense V2 runtime;
- `9da1aea0ac515bc41f5df5770d63dee393e511c1`: Dashboard support.

Dense V2 keeps the existing baseline coverage:
- one favored long and one favored short on each eligible fresh sweep;
- existing Dense tickets and current pending batch remain intact.

Changes:
- favored price offset changes from ±2% to ±1% after V2 is explicitly enabled;
- historical Dense reference low/high are initialized from already-submitted Dense tickets;
- new all-time Dense ref high => short side is boosted to 8 total copies for that sweep;
- new all-time Dense ref low => long side is boosted to 8 total copies;
- the baseline ticket counts as copy #1, so an extreme uses up to 7 additional target/feeder pairs;
- a pre-registered reserve pool of 16 generic target/feeder pairs is maintained so extreme copies can be sent on the same fresh sweep;
- consumed reserve pairs are replenished automatically;
- the existing 8,000 dynamic-key hard safety cap remains in force;
- boost submission is best-effort and recorded separately, so a boost shortage/error does not discard the baseline dual-direction ticket.

New command:
```bash
uv run crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py enable-dense-v2
```

Dense status now includes:
- `v2_enabled`;
- active offset;
- historical low/high ref;
- extra boost-ticket count;
- registered/ready reserve counts.

Dashboard now shows:
- Dense V2 baseline count;
- Extreme Boost extra-ticket count;
- reserve readiness;
- historical ref range;
- boost tickets in local best-score estimation;
- side-aware prize targets for one-sided boost tickets.

Migration behavior:
- V2 is explicit opt-in;
- the currently pending V1 batch is preserved and will use V2 pricing when submitted after enablement;
- the first V2 extreme may have fewer than 8 copies if the reserve pool has not yet aged through one referee sweep;
- after reserve priming, later new extrema can use the full configured multiplicity.

Execution state:
`DENSE_V2_IMPLEMENTED_ENABLE_AND_RESTART_REQUIRED`.


Dense V2 follow-up capacity hardening:
- `5d76eadde01fced968d7614cc72b47de29d12d78`: dynamic-key hard cap raised from 8,000 to 40,000 so baseline coverage plus extreme multiplicity can continue through the remaining contest under a much larger range of price paths; `dense-status` now reports used/remaining key budget.
- `e635ca96e1ec12c13918262387db1c6d9d558990`: dashboard shows Dense V2 key usage and remaining budget.


## 2026-09-27 — Dense V2 enabled successfully in live runtime

User-side activation proof after pulling the V2 commits and reinstalling the LaunchAgents:
- `enabled: True`
- `v2_enabled: True`
- `submitted_sets: 50`
- `v2_offset: 0.01`
- historical Dense ref range: `224.39 .. 224.62`
- `boost_tickets: 0`
- `boost_reserve_registered: 16`
- `boost_reserve_ready: 0` at referee sweep 498, as expected because the newly registered reserve pairs require one later sweep before they are eligible
- `dynamic_keys: 185 / 40000`
- remaining dynamic-key budget: `39815`
- dedicated room registration remains confirmed
- pending Dense #51 is registered with `ready_after_sweep: 499`
- current reference at the captured check was sweep 498, ref 224.60, effective age 291s, so trading correctly remained paused by the <=120s freshness gate.

The last submitted ticket (#50) still shows the old ±2% prices (220.10 / 229.09) because it was submitted before V2 was enabled. The preserved pending #51 will use the V2 ±1% offset when it is submitted.

Minor observability fix:
- `8d93c180a6bafe8c6343657f2317441cc7c5368e` makes `dense-status` calculate reserve readiness from the current referee sweep instead of the last processed sweep, eliminating a one-sweep display lag.

Execution state:
`DENSE_V2_LIVE_WAITING_FOR_SWEEP_499_AND_FRESH_REF`.


## 2026-09-28 — Dense V3 every-sweep multiplicity implemented

The user approved replacing the V2 extreme-only boost after the live board showed a new short cohort overtaking the old leaders while our strategy still carried a stable ~90 POLF deficit.

Diagnosis:
- the new prize-line score implied a materially better short entry than our best historical Dense ref;
- V2 used ±1%, which can fail to claw back a fast within-sweep move of roughly 1%;
- V2 only multiplied *after* a new ref extreme became visible, so the first sweep that actually created the extreme could be missed;
- the custom <=120s underlying-market trade-age gate skipped many otherwise valid referee sweeps even though the referee continued publishing authoritative sweep/ref data.

Dense V3 changes:
- participate in every aligned referee sweep;
- remove the custom 120-second ref-age trading gate for V3 only;
- keep referee price/flow/state alignment, room-registration, missed-range and contest-lock safety gates;
- restore favored offset to ±2%;
- target 8 long copies and 8 short copies on every eligible sweep;
- baseline copy remains the existing 3-key Dense batch;
- 7 additional paired copies each use their own long target, short target and feeder;
- maintain 16 pre-registered V3 reserve copy-sets, each 3 keys, so same-sweep multiplicity does not wait for owner registration;
- reserve copy-sets are replenished automatically after use;
- partial copy failures are quarantined as `partial_error` and never reused;
- dynamic-key hard cap raised to 60,000 for contest-lifetime coverage;
- existing V1/V2 positions and pending baseline batch are preserved.

Implementation commits:
- `baae0165c3302f09da27cc50ed6e9f94406ef93e`: Dense V3 runtime;
- `c4cc5d0829b87d7ff65f9222d3ec3405a1e2358a`: V3 dashboard;
- `f48e0543d42c580459b4092ada1a152114316fb4`: partial-copy failure quarantine/status;
- `8e35c954b646c04cec7d62a9e0d82942459391c8`: dashboard copy-health visibility.

Enable command:
```bash
uv run crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py enable-dense-v3
```

Expected post-enable status:
- `v3_enabled: True`;
- `active_offset: 0.02`;
- `v3_total_copies_per_side: 8`;
- `ref_age_gate_enabled: False`;
- `v3_reserve_registered: 16` after reserve priming;
- `v3_reserve_ready: 16` one later referee sweep after priming;
- each fully supplied V3 sweep records `last_v3_long_copies: 8`, `last_v3_short_copies: 8`.

Execution state:
`DENSE_V3_IMPLEMENTED_ENABLE_AND_RESTART_REQUIRED`.


Dense V3 startup hardening:
- `1cef79ddb830d4d9db2cf7943ba8e6a01433918c` primes all 16 V3 reserve copy-sets synchronously when V3 is enabled and records `v3_not_before_sweep = enable_sweep + 1`.
- This prevents the preserved pending baseline batch from firing immediately with only 1L/1S before the reserve multiplicity keys have aged through one referee sweep.
- The first V3 trade therefore waits until the pre-registered reserve can support the intended 8L + 8S construction.


## 2026-09-28 — Dense V3 enable verification and dashboard legacy-schedule fix

User-side enable/status output verified:
- Dense V3 enabled successfully;
- enable sweep 830;
- first V3-eligible sweep recorded as >=831;
- baseline submitted sets 317;
- pending baseline index 318, ready after sweep 831;
- V3 reserve registered 16, ready 0 on the enable sweep as expected;
- no V3 partial reserve errors;
- ref-age gate disabled while referee alignment/room safety remains active;
- local dynamic keys 1566 / 60000;
- room registration confirmed.

The dashboard still displayed an overdue Static T03 message even though Dense mode had already frozen all future legacy Static/Bracket execution. Runtime was safe because `autopilot_iteration()` returns through `dense_autopilot_step()` before legacy scheduling. The issue was display-only.

Fix:
- commit `73104dbb35016575ec06a68bc7e4e3bcb312c978`
- dashboard no longer surfaces Static/Bracket pending schedules while Dense is enabled.


## 2026-09-28 — Sweep 855 competitor scan: board regime switched to historical longs

A 50-sweep / 1,000-message scan at referee sweep 855 materially changed the interpretation of the live board.

Observed:
- mark jumped from 223.83 at sweep 851 to 229.21 at sweep 855;
- prize line moved into the 426-434 POLF area and leader reached 465.97;
- several current Top-25 DIDs also appeared in the public top-position list with +45.10 long positions;
- for those directly matched keys, `effective_entry = mark - score / position` gives roughly 219.60-219.70;
- therefore the current high-price board is dominated by old low-entry longs, while the low-price board seen earlier was dominated by old high-entry shorts;
- this is consistent with a two-sided historical frontier strategy, not evidence that V3 stopped working.

The same public sample showed large coordinated fleets still active:
- 183 distinct makers shared one sell template at 229.40 / qty 42.52;
- 69 makers shared sell 228.61 / qty 42.22;
- another cluster used ±2%-style large trades around the current reference.

Important scanner correction:
The original `competitor-scan` computed every sampled trade's deviation against the *current* reference, which makes historical `dev_pct` labels misleading. A trade shown as +0.35% relative to sweep 855 may have been posted under a different referee reference. Commit `db5e3dc42b826ec871ab2955a728358f58b917e6` fixes this by:
- mapping each sampled trade timestamp to the contemporaneous referee price post;
- reporting source sweep/source ref and true submission-time deviation;
- cross-matching current leaderboard DIDs with public top positions;
- estimating position from score-vs-mark slope when possible;
- estimating effective entry from signed position;
- listing recent public trades involving current top DIDs.

Strategic implication:
- do not change V3 solely because the current board gap widened while NVDA rallied;
- V3 now has the correct mechanism to capture a *future* new short frontier when the market makes a new high, and a future new long frontier on a new low;
- whether competitors are also actively locking/closing profitable historical positions is still unresolved and should be checked with the corrected scan before adding an exit/harvest layer.


## 2026-09-28 — Dense V4 asymmetric clawback ladder implemented

The corrected 2,000-message competitor scan at sweep 856 showed:
- current leaders are historical long positions with effective entries around 218.5-219.7;
- large live trade clusters at submission-time deviations near -5%, -2%, +1%, +1.7% and +2%;
- especially heavy short-side activity around +1% with quantities near 42.2-42.8;
- the prior scan's historical deviation labels were corrected to use each trade's contemporaneous referee ref.

V4 keeps V3's every-sweep bidirectional coverage and 8 copies per side, but changes quote construction:

Long side:
- all 8 copies quote at the referee's exact lower limit, approximately -5%;
- using the posted lower limit avoids one-cent rounding outside the official 5% window.

Short side:
- 3 copies at +1.0%;
- 2 copies at +1.7%;
- 3 copies at +2.0%.

Sizing:
- each paired long/short copy uses one common quantity so its feeder can open at the low quote and close at the high quote without leaving a residual directional lot;
- quantity is derived directly from the frozen fold's cash test under a close≈ref sizing model;
- +1.0% copies use 0.995 cash safety;
- +1.7% copies use 0.99;
- +2.0% copies use 0.98;
- this intentionally creates an aggressive / balanced / robust short ladder rather than forcing one quantity on every offset;
- the model is not a guarantee against arbitrarily large within-sweep moves, and the deeper ladder rungs reserve more free cash to reduce funds-void risk.

Runtime:
- every aligned referee sweep remains eligible;
- the custom 120s underlying-trade-age block stays disabled;
- price/flow/state alignment, room registration, missed-range and lock protections remain enabled;
- V4 reuses the proven V3 3-key paired reserve pool;
- partial copy failures remain quarantined and are never reused;
- existing V1/V2/V3 positions are untouched;
- a mode switch is refused if the current pending batch already contains partial trades.

Implementation:
- `eacc193b1412407c3a6c3dce8f4570b6e8c46341`: Dense V4 runtime;
- `035839860be2b89f27527fb8b96fa717ce34ad8c`: V4 dashboard;
- `71335a7957c1a0f90cb142ec35c10c4fd4d7c082`: V4 preview + safe mode-switch guard.

Read-only preview:
```bash
uv run crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py dense-v4-preview
```

Enable:
```bash
uv run crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py enable-dense-v4
```

Execution state:
`DENSE_V4_IMPLEMENTED_PREVIEW_ENABLE_RESTART_REQUIRED`.


## 2026-09-28 — Dense V4 enable verified locally

User-side runtime verification after pulling through `d65dd86`:

- V4 preview sweep: 861
- referee ref: 227.10
- official limits: 215.75 / 238.45
- V4 long quote: 215.75 on all 8 copies
- short ladder:
  - copies 1-3: 229.37, qty 42.95, +1.0%
  - copies 4-5: 230.96, qty 42.15, +1.7%
  - copies 6-8: 231.64, qty 41.49, +2.0%
- V4 enabled successfully on sweep 861
- first V4-eligible sweep: >=862
- V2 disabled
- V3 disabled
- V4 enabled
- room registration confirmed
- flow/state safety gates remain active
- V3 paired reserve pool available: 16 registered / 16 ready
- pending baseline index 348 already registered
- pending ready-after sweep 861
- no pending owner re-registration requirement
- dynamic keys: 2,286 / 60,000
- V4 multiplicity tickets: 0 at sweep 861, expected because V4 is intentionally gated until sweep 862
- last submitted ticket remains V3 sweep 860, expected before the first V4 execution

Expected first complete V4 post-sweep status:
- `submitted_sets: 348`
- `v4_multiplicity_tickets: 7`
- `last_v4_sweep >= 862`
- `last_v4_long_copies: 8`
- `last_v4_short_copies: 8`
- `last_v4_reserve_shortage: 0`
- `last_v4_errors: 0`

Execution state:
`DENSE_V4_ENABLED_WAITING_FIRST_ELIGIBLE_SWEEP`.


## 2026-09-29 — Sweep 936 realized-PnL carry evidence and scanner slope hardening

A 300-PnL / 10,000-message competitor scan at sweep 936 produced two important findings.

Strong evidence of realized-PnL carry:
- a 14-account cohort occupied ranks 7-20 at exactly 680.27 POLF;
- its latest consecutive-sweep score sensitivity implied a short position of about 43.12 contracts;
- visible referee history had min ref 223.01 and max ref 232.78, so the highest legal single-trade sell price reachable under the 5% limit was about 244.42;
- at mark 230.65, even a perfect 43.12-contract short opened at 244.42 could contribute at most about 593.76 POLF before fees;
- the observed 680.27 score therefore requires at least about 86.51 POLF of previously realized/cash-carried profit, and actual required carry is larger after fees;
- this proves that at least this cohort's current score cannot be explained by one untouched short opened from the original 10,000 POLF alone.

Active management evidence:
- several current leaders show earlier long-like score sensitivity and later reappear in a different regime;
- one current Top-5 DID posted full-size sell trades around 43.62 contracts at 234.72/234.77 on sweeps 934-935, consistent with active closing or direction management.

Scanner correction:
- the prior path diagnostic treated score/mark slopes across sparse top-board appearances as if they were positions. A gap such as sweep 917 -> 936 can include trades and realized PnL, so a value such as -167.38 is not a valid literal position estimate.
- commit `0106f663005cf4862a92012ab089adb19398fcc0` now uses only consecutive referee sweeps for position-slope estimates and labels sparse transition slopes separately as non-position diagnostics.

Strategic implication:
- realized-PnL harvesting is now directly evidenced;
- exact same-account long->short flipping is strongly suggested but should not be considered proven solely from sparse slope transitions;
- V4 should continue as the entry engine while a V5 harvest/flip layer is designed around confirmed settlement/cash reconstruction rather than sparse-board heuristics.


## 2026-09-29 — Dense V5a staged profit-harvest layer implemented

Evidence basis:
- sweep-936 competitor diagnostics proved that a large current short cohort's score exceeded the maximum profit explainable by any single untouched short reachable under the visible 5% price limits;
- therefore at least part of the leading score must be realized/cash-carried PnL from earlier trades;
- active full-size sell management by current Top-5 accounts reinforced the case for adding a harvest layer while keeping V4 as the entry engine.

V5a design:
- V4 remains enabled and continues creating 8 long + 8 short copies every aligned referee sweep;
- V5a never harvests more than two copy-pairs from the same V4 cohort, leaving at least six copies open;
- first harvest allowance starts at max(300 POLF, 80% of the live prize cutoff);
- second harvest allowance starts at max(400 POLF, 95% of the live prize cutoff);
- candidate scores are reconstructed from the frozen fold using the next sweep's referee close, the actual V4 opening prices/qty and opening clawback fees;
- any pair with a visible opening void or a dedicated-room missed settlement sweep is excluded;
- visible outcome lookup and missed-sweep checks are indexed once per scan instead of rescanning the full flow for every pair;
- scans run at most once per referee sweep when no harvest is active.

Safe close mechanics:
- a V4 long target and its paired V4 short target close directly against each other, so no new directional counterparty is created;
- because the fold checks fee cash before releasing collateral, the close is staged;
- the first bootstrap tranche is sized so both accounts can afford a conservative 5% close-gap fee buffer and the released collateral should fund the remaining close;
- if one bootstrap is insufficient, additional small bootstrap tranches are submitted on later aligned sweeps;
- once both accounts have enough fee cash, the remainder is closed;
- at most six verified bootstrap/finish actions are allowed before blocking for review;
- visible close voids, missed settlement sweeps, simulated funds failures and unresolvable staged funding all block the active harvest rather than blindly continuing;
- an in-flight harvest is tracked as a state machine and is idempotent across autopilot restarts.

Pause behavior:
- `pause-dense-v5a` stops only new harvest selection;
- an already-started staged close is allowed to finish or block safely;
- V4 entry generation continues.

Commands:
```bash
uv run crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py dense-v5a-preview
uv run crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py enable-dense-v5a
uv run crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py pause-dense-v5a
```

Implementation commits:
- `4db64533338b06b5ae1b6e7f7397f18d643d5c99` — initial V5a staged harvest;
- `0c3cb6e10a59f388ba5b7af56d64a7a6554ccd65` — exact settlement reconstruction and scan indexing;
- `4805bc507b6e4a15389d9cd3978b33c46d94798f` — idempotent scan/block handling;
- `dc57f8e3ad56eff982253c0fcb382d4bb70b08ef` — dashboard V5a state;
- `268a4a983b745b3956a00417261e220df970c9d6` — adaptive staged close and safe pause.

Execution state:
`DENSE_V5A_IMPLEMENTED_PREVIEW_ENABLE_REQUIRED`.


## 2026-09-29 — V5a threshold retune after live preview

Live preview at sweep 939:
- ref 230.06;
- mark 230.16;
- previous first threshold 561.2640;
- previous second threshold 666.5010;
- eligible candidates: 0.

The earlier 80%/95% prize-line thresholds were too conservative for the purpose of creating realized-PnL carry. The competitor evidence only proved at least ~86.5 POLF of carried realized profit for the observed leading short cohort, while a typical full-size close costs roughly one 1% fee per side under a stable next sweep. Waiting until ~560 POLF before harvesting would miss the early carry mechanism we are trying to reproduce.

V5a thresholds are therefore retuned to:
- first harvest: max(180 POLF, 25% of live prize cutoff);
- second harvest: max(300 POLF, 45% of live prize cutoff);
- still at most two harvested copy-pairs from one V4 cohort;
- still leave at least six of eight copies open;
- all staged-close funding, missed-room, visible-void and lock gates remain unchanged.

At the sweep-939 prize cutoff implied by the preview (~701.58), the new thresholds would be approximately:
- first: 180 POLF;
- second: 315.71 POLF.

Commit: `a8331fb274179c47ef65e1ea81cf3f04f4b99dda`.


## 2026-09-29 — Dense V5a enabled live

User-side status after enabling V5a:
- V4 remains enabled;
- V5a enabled: true;
- new harvest selection enabled: true;
- harvested count: 0;
- no active harvest yet;
- V4 sweep 941 completed successfully with 8 long + 8 short, zero reserve shortage and zero errors;
- next Dense batch 427 was in the transient registration phase when status was sampled;
- V4 reserve pool showed 9 ready/registered at that instant, consistent with 7 sets having just been consumed and refill work still in progress;
- room registration confirmed and recent room activity age was 0 seconds.

The lack of an active V5a harvest in this snapshot is not itself a failure. The status was taken about 10 seconds after LaunchAgent restart. Dense autopilot first finishes the current V4 submission/next-batch registration work; V5a candidate selection runs on a subsequent poll in the same referee sweep when no V4 submission is due. With the default 60-second poll interval, the first V5a selection may therefore appear roughly one poll later. Candidate eligibility can also disappear if mark moves below the trigger before that poll.

Execution state:
`DENSE_V5A_LIVE_WAITING_FIRST_HARVEST_SCAN`.


## 2026-09-29 — Dense V5a first harvest completed

Live status at referee sweep 944 confirms the first V5a staged harvest completed successfully.

Result:
- pair: `v4-00213`;
- winner: long;
- trigger score: 180.8150 POLF;
- final locked winner score: 58.949759 POLF;
- harvested count: 1;
- active harvest state returned to null;
- V4 remained healthy and continued sweep 944 with 8 long + 8 short, zero reserve shortage and zero errors;
- next Dense batch 430 was already registered for sweep 945.

Interpretation:
- the staged close state machine worked end-to-end: bootstrap -> finish -> locked;
- realized-PnL carry is now live in our own fleet;
- this first lock retained only ~32.6% of the trigger score, implying a total haircut of ~121.87 POLF from close fees, staged execution and price movement between trigger and settlement;
- therefore the 180-POLF first threshold is mechanically valid but economically too early if the goal is to create a materially useful realized-PnL carry account.

Execution state:
`DENSE_V5A_FIRST_HARVEST_LOCKED_58.949759`.


## 2026-09-29 — Dense V5b realized-profit flip engine implemented

V5b now sits after V5a and reuses flat V5a winners as compounding seeds.

Core behavior:
- minimum realized seed score: 40 POLF;
- first direction is the opposite of the V5a winning side;
- a seed never reopens at full size blindly;
- planned opening notional is capped so the expected 1% opening fee consumes at most 45% of the realized seed score;
- two fresh registered feeder accounts split the counterparty exposure, so the winner account is not constrained by one feeder's collateral;
- opening and closing settlement are reconstructed against the next referee sweep's closing reference;
- winner and feeder funds are checked under the frozen fold before a state transition is accepted;
- visible voids or dedicated-room missed settlement sweeps block the cycle.

Risk controls:
- only one compound account can be active at a time;
- take-profit closes when projected flat score is at least seed score + 30 POLF;
- stop closes when projected flat score falls to -25 POLF;
- close uses the same two feeder accounts and reverses the opening legs, returning the winner flat;
- new cycles stop being created after sweep 2554.

True compounding loop:
- a successful V5b take-profit close becomes a new seed;
- the same winner key can then reopen in the opposite direction again;
- stop-closed cycles are not automatically recycled;
- this produces flat cash -> flipped exposure -> flat cash -> flipped exposure while retaining V4/V5a as the broad entry/harvest engines.

Initial seed currently available:
- V5a pair `v4-00213`;
- locked score 58.949759 POLF;
- prior winner long, so the first V5b direction will be short;
- because fee budget is tied to the realized cushion, expected position size is intentionally much smaller than a full 10k account.

Implementation commits:
- `a80aca6aaef3608fadad2c5ea283e066c9e6c6f0` initial V5b flip engine;
- `d3d54efc51feced9ee92654dc8f5e93b4131ee17` chained realized-profit seeds;
- `3a4972dba113eaa2edaf91cb945354f57edd1292`, `5168deb094cd325369f19d6525c4f5e6cd4b000b`, `de687681631304d874c76511dd265d8f972a2943`, `0aa5c0ee930a99e12acce30f7f91f2dbe4df1bd1` seed-lineage/status plumbing;
- `1fed1b3012abe471fc1471ff8c6801e62e2d6be8` counterparty funds verification;
- `96ace16f99fc4777f22993410826d1db60270832` dashboard support.

Execution state:
`DENSE_V5B_IMPLEMENTED_PREVIEW_REQUIRED`.


## 2026-09-29 — Dense V5b live preview validated

Preview at sweep 947:
- ref 229.98;
- V5b disabled, no active/pending cycle;
- one eligible seed: `v5a:v4-00213`;
- parent V5a pair: `v4-00213`;
- realized locked score: 58.949759 POLF;
- cash: 10058.949759;
- previous winning side: long;
- planned V5b flip side: short;
- planned qty: 11.53 NVDA;
- estimated opening base fee: 26.52 POLF;
- take score: 88.949759;
- stop score: -25.

The preview matches the intended seed lineage and sizing model. Before live enable, V5b settlement reconstruction was aligned with V5a by preferring the referee PnL mark for the next-sweep close and falling back to the next price ref only when needed.

Commit: `fe89f136e78d245d6993d76474cd70953ab7d526`.

Execution state:
`DENSE_V5B_PREVIEW_VALIDATED_READY_TO_ENABLE`.


## 2026-09-29 — LaunchAgent reinstall recovered; V5b waiting first post-restart poll

Observed after reinstall:
- autopilot LaunchAgent: running;
- dashboard LaunchAgent: running;
- V4 remains enabled;
- V5a remains enabled and its second harvest `v4-00227` advanced to `finish_submitted`;
- V5b remains enabled/accepting new cycles, with no pending or active cycle yet;
- referee sweep observed: 950.

Interpretation:
- installer recovery succeeded and local strategy state survived;
- V5b still needs a post-V4, post-restart autopilot poll to register the existing `v4-00213` realized-profit seed;
- because poll interval is 30 seconds, a null V5b state immediately after reinstall is not yet evidence of a logic failure.

Execution state:
`LAUNCHAGENTS_HEALTHY_V5B_WAITING_FIRST_REGISTRATION_POLL`.


## 2026-09-29 — V5b scheduler starvation confirmed and hardened

At sweep 951 the manual V5b preview still showed one eligible seed:
- `v5a:v4-00213`;
- locked score 58.949759;
- planned short qty 11.53;
- estimated opening fee 26.51;
- take score 88.949759;
- stop score -25.

Yet live state still showed no V5b pending or active cycle. This confirms the seed-selection logic is healthy and the remaining fault is scheduler reachability.

Hardening:
- V5b now runs before V4 pending submission/wait handling on every autopilot poll;
- this prevents V4 alignment/room-wait transitions from consuming every poll before V5b can register a seed;
- active V5b risk management therefore also runs before V4 wait paths;
- a persistent `v5b_last_check` heartbeat records the last sweep on which the scheduler actually entered V5b.

Commit: `2ce6f92baa9f39ed99df79db9eb5c873b4b90c3e`.

Execution state:
`DENSE_V5B_SCHEDULER_HEARTBEAT_ADDED`.


## 2026-09-29 — V5b reached scheduler but still failed before pending creation

Observed at referee sweep 954:
- V5b scheduler heartbeat present at sweep 952/954;
- V5b enabled and accepting new cycles;
- no active or pending V5b cycle;
- no persisted V5b registration error;
- V5a seed `v4-00213` remains the last successfully locked winner at 58.949759 POLF.

This narrows the fault to the interval after entering V5b but before a pending cycle was persisted. The registration state machine is hardened again:
- persist the V5b plan before feeder key generation or owner POSTs;
- persist `creating_keys` / `registering` stages;
- catch and expose seed-scan, feeder-key, and owner-registration errors;
- when seed scan returns empty, persist diagnostics including harvested count and whether `v4-00213` is still present in the V4 pair index.

Commit: `e1ecf37607f2804a3a82c19cd237574badb0c010`.

Execution state:
`DENSE_V5B_PRE_PENDING_DIAGNOSTICS_HARDENED`.


## 2026-09-29 — V5b root cause found: Decimal seed serialization

At referee sweep 955:
- V5b scheduler heartbeat was present;
- V5b was enabled and accepting new cycles;
- no pending/active cycle existed;
- no seed-empty or persisted V5b error diagnostic was present.

Root cause:
- `_v5b_seed_candidates()` intentionally returns `locked_score` and `cash` as `Decimal` values for sizing math;
- `_v5b_register_pending()` copied that seed directly into the persistent JSON state and called `save_state()`;
- `json.dumps` cannot serialize `Decimal`, so the autopilot iteration failed after entering V5b but before the pending object could be written;
- preview did not expose this because it performs the math without persisting the candidate.

Fix:
- convert V5b seed `locked_score` and `cash` to strings before persisting pending state;
- downstream V5b logic already reconstructs those values via `Decimal(str(...))`, so no calculation semantics change.

Commit: `62353a588336ace7cd800bfad044e39cc822b4d9`.

Execution state:
`DENSE_V5B_DECIMAL_SERIALIZATION_FIXED`.


## 2026-09-29 — V5a second lock completed; V5b cycle 1 open verified

Live status at referee sweep 957:
- V5a harvested count: 2;
- second harvested pair: `v4-00227`;
- second winner: long;
- second final locked score: 50.484365 POLF;
- no active V5a harvest remains.

V5b cycle 1:
- source: `v4-00213`;
- direction: short;
- entry px: 228.36;
- qty: 11.61;
- status: `open_verified`;
- current mark-to-market score: 47.762363;
- projected flat score at the current close reference: 4.400174;
- take score: 88.949759;
- stop score: -25.

Interpretation:
- V5b opening settlement reconstruction succeeded end-to-end;
- current score and projected-flat score must not be conflated: the former includes the live short position, while the latter includes the cost of closing it now;
- the second V5a lock again converted an approximately 180-POLF trigger into only about 50 POLF of realized carry, reinforcing that the 180 first-harvest threshold is economically thin after close fees and settlement movement.

Execution state:
`DENSE_V5A_TWO_LOCKS_V5B_CYCLE1_OPEN_VERIFIED`.


## 2026-09-29 — Dashboard dynamic relative catch-up line

Added a live relative catch-up estimate to the Close Call dashboard.

The new metric compares:
- our current best directional candidate's score sensitivity to NVDA mark;
- the current public leader cohort's position sensitivity.

Leader position source priority:
1. official `d-close1-positions.top` position when a current leader DID is visible there;
2. otherwise the most recent consecutive-sweep `Score / Mark` slope for current leader DIDs.

The dashboard now reports:
- our position slope;
- leader position slope;
- relative score slope in POLF per $1 NVDA move;
- the NVDA move and percentage that would close the current leader-score gap if both positions stay unchanged.

This is intentionally shown alongside, not instead of, the existing static prize-line target. The relative target is conditional and automatically recalculates if the public leader position changes.

Commit: `8ca5e2608b04b127be56a85cecd12cf2a0c3ebc8`.
