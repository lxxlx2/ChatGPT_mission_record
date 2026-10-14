# Monster Stage132：首次动量信号后固定持有期真实历史价格路径，经济代理呈负值

日期：2026-10-14 Asia/Bangkok。原 [Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。模型及实盘 `NO_GO`。**这些是已曝光历史 1m OHLC 的零费、零滑点、未成交报价代理；绝非实际净收益或新的样本外（OOS）。**

## 一、先验与真实源

1. 在本轮经济代理计算前，先将唯一 [Stage132 固定实验口径](MONSTER_STAGE132_FROZEN_FIRST_SIGNAL_DELAYED_CLOSE_EXIT_PROXY_PROTOCOL_20261014.md) 提交 commit `a5e9a0f7905ee232062d3c3ff60755eb746613b2`。仅采用原 Stage130 **全部31个** 已有新上市候选，19个去重后的首次动量信号、12个无信号，不根据未来2×暴涨或当前收益挑选；没有修改 Stage118/127/130 的冻结阈值或时间。
2. 原始来源完全复用 [Stage130 官方 Binance Data Vision 1m Publisher SHA 研究](MONSTER_STAGE130_FROZEN31_OFFICIAL_1M_CAUSAL_NEWLISTING_RESULTS_20261014.md)：固定原 `stage130_real31.json` SHA256 为 `a97037bff9d834f0f59fb3a0ae45942a9c28453dbfc0d01331fd78afa49b8f50`，原 ZIP artifact SHA256 `e1a5931b64497214faa726831cbe1c64e2c93c3cbfd1c2e101af402da816372b`；31/31，159,675条真正原始1m，147个官方日ZIP及对应 `.CHECKSUM` 配对。完整源仍可从原 [CI #38566877450](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38566877450) 的30天保留制品取回，不宣称 Git 已永久保存147个源ZIP。
3. 固定入场价格代理：首次动量产生于已闭合一分钟 UTC 整3分钟时刻 `t`，模拟再等待一分钟，在 `t+1m` 这一分钟的**OPEN**作为未成交入场价格。严格按 `15/60/360/1440` 分钟持有，退出取相应未来分钟 OPEN；从假定入场至退出前一分钟的 LOW/HIGH 算不利/有利路径。没有止损、止盈、杠杆、延迟变化、手续费、市场冲击或用户未指定的交易额。窗口外未来数据严格 `RIGHT_CENSORED_SOURCE_END`，不填零、不把极端 HIGH 直接当利润。

## 二、全量历史结果

| 固定退出时间 | 成功取到价格的首次动量案例 | 右删失 | OPEN→OPEN 毛收益为正 | 中位毛收益 | 算术平均毛收益 | 最差期内 MAE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 15分钟 | 19 | 0 | 6 | **-2.5681%** | **-1.9012%** | **-15.3675%** |
| 60分钟 | 19 | 0 | 6 | **-3.9260%** | **-3.3830%** | **-19.2483%** |
| 360分钟 | 19 | 0 | 5 | **-4.8253%** | **-3.6554%** | **-40.8693%** |
| 1440分钟 | 15 | 4 | 4 | **-3.2593%** | **-4.3866%** | **-69.8493%** |

剩余 **12/31** 无初次动量信号，保留 `NO_SIGNAL`，不能假设可买/收益零。24h 的四例在已冻结七日资料结尾没有完整未来退出价，为右删失而非亏损。中位/均值针对具有固定持有期价格的原19个首信号，**没有扩展为全市场 Crypto**；其中有后验标为 Equity/HK Equity 的代理，必须单列 G0 未认证。完整分布（p25/p75、最差毛价和删失计数）保存 [机器结果](evidence/monster_stage132_original31_delayed_entry_fixed_horizon_machine_summary_20261014.json)。

已知两个后验历史2×上涨案例，按同样冻结方法计算：`VINEUSDT` 15m **+6.84%**、1h **-12.95%**、6h **-23.50%**、24h **+12.51%**；`APRUSDT` 15m **-12.06%**、1h **-9.54%**、6h **-20.98%**、24h **+58.73%**。此处约值是已回放结果的便读呈现，精确口径以原CI逐事件JSON为准，绝不将事后最高2×用于决定退出。两例已曝光，不构成正向前瞻策略证据。

**业务结论：即使不计算实际手续费和滑点，以固定未来开盘退出计算的样本中位数在全部四个预定持有期均为负。** 这批原新上市动量条件只能保留为历史早期发现研究，不能升级为可执行买入模型。不得选择最优单一持有期、改信号阈值或挑VINE/APR盈利持仓声称该模型成功。

## 三、代码、失败与成功证据

- [同一份离线脚本](../local-agent/scripts/monster_v4_stage132_delayed_entry_horizon_proxy.py) 和 [回归测试](../local-agent/scripts/test_monster_v4_stage132_delayed_entry_horizon_proxy.py)；程序重新独立验147个 publisher ZIP SHA、全部31 case ID、159,675分钟、来源开头和时间连续性；从原Stage130冻结最早动量时点直接计算，不从未来高点倒推。
- 首轮 [GitHub CI #38578392121](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38578392121) 为 **FAILURE**：离线合成测试通过，但完整实际源码重放前，单测脚本变更目录之后使用相对 `stage130_original` 而找不到ZIP artifact JSON。明确保留失败，没有调整交易规则或市场源。
- 只修复工作流中单测的路径为 GitHub workspace 绝对目录；修复 commit `4aca6a86123445d079727373dc623aee808529bb`。
- 修复后 [GitHub CI #38578529492](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38578529492)，macOS job `115901937437` 和 Ubuntu job `115901938324` 均实际 `SUCCESS`。两个平台均实际从冻结的旧Stage130 CI源 artifact 读取全部147日ZIP/校验文件、重算159675根1m和全部31币；按两端机器输出的完整固定期汇总逐字段比较一致。新CI保存各自完整31条结果JSON的短期 artifacts。
- 永久 [Stage132机器摘要](evidence/monster_stage132_original31_delayed_entry_fixed_horizon_machine_summary_20261014.json) 含4种固定持有期、有效/删失、均值/中位/P25/P75、最坏风险代理与原先失败CI信息。编译/回归及真实源测试成功**只说明结果可重现，不构成赚钱或模型通过**。
- 其他AI独立Review **NOT_DONE**。没有生产安装、Mac服务恢复、邮箱发送、Frank更改、交易或通知。

## 四、下一主线，必须止损于已见历史参数

1. **冻结 Stage130 的“新上市首动量即买入”研究通道为 `HISTORICAL_ECONOMIC_PROXY_NEGATIVE / BUY_NO_GO`**。仍可保留 D0 发现研究，19信号/2早5分钟是值得进一步真实验证的 *发现* 证据，不是 D1/D2。
2. 核心下一步应优先整合 Stage131 全市场既存及窗口内新上市人口、真实现货/合约crypto身份与真实事件时间证据，事先锁定**全新三段互相独立的前瞻窗口**，对每笔D0、D1使用同一源时间与全分母验证。旧 Stage116 原2026-10-14 06:00 UTC采集失败不得补判。
3. 真正 G4 依然必须读取当时可以交易的场所、买卖盘口真实深度、适用手续费、明确由用户给的成交额、模拟/实际退出价和失败统计，至少30个完整独立进出场证据；在此之前一切毛价代理保持 `EXECUTION_UNKNOWN`。
4. 正式 G0/G1/G2/G3/G4 未通过、没有真正另一模型Review之前，任何 Mac Shadow 或邮件仍 `NO_GO`。用户2026-10-28、11-11只有主动聊天触发的手动行情快照，不建立任何定时任务。

`STAGE132_SOURCE_AND_REPLAY=DONE`; `STAGE132_EXPOSED_FIRST_MOMENTUM_BUY_PROXY=NEGATIVE`; `STAGE132_TWO_OS_CI=PASS_AFTER_INITIAL_FAILURE`; `STAGE118_STAGE127=REJECTED_UNCHANGED`; `G0=PARTIAL`; `G1_NEW_OOS=NOT_SCORABLE`; `G2_G3=NOT_PASSED`; `G4=UNKNOWN`; `G5_OTHER_AI_REVIEW=NOT_DONE`; `DEPLOYMENT=NO_GO`; `FRANK=UNCHANGED`; `GMAIL=OFF`; `NO_NEW_SCHEDULE`.
