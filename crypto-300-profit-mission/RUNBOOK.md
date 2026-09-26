# Crypto Profit Mission Runbook

Updated: 2026-09-26
Timezone: Asia/Bangkok

MISSION_SPEC.md 保留策略、资金与仓位权威。本文件只定义每小时运行合同，减少 scheduler prompt 负载。

## Schedule

每小时 :29。

## Start-of-run

**第一项持久化动作必须先写 skeleton audit，再做重研究。**

1. 只获取当前 Asia/Bangkok 时间并创建唯一 `runs/YYYY-MM-DD/HHMMSS.md`，初始 `run_status: in_progress`。
2. skeleton 成功后再读执行文件。

必读：
1. MISSION_SPEC.md
2. state/latest.md
3. health/current.md
4. portfolio/current.md
5. performance/current.md
6. active positions
7. active watchlists

若单个非关键文件读取失败，继续其余 lane，并记 partial_failure。

## Mandatory fast lanes

- wallet/gas delta
- PONS
- XRP/Variational
- ETH conditional
- BTC regime
- JUMP
- launch/NFT radar
- active-position security
- monster squeeze V2.1
- Robinhood/FOMO execution flow

## Monster V2.1

已经合并，不存在独立执行任务。

每小时：
- Binance Alpha universe
- Binance USDⓈ-M Futures universe
- 7-day carried candidates
- frozen STRUCTURAL → PRESSURE → IGNITION → EXHAUSTION

首次 IGNITION：Gmail + ChatGPT。
相关 EXHAUSTION：按 watchlist 规则。
19:29：固定用户可见日汇总。

## Opportunity

- ACTION：Gmail + ChatGPT。
- WATCH：Gmail + ChatGPT。
- unchanged WATCH：静默。
- rejected/noise：静默。

## Health

每轮必须更新 health/current.md 和 state/latest.md，并创建 run audit。

如果 scheduler 上次“有触发”但 GitHub 没有对应 audit：
- 记为 missing_audit；
- 不把 scheduler trigger 当 success。

成功 run 间隔 > 90 分钟：
- 恢复时发送一次 MONITOR_HEALTH_GAP。

相同 mandatory lane 连续两轮失败：
- 发送 MONITOR_LANE_FAILURE。

## GitHub write strategy

先写最小 run audit，再写 state/health 的完整更新，避免整轮完成研究后没有任何 heartbeat。

推荐顺序：
1. create skeleton audit: run_status=in_progress，必须发生在完整文件读取、市场搜索和所有重 lane 之前
2. read RUNBOOK/MISSION_SPEC/current files
3. execute lanes
4. update state/latest
5. update health/current
6. finalize same run audit status

若最终 update 失败，至少 skeleton audit 能证明 scheduler 确实启动过。

## Success

只有：
- mandatory lanes 有明确 checked/failed 状态；
- state/health 更新成功；
- run audit 最终完成；
才允许 success。

其它情况使用 partial_success / partial_failure / failed。


## Scheduler side-effect execution contract

The hourly Mission scheduler is explicitly authorized to use the already-connected GitHub and Gmail connectors for the persistent side effects defined by this runbook. Do not ask for interactive confirmation for these recurring audit writes or for alert emails that already satisfy MISSION_SPEC notification gates.

Use a fixed hourly exact schedule. Signal conditions control notification only; they do not control whether the hourly run executes.

GitHub write protocol:
1. Immediately after start-of-run reads, create a minimal skeleton audit with a unique second-level timestamp and `run_status: in_progress`.
2. Use GitHub contents API connector actions directly for normal file writes.
3. Before replacing `state/latest.md` or `health/current.md`, fetch the file in the same run and use that returned current blob SHA.
4. On SHA/conflict error, refetch and retry exactly once.
5. On create-file path collision, generate a new second-level timestamp and retry exactly once.
6. If a connector call is blocked before reaching GitHub, record the exact surfaced tool/connector error when possible. Do not relabel an unknown error as a GitHub permission or safety error.
7. A failed write never disables or pauses the automation. The next scheduled hour must still execute.
8. If normal contents-API write is unavailable but lower-level Git object actions are available, a run may use an equivalent safe GitHub write path. Do not use shell, local git credentials, or external tokens.

Gmail execution:
- Gmail is called only when MISSION_SPEC/RUNBOOK requires ACTION, changed WATCH, health alert, or 19:29 monster summary.
- These alerts are already user-authorized by the standing automation contract.
- Gmail failure does not stop GitHub audit finalization or other lanes.

Finalization order:
1. state/latest.md
2. health/current.md
3. finalize the same run audit
4. only then classify the scheduler run as success

A scheduler trigger without a finalized audit remains missing_audit and cannot be counted as success.
