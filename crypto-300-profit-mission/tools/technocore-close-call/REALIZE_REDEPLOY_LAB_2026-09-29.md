# FLOP Close Call Realize -> Redeploy Lab

Branch: \`review/flop-realize-redeploy-lab-20260929\`

Base: fee-aware leader pivot solver.

This is read-only research tooling. It does not post trades and is not wired to
autopilot.

## Why

The leader replay now supports a simple mechanism:

1. accumulate a large directional score/carry;
2. close the current position;
3. use the released flat cash;
4. open the opposite side later in the same sweep;
5. then hold the new directional position.

The V3 replay for the historical leader fits a sweep-957 short-close then
long-open path within about 0.23 POLF while the one-trade flip is ruled out by
the pre-apply funds check.

The next question is whether any of our current unmodified V4 target accounts
would improve our prize-line coverage by using the same close-first/redeploy
sequence.

## Inputs

The lab uses:

- conservative reconstructed unmodified V4 target accounts;
- each account's original entry, quantity and official opening fee;
- exact remaining cash for those unmodified accounts;
- current referee price and legal trade limits;
- historical within-sweep close-move samples;
- the same static current-podium stress model used by V4.2.

Accounts touched by V5a are excluded by the existing reconstruction path.

## Simulation

For every reconstructed V4 account and every historical settlement-close move:

### Existing long

1. sell the full long at the current upper legal quote;
2. pay official seller base/clawback fee;
3. if the first funds check passes, become flat;
4. use \`10000 + flat_score\` as cash;
5. open the largest two-decimal short that passes the official collateral + fee
   check at the upper legal quote.

### Existing short

1. buy back the full short at the current lower legal quote;
2. pay official buyer base/clawback fee;
3. if the first funds check passes, become flat;
4. use released flat cash;
5. open the largest two-decimal long that passes the official funds check at the
   lower legal quote.

The first and second trades are ordered within one sweep, matching the official
fold semantics used by the leader pivot solver.

If the first close fails, the account remains in its original position. If the
close succeeds but the second open cannot, the account remains flat.

## Objective

For each candidate account the lab compares:

- leave all current reconstructed accounts untouched;
- replace only that account with the realize -> opposite-side redeploy path.

Across historical close moves and the default Final-S grid \`220..245\`, it
reports:

- podium-covered cells;
- total positive gap to static podium;
- worst positive gap;
- delta vs untouched baseline;
- close-feasibility rate;
- new opposite-side qty min / median / max;
- flat realized score min / median / max.

This does not predict future NVDA direction. It measures whether the leader's
capital-redeployment mechanism improves our existing score frontier.

## Commands

\`\`\`bash
uv run --with "cryptography>=42" python -m unittest -v \
  test_realize_redeploy_lab.py
\`\`\`

Full JSON:

\`\`\`bash
uv run --with "cryptography>=42" close_call_fleet.py \
  realize-redeploy-lab \
  --start 220 --end 245 --step 0.50 \
  > ~/Desktop/flop-realize-redeploy.json
\`\`\`

Compact summary:

\`\`\`bash
uv run --with "cryptography>=42" close_call_fleet.py \
  realize-redeploy-summary \
  --start 220 --end 245 --step 0.50 \
  > ~/Desktop/flop-realize-redeploy-summary.txt
\`\`\`

For all retained historical close samples:

\`\`\`bash
uv run --with "cryptography>=42" close_call_fleet.py \
  realize-redeploy-lab \
  --lookback 0 \
  --start 210 --end 255 --step 0.50 \
  > ~/Desktop/flop-realize-redeploy-all.json
\`\`\`

## Evidence limits

The current-account reconstruction is still subject to the known compact-flow
application-sweep ambiguity for locally reconstructed historical trades.

The podium model freezes current competitor score/position lines. It is a stress
scenario, not a forecast of what rivals will do.

No production execution code is included.
