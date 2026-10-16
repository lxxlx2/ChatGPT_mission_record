# Monster 2026-02 原445来源完整成员：前32币一库真实D0 + 零成交额D1研究变体 V2

2026-10-16 (Asia/Bangkok)。源库[Mission PR#30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)继续 Draft/Open。**不是原生产D1已批准版本的业务回测，也不是全445或758币同库回放，更不是盈利模型验收。** 原有`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`、`G4 UNKNOWN/G6 NO_GO`均保持。

## 由真实SHA锁定官方source触发的阻断，而非代码性能假象

原真实first32回放，利用GHA Artifacts `12021352471` (shard00)及`12021445690` (shard01)共32币、320天的Binance官方Spot1m ZIP和同host CHECKSUM数据；2026-02原758分母中445 Stage26来源完整、313缺源。原固定Core在`ACAUSDT` 2026-02-08 04:42 UTC读8根闭合5m，04:30–04:34:59该根实际quote=`0E-8`、OHLC均`0.0038`，原production`evaluate_closed_5m`要求quote>0；上轮原core正确`RuntimeError SHARED_SPOT_ORIGINAL_D1_SOURCE_INVALID_CANDLE` fail-closed，无错误LATE，更不能直接当作伪造历史OHLC。原Codex`APPROVE@1154e97a...` 只关闭HIGH=0破坏source被误吞的旧P2，不允许擅自修改原production。

事前已Git记录[研究V2不改原核心的语义冻结](MONSTER_SHARED_D1_GENUINE_ZERO_QUOTE_SEMANTIC_V2_PREREG_20261016.md)：
- Quote正数全部交原未改`production.process_queue`评价，无任何未来K线、信号阈值和入场额外滤镜；D0共享`observe_snapshot`原函数不动。
- 合法已闭合5m quote正好0、OHLC/时钟仍合法：该轮占用FIFO每3min最多8个候选的预算，不假造成交量，不标SETUP/LATE，记录`SOURCE_UNSUPPORTED_ZERO_QUOTE`并下一轮尝试；没有完成成功评价且截止仍无法评价：终态`SOURCE_UNSUPPORTED_D1_ZERO_QUOTE`，明确是D1不可评分，并非“真实误报/盈利损失”。
- 若HIGH=0、价格包络坏、非法时间、非有限数值、负quote、bad JSON等，仍致命`RuntimeError`，不可被0特例伪装成有效source。
- D1 FIFO**严格选原队列前8且不借出slot给第9个**；若没有任何quote0，直接原完整`process_queue(limit8)`调用得到字节等价候选/events/count。出现合法0时，研究模式仅在该3min tick临时抑制第9及之后的候选，使剩余有数据的最多7个由**原未修改process_queue**一次处理，并恢复未入选队列的retry时钟。该研究运行时局部观察函数patch，在Python离线研究内部切换调用，不修改原模块源码；明确不得称“完全原生产D1”。
- 旧Stage26独立逐币WATCH必须与同一32币source真正共享D0发生UTC逐个一致，否则fail closed。原Stage28是历史WATCH人工注入，不构成本次共享信号发生验证。

## 最新源码和真实CI证据（作者自测，不是独立Codex批准）

唯一这轮完整源码+测试+workflow固定SHA **`dfceade891909bf374ce3e790f3aef33746f2938`**；原研究V2源码commit`f0e45dc08f24575ca59ef1bb2cacd20cd853e46f`改进原预实现错误：不再逐个调用`process_queue(limit1)`导致同一仍PENDING候选同tick重复选中、又恢复V2明确schema后丢失。新增两个重要负向单测commit`dfceade...`（第6测试9个同刻候选第1个quote0、第9个不可借走名额；第7测试等待合法零quote后到期必须弃评分母，不能假LATE）。**原生产`monster_v4_shadow.py`与先前独立批准的`monster_v4_shared_spot_d0_d1_original_core.py`内容未修改**。

真实[GitHub Actions #38855446302](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38855446302)：唯一触发SHA精确一致，**4/4任务completed/success**。Ubuntu24.04和macOS各`Ran 7 tests ... OK`及`py_compile`，同SHA重新从原两个GitHub Artifact下载32币×10天真实Source archive、对之前Git保存proof及每币源的SHA验证通过；源研究用完整3,360个3min tick、每tick真实32共享D0且一个共享原production SQLite，成功完成；归档Job校验研究代码/测试/旧core/旧production/ workflow Git blobs均与触发SHA一致才提交机器结果，后续当前PR HEAD前移不替代旧固定源码。

[完整机器证据](evidence/monster_feb445_first32_zeroquote_D1_research_v2_actual.json) Git blob `d741cabce2784e9e9dd2e2b549ae9013f9dd9f38`；机器`trigger_commit_sha=dfceade891909bf374ce3e790f3aef33746f2938`。

| 业务指标 | 32币历史真source+共享 D0／变体 D1 实测 |
|---|---|
| 研究轮询 | 3360次，共同SQLite，仅一次全32 D0 |
| 新真正共享D0 WATCH | **29** |
| 原Stage26相同分钟源单币D0 WATCH | **29**，逐币UTC完全一致 |
| 2026-02-06 00:36UTC 真共享D0 同时 WATCH | **7** （1000SATS/1INCH/2Z/ACA/AIXBT/ALT/APE 的USDT对） |
| 最大同一3分钟tick WATCH | **7**，**未触发每轮8个的队列容量拥塞** |
| SETUP_ACTIVE | **13** |
| INVALIDATED | **7** |
| D1真正EVALUATED候选 | **27** |
| D1真正LATE | **0**，只代表这32币本次研究 |
| D1源语义不可评价终态 | **2**，都属于ACAUSDT不同WATCH episode |
| 合法零quote占据过的D1评价slots | **10**（重复轮次，非10个币） |
| D1选取/延期 | **134 / 105**（累计次数不是独立候选数） |
| 758原历史分母 | 32真正回放、413原来源完整但本轮未回放、313原缺源/不完整 |
| 严格原D1与变体是否同语义 | **否**，旧原D1在零quote时fail-closed；变体把其分类为不可评价，务必分开报告 |
| 是否具备历史PIT/OOS/成交/净利润证据 | **否** |

新7单测包括原production未改同数据没有quote0时机器候选/events/count逐项等价、原D1遇合法quote0确实fail-closed、新变体quote0不伪造SETUP而终态SOURCE_UNSUPPORTED、同时HIGH0非法仍fail-closed、limit8上限、**9人同时排队第9人绝不可因第一人无quote而挤进来**、先前源不可评分超期非假LATE。

## 主线研发接下来（不得跳级）

1. 将这份 V2 的新FIFO封装、临时数据库掩码、审核身份与原32证据交给**另一个真实AI独立固定SHA review**；还未收到独立回执，作者不自评APPROVE。特别要求核查：临时mask是否会污染retry/stale真实排序、是否会出现正常可评价候选重复处理、zeroquote后曾经真实评价的候选截止归类是否正确、SQL异常引发缓存事务半写或源毁坏、原8-slot是否真的在高于8 WATCH并发有效。需独立复现，不用仅看7个已有测试。
2. 取得独立审查并关闭P1/P2后，在已经锁定445来源资格的28分片基础上继续官方真实source取得，最后**全部445在同一个SQLite中完整3360tick**，才能观察原98同刻共享D0实际候选和全局队列LATE。如今同时最多7，无法宣称旧91 LATE被消除。
3. 将零成交源不支持明确映射为不给BUY/不推荐，且与来源污染和可盈利策略是否真实有效分离。不能把13个SETUP转成13笔盈利交易。历史已曝光非OOS、缺313源、PIT listing、真实盘口和通知送达、Mac本地部署、Frank独立服务、G4收益评价均NOT_DONE。

**状态**：数据与代码研发可继续；`G0 PARTIAL,G1 NOT_SCORABLE,G2/G3 NOT_PASSED,G4 UNKNOWN,G5_RELEASE NOT_PASSED,G6 NO_GO`；`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`，Stage99不开，Frank不改。
