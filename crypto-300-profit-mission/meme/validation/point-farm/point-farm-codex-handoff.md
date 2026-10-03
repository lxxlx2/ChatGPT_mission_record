# CODEX_HANDOFF: Point Farm historical validation

Date: 2026-10-03
Status: `NO_VALIDATED_PATTERN`
PERSON_PATTERN: keep `OBSERVE_ONLY`
Production: `NO_GO`
No automation/task/production configuration change is authorized by this handoff.

## 1. Wallet state

```yaml
person_id: point_farm
public_identity: "Point Farm Capital (@pointfarmcap)"
solana_wallet_primary: "Beqv6dzTcjV2eodo8RRXCiCcnSYrS1vkQKhfqwHXqeit"
identity_confidence: HIGH_CURRENT_CONTINUITY_INCOMPLETE
unresolved_wallet_hint: "6cerGp…615t"
unresolved_wallet_status: UNRESOLVED_DO_NOT_MERGE
evm_wallet_secondary: "0xfd87eda88be6c372453b721da63d58ad1a5b2d94"
production_enabled: false
```

Current raw-chain research confirmed that the primary Solana wallet owns the STONK token account. The unresolved Dexu address must not be added to `wallets[]`, treated as an old wallet, or merged into history until a full address and direct relationship are established.

## 2. Research data status

The source research contains 17 real token-cycle fixtures. They are not fully reconstructed episodes.

Canonical record label:

`PARTIAL_TOKEN_CYCLE_NOT_FULLY_SEGMENTED`

The repo copy of `point-farm-episodes.csv` is a compact canonical fixture projection for Codex. It preserves all 17 rows and the key wallet-position metrics needed for regression testing. The original source research defined a broader 47-column schema; Codex should generate the full schema below from chain-complete data rather than treating missing source columns as zero.

No trigger has passed replay. `point-farm-patterns.json` must remain:

```json
{
  "status": "NO_VALIDATED_PATTERN",
  "patterns": []
}
```

## 3. Source hierarchy

Prefer, in order:

1. finalized Solana transactions / parsed swap indexer;
2. Alchemy/Helius-compatible programmable Solana history;
3. DEX pool historical reserves/trades for executable replay;
4. Fomo wallet-trades API when a valid API key is available through environment configuration;
5. OKX/uwuu/Cielo/GMGN only as discovery and reconciliation layers.

Never make third-party PnL canonical episode truth.

## 4. Person-level event classification

Before PnL or episode construction, classify every event as at least:

```text
MARKET_BUY
MARKET_SELL
INTERNAL_TRANSFER
EXTERNAL_TRANSFER
AIRDROP
FEE
ATA_CREATE
BRIDGE_OR_CEX_FUNDING
UNKNOWN
```

If future research proves multiple Point Farm wallets, direct transfer between accepted wallets in the same person cluster is an internal transfer and must not create synthetic BUY/SELL events or alter person-level cost basis.

Do not merge wallets solely because a third-party site attaches the same handle.

## 5. Episode segmentation

Use position state, not an arbitrary fixed inactivity threshold.

Pseudo-logic:

```text
for person_id + mint ordered by finalized block_time:
    classify event

    if no active episode and MARKET_BUY moves position from zero/dust to positive:
        start episode

    while episode active:
        MARKET_BUY -> add
        MARKET_SELL -> reduce
        partial sell + later add -> same episode while meaningful balance remains
        same-person internal transfer -> no new market event

        if position <= validated dust_exit_threshold and remains effectively exited:
            close episode

    next MARKET_BUY after closed episode -> new episode
```

If a position never reaches exact zero, derive any dormant-gap threshold from Point Farm's TRAIN history:

1. compute log inter-event gaps by mint;
2. inspect for a natural regime valley;
3. estimate threshold on TRAIN only;
4. require a position/thesis reset condition as well as elapsed time;
5. freeze before VALIDATION/HOLDOUT.

Do not hardcode 24h/7d and call it validated.

## 6. Canonical full episode schema

At minimum persist:

