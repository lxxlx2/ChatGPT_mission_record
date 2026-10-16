# 发给独立 Codex/Claude：Monster Shared Spot D1同时间戳坏K线重试污染P2最后复审

**唯一待审代码SHA** `1154e97a25648dbf58c181be62076e4c1d406dde`。请使用detached worktree固定commit，不把后来CI机器证据或文档提交的PR HEAD当待审源版本。
- 仓库：https://github.com/lxxlx2/ChatGPT_mission_record
- 原Draft PR：https://github.com/lxxlx2/ChatGPT_mission_record/pull/30
- 分支：`research/monster-v4-local-discovery-20261010`
- 上轮独立Codex：`REQUEST_CHANGES@6e2897c4602ce554b57634fe05d25e7244068316`；该轮旧3P1工程关闭+36原来源 ZIP/JSON双SHA、20份BTC/ETH官方Spot日1m ZIP及CHECKSUM独立实际复核成功，但一个P2未关。审查者底层精确模型型号`UNVERIFIED`。
- [事前冻结的单个P2源码修复范围与预期测试](MONSTER_SHARED_SPOT_D1_CANDLE_CONTENT_FAIL_CLOSED_P2_FIX_PROTOCOL_20261016.md)，提交先于本轮代码。
- [本轮源头复现、修复逻辑、22项CI及来源固定证据](MONSTER_SHARED_SPOT_D1_CORRUPT_5M_CODEX_P2_REAL_PROD_QUEUE_FIX_AND_CI_20261016.md)，仅作自述，**请自行实测确认**。

## 上轮阻断问题：须独立原样重现并确认新旧代码差异

原失效路径：Stage26合成1m会产生WATCH=1、原生产真实D1 `completed=1,late=0`；在历史SQLite `closed5m_source`只把WATCH后首次评价所读的一根5m `HIGH`改为字符串`"0"`，`end_ms`和开/收盘时钟、SQL总行数完全不变。旧`6e2897c`只检查8条+结束时钟，新数据仍进入原`monster_v4_shadow.process_queue`。冻结原`evaluate_closed_5m`抛`ValueError:INVALID_HIGH`，被生产retry吞掉，研究最后错误输出`completed=0, LATE=1`；所以仅检查时钟的原20测试无法发现。

修复版新增源 `crypto-300-profit-mission/local-agent/scripts/monster_v4_shared_spot_d0_d1_original_core.py`中`verified_closed_5m_for_original_d1`：在调用**原未修改的`process_queue()`**前，对reader的8条缓存K线逐条校验JSON长度、UTC5m开盘和收盘正确性、闭合时钟连续且不含未来、finite Decimal和正数OHLC、价格包络、有限非负volume、正quote，并重用原production`evaluate_closed_5m`作最后同规则特征预核。解析/数据/算法不能成立则**抛`RuntimeError SHARED_SPOT_ORIGINAL_D1_SOURCE_INVALID_CANDLE`并传播中止研究**，不能被原production`ValueError`重试捕获、不生成错误机器状态，不改变老`monster_v4_shadow.py`或真实Mac。注意合法官方5m quote=0虽可能代表无交易，但冻结原生产D1需要positive CLOSED_QUOTE，此时研究必须标为**无法评价/中止**，而不能把它冒充原可用信号或任意归因伪造数据。

完整新增测试文件`crypto-300-profit-mission/local-agent/scripts/test_monster_v4_shared_spot_d0_d1_original_core.py`：
- `test_20_real_production_queue_high_zero_same_clock_is_fatal`：**严禁mock`process_queue()`**，先复算正常基线，更新原SQL一根candle HIGH=0（其余字段、时间戳和记录行数不变），再实际完整3360轮研究，要求明确`RuntimeError`而非错误LATE；
- `test_21_cached_closed5m_shape_open_clock_nan_and_quote_fatal`：10种独立变异 HIGH0、LOW坏、quote NaN/Infinity/zero、volume负、OPEN/CLOSE毫秒错位、缺元素、JSON不可解析，恢复原record后合法路径仍需通过；原20测试继续通过。对破坏非最后一条K线、finite并非合法数值字段、Zero quote实际Source所表达语义，请自行增加最小负测以评估是否漏掉某个相同P2分支。请明确记录发现的P0/P1/P2或真正限制，而不是靠测试数量批准。

## 实际来源及CI复核

固定版真实[GitHub Actions #38835269851](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38835269851) `head_sha=1154e97a25648dbf58c181be62076e4c1d406dde`；所有**5/5 Job success**：Ubuntu24.04/macOS各`Ran 22 tests` OK及py_compile，源Job重新GitHub下载36原Stage26 artifact压缩ZIP及内层JSON、逐份SHA256匹配冻结清单、源资格758×6=4548（2719来源完整/1829缺失，六日期完整433/440/445/438/478/485）；BTC+ETH各10天真正Binance官方Spot1m ZIP+CHECKSUM、20个按日SHA与预先留在原仓库的**二次**pin匹配，真实两币单SQLite 3360 poll，WATCH=0，`true_full_758_replay=false`；证据归档日志实际`MONSTER_SHARED_SPOT_REAL_ORIGINAL_SOURCE_PROOFS_PINNED_GIT_PASS`且四源/test/workflow Git blob与触发SHA一致。证据输出的源码SHA256`23793c2ddd031cb3e31a88eb34c20bd62b52b3b3125d8f8deaffa49e8755c363`。

查新证据：
- `crypto-300-profit-mission/monster/evidence/monster_shared_spot_stage26_36_source_census.json`
- `crypto-300-profit-mission/monster/evidence/monster_shared_spot_real_BTC_ETH_20260204.json`
- 758二次冻结名单`monster_shared_spot_stage26_original758_secondary_freeze_20261016.json`、BTC/ETH20每日SHA二次固定文件位于同一个`monster/evidence`目录。

如果没有权限获取GitHub original artifacts或无法联网下载Binance官方日ZIP，请写`UNVERIFIED`而不是口头声称自己重复下载。生产核心原SHA仍为`bc958b3d90a8a52afa51515cb53f7e5fafaffaaa`，Stage152/153各自旧固定APPROVE局部不变。严禁改动Frank、Stage99、Mac、本地生产SQLite、Gmail、交易或merge。

## 审核交付

审核者、精确底层型号（不可独立确认写`UNVERIFIED`）、**唯一代码SHA`1154e97...`**、本地实际运行22项与独立故障注入/日志、来源证据核验等级、负例新旧差异、是否真正闭合唯一P2、额外P0/P1/P2和固定行号、最终`APPROVE|REQUEST_CHANGES|BLOCKED`。即便APPROVE也只代表该源码Bug和旧双币研究范围，**445历史高压SOURCE_COMPLETE_SUBSET并未跑；全758不可支持、交易实际盈利未知、Mac/邮件仍NO_GO**。所有`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`、`G4 UNKNOWN/G6 NO_GO`继续。
