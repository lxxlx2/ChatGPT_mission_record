# 32/445共享Spot D1：合法0报价分钟的研究专用非可评价语义 V2——修改前冻结

2026-10-16真实官方来源事实：SHA锁定官方Spot1m分片0/1（共32个早已冻结完整来源币种）的原V4共用SQLite研究在ACAUSDT`2026-02-08T04:42:00Z`第一次因8根闭合5m中一根`2026-02-08T04:30–04:34:59Z`报价成交额精确`0E-8`而fail-closed；该5m OHLC四价均为`0.0038`，前后正常K线成交额为正、15min source由官方ZIP+CHECKSUM读来。真实原生产`evaluate_closed_5m`对所有输入quote调用`positive(CLOSED_QUOTE)`，故不能把真实零报价当source损坏、也不可凭原旧D1的一次临时ValueError断言骗单或盈利。原SHA `1154e97a25648dbf58c181be62076e4c1d406dde` 已独立Codex APPROVE的HIGH=0坏源fail-closed语义必须保留，**禁止修改该旧approved source/production源码**。

## 本轮新增实验与前瞻否决条件

1. 在**另一个仅历史研究、非生产的新语义实验脚本**下，保留全部原D0和预注册758/445/313名单及官方SHA、3min完整数据和同一SQLite。冻结原`monster_v4_shadow.py`、原`shared_spot_d0_d1_original_core.py`完全不修改。该脚本明确命名`ZERO_QUOTE_RESEARCH_VARIANT_NOT_ORIGINAL_CORE`，严禁将实验结果与最初“完全原production D1”混淆。
2. 每轮仍按照原生产队列`ORDER BY first_seen_ms,id LIMIT 8`取得最多8个eligible候选；对每个候选依据**当时已经完整闭合**的8根5m真实原始quote确认是否存在`quote==0`。负价格、HIGH=0、非法OHLC/close时间、非有限数值、缺根或坏JSON必须仍`RuntimeError`整研究失败，**不能被零成交特例吞下**。
3. 若8根严格时钟/OHLC均可信，但某5m`quote==0`，**禁止伪造正成交量或BUY**：本轮该候选消耗一格真实原队列深查预算、`last_error=SOURCE_UNSUPPORTED_ZERO_QUOTE`、下次可用轮询时允许再次评价（以真实闭合source为准），**不计入已成功评价，也不触发SETUP**。如果直到有效15分钟deadline仍不可评价，才终态`SOURCE_UNSUPPORTED_D1_ZERO_QUOTE`并作为**源语义/可执行性弃单**，非`LATE_REVIEW`且非盈利机会损失；有价格但quote0不代表source造假。若曾因合法quote0不可评价而到达`now>deadline`，转明确不支持而非假LATE；从未尝试/因队列容量积压而到期的候选继续按冻结原D1真正LATE处理。另保留各候选的ZEROQUOTE尝试数和15分钟内恢复为可评价的数量。
4. 对没有任何零quote的样本，新研究队列必须与原生产`process_queue(limit=8)`在所有WATCH时间、SETUP、延期、确认和LATE完全一致；有合法quote0时新语义修改的是缺source评价类别，**其余原D1由未经修改的production.process_queue(limit=1)**处理。固定最多8个评价槽、FIFO、backoff，不得通过单轮循环处理第9个候选或忽略历史候选源失败。
5. 先在原**真实32币**两份已锁源中成功完整跑3360轮、报原`2026-02-06T00:36Z`真实共D0同刻WATCH、全D1评价/最终LATE/零quote弃评分母，再去固定445**不修改既定原445 SourceComplete人口**。此实验与原旧失败的两个结果要并列，而不是改写原实验为PASS；保留单独`SOURCE_UNSUPPORTED`原因以利后续模型真实性判断。
6. 两OS完整负向测试覆盖合法zero报价、HIGH=0腐败源、源闭合时间漂移、多候选FIFO达到8上限、从未尝试到期仍LATE、已发过合法ZEROQUOTE等待到期成为SOURCE_UNSUPPORTED，以及无quote0时与原production原队列同源同结果。真实新固定SHA CI和另一AI独立review是推进任何Mac/邮件或交易之前的硬门槛，**研究性质创新不等于原approved V4生产规则认可**。
7. 全程`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`、`G4 UNKNOWN/G6 NO_GO`，Frank/Stage99不动，无schedule、没有隐含单笔金额。

本协议只定义拟测试的**新研究变体**，绝不是用户允许改生产策略、部署或下单的授权。若模型审查出现新的P1/P2，源变体不得认为业务通过。
