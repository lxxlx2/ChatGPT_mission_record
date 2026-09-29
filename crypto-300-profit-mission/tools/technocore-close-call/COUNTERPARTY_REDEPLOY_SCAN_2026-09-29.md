# FLOP Close Call Automatic Counterparty Trio Scan

Branch: \`review/flop-counterparty-scan-20260929\`

Base: exact three-account counterparty replay.

This is read-only research tooling. It posts no trades and is not wired to
autopilot.

## Motivation

The first exact trio replay for:

\`\`\`text
DENSE-V3-01619-L
DENSE-V3-01620-S
DENSE-V3-01621-S
\`\`\`

proved that both same-sweep legs settle across all 576 historical close samples,
but the full portfolio podium coverage did not increase.

The replay still reduced total positive podium gap, so the next step is to find
whether another visible-settled trio does materially better after accounting for
both donor accounts.

## Search space

Default mode only uses accounts reconstructed with:

\`\`\`text
evidence_mode = visible_settled
\`\`\`

Accounts are grouped by identical side, qty, entry, opening fee, remaining cash,
source and evidence mode. This avoids repeatedly evaluating mechanically
identical copies.

### Target shortlist

Long signatures are ranked by the realized flat score and redeployable short
quantity they unlock at the median historical close.

Default:

\`\`\`text
top 60 target signature groups
\`\`\`

### Donor shortlist

For every target, short signatures are ranked by:

1. how often that signature currently participates in the local best frontier;
2. quantity compatibility with the target;
3. higher original short entry;
4. available fee cash.

This biases the search toward redundant/dominated shorts that are cheaper to
sacrifice as counterparties.

Default:

\`\`\`text
top 24 donor-A groups
top 24 donor-B groups
\`\`\`

Donor A must be able to absorb the target's full long close without opening a
new long. Donor B may retain residual short but the exact replay never forces it
through flat into a new long.

## Two-stage evaluation

### Quick stage

Every candidate trio is exact-replayed at historical close P10/P50/P90.

The whole reconstructed portfolio frontier is recomputed after all three account
states change.

Ranking:

1. more podium-covered cells;
2. smaller total positive podium gap;
3. smaller worst positive podium gap.

### Full stage

The best quick candidates are replayed again on all retained historical close
samples, normally 576.

Default:

\`\`\`text
20 finalists
\`\`\`

Full output includes:

- exact selected account names;
- full baseline/scenario stats;
- coverage delta;
- total-gap delta;
- mean-gap delta;
- max-gap delta;
- leg-1/leg-2 settlement rate;
- target redeployed short qty distribution;
- target realized flat-score distribution;
- best/worst historical close sample;
- per-Final-S grid for the best trio.

## Commands

Tests:

\`\`\`bash
uv run --with "cryptography>=42" python -m unittest -v \
  test_counterparty_redeploy.py \
  test_counterparty_redeploy_scan.py
\`\`\`

Full scan:

\`\`\`bash
uv run --with "cryptography>=42" close_call_fleet.py \
  counterparty-redeploy-scan \
  > ~/Desktop/flop-counterparty-scan.json
\`\`\`

Compact summary:

\`\`\`bash
uv run --with "cryptography>=42" close_call_fleet.py \
  counterparty-redeploy-scan-summary \
  > ~/Desktop/flop-counterparty-scan-summary.txt
\`\`\`

Search breadth can be changed with:

\`\`\`text
--top-targets N
--top-donors N
--finalists N
\`\`\`

\`--allow-local\` expands the research pool to locally reconstructed evidence.
It is not intended as production evidence.

## Interpretation gate

A trio is not a production candidate merely because total gap improves.

The strongest signal would be:

\`\`\`text
coverage_delta > 0
\`\`\`

If coverage remains unchanged, a trio would still need a substantially larger
gap reduction than the first 01619/01620/01621 replay and no meaningful damage
to an existing frontier before further production work is justified.

The competitor podium model remains a static-current-position stress model, not
a forecast of rival actions.

No execution or deployment code is included.


## Full-portfolio baseline and progress output

Only the **search pool** is restricted to `visible_settled` accounts by
default. Baseline and scenario frontiers still include every conservatively
reconstructed unmodified V4 account, including locally reconstructed accounts.
This keeps the scan comparable with the earlier portfolio-level labs.

The scanner prints progress to stderr while JSON/stdout remains clean. When the
JSON command is redirected to a file, the terminal will still show:

```text
counterparty-scan quick: ...
counterparty-scan full: ...
```

so a long search should no longer look frozen.


## Ex-ante sizing correction

The first real scanner output exposed an important research flaw: the second-leg
short quantity was being recomputed separately for each historical settlement
close. That uses information unavailable when a real trade is submitted.

The scanner now removes that lookahead.

For each candidate trio it first derives one fixed second-leg quantity:

```text
fixed_leg2_qty
  = minimum feasible leg-2 cap across the declared close stress set
```

Quick ranking uses one fixed quantity across its P10/P50/P90 close samples.

Every full finalist is then re-sized again using one fixed quantity across all
retained historical close samples, normally 576, and that same quantity is used
for every replayed close.

The exact trio replay command also uses a fixed quantity across all retained
close samples.

This correction can materially reduce the apparent coverage improvement from
the earlier adaptive-quantity output, so earlier coverage numbers must not be
treated as production-valid until rerun with this version.
