# BSC Address Modeling V1: Original Episode Cashflows and Fixed Multi-Fill Reserve Replay

As of 2026-10-11. RESEARCH_ONLY / OBSERVE_ONLY / PRODUCTION_TRADING=NO_GO.

## Key findings

1. Wallet 0x8e6b3c9c72ca592bbab470f761fa869c174e9ea0 on token 4 has **two separate closed inventory episodes**. The prior 19/19 owner-signed original transaction BNB/WBNB exact settlement audit gives first episode **-0.117977426190152500 BNB**, second **+13.282964879793219115 BNB**, combined **+13.164987453603066615 BNB**. The profit is concentrated in the second original episode, not the first.
2. Wallet 0x239e74bfbd02d71cdc70fecc2d505dc13acfb337 has **two confirmed actively traded token positions** (我踏马来了, 龙虾) and one additional inbound-only 牛来 token record within the 19 previously selected BSC token contracts. All original 27 trading transaction signer/status records for the two active positions are verified. The 牛来 inbound has zero native BNB balance change in its block and a truncated original sender field; do not classify it as a self-initiated buy.
3. Within the prior narrow 19-CA venue-sample set, four tokens have sampled pool activity at/after the wallet's first confirmed active material trade minus one block: 我踏马来了, 龙虾, MARSCOIN, 牛来. Wallet 239e actively traded the first two; MARSCOIN shows no token transfer and 牛来 has unverified, external-source inbound only. This is **not an estimate of a general opportunity hit rate**; earlier coin samples predate the wallet's first verified active trade.
4. Wallet 239e's 龙虾 original 21 token-event BNB block-delta sum was **+0.199125593493335144 BNB**. Partitioned by six fully closed token inventory rounds, round one was **+0.196173568640778761 BNB**; the other five netted **+0.002952024852556383 BNB**. This is a scoped native balance observation, not full multi-asset realized PnL.

## Frozen V1 scenario design

Three source-complete historical cohorts were fixed before the new reserve queries: 8e6b token 4 with 2 buy and 17 sell events; 239e 我踏马来了 with 1 buy and 5 sell events; 239e 龙虾 with 7 buy and 14 sell events. Exactly 46 separate original owner self-signed success transactions and inventory-closed owner histories.

Entry quote = historical Pancake V2 getReserves after the original owner transaction block + 1 + latency. Latencies: 0 and 10 blocks. Each original buy triggers a fresh fixed 0.05 or 0.1 BNB buy, subject to a hypothetical initial 1 BNB cash balance. Each original sell triggers selling the same fraction of currently held follower tokens as the original owner sells from its presale inventory, with terminal owner liquidation triggering full follower token closure. Both token directions, quantities and transaction order are sourced from persisted raw ERC20 events.

Fee sensitivity: (a) zero swap fee and zero Gas, (b) hypothetical 0.25% swap fee per buy/sell and fixed hypothetical 0.0005 BNB per modeled transaction. These **are assumptions**, not verified historical route fee quotations. Snapshot-based pool prices are treated as exogenous; simulated purchases/sales do not persistently alter later historical reserves. The replay is an **in-sample reserve-scenario model**, not a proven executable backtest.

Exactly **92/92** original archived block reserve snapshots have been read and stored. The complete 2 latencies x 2 amounts x 2 fee settings x 3 token groups = **24/24** scenario ledger outputs were computed. Independent exact integer QA rechecked **368/368** trade ledger steps over 24 scenarios with **zero cash/token arithmetic failures**. All final follower token inventory was zero and all model accounts remained nonnegative. Five fixed-gas ROI-vs-size warnings are preserved because a fixed fee's percentage burden shrinks at larger size; the corresponding no-gas price-impact checks did not flag inversion. Original QA commit message accidentally referenced 1104 entries; the actual independently reviewed number is **368** and is explicitly corrected in the QA source file.

## Results: hypothetical 0.05 BNB each original buy, 10-block latency

| Wallet / token | Modeled buys | Modeled sells | Total BNB buy outlay | Zero-fee net BNB | Hypothetical fee+Gas net BNB |
|---|---:|---:|---:|---:|---:|
| 8e6b / 4 | 2 | 17 | 0.100000 | +1.341113 | +1.324428 |
| 239e / 我踏马来了 | 1 | 5 | 0.050000 | +0.122411 | +0.118552 |
| 239e / 龙虾 | 7 | 14 | 0.350000 | +0.444836 | +0.430373 |

