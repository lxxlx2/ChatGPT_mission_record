# CODEX_HANDOFF — Ethermonk PERSON_PATTERN Validation Pipeline

## Status

```yaml
candidate: Ethermonk
person_id: ethermonk
current_person_pattern_state: OBSERVE_ONLY
research_recommendation: KEEP_OBSERVE_ONLY
validated_pattern_count: 0
production_trading: NO_GO
production_config_change_authorized: false
```

## 1. Confirmed facts

- High-confidence public holding wallet:
  `2xUbYAVq1oJGj45d6JjnaYHAke3NQecUcqWvvVbwmYw8`.
- Related operational wallet with raw bidirectional evidence:
  `58c8h7YHd4DW25RBroRHC3D9wyLq8xKuaC7q4K5PNbSr`.
- `58c8` created/funded the first observed `2xUb` CATE ATA and transferred `2,840,053.288293 CATE`.
- `58c8` created/funded the first observed `2xUb` FONE ATA and transferred `9,824,921.440752 FONE`.
- `2xUb` later transferred `15,452,352.182300252 STONK` directly to a `58c8` token account.
- The STONK transfer was not a DEX sell.
- `58c8` later used the received STONK account in DEX activity.
- FOMO co-signer/fee payer:
  `AgmLJBMDCqWynYnQiPCuj9ewsNNsBJXyzoUhD9LJzN51`.
  It is platform infrastructure and must not be clustered as Ethermonk merely because it signs/pays gas.
- No PERSON_PATTERN passed historical/replay validation in this research.

## 2. Unconfirmed facts

- Whether `58c8` is Ethermonk-owned, delegated, or platform-managed.
- Full `Gt6MM3…pRqd` address and exact role from Dexu.
- Complete wallet migration history.
- Lifetime first activity / original capital source of the person-level wallet cluster.
- Full six-month person-level swaps.
- Chain-complete cost basis, realized PnL and exit mapping.
- Followability at required delay horizons.

## 3. Seed wallet map

```yaml
person_id: ethermonk
wallet_candidates:
  - address: 2xUbYAVq1oJGj45d6JjnaYHAke3NQecUcqWvvVbwmYw8
    role: HOLDING_OR_USER_WALLET
    identity_confidence: HIGH_BUT_NOT_FIRST_PARTY
    include_for_research: true
    production_enabled: false

  - address: 58c8h7YHd4DW25RBroRHC3D9wyLq8xKuaC7q4K5PNbSr
    role: EXECUTION_OR_SOURCE_CANDIDATE
    relationship_confidence: HIGH
    same_person_ownership: UNCONFIRMED
    include_for_research: true
    production_enabled: false

platform_addresses:
  - address: AgmLJBMDCqWynYnQiPCuj9ewsNNsBJXyzoUhD9LJzN51
    role: FOMO_COSIGNER_FEE_PAYER
    person_wallet: false

unresolved_profile_addresses:
  - address: Gt6MM3…pRqd
    source: Dexu
    status: FULL_ADDRESS_AND_ROLE_UNRESOLVED
```

## 4. Required historical range

```yaml
preferred: full_history
minimum: 6_months
current_research_raw_targeted_start: 2026-08-11
current_research_end: 2026-10-03
current_research_is_sufficient_for_qualification: false
```

Do not use the FOMO profile statement "2,260 trades since 2026-02-14" as a substitute for raw wallet history.

## 5. Source hierarchy

1. Solana finalized RPC / raw transactions / account state.
2. Decoded DEX/indexer rows with user account owner and route identity.
3. Historical pool OHLC/liquidity and token creation data.
4. Reliable analytics as cross-check.
5. FOMO/CopyFomo/uwuu/Fomp/social sources as discovery only.

## 6. Canonical data model

