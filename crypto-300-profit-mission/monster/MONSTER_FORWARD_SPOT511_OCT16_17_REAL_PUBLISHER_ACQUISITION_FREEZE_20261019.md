# Monster前瞻主线：真实原Publisher整511币10月16—17日分钟源首次获取（预冻结2026-10-19）

**目标**：从Stage166“只有4599条未提供/未来日期的来源检查清单”跨到真正的官方数据源。基于已获Codex APPROVE的原T0真实Binance Spot/USDT 511个TRADING币种及原始HTTP ZIP SHA `b47e206345c0a04b16b37c38795d726553ef83ca679f443f9fba89805483216b`，通过**一次由本分支Git push触发的手动、无schedule GitHub Actions**直接下载原`https://data.binance.vision/data/spot/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{DAY}.zip`及`{ZIP}.CHECKSUM`。本次仅两日`2026-10-16`、`2026-10-17`（明确早于2026-10-19当前日，避免误称尚未发布的18日已经可用），**511×2=1022**个分母。覆盖T0前24h回看以及10月17日截至22:06的近前窗历史，不等于完成7日前瞻。

**真实来源准入**：每个币每天同时取得独立原ZIP与配套官方CHECKSUM、以SHA256逐字节校验、ZIP内唯一预期CSV与1440根精确微秒1m K线/完整OHLC结构通过现有Stage166获审只读`validate_daily_zip`。HTTP状态404/403/429/超时、无CHECKSUM、issuer SHA错误、仅部分上市分钟不足1440与原minute异常必须分开计数并留下机器原因，**不准把缺source当0 WATCH、0收益**，更不准把合成测试冒充官方数据。目标1022真实校验通过数**不得预填**，原始1022 status全部归档；已验原ZIP/原CHECKSUM上传Actions artifact以支持未来真正D0/D1多日回放，原Git只保存每条SHA/源证明/观测时刻/状态（原始ZIP可能超Git大小限制）。Github Artifact可能过期，必须披露retention天数及对应run ID。

**运行安全**：仅只读原公开Publisher HTTPS资源，不访问用户账户/API密钥/订单，不触碰Mac、Frank、Gmail、主分支，不设ChatGPT automation/GitHub schedule/launchd，严格最多8个并发下载、每源限制20MB、最多2次网络重试，每个URL明确记录官方域名与观测时刻。实验固定上市人口是原T0 511，历史不足24h要保留`INCOMPLETE_OR_NOT_YET_LISTED`，不临时剔除不利币。当数据真正下载成功方可宣称`OFFICIAL_DAILY_PUBLISHER_ZIP_SHA_VERIFIED`，但那也不能证明7日内连续上市PIT、ticker24、同刻双边盘口或实盘盈利。

**独立资金与原已批准代码边界**：Stage165/166和已获Codex APPROVE的300U有限资金账本固定SHA`5eeee8c05cd3eaf2b52e779c22759aed2c75aa49`完全不改。源获得后在另一次用户要求继续时可从真数据顺序推进全511剩余UTC日和日内3min真实行情研究；未来全部24h退出还需2026-10-25（完整511×10=5110计划日对象），但目前绝不虚构。新源采集代码**独立审核NOT_DONE**；代码/CI成功只表示作者获取和初验。PR #30继续Draft，`G4 UNKNOWN/G6 NO_GO/NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`。
