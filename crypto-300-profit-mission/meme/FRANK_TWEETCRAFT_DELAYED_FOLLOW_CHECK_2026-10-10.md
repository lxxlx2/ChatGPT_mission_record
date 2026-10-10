# Frank TWEETCRAFT: delayed-copy historical spot check, 2026-10-10

## Scope, permissions, source quality

**Status: HISTORICAL_CANDLE_PROXIES_OBSERVED / EXECUTABLE_FOLLOW_ALPHA_NOT_VALIDATED / PERSON_PATTERN_OBSERVE_ONLY / PRODUCTION_NO_GO.** One **onchain-confirmed** Frank-root-authorized historical TWEETCRAFT BUY/SELL round trip from Oct 8 08:46:16 to Oct 9 08:26:47 Bangkok was +315.822278 USDC in transaction-net changes (+4.702721%), held 85,231 seconds. Those exact transactions are separately documented in `FRANK_TWEETCRAFT_ROOT_SWAP_EVIDENCE_20261009.md`.

To assess whether a follower could still profit by entering **later**, the research branch used GitHub Actions' own Internet access and the public, keyless **GeckoTerminal** Solana `/networks/solana/tokens/{mint}/pools` and `/networks/solana/pools/{pool}/ohlcv/minute` endpoints. This did **not** use Mac, user Alchemy keys, GMGN paid API, wallet signing or production systems. Historical OHLCV represents **pool prices at discrete candle CLOSES**, not executable quotes, guaranteed fills, timestamp-exact orderbook, SOL/Jupiter/FOMO router quotes or actual slippage for the user's $300 order. Market depth at that historical instant is not reconstructed; current pool reserves must never be used as historic liquidity.

Verification links:
- Historical two-pool, 5-minute-source query: https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/37965194086 (COMPLETE, success, source responses).
- Follow-up 1-minute-price query: https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/37965366394 (PumpSwap 1m success, **Meteora 1m returned HTTP 429**; no retry or invented price).

These are **single episode, after-the-fact timing-sensitivity probes**, not train/validation/holdout price forecasts, not a transferable investment strategy. Sampling the next candle starting at or after each target time introduces 1–5 minute candle close lookahead beyond the stated lag; reported percentages are **not timestamp-exact execution performance**. Exiting at the first candle start at/after Frank's actual sale time imposes the same close-proxy limitation on the exit. No tax, platform fee, gas, priority fee, MEV, swap spread or adverse price impact is modeled.

## Two actual historical pools, created before Frank's BUY

- PumpSwap TWEETCRAFT/SOL: `3NBq9zynLPDQQDvYf8xiMbWywQfKZD7m7fyprY524efq`, pool created `2026-10-06T20:27:40Z`.
- Meteora TWEETCRAFT/SOL: `3fCT5evpwmTSMWwpocRWG7jaMKnrKcbt6QdZxkWJ9gpf`, pool created `2026-10-07T03:49:14Z`.
- Both pair addresses appear compatible with the Pump AMM / Meteora routed transactions in the independent chain instruction audits. No proof that a $300 follower would be able to replicate Frank's split route and limit execution is available.
- Current API-reported reserves of these pools were ~$147k / ~$121k when queried. **Not historic liquidity**, do not input them as buying power at the moment of Frank's trade.

## Public historical price-proxy return observations (gross, before all costs)

Each percentage is `exit_pool_candle_close / delayed_entry_pool_candle_close - 1`. Not a signal, not a tradable fill, and ***not*** Frank's own realized execution return.

| Delay after the original Frank buy | PumpSwap 5m bar close | Meteora 5m bar close | PumpSwap 1m bar close | Meteora 1m |
|---|---:|---:|---:|---|
| 0 min (earliest next-candle proxy) | -14.393467% | -15.799096% | -20.865428% | UNVERIFIED: 429 |
| 5 min | **-7.858992%** | **-10.754997%** | **-12.721685%** | UNVERIFIED: 429 |
| 15 min | **-2.133872%** | **-5.232482%** | **-3.570757%** | UNVERIFIED: 429 |
| 30 min | -10.825741% | -14.522429% | +1.552257% | UNVERIFIED: 429 |
| 60 min | +4.934068% | -0.749868% | -8.723499% | UNVERIFIED: 429 |

The price/path data are highly sensitive to **bar resolution**, especially 30–60 minute follow lags. Therefore none of the positive proxies (PumpSwap 5m +4.93% at 60m, PumpSwap 1m +1.55% at 30m) can validate a profitable copy: their sign can reverse at finer granularity and excludes real transaction costs.

Recorded raw reference (per-token USD proxy):
- PumpSwap 5m exit close `0.001380815915660889`; 5m entry +5m `0.0014985899796560284`, +15m `0.0014109232100567002`, +30m `0.001548446746509389`, +60m `0.0013158890524758455`.
- Meteora 5m exit close `0.0013489287472019168`; 5m entry +5m `0.001511489389232072`, +15m `0.001423408335129342`, +30m `0.0015781084211944183`, +60m `0.0013591203605188538`.
- PumpSwap 1m exit close `0.001406682560137852`; 1m entry +5m `0.0016117205750532894`, +15m `0.0014587717595671912`, +30m `0.0013851809897536566`, +60m `0.0015411223573535858`.

## Evidence-based decision against frozen Meme policy

The policy in `crypto-300-profit-mission/MISSION_SPEC.md` and `crypto-300-profit-mission/meme/FRANK_LOCAL_SIGNAL_V1_POLICY.md` requires **at least TWO independently confirmed ACTIVE BUY swaps within 60 minutes AND cumulative 25,000 USDC** for the frozen `ACCUMULATION` classification. The old single-large-buy Path C does NOT qualify. This TWEETCRAFT sample has ONE confirmed buy spending 6715.734492 USDC and one confirmed full exit the following day. It **does not meet** the frozen accumulation gate and must not generate a live follow signal, regardless of its nominal positive realized net-USDC difference.

The visible data are not sufficient for a general Frank `PERSON_PATTERN`, repeatable alpha, profitable $300 delayed following, token-level consensus or 300-to-3000 strategy. Stronger evidence would require **independent additional** full-cost entry/exit rounds on distinct Solana mints, an explicit pre-specified signal timestamp and multiple lag scenarios with executable historical quotes, depth, fees, failed/no-route observations and outlier-excluded holdout evaluation. Those were not retrieved, and should remain `UNVERIFIED` rather than filled with backfitted assumptions.

**Operational**: GitHub Draft PR #29 research-only; no main merge, no standing scheduled workflow, production trades, alerts, Gmail, secret usage, dashboard, LaunchAgent or live config changes. Public GeckoTerminal 429 is a separate external data-source limit, never silently retried. No new Mac command required.
