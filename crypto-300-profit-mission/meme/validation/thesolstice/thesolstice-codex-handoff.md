# TheSolstice CODEX_HANDOFF

Date: 2026-10-03  
Mission: `$300 → $3000 Mission`  
Module: Meme / tracked-person validation  
Subject: `TheSolstice / @The__Solstice`  
Current state: `OBSERVE_ONLY`  
Production trading: `NO_GO`  
Validation outcome: `NO_VALIDATED_PATTERN`

## 1. Confirmed wallet

```yaml
person_id: thesolstice
public_handle: "@The__Solstice"
solana_wallet: "4ugDhHJ8XDXAeABmrNmGffFaLbJb9BkPyiFGVSV9ocwo"
wallet_identity_status: "HIGH_CONFIDENCE_NOT_FULLY_CRYPTOGRAPHICALLY_CONFIRMED_TO_X"
evm_wallet_secondary: "0xd1c77a04b87393e98a1220532e72e8f7d0a31c5a"
old_wallets: null
multiple_solana_execution_wallets: null
initial_funding: null
```

Evidence:
- Pump address profile renders `The__Solstice`.
- Vaulted independently reports recovery of a Solana address ending `ocwo` using 25 position matches.
- Fomo Wallet Finder secondary export gives the same full Solana address.
- Complete raw signature mapping of all profile trades has not been completed.

Fail closed on any future wallet merge. Never merge social-profile history across addresses only because the handle is the same.

## 2. Historical coverage

```yaml
profile_level:
  start: "2026-03-10"
  end_observed: "2026-09-30"
  evidence:
    fomo_trades_sep06: 1559
    fomo_wallet_finder_trades_sep30: "~3000"
detailed_public_trade_window:
  dates: "2026-08-15..2026-09-06"
  provider: "fomp"
  unique_tokens_aggregate: 38
  classified_buys: 75
  classified_sells: 90
  route_total: 166
  visible_history_rows: 150
  row_cap_detected: true
```

The detailed dataset is incomplete and cannot serve as a full six-month replay dataset.

## 3. Dataset schema

Each normalized swap row should contain at minimum:

```text
person_id
wallet
chain
signature
slot
block_time_utc
block_time_bangkok
mint
symbol
side
token_in
token_out
token_amount
quote_asset
quote_amount
usd_notional
route
pool
pool_type
pre_token_balance
post_token_balance
position_qty_after
position_cost_after
realized_pnl_delta
price_usd
market_cap
liquidity
volume_5m
volume_1h
holder_count
source
source_confidence
```

Each episode row should contain:

```text
episode_id
person_id
wallet
mint
first_buy_time
first_buy_price
first_buy_usd
buy_count
cumulative_buy_usd
average_entry
accumulation_duration
max_position_usd
position_growth_ratio
first_sell_time
first_sell_price
sell_count
full_exit_time
total_sell_usd
realized_pnl
roi
unrealized_pnl
hold_duration
mfe
mae
token_age_at_entry
market_cap_at_entry
liquidity_at_entry
volume_at_entry
market_cap_at_each_major_add
price_move_between_adds
is_full_exit
evidence_confidence
```

Missing values must remain `null`. Do not infer missing prices from market cap unless circulating supply and timestamp are independently verified.

## 4. Episode segmentation

Algorithm:

1. Group by `person_id + wallet + mint`.
2. Normalize all swap directions to BUY / SELL from the tracked wallet's point of view.
3. Exclude:
   - inbound airdrops;
   - token-account creation;
   - ordinary transfers;
   - CEX/bridge funding transfers;
   - internal wallet transfers;
   - spam token transfers.
4. Episode starts when position goes from zero to positive due to a BUY.
5. Episode remains open through adds and partial sells while position quantity stays above the dust threshold.
6. Episode ends only when economically material position reaches zero / configured dust.
7. Re-entry after full exit starts a new episode.
8. Open episodes are censored. Keep realized and unrealized PnL separate.
9. Symbol is display-only. Mint is canonical identity.
10. If wallet migration is later proven, do not merge episodes until the ownership link has its own evidence record.

## 5. Trend features

For every BUY after the first:

```text
price_change_since_first_buy
price_change_since_prev_buy
return_since_first_buy
unrealized_pnl_before_add
position_qty_before_add
position_qty_after_add
position_growth_ratio
mcap_before_add
mcap_change_since_first_buy
liquidity_before_add
liquidity_change_since_first_buy
volume_5m
volume_15m
volume_1h
volume_expansion_ratio
holder_count
holder_growth
buy_sell_flow_ratio
token_age
time_since_first_buy
time_since_prev_buy
```

Optional social/narrative fields must be point-in-time and cannot use future information.

## 6. Accumulation features

