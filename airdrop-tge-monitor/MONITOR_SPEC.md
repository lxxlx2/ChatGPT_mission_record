# Airdrop / TGE Monitor Spec

Updated: 2026-09-26
Timezone: Asia/Bangkok

## 目标

提高真实执行率。取消“每小时穷尽完整白名单”的不可持续要求，改为 urgent + shard。

## 每小时 :14

读取：
- `REGISTRY.md`
- `state/current.md`
- `README.md`
- 最近 24h event / run 用于 dedupe

执行：
1. 立即创建唯一秒级时间戳的 skeleton run audit，`run_status: in_progress`。
2. 检查 always-hourly urgent set。
3. 检查当前 hour 对应 shard。
4. 跟随官方公告中的 action links 到最终页面。
5. identity gate + two-anchor。
6. 判断是否出现新 ACTION event。
7. 重新读取 state/current.md 最新 SHA 后更新状态。
8. finalize 同一个 run audit。

不得等完整扫描结束后才第一次写 GitHub。单一项目失败继续其余项目。

完整 registry 四小时覆盖一次。

## Event notification

只有新的、官方证据确认、会影响用户资格/权益/截止时间的 ACTION 才通知。

允许：
checker, registration, snapshot, wallet linking, KYC, form/signature,
allowlist, allocation, investor distribution, claim open/close,
规则/资格实质变化, TGE 前后必须步骤, token delivery。

ACTION：
- Gmail + ChatGPT；
- Gmail subject: `[空投/TGE提醒][项目][事件]`；
- event archive 写入 `reports/events/`。

NO_ACTION：
- 用户完全静默；
- 仍写 run audit。

## Identity / Hard fail

沿用 README 的 canonical identity、two-anchor 与 Space/Spacecoin 回归规则。
身份冲突不得为了“发提醒”而降级门槛。

## 每日汇总

每天第一次 Asia/Bangkok 00:00 后的运行：
- 汇总前一自然日真实存在的 run files；
- 生成 `reports/daily/YYYY/YYYY-MM/YYYY-MM-DD.md`；
- 不伪造缺失 run；
- daily summary 只上 GitHub，不发 Gmail/ChatGPT。

历史完整性回填只放在 daily summary 阶段或专门 repair，不再占用每小时关键路径。

## Run audit

每轮必须写：
`runs/YYYY-MM-DD/HHMMSS.md`

最低字段：
- run_time
- automation_id
- run_status
- urgent_checked
- shard_index
- shard_projects_checked
- candidate_count
- triggered_events
- identity_failures
- source_failures
- gmail_attempted/sent/error
- event_paths
- daily_summary_attempted/status
- github_write_status

如果一个项目 source 失败：
- 记录项目级 failure；
- 继续其余项目；
- 只有整轮无法完成 urgent + shard 才标 failed。

## Health

state/current.md 维护：
- last_run
- last_success
- last_shard_0..3
- consecutive_failures
- daily_summary_last_date
- open_urgent_events

同一 shard 超过 6 小时未成功覆盖，在下一轮记录 HEALTH_GAP，并通知用户一次。


## Scheduler proof

- scheduler trigger 不能替代 GitHub run audit。
- 自动运行只有在 skeleton audit 已创建、urgent+shard 有 checked/failed 状态、state/current.md 更新或明确记录更新失败、同一个 audit 被 finalise 后才算 success。
- GitHub/单一来源/Gmail 临时失败绝不允许自动 disable 或 pause 本 automation。


## Source-result classification

Do not confuse “no new official event found” with a source failure.

Per project, classify as:
- `checked_no_update`: official/search sources were reachable/queryable and no new ACTION evidence was found;
- `checked_action`: new official ACTION evidence passed identity/action gates;
- `source_unavailable`: an actual tool/request/access error prevented meaningful checking;
- `identity_fail`: evidence existed but canonical identity could not be safely resolved.

Only `source_unavailable` counts toward source_failures or partial_failure. A normal no-result / no-update check is healthy and must not downgrade the run.
