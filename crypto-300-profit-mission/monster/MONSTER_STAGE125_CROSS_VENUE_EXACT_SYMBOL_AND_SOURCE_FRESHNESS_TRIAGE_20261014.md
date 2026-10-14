# Monster Stage125：Spot 与 USD-M 跨场所标的可交易性初筛及数据时钟证据边界

日期：2026-10-14，研究仅限原 [Monster PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。本轮直接调用已连接的 Binance 公开只读 `get_futures_usds_exchange_information({})` 与 `get_spot_exchange_information({})`，仅作**当前返回的结构化交易元数据**诊断，不是新的 Stage123 四源行情批次，不创建定时器，不改变原 Stage79/118 模型，不产生交易执行建议。

## 为什么进行此项诊断

Monster 真实可执行性 G0/G4 要求区分「合约异动」与「现货可以买」。原 Stage119 824 个 D0/D1 历史事件没有一笔获得完整可成交净收益证据；Stage120 有 Binance USD-M 交易规则解释器，但尚不能证明同一基础币在 Spot 上的真实可交易路径，也不能自行假设 `1000`/`1000000` 前缀的单位换算。这是主线发现→执行间的重要断点。

## 实际来源与证据限制

| Binance 结构化来源 | 本次返回字段 | 数量 |
| --- | --- | ---: |
| USD-M `exchangeInfo` | `serverTime=1791968914197` (2026-10-14T09:08:34.197Z) | 927 全部条目；525 个 `TRADING+PERPETUAL+USDT` |
| Spot `exchangeInfo` | `serverTime=1791973441878` (2026-10-14T10:24:01.878Z) | 3725 全部条目；761 个 USDT 现货对；其中 507 标记 `TRADING` |

两边嵌入式 `serverTime` 相隔 **4527.681 秒（75 分 27.681 秒）**。**Binance exchangeInfo 内嵌 serverTime 不能独立证明客户端真实收取时间**，没有原始 HTTPS body、成对官方 /time 证据、原子同时观测或者完整原始源的 Git 归档。因此下述比对仅为 `STRUCTURED_CONNECTOR_METADATA_DIAGNOSTIC_PARTIAL`，严禁记成当前同步真实 Spot 成交、G0 已证实、独立 OOS 或 Stage97 原始快照。此衍生统计未归档完整双源 raw JSON，独立逐字段再现必须重新获取真实快照；不要对时效性做未经证明的升级。

## 使用完整返回符号数组进行精确配对（只用于诊断）

精确条件：以 USD-M 中 525 个活跃 USDT 永续为固定分母，对 Spot 所有 USDT 交易对按 **完整原始 symbol 字符串** 一对一 join；Spot `status=TRADING` 且 `isSpotTradingAllowed=true` 才列为 **结构上允许的 Spot 对候选**，这不意味着实际盘口、币种身份、数量精度、订单费用和成交已验证。没有任何一项使用涨幅榜或历史赢家筛选。

| 固定分母分类 | 数量 |
| --- | ---: |
| USD-M 活跃 USDT 永续 | **525** |
| 找到完全相同的 Spot USDT symbol | **359** |
| 其中 Spot 标记 TRADING 且允许现货交易 | **357** |
| symbol 完全相同但 Spot 不满足上述状态 | **2**：`XMRUSDT`、`LITUSDT` |
| 完全不存在同名 Spot USDT symbol | **166** |
| 归类求和 | 357 + 2 + 166 = **525** |

**166 个缺少同名 Spot USDT symbol 绝不能被自动分类为资产没有现货交易。** 如 `1000PEPEUSDT`、`1000SHIBUSDT`、`1000BONKUSDT`、`1000000MOGUSDT` 的期货 symbol 含合约数量前缀，Spot 若存在可能使用另一个不同单位/代号；也有真正仅合约或已退市资产以及需要在其他 quote 交易对转换的情况。精确 symbol 相同也不自动证明合约对应相同底层 token、相同单位和提现链。

源返回 525 个 USD-M 活跃合约中，`underlyingType=INDEX` 的两个是 `BTCDOMUSDT` 与 `ALLUSDT`，Binance 自身标签不能单独证明当前标的为独立 crypto token；前缀合约及基础单位仍须依据官方现货/期货合约说明逐个确认。

## 下一阶段最有价值的实际开发步骤

1. 在原 Monster 分支实现研究用只读 source-cohort join，将 USD-M symbol、baseAsset、pair、底层指数或合约单位/乘数，与 Spot baseAsset 和各 quote 市场分离存档，不再拿 symbol 字面同名充当资产级市场覆盖；所有不明量纲明确 `MULTIPLIER_UNVERIFIED`。
2. 在**同一真实观察批次**获取可核验的 Spot+USD-M 元数据和 BBO/深度，验证当时交易状态、时间来源及可能的有效交易路径；若只有内嵌 exchangeInfo.serverTime，则 `ASOF_PROOF_PARTIAL`，绝不能推断 D0 时现货可买。
3. 原 D0 519 及 D1 305 继续保留原身份缺失和 Stage118 `REJECTED`；不能用今天 Spot 是否开放倒填它们的历史交易状态。将真正可确认的身份/单位样本分级记录，再研究首次早报实际成交成本/退出价格。
4. 用户下一次手动正式采集仍遵守 Stage124 冻结 T0/T1 比较器的四源全市场批次，不把本次元数据诊断算成完整 T1。新 OOS G1/G2/G3、真实 G4 净收益和另一 AI Review 仍未完成。

## 事实与门禁

`SOURCE_METADATA_RETURN_COUNTS=OBSERVED_CONNECTOR_STRUCTURED`;
`DUAL_VENUE_COHORT_EXACT_SYMBOL_JOIN=DESCRIPTIVE_ONLY_525`;
`ASOF_CROSS_VENUE_SYNC=UNVERIFIED`;
`INDEPENDENT_ASSET_IDENTITY_AND_MULTIPLIER_G0=PARTIAL`;
`TRADEABLE_SPOT_EXECUTION_AND_NET_G4=UNKNOWN`;
`STAGE118_HISTORIC_MODEL=REJECTED`;
`NEW_TRUE_OOS=NOT_DONE`;
`EXTERNAL_OTHER_AI_REVIEW=NOT_DONE`;
`MONSTER_DEPLOYMENT=NO_GO`;
`GMAIL=OFF`;
`FRANK_UNCHANGED`;
`NO_NEW_SCHEDULES`.

2026-10-14 用户 Mac 截图实际给出三个 `STOPPED_AND_PLIST_REMOVED`，详见长期节奏文件；本报告没有访问用户 Mac，也未重新启动任何 Stage99 服务。
