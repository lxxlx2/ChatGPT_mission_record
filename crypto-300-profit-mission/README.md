# Crypto $300 Profit Mission

Crypto 资产、活动仓位与机会的决策层。

## 权威文件

- `MISSION_SPEC.md`：精简后的全局策略、资金、通知与数据真实性规则
- `RUNBOOK.md`：每小时 scheduler 的分阶段执行合同
- `portfolio/current.md`：当前资金分布
- `performance/current.md`：收益口径
- `state/latest.md`：当前综合状态
- `health/current.md`：scheduler / lane 健康
- `positions/`：各活动仓位的细则
- `watchlists/`：BTC、NFT、Monster V2.1、SAGA、FOMO 等模型
- `runs/`：不可变执行 audit

## 每小时 :29

### Phase A
优先完成：
- Ethereum / Solana 实时资金与 gas
- PONS
- XRP / Variational
- ETH conditional
- BTC regime
- JUMP / deadline
- 活动仓位安全事件

### Phase B
机会发现：
- 优先读取最近两份 Crypto Daily research
- Monster V2.1 用一次 bulk universe screen 做全市场覆盖
- 只对 shortlist 做 funding/OI/taker/top-trader 深查
- launch / NFT / FOMO 只对真实候选深查
- 上游 research 过旧时才做 compact fallback discovery

### Phase C
每 3 小时或发生重大事件时：
- UNICRED
- Credits
- 其它慢速数据

这种结构保留原有监控范围，同时避免每个小时重复跑多套完整全网搜索。

## Monster V2.1

已经完全并入本 Mission。

独立 `妖币每日汇总` automation 保持关闭。

19:29 的日汇总仍由本 Mission 同一轮输出。

## 成功标准

自动触发后必须：
1. 先创建 skeleton audit
2. 留下 Phase A 状态
3. 留下 discovery 状态
4. 更新 state / health
5. finalize 同一个 audit

只有 scheduler last_run_time，没有 finalized audit，不算成功。
