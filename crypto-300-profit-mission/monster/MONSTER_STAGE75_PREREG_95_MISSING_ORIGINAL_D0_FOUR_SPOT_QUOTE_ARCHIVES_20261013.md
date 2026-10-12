# Monster Stage75：原D0中95条没有同名Binance Spot USDT前一分钟成交确证——其他Spot报价对官方归档排查（价格查询前冻结）

时间：2026-10-13 Asia/Bangkok。研究仅Monster原PR #30 `research/monster-v4-local-discovery-20261010`，仍依照 MONSTER_MODULE_DEVELOPMENT_RULES.md、Mission Spec。P1与P2均REJECTED，Monster DEPLOYMENT=NO_GO。

## 数据事实、范围、目的

Stage74已在官方Spot1m+发布者CHECKSUM核验全部196个冻结的原V4第一次D0 WATCH，结果101条同名USDT前一分钟有交易、94条USDT日度ZIP为404、另1条USDT日ZIP存在但D0前一分钟无bar。**锁定后者95条**；来源为Git blob `c9002d380d0b2db786e58461579b862e7afab054`（Stage74 196条逐币正式记录），必须全部95且由原3个UTC06冻结窗口产生。每一条保留原date、symbol、原D0首次UTC、Stage74状态，绝不据新结果删币、挑赢家、换时间或改变策略。

问题：这些原期货USDT第一D0信号前一分钟有没有其他 **Binance Spot** 交易对的真实历史K线？不能仅凭同名 USDT Spot ZIP=404 断言没有现货或其他可买渠道，也不因为另一个报价对有K线断言订单簿可在当时成交。**这不是整个meme或币安全市场人口。**

## 事先锁定的全部市场检查列表和算法

- 对原symbol严格去除末尾单一 `USDT` 字面后缀作为**候选基础代币代码**（不移除NEIROETH或1000/1000000前缀，也不猜合约地址）。按严格固定优先顺序检查四个**完全同名base**的Spot历史交易对：`{BASE}USDC`、`{BASE}FDUSD`、`{BASE}BTC`、`{BASE}BNB`，**每条95原事件均尝试全部四种，共380个交易对×事件**，相同源日期可以复用已取得SHA资料。只有精确同base token代码候选；不转换1000/1000000倍期货命名，因为不经官方映射无法保证真实现货资产单位一致。
- 查的是原首次D0时刻 `t` 的**同一真实UTC日**、该分钟前一根 `[t-1m,t)`已闭合Spot1m；必须是Binance官方历史每日ZIP `data.binance.vision/data/spot/daily/klines/...` 与发布者 `.CHECKSUM`，SHA256严格等于发布者收据，Spot2025时间戳必须是微秒、严格对齐、不重复、CSV价量交易计数可信。重用Stage74已审的 `parse_spot_1m` 和 `fetch_day`，而不是自己另写一套时间基准。未取得归档只能 `ARCHIVE_404_UNKNOWN`，不能等同当时下架或所有市场无交易。存在发行者SHA但无t-1 bar、t-1 bar零交易以及有t-1真实成交分别列状态。
- 每个新的合格交易对只能说明**这一分钟Spot有真实历史成交，且候选symbol字符串一致**，不能说明该交易时点正好有可吃卖单、同一CA、用户实际交易净利润；尤其 BTC/BNB 计价量仍以BTC/BNB为单位，**不转换成USDT，也不与USDT/USDC分钟成交额直接加总**。每一条原事件可多种计价方式均真实成交；按原事件只计一次 `ANY_QUOTE_HISTORIC_TRADES_VERIFIED`，其他报价对逐条证据保留（不用新结果挑最有利一对）。
- 缺失证据和失败分开：来源真实HTTP 404、完整ZIP但前一分钟缺bar、完整真实0 trades、能核实正成交，以及发布者SHA错误/网络超时/解析错误。一旦checksum/时间/源异常即**CI fail**并报告，不能把异常当404或当负例。严禁用未来bar有无变化决定t的结论。
- 对Stage74的95条，分3个原窗口出全部4类及任一报价对正成交统计；保留原期间BTC/BNB等单独计数。历史K线ZIP通常事后发布，因此“asof”只指依据已闭合bar的原时刻数据因果性，**不表示ZIP当时可下载**。当时真实Spot listing/delisting、Alpha/DEX、CA、实际订单簿依然未知；不据此声称95条都不可买或算盈利率。

## 技术、回归、审批

新增独立Stage75脚本，通过GitHub CI先用**冻结六个案例**调试（HUSDT、PIPPINUSDT、TANSSIUSDT、TRADOORUSDT、FARTCOINUSDT（2025-03-30）、1000000BOBUSDT），不得据结果更改四个报价对名单、样本或已锁阈值。随后以3/4 shard从原95严格无重复地完整验证，保留每个95×4来源记录和逐ZIP SHA；必须再度核对Stage74旧95身份与D0时刻并完整聚合才算DONE。自测至少覆盖Spot微秒与checksum、更改未来尾部不影响t、同一个原D0多报价对不重复计数、1000前缀不自动映射、有效空分钟/404、不偷偷把价格单位按USD换算。

后续仍应调查非Binance Spot场所、Alpha、DEX/链上CA、独立未曝光窗口和真实盘口/买卖价差/深度与净收益；遵守其他AI Review→最终测试→本地验收关口。无自动交易、无Gmail、无真实通知，Frank与其他模块不修改。订单金额UNKNOWN。
