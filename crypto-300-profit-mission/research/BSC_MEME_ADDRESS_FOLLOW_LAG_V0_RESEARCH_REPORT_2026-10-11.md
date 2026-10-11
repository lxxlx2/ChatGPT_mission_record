# BSC address follower first-leg V0: frozen historical reserve study (2026-10-11)

State: `RESEARCH_ONLY / IN_SAMPLE / OBSERVE_ONLY / PRODUCTION_TRADING_NO_GO`.

## Evidence and frozen design

- 8 predeclared 8e6b token cohorts, 4 lags (0,10,30,60 blocks) and two fixed sizes (0.05, 0.1 BNB), with 64/64 block reserve snapshots, 64/64 arithmetic rows, eight correct token/WBNB V2 pool identities. Three wallet tokens were explicitly excluded before new reserve queries: MUBARAK, BROCCOLIF3B, BULLA.
- 239e comparator on two overlapping cohorts used identical lag/size assumptions. 16/16 snapshots and 16/16 arithmetic rows. Both sample cohorts were chosen after historical outcome inspection; this is **not** untouched evaluation.
- Snapshot model buys at the **state after the identified original owner's first acquisition block + N**, and sells at the **state after the owner's first outgoing token block + N**. It uses zero-fee x*y=k constant product arithmetic without market-level settlement trace, transfer tax, gas, MEV, route choice, transaction eligibility, or impact persistence. Results are **non-executable upper-bound what-ifs**, not realized PnL, a backtest winner, or trading signals.

## Required causality and liquidity audit

- 8e6b frozen scenarios: 64 raw computations, 10 causally invalid because hypothetical buy block was later than or equal to the owner's actual first-out block, 8 quote-depth warnings, and 50 arithmetic rows remaining after diagnostic masks. Depth diagnostic is post-freeze QA, **not** a frozen pass threshold. Overlaps are counted once in diagnostic remainder.
- 239e comparator scenarios: 16 raw computations, 0 causal invalid and 0 depth warnings.
- **Original frozen scenarios, raw reserves, and raw return numbers are retained verbatim.** No hindsight parameter optimization, no hidden exclusions, no certification of the 50 remaining 8e6b rows as live executable.
- Causal example: Binance Life at 60-block lag returned a mathematical +65.015% (0.05 BNB) but first exit was at block 63454476 while hypothetical buy occurred at 63454487, so this outcome is **INVALID**, not a winner. TUT at lags 30 and 60 is also invalid; SIREN at 30 and 60 additionally has a near-empty pool.

## Same-denomination exploratory first-leg results

Values below are scenario returns **before any fees** for the predeclared 0.05 BNB size. `INVALID` means noncausal; `DEPTH` is non-executable pool depth warning. Reporting complete records is essential, not only winners.

| Wallet / token | 0 blocks | 10 blocks | 30 blocks | 60 blocks |
|---|---:|---:|---:|---:|
| 8e6b / 4 | -21.97% | -31.10% | -21.22% | 11.72% |
| 8e6b / GIGGLE | 344.48% | 271.08% | 313.28% | 276.48% |
| 8e6b / 币安人生 | -49.86% | -36.94% | -29.72% | INVALID |
| 8e6b / SIREN | DEPTH (-100.00%) | DEPTH (-100.00%) | INVALID | INVALID |
| 8e6b / TUT | 45.47% | -7.00% | INVALID | INVALID |
| 8e6b / HAJIMI | 6.17% | 3.09% | -1.09% | -4.01% |
| 8e6b / 龙虾 | 87.91% | 76.48% | 89.99% | 76.55% |
| 8e6b / 我踏马来了 | -24.03% | -7.62% | -5.83% | -11.43% |
| 239e / 我踏马来了 | 234.38% | 251.81% | 147.86% | 110.53% |
| 239e / 龙虾 | 476.76% | 483.10% | 364.50% | 330.65% |

## Cross-wallet timing controls

| Token | 239e vs sampled first V2 transfer | 8e6b vs sampled first V2 transfer | First entry 239e earlier than 8e6b |
|---|---:|---:|---:|
| 我踏马来了 | 0 s | 611130 s | 611130 s |
| 龙虾 | 0 s | 431 s | 431 s |

The near-zero 239e timestamp lag means **same block timestamp** as the first sampled V2 transfer, not guaranteed pretrade access, not proof of control, and not evidence that pool/reference denotes first-ever trade. The two 239e first native inputs were 0.0303 BNB (IFML) and 0.0202 BNB (Lobster), significantly smaller than both hypothetical fixed allocations and 8e6b's major positions.

## Interpretation and blockers

1. 239e deserves an explicit **early-entry-timing** research label on two already selected high-interest coins, while 8e6b has **broader observed repeat participation** across 11 known token contracts. Neither is independently proved universally profitable or live-followable.
2. Three of 11 tokens for 8e6b remain open-inventory; full wallet lifetime, true capital denominator and non-native cashflow attribution are unresolved. Other pool venues/launchpad stages and 23-wallet candidate discovery remain incomplete.
3. To advance beyond this V0, obtain historically executable route quotes including token taxes and true swap fees, simulate signing-observation delay in chronological order across **every owner fill**, classify unrelated transfers, and add loss/abstention controls. The current two-snapshot V0 does not meet that gate.
4. Independent external AI code review and production acceptance have **not** been executed. No automated trade alerts, new tasks, paid RPC, live testing, Gmail or orders were enabled.

## Canonical evidence paths

- `BSC_MEME_8E6B_FOLLOW_LAG_V0_FROZEN_SPEC_2026-10-11.json`
- `BSC_MEME_8E6B_FOLLOW_LAG_V0_POOL_RESERVE_EVIDENCE_2026-10-11.json`
- `BSC_MEME_239E_FOLLOW_LAG_V0_COMPARATOR_FROZEN_SPEC_2026-10-11.json`
- `BSC_MEME_239E_FOLLOW_LAG_V0_COMPARATOR_EVIDENCE_2026-10-11.json`
- `BSC_MEME_8E6B_VS_239E_IFML_LOBSTER_ENTRY_TIMING_2026-10-11.json`
- `BSC_MEME_8E6B_ELEVEN_TOKEN_COHORT_NONOVERLAP_AUDIT_2026-10-11.json`
- `BSC_MEME_239E_TWO_MAJOR_FULL_SIGNED_FLOW_SOURCE_2026-10-11.json`

All reads were through the existing read-only BSC source. No unverified future fill claims.
