# Monster Stage152 独立 Codex P2：6h/24h 敏感性汇总覆盖的最小修复协议

2026-10-15 Asia/Bangkok；Mission Monster 原 Draft PR #30。输入：用户提供的 Codex 独立固定 SHA `f12d6635c6f8a5e2ba8fbb2feeca29688583245b` 复审 `REQUEST_CHANGES`：前三个 P1 已在声明的历史研究范围关闭，原始 1,220 份官方日 ZIP/CHECKSUM 均独立 VERIFIED，全部305逐币历史重放与归档逐行一致，新增唯一阻断为聚合器 P2。该认可仅针对历史原始价格资料真实性与实现，不是G4成交/交易净收益认可。

## P2 可复现根因

`crypto-300-profit-mission/local-agent/scripts/monster_v4_stage151_aggregate_post_d1_research.py` 的 `groups()` 中按 `h in ("360","1440")` 循环，将两种持有期各自算出的 `tiers` 和 `delays` 写入**相同的顶层键** `market_1m_turnover_sensitivity_NOT_execution` 和 `entry_delay_price_only_sensitivity_NOT_execution`，导致360m数据被1440m覆盖。原逐事件行、本次305原始D0/D1和其余24h统计均不受影响。

## 先冻结的最小修复

1. 仅把这两个敏感性聚合对象改为明确按研究持有期字符串 `"360"` / `"1440"` 索引的两级映射。保留原有键名，在同一个层级里每个持有期只存自身在全体已确认/支持样本的成交额 tiers / 1m、3m延迟结果；不变动分层参数、收益算法、原D1、stage151核心逻辑和输出字段含义。必要时可将两个键提前设为空字典并在原循环内按 `[h]` 赋值。
2. 更新旧 Stage152 synthetic 测试的读取路径，不再接受模棱两可的顶层直接 `["10000"]` / `["3"]`；新增一个特别设计的不等价案例，在6h退出1m总quote仅1 USDT、24h退出20,000 USDT，同时设置6h延迟1m毛价-50%、24h延迟1m毛价+9%，断言6h成交量≥10k样本 **0**、24h为 **1**，6h延迟收益 **-50%**、24h为 **+9%**。另要求360和1440两个对象的结构键完整，NO_TRADE/UNSUPPORTED独立且不变。
3. 双系统离线unittest + 原冻结305官方历史1m跨六个日期×四个shard + 汇总/归档CI; 归档必须与本次 trigger SHA 绑定并保留旧Stage152历史Git证据，通过前不得说PASS。源参数 `DROP=.97`, `RECLAIM=1.01`, `MAX_BARS=120`, `HORIZONS=(360,1440)`, `FEE=.002` 双边不动。全305原 184/113/8、24h 184/124/39、24h延迟1/3m样本184及全统计必须不变；新增6h市场成交活跃度理论应回到184/133/54，6h额外延迟1m/3m中位理论约-1.684256%/-1.720261%。真实结果取CI原始机器报告，不提前填写未取证的断言。
4. 归档的新聚合器 SHA 必然变化；触发SHA也随提交变化。单独保存新的结果文件（或在原Stage152由新trigger版本化记录）且明确与前一版区分，不能假装旧固定SHA产出了新两维汇总。完整交付一份新固定SHA的可复制其他AI复审提示词。
5. 禁止为这个局部P2扩大工作到已审计完成的P1、历史已曝光样本调参或长期改边界；不启动Monster正式生产、Mac、Frank、邮件、定时采集或真实交易。D0 WATCH完整保留。仍为 **NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE, G0 PARTIAL, G1 NOT_SCORABLE, G2/G3 NOT_PASSED, G4 UNKNOWN, G5_FULL_RELEASE NOT_PASSED, G6 NO_GO**。

本协议需先提交Git，后提交实现及测试。用户不是要求等待Oct24发布窗口才修复此问题；旧305原始数据仍可现在独立复算。
