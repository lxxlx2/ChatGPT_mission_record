# Monster Stage166 — 正式Spot T0 511全人口与未来9日官方Publisher 1m来源准入（预冻结2026-10-19）

## 目标

不等待2026-10-24T22:06Z七日窗结束才去临时开发工具。**只解决新Spot样本独立OOS的真实输入分母与原始分钟来源**，不是给511币盲目发BUY、不是重调D1盈利阈值，更不是再回审已获批的Stage165历史27次评价。真实价值在于未来只要某币缺一天档案，就不会假装它没触发WATCH或没有收益。

原始Binance Spot T0固定真实服务端时间2026-10-17T22:04:40.094Z，原正式source bytes Git `monster/evidence/monster_stage163_spot_original_http_t0_actual/source_raw_http.zip` SHA256 `b47e206345c0a04b16b37c38795d726553ef83ca679f443f9fba89805483216b`，配对`source_receipts.json`；复用已获审读端`monster_v4_stage163_spot_t0_quote_friction.load_archived()`（校验ZIP字节、HTTP response SHA、HTTPS端点、HTTP收包时间、serverTime）。**只有**原T0真实`quoteAsset=USDT, isSpotTradingAllowed!=false, status=TRADING`的**511个symbol**构成主原点集合。原另214个USDT`BREAK`不加入511，单列；中途新上市、暂停、恢复只可依据到时的真实人口变更记录归档，当前缺失标`DYNAMIC_LISTING_FEED_NOT_CAPTURED`，不声称七日全动态真PIT。

### 先冻住的数据时钟

- 窗口左闭右开：`[2026-10-17T22:06:00Z, 2026-10-24T22:06:00Z)`，**3,360个3m tick**，七日整个结束前不出完整样本外结论。要构造T0前24h滚动quote warmup，要求含`2026-10-16…2026-10-24` **9个UTC日**的官方Spot 1m原ZIP；研究范围T0完整511枚，理论文件数`511×9=4599`个。
- 每个对象的官方来源 URL 仅按`https://data.binance.vision/data/spot/daily/klines/<SYMBOL>/1m/<SYMBOL>-1m-YYYY-MM-DD.zip`格式**推导待请求位置**，它不是对可访问/已发布的声明。相邻`.CHECKSUM`需要真实下载、按发布方哈希验证后才可升级状态。
- Spot官方2025-01-01后Kline ZIP CSV的开盘/收盘时间为**微秒**，必须检查每一分钟`open_time_us`和`close_time_us=open_us+59_999_999`、完整有效字段，才允许`VERIFIED_FULL_DAY_1440`；不可按USD-M毫秒误读。partial、零成交或新停牌不能按1440完整来源静默通过，且是否仍可交易须与独立点时上市证明核对。
- 当前时刻`--asof-date`只能用于“该交易日是否已经结束”的**研究报表标签**，不改变原文件/事件UTC，不假定发布完毕，也不触发下载；当文件不存在，报告`SOURCE_NOT_SUPPLIED`，**不得误称**源不存在或者没有WATCH。已有ZIP而没有合法CHECKSUM、文件名不符、SHA错误、CSV行缺失/时间不连续都只能`SOURCE_REJECTED_OR_INCOMPLETE`，不可悄悄用近时段价或者别的venue补齐。

### 最小交付边界

先实现**无网络、无交易、无后台权限**的独立CLI读端和小型可证伪合成测试。输出Machine JSON包含来源原ZIP SHA、T0 511 symbol身份、原9个UTC日期与4599个source admission attempt以及失败原因，所有attempt不能被不完整数据算作0 WATCH、0 SETUP或0利润。给未来真实API数据来源集成留入口；不在此阶段改生产D0/D1/D2、Stage162 Fair8、Frank、Mac/Gmail或交易。

真正的源验证/未来完整OOS必须等完整9日原publisher ZIP与CHECKSUM、真实来源当时交易身份/上市变更、逐轮真实closed 1m和原研究D1规则及入退出bid/ask证据到位后才能升级。**今天预冻结并跑CI不代表已有511×9真实分钟源。**

## 不可变当前门禁

`G0_STAGE166_DAILY_PUBLISHER=NOT_DONE`、`DYNAMIC_LISTING_CHANGE_RECEIPTS=UNKNOWN`、`SPOT_SEVEN_DAY_OOS_MATURE=NOT_YET`、`G4 UNKNOWN`、`G6 NO_GO`、`NO_MERGE`、`NO_DEPLOY`、`NO_GMAIL`、`NO_TRADE`。GitHub workflow若需要，仅本分支代码显式push触发的离线研究，不准schedule/launchd/cron/ChatGPT自动任务。Stage165已独立APPROVE，不重复评审。
