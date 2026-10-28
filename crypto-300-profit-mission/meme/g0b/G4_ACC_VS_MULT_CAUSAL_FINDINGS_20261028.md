# Frank G4: ACC vs formal MULT causal-clock comparison (offline evidence, 2026-10-28)

**Final research result: `ACC_EARLIER_NOT_YET_PROVEN_PROFITABLE / MULT_PRICE_CAUSALITY_INADEQUATE / STRATEGY_NEED_MORE_DATA`.** This is a completed **historical source and timing study**, not an executable follower PnL backtest, independent out-of-sample validation or production approval. No additional provider requests, RPC, private Mac data, production startup, trade, default investment amount or new monitoring were used.

## 1. Frozen evidence and exact scope

- Research parent: PR #235 HEAD `a5b7bd985ebd44ae2b661188a62898b11fe431bc` (still a separate Draft), building upon G0-A PR #117 frozen archive.
- Machine-readable comparison: [G4_ACC_VS_MULT_CAUSAL_CROSSWALK_20261028.json](./G4_ACC_VS_MULT_CAUSAL_CROSSWALK_20261028.json), with all **22 ACC episode rows**, all **10 paired MULT rows**, exact event epochs and six selected root-wallet cashflow-lot associations.
- Actual M3 archived study blob `a31a2bbcd1fe7c70951152f2a23edca6c934dc40`; selected six-lot source blob `b44cc2140927246f9a428c8c455a6793eb80b662`; G0-A inventory blob `0f06fbcc5a1cc8896e54fdf4b83b743ca3c928ac`; G0-B finished-price-pilot report blob `4c138ae3083fbdd0e72c5e34ba096e62189b4d1d`.
- The archived M3 population covers **315 research ACTIVE BUY signatures / 188 BUY episodes / 160 mints**, and **22 signal-bearing episodes / 18 signal-bearing mints**. All **10 formal MULT** episodes overlap with the ACC cohort; they are NOT additional independent opportunities. The study represents a known bounded 2026-09-03 to 09-30 historical development subset, not full-chain person coverage or untouched OOS.
- Calculations match by the exact `episode_id` for ACC→MULT. The `position.first_buy_at` clock means **model-episode first BUY**; it is not a verified first-ever BUY on all Frank wallets. Selected root-lot join matches the exact full mint to a **unique** M3 ACC episode; it is not a fresh reconstruction of every fill.

## 2. Pre-trade decision clocks: ACC and MULT are distinct strategies

| Measure | ACC model event | Formal MULT model event |
|---|---:|---:|
| Unique historical episodes | 22 | 10 (subset of ACC) |
| Anchor event | `ACC.triggered_at` | `MULT.triggered_at`, never backdated to ACC |
| Median time after preceding milestone | **13 sec** from model first BUY | **75 min 38 sec** after ACC |
| Lag over 10 min | **6/22** | **8/10** |
| Same timestamp as earlier milestone | Not applicable | **2/10** |
| Strict verified follower entry+exit quotes | **0 in inspected records** | **0 in inspected records** |

12/22 archived ACC triggers were within 60 seconds of the model episode's first BUY. This is historical **model clock alignment**, not proof the signal was indexed, delivered, read or traded within 60 seconds.

**All 10 distinct MULT episodes (including two separate episodes of Hg5):**

