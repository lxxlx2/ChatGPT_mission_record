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
