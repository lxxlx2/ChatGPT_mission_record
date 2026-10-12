# Monster Stage97：冻结前瞻时点的 Binance USD-M 一次性原始完整市场快照采集

日期2026-10-13 Asia/Bangkok | 原Monster Draft PR #30。

## 为什么必须修正Stage91

Binance官方[USD-M REST Market Data](https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data)在`GET /fapi/v1/exchangeInfo`的`serverTime`说明中明确写有“ignore please”，另设`GET /fapi/v1/time`才是正确的服务器时钟。Stage91初版用`exchangeInfo.serverTime`判断鲜度会错误拒绝真实官方响应，因此Stage97实施前已修正：保留exchangeInfo整包raw和SHA，不将其内部serverTime当作时间见证；用**分开的前后两次 /fapi/v1/time 原始响应+SHA**和GitHub runner实际采集时间给出官方时钟一致性证据。

## 锁定时点、脚本及安全边界

- 三个快照的唯一合法开始为2026-10-14、10-28、11-11 UTC06，每个仅接受开始前15分钟内、且不晚于UTC06的**真实HTTPS原始响应**。不使用从未来补抓的名单，也不把旧900币名单当点时全市场人口。
- 一次性采集脚本必须对`fapi.binance.com/fapi/v1/time`（采集前）、`fapi.binance.com/fapi/v1/exchangeInfo`、`fapi.binance.com/fapi/v1/time`（采集后）顺序获取原始UTF-8 HTTP响应，写入完整响应raw，SHA256，capture UTC毫秒、GitHub run id/commit和响应URL。时钟差异/响应不一致、超时、越过窗口开始、源字段不符全部fail-closed；官方单个包的`serverTime`不用于时钟同步。
- 固定的`Stage91.freeze_universe`按保存的exchangeInfo**全量symbols**逐行生成attempt资格，不过滤未来涨了几倍的赢家。底层Crypto身份、1000等映射和窗口内新增/退市仍独立标`UNKNOWN`；获取一次开窗快照不构成七天持续市场人口覆盖。
- **不允许加计划cron、long-running Agent、Gmail、Monster/Frank生产代码、Mac服务或自动下单。** 为减少漏时机会，预先交付仅经**主动、单次Git提交**触发的GitHub CI：只有在到达允许的15分钟内、在原Monster PR分支提交带`[MONSTER_USDM_CAPTURE]`标记的commit及相应`monster_stage97_one_shot_capture_request.json`，才会进行一次网络采集；常规push仅运行纯离线测试。
- 工作流依赖GitHub runner排队：如果开始执行已晚于UTC06，则直接拒绝记录为过期，**绝不能为了CI通过回填旧日期**。GitHub workflow本身不会在未来自动运行，本阶段只准备代码；要真正产生未来时点证据，必须届时有人授权触发。即使GitHub日志见到请求，也不代表真实投递或是完整市场Crypto验证。
- 原始HTTPS采集虽有CI及官方响应校时记录，但没有额外链上/交易所签名可证明官方身份，必须称`RECORDED_REAL_HTTPS_SOURCE_WITH_RUN_AUDIT`，不称`INDEPENDENT_CRYPTO_IDENTITY_VERIFIED`。

## 后续验收

纯函数先使用合成响应测试：旧exchangeInfo serverTime不误拒、/time前后服务器时间一致、源SHA损坏或时钟超5秒拒绝、窗口提前15分钟以外拒绝、未来抓取拒绝、symbols重复拒绝。专项CI实际成功后发布具体Git commit，不预写任何真实未来市场清单、价格、2×、实际利润数字。

当前`STAGE97_REAL_FUTURE_CAPTURE=NOT_DONE`、`G0_INTRAWINDOW_LISTINGS=UNKNOWN`、`STAGE96_H1=UNDERPOWERED_IF_POSITIVES_LT20`、`STAGE79_D1_G3=REJECTED_EXPOSED`、`OOS_NOT_DONE`、`OTHER_AI_REVIEW_NOT_DONE`、`MONSTER_DEPLOY=NO_GO`、`GMAIL_OFF`、`AUTOTRADE_NO_GO`、`FRANK_UNCHANGED`。
