# Monster Stage28：原生产共用D1队列、真实官方5m、1128个候选与826→828逐事件验收

2026-10-11（Asia/Bangkok）。当前研究PR #30，原分支 \`research/monster-v4-local-discovery-20261010\`。**SOURCE=VERIFIED / PRODUCER_CI=PASS / PAIRWISE_CI=PASS / STRATEGY_PROFIT_GATE=NO_GO / DEPLOYMENT=NO_GO**。

## 核心结论

此前Stage26按**每币一个SQLite**、原V4连续168小时扫描，在六日期4548个币日期中，2719组官方完整分钟史产生1132 WATCH和826 D1 SETUP。Stage27仅假定“每三分钟处理最多8个、15分钟有效”的简化**一次首次评价模型**，估算50个候选未获得首次评价；它没有计算真实生产D1反复等待5m收盘、拒绝重复bar、延期处理和最终退出，因此不能等同真实D1性能。

本轮[预先冻结的Stage28合同](evidence/monster_stage28_exact_shared_d1_production_queue_prereg_20261011.json)不改变原 WATCH/D1阈值，直接将**全部Stage26原始真实WATCH到达时间线**按UTC注入**每个历史日期一个全市场共用SQLite**，调用原生产 \`monster_v4_shadow.process_queue\` 和 \`evaluate_closed_5m\`，而不是另写近似打分器。每笔需要的历史已收盘5m全部来自Binance官方Spot daily/klines/5m，逐ZIP验证发行方 \`.CHECKSUM\` SHA-256，并校验日内完整288根、时间戳精度和5m收盘因果关系。处理容量仍是每3分钟最多8个，WATCH候选15分钟截止，真实生产重复评价、\`retry_after_ms\`、延期/过期分支不变。

**重要研究范围界限**：这是真正共用SQLite上的**原生产D1子系统**；WATCH时间来自之前“每币独立”的D0结果，未将完整758币历史1m行情重新喂给同一个全市场\`observe_snapshot\`；也没有把Stage26原始D0 INVALIDATED事件注入或重放真实Spot+Futures共同排队。不能写成全套真实系统时效已验证、真实通知投递成功或全历史上市币完整覆盖。

## 真实Git CI、原始来源验证与独立回算

- [Stage28六日期原生产D1共用SQLite真实CI #38146403662](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38146403662)：**6/6成功**，原生产代码Git Blob SHA严格匹配 \`bc958b3d90a8a52afa51515cb53f7e5fafaffaaa\`，执行实际代码SHA \`973891aae686b05e6bba35bdf506ddca578b1bda\`，7/7单元测试PASS。六日期一共引用**1421份**独立币日5m官方来源SHA证据（有多日期重复币，计数是币×日5m ZIP）。
- 首次Stage28单测曾因**生产源码自动吞下行情错误并安排重试**导致测试拒绝放行。新增严格研究入口：只要官方5m源下载或完整性错误，被生产函数吞掉并重试，也要使整次回测失败，不能将来源缺失伪装为“无D1”。该失败和修复CI均保留。
- [Stage28六原始Artifact ZIP和内部JSON SHA-256再验收CI #38146953673](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38146953673)：success，5/5独立统计测试PASS，逐个核对六日期、全部1132 WATCH事件、源身份、真正生产D1队列事件和最终状态。
- [Stage28全部**36份Stage26原始证据 + 6份Stage28**原始证据，合计42 ZIP/JSON逐字节校验并逐事件对账CI #38147245694](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38147245694)：success，4/4对账测试PASS；真实原始复算Artifact \`11704518945\`，ZIP SHA \`82b1037531f4d1df7a20883277ddf47f8cc2d87f10c547d5bc62a556f1ba5cca\`，内部JSON SHA \`5169daf2a9c4956ac16e32ee8f50639030596e957d2364fc7c0f9c14d7b6597e\`。用于永久追溯的[六日期原始身份登记](evidence/monster_stage28_original_six_real_shared_sqlite_artifact_proof_20261011.json)与[42源逐D1证据](evidence/monster_stage28_actual_42original_D1_pairwise_loss_audit_20261011.json)已提交原PR，不依赖仅30日保存的Artifact才知道关键结果。

本阶段代码：[真实共用D1生产回放器](../local-agent/scripts/monster_v4_stage28_real_shared_sqlite_d1.py)、[六原始ZIP聚合器](../local-agent/scripts/monster_v4_stage28_aggregate.py)、[42原始ZIP/JSON逐事件对账器](../local-agent/scripts/monster_v4_stage28_pairwise_D1_compare.py)及各自回归测试。

## 六日期全部1132 WATCH真实生产D1结果

| 已冻结UTC日历起点 | WATCH到达 | 逐币独立旧D1 | 共用SQLite真实D1 | 队列LATE_REVIEW | 最多同时PENDING |
|---|---:|---:|---:|---:|---:|
| 2025-11-04 | 260 | 219 | 220 | 2 | 6 |
| 2025-12-04 | 133 | 113 | 113 | 2 | 4 |
| 2026-02-04 | 269 | 120 | 121 | **96** | **101** |
| 2026-04-04 | 181 | 149 | 150 | 9 | 5 |
| 2026-08-04 | 182 | 146 | 147 | 3 | 3 |
| 2026-09-04 | 107 | 79 | 77 | 11 | 13 |
| **汇总** | **1132** | **826** | **828** | **123** | **101** |

真实六日期累计1128个\`candidate_queue\`记录（同币少量WATCH更新尚未完成的PENDING，故少于1132次WATCH），最终1005个\`EVALUATED\`、123个\`LATE\`，生产\`process_queue\`累计3542次候选选取，2414次延期/重试。不能把“LATE”当作已形成的买单、亏钱或丢失的邮件；生产原始\`SETUP_ACTIVE\`才算D1。

**2026-02-06 00:36UTC历史共振**：本轮真正共用SQLite中当时98个代币WATCH，**91个最终LATE、7个EVALUATED**；该日历实验整周共96个LATE。Stage27一次首评模型对该批次估计有50个候选未被首次处理，实际原生产会占用队列多次处理同一候选，因此得出91个过期，证明简化吞吐上界确实明显偏乐观。但所有6日期的D1总量仍为828，甚至比旧独立版826多2个；直接说“因此丢失91个有效买入机会”是错误的。

## 826个历史独立D1 vs 828个共用D1，逐笔精确对账

由42份源文件逐事件而非仅计数：

| 完全相同的币、UTC D1确认时间 | 旧版存在但本次不在相同时间 | 共用版有但旧版不在相同时间 |
|---:|---:|---:|
| **823** | **3** | **5** |

旧版未原时点确认的3个全部是2026-09-09：

- \`IQUSDT\`：旧D1 22:21 UTC，共用队列在**22:30 UTC才出现D1**，即确认延迟9分钟，**不是永久丢失**。其WATCH固定24h退出的价格代理因退出分钟零成交而被标\`CENSORED\`，没有可信净回报。
- \`SYNUSDT\`：旧D1 22:27，真实共用队列在候选有效期内未评价成功并\`LATE\`；该币WATCH所对应买卖分钟成交额不足30 USDT，原研究价格代理\`CENSORED_MINUTE_QUOTE_LT_30_USDT\`，无法认定可买可卖。
- \`TUTUSDT\`：旧D1 22:27，真实共用队列\`LATE\`；同轮WATCH的24h价格代理，20bps/边滑点+10bps手续费假设下**净回报仅+0.226808%**（独立30U头寸约+0.068042U）。这**不是若D1确认后才买入的收益**，更不是该笔真实可以成交或用户已失去的收益。

共用版新增的5条精确\`(币, D1 UTC)\`事件为\`C98USDT\`（2025-11-07 17:12）、\`FUSDT\`（2026-02-08 00:12）、\`MEUSDT\`（2026-04-05 13:00，原该币同日13:27另有旧SETUP）、\`BICOUSDT\`（2026-08-09 07:21，该币原本同周就有其他D1），以及IQ在22:30的延迟确认。

**统计口径必须严格统一。** 准确口径为826旧、828新、精确匹配823、旧独有3、新独有5；其中IQ为同一个币延迟确认的迁移，SYN/TUT确实旧D1未在共用队列中重现，其他有新的事件。差异也可能受“原独立回放从官方1m累加成5m”与“Stage28直接读取官方发行5m”在成交额精度边界的影响，加上没有重放全球D0撤销事件，**未能完全隔离全球队列拥堵与行情聚合粒度这两个变量**。

## 经济重要性判断与下阶段

已验证：原V4能在六组已暴露历史的40个2×事件前WATCH，但Stage26固定24h交易价格代理549笔206赢343亏、中位-4.858376%，即便修正为Stage27数学不透支现金30/300U模拟，最佳确定性20bps乐观回收场景仍净亏。Stage28进一步说明，拥堵确实会让大量D1候选\`LATE\`，却**没有证实大规模有效盈利D1因此丢失**。过度专注“让所有不具备有效买入价值的D1都被及时处理”不能完成用户的盈利目标。

高价值后续应当：

1. **完整同一共享D0状态**：Stage28已经真实回放\`process_queue\`，但全市场\`observe_snapshot\`仍按币独立从Stage26派生；若继续做真实生产时效验证，需要将同一来源全市场官方1m的3分钟时点数据一次性注入一个SQLite、保留原D0撤销和共享D1，再核查全部826旧SETUP及已确认大涨币的真正告警领先。不得将Stage28冒充完成这一步。
2. **大涨发现不等于可盈利买入**：下一策略研究不得在已暴露六日期改阈值或根据91条LATE筛“赢家”；应在事先冻结的全市场**新日期**，同时比较原V4 WATCH与净盈利/成交额/滑点/资金机会成本，尤其是30/300 USDT真实可用现金及退出流动性。必须选能够得到官方原始分钟/成交源和可验证执行数据的标的，不编造历史L2。
3. **独立AI review和本地部署放行**：截至本轮，真正其他AI独立Review\`NOT_DONE\`，交易净盈利策略\`FAIL\`，Frank生产服务不动，Monster本地/邮件/自动交易均\`NO_GO\`；成功完成GitHub CI、历史事件对账不代表策略可以部署。

状态：\`STAGE28_REAL_PRODUCTION_SHARED_SQLITE_D1=VERIFIED\`，\`STAGE28_ORIGINAL42_ZIP_JSON_SHA=PASS\`，\`STAGE28_D1_SETUPS=828\`，\`STAGE28_LATE_EVENTS=123\`，\`STAGE28_D0_SHARED_FULL_REPLAY=NOT_DONE\`，\`BUY_STRATEGY_NET_PROFIT=FAIL\`，\`OTHER_AI_REVIEW=NOT_DONE\`，\`FRANK=UNCHANGED\`，\`DEPLOYMENT/REAL_GMAIL/TRADING=NO_GO\`。
