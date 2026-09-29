# FLOP Close Call V4.2 Frontier Optimizer

Branch: \`review/flop-v42-frontier-20260929\`

Base: V4.1 read-only strategy lab.

This is **read-only research tooling**. It does not submit trades and is not wired
to autopilot.

## Why V4.2 exists

The current reconstructed Final-S grid has a deep score valley around the live
reference region while both tails already have much stronger score lines.

V4.1 improved average long size by roughly 2.5%, but that alone cannot repair a
central frontier that is hundreds of points below the current public prize line.

V4.2 therefore changes the research objective from:

\`\`\`text
maximize average surviving qty
\`\`\`

to:

\`\`\`text
maximize our best-key Final-S frontier
and minimize the positive gap to a static current-podium scenario
\`\`\`

The default optimization interval is \`S=220..245\`.

## Competitor model

V4.2 reads the current public PnL top and public positions.

For each competitor it builds:

\`\`\`text
score(S) = score_at_current_mark + position * (S - current_mark)
\`\`\`

Evidence priority:

1. \`published_position\`
2. \`consecutive_pnl_slope\`
3. \`flat_score_fallback\`

The third-highest modeled score at each S is the static podium line.

This is a stress scenario, **not a forecast**. Competitors can trade again and
their positions can change.

## Candidate search

The research pool includes:

- empirical stress bands inherited from V4.1;
- long quote offsets of 1%, 2%, 3%, 4%, 5%;
- short quote offsets of 1%, 2%, 3%, 4%, 5%;
- long size at 100% and 97% of the independently stress-sized maximum;
- the current V4 templates as explicit fallback candidates.

Each pair is evaluated with the same official-style two-leg cash/clawback
simulator used by V4.1.

The short side remains constrained to \`short_qty <= long_qty\` in this review
version so the feeder does not intentionally open an extra net-long remainder.

## Historical settlement uncertainty

Greedy search uses a quantile-thinned set of historical within-sweep
\`ref/applied - 1\` moves for speed.

After selecting up to eight pairs, V4.2 re-evaluates the selected set on **all**
retained historical move samples.

For every Final-S point it reports:

- static podium score;
- our existing reconstructed best score;
- optimized minimum score across historical settlement moves;
- optimized P10;
- optimized median;
- optimized maximum;
- fraction of historical settlement moves where our optimized frontier meets or
  exceeds the static podium line.

## Greedy objective

Each new candidate can only raise the existing frontier.

Greedy selection ranks candidate additions by:

1. number of \`(historical move, Final-S)\` cells that meet/exceed the podium;
2. lower total positive podium gap;
3. lower worst positive podium gap.

This directly targets the contest goal of producing at least one high-scoring
key across the central Final-S region.

## Commands

From the Close Call tool directory:

\`\`\`bash
uv run --with "cryptography>=42" close_call_fleet.py dense-v42-optimize \
  > ~/Desktop/flop-v42-optimize.json
\`\`\`

CSV summary:

\`\`\`bash
uv run --with "cryptography>=42" close_call_fleet.py dense-v42-grid \
  > ~/Desktop/flop-v42-grid.csv
\`\`\`

Wider custom range:

\`\`\`bash
uv run --with "cryptography>=42" close_call_fleet.py dense-v42-optimize \
  --start 210 --end 255 --step 0.50 --lookback 0 \
  > ~/Desktop/flop-v42-optimize-all.json
\`\`\`

## Deployment gate

V4.2 is not an execution mode.

Before any production integration:

1. run tests;
2. inspect selected plans;
3. compare current V4, V4.1 and V4.2 on real outputs;
4. externally review the optimizer math;
5. only then prepare a small live execution patch.

No LaunchAgent, room, owner, key, V5, or live V4 behavior is changed by this PR.
