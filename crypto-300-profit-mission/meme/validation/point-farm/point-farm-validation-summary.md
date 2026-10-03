# Point Farm PERSON_PATTERN historical validation

Date: 2026-10-03
Project: `$300 -> $3000 Mission`
Scope: Point Farm only
Production trading: `NO_GO`
Current decision: **KEEP `PERSON_PATTERN = OBSERVE_ONLY`**
Research status: **`CANDIDATE_NOT_QUALIFIED` / `NO_VALIDATED_PATTERN`**

## Executive conclusion

Point Farm does not currently pass independent PERSON_PATTERN qualification.

Five direct answers:

1. **Wallet identity:** current primary Solana wallet is high-confidence, but long-run person-level wallet continuity is incomplete. `Point Farm Capital (@pointfarmcap)` is independently mapped to `Beqv6dzTcjV2eodo8RRXCiCcnSYrS1vkQKhfqwHXqeit`. Direct Solana RPC in the research run confirmed that this wallet owns the current STONK token account. Dexu also maps the same handle to an unresolved truncated address `6cerGp…615t`; it must not be silently merged.
2. **Winner concentration:** reported recent PnL is overwhelmingly dominated by STONK and a few outliers. The 30-day uwuu snapshot puts STONK at roughly **95.8%-96.2%** of total displayed PnL. Removing STONK alone leaves roughly **+$380K to +$426K** at those snapshots, but removing STONK + ZCAT + RAYCAT gives about **-$231,998.99**. These are third-party snapshot values, not canonical chain-recomputed PnL.
3. **Accumulation discrimination:** accumulation describes Point Farm behavior but does not currently distinguish winners reliably. In 17 recoverable token-cycle fixtures, winner median buy count is 127 vs loser 117; winner median cumulative buy is about $20.5K vs loser about $27.2K. Buy-count/PnL association is weak and becomes weaker after removing STONK. High buy count, continued buying, and no-sell state are therefore rejected as standalone signals.
4. **Delayed replay:** not completed. Exact swap timestamps, causal trigger time, historical pool state, route quote, liquidity and slippage-adjusted executable entry are not available from the current data path. All delayed replay outputs remain `NOT_RUN_DATA_BLOCKED`; no candle-return substitute is accepted.
5. **Qualification:** not passed. There is no chain-complete >=30-episode ledger, no accepted delayed replay, no TRAIN/VALIDATION/HOLDOUT proof, and no robust positive result after top-winner exclusions.

Point Farm may still be useful later in `TOKEN_CONSENSUS` after conservative wallet-graph resolution, but this report does not enable any production signal.

## Wallet / identity map

Primary Solana wallet:

`Beqv6dzTcjV2eodo8RRXCiCcnSYrS1vkQKhfqwHXqeit`

Status:

`HIGH_CURRENT / CONTINUITY_INCOMPLETE`

Unresolved alternative attribution:

`6cerGp…615t`

Do not add the truncated address to a person wallet cluster until the full address and relationship are resolved.

Secondary EVM mapping exists (`0xfd87eda88be6c372453b721da63d58ad1a5b2d94`) but is outside this Solana replay pass.

Research evidence used:

- CopyFomo profile-to-wallet resolution;
- Banana Gun / Fomo Wallet Finder full-address publication;
- WPM independent mapping;
- direct Solana RPC ownership check for the current STONK token account;
- Dexu as a conflicting wallet-attribution signal that remains unresolved.

The Fomo profile has older public history, but pre-Sep-2026 profile activity must not automatically be assigned to the current Beqv wallet.

## Historical coverage

A chain-complete six-month swap ledger was not recovered.

Available broad coverage consists of:

- 30-day wallet aggregates refreshed around 2026-10-02;
- token-level OKX position/cycle snapshots;
- current raw-chain STONK ownership verification;
- identity cross-checks from several public wallet-resolution sources.