**These are entirely hypothetical fixed-route model net cash deltas.** The buy outlay is the sum of repeat buys, not one fixed total investment; all owner wallet realized/native figures in this report use different actual transaction sizes and evidence grades. Do not extrapolate these returns to a real follower position.

## Hypothetical episode concentration under same fee+Gas sensitivity

| Wallet / token | Episode | Scenario episode BNB delta |
|---|---:|---:|
| 8e6b / 4 | First | -0.010404 |
| 8e6b / 4 | Second | +1.334832 |
| 239e / 我踏马来了 | Only | +0.118552 |
| 239e / 龙虾 | First | +0.434181 |
| 239e / 龙虾 | Second | +0.007401 |
| 239e / 龙虾 | Third | +0.015197 |
| 239e / 龙虾 | Fourth | -0.007500 |
| 239e / 龙虾 | Fifth | +0.003567 |
| 239e / 龙虾 | Sixth | -0.022472 |

The 龙虾 first episode in 239e's 龙虾 model exceeds the total scenario net gain; remaining episodes net slightly negative. Profit concentration also appears in the separately verified original owner-native cashflow evidence. This does not prove a future edge or winning wallet in the broader BSC universe.

## Evidence grading and blocked production gates

CONFIRMED DIRECT CHAIN: 46 signed successful original owner transactions, associated ERC20 incoming/outgoing quantity histories, 92 original V2 historical reserve snapshots; token 4 exact 19-tx BNB/WBNB settlement and 239e two selected wallet-token signed trade histories.

CONFIRMED BUT NARROW SCOPE: 239e six original 龙虾 round groupings show summed **wallet native block balance changes**, not isolated quote proceeds after all gas and non-native trading flows.

RESEARCH SIMULATION: 24 fixed parameter what-if scenarios, including fee stresses, fully audited arithmetic. This is **not externally reviewed AI code**, live quote execution, persistent-AMM replay, out-of-sample validation or a statistically supported copy-strategy backtest.

UNKNOWN / UNRESOLVED: true market-wide large opportunity denominator, alternate Four.meme pre-V2 execution, routes and pool choice, transfer taxes, live historical gas, delayed follower inclusion feasibility, sandwich/MEV, concurrent follower price impacts, other wallets controlled by the same trader, portfolio-wide negative token cohorts and untreated missed launches.

Decision: keep both 8e6b and 239e in the research queue. The former exhibits broader repeated major-token participation with strongly concentrated actual profits. The latter exhibits two exceptionally early independently signed launches with strongly concentrated first-round profit. **No ranking by generalized win probability is justified yet.**

Next gate: freeze a broad opportunity universe independently of wallet winner history, test 239e's effective participation window and negative/missed outcomes, reconstruct actual venue-by-venue token/quote settlement, and test an executable chronological shadow-order engine on untouched dates. Independent reviewer and deployment acceptance **NOT DONE**. No production monitoring, automation, Gmail, paid RPC, or orders authorized.

## Durable sources

- `BSC_MEME_FOLLOW_V1_MULTIFILL_FROZEN_SPEC_2026-10-11.json`
- `BSC_MEME_FOLLOW_V1_MULTIFILL_HISTORICAL_RESERVE_EVIDENCE_2026-10-11.json`
- `BSC_MEME_FOLLOW_V1_MULTIFILL_SCENARIO_RESULTS_2026-10-11.json`
- `BSC_MEME_FOLLOW_V1_MULTIFILL_INDEPENDENT_LEDGER_QA_2026-10-11.json`
- `BSC_MEME_FOLLOW_V1_EPISODE_PROFIT_CONCENTRATION_2026-10-11.json`
- `BSC_MEME_8E6B_4_ORIGINAL_TWO_EPISODE_EXACT_SETTLEMENT_2026-10-11.json`
- `BSC_MEME_239E_ORIGINAL_LATE_EPISODE_NATIVE_CASHFLOW_CHECK_2026-10-11.json`
- `BSC_MEME_239E_19_CA_ELIGIBLE_OPPORTUNITY_COVERAGE_2026-10-11.json`
- `BSC_MEME_ADDRESS_FOLLOW_LAG_V0_RESEARCH_REPORT_2026-10-11.md`
