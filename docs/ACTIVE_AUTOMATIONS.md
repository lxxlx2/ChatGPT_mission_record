# Mission 自动化任务现状及原始调度对账（2026-10-18）

Updated: 2026-10-18 Asia/Bangkok
Status: `READ_ONLY_TASK_CONFIG_SNAPSHOT / DELIVERY_HEALTH_NOT_PROVEN`
Timezone: Asia/Bangkok

This is a human-facing **configuration snapshot**, obtained by reading existing ChatGPT task IDs, enabled flags and iCal schedules on 2026-10-18. It is not a scheduler or monitoring health receipt. The original task configuration and each module's current `AUTOMATION_RUNTIME.md` take precedence if newer. Historical :00 / :14 / :29 lists from 2026-09-26 have been superseded. **No automation was created, resumed, renamed, disabled, deleted or rescheduled in this documentation correction.**

## Existing active scheduled tasks

| Task | Existing ID | Enabled | Effective Asia/Bangkok execution times | Functional authority |
| --- | --- | --- | --- | --- |
| Crypto 每日情报 | `6a8600b9d12481919bc43ebc800c9916` | **true** | **00:20, 03:20, 06:20, 08:20, 09:20, 10:20, 11:20, 12:20, 16:20, 20:20** every day | [Crypto runtime](../crypto-daily/AUTOMATION_RUNTIME.md); ordinary source collection 00/03/06/12/16/20, prebuild 08, formal delivery 09, conditional recovery 10/11 |
| 美股每日晨报 | `6a8600c16e7081919566f170f58045a6` | **true** | **05:40, 06:40, 07:40, 08:40** every day | [US Stock runtime](../us-stock-daily/AUTOMATION_RUNTIME.md); prebuild/repair/formal send/conditional recovery respectively |
| 全项目空投与TGE监控 | `6a85fff710e0819190ffcf8c1145a170` | **true** | **HH:00** every hour (24 daily) | [TGE runtime](../airdrop-tge-monitor/AUTOMATION_RUNTIME.md); always-hourly urgent set + one deep registry shard, stable event-key dedupe, only verified material ACTION notifies |

The execution time is confirmed from the **existing task configuration**, and matches the current October 10 overrides in the Crypto Daily and TGE runtime documents. Enabled means scheduling is configured; it does **not** establish successful invocation, complete source coverage or Gmail delivery.

## Explicitly disabled or paused existing tasks

| Task | Existing ID | Observed task state / scope |
| --- | --- | --- |
| `$300-3000` | `6ac0826c02408191b70d206098702ff2` | **disabled**. Umbrella Mission GPT task paused; independent Frank local deterministic runtime is not this task |
| `$300 Crypto资产状态监控` | `6ab46906a0cc8191880f1922dbef954a` | **disabled**. Historical :29 and embedded Monster descriptions are legacy, not an operating price/Monster monitor |
| `Crypto 09:00 日报发布` | `6ab7240960f08191aab9a24996bd58b2` | **disabled**; original Crypto Daily handles its own conditional 10:20/11:20 recovery |
| `Monster 445 采集验收` | `6ad1e1a0bb8481919bcc2fc3b8cb3b2b` | **disabled**, research collection acceptance only, not a live production alert |
| `Monster 原始市场快照采集` | `6acd6f4bbf4c8191944fcee26c6f4965` | **disabled**, no future scheduled snapshots authorized by this document |
| `Frank 30D 全量回测` | `6abb7938e00481919a4ca1cab1d2acb9` | **disabled**, historical backtest only |
| `妖币每日汇总` | `6ab6c5c461dc819182a31f8669b8b2f3` | **disabled**; the old embedded Monster V2.1 reference is historical, not evidence of an active lane |
| `Crypto 日报滚动素材池` | `6ab0b7a02d448191a469742b8dea7229` | **disabled** |
| `历史报告回填修复` | `6a9950d2178881919ae04e7c954479b2` | **disabled** |
| `ETH期权到期交易检查` | `6ab4691385a48191898834e806c697da` | **disabled** |

Other unrelated account tasks are outside Mission registry scope and have not been edited. Disabled tasks are intentionally kept for audit, not recreated, cleaned up or reenabled.

## Health and notification evidence

- [Issue #4](https://github.com/lxxlx2/ChatGPT_mission_record/issues/4) Crypto Daily: `DEGRADED / AUTO_DELIVERY_UNVERIFIED`. 2026-10-17 corrected formal report was manually recovered with Gmail Sent; 2026-10-18 early collector final remains `PARTIAL`.
- [Issue #5](https://github.com/lxxlx2/ChatGPT_mission_record/issues/5) US Stock: latest 2026-10-17 formal report was manually recovered with Gmail Sent; original scheduled send reliability remains unverified.
- [Issue #6](https://github.com/lxxlx2/ChatGPT_mission_record/issues/6) TGE: `DEGRADED_PARTIAL`; latest 2026-10-18 early final is partial with source gaps; last full-success reference in `state/current.md` remains 2026-10-10. With no newly verified actionable rights delta, silence is expected; a failed official source cannot count as full coverage.
- Source records: [2026-10-16 investigation](MONITORING/2026-10-16-three-monitor-root-cause-repair.md), [2026-10-17 recovery](MONITORING/2026-10-17-three-monitor-delivery-recovery.md), [history triage ledger](mission-historical-pr-issue-triage-2026-10-18.md).

## Completion and continuity constraints

- A scheduler's `last_run_time` means it triggered, not that a required report was produced. Required terminal audit: `runs/YYYY-MM-DD/HHMMSS-final.md` or durable `HHMMSS-final-retry.md`. A `*-attempt.md` or legacy `*-start.md` alone is not completion.
- Gmail delivery success requires a real Sent ID with recipient/subject/body readback; Git archive write success alone cannot prove email delivery.
- Source failures must retain `PARTIAL` / `UNVERIFIED` and can never be turned into fabricated `HEALTHY`, a zero wallet balance, or an invented token event.
- Read and repair the **original** automation on root failure. Do not create fallback copies, widen scopes, alter recipients, enable paused monitors or modify production software in order to tidy documentation.
- This file is a proposed documentation change on **Draft PR #99**, not an applied main-branch task-control rule until reviewed and merged.