```text
buy_count_5m
buy_count_15m
buy_count_1h
buy_count_6h
buy_count_24h
cumulative_buy_usd_5m
cumulative_buy_usd_1h
cumulative_buy_usd_24h
net_buy_usd
gross_buy_usd
gross_sell_usd
position_growth_5m
position_growth_1h
position_growth_24h
max_single_add_usd
median_add_usd
add_size_trend
no_major_sell
partial_sell_ratio
time_to_stop_adding
```

## 7. Signal trigger

No production or validated research trigger currently exists.

A naive trigger such as:

```yaml
buy_count_Xm: ">= 3"
position_growth_ratio: ">= 2"
no_major_sell: true
```

must be treated as a rejected baseline because MARKET is a likely false positive.

Research candidate only:

```yaml
pattern_id: trend_accumulation_research_v0
status: RESEARCH_ONLY_UNVALIDATED
trigger_components:
  repeated_adds: true
  position_growth: true
  no_major_sell: true
  favorable_price_change_since_first_buy: true
  unrealized_pnl_before_add_positive: true
  trend_persistence_filter: true
```

Do not assign thresholds until the historical dataset is rebuilt and threshold search is separated into TRAIN / VALIDATION / HOLDOUT.

## 8. Replay logic

For every candidate trigger time `T_signal`:

1. Freeze all features strictly at `T_signal`.
2. Query the actual pool/route state after:
   - +1m
   - +2m
   - +5m
   - +15m
3. Use an executable buy quote for the mission's modeled size.
4. Include:
   - pool fee;
   - transfer tax if any;
   - route fee;
   - price impact;
   - slippage;
   - failed-route / insufficient-liquidity state.
5. Record:
   - executable entry;
   - quantity acquired;
   - post-signal MFE;
   - post-signal MAE;
   - return at source first sell;
   - return at source full exit;
   - max drawdown;
   - liquidity;
   - remaining upside ratio.
6. For open source episodes, use censoring and do not invent a full-exit return.
7. Compare signal performance against a token-universe base rate for the same launch-age and liquidity bucket.
8. Calculate false-positive rate.

Required output fields:

```text
T_signal
pre_signal_runup
entry_1m
entry_2m
entry_5m
entry_15m
slippage_1m
slippage_2m
slippage_5m
slippage_15m
post_signal_mfe_1m
post_signal_mae_1m
post_signal_mfe_2m
post_signal_mae_2m
post_signal_mfe_5m
post_signal_mae_5m
post_signal_mfe_15m
post_signal_mae_15m
return_to_first_sell_1m
return_to_first_sell_2m
return_to_first_sell_5m
return_to_first_sell_15m
return_to_full_exit_1m
return_to_full_exit_2m
return_to_full_exit_5m
return_to_full_exit_15m
remaining_upside_ratio
```

## 9. STONK exclusion test

Run all metrics on:
1. all episodes;
2. `mint != STONK`;
3. generic Top1 PnL contributor removed;
4. generic Top3 positive PnL contributors removed;
5. largest validated theme removed.

STONK mint:
`6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx`

Current partial-platform observation:
- Pump total displayed profit: `$7,473,255.25`
- STONK displayed contribution: `+$7,259,420.10`
- share: `97.14%`
- residual: `$213,835.15`

Do not use this platform subtraction as the final chain-level exclusion metric.

## 10. Generic Top1 / Top3 exclusion

Define ranking from the normalized episode table, after closing/censoring policy is fixed.

Suggested research ranking key:
- closed episodes: realized PnL;
- open episodes: keep unrealized separate and run an additional mark-to-market scenario.

Do not rank a closed episode and an open unrealized episode in the same field without an explicit accounting mode.

Required output:

```text
accounting_mode
top1_episode_id
top3_episode_ids
all_pnl
ex_top1_pnl
ex_top3_pnl
all_median_return
ex_top1_median_return
ex_top3_median_return
all_profit_factor
ex_top1_profit_factor
ex_top3_profit_factor
```

## 11. Pattern output schema

Only validated patterns can populate `patterns`.

```json
{
  "status": "VALIDATED_PATTERN_OR_NO_VALIDATED_PATTERN",
  "patterns": [
    {
      "pattern_id": "string",
      "description": "string",
      "trigger": {},
      "sample_count": 0,
      "winner_count": 0,
      "loser_count": 0,
      "median_return": null,
      "profit_factor": null,
      "ex_stonk_result": null,
      "ex_top1_result": null,
      "delay_1m": null,
      "delay_2m": null,
      "delay_5m": null,
      "delay_15m": null,
      "false_positive_rate": null,
      "failure_modes": [],
      "confidence": "LOW|MEDIUM|HIGH"
    }
  ]
}
```

Current file must remain:

```json
{
  "status": "NO_VALIDATED_PATTERN",
  "patterns": []
}
```

## 12. Acceptance criteria

These are research gates, not production configuration.

A candidate cannot pass if any mandatory field below is unavailable:

