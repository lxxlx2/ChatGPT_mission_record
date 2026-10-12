# Monster Stage74：全部196个原首次D0历史信号——Binance Spot 真实前一分钟成交验证

日期：2026-10-13 Asia/Bangkok。只研究Monster妖币主线，原Draft PR #30；**先冻结再读取现货**：[预注册合同](MONSTER_STAGE74_PREREG_196_ORIGINAL_D0_ASOF_BINANCE_SPOT_BUYABILITY_EVIDENCE_20261013.md) Git blob `0e904f41d5140a20d9bd8df4e6eb3ae83b2080e0`。真实Spot初始数据请求发生在研究合同提交之后，未按赢家或Spot是否存在反向挑样本。

## 来源真实性、时间因果及抽样范围

输入冻结为Stage66完整原2700 USD-M期货×历史日期来源 Git blob `9eb19c22ae8d34d030ccabd7176c3cd4d2e2e3f8`，原生产V4不变；从中取**全部196个真实第一WATCH**，不是只取五个历史事后2×赢家。分日期原始44/49/103，首次WATCH精确UTC及所有候选身份不变。由于输入是**期货先筛出D0**，196不等于真正全市场、也不代表任何Spot、Alpha或DEX所有meme人口。

Binance官方[公开数据说明](https://github.com/binance/binance-public-data)明确：2025年起Spot历史K线时间戳是微秒，支持日度 `spot/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{day}.zip` 和 `.CHECKSUM`。本轮真实取回每个D0同名symbol×**首次WATCH发生的UTC日期**的ZIP及原发布者CHECKSUM，逐字节SHA256校验，CSV微秒时间转换时必须整除1000且一天内、无重复/错序分钟；每条原分钟OHLC与quoteVolume/trade_count格式验证；仅使用首次D0前的**精确已收盘一分钟** `[t-60秒,t)` 判定当时存在现货成交。

相反如果ZIP为404，结果只能是`SPOT_DAILY_ARCHIVE_404_UNVERIFIED`，**不能推断当时此币在Binance/DEX/Alpha全部不可购买**；如果ZIP存在但这个前一分钟K线不存在，则只能写`SPOT_ARCHIVE_SAME_DAY_NO_PRIOR_1M_BAR`。即使先前1分钟成交额很高，也不证明该分钟末有可成交卖单、实际盘口/滑点/深度、当前交易状态或用户所能实现的利润。

## 完整实际回测与Git证据

- [Stage74源代码：预冻结original196、微秒官方源验证、因果一分钟分类、全体逐币身份对照](../local-agent/scripts/monster_v4_stage74_original196_spot_asof_prior_minute_SHA.py)。原 Stage74 设计合同 Git blob和原196的Stage66源码blob固定，禁止未来结果标签参与分配。
- [Stage74真实6例预检CI #38293800560](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38293800560)：SUCCESS；6个锁定案例中Spot已证实前一分钟真实成交2、日度归档404为4；官方SHA、2025微秒、重复时间戳拒绝、未来后缀不泄漏、合法时间和404分类通过。
- [Stage74全部196个原D0、4×49分片及全体身份SHA验收CI #38293915641](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38293915641)：SUCCESS。四个真实49行源分片全部通过，全球合并身份196/196无重复，日期仍44/49/103，100%原首次UTC不变。原始资料保留：
  - [196个逐币首次D0、Spot前一分钟历史K线及出版者ZIP SHA、4种来源分类](evidence/monster_stage74_original196_exact_asof_spot_prior_trades_source_SHA.jsonl) Git blob **c9002d380d0b2db786e58461579b862e7afab054**；
  - [真实196个总量、各冻结日分组及逐个来源SHA汇总](evidence/monster_stage74_original196_spot_trading_source_summary.json) Git blob **d7ab49a3bcb994129677e9c3b2e57df87cdc7e74**。

| 原冻结币日窗口UTC06 | 全部第一D0 | Spot前一分钟真实成交+publisher SHA | 同名Spot日归档404，仍未验证其他场所 | 当天Spot归档存在但前一分钟无bar |
|---|---:|---:|---:|---:|
| 2025-03-30 | 44 | 30 | 14 | 0 |
| 2025-06-30 | 49 | 27 | 22 | 0 |
| 2025-11-27 | 103 | 44 | 58 | 1 |
| **合计** | **196** | **101** | **94** | **1** |

101个前一分钟确有历史Spot真实成交的信号，其当时已闭合一分钟quoteVolume USDT分布：最小**11,375.24**，第10百分位约**50,541.00**，中位数**148,341.36**，第90百分位约**623,369.14**，最高**8,599,108.87**；同一分钟成交笔数中位数**1,289**。这些是分组后历史 `t-1m` 已完成K线数据**观察值**，不是真正可成交盘口深度或用户允许的订单金额。没有设定任何单笔投入默认数额，也没有用这些数字选择策略阈值。

另一项必要的历史对照：五个已验证的固定七日**期货2× HIGH**事件中，HFTUSDT的首次D0于2025-06-30 17:00 UTC，其官方Spot前一分钟资料有**413笔、57,545.96761 USDT quoteVolume、close 0.0924 USDT**；而HUSDT、PIPPINUSDT、TANSSIUSDT、TRADOORUSDT四个同名Spot当日归档均404。对HFT，Spot的close仍不是可以实现的买入成交价，更不是后续可卖出利润；对其他四个，**必须继续从官方现货/Alpha/DEX/链上映射调查当时真实可买渠道**，不能因为同名Spot找不到就称不能买。五个历史赢家是本次全196源证据完成后的辅助解读，不构成子集选择或新成功率验证。

`ATUSDT` 在2025-11-27 08:39 UTC的原WATCH当日Spot官方ZIP存在、实际该历史ZIP有600条分钟数据，但`t-1` bar不存在。该币不能被归类为“WATCH时Binance Spot已真实成交”，也不等于当时所有市场不能买。

## 结论与下一个核心步骤

**这轮发现了原策略一个实质问题：原D0的“期货有WATCH”远不能等价于Binance Spot同刻交易有明确证据。** 101/196只能归类`SPOT_PRIOR_MINUTE_TRADES_VERIFIED`，其余95必须追踪其他场所或源差异。由于196来自原USD-M币种/场所筛选，无法据此计算真正所有meme的发现率；没有某笔Spot成交与订单簿深度证明同刻可执行价格，不能计算净利润。

下一阶段主线不是再盯着极少量赢家调参数，而是先为全部**95个没有Spot前一分钟成交确证的首次D0**研究多场所交易证据来源、当时币种标识映射和真实成交路径；保留真实官方或链上身份不清的`UNKNOWN`。同时对101个已证实Spot成交的币研究当时点可得的报价/盘口深度来源、成交笔数/1m quote与执行价格的可证伪边界。必须有真正官方历史上市/退市完整分母才能从“当前归档全集”过渡到全市场评价，且不能为了填充missing强行猜CA或合约单位转换。

验收关口：`STAGE74_OFFLINE_ORIGINAL196_SOURCE_SHA_AND_ASOF_PASS`；`HISTORICAL_TRADABLE_ALL_VENUE=PARTIAL/UNKNOWN`；`REAL_EXECUTABLE_NET_RETURN=UNKNOWN`；`INDEPENDENT_OTHER_AI_REVIEW_OF_STAGE74=NOT_DONE`；`P1/P2=REJECTED`；`STAGE74_DEPLOYMENT=NO_GO`；`GMAIL=OFF`，`AUTOTRADE=NO_GO`，`FRANK=UNCHANGED`，`USER_ORDER_NOTIONAL=UNSPECIFIED`。