```text
person_id
wallet_id
mint
episode_id
first_buy_time
first_buy_price
first_buy_usd
second_buy_time
second_buy_usd
buy_count
sell_count
gross_buy_usd
gross_sell_usd
net_cost_basis_usd
peak_net_exposure_usd
current_net_exposure_usd
first_buy_pct_of_total_gross_buy
position_growth_ratio
time_to_2x_initial_position
time_to_3x_initial_position
accumulation_duration
median_inter_buy_gap
p25_inter_buy_gap
p75_inter_buy_gap
buys_15m
buys_30m
buys_1h
buys_6h
buys_24h
gross_buy_15m
gross_buy_30m
gross_buy_1h
net_buy_15m
net_buy_30m
net_buy_1h
sell_during_accumulation
price_return_since_first_buy
price_return_between_adds
adds_on_green_count
adds_on_drawdown_count
market_cap_at_first_buy
liquidity_at_first_buy
volume_at_first_buy
holder_count_at_first_buy
concentration_at_first_buy
first_sell_time
full_exit_time
realized_pnl_usd
realized_roi
unrealized_pnl_usd
mfe
mae
holding_duration
followable_at_trigger
unfollowable_reason
source_signatures[]
reconstruction_status
```

Missing historical values remain null/UNAVAILABLE. Never impute them as fact.

## 7. Accumulation feature definitions

Use only information available at event time.

```text
initial_exposure = net market exposure immediately after first MARKET_BUY
position_growth_ratio(t) = net_exposure(t) / initial_exposure

time_to_2x = first t where net_exposure(t) >= 2 * initial_exposure
time_to_3x = first t where net_exposure(t) >= 3 * initial_exposure

buy_velocity(window,t) = count(MARKET_BUY in [t-window,t]) / window
gross_buy_velocity(window,t) = sum(buy_usd in [t-window,t]) / window
acceleration = recent_velocity_short - prior_velocity_comparable_window
```

Forbidden trigger leakage:

- final episode buy count;
- final PnL;
- future peak exposure;
- future exit state;
- future liquidity/volume/holders.

## 8. Candidate trigger research

Generate thresholds from TRAIN distributions only. At minimum evaluate:

```text
second_buy
third_buy
position_growth_ratio >= TRAIN-derived threshold
N buys within 15m / 30m / 1h
cumulative gross buy >= TRAIN-derived percentile
continued net buying with no meaningful sell
positive-price confirmation + continued add
pullback-add / averaging-down state
velocity acceleration
```

Do not optimize thresholds on the 17 source fixtures.

Research result already established:

- terminal buy count is not sufficient;
- terminal gross buy is not sufficient;
- no-sell + continued accumulation is not sufficient.

PURR, UBI and TOEROGAN are mandatory negative controls.

## 9. Replay horizons

Canonical current repo horizons:

```text
T+5m
T+15m
T+1h
T+6h
T+24h
```

Allowed extra high-resolution research horizons:

```text
T+1m
T+2m
```

Point Farm auxiliary compatibility horizons:

```text
T+0m
T+30m
T+2h
```

Keep groups tagged by role. Auxiliary horizons never replace canonical qualification horizons.

For every candidate trigger:

1. `T_signal` is the first finalized moment all trigger conditions are causally observable;
2. query historical pool/route state at each replay horizon;
3. use a pre-declared user notional;
4. include route fee, pool fee, price impact and slippage;
5. mark `UNFOLLOWABLE` when no reliable route/quote exists or configured impact limit is exceeded;
6. compute return to Point Farm first sell, full exit/common timeout, fixed horizons, MFE and MAE;
7. never use Point Farm's own source entry as the user's delayed entry.

Do not silently invent slippage/max-impact thresholds. Put them in validation config and freeze before HOLDOUT.

## 10. Robustness

For each pattern and full episode set compute:

```text
All
Ex-Top1
Ex-Top3
Ex-STONK
Ex-largest-theme
```

Metrics:

```text
sample_count
winner_count
loser_count
realized_pnl_usd
median_roi
mean_roi
win_rate
profit_factor
median_hold
mean_hold
false_positive_rate
followable_rate
pnl_concentration_top1
pnl_concentration_top3
```

Use episode-level realized economics for formal qualification. Keep open/unrealized mark-to-market in separate fields.

Current third-party research warning to reproduce from canonical transactions before any promotion:

