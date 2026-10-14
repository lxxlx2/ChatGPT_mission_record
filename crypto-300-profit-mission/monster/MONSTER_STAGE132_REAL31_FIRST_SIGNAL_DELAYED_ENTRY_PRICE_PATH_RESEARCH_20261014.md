# Monster Stage132: original31 first-signal delayed-entry historical price-path research and actual results

Date: 2026-10-14 Asia/Bangkok. Original [Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30). Source is the actual Stage130 historical Binance Data Vision 1m publisher ZIP/CHECKSUM archive, not today's live market. **The original V4 model remains unapproved; this is not an authorized order, actionable signal, actual fill, realized net profit or new OOS.**

## 1. Source, chronology and frozen decision

- Before examining new Stage132 fixed-horizon outcomes, frozen [Stage132 protocol](MONSTER_STAGE132_FROZEN_FIRST_SIGNAL_DELAYED_CLOSE_EXIT_PROXY_PROTOCOL_20261014.md), actual commit `a5e9a0f7905ee232062d3c3ff60755eb746613b2`. All 31 fixed previous Stage130 original symbol/date cases stay in cohort: 19 have one first momentum research signal, 12 no signal. Only the first signal is counted, not 581 repeat positive 3m conditions. Two known VINE/APR gross high2x events are already exposed retrospective historical information and cannot be relabeled new forward.
- Original Stage130 source `stage130_real31.json` SHA256 `a97037bff9d834f0f59fb3a0ae45942a9c28453dbfc0d01331fd78afa49b8f50`, parent 31 source ZIP artifact SHA256 `e1a5931b64497214faa726831cbe1c64e2c93c3cbfd1c2e101af402da816372b`. Full source comes from [Stage130 CI #38566877450](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38566877450). Actual local 31-source rerun and subsequent two-OS CI verified all **147/147** source daily ZIPs against the original per-day publisher SHA and 159,675 original minute bars; the last publisher UTC date can extend beyond original 7-day evaluation window, which must be cropped to the originally frozen anchor end before checking bar count.
- Research code [Stage132 original31 entry/exit proxy](../local-agent/scripts/monster_v4_stage132_delayed_entry_horizon_proxy.py) computes fixed `signal + 1m` entry at that minute OPEN, then exits at the exact OPEN of that instant plus `15m, 60m, 360m, 1440m`; each gross price change is `(exit_open/entry_open - 1)*100`. The one minute after research signal is a hypothetical delay, not an actual order; actual entry and all exits are **unfilled optimistic OHLC proxies**, without bid/ask, depth, spreads, fees, slippage, funding, notional or market impact.
- Within each fixed interval `[entry, exit)` the lowest 1m LOW is used to calculate observed adverse excursion and highest 1m HIGH used only as observed favorable excursion; never implies limit/stop fills or retrospectively chosen exit. No profit-target selection, no manual sale at future HIGH, no threshold changes. If the frozen seven-day source stops before an exit time, record `RIGHT_CENSORED_SOURCE_END`, never a losing or winning trade.

## 2. Observed fixed-horizon original19 research signal price paths

| Zero-cost unfilled-price proxy | 15 minutes | 60 minutes | 6 hours | 24 hours |
| --- | ---: | ---: | ---: | ---: |
| Original31 attempts | 31 | 31 | 31 | 31 |
| First research signals | 19 | 19 | 19 | 19 |
| No research signal | 12 | 12 | 12 | 12 |
| Valid entry+exact exit proxy | **19** | **19** | **19** | **15** |
| Right censored after original 7-day end | 0 | 0 | 0 | **4** |
| Gross price change above zero | **6** | **6** | **5** | **4** |
| Gross price change below zero | 13 | 13 | 13 | 10 |
| Gross price change exactly zero | 0 | 0 | 1 | 1 |
| Median gross return | **-2.5681%** | **-3.9260%** | **-4.8253%** | **-3.2593%** |
| Mean gross return | **-1.9012%** | **-3.3830%** | **-3.6554%** | **-4.3866%** |
| Worst 1m LOW adverse excursion until fixed exit | -15.3675% | -19.2483% | -40.8693% | -69.8493% |

Counts are conditional on source-valid first-signaled symbols and **are not the success rate of all Crypto tokens**, because 31 were selected from historical later-onboard anomalies, later Binance metadata labels COIN/EQUITY/HK_EQUITY have no point-in-time crypto issuer verification, and the first research trigger is a retrospective as-of closed-bar simulation, not documented actual real-time watch.

### Known retrospective 2× examples demonstrate entry and exit gap

| Historical symbol | 15m gross proxy | 1h | 6h | 24h | 24h worst adverse excursion |
| --- | ---: | ---: | ---: | ---: | ---: |
| `VINEUSDT` | +6.8447% | -12.9452% | -23.4973% | +12.5118% | **-49.8775%** |
| `APRUSDT` | -12.0554% | -9.5382% | -20.9780% | +58.7269% | **-40.8693%** |

Stage130 previously established first D0-like research momentum happened before **first future 1m HIGH 2×**, but this result proves that **neither later maximum HIGH nor an early signal entails an accessible 2× sale or even positive fixed-horizon gross change**. For the two known winners, first-hour delayed-entry gross proxy is negative in both cases. Large adverse path changes threaten any strategy using real leverage, latency, fees, or constrained risk budgets. These proxy outcomes do not prove what a real account would have earned or lost.

## 3. Engineering and test evidence; failure preserved

- A standalone original31 [pure offline Stage132 script](../local-agent/scripts/monster_v4_stage132_delayed_entry_horizon_proxy.py) parses the actual Stage130 ZIP archive publisher-receipt data without connecting to current Binance markets. [Six regression tests](../local-agent/scripts/test_monster_v4_stage132_delayed_entry_horizon_proxy.py) cover 1-minute entry delay, fixed exact exit timestamps, changing future bars beyond exit without affecting earlier outcomes, source gap/nonfinite rejection, immutable source SHA gate and real full31 source. No production.
- First [CI #38578392121](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38578392121) **FAILURE**: relative `MONSTER_STAGE130_SOURCE_ROOT` was resolved inside the nested `local-agent/scripts` test cwd; source had been downloaded, but the real-source test could not open `stage130_real31.json`. This was a CI source-path wiring error; original on-disk independent full31 local calculation had been done, but initial CI cannot count as a pass.
- Patched the workflow to absolute `github.workspace/stage130_original`, no source substitution, no strategy or price formula change. Retest [CI #38578529492](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38578529492) succeeded: macOS job `115901937437` and Ubuntu job `115901938324` both `success`; two original source sets each verify 147 publisher ZIP SHA and original 159,675 minutes, full per-case replay, synthetic invariants and a full snapshot. Both machine stdout summaries match **all summary fields exactly**, and match the independent local historical replay.
- Permanent [Stage132 machine summary](evidence/monster_stage132_original31_delayed_entry_fixed_horizon_machine_summary_20261014.json) includes frozen source hashes, full provenance, all horizon counts, exact unrounded summary values, and failed/successful CI IDs. Full 31-row machine outputs reside in [successful CI artifacts](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38578529492) with 30-day retention; generated from original publisher ZIPs with committed code. Do not falsely describe those large ZIPs or full derived row artifacts as permanently stored Git blobs.

## 4. Business conclusion and next work

The available **exposed historical cohort does not support the hypothesis that the existing Stage130 first-momentum event reliably delivers positive fixed-horizon gross price changes**. It also fails actual executable-net validation by construction. Even the relatively generous zero-cost open-price assumptions produce negative medians and negative means at all four frozen horizons. **Do not promote Stage130 as BUY or pass G4**, and do not tune its 5%/8%/15% trigger thresholds using these same 31 historical outcomes.

The next decisive tasks are:
1. Secure genuinely new and authenticated point-in-time full-market crypto-only population, including arriving and halting/delisted contracts and no-WATCH negatives, with an independent pre-registered multi-window holdout. Original 2026-10-14 06:00 UTC forward source failure cannot be replaced. User requested manual snapshots on demand, which cannot retroactively provide minute-level production alert timing.
2. Any new entry/exit strategy must be *frozen before* new independent outcomes. Per Stage77 require G1/2/3 independently achieved; actual G4 requires at least 30 independent paired **tradeable** as-of bid/ask depth + fees + exits and user-specified notional, not an invented 30U or 300U investment.
3. Obtain actual independent other-AI review output for completed candidate and code; no review or Mac deployment authorization yet. No new manual market snapshot created in Stage132, no schedule, Frank/Gmail/auto trade unchanged.

`STAGE132_SOURCE31=VERIFIED`; `STAGE132_2OS_ACTUAL_FULL_REPLAY=PASS`; `STAGE132_FIXED_HORIZON_MEDIAN_GROSS=NEGATIVE_ALL_4`; `G0=PARTIAL`; `G1_NEW_OOS=NOT_SCORABLE`; `G2_G3=NOT_PASSED`; `G4_ACTUAL_NET=UNKNOWN`; `G5_OTHER_AI_REVIEW=NOT_DONE`; `G6_MONSTER_DEPLOY=NO_GO`; `FRANK=UNCHANGED`; `NO_NEW_AUTOMATION`.
