# Frank Wallet Conviction Watch

Updated: 2026-09-29 Asia/Bangkok
Parent automation: `$300 Crypto资产状态监控`
Cadence: existing hourly :29 run only. Do not create a separate scheduler.

## Target

Solana wallet:
`498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`

Purpose:
- use the wallet as a high-signal Meme/opportunity source;
- identify medium-duration conviction positions;
- explicitly reject latency/HFT copy-trading;
- never auto-trade.

## Runtime state

Persist the latest scan state here or in a sibling machine-readable/state artifact:
- last_scan_at
- per-mint first_seen_buy_at
- per-mint last_buy_at
- gross_buy_usd
- gross_sell_usd
- net_buy_usd
- buy_count
- sell_count
- estimated Frank VWAP
- current executable price
- price_vs_vwap_pct
- current liquidity / quote reserve when available
- classification: NO_ACTION | WATCH | HFT_EXECUTION | FORMAL_ENTRY | FORMAL_EXIT
- last_alert_key
- pending_email_subject
- pending_email_reason
- gmail_message_id
- gmail_readback_ok

Never infer a current state from a stale prior scan.

## What counts as an active buy/sell

Count only a transaction where the Frank wallet is the active swap participant and value is exchanged through a DEX/aggregator/pool.

Ignore:
- plain SPL/Token-2022 transfers;
- airdrops;
- creator-fee/reward receipts;
- token mint/creation;
- claim distributions;
- unsolicited deposits;
- LP bookkeeping that is not a directional token buy/sell.

A token balance increase alone is never a BUY signal.

## HFT / execution filter

Classify a mint as `HFT_EXECUTION` and do not alert when any strong execution pattern is present, including:
- >=3 active swaps in <=60 seconds for the same mint;
- rapid buy/sell round trips that largely close inside ~20 minutes;
- repeated routing/arbitrage across multiple pools where the wallet is cycling inventory rather than building a position.

HFT_EXECUTION is GitHub/state only. No Gmail. No ChatGPT notification.

## WATCH

WATCH is research state only and is silent.

A mint may enter WATCH when:
- at least 2 distinct active BUY swaps occurred within the rolling 60 minutes;
- gross active buys are directionally larger than sells;
- the wallet still has positive exposure;
- the pattern is not HFT_EXECUTION.

WATCH must never produce Gmail or ChatGPT output.

## Formal entry signal

Emit `FORMAL_ENTRY` only after **two consecutive hourly observations**. There is no one-cycle fast path.

First qualifying hourly observation:
- persist `WATCH`;
- stay completely silent.

Second or later hourly observation may become `FORMAL_ENTRY` only when every safety gate below is still satisfied:
1. active swaps only, no transfer-derived false signal;
2. the mint was WATCH in the prior hourly run;
3. Frank still has a materially open position and has either added exposure or retained >=70% of the WATCH-cycle peak token exposure;
4. cumulative gross active buys since first WATCH are >=10,000 USD equivalent;
5. sell value since first WATCH is <=30% of gross buy value;
6. estimated current executable price is between **8% below and 10% above** Frank VWAP. Below -8% is treated as possible deterioration, above +10% as too late to copy;
7. liquidity/quote reserve is adequate for a small Mission entry and is not collapsing;
8. no obvious token-control red flag is found in a bounded mint check, including unexpected mint/freeze authority, dangerous Token-2022 fee/hook/pause control, or an obvious honeypot/transfer restriction;
9. no HFT_EXECUTION classification;
10. the asset is not a stablecoin, wrapped major, canonical BTC/ETH/SOL wrapper, or obvious execution/hedging instrument already covered by other Mission lanes.

This intentionally gives up first-hour speed to reduce false positives and copy latency.

Do not alert solely because Frank made one large first buy.

For a valid FORMAL_ENTRY, include a Mission-sized action range of only 10-30 USD initially unless a separate stored rule justifies more. No automatic execution.

## Formal exit signal

Only evaluate FORMAL_EXIT for a mint that previously generated a delivered FORMAL_ENTRY.

Emit FORMAL_EXIT when one of these is verified:
- Frank reduces the tracked position by >=35% in a rolling hour;
- Frank effectively closes the position;
- repeated active sells clearly replace the prior accumulation regime;
- a hard token/liquidity invalidation emerges.

Small trims remain silent.

## Email-only formal delivery

Frank-wallet WATCH/HFT/NO_ACTION states are silent.

For FORMAL_ENTRY or FORMAL_EXIT:
- send Gmail to the existing Mission notification recipient;
- do not send a ChatGPT notification for this lane;
- use plain text;
- keep the body action-oriented and include: Bangkok timestamp; ticker/name if verified; full CA; signal type; why this passed the conviction filter; active buy/sell counts; estimated USD flow; Frank VWAP; current executable price and deviation; liquidity/quote reserve; bounded token-control/holder-risk notes; relevant transaction hashes; a clear **do-not-chase price**; invalidation/exit conditions; and the 10-30 USD Mission action range or exit instruction.
- do not include raw WATCH candidates, generic market commentary, or unrelated wallet activity.