| Mint prefix | Episode prefix | ACC time | MULT time | ACC→MULT minutes |
|---|---|---|---|---:|
| `MukLDtJ8C…` | `1a894b5b9f…` | 2026-09-05 21:00 UTC | 2026-09-05 21:00 UTC | 0.00 |
| `BPxxfRCXk…` | `a47f853423…` | 2026-09-20 18:56 UTC | 2026-09-20 18:56 UTC | 0.00 |
| `CbcyNo7m1…` | `8f1f62ae6a…` | 2026-09-26 03:26 UTC | 2026-09-26 04:29 UTC | 62.83 |
| `Hg5Ja55T5…` | `8a5edea645…` | 2026-09-16 19:18 UTC | 2026-09-16 20:29 UTC | 70.03 |
| `DEW9dSN6Q…` | `a48f9a0e5d…` | 2026-09-23 23:13 UTC | 2026-09-24 00:29 UTC | 75.08 |
| `4K1m7gAMD…` | `32e5cdb790…` | 2026-09-22 17:12 UTC | 2026-09-22 18:29 UTC | 76.18 |
| `98kfF7rms…` | `14439f5c03…` | 2026-09-16 14:11 UTC | 2026-09-16 15:29 UTC | 77.77 |
| `Hg5Ja55T5…` | `ecbae1d4c2…` | 2026-09-14 16:45 UTC | 2026-09-14 18:29 UTC | 103.55 |
| `PerPsCe2S…` | `ba70bd2771…` | 2026-09-12 16:37 UTC | 2026-09-12 18:29 UTC | 111.75 |
| `HcRLc9VDg…` | `a26e0ae867…` | 2026-09-06 19:34 UTC | 2026-09-06 21:29 UTC | 114.87 |

The 8 late MULT events cannot inherit a hypothetical ACC+5-minute fill. M3's 5-minute candle proxy for PerPs (an eventually-MULT episode) is keyed to its prior ACC T0. The actual PerPs formal MULT occurs 111.75 min after ACC. It is a lookahead violation to label **+118.154%** from ACC+300 seconds as a formal MULT follower outcome.

## 3. Check against previously independently examined root-wallet quote-lot outcomes

These are selected, mostly root-signed historical USDC trade-flow case studies. Returns reflect **Frank's entire observed original lot from gross buy quote to documented sales**, NOT buying at a signal nor a follower net ROI. Native SOL gas and all external costs/person-linked wallets are not fully reconciled. The samples were chosen by available evidence, not randomly.

| Mint prefix | ACC in M3 | Formal MULT after ACC | ACC to last observed root exit | Frank observed quote spread % | Note |
|---|---|---|---:|---:|---|
| `MukLDtJ8C…` | 有 | 0.00 分 | 353.75 分 | +19.89% | 已在 ACC+24h 前退出 |
| `8K5X85PAJ…` | 有 | 无 | 105.32 分 | -0.05% | 已在 ACC+24h 前退出 |
| `E4Ap4icML…` | 有 | 无 | 23.87 分 | -18.18% | 已在 ACC+24h 前退出 |
| `PerPsCe2S…` | 有 | 111.75 分 | 1880.75 分 | +129.33% | 晚于 ACC+24h 退出 |
| `4K1m7gAMD…` | 有 | 76.18 分 | 211.22 分 | -37.90% | 已在 ACC+24h 前退出 |
| `HzYCHqAN2…` | 未触发 | — | — | +4.70% | 非信号对照，不能算 ACC 跟单 |

**4/5 ACC-matched observed lots had already completed their documented last sale BEFORE ACC+24h.** The old single `T0+24h` price horizon thus measures a *different exit policy* from mimicking Frank's exit on at least four of five known lots. It is not an inferable follower trailing-exit return.

Within the five selected ACC-matched root lots: 2 positive, 3 negative observed USDC spreads. Three of these five later had a formal MULT: MukLD positive, PerPs positive, 4K1m negative. The other two ACC-only selected lots, 8K5 and E4Ap, were negative. These small, outcome-conditioned counts **cannot** establish MULT positive predictive accuracy or ACC false-positive rate. TWEETCRAFT was a separately studied **non-ACC control** with positive root cashflow, so an ACC filter can omit Frank winners as well.

Separate source study of **six** root lots: total observed quote spread +25,110.285414 USDC; excluding the PerPs winner leaves **−9,809.708488 USDC**. Another **10-mint local-ledger** study had 3 positive/7 negative nominal cashflow spreads and flips from +2,857.194601 to −17,844.063583 without its largest winner, but its raw execution evidence grade is lower. **These cohorts overlap on TWEETCRAFT and must never be summed.** Neither is representative of all 188 historical episodes.

## 4. Historical market-price data cannot yet compare the two strategies' returns

