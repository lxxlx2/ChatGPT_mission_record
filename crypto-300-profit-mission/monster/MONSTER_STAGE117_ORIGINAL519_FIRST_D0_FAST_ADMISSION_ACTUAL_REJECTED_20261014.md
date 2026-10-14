# Monster Stage117: first-D0 fast admission rejected on actual original519 source

Date: 2026-10-14 Asia/Bangkok. **Actual tested model result: `REJECTED_HISTORICAL_G2_28_EARLY_RECALL`**. Research-only original Monster Draft PR #30. This is not a strategy fitted to be profitable, not independently reviewed, not live and not an additional Monster monitor.

## Hypothesis was frozen before backtest

- At Git SHA `b02365f4e61372d02273e1176124ce7a9cac9edc`, `MONSTER_STAGE117_FROZEN_FIRST_D0_FAST_ADMISSION_V1_20261014.md` locked one new admission rule: look ONLY at as-of first D0, with exactly the unchanged Stage79 `entry_first` gate (ret60 >=8%, quote15 >=1m USDT, trades15 >=10,000, normalized quote15 against prior45 >=1.3). No 48h late-reignition wait. Preserve all D0 raw WATCH. **No thresholds tuned afterwards.**
- Core: `../local-agent/scripts/monster_v4_stage117_first_d0_fast_attention_core.py`; historical Stage64+83 all519 source lock audit: `../local-agent/scripts/monster_v4_stage117_original519_first_d0_audit.py`; original Stage116 official nine-day replay adapter imports exact Stage117 candidate core without changing frozen original V4/Stage79 D1 output. All new code remains research only.
- Immutable full source input: original Stage64 519 as-of only official publisher-SHA-checked 61 closed 1m observations Git blob `8ebe53acfdfe10413ac1e6f03457d6ace25d9d5a`; original Stage83 full519 D1/2x evaluation-only labels Git blob `c76b3a137c8dbe56feed3a79a63adcc0752f5e2e`. Source and historic 2x are disjoint input/output roles; future 2x is never an admission feature.
- Machine result: `evidence/monster_stage117_frozen_first_D0_original519_actual_summary.json` Git blob `67c93d28a8f748ae2337b22f536839df0f8e748b`; exact 519 decisions also archived at `evidence/monster_stage117_frozen_first_D0_original519_actual_rows.jsonl`. No historical source price or candidate suppressed.
- Final exact code/CI validation: [Stage117 run #38504020737](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38504020737), `success`, cross-platform macOS/Ubuntu original D0 pure causal unit suite, Stage116 replay adapter selftest, original Stage80 regression, followed by Git-blob-locked real original519 audit and explicit `REJECTED` status assertion. The CI success proves calculations ran; it **does not** mean the strategy passed.

## Original historical decision and rejection

| Historical finding | Actual observed | Existing frozen gate |
| --- | ---: | --- |
| Original D0 population | 519 | Preserve 519 |
| Previously historical original first D1 | 305 | Comparison only |
| New Stage117 first-D0 fast attention | 164 | No minimum |
| Raw attention per UTC06 calendar day / all42 days | 3.904762 | <=5 |
| Worst full day attention | 10 | <=12 |
| Original D0 events early >=5m before first 2x | 28 | Denominator 28 |
| Stage117 fast attention also early >=5m before 2x | **17** | Need >=23 of 28 to pass 80% |
| Original G2 candidate retention | **60.714%** | >=80% |

**G3 historical raw load proxy passes, G2 fails.** In six exposed historic anchor windows this first-D0 candidate missed 11 of 28 original important early-2x signals and performs WORSE on early-2x retention than Stage111 rejected delayed priority (19/28). No claims of crypto-only executable net, OOS or opportunity profitability are possible.

## EXACT eleven losses / cause (as-of first D0, known historical 2x only for post-hoc evaluation)

| Historic symbol | Original Stage79 first-D0 admission field(s) that failed |
| --- | --- |
| MYXUSDT | 60m return |
| AIAUSDT | 60m return |
| ALCHUSDT | 60m return; 15m quote; 15m trades |
| BROCCOLI714USDT | 15m trades |
| DOODUSDT | 15m quote |
| SOONUSDT | 60m return |
| VELVETUSDT | 60m return |
| 1000RATSUSDT | 15m quote |
| BEATUSDT | 60m return; normalized 15m volume |
| KOMAUSDT | 15m quote; 15m trades |
| MMTUSDT | 60m return; 15m quote; 15m trades |

The eleven missing early positives have **seven** failures involving the 60m price momentum requirement, five involving absolute quote15 turnover, four involving trade15, one involving relative normalized quote15 (categories overlap). These are authentic as-of feature values, with non-overlapping original event evidence and no future labels used by the model. This points to a **structural** tension: strict pre-D0 volume/momentum filters suppress early discoveries before major price increases, but emitting every D0 also breaches attention burden and has unstable price economics (Stage115). Do not retrospectively lower thresholds in this same known 519 until it passes.

## Next highest-value strategy step (not a report-count target)

One genuinely different fast valuation hypothesis can be specified **before consuming any genuine new 7-day source**: preserve full D0 with no top-N quota, distinguish as-of unusual volume / order-flow from the requirement that prices already rise >=8% over 60min, then require positively confirmed point-in-time crypto listing/market D2 and real book / fee / notional before any actionable signal. This needs a novel candidate frozen in advance, causal implementation, honest unchanged historical baseline, then new three-window forward OOS full-universe replay. Ordinary D0 controls and missed historical 2x must remain visible. No new date or threshold tuning based on 11 known losers.

`STAGE117_HISTORICAL_AUDIT=DONE`; `STAGE117_FAST_CANDIDATE=REJECTED`; `STAGE116_FORWARD_SCORER=CODE_AND_SYNTHETIC_CI_PASS`; `NEW_GENUINE_OOS=NOT_DONE`; `CRYPTO_IDENTITY_SCOPE=PARTIAL`; `REAL_EXECUTABLE_NET=UNKNOWN`; `NEW_MODEL_OTHER_AI_REVIEW=NOT_DONE`; `MONSTER_DEPLOYMENT=NO_GO`; `FRANK=UNCHANGED`; `STAGE99_INSTALLED_ONESHOT_NOT_MODIFIED`; `GMAIL=OFF`; `NO_AUTOTRADE`; `NO_NEW_SCHEDULERS`.

The already explicitly authorized Stage99 one-shot Mac collector is the only existing scheduled research source. Stage117 added no Mac instructions and no shadow deployment. Production changes still require all gates and separate consent.
