# Monster Stage90：D2可成交证据合同，独立于失败D1模型

日期：2026-10-13，Asia/Bangkok；范围仅原 PR #30；`STANDARD_FROZEN_BEFORE_IMPLEMENTATION`。严格继承 [Stage77](MONSTER_STAGE77_CORE_MODEL_ACCEPTANCE_AND_BOUNDARY_FREEZE_20261013.md)、[Stage89](MONSTER_STAGE89_STAGE88_305_D1_POST_SIGNAL_PRICE_PATH_RETURN_TAIL_RISK_FINDINGS_20261013.md)、`MONSTER_MODULE_DEVELOPMENT_RULES.md`及 Mission Spec。**本阶段不改变D0发现、不改变冻结Stage79 D1、不新增盈利预测阈值、不触碰Frank或生产通知。**

## 0. 决策

已核实历史305个D1，24h固定退出价格中位-2.7992%，72h -6.3536%；虽然七日锚点2×旧发现保留27/28，注意力负载7.26/天、峰值52，D1仍失败。仅把当前D1视为`SETUP_RESEARCH`。即使D2未来查到真实盘口，也不能将失败D1自动升级为`BUY`或真实通知。

当下Stage88官方1m OHLC只证明价格曾出现及当分钟有成交，**无法证明在D1时刻存在足额深度、买卖报价、费用或按指定金额可退出**。Binance官方`/fapi/v1/depth`响应包含`lastUpdateId`、`E`、`T`、`bids/asks`，仅为获取当时的订单簿快照；当前API返回的最新深度**不可回填2025/2026历史D1**。[官方接口](https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data)。Spot `/api/v3/exchangeInfo` 和 USD-M `/fapi/v1/exchangeInfo`只能提供查询时的市场状态，不能代表没有存档时的历史挂牌状态。[现货官方文档](https://developers.binance.info/en/docs/catalog/core-trading-spot-trading/api/rest-api/general)。

## 1. 一个确定、能复用的纯函数证据合同

输入对象必须携带：

- `D1 observed_utc`、`venue`（BINANCE_USDM/BINANCE_SPOT）、`symbol`、研究身份`identity`（独立验证为Crypto、已确认非Crypto、暂不明）、`identity_evidence`（来源、真实见证时间、验证状态）、`mapping_verified`（1000/1000000等商品单位倍数确认）。任何一项无法确认的交易身份不得当成Crypto。
- `market_status_asof`（同venue、同symbol、在D1时间**已生效**且有效的挂牌/交易状态与资料证明），`book`（同venue/symbol的买一/卖一及逐档价格×数量、官方接口原始body哈希、接收时刻、撮合事件时刻、更新序号、来源），必须与信号时间先后因果一致。
- `notional_quote`显式来自用户/策略测试请求、`entry_taker_fee_bps`、`exit_taker_fee_bps`及该费率适用时间/来源；未给出则保持`UNKNOWN`，不能挪用旧30U/300U和历史20bps。
- `book`安全时钟：`capture_ms`必须在D1之后0～5000ms内，`event_ms <= capture_ms`，且`capture_ms-event_ms<=5000ms`；这是**工程上的新鲜度拒绝上限**，不代表经过回测验证的利润参数。采集者必须保存可审计原始响应SHA并由外层独立核验来源真实性；纯函数只验证输入一致性，绝不能因为一个字段写`verified=true`就声称已经独立核对互联网来源。

严格状态层级（最先未满足的一项立即退出，并保留原因）：

1. `OUT_OF_SCOPE`：经时点独立证明确认的股票/ETF等非Crypto。
2. `IDENTITY_UNKNOWN` / `MAPPING_UNKNOWN`：Crypto身份或单位/基础资产映射证据不足。
3. `VENUE_UNKNOWN` / `STATUS_NOT_TRADING`：当时正式市场资格来源不足或确实未开放。
4. `BOOK_UNKNOWN` / `BOOK_INVALID` / `BOOK_STALE`：无时点订单簿、档位错误、跨币、超时、顺序交叉或来源未核验。
5. `NOTIONAL_UNKNOWN` / `FEE_UNKNOWN`：无交易金额或双边费率可查；即使有价差，也**不**宣称真实下单足额。
6. `DEPTH_INSUFFICIENT`：按当时ask逐档模拟买入与按bid逐档模拟**同时刻反向退出**，任一方向数量不足。此检查不能证明未来退出有买盘。
7. `SNAPSHOT_COST_EVIDENCE_ONLY`：仅在全部齐备时输出当时模拟双边消耗的买入VWAP、卖出VWAP、价差、总额、双边费率和“同快照瞬时往返”成本下界。**这个值是行情瞬时深度敏感的研究证据，禁止称实际下单利润、保证成交或未来平仓净收益。**

## 2. 回归要求

- 使用原Stage85全部305条原始D1和Stage88全部官方K线结果作只读来源锁定。当前仓库没有同时刻的真实bid/ask、历史listing proof及用户单笔notional，因此305/305应如实输出`BOOK_UNKNOWN/IDENTITY_UNKNOWN`等缺口；不能伪造历史真实成交，不能把305个未知计为305个不挣钱。
- 核心函数测试必须包含：有效Crypto/合规市场/有来源的深度、延迟、部分盘口、跨币、倒挂盘、买侧与卖侧深度不足、用户金额未知、费率未知、股票标的、1000前缀映射未知。按固定已知数值构造**合成测试**，合成价格只用来验证计算，不用于报告真实市场价格/成功率。
- 源测试核对官方Binance文档字段，真实生产来源适配必须由后续独立AI Review、前向采集、准确时点原始响应和真实验证才能引用；本期不开放任何新服务、automation或邮件。未来`2026-10-14`、`2026-10-28`、`2026-11-11`三段七日OOS尚未完成。
- 历史`D1_G3=REJECTED`、`REAL_NET_EXECUTABLE=UNKNOWN`、`INDEPENDENT_OTHER_AI_REVIEW=NOT_DONE`、`MONSTER_DEPLOYMENT=NO_GO`、`GMAIL=OFF`、`AUTOTRADE=NO_GO`、`FRANK=UNCHANGED`。

本阶段的价值是冻结后续真正能核对「能否买、卖、买卖多少」所需的证据门槛。**不能**把它解释为Stage79模型通过或产生了新的交易机会。
