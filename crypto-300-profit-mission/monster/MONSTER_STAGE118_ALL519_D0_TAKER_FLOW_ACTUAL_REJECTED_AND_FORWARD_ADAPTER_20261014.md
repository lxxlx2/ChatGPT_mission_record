# Monster Stage118 — verified first-D0 price OR taker-buy flow model: rejected on exposed 519

Date: 2026-10-14 Asia/Bangkok. Mission Monster existing Draft PR #30 only. **`STAGE118_V1=REJECTED_HISTORICAL_EARLY_2X_RECALL`**. No live installed monitor, no production trade, no real Gmail or alteration to Frank and the previously approved Stage99 three one-shot Mac captures.

## 1. Frozen-before-test facts

- New single price-or-flow attention hypothesis froze at commit `43f66103f84372d1b62feeeb8d6d4425285362bc`, `MONSTER_STAGE118_FROZEN_D0_FLOW_IMBALANCE_TWO_LANE_CANDIDATE_20261014.md`.
- PRICE lane = unchanged Stage117/Stage79 first D0 ret60 >=8%, quote15 >=1m USDT, trades15 >=10k, quote15 normalized prev45 >=1.3; exact original Stage79 contract Git blob `292e0cefe2089214dbde48ee50d6baf6cf590f8e`.
- FLOW lane = SAME D0 timestamp, unchanged quote/trade/acceleration minimums but NO ret60 threshold; actual Binance USD-M buyer-taker quote share last15 >=55%, and share last15 minus last60 >=3 percentage points. Both lanes together count ONE attention ID, not two.
- Source locked ORIGINAL full519 Stage64 61 past CLOSED 1m including taker quote amount `8ebe53acfdfe10413ac1e6f03457d6ace25d9d5a`; immutable Stage83 28 original early5 GT2 evaluation cases `c76b3a137c8dbe56feed3a79a63adcc0752f5e2e`; original Stage114 real minute D0 postprice results `de64a09ff4f8b35009fd1ff71a284542fd5de5ac`.
- Real source outcome machine files `monster/evidence/monster_stage118_first_D0_flow_full519_actual_summary.json` and `monster_stage118_first_D0_flow_full519_actual_rows.jsonl`. Summary Git blob `f469a4b2b50a6746cd3da295060754990cb6affe`.

## 2. Actual source-locked cohort result

| Prespecified measure | Previous Stage117 | Frozen Stage118 | Gate |
|---|---:|---:|---:|
| Original D0 | 519 | 519 | Preserve full cohort |
| Attention events | 164 | 183 | No hard quota |
| New flow-only events | — | 19 | Not proof of value |
| Qualifying on both price & flow | — | 8 | Deduplicated |
| Historical original D0 early5 GT2 | 28 | 28 | Full prior denominator |
| New candidate admitted among those 28 | 17 | **18** | Need >=23 (=80%) |
| Mean attention / original 42 full UTC06 days | 3.9048 | 4.3571 | <=5 |
| Peak daily attention | 10 | 10 | <=12 |
| Price-only gross 5m median on new attention | — | **-0.676590%** (183/183) | Real net not proven |
| Price-only gross 24h median on new attention | — | **-3.919125%** (161/183; 22 source-censored) | Real net not proven |
| Synthetic 20bps on each side 24h median | — | -4.302681% | NOT actual fees/fills |

G3 raw attention load condition PASSES, but G2 major early2x recall **FAILS** at 18/28 (64.29%). Therefore Stage118 is **REJECTED** regardless of any apparent profitable subtype.

FLOW-only added 19 new events, **one** further historical early 2x opportunity, MYXUSDT. The ten remaining missed original early2x opportunities include AIA, ALCH, BROCCOLI714, DOOD, SOON, VELVET, 1000RATS, BEAT, KOMA and MMT. Do NOT choose a threshold on these named successes or missed cases.

## 3. The attractive 19-case subtype is NOT a model PASS

