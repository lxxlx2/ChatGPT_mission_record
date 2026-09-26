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

Next gate:
- wait for at least one fresh referee sweep after registration;
- run local `status`;
- do not open T01 or bracket round 1 until referee freshness and registration/mint state are acceptable.

Execution state:
`BOOTSTRAPPED_WAITING_FOR_FRESH_SWEEP`

## Execution status

BOOTSTRAPPED_WAITING_FOR_FRESH_SWEEP.

The user has authorized starting this stored plan. Live secret generation and signing must occur locally on the user's Mac; do not move private seeds into GitHub or chat.
