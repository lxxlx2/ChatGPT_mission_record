# Monster Stage59：166条妖币候选跨场所证据与取消固定交易金额

日期：2026-10-12（Asia/Bangkok）。归原 [Monster PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。严格沿用 [开发门槛](MONSTER_MODULE_DEVELOPMENT_RULES.md) 和 [完整数据→方案→技术→代码→回测→独立Review→测试→部署顺序](../MISSION_SPEC.md)。

## 1. 当前金额约束与历史实验之间的明确边界

用户已明确纠正：Monster 妖币模块没有指定单笔交易金额。过去研究用过的 30U / 300U 只是当时已冻结历史实验的模拟参数，不是本轮用户设定，不能用于后续交易资格判定、模型筛选或估算用户实际可成交收益。

已修改正式 Monster V4 架构，新增订单金额状态为 UNSPECIFIED；未来如研究订单簿和滑点，订单金额为明确输入而非固定预设。缺少金额时可以照常研究真实行情、成交、跨场所流动性及早期发现；可执行滑点与资金盈亏必须保持 UNKNOWN。不改任何历史已完成回测数值、原P1 v0.3失败结论或生产环境。

本轮仅涉及 Monster 模块和其研发目录，其他监控模块不处理。

## 2. 本轮经核实的输入和新增来源

Stage59独立源码：[monster_v4_stage59_all166_cross_venue_evidence_matrix.py](../local-agent/scripts/monster_v4_stage59_all166_cross_venue_evidence_matrix.py)。

[Stage59真实GitHub CI #38255294728](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38255294728) SUCCESS，包含源码自检、166条数据完整核验、跨币身份一致性、各Alpha公告早于原本合格信号的时点校验、来源Git blob完整性校验及Git证据持久化。

不可修改的既有输入：
- 原Stage57 166份Spot实际历史1m成交记录 Git blob：561b5a7dd5b894565d01b24671aa6d96d921bda8。
- 原Stage58 166候选完整源、Spot-only反事实5×错过记录的汇总 Git blob：a0f377027ec49e8ec572fba53a2c8cf8872b3180。
- 原P1信号首次达到条件的时间、原全市场每天5条研究URGENT、后验高倍数事件保持原值。

本轮独立搜索并核对三个信号发生前的 Binance 官方英文公告：

- MYXUSDT：2025-06-18发布的[Binance MYX合约与Alpha公告](https://www.binance.com/en-IN/support/announcement/detail/9801625522154e098d73b8245ad70646)明确 MYX 在公告时已经是 Alpha 交易资产，原P1信号为2025-08-03T20:27Z。没有把公告时间错算成实际最早开盘时间。
- AIAUSDT：Binance在2025-09-16发布[官方公告](https://www.binance.com/en/support/announcement/detail/aadbfbfee34c404c896f93957a0c08c7)，声明Alpha于2025-09-18T08:00Z开放，原P1信号为2025-10-02T14:03Z。
- COAIUSDT：Binance在2025-09-23发布[官方公告](https://www.binance.com/en/support/announcement/detail/89921e2281204d32a5fead5b711f6770)，声明Alpha于2025-09-25T07:00Z开放，原P1信号为2025-10-02T07:03Z。

上述证据能确认：在这些原信号之前已经存在Alpha相关的**官方公告**。不能由公告证明精确信号时Alpha仍然正常交易、那一刻订单簿有流动性、链上实际成交池或任何具体买卖金额。MYX合约地址在Binance旧公告中披露，但其他同名代币的CA与池子未完成可靠的历史时点链上绑定，不能任意复用第三方名字相似的token合约。

## 3. 166条真实来源支持的跨场所证据矩阵

[机器汇总](evidence/monster_stage59_all166_venue_evidence_coverage_summary.json)和[166条原始证据矩阵](evidence/monster_stage59_all166_cross_venue_evidence_matrix.jsonl)已经由CI写回原PR分支。

| 原166条既有事件类别 | Binance Spot 15m实际成交SHA已证实 | Binance Alpha官方事前上市公告，但该时刻成交未证实 | 其他交易场所未核实 | 共 |
|---|---:|---:|---:|---:|
| 未来2×且原P1至少提前5分钟 | 7 | 3 | 17 | 27 |
| 未来2×但P1达到太晚 | 0 | 0 | 2 | 2 |
| 未达到固定起点7日2×的普通候选 | 69 | 0 | 68 | 137 |
| **合计** | **76** | **3** | **87** | **166** |

这是已核实的**两种不同证据强度**，不能把76+3=79称作79笔已证明可成交的交易。剩余87例并非已证实不可交易，也可能经Alpha、其他Spot或DEX参与。真实链上DEX在这87例与另外79例中的全市场系统取证未完成，不可宣称已经覆盖全部交易渠道。

3个≥5×事件中MYX、AIA、COAI的官方Alpha公告均发生在信号前，MYX和COAI的历史期货HIGH也≥10×。历史期货极值标签属于事后评价，**不能当作对应Alpha或DEX的可卖成交价和投资回报**。

## 4. 对原研发主线的限制和下一步

Stage59没有更改P1阈值，没有重新配置紧急5条配额，没有选取新模型，也没有宣称发现率/盈利率有提升。Stage52冻结失败保持75%和REJECTED。

下一主线不再反复拟合已曝光166中的赢家：先完善**妖币发现与交易路径两个独立输出**，保存原D0全市场WATCH并不静默遗漏；重大事件在Alpha/DEX有可靠事前交易路径时可提高后续深入核验优先级，但任何新优先级必须事先冻结并在尚未使用的日期做真实因果全市场回测，普通币对照不能省略。无需用户指定资金即可研究报信时效、全市场拥挤、盘口/成交证据；实际金额相关净收益待用户未来定义可执行交易额才评价。

Stage59状态：SOURCE_LOCKED_HISTORICAL_EVIDENCE_DONE，CI SUCCESS，策略/技术新版本 NOT_DESIGNED_OR_VALIDATED，EXACT_EXECUTION_AND_PROFIT UNKNOWN，OTHER_AI_REVIEW NOT_DONE，MONSTER_DEPLOY NO_GO，FRANK UNCHANGED，GMAIL OFF，AUTOTRADE NO_GO。