G0-B PR #235 already performed **36 public HTTP200 GETs once** on a frozen **12-episode** sample. Only **6/12** had complete five-lag 1m candle-close proxies; 4/8 signal and 2/4 biased non-signal controls missed precommitted 6/8 and 3/4 sufficiency gates. The returned 1m bar closes are future-known prices, not executable quotes. Present-day-ranked pool selection has survivorship risk; missing bars and tiny volumes remain missing or unsuitable, not risk-free fills.

In the four "eventual MULT" episodes, the source pilot actually anchored T0 to first ACC-or-MULT. Only **M1 MukLD (1/4)** has coincident first ACC/formal MULT and thus an available true-MULT aligned price window. For M2 HcRL, M3 PerPs, M4 Hg5 the formal MULT is **about 103–115 minutes after** that first ACC; the archived entry OHLCV windows DO NOT reach the formal MULT time. There is consequently **no valid pairwise ACC-vs-MULT follower-return estimate** from the available pilot. M4's $0.62 entry and $0.01 exit minute pool volumes, and C3's $5.19 exit minute volume, are especially poor executability evidence.

| Proposed research strategy | Defensible entry clock | Required exit clocks | Price / liquidity evidence now | Verdict |
|---|---|---|---|---|
| Earliest ACC | Actual frozen ACC timestamp **plus measured visibility latency** | (a) precommitted fixed horizon; (b) separately verified first Frank SELL/exit observation | Partial 1m close proxies; no time-and-size matched executable entry/exit | **NEED_MORE_DATA** |
| Confirmed MULT | Actual frozen formal MULT timestamp **plus measured visibility latency** | Same two policies, with identical cost and timing rules | True MULT entry-time pilot covered **1/4** eventual MULT; no verified size-dependent fills | **NEED_MORE_DATA** |
| All Frank BUY as comparator | Explicit actual BUY event from local verified ledger, **no signal retrofilling** | Same two policies | Wallet's own trading price is NOT a follower quote | **CONTROL_ONLY / NOT_SCORABLE** |

**Mandatory denominator:** keep all 22 ACC episodes and all 10 MULT subset episodes as distinct strategy memberships, not 32 independent episodes; carry missing post-trigger data through outcome calculations. Comparing costless candle outcomes on the few surviving pools would be misleading.

## 5. What is still necessary for a genuine strategy decision

1. Hold `ACC` and `MULT` signal clocks separately, and record the **first verifiable actual availability** of each signal. Historical model-trigger time alone cannot establish alert delay.
2. Before data collection, lock entry lag ladder **30/120/300/900/3600 seconds**, two non-mixed exit policy families (fixed horizon versus actual observed Frank exit), inclusion denominator and source/missingness treatment.
3. To compute actual follower returns, obtain timestamp-aligned **entry and exit** price/route/depth/fee/gas/failure evidence appropriate to a **user-chosen amount**. **No default order amount** or simulated PnL when unknown. Price-only proxies remain explicitly non-executable.
4. Report both winner-removed and all-case outcomes; preserve loss, illiquid exit, missing quotation, missing sell and uncaptured old wallet addresses as separate categories.
5. If existing cached evidence is insufficient for *causal aligned* prices, stop with `NEED_MORE_DATA`; do not silently consume previously unused API budget or launch repeated/live polling. A **new specific user authorization** is required for any fresh historical or forward provider/RPC collection, and likewise for production changes, notifications or trading.

## Audit disposition

**Completed in this work:** exact 22/10 archived signal-clock matching, independently recalculated 13-sec/75m38s medians, selected root-lot signal/last-exit crosswalk, evidence grade and 24h-horizon mismatch. No new prices were invented. The original PR #235 was **not mutated**; this result is isolated to a child research branch for independent fixed-SHA review.

**Current status: `G4_OFFLINE_CAUSAL_CLOCK_PASS / ACC_VS_MULT_EXECUTABLE_RETURN_NOT_SCORABLE / STRATEGY_NEED_MORE_DATA / PRODUCTION_NO_GO`.**
