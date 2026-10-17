# Monster Stage162 — 同一8槽D1公平性隔离A/B技术合同（先于代码）

**既有研究预注册**：`MONSTER_445_STAGE162_FIRST_VALID_D1_FAIRNESS_RESEARCH_PREREGISTRATION_20261017.md`。Stage161 Claude独立审核固定SHA `0b3044daa9eeef14ac968c6d0f36a430b6b9ca23` 仅批准观察器和证据，shard0失败整体run的成功publisher Job与后续原D1零quote故障已经单独披露；Stage162实验代码需自己测试+外部新审核，不能复用Stage161批准。

## 本次技术预冻结B优先级（不利用未来）

源仍为同一445同SQLite 28历史官方ZIP，原758中313缺源。保留3分钟全球poll，每轮最高8候选、候选自己的持久`deadline_ms`、原D0 WATCH生成及事件身份/快照规则、原生产`process_queue`的5分钟K线特征判断，以及隔离zeroquote研究V2的保护。严格不得改`monster_v4_shadow.py`、`monster_v4_shared_spot_d0_d1_original_core.py`、`monster_v4_shared_d1_zeroquote_research_v2.py`任何一字节。

每轮，在原D0之后、原V2 handler之前，**只读** `candidate_queue` 中满足`status='PENDING' AND retry_after_ms<=now`的当前行；其余不能选中。
- `FIRST_VALID_5M_ONCE_PRIORITY_8` 的优先首评类：行的`last_evaluated_bar_ms IS NULL`，`now<=deadline_ms`，并且**截至本tick已有一根WATCH后完整闭合的5m bar**，严格使用 `latest_closed_5m_end= floor(now/300000)*300000-1` 与冻结生产比较`bar_last_open_ms+INTERVAL_MS>first_seen_ms`的相同时序边界。这里只做时钟资格，不窥未来价格/成交额，也不预言K线source一定可读/quote正值，真正评价仍交给原V2 handler。
- 先按已成熟且尚无`last_evaluated_bar_ms`的候选 `(first_seen_ms,id)` 选最多8，剩余槽按原`(first_seen_ms,id)`从其它**当前eligible**候选填满。PENDING但尚未成熟时仍可选中（在无成熟者竞争时）以保持原D1 AWAIT历史语义。绝不让过期候选伪装成可合法首评，过期候选仅可在fallback里接受LATE终结。
- 仅在隔离实验中临时将**没有选中的eligible ID** 的`retry_after_ms`掩蔽为`now+1`，交给**原`zeroq.experimental_queue_handler`只调用一次**、其内有零报价保护并调用冻结`production.process_queue`；之后在独立事务恢复原retry并读回验证。无更改原5m特征判断、无自造SETUP、无增加8槽或D0流量。临时掩码必须在异常时也恢复，源坏时报真实失败而非假盈利。
- 整个执行同源完整445、原3,360 poll、269原WATCH；从旧官方run `12044872933` 的完整全JSON SHA `370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf` 取得baseline，**逐事件键/候选ID/first_seen**检验所有D0 WATCH身份与计数完全相同。其它D1结果故意允许不同，不得错误断言都跟baseline相同。

## 两侧必须报告的效果与负面影响（不按单峰优化结果）

原FIFO8的baseline来自同一来源冻结真实V2，其原始`queue_rows/events`为对照。B实验逐tick记录当前8选中ID、哪些是首次/重复、是否推进5m评价游标、初次首选与初次有效评价时刻、超deadline候选、来源零quote/失效/SETUP。分唯一历史`PEAK_98`和`OTHER_171`报告**各自**有效首评覆盖、+6/+9/+12/+15实际评价数及延迟分位数、D1状态、重复槽变动。SETUP必须同原120个`event_id`或候选精确锚点比较`retained/lost/new`，报告其它171历史正常信号损失，禁止只展示增益。真实结果如损失原SETUP，即`MODEL_GUARDRAIL_NO_GO`，仍可保留真实负面研究报告（不能因为失败或负收益擦除）。

Stage162是已有Feb445回看机制实验而非独立OOS，historical executable PnL仍UNVERIFIED；冻结报价24h代理不等于当时真实PIT上市或盘口买卖成交量，无BBO/L2、手续费/滑点时无BUY或资金金额。G4 UNKNOWN/G6 NO_GO/NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE。独立研究只允许显式单次request触发Github Actions，不建cron、workflow schedule、launchd/ChatGPT Automation、不用Mac/Frank/Gmail/交易。任何新队列实验必须在新固定SHA和原始输入上提交其它AI独立审核，CI绿不代表模型盈利。
