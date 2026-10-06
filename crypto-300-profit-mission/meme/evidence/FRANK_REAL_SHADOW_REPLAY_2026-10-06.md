# Frank real shadow replay evidence — 2026-10-06

Status: `REVIEW_ONLY`

Production trading: `NO_GO`

Reviewed code commit used locally: `858ef37bbabcfe2f2baeaaeeb95f3478e044defb`

## Real production snapshot replay

Local production DB identified from the active Frank health/runtime evidence as:

`crypto-monitor-frank-only-evidence-20261003/live-v1/forward.sqlite`

A SQLite `.backup` snapshot was created before replay. The snapshot integrity check returned `ok`.

Snapshot observations supplied from the local run:

- signatures: `667`
- latest block time: `1791289006`
- source signals: `2`
- shadow signals: `2`
- missing source signals: `0`
- source signal regression pass: `true`
- active trades: `54`
- direct USDC trades: `54`
- SOL/WSOL trades: `0`
- SOL resolved: `0`
- SOL unresolved: `0`
- reference cache hits: `0`
- reference cache rejects: `0`
- reference failures: `{}`
- normalization failures: `{}`
- SOL-added signals: `[]`
- approval blocker: `NO_SOL_TRADES_EXERCISED`

The code-level aggregate `shadow_replay_gate_pass` was therefore `false` solely because the strict SOL capability gate requires at least one real SOL/WSOL trade to be exercised.

## Historical V1-compatible sample scan

The available DBs containing the current `signatures` schema were checked:

- `live/forward.sqlite`: 8 ACTIVE_TRADE, 8/8 quoted in USDC, 0 SOL/WSOL.
- `live-v1/forward.sqlite`: 54 ACTIVE_TRADE, 54/54 quoted in USDC, 0 SOL/WSOL.

Several older FM2/FM3/FM4 evidence databases use legacy tables such as `frank_transactions`, `frank_observations`, `candidates`, and `decisions`, but do not contain the current `signatures` table. They were not treated as equivalent V1 strict-replay samples.

## Interpretation

For the currently available V1-compatible real data:

```text
BASE_REPLAY = PASS
SOL_NORMALIZATION = IMPLEMENTED_BUT_NOT_EXERCISED
PRODUCTION_TRADING = NO_GO
```

`BASE_REPLAY = PASS` means the existing real USDC path reproduced all source signals with no missing signal under the reviewed shadow replay code.

`IMPLEMENTED_BUT_NOT_EXERCISED` is not a claim that the Binance SOLUSDC historical-response path has been validated against real SOL Frank trades. No available V1-compatible real sample exercised that path, so it remains an unvalidated capability sub-gate.

The absence of a SOL sample must not be represented as a USDC-path regression. Conversely, it must not be converted into a false SOL validation pass.

## Next validation stage

Proceed with real read-only Jupiter fixtures:

1. liquid route;
2. thin-liquidity route;
3. no-route behavior;
4. parser verification against immutable captures;
5. Mission Control `REVIEW_ONLY` forward observations;
6. Dashboard and notification-path validation without enabling live delivery.

No result in this evidence note authorizes production trading, live notification delivery, production policy mutation, scheduler creation, or automatic execution.