- 19 FLOW-only events with complete 24h price proxy: median gross **+5.572254%**, 13/19 positive, but predeclared 5-minute price proxy median **-1.275847%** and actual spreads/depth/executions UNKNOWN.
- Only 19 observations distributed unevenly across the six exposed windows. 2025-01-30 has 6/6 positive (median +16.52%); 2025-08-01 has only TWO complete outcomes with an extreme +102.82% median. 2025-10-02 contains only ONE FLOW-only event (negative). Tiny samples and date-level dependence prohibit treating the subgroup as OOS or a robust profit strategy.
- Original PRICE-only 156 events: 134 complete 24h price proxies; gross 24h median -5.095203%. BOTH 8 events: gross 24h median -5.370535%. Buying every D0 is still disallowed by Stage115's five negative date medians and missing execution evidence.
- Raw Stage118 event decisions, positive/negative/censored outcomes and original symbol/date identity are preserved in exact Git JSONL, not postfiltered to a winning subgroup.

## 4. Forward research adapter implemented and verified independently

- Pure shared Stage118 rule: `local-agent/scripts/monster_v4_stage118_first_d0_dual_lane_flow_core.py`. Two-lane decision uses Stage64's exact official as-of math with never any future label.
- Stage118 519 source/price/42day replay: `local-agent/scripts/monster_v4_stage118_full519_taker_flow_backtest.py`.
- **Actual future official minute adapter** `local-agent/scripts/monster_v4_stage118_asof_taker_proof_adapter.py` reads genuine Binance USD-M column 10 `taker_buy_quote_asset_volume` via existing Stage56 official ZIP + CHECKSUM parser, for 61 CLOSED minutes before D0. It compares every day ZIP SHA to the exact same Stage91 original 9-day official minute source SHA receipt, and all 61 minute close/quote/trade values to the Stage116 replay's already verified candles. SHA mismatch, price/quote/trade mismatch or post-time data cannot produce valid fast attention. Ordinary second retrieval 404 returns explicit `SOURCE_UNKNOWN_RETAIN_D0`, not a false negative.
- Existing `monster_v4_stage116_one_shot_forward_replay.py` now attaches Stage118 as an **additional immutable research result**, never replacing original V4 D0 or frozen D1, and checks the Stage117 price lane's exact match in prospective replay. It does not initiate a source capture without an existing authorised snapshot.
- [CI run #38505836010](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38505836010): Ubuntu and macOS causal selftests + original locked 519 research replay SUCCESS at exact tested workflow head `7cdb09236f4309056c6b127cdd5ef476bd22a904`. Earlier original519 workflow [#38505569021](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38505569021) also SUCCESS. **CI passes mean code ran correctly; the model failed historically.**

## 5. What is worth doing next (not a threshold-tuning loop)

This line of repeated increasingly tight post-D0 signal filters has failed on its real research recall and/or price economics. Preserve raw D0 for early discovery; separate watch attention from executable buy. Research should now focus on **point-in-time verified crypto/contract identity and as-of venue/book/fee/exit evidence** for the full normal cohort, independent of any new signal threshold, and on actually complete new future windows with original Stage105 frozen three dates. A new strategy should not be selected merely because 19 retrospective flow-only symbols have attractive gross 24h returns.

`STAGE118_HISTORIC_REPLAY=DONE`; `STAGE118_CORE_AND_STAGE116_ADAPTER=DONE`; `STAGE118_REAL_HISTORIC_STRATEGY=REJECTED`; `STAGE118_NEW_3_WINDOW_FORWARD_OOS=NOT_DONE`; `G0_CRYPTO_ASOF_VERIFICATION=PARTIAL`; `G4_ACTUAL_EXECUTABLE_NET=UNKNOWN`; `INDEPENDENT_OTHER_AI_CODE_REVIEW=NOT_DONE`; `MONSTER_LOCAL_DEPLOYMENT=NO_GO`; `TRADING=NO_GO`; `GMAIL=OFF`; `FRANK=UNCHANGED`; `EXISTING_STAGE99_MAC_CAPTURE=UNCHANGED`; `NEW_SCHEDULED_MONITOR=NONE`.