```yaml
wallet:
  person_id: string
  address: base58
  role: enum
  relationship_confidence: enum
  ownership_confidence: enum
  valid_from: timestamp|null
  valid_to: timestamp|null
  evidence_ids: [string]

raw_event:
  event_id: string
  signature: string
  slot: int
  block_time: timestamp
  signer_set: [address]
  fee_payer: address
  source_owner: address|null
  destination_owner: address|null
  source_token_account: address|null
  destination_token_account: address|null
  base_mint: address|null
  base_delta: decimal|null
  quote_mint: address|null
  quote_delta: decimal|null
  dex: string|null
  route_id: string|null
  event_type: enum[SWAP_BUY,SWAP_SELL,INTERNAL_TRANSFER,EXTERNAL_TRANSFER,FEE,ATA_CREATE,UNKNOWN]
  raw_confidence: enum

episode:
  episode_id: string
  person_id: ethermonk
  mint: address
  contributing_wallets: [address]
  first_market_buy_time: timestamp|null
  first_market_buy_signature: string|null
  observable_signal_time: timestamp|null
  signal_definition: string|null
  accumulation_start: timestamp|null
  accumulation_end: timestamp|null
  total_buy_usd: decimal|null
  buy_count: int|null
  average_entry: decimal|null
  max_position_usd: decimal|null
  first_sell_time: timestamp|null
  total_sell_usd: decimal|null
  realized_pnl_usd: decimal|null
  realized_roi: decimal|null
  unrealized_pnl_usd: decimal|null
  holding_duration_seconds: int|null
  mfe: decimal|null
  mae: decimal|null
  full_exit: bool|null
  entry_market_cap: decimal|null
  entry_liquidity: decimal|null
  token_age_seconds: int|null
  entry_volume: decimal|null
  holder_concentration: decimal|null
  reconstruction_status: enum
```

## 7. Validated patterns

```json
{
  "status": "NO_VALIDATED_PATTERN",
  "patterns": []
}
```

Research-only hypothesis: `EM_ACCUMULATION_CONVICTION_TRANSITION_V0`.

Do not convert the hypothesis into a production pattern or choose thresholds from the visible winners.

## 8. Implementation logic

### Phase 1 — wallet graph resolution

- Pull full signature histories for `2xUb` and `58c8`.
- Discover all directly interacting owner wallets.
- Exclude known platform/program/fee-payer/vault accounts.
- Score wallet relationships from:
  - bidirectional transfers,
  - repeated cross-token movement,
  - account creation funding,
  - same transaction control,
  - timing correlation,
  - downstream DEX execution.
- Never merge wallets solely from one CEX source or one transfer.
- Persist relationship evidence separately from ownership conclusion.

### Phase 2 — transaction classification

For every transaction:
- decode all token balance deltas;
- identify DEX route vs direct SPL transfer;
- dedupe aggregator + underlying pool rows;
- classify internal transfer separately;
- preserve signer/fee-payer distinction because FOMO sponsors gas.

Regression fixtures that must classify correctly:
- CATE `58c8 -> 2xUb` = internal/related transfer candidate, not `2xUb BUY`;
- FONE `58c8 -> 2xUb` = internal/related transfer candidate, not `2xUb BUY`;
- STONK `2xUb -> 58c8` = internal/related transfer candidate, not `2xUb SELL`.

### Phase 3 — person-level episode ledger

Only after wallet roles are resolved:
- merge accepted related wallets at person level;
- internal transfers do not alter person-level realized PnL/cost basis;
- DEX swaps create buy/sell lots;
- preserve partial sells and runner inventory;
- reconcile end balances exactly to chain state;
- flag unexplained token deltas.

### Phase 4 — signal discovery

Generate features without looking at HOLDOUT outcomes:

```yaml
features:
  first_market_buy_usd:
  buys_5m:
  buys_15m:
  buys_30m:
  buys_1h:
  cumulative_buy_5m_usd:
  cumulative_buy_30m_usd:
  cumulative_buy_1h_usd:
  position_growth_ratio:
  seconds_since_first_buy:
  token_age_seconds:
  market_cap:
  liquidity:
  volume_5m:
  volume_1h:
  holder_concentration:
  wallet_role:
  internal_transfer_ratio:
```

Candidate pattern family may include "probe → add → conviction transition", but thresholds are to be selected from TRAIN only.

### Phase 5 — delayed replay

For each causally observable signal T0:

```yaml
delays:
  - 1m
  - 2m
  - 5m
  - 15m
  - 1h
  - 6h
  - 24h
```

At each delay:
- query executable pool price;
- enforce liquidity floor;
- estimate small-account slippage;
- reject impossible fills;
- compute MFE/MAE;
- compute return to Ethermonk first market sell;
- compute return to person-level full exit;
- if no full exit, use one predefined timeout policy consistently;
- record win rate, median, mean, profit factor and false-positive rate.

### Phase 6 — robustness

Compute:
- All
- Ex-Top1 winner
- Ex-Top3 winners
- Ex-largest token/theme
- Ex-STONK if STONK is material

Do not use third-party PnL for these calculations.

### Phase 7 — validation splits

Chronological:
- TRAIN
- VALIDATION
- HOLDOUT
- real FORWARD