Subject format:
`[300 Mission][ACTION][Frank] <ENTRY|EXIT> | <TICKER-or-CA-short> | YYYY-MM-DD HH:mm BKK`

## Delivery proof and retry

A formal signal is not delivered until Gmail Sent/readback is verified.

Before sending:
- search Gmail Sent by exact subject to deduplicate.

After sending:
- read back the returned Gmail message id;
- persist gmail_message_id and gmail_readback_ok=true.

If send or readback fails:
- persist `pending_email_subject` and `pending_email_reason`;
- on the next hourly run, recovery of the pending formal email happens before evaluating new Frank alerts;
- never downgrade a pending FORMAL_ENTRY/FORMAL_EXIT to NO_ACTION merely because a later scan is quiet;
- do not emit a substitute informal ChatGPT alert.

No test email should be sent merely to prove the connector works.

## Audit

Each hourly run should record one compact Frank lane result in the existing run final or a bounded sibling state update:
- frank_lane_status
- scanned_from / scanned_to
- tx_count_examined
- active_swap_count
- watch_mints
- hft_filtered_mints
- formal_signal
- email_delivery_state

Infrastructure/source errors are audit-only and silent.


## Latency-aware conviction override — 2026-09-29

User objective for this lane:
- working capital reference: about **100 USD**;
- prioritize stability over first-block speed;
- still preserve enough entry runway to participate in a later **3x-5x price move** when one occurs;
- a first alert that arrives only after a half-day without a fresh accumulation reason is normally too stale.

### Backtest / recall requirement

A delivery test with one hand-picked token is only a positive-control test. It does **not** prove there are no missed alerts.

A proper historical replay must:
1. enumerate every token with an active Frank DEX/aggregator swap in the replay window;
2. process events in timestamp order with no future information;
3. simulate the actual hourly :29 observation cadence;
4. output every historical FORMAL_ENTRY / FORMAL_EXIT that the rules would have generated;
5. report silent WATCH, HFT_EXECUTION, STALE_SIGNAL and rejected candidates separately;
6. calculate first meaningful accumulation time `T0`, alert time, alert latency, price-vs-Frank-VWAP at alert, and forward 1h/3h/6h/24h/7d outcome when historical pricing is available.

Historical replay results should be summarized in one audit/report. Do not send one Gmail per historical signal unless the user explicitly requests that.

Live operation remains different: every distinct new FORMAL_ENTRY / FORMAL_EXIT that passes the rules should be delivered once.

### Meaningful accumulation clock T0

Do not anchor latency to a dust/probe buy.

Start an accumulation episode clock `T0` when either:
- Frank makes >=2 active BUY swaps in <=60 minutes with combined gross buy >=3,000 USD equivalent; or
- one active BUY >=5,000 USD is followed by at least one additional active BUY within 60 minutes.

A single buy, regardless of PnL later, cannot by itself create FORMAL_ENTRY.

### Persistence can be proven from chain history

Do not require an extra scheduler cycle when the chain itself already proves persistence.

Persistence is satisfied by either:
- Path A: the mint was WATCH in the previous hourly run and still satisfies the entry gates now; or
- Path B: at the current run, the observed active BUY sequence already spans >=45 minutes from first to latest BUY, contains >=3 active BUY swaps, and the other FORMAL_ENTRY gates are satisfied.

This keeps the scanner hourly while avoiding an unnecessary additional 1-hour wait.

### Freshness guard

Normal desired first-alert latency after T0:
- target: **45 to 120 minutes**;
- >3 hours is considered late for a fresh new entry.

If `now - T0 > 3h`, a new FORMAL_ENTRY is allowed only when:
- Frank made a fresh active BUY in the last 60 minutes;
- the position remains materially open;
- current executable price <= Frank VWAP * 1.05;
- all normal safety/liquidity gates pass.

Otherwise classify `STALE_SIGNAL`, keep it silent, and do not send a late chase email.

### Formal-entry gates under this override

For a fresh FORMAL_ENTRY:
- persistence Path A or B above;
- cumulative gross active buys in the episode >=10,000 USD equivalent;
- sell value in the episode <=30% of gross buy value;
- current exposure >=70% of episode peak exposure or Frank has added exposure since the prior observation;
- current executable price normally between Frank VWAP * 0.92 and * 1.10;
- liquidity / quote reserve sufficient and not collapsing;
- bounded token-control / transfer restriction checks pass;
- no HFT_EXECUTION;
- stablecoins, wrapped majors and obvious execution/hedging instruments excluded.

### Runway information

A FORMAL_ENTRY email must also show:
- current market cap / FDV when reliably available;
- 3x implied market cap;
- 5x implied market cap;
- alert latency from T0.

These are scenario arithmetic, not a forecast.

### 100 USD lane sizing reference

For this Frank lane only:
- normal initial test size in a FORMAL_ENTRY: **20-30 USD**;
- if the next observation remains qualified and price has not violated the do-not-chase level, an additional **20-30 USD** may be considered;
- normal per-token cap from this ~100 USD lane: **50-60 USD**;
- preserve the rest as reserve for another signal / invalidation response.

No automatic transaction is permitted.
