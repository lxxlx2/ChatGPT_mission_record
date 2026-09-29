# FLOP Close Call Leader Path Replay

Branch: \`review/flop-leader-path-20260929\`

Base: V4.2 read-only frontier optimizer.

This is **read-only research tooling**. It posts nothing, changes no state and is
not wired to autopilot.

## Purpose

V4.2 showed that fresh static V4-style accounts cannot close the central
Final-S gap to the current podium. The next question is how the current leading
accounts accumulated roughly 900+ points of score while still carrying large
open positions.

The leader-path replay therefore reconstructs the current non-local leaders
from public referee snapshots and every currently readable registered trading
room.

## Authoritative inputs

The tool reads:

- \`d-close1-pnl\` history;
- \`d-close1-positions\` history;
- \`d-close1-price\` history;
- \`d-close1-flow\` outcomes and room registrations;
- \`close1\`;
- every room ever named under referee \`flow.rooms\`, when still readable.

No private local key material is exported.

## Per-leader path

For each current leader it records:

- all PnL snapshots where that DID appears;
- published positions where available;
- a clearly labelled \`consecutive_pnl_slope\` fallback when a published
  position is unavailable;
- score intercept \`score - position * mark\`;
- synthetic effective entry \`mark - score / position\`;
- historical legal quote envelope up to each sweep;
- a conservative lower bound on realized carry when the synthetic entry lies
  outside every historically legal quote;
- exact flat-account score whenever a published position is zero;
- consecutive-sweep position transitions;
- the score expected from simply holding the previous position;
- residual \`trade_impact_at_current_mark\` when the observed score differs from
  that hold path;
- signed trades involving the leader found in scanned rooms;
- visible referee outcome when compact flow still contains it.

## Important interpretation

\`min_realized_carry_required\` is a mathematical lower bound, not a complete
cash-ledger replay.

For a long position:

\`\`\`text
synthetic_entry = mark - score / position
\`\`\`

If that synthetic entry is below the lowest legal buy quote ever available up
to that sweep, the difference cannot be explained by one still-open position.
Some positive realized carry is required.

For a short position, the symmetric proof applies when the synthetic entry is
above the highest legal historical sell quote.

This test is deliberately conservative. Fees make the true realized-carry
requirement at least as hard, not easier.

A snapshot with published position zero is stronger evidence:

\`\`\`text
score == realized net PnL after fees
\`\`\`

because no open future remains.

## Trade discovery limitations

The referee archive redacts trades from private rooms. This tool instead tries
to read every registered room directly from technocore.chat.

Rooms that are deleted or otherwise unavailable cannot be reconstructed from
public data. Compact flow may also omit settled/void IDs because of the 4096
character post limit. Missing outcomes are reported as \`not_visible\` and are
not silently promoted to settled.

A trade timestamp provides only a \`first_possible_sweep\` estimate. When the
compact flow still contains that trade ID, \`outcome_sweep\` is authoritative.

## Commands

From the Close Call tool directory:

\`\`\`bash
uv run --with "cryptography>=42" close_call_fleet.py leader-path-replay \
  --top 8 --rooms registered \
  > ~/Desktop/flop-leader-path.json
\`\`\`

Compact summary:

\`\`\`bash
uv run --with "cryptography>=42" close_call_fleet.py leader-path-summary \
  --top 8 --rooms registered \
  > ~/Desktop/flop-leader-summary.txt
\`\`\`

For a quick public-room-only diagnostic:

\`\`\`bash
uv run --with "cryptography>=42" close_call_fleet.py leader-path-replay \
  --top 8 --rooms public \
  > ~/Desktop/flop-leader-path-public.json
\`\`\`

\`--room-limit N\` can cap the registered-room scan for debugging; zero means
scan all discovered rooms.

## What we want to learn

The useful outcomes are:

1. whether the leading keys ever became flat with hundreds of realized points;
2. when their position changed materially;
3. whether the score path shows repeated realize-and-redeploy cycles;
4. the minimum realized carry mathematically required by their current
   score/position;
5. which signed trades can be matched to those transition sweeps;
6. whether the same pattern can be reproduced with the official fold before
   designing any new live strategy.

No production integration is included in this branch.
