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