- STONK contributes about 95.8%-96.2% of the displayed 30-day PnL;
- detailed Ex-Top3 snapshot is about `-$231,999`.

## 11. Mandatory regression fixtures

1. `wallet_identity_primary` — `@pointfarmcap` maps to `Beqv6d…qeit` with high current confidence.
2. `wallet_identity_conflict` — `6cerGp…615t` remains unresolved and must not auto-merge.
3. `stonk_balance_snapshot` — use a frozen research snapshot, not a live mutable balance assertion.
4. `partial_sell_rebuy_same_episode` — BUY -> partial SELL -> BUY with meaningful balance stays one episode.
5. `full_exit_reentry_new_episode` — full exit -> later BUY starts a new episode.
6. `dust_exit` — tiny residual dust does not keep an episode open forever.
7. `internal_transfer_not_market_trade` — same-person transfer is not BUY/SELL.
8. `purr_accumulation_failure` — high/repeated accumulation must not automatically qualify.
9. `ubi_accumulation_failure` — 692-buy losing snapshot defeats buy-count-only logic.
10. `toerogan_no_sell_failure` — repeated buys + zero sells must not auto-pass.
11. `top1_removal` — recompute after STONK removal.
12. `top3_removal` — recompute metrics and denominators after top-three removal.
13. `no_lookahead` — trigger builder cannot access final buy count/PnL/future peak exposure.
14. `canonical_horizons` — 5m/15m/1h/6h/24h always present; other horizons tagged extras.
15. `unfollowable` — missing historical route/liquidity produces `UNFOLLOWABLE`, not candle substitution.

## 12. Acceptance criteria

Point Farm PERSON_PATTERN cannot pass unless all are true:

1. wallet graph is sufficiently resolved to attribute events to one `person_id` without double counting;
2. at least **30 valid, fully reconstructed episodes** exist for the tested pattern family;
3. no look-ahead features;
4. chronological TRAIN / VALIDATION / HOLDOUT split;
5. canonical delayed replay complete with executable historical entry assumptions;
6. pattern remains useful after Ex-Top1 and Ex-Top3 stress and explicit Ex-STONK test;
7. result is not dependent on a single narrative/theme or market regime;
8. false-positive burden and followable rate are measured against a relevant base rate;
9. liquidity/price-impact constraints pass for the configured user notional;
10. real FORWARD observation completes before production enablement.

The repository does not currently define a universal minimum profit factor or win rate. Do not invent one after seeing outcomes. If numeric gates are introduced, pre-register them before VALIDATION/HOLDOUT.

## 13. Current technical blockers

The source research attempted:

- Alchemy Solana RPC: current signatures/token ownership works;
- OKX wallet analytics: token-level buy/sell counts and snapshot economics available;
- uwuu: 30-day aggregate/top winner-loser context available;
- CopyFomo/Banana Gun/WPM: identity resolution evidence;
- Dexu: conflicting attribution evidence;
- Fomo wallet-trades API: documented but API key unavailable;
- public Solana RPC in local environment: DNS/network blocked;
- Solscan path: unavailable in the research interface;
- Alchemy connector backward history: possible but large-response truncation and no batch parsed-swap export make ~14K-trade reconstruction impractical through that interface.

Blocked outputs:

- complete six-month swap ledger;
- exact first/second/third buy timestamps;
- 2x/3x exposure transition time;
- numeric episode-gap distribution;
- >=30 fully reconstructed episodes;
- historical executable liquidity/slippage at T_signal;
- MFE/MAE and delayed replay;
- formal TRAIN/VALIDATION/HOLDOUT qualification.

## 14. Production restrictions

This handoff does **not** authorize:

- enabling Point Farm PERSON_PATTERN alerts;
- changing `OBSERVE_ONLY`;
- adding/removing ChatGPT automations or local schedulers;
- changing production wallet registries;
- live validation;
- Gmail alert changes;
- wallet mutation or trading;
- production config changes.

## 15. Engineering conclusion

The next useful engineering step is a chain-complete programmable swap export for the resolved Point Farm wallet graph, followed by deterministic person-level episode construction and delayed replay.

Do not optimize strategy thresholds on the 17 partial token-cycle fixtures.