No threshold retuning after HOLDOUT is viewed.

## 9. Recommended artifacts

```text
validation/ethermonk/
  wallet-map.json
  wallet-relationship-evidence.csv
  raw-events.parquet
  transfer-classification.csv
  episodes.csv
  replay.csv
  robustness.json
  pattern-candidates.json
  holdout-report.json
  validation-report.md
  forward-state.json
```

## 10. Tests

1. CATE transfer fixture does not become a market buy.
2. FONE transfer fixture does not become a market buy.
3. STONK direct transfer does not become a market sell.
4. FOMO fee payer is excluded from person wallets.
5. DFlow/aggregator + pool legs dedupe to one user trade.
6. Same-person internal transfer preserves cost basis.
7. If `58c8` ownership remains unresolved, material episodes become `QUALIFICATION_BLOCKED`.
8. Replay T0 must be causally observable.
9. 1m/2m tests are extra; repo-required 5m/15m/1h/6h/24h must still run.
10. Replay uses executable price + slippage.
11. Robustness is recomputed from episode ledger after exclusions.
12. HOLDOUT does not modify learned thresholds.
13. Missing historical price/liquidity produces `UNAVAILABLE`, never imputation disguised as fact.

## 11. Acceptance criteria

No numerical alpha threshold is invented by this handoff. Preserve the Mission's current strategy-validation policy and require explicit user approval if a new profitability cutoff is needed.

Hard evidence gates before even considering `SIGNAL_ENABLED`:

```yaml
identity_gate:
  primary_wallet_confidence: sufficient
  material_wallet_graph_resolved: true

history_gate:
  full_or_min_6m: true
  major_data_gaps: false

episode_gate:
  chain_reconciled: true
  internal_transfers_separated: true
  major_winners_and_losers_complete: true

robustness_gate:
  all: complete
  ex_top1: complete
  ex_top3: complete
  ex_largest_token_theme: complete
  ex_stonk_if_material: complete

followability_gate:
  delay_1m: complete
  delay_2m: complete
  delay_5m: complete
  delay_15m: complete
  delay_1h: complete
  delay_6h: complete
  delay_24h: complete
  mfe_mae: complete
  liquidity_slippage: enforced

validation_gate:
  train: complete
  validation: complete
  holdout: complete
  real_forward: required_before_production_enablement
```

## 12. Forbidden production actions

- no `SIGNAL_ENABLED`;
- no task/automation creation;
- no `$300-3000` production task modification;
- no production Gmail alerts for Ethermonk;
- no production registry wallet addition;
- no wallet/trading action;
- no canonical PnL sourced only from third-party pages;
- no silent merge of `58c8` and `2xUb`;
- no use of profile lifetime stats as current-wallet lifetime history.

## Evidence transaction IDs

- CATE source transfer: `a8LVK2BKdwwa9US2Q3Sd4Jsq2NkHUZpMaXYzX1v4oo88dCwWWXbNjicjoUGK3q8UdLZkf2tQG1Ld3Yb2v8qMPS1`
- FONE source transfer: `5TikrUgW9orCCMvwFWZ1bLtvfpr7RfWqV4Y3MzZ4htmq4DUqvcM7uhkVH7WYwPKYoMH33RVWWeG4MQBrDMzzmdz`
- STONK transfer-out: `59Wdr1ZAMkdEFFJKvzUw8TrYRQkK38iRfqgNFhqhnJRWCVW4R5hb23zNkhQ2giCjpKDxGHXYnrXWX96yVqJ4YVin`
- downstream STONK DEX sample on `58c8`: `5n7rZaua69XMYp8NaNYvTL4B768izT2fxF6uLTwSqLViy9NWcMoep9bKDCnCAJ4bvHztVeBVssczrK47gfdiJyBg`
- MINI route sample: `MvgBJvSkiqofTGrXu4npg2hgkFTFPNsNApKdAsEpNwrzn1LTAHxR8iPe3PJ1XqeJatVoo8XrWf9iVK9cZZEDYR7`
- CTO route sample: `4C5uG3RArWgQDXxR6CGETKardTbwmierr2EFRLak2yBTZxJmsMRyCgYiDGBDg9FXnjDEc1NPX5jokmxNn6haGiM`

## Import authorization note

The originating research conversation was instructed not to write Git. The user explicitly authorized this separate conversation on 2026-10-03 to synchronize the research progress and required files into the Mission repository. This does not authorize any production/config/task change.
