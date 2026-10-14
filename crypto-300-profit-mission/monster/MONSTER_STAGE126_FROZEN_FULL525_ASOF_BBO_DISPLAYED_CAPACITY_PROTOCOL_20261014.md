# Monster Stage126：全市场 BBO 可见容量主线预注册协议

状态：`FROZEN_BEFORE_NEW_CALCULATION`，2026-10-14 Asia/Bangkok。仅原 [Monster PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。读取已经归档的 Stage123 实际完整市场数据，无网络采集、无新的定时任务、无交易、无 Frank / Gmail / Stage99 改动。

## 决策问题

Stage125 已确认 525 个 USD-M 活跃 USDT 永续中，跨场所 Spot 身份仍不能通过 symbol 文字机械推定。Stage119 表明历史 824 个 D0/D1 无有效实时真实深度或双边成交证据。Stage124 已证明 525/525 完整真实 Binance 结构化 ticker+BBO+mark，但只统计价差，未核对买卖**数量**。这一阶段补足全市场容量和广度诊断，避免把巨额滚动 24h 成交量等同于进场即时可获得的流动性。

## 固定输入和计算

- 只读取 `monster/evidence/monster_stage123_20261014T094824Z_manifest.json` 加八份原始 Stage123 源文件；必须重用已测试的 `monster_v4_stage124_manual_snapshot_comparison.load()` 进行全部证据文件及 927/525 分母、符号完整性、源标注检查。用户下次显式请求可换新的完整实际 manifest，但本轮不得将此结果伪装 Stage105 七日 OOS。
- 固定活跃全集：`status=TRADING`、`contractType=PERPETUAL`、`quoteAsset=USDT`，按 Binance USD-M 原始 exact symbol 保留，不自动做 crypto token 身份认证，不剔除已涨或未涨币。全部 525 个 symbol 各有一个结果行，即使 BBO 缺失、无正价/数量或源时间不合格也保留缺口。
- 按**官方 BBO 字段** `bidPrice, askPrice, bidQty, askQty, time` 原样解析 Decimal；拒绝 NaN、Inf、负数量、交叉盘或无效时间。缺失正向挂量标记 `ZERO_OR_INCOMPLETE_DISPLAYED_SIZE` 而非把容量算 0 且写成“不可能交易”。
- `bid_display_quote_proxy=bidPrice*bidQty`、`ask_display_quote_proxy=askPrice*askQty`、`two_sided_common_units=min(bidQty,askQty)`、`instantaneous_visible_roundtrip_quote_ceiling=askPrice*min(bidQty,askQty)`。**单位为交易所 USD-M 报价的合约资产单位数量代理**；有 1000/1000000 前缀时不做单位换算，也不声称按相同币的 Spot 资产数量可转换。
- `spread_bps=(ask-bid)/(0.5*(ask+bid))*10000`；`time_lag_ms=manifest_batch_utc_ms - BBO.time`。多源非同毫秒允许负 lag，但要单独计数；`abs(lag)>60s` 记 `SOURCE_TIME_GAP_GT_60S`，不混入完整时效 cohort。Stage123 的 batch 接近 BBO 实际原始报价，不使用 exchangeInfo.serverTime 作为证明。
- 对全体有效 BBO 单独输出 spread 与买盘、卖盘、双边共同容量的 p25/median/p75/p90、min、max；一旦有删失，报告每类计数。针对**当时之前滚动** `24h priceChangePercent >=10%`、`<=-10%`、其他做分组诊断，不能选择结果为正的币作“成功率”。
- 仅展示**同一快照的可见盘口流动性上限代理**，缺多档深度、盘口在真实买卖时的持续性、实际成交、双边手续费、信号 D0 时间、现货映射、真实委托额度及后续退出证据，**G4=UNKNOWN**。不能将 top-of-book 数量、quote turnover、mark 与成交价或净收益画等号。

## 实现与验收

1. 在 `local-agent/scripts/` 下建立独立离线 Stage126 程序，纯 `analyze(snapshot)` 返回全量 525 rows、显式 invalid/missing/censored、分组指标；CLI `--manifest --out`。
2. 测试应覆盖：市场名单保留与 Unicode、Decimal 正确计价、买卖两边共同约束、时间超60秒明确删失、负数/非有限拒绝、零量不可伪造容量、完整 Stage123 八源回读以及无交易额时只作容量上限，不声称任何买入。
3. 用 GitHub Ubuntu/macOS **offline** CI 运行合成测试和**真实已归档 Stage123** 的 525 完整全市场重算。保存机器审计结果/关键摘要到原 PR30，不将 CI success 等同策略验收；若任何原源缺失或测试失败，立即保留失败事实并修复后复验。
4. 冻结 Stage77 G0–G6、Stage118 `REJECTED`、旧样本 519/305 的结果不变。独立外部 AI review、真实七日前瞻、用户指定订单金额、实际 G4 买卖净价与 Mac 部署都不因 Stage126 离线分析自动放行。

`STAGE126_PROTOCOL=FROZEN`; `STAGE123_SOURCE=ARCHIVED_8_FILES_927_525`; `STAGE118_MODEL=REJECTED`; `G0=PARTIAL`; `G4=UNKNOWN`; `REAL_BUY=NO_GO`; `INDEPENDENT_OTHER_AI_REVIEW=NOT_DONE`; `MONSTER_DEPLOY=NO_GO`; `FRANK_UNCHANGED`; `NO_NEW_SCHEDULES`.
