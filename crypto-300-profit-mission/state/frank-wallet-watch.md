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
- do **not** use lifetime/gross sell-value ratio as a hard rejection gate: profitable conviction positions can recycle principal or trim while remaining materially exposed;
- current token-unit exposure should normally remain >=50% of the episode peak token-unit exposure; alternatively, Frank must have resumed net buying in the last 60 minutes and still hold a material open position;
- if token-unit exposure fell >35% during the last 60 minutes with no fresh re-accumulation, suppress ENTRY as distribution/exit-risk;
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


## Two-stage early-alert override — 2026-09-29 04:20 Asia/Bangkok

This section overrides earlier Frank notification staging where inconsistent.

User priority:
1. recall / no silent misses of qualifying Frank signals;
2. timeliness;
3. let the user make the final trading judgment;
4. preserve the later conviction filter for sizing.

The live notification state machine is now:
`PRECONFIRM -> SUSPECTED_CONVICTION | PRECONFIRM_CANCELLED`

A later `FORMAL_EXIT` may follow a delivered SUSPECTED_CONVICTION.

### Stage 1: 预确认 / PRECONFIRM

Send Gmail PRECONFIRM at the first hourly scan that verifies active Frank buying and one of these paths.

Path S: large buy + verified public call
- single active BUY >= 5,000 USD equivalent, OR active BUY aggregate >= 10,000 USD equivalent inside rolling 60 minutes; AND
- a first-party public Frank post/call on his own X/FOMO/public profile mentions the same token/ticker/CA within the prior 2 hours.

Third-party reposts, replies from other accounts, and generic market posts do not satisfy the social condition.

Path C: chain-only high-conviction fallback
- use only when first-party social source is unavailable, delayed, or not indexed;
- single active BUY >= 15,000 USD equivalent; OR
- active BUY aggregate >= 25,000 USD equivalent inside rolling 60 minutes with >=2 BUY swaps.

Path C email must explicitly state:
`社交喊单未核验 / 链上大额预确认`.

PRECONFIRM is an awareness alert, not a conviction confirmation.

Do not suppress PRECONFIRM solely because current price has moved above Frank VWAP. Show the deviation:
- > +15%: `追价风险：高`;
- > +25%: `仅观察，不建议追价`.

Minimal safety check before PRECONFIRM:
- exact mint/CA verified;
- active swap confirmed, not transfer/airdrop/reward;
- basic liquidity exists;
- no immediately visible hard honeypot / frozen-transfer condition.

Suggested PRECONFIRM capital language:
- `观察仓 0-15 USD`;
- never present PRECONFIRM as a reason to deploy the full ~100 USD lane.

### Stage 2: 疑似观点仓 / SUSPECTED_CONVICTION

This replaces the previous user-facing FORMAL_ENTRY label for Frank-lane entry alerts.

Send the second Gmail once later conviction conditions are satisfied:
- persistence Path A or B from the latency-aware override;
- meaningful accumulation T0 established;
- episode cumulative active BUY >=10,000 USD;
- current token-unit inventory remains materially open under latest inventory-retention rules;
- no recent distribution invalidation;
- current executable price normally inside Frank VWAP * 0.92 to * 1.10;
- liquidity, token-control and transfer-restriction checks pass;
- no HFT_EXECUTION;
- not a stablecoin/wrapped major/obvious execution or hedging instrument.

Subject label must contain `[疑似]`, not `[确认]`.

Suggested capital language:
- if user has not acted: `可考虑 20-30 USD 初始测试仓`;
- if a PRECONFIRM observation position was taken: `总风险仓位通常不超过 50-60 USD`;
- no automatic trading.

### PRECONFIRM cancellation / deterioration

If PRECONFIRM was delivered but SUSPECTED_CONVICTION does not develop, send one `[撤销预确认]` follow-up only when a hard invalidation is observed:
- token-unit inventory falls >35% in rolling 60 minutes with no re-accumulation;
- Frank effectively exits;
- liquidity collapses materially;
- a hard token-control / transfer-restriction risk appears;
- original first-party social call is deleted/retracted and chain behavior also fails to confirm.

Do not send cancellation merely because the next scan is quiet.

### Delivery labels

Use exact Frank subject prefixes:
- `[300 Mission][预确认][Frank]`
- `[300 Mission][疑似][Frank]`
- `[300 Mission][撤销预确认][Frank]`
- `[300 Mission][EXIT][Frank]`