The imported `point-farm-episodes.csv` contains **17 research fixtures**, not qualification-grade episodes. Every row is marked:

`PARTIAL_TOKEN_CYCLE_NOT_FULLY_SEGMENTED`

They preserve real winner/loser examples while refusing to fabricate first-buy time, second-buy time, causal episode boundary, MFE/MAE or replay entry data.

## STONK and robustness

Canonical STONK mint:

`6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx`

The research confirms persistent accumulation behavior. Provider snapshots show very high buy counts and a large still-open position. Direct RPC confirmed the primary wallet still owned a large STONK balance during the research run.

Important accounting warning: the dominant multi-million-dollar STONK result is largely mark-to-market/open-position economics in current public snapshots. Do not treat it as fully realized profit.

uwuu contains internally inconsistent 30-day summary blocks, so both are preserved instead of silently choosing one:

- total PnL about $9.91M / STONK about $9.53M -> STONK share ~96.16%;
- total PnL about $10.16M / STONK about $9.73M -> STONK share ~95.81%.

The detailed snapshot also lists ZCAT about +$516.9K and RAYCAT about +$140.8K. Removing STONK, ZCAT and RAYCAT from that same displayed total yields about **-$231,998.99**.

Formal robustness still requires chain-level episode reconstruction. Third-party aggregate subtraction is a research warning, not final qualification evidence.

## Accumulation test

The 17-fixture exploratory sample contains 10 positive-PnL and 7 negative-PnL token cycles.

Key exploratory results from the source research:

- winner median buy count: 127;
- loser median buy count: 117;
- winner median cumulative buy: about $20.5K;
- loser median cumulative buy: about $27.2K;
- buy_count vs snapshot PnL Spearman rho ~0.275;
- excluding STONK, rho ~0.130.

These statistics are not a formal inference sample, but they are enough to reject simplistic rules such as `many adds = good signal`.

### Mandatory negative controls

**PURR**

An older snapshot showed roughly 943 buys, 0 sells and positive marked PnL. A later snapshot showed 1,150 buys, 2 sells, roughly $289.5K cumulative buys and about **-$124.3K total PnL**. Continued accumulation did not preserve the apparent edge.

**UBI**

About 692 buys and roughly $89.3K cumulative buy with around **-$17K** total PnL in the retained snapshot.

**TOEROGAN**

About 155 buys, 0 sells, roughly $49.7K cumulative buy and around **-$20.5K** total PnL.

Therefore these standalone proxy patterns are rejected:

- high buy count;
- repeated accumulation with no meaningful sell;
- large terminal cumulative exposure.

## Replay status

Canonical current repo horizons:

- T+5m
- T+15m
- T+1h
- T+6h
- T+24h

Additional research horizons:

- T+1m
- T+2m

Point Farm auxiliary compatibility horizons retained for research only:

- T+0m
- T+30m
- T+2h

All remain `NOT_RUN_DATA_BLOCKED` in this research pass because exact causal T0 and historical executable route/liquidity data were not recovered.

## Required future implementation

The next useful step is a chain-complete programmable swap export for the resolved Point Farm wallet graph, followed by deterministic position-state episode reconstruction and delayed replay.

Do not optimize trigger thresholds on these 17 partial rows.

Formal validation must include:

- >=30 valid fully reconstructed episodes for a tested pattern family;
- wallet graph resolution and internal-transfer exclusion;
- causal trigger features only;
- TRAIN / VALIDATION / HOLDOUT separation;
- executable delayed replay;
- All / Ex-Top1 / Ex-Top3 / Ex-STONK / Ex-largest-theme robustness;
- false-positive and followable-rate measurement;
- real FORWARD observation before any production enablement.

## Final state

```text
Point Farm
PERSON_PATTERN = OBSERVE_ONLY
validated patterns = 0
qualification = NOT PASSED
production = NO_GO
```

No automation, task, live validation, production registry, Gmail alert, wallet mutation or trading change is authorized by this research.
