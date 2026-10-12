# Monster Stage74：196个历史首次D0的同刻 Binance Spot 实证——市场可买性第一道关口（预注册）

日期：2026-10-13 Asia/Bangkok；Monster原Draft PR #30。此合同**先于本阶段取得任何原D0对应日期的Spot官方K线与统计结果**，不改V4 D0/P1模型、不回写Stage65–73冻结档案或策略失败门槛。

## 为什么做这一步

Stage73证实2700个USD-M历史归档币日、1497份未来可评分、196个首次D0 WATCH；这些完全基于**期货**，不能断定用户当时在现货/Alpha/DEX能买入。其他AI审查M03的“真实可交易市场”仍未解决。第一步不因未来赢家筛样本：采用原Stage66固定源 blob `9eb19c22ae8d34d030ccabd7176c3cd4d2e2e3f8` 中**全部196个首次D0**，3窗口44/49/103，全部普通WATCH及P1候选一起检验；不是只拿五个事后2×赢家。

## 冻结后的待检验观察字段

- 以`(date,symbol,original_D0_first_UTC)`为不可变原始行身份；完全同名的 `symbol` 去查Binance官方**Spot**日度`1m`K线历史ZIP（`data.binance.vision/data/spot/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{UTC date}.zip`），并下载原发行方 `.CHECKSUM` 后 SHA256逐字节验证。使用对应D0信号所在的UTC日，而非研究窗第一日。多币日可重用相同symbol不同日期的来源；归档读取当前的历史数据不能冒充当年ZIP当场发布。
- Binance官方[binance-public-data](https://github.com/binance/binance-public-data)明确：Spot从2025-01-01起归档时间戳为**微秒**，要安全换算为毫秒（不接受任意向下取整、跨日、乱序、重复或非1m对齐）。允许合法历史某些日只有非完整1440条K线，**绝不填充空白分钟或把“没有bars”解释为无市场**；对每一个真实存在的bar验证OHLC、quoteVolume、交易笔数、时间以及CSV头；精确找到首次D0 `t` 之前最近已闭合且恰好为 `[t-60秒,t)`的1分钟bar。
- 事先冻结分类：
  1. `SPOT_PRIOR_MINUTE_TRADES_VERIFIED`：同名Spot官方1m`t-1`分钟bar存在、该分钟真实trade count>0且quoteAssetVolume>0。说明*过去一分钟Spot有真实历史成交*；并非当前盘口可执行、成交可买或ROI。
  2. `SPOT_PRIOR_MINUTE_BAR_ZERO_TRADES`：有已闭合分钟bar，但计数或quote为零。不能据此视为可以立即成交。
  3. `SPOT_ARCHIVE_SAME_DAY_NO_PRIOR_1M_BAR`：该Spot来源日已由官方SHA验证，但没有精准`t-1` bar，即便当天其他分钟存在也不得给当时现货已成交认证。
  4. `SPOT_DAILY_ARCHIVE_404_UNVERIFIED`：当天同名币对官方归档不存在。**不等于当时未上市或不可在DEX/Alpha买**，更不证明“整个市场无机会”。
  5. 其他源/校验错误一律`SOURCE_HARD_ERROR`且CI fail-closed，不静默当作404。
- 对具有真实Spot先前一分钟成交的signal记录当时已闭合Spot`close`、该分钟`quoteAssetVolume`、实际笔数、历史已验证日ZIP SHA、首次D0时差1分钟。禁止用该历史收盘价当成用户能以该价格买入、没有当时买卖盘和深度时不能测真实滑点或利润。历史同名USDM期货资产的计价倍数和Spot真实代币unit未确认：**不自动把1000XXX或1000000XXX合约乘除与Spot对齐**。
- 同一天同名Spot归档并未证明该时刻symbol处于可下单TRADING状态；使用的当日完整CSV自然包含未来分钟，选择时**只能**参考原D0前已闭合一分钟。禁止使用当天未来bar是否存在、未来OHLC或本次最后是否翻倍作门槛。新增失败指标如发现任何未来泄漏、原196身份发生变化、未通过SHA、使用毫秒/微秒错误、虚构成交或漏掉任何一例，就拒绝本阶段研究。
- **主线边界**：此次仅做`SPOT_HISTORIC_PRIOR_MINUTE_TRADES`，后续继续调查当时Alpha/DEX可交易路径、上市/退市全市场名单/抽样偏差和实盘盘口/净收益；绝不将单Binance Spot市场的百分比外推为全球所有meme机会或当时全市场召回。

## 验收与投递

第一步真实6例 `HFTUSDT,HUSDT,PIPPINUSDT,TANSSIUSDT,TRADOORUSDT,ACTUSDT`（ACT来自不同日期，则选2025-03-30原窗口），只用于调试数据和事实核验，绝不据其结果调百分比分组门槛。第二步同一冻结代码执行全部196候选（4个shard×49，按原身份稳定哈希散列），每个分片必须49、全部完整196去重与原日期44/49/103精确一致，保存每币来源SHA与绝对UTC前一分钟信号/现货状态，单独分三日期及每类结果。

若2025某真实符号源官方不可得，标`UNVERIFIED`，不借当前exchangeInfo编造2025历史TRADING标识。真实订单资金UNKNOWN，任何历史期货HIGH仍非真实交易收益。Stage71/73其他AI独立审查、未来未曝光市场检验、真实Spread/L2/成本与模拟交易收益仍未完成；旧P1、P2均REJECTED；Monster部署NO_GO，Gmail OFF，Frank UNCHANGED，自动交易NO_GO。
