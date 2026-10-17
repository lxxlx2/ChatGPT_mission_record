# Monster Stage162 — 独立 Codex APPPROVE 回执及研究关口关闭（2026-10-18）

## 独立审核来源与不可变版本

此文基于用户直接提供的完整Codex独立审核报告归档；审核者自述 **Codex**，精确底层模型 **UNVERIFIED**；不冒充GitHub原生review按钮，也不冒充作者本会话代替另一AI复核。

- 审核唯一固定SHA：`b85dee96ec6f567e1f0b90f0d50cc5b19c79018b`；基线Stage161固定SHA：`0b3044daa9eeef14ac968c6d0f36a430b6b9ca23`。
- 正式结果：**APPROVE（严格仅限Stage162首次有效5m评价优先公平8槽研究代码及本次同源历史445 A/B数据证据）**。Codex报告未发现新P0/P1/P2，真实28/28 unit tests exit 0、py_compile exit 0。
- 审核者独立下载3套原始GHA Artifact（不只看作者Git摘要）：原445 baseline `12044872933`，Stage161逐槽 `12113086240`，新Stage162完整A/B `12113719899`；各自核心full JSON SHA256按顺序是 `370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf`、`8d7ac8d9a0a78a0daa1164d0aee7783b0a51f29ef099437590b103bad0bab76d`、`c30c8b6467b0017b36efc33fadfa2c7853f29f9c7e32993249774269ba4e2ae2`，全部一致。
- 独立审核 checkout `/tmp/monster162-review-b85dee`，detached、clean。验证CI #39068290868 的trigger SHA `46f637c7aa2a833915c754b271ec413b67442c5f` 和审核SHA的7个核心文件内容字节一致，不混同SHA。Codex没有自行从28 ZIP/4450 publisher days重放官方原始1m源；这部分信赖CI及来源审计，不能宣称独立完成原始行情再次采集重放。
- 原生产 `monster_v4_shadow.py`、`monster_v4_shared_spot_d0_d1_original_core.py`、零quote研究V2字节没有改变，仍不属于新策略生产部署批准。
- 独立SQLite故障探针：8槽正确选中、强制原handler SQL失败后未选中retry关闭重开已恢复、源读取中途故障只保留已经提交的队列变化、初始mask写失败异常、恢复SQL被强制拒绝时 **明确抛MONSTER162_MASK_RESTORE_FAILED且不返回成功报告**。后者不能保证不可恢复的mask依旧干净，审查正确保留异常边界。

## 业务结果独立复算

保持1轮最多8、3min poll、真实每人deadline15min；不窥未来价格、收益或事后赢家名单，仅当前PENDING+retry已到期+尚无有效5m评价+已过时钟闭合K线资格。269 WATCH事件及队列身份/first_seen/deadline不变，双方3360轮、753个D1选中槽（269首次、484重复）。

| 指标 | FIFO8基线 | Stage162 |
|---|---:|---:|
| PEAK98 有效首次5m评价 | 7 | **32** |
| PEAK98 最终LATE | 91 | **66** |
| OTHER171 有效首次评价 | 165 | **167** |
| OTHER171 最终LATE | 2 | **0** |
| 原SETUP_ACTIVE精确持久队列ID事件数 | 120 | **120** |
| 原SETUP丢失/新增/延迟 | 0/0/0 | **0/0/0** |
| PEAK98 SETUP | 0 | 0 |
| OTHER171 SETUP | 120 | 120 |
| 重复选中但未推进有效5m评价游标 | 190 | **206** |

独立审核者从原始 `slot_trace` 和 `last_evaluated_bar_ms_before/after` 重算：此前172个已有有效评价的候选，首次评价时刻全部不变；新首评27个（峰值25，其他2）。**新增SETUP是0**。120个原SETUP按生产 `event_key(venue,symbol,"SETUP_ACTIVE",persistent_queue_id)`核对，event_id及observed_ms逐条完全相同；同币多次WATCH的合并归因错误已关闭。

## 审核后状态与不许偷换概念

- `STAGE162_RESEARCH_CODE_AND_HISTORICAL_AB_EXTERNAL_REVIEW=APPROVED_FIXED_B85DEE`；**不需要再为同一固定研究代码索求一轮审查**。
- `STAGE162_G5_PRODUCTION=NOT_PASSED`；历史来源是已看过的2026-02后验445/758，313符号删失，历史quote24为派生proxy，不是真正PIT上市时的全量可交易盘口。
- `STAGE162_NEW_SETUPS=0`，无可执行买卖盘口及完整点时费用/滑点、真实入场/退出价，`PROFIT_UNVERIFIED / G4 UNKNOWN / G6 NO_GO`，禁止宣称交易策略盈利或生产就绪。
- 把主研发重心转向**区分Spot和USD-M场所的独立时间样本及可执行交易证据**；旧Stage91/92冻结前瞻窗口是USD-M，不能将Stage162 Spot研究调度直接拿USD-M D1结果当同venue独立OOS。未来数据需保留真实当时上市人口snapshot、冷启动新上市、原始源接收时间和引用身份；缺失一律`OOS_NOT_SCORABLE`。
- PR #30 保持Draft/open/unmerged；`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`，Frank不动。用户禁止所有自行新建定时任务/launchd/cron/ChatGPT Automations；Stage99已按用户本机readback取消，Oct28及Nov11只是将来用户主动提出采集的参考日期。