1. Wallet identity is sufficiently resolved for all included history.
2. Full target historical range is normalized from raw or lossless data.
3. Episode segmentation is deterministic.
4. Exact `T_signal` is deterministic and uses only information available then.
5. Ex-STONK and generic Ex-Top1 results remain positive under the chosen accounting mode.
6. Ex-Top3 result is reported.
7. +1m / +2m / +5m / +15m executable replay is complete.
8. +5m and +15m delayed performance must not have negative expected value under the selected validation metric.
9. Profit factor and median return are both reported.
10. False-positive rate is reported against a relevant base universe.
11. No single winner is allowed to be the sole reason the result is positive; the generic exclusion tests enforce this without inventing a concentration threshold.
12. TRAIN / VALIDATION / HOLDOUT separation exists with no token/time leakage.
13. Failure modes are explicitly enumerated.
14. Open positions are censored correctly.
15. A missing historical price/liquidity point causes the relevant replay sample to be invalid, not silently imputed.

Current TheSolstice candidate fails criteria 2, 4, 7, 9, 10 and 12, and the simple repeated-add rule is contradicted by MARKET.

## 13. Unit-test cases

### Identity and normalization

1. `same_symbol_different_mint`
   - two EYE/NEET-style same-symbol assets;
   - assert mint is canonical identity.

2. `inbound_airdrop_not_buy`
   - third party creates ATA / transfers token to tracked wallet;
   - assert no BUY episode starts.

3. `bridge_or_cex_transfer_not_swap`
   - inbound/outbound funding transfer;
   - assert excluded from buy/sell count.

4. `multi_wallet_person_no_double_count`
   - same person has Solana and EVM addresses;
   - assert TOKEN_CONSENSUS person_id counts once where designed.

### Episode segmentation

5. `stonk_partial_sell_keeps_episode_open`
   - buy → add → partial sells → more adds;
   - assert episode does not split while material balance remains.

6. `eye_multiple_sells_same_episode`
   - 3 buys + 4 sells;
   - assert sells are reductions until balance reaches zero.

7. `reentry_after_zero_starts_new_episode`
   - full exit followed by new buy;
   - assert new episode_id.

8. `open_episode_realized_unrealized_separate`
   - assert no synthetic full-exit PnL.

### Pattern false positives

9. `market_repeated_adds_must_not_auto_pass`
   - 22 buys / 0 sells sequence;
   - later severe loss;
   - assert repeated-add feature alone cannot qualify.

10. `pumprpg_single_buy_no_accumulation_signal`
    - 1 buy / 1 sell;
    - assert no accumulation trigger.

11. `missing_price_fails_closed`
    - add exists but no exact price/liquidity;
    - assert replay sample invalid.

### Exclusions

12. `exclude_stonk_by_mint`
    - remove only canonical STONK mint.

13. `exclude_top1_dynamic`
    - calculate top contributor from normalized episode PnL, do not hardcode STONK.

14. `exclude_top3_dynamic`
    - remove top three positive contributors and recompute all metrics.

15. `largest_theme_requires_validated_labels`
    - if theme membership unresolved, assert result is unavailable.

### Delay replay

16. `delay_1_2_5_15_uses_future_execution_only`
    - entry quote must be at or after delayed timestamp.

17. `no_lookahead_feature_leakage`
    - future volume/holders/price cannot enter T_signal features.

18. `insufficient_liquidity_invalidates_execution`
    - quote size cannot be filled inside modeled slippage;
    - assert no synthetic price.

## 14. Production restrictions

Hard restrictions for this handoff:

```yaml
production_trading: NO_GO
create_monitor: false
create_automation: false
modify_production_config: false
enable_live_validation: false
send_trade_alerts_from_this_pattern: false
commit_or_push_this_research: false
```

Codex may implement offline research/data-rebuild tooling only under existing repository rules.

## 15. Key research facts Codex must preserve

- TheSolstice Solana wallet candidate: `4ugDhHJ8XDXAeABmrNmGffFaLbJb9BkPyiFGVSV9ocwo`.
- Identity confidence: high, but not full cryptographic social proof.
- Profile history visible since Mar 10, 2026.
- Fomp detailed view is capped: 150 visible rows vs 165 classified buy/sell events / 166 route events.
- STONK: 13b/4s in tracked window; very large current winner.
- MARKET: 22b/0s in tracked window; later about -95.1% on Pump.
- EYE: 3b/4s.
- PUMPRPG: 1b/1s; dated Fomp snapshot shows material loss.
- STONK is ~97.14% of current Pump displayed profit.
- Simple continued-commitment signal is invalidated by MARKET.
- No valid 1/2/5/15 minute replay has been completed.
- Current status stays `OBSERVE_ONLY`.
- `thesolstice-patterns.json` stays `NO_VALIDATED_PATTERN`.
