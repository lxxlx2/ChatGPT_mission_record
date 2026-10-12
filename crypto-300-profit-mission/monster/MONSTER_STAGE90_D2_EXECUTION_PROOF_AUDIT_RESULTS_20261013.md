# Monster Stage90：D2真实交易资格与双向盘口证据关口的首版实际结果

日期：2026-10-13（Asia/Bangkok），原 Monster [PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。

## 已执行与证据

1. 先提交[Stage90冻结合同](MONSTER_STAGE90_D2_EXECUTION_EVIDENCE_CONTRACT_AND_BOUNDARY_20261013.md)，明确D1依然是研究SETUP，D2只能核对交易资格、同一时点订单簿、双边交易成本和资金容量。没有给出用户单笔名义金额，**不得默认**原历史30U或300U。
2. 新实现[Stage90只读D2证据判定器](../local-agent/scripts/monster_v4_stage90_d2_execution_proof.py)，代码Git blob `d71f46370e40748b7db90d8f18a0599df2522510`。固定优先级`OUT_OF_SCOPE/IDENTITY_UNKNOWN/MAPPING_UNKNOWN/VENUE_UNKNOWN/BOOK_UNKNOWN或INVALID或STALE/NOTIONAL_UNKNOWN/FEE_UNKNOWN/DEPTH_INSUFFICIENT/SNAPSHOT_COST_EVIDENCE_ONLY`。对真实binance USD-M订单簿原始`lastUpdateId,E,T,bids,asks`做raw JSON->SHA256与提取字段逐一对账、5秒因果性窗口、逐档ask模拟买入、逐档bid模拟同瞬间退出。不得用当前2026-10订单簿代替2025历史信号。
3. GitHub Actions[Stage90 CI #38312326794](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38312326794)完成早期合成测试和原305审计成功，但此后的原始body-SHA改进版首次[CI #38312466187](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38312466187)曾**失败**，原因是原合成薄盘口测试在改变深度之后没有重算对应的原始响应哈希，结果被完整性检查按预期拒绝。调整测试夹具使有效薄盘口案例携带匹配的合成raw payload，并保留另一个篡改失败案例，重跑[最终Stage90 CI #38312526532](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38312526532)，实际 **SUCCESS**。最终模块版本提交`99b8d6eaa73780b693c5424eb940a1b0d3b9777e`；失败结果没有隐藏。
4. [Stage90全部305条来源锁定机器审计](evidence/monster_stage90_all305_D2_execution_evidence_gap_audit.json)，Git blob `11e0a62d46c2da2f7c7854c14d15edd84abc7d5f`。由Stage88真实官方1m价格证据锁定的原305条D1/混合USD-M币日期，没有静默删除任何一个。

## 全量审计：能确认与不能确认的事实

| 冻结原D1人口 | 数量 | 解释 |
|---|---:|---|
| `IDENTITY_UNKNOWN` | 294 | 当前归档缺少足以独立判定D1当时为Crypto的正式身份证明，**不代表这些币不是真实加密资产** |
| `MAPPING_UNKNOWN` | 9 | 1000/1000000等合约标的单位、倍数映射未有同刻独立完整证明 |
| `OUT_OF_SCOPE` | 2 | 已归档且时点证实为TradFi非Crypto，如LRCX/KLAC对应历史样本 |
| **总计** | **305** | 原Stage88全人口，没有新条件筛掉赢家或普通样本 |

这305条在过去只有已闭合1m K线和官方发布者SHA，**没有**过去D1当时完整双向历史盘口原始响应，亦没有用户本轮给定的金额和完整双边费用证据。因此：

- **真实可买入报价/退出深度**：`UNKNOWN`。
- **当前完整历史可成交净回报**：`UNKNOWN`；Stage88毛价格中位24h -2.80% / 72h -6.35%只是信号后K线研究，不能当成交亏损。
- **真实 D2 ACTIONABLE_CANDIDATE数量**：`NOT_SCORABLE`，绝不将0条有证明误写为0条真实可以交易。
- **真实 D1 核心策略状态**：平均7.26个/日、峰值52个/日，Stage77 G3仍失败；Stage90工程成功没有修复策略质量。
- **真实Crypto-only全人口与G0**：`PARTIAL`，还需历史交易所产品公告、官方上市/交易状态及单位映射证据。
- **Spot订单簿适配范围**：Binance Spot REST depth没有USD-M那样的`E/T`时钟字段，Stage90首版因此fail-closed为`BOOK_UNKNOWN`。需真实已校验的历史/前向stream as-of资料与本地采集设计才可升级，不能改用接收时间假装撮合事件时间。

## 为什么当前不应增加更多任意策略阈值

Stage85–87已证明原D1升级时的60m动量、quote、trade、量比和简单BTC/ETH相对强弱不能稳定在同日期将历史重大机会和普通样本分开；Stage88证明很多D1随后24/72h下跌且回撤大。下一步若仅为历史305赢家设新阈值，会重复在已曝光数据中过拟合。现阶段最合理的工程结果是**固定对可交易证据的真实性要求，禁止把不完整盘口的D1伪装成可以买入**。

唯一后续主线：在后续真正前向样本上，用同一D0/D1核心保留全量WATCH，实际采集point-in-time Crypto身份、上市状态、单位及深度的原始source bytes和hash，并结合用户明确指定的测试订单金额进行**无真实下单的**买卖容量/费用检验；然后才有资格研究一个同时满足G2重大机会保留、G3注意负载和G4真实净收益的新D2高优先级确认方案。必须先取得完整证据和真正其他AI独立审查，才讨论Mac本地部署；不得未经授权启用自动化、Gmail或交易。

当前 `STAGE90_D2_EVIDENCE_CORE=CODE_CI_PASS`；`STAGE90_HISTORICAL_ALL305_PROVENANCE_AUDIT=COMPLETE_WITH_EVIDENCE_GAPS`；`D1_G3=REJECTED`；`REAL_EXECUTABLE_NET_PNL=UNKNOWN`；`OOS=NOT_DONE`；`OTHER_AI_REVIEW=NOT_DONE`；`DEPLOYMENT=NO_GO`；`GMAIL=OFF`；`AUTOTRADE=NO_GO`；`FRANK=UNCHANGED`。
