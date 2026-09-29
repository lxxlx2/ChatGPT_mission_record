# FLOP Close Call Three-Account Counterparty Redeploy Replay

Branch: \`review/flop-counterparty-redeploy-20260929\`

Base: read-only realize -> redeploy lab.

This is read-only research tooling. It posts no trade and is not wired to
autopilot.

## Purpose

The single-account lab showed that many long -> short redeploys reduce total
podium gap, but it did not include the accounts that must countersign those
trades.

The first high-confidence candidate family is:

\`\`\`text
target  DENSE-V3-01619-L
donor A DENSE-V3-01620-S
donor B DENSE-V3-01621-S
\`\`\`

All three were reconstructed with \`visible_settled\` evidence in the first
real lab output.

The replay evaluates the full three-account state after each trade and then
recomputes the entire reconstructed portfolio frontier.

## Ordered same-sweep mechanism

At each historical close sample the tool performs:

\`\`\`text
leg 1
target long maker sells its full long at the current upper legal quote
donor A buys

official check on both pre-apply cash balances
official maker/taker fees
apply both accounts

leg 2
target is now flat and has released cash
target maker sells the largest feasible new short at the same upper quote
donor B buys only enough to reduce its existing short

official check again on the post-leg-1 target cash and donor-B cash
official maker/taker fees
apply both accounts
\`\`\`

The second-leg quantity is capped by:

- target flat cash;
- donor B's remaining short quantity;
- donor B's available cash for the buyer fee.

The model intentionally does not make donor B cross through flat and open a new
long.

## Official account semantics

The helper mirrors the official fold:

- funds are checked before each trade is applied;
- closing a long releases the sale price;
- closing a short releases \`2 * lot_entry - buy_px\`;
- new contracts tie up their trade price;
- base/clawback maker and taker fees are both charged;
- the second trade can use cash released by the first trade because trades are
  checked/applied sequentially.

## Portfolio evaluation

The three selected accounts are removed from the untouched baseline frontier.

For every historical settlement-close sample:

1. replay both trades;
2. calculate the post-trade score line of target, donor A and donor B;
3. combine those lines with every untouched reconstructed account;
4. compare the resulting best-key frontier against the same static podium
   stress line used by V4.2.

The output reports:

- baseline and scenario podium-covered cells;
- coverage-rate delta;
- total positive podium-gap delta;
- mean positive-gap delta;
- worst-gap delta;
- leg-1 and leg-2 settlement rates;
- per-Final-S min/P10/P50/P90/max frontier;
- best and worst historical close samples;
- final positions and cash of all three accounts for those samples.

## Default command

\`\`\`bash
uv run --with "cryptography>=42" close_call_fleet.py \
  counterparty-redeploy-replay \
  > ~/Desktop/flop-counterparty-redeploy.json
\`\`\`

Compact output:

\`\`\`bash
uv run --with "cryptography>=42" close_call_fleet.py \
  counterparty-redeploy-summary \
  > ~/Desktop/flop-counterparty-redeploy-summary.txt
\`\`\`

The defaults are the 01619-L / 01620-S / 01621-S trio.

Custom accounts can be supplied with:

\`\`\`bash
--target ACCOUNT --donor-a ACCOUNT --donor-b ACCOUNT
\`\`\`

By default all three must have \`visible_settled\` evidence. \`--allow-local\`
exists only for research comparisons and should not be used as production
evidence.

## Interpretation gate

A smaller total gap alone is not sufficient for production.

The trio becomes interesting only if the full portfolio replay shows one of:

- positive podium-coverage delta;
- a large gap improvement without damaging a critical existing frontier;
- a clearly stronger risk-adjusted frontier under the full 576-sample close
  distribution.

The competitor model remains a static-current-position stress model. It is not
a forecast of rival trading.

No production integration is included.
