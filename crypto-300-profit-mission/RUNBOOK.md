# Crypto Profit Mission Runbook

Updated: 2026-09-26
Timezone: Asia/Bangkok

MISSION_SPEC.md 保留策略、资金与仓位权威。本文件只定义每小时运行合同，减少 scheduler prompt 负载。

## Schedule

每小时 :29。

## Start-of-run

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
1. create skeleton audit: run_status=in_progress
2. execute lanes
3. update state/latest
4. update health/current
5. finalize same run audit status

若最终 update 失败，至少 skeleton audit 能证明 scheduler 确实启动过。

## Success

只有：
- mandatory lanes 有明确 checked/failed 状态；
- state/health 更新成功；
- run audit 最终完成；
才允许 success。

其它情况使用 partial_success / partial_failure / failed。
