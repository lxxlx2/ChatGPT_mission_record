# Monster Stage124 — manual-only cadence, real 927-market source audit, next manual comparison ready

Date: 2026-10-14 Asia/Bangkok. Original Monster Draft [PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30). This is a user-authorized change of research **capture operation**, not trading-strategy acceptance or permission to deploy.

## Long-term instruction saved and approved scope

User: "**给我个命令把采集任务停了，到时间我会记得让你采集的，你也把采集任务和时间写到这个模块的开发节奏里，后续对话直接采集**". The exact three-label bootout / registry-verification / plist-removal zsh command is in [manual cadence](MONSTER_MANUAL_COLLECTION_AND_DEVELOPMENT_CADENCE_20261014.md), and the same manual-first rule is cross-linked in `MONSTER_MODULE_DEVELOPMENT_RULES.md` and `AGENTS.md`. **DO NOT assume this Mac local action already completed**: command delivered, user execution and result still unknown.

Future user-requested checkpoints, Asia/Bangkok: **2026-10-28 13:00** and **2026-11-11 13:00** (original 06:00 UTC Stage105 experiment timestamps). These are suggested times for the user to message, NOT scheduled automation or an enforced data source clock. On a request in any future chat, immediately query the currently available public Binance USD-M connected market endpoints, save full market data to PR30 with **actual observation timestamps**, analyze, re-read archive, and report, without asking the user to execute a local collection script. Existing 2026-10-14 06:00Z `SOURCE_FAILED_NO_BACKFILL` stays as a failed *old* frozen source; the user's new successful 2026-10-14 09:48:24.840Z Stage123 snapshot remains a separate *new exploratory T0*.

No new launchd, ChatGPT automation, GitHub scheduled CI, cron, Gmail, automatic trading, Frank modification or Mac deployment is authorized.

## Genuine Stage123 source inputs and Stage124 offline repeatability

Actual full original market evidence is [Stage123 eight-file manifest](evidence/monster_stage123_20261014T094824Z_manifest.json), with all original five segmented exchangeInfo chunks, full 24h ticker, BBO ticker and mark-price files and a genuine source-time label. Stage124 independent source-quality and market distribution code `../local-agent/scripts/monster_v4_stage124_manual_snapshot_comparison.py` reads **all eight** from the original Git checkout, no internet requests and no model threshold adjustment; its exact verified output is [Stage124 actual full-market audit](evidence/monster_stage124_20261014T094824Z_actual_full_market_audit.json), Git blob `93aefbb2ad68d79284e596e456b1a04ac052818e`.

| Verified input/measure | Actual real source count |
| --- | ---: |
| exchangeInfo complete all-contract universe | **927** |
| TRADING + PERPETUAL + USDT | **525** |
| Complete rolling 24h ticker, BBO, mark within this active cohort | **525 / 525 / 525** |
| Active 24h gain / loss / no change | **161 / 363 / 1** |
| Active gains >=10% / >=20% | **9 / 5** |
| Active losses <=-10% | **13** |
| Active BBO spread bps median / p25 / p75 | **3.8647 / 2.0016 / 5.9471** |
| Source timestamps among active feeds older than 60 minutes | **0** |
| Non-ASCII exact Binance symbols retained | **5** |

There are 951 active-feed timestamps after the recorded batch median by up to approximately 1.2 seconds; **the four API feeds are not simultaneous**, and the report explicitly describes these harmless non-atomic timing differences rather than pretending they were captured in one matching exchange tick.

Old original Stage118 historical fast buy candidate `REJECTED`, G0 independently proven crypto/contract unit `PARTIAL`, real G4 executable net `UNKNOWN`, G1–G3 OOS `NOT_SCORED`. A 24h rolling price movement from Stage123 cannot be a 7-day forward label.

## Tested and reproducible

- Dedicated [Stage124 source audit CI #38548045731](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38548045731): **success**, Ubuntu+macOS selftest and real 8-file market readback 927/525, with one genuine earlier failed run [#38547891418](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38547891418) caused by misinterpreting manifest length as excluding the trailing newline; the producer recorded inclusive length. Corrected the one source decoding expression; did not modify original market data or thresholds.
- Already-existing canonical pre-T1 single-model manual **forward comparison** code `../local-agent/scripts/monster_v4_stage124_manual_snapshot_forward_compare.py` was separately tested in [Stage124 manual comparison CI #38547672796](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38547672796), also success. Its associated [frozen T0/T1 protocol](MONSTER_STAGE124_FROZEN_MANUAL_MARKET_TWO_SNAPSHOT_FORWARD_COMPARISON_PROTOCOL_20261014.md) was written before the next actual user-requested T1. **Use THAT frozen comparator for actual T0→T1 endpoint forward price proxies; use the newly added distribution audit for single-batch QA.** Never run multiple result definitions and select a more favorable one.
- No actual future T1 has been requested/obtained. Synthetic future test is not OOS. The immutable 525-case T0 can be compared to a future user-requested manual T1, but a pair of snapshots alone CANNOT measure the first 1m 2x event or causal original V4 D0/D1 recall.

## Work status and next actions

`MANUAL_CADENCE_SAVED_ACROSS_CHATS=DONE`;
`MAC_STAGE99_STOP_COMMAND_PROVIDED=YES`;
`MAC_STAGE99_ACTUAL_STOP_VERIFIED=NO_USER_OUTPUT_YET`;
`T0_REAL_927_525_MARKET_ARCHIVED_AND_REPRODUCED=DONE`;
`T1_NEXT_USER_REQUESTED=NOT_YET`;
`OOS_G1_G2_G3=NOT_DONE`;
`STAGE118_STRATEGY=REJECTED`;
`G0_CRYPTO_ASOF_PARTIAL`;
`G4_ACTUAL_NET_UNKNOWN`;
`INDEPENDENT_OTHER_AI_REVIEW_NOT_DONE`;
`MONSTER_DEPLOYMENT_NO_GO`;
`NO_NEW_AUTOMATIC_TASKS`;
`FRANK_UNCHANGED`.
