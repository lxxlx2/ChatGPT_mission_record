# FLOP Close Call V4.1 Strategy Review

Branch: \`review/flop-v41-strategy-20260929\`

Base: the latest V4 correctness review branch.

This is a **read-only strategy lab**. It does not alter the running autopilot and does not enable a new strategy mode.

## Goal

Use the referee's own historical within-sweep price moves to replace the current near-duplicate V4 sizing with an eight-copy empirical \`qty / quote / stress\` grid.

The lab answers:

1. How often current V4 loses every long or short candidate to \`funds\` under observed five-minute moves.
2. Whether the same eight target slots can keep one aggressive near-max-size ticket while progressively adding tail survival.
3. Where our currently open V4 positions have strong or weak hypothetical final-S coverage.

## Historical move

For each \`d-close1-price\` sweep:

\`\`\`text
move = price.ref / price.applied - 1
\`\`\`

\`applied\` is the reference used to check that sweep's trades.
\`ref\` is the close used for clawback and the next sweep's reference.

Default lookback: 576 sweeps.

## Eight-copy proposal

\`\`\`text
copy 1: 40.0% .. 60.0%   narrow core band, aggressive
copy 2: 25.0% .. 75.0%
copy 3: 15.0% .. 85.0%
copy 4:  9.0% .. 91.0%
copy 5:  5.0% .. 95.0%
copy 6:  2.5% .. 97.5%
copy 7:  0.5% .. 99.5%
copy 8:  0.0% .. 100.0%  full observed range
\`\`\`

Copy 1 intentionally keeps an aggressive ticket while covering a narrow empirical core instead of a single median point. Later copies trade some quantity for wider empirical survival coverage.

## Long

The long quote remains at the exact referee lower limit.

\`long_qty\` is independently maximized in 0.01-contract increments against official-style fresh-account cash checks at:

\`\`\`text
lower stress close
current reference
upper stress close
\`\`\`

This removes the current coupling where the short leg's funds requirement can shrink every long copy.

## Short

The short quote is placed near the clawback boundary for that copy's upper stress close:

\`\`\`text
short_px ~= max(current_ref, upper_stress_close) / 0.99
\`\`\`

and is capped at the referee +5% limit.

\`short_qty\` is then independently maximized while:

- both V4 legs pass the declared stress closes;
- feeder funds checks pass;
- \`short_qty <= long_qty\`, so leg 2 does not make the feeder open extra net long.

## Commands

Run from:

\`\`\`bash
cd ~/ChatGPT_mission_record/crypto-300-profit-mission/tools/technocore-close-call
\`\`\`

Preview the proposed eight-copy grid:

\`\`\`bash
uv run close_call_fleet.py dense-v41-preview
\`\`\`

Compare current V4 against V4.1 on retained historical moves:

\`\`\`bash
uv run close_call_fleet.py dense-v41-backtest
\`\`\`

Use all retained price history instead of the default 576 sweeps:

\`\`\`bash
uv run close_call_fleet.py dense-v41-backtest --lookback 0
\`\`\`

Inspect our current hypothetical final-S coverage:

\`\`\`bash
uv run close_call_fleet.py dense-final-s-grid --start 200 --end 260 --step 0.50
\`\`\`

## Backtest metrics

For both \`current_v4\` and \`proposed_v41\`:

- historical moves with no surviving long candidate;
- historical moves with no surviving short candidate;
- distribution of best surviving long quantity;
- distribution of best surviving short quantity;
- best long score in a standardized \`final = current ref +5%\` scenario;
- best short score in a standardized \`final = current ref -5%\` scenario.

The standardized final scenarios compare ticket quality. They are not price predictions.

## Final-S grid

The grid reconstructs currently saved, unmodified V4 target tickets.

It excludes V5a-modified pairs and uses:

- explicit referee \`settled/void\` when visible;
- private-room exact trade submission plus compact-flow omission as local reconstruction evidence;
- official \`price.ref\` as settlement close;
- referee \`missed\` as a rejection gate.

Historical application-sweep ambiguity still exists for omitted outcomes, so this grid is a strategy diagnostic rather than an authoritative final ledger.

## Deliberately unchanged

This strategy branch does not:

- wire V4.1 into \`dense_submit_pending\`;
- enable live V4.1 orders;
- change current V4 live quantities or offsets;
- re-enable new V5a/V5b work;
- change LaunchAgents, keys, room state or secrets.

The intended gate is:

\`\`\`text
external review
-> local preview/backtest/final-S output
-> compare current V4 vs V4.1
-> only if clearly better, prepare a small production integration patch
\`\`\`


## External review note: feeder leg-2 cash semantics

One review suggested crediting feeder close proceeds before the leg-2 funds check.
That would diverge from the official fold.

The official implementation calls `check()` before `apply()`. For a feeder
buy that closes its existing short, `Account.opening(+1, qty)` is zero for the
closing portion, so the pre-settlement funds check requires only the taker fee
for that portion. The collateral/PnL release occurs later in `Account.apply()`.

Therefore V4.1 intentionally does **not** add close proceeds to feeder cash before
the leg-2 funds check. A comment and regression test now document this ordering.

## External review round 1 adjustments

- copy 1 changed from `50/50` to `40/60`;
- backtest now reports standardized ±5% and ±10% final-S scenarios;
- final-S rows now expose per-leg evidence mode:
  `visible_settled` or `local_reconstruction`;
- the strategy remains read-only and is still not connected to autopilot.
