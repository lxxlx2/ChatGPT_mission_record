# FLOP Close Call Leader Pivot Solver

Branch: \`review/flop-pivot-solver-20260929\`

Base: read-only leader-path replay.

This is **read-only research tooling**. It does not post trades, alter account
state or change autopilot.

## Why this exists

The first leader replay narrowed the interesting regime to the interval around
sweeps 956–960:

- the leading key is visible around sweep 956 with a large inferred short;
- by sweep 960 the referee publishes a \`+46.07\` long;
- from sweep 960 onward the leading score is almost perfectly explained by
  simply holding that \`+46.07\` long.

The missing question is how much locked score/cash had to exist before that
long was opened, and whether a direct short-to-long flip can explain the
observed sweep-960 state under the official fee/clawback rules.

## Fee-adjusted carry lower bound

The earlier leader replay compared the synthetic entry only with the raw legal
quote envelope. This branch adds the mandatory fee.

For a fresh long opened at price \`p\` in a sweep closing at \`c\`:

\`\`\`text
buyer_fee / qty = max(0.01 * p, c - p)
score contribution at later mark m
  = qty * (m - p) - buyer_fee
  = qty * (m - max(1.01 * p, c))
\`\`\`

Therefore the best fee-adjusted long effective cost in a sweep is:

\`\`\`text
max(1.01 * lower_legal_quote, close)
\`\`\`

For a fresh short the symmetric best effective sale is:

\`\`\`text
min(0.99 * upper_legal_quote, close)
\`\`\`

The cumulative best values are used to calculate a stronger conservative lower
bound on prior realized carry.

## Transition evidence fix

\`consecutive_pnl_slope\` remains useful as a directional diagnostic, but this
branch no longer counts changes between inferred slopes as real position
transitions.

\`transition_count\` now requires both adjacent positions to come from
\`published_position\`.

Inferred slope changes are kept separately under
\`inferred_position_diagnostics\`.

## Pivot solver

Default target:

\`\`\`text
rank = 1
pre snapshot <= sweep 956
target snapshot = sweep 960
\`\`\`

The target sweep must have a referee-published position.

The solver enumerates each official price sweep inside the window and evaluates
three models.

### A. Long-only carry requirement

Assume all prior strategy activity has already been realized before opening the
target long.

For each possible long-opening sweep it uses the lowest legal two-decimal quote
and the official buyer fee/clawback rule, then solves:

\`\`\`text
required_locked_carry
  = observed_target_score
    - target_qty * (target_mark - buy_px)
    + buyer_fee
\`\`\`

This directly answers the minimum locked score needed before opening the final
long.

### B. One-trade direct flip

Assume the pre-snapshot short estimate is correct and a single buy trade flips:

\`\`\`text
-short_qty  ->  +target_long_qty
\`\`\`

The buy quantity is:

\`\`\`text
short_qty + target_long_qty
\`\`\`

The solver propagates the pre score to the settlement close, applies the
official buyer execution edge minus clawback/base fee, then marks the resulting
long to the target snapshot.

It reports:

\`\`\`text
observed_target_score - modeled_target_score
\`\`\`

A positive residual means the one-trade model needs additional prior carry or
the inferred pre-position is inaccurate.

It also reports the official pre-apply funds requirement:

\`\`\`text
target_long_qty * buy_px + buyer_fee_on_full_flip_qty
\`\`\`

because \`Fold.check()\` runs before closing proceeds are released.

### C. Close then open

Enumerate:

\`\`\`text
close short at sweep i
open target long at sweep j
j > i
\`\`\`

Both legs use the lowest legal quote and official buyer fees. This model lets
the short close release cash before the later long-opening funds check.

## Commands

From the Close Call tool directory:

\`\`\`bash
uv run --with "cryptography>=42" python -m py_compile close_call_fleet.py

uv run --with "cryptography>=42" python -m unittest -v \
  test_correctness_patch.py \
  test_v41_strategy_lab.py \
  test_v42_frontier_optimizer.py \
  test_leader_path_replay.py \
  test_leader_pivot_solver.py
\`\`\`

Full solver output:

\`\`\`bash
uv run --with "cryptography>=42" close_call_fleet.py \
  leader-pivot-solve \
  --rank 1 \
  --from-sweep 956 \
  --target-sweep 960 \
  > ~/Desktop/flop-leader-pivot.json
\`\`\`

Compact summary:

\`\`\`bash
uv run --with "cryptography>=42" close_call_fleet.py \
  leader-pivot-summary \
  --rank 1 \
  --from-sweep 956 \
  --target-sweep 960 \
  > ~/Desktop/flop-leader-pivot-summary.txt
\`\`\`

## Evidence limits

The sweep-956 short position is currently based on
\`consecutive_pnl_slope\`, so direct-flip and close-then-open results are
diagnostics rather than authoritative replay.

The sweep-960 target position is required to be \`published_position\`.

The long-only carry lower bound is stronger because it does not require the
sweep-956 inferred short to be correct.

No live strategy change is included in this branch.