Each stage for a mint/episode is delivered at most once.

### Anti-miss cursor / replay rules

1. Persist Solana cursor: last successfully processed signature/slot and scan timestamp.
2. Every run scans from persisted cursor to current finalized head, with 15-minute overlap.
3. Deduplicate by transaction signature.
4. Never advance cursor past an unprocessed/error gap.
5. If a run fails, next successful run resumes from old cursor and replays the gap.
6. Persist stage event before Gmail: event_id, mint, T0, stage, trigger tx hashes, created_at, delivery_state.
7. Gmail failure leaves event PENDING_DELIVERY and must be retried before newer Frank events.
8. A later quiet run cannot overwrite an undelivered event.
9. Social checking uses at least a 2-hour lookback overlap. If source is unavailable, record `social_source_unavailable`; never infer `no call`.
10. When social data recovers, re-evaluate unresolved large-buy episodes still inside freshness window.

This minimizes software/scheduler missed alerts. External provider outages can still delay delivery, so Gmail Sent + message-id readback remains mandatory proof.

### Timeliness constraint

The existing scheduler is hourly, so a qualifying event is sent on the next successful :29 scan.
Practical scheduler latency is 0-59 minutes before analysis/delivery.
Do not add another intentional full-hour wait when chain history already proves persistence.
Historical replay must measure both `T0 -> next :29` and `T0 -> delivered stage`.

## Live source hardening — 2026-09-29 12:45 Asia/Bangkok

The 12:33 scheduled Frank lane wrote `unavailable_source`, but a direct manual Alchemy read immediately afterwards successfully returned finalized signatures for the target wallet. Treat that run as a source-selection regression.

Primary chain source for every Frank run:
- select Alchemy app `mkhr4iorbgonin56` first;
- call Solana mainnet `getSignaturesForAddress` for `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ` from the durable cursor to finalized head;
- use `maxSupportedTransactionVersion=1` when reading transactions;
- keep 15-minute overlap and signature dedupe.

Active-swap proof:
- a signature merely mentioning the wallet is insufficient. Recent history contains third-party ATA creation and fee/reward transactions where Frank is not the active trader;
- when signer status is available, require Frank to be a transaction signer;
- if a complex transaction response is truncated before signer metadata, count it only when the same transaction contains a Frank-owned token balance delta plus a recognized DEX/aggregator/pool program or swap log and an opposing quote-asset delta consistent with a swap;
- if active-swap proof cannot be completed, classify the transaction `UNRESOLVED_TX` and do not advance the cursor past it. Never guess BUY from balance increase alone.

Fallback:
- web/OKX/uwuu/public analytics may enrich token name, historical profile or market context;
- they may not replace direct-chain proof of a live BUY/SELL;
- if Alchemy signature retrieval itself fails, retain the old cursor and retry next hour. Do not write `NO_ACTION` for that gap.

Cursor initialization:
- live two-stage rules became active around 2026-09-29 04:20 Asia/Bangkok;
- baseline signature immediately before activation: `35s2Y8jayg4XjASEWmNmFTAYBqbFE1G2XAc3CmVQG5zxiCZWBRcQFDmyAtvDkQn9deNJhSaxofS6NU34mDtWYtQS`, slot 451436899, blockTime 2026-09-29 04:15:07 Asia/Bangkok;
- first recovery scan must process every newer finalized signature before advancing the durable cursor.

Health proof required in every run audit:
- source_selected
- cursor_before / cursor_after
- signatures_seen
- active_swaps_verified
- passive_or_reward_filtered
- unresolved_tx_count
- cursor_advanced
- stage_events_persisted
- gmail_delivery_state.


## Dual Alchemy failover — 2026-09-29

Primary live app:
`mkhr4iorbgonin56`

Backup live app:
`h6m5pairkgzet7vz`

For finalized `getSignaturesForAddress` / `getTransaction` reads:
- use primary first;
- on 429, timeout or provider-unavailable, preserve cursor and retry the same request once on backup;
- record which app actually supplied the successful data;
- do not loop or fan out;
- if both fail, cursor remains unchanged and the lane is partial_failure.

Manual smoke test on 2026-09-29 confirmed both apps can independently return the same current finalized head signature for the Frank wallet.

This failover is availability hardening only. Active-swap proof and alert thresholds are unchanged.
