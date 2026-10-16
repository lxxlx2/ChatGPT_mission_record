# Monster Shared Spot：Codex P2 单根5m OHLC损坏被误计LATE——修复、实测及回审

时间：2026-10-16（Asia/Bangkok）。唯一研发PR [#30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)，保留Open/Draft。原独立Codex固定审查`6e2897c4602ce554b57634fe05d25e7244068316`最终`REQUEST_CHANGES`：3个旧P1工程修复已独立核实，36个原Stage26 Artifact双SHA及BTC+ETH20个Binance官方1m day source已由Codex独立下载复核通过；唯一阻断是**闭合时间正确但K线内容损坏仍经冻结生产D1重试被吞、研究错误产生LATE**。本轮不涉及Stage152/153原固定APPROVE，也不补造历史758缺源价格。

## 事前冻结与唯一待外部复审版本

先将[本轮P2内容完整性故障事前修复协议](MONSTER_SHARED_SPOT_D1_CANDLE_CONTENT_FAIL_CLOSED_P2_FIX_PROTOCOL_20261016.md)提交Git，commit `f7275a66e66422c7ea2f59a1b37296fb76363df6`，**再**修改源和对应tests。

本轮唯一代码+测试+workflow待审 SHA：**`1154e97a25648dbf58c181be62076e4c1d406dde`**。仅改动:
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_shared_spot_d0_d1_original_core.py`，本SHA Git blob `3a9e4bbd75ff4f5ef6cd0bfe87895d932c95892c`，当前源SHA256在下述真实CI机器报告中为`23793c2ddd031cb3e31a88eb34c20bd62b52b3b3125d8f8deaffa49e8755c363`。
- `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_shared_spot_d0_d1_original_core.py`，旧20测试保留更新一项旧错误消息，新增加两项高价值测试：未mock原生产process_queue真实故障反例，及10种5m内容和格式错误的参数化校验。

**生产`monster_v4_shadow.py`的SHA原冻结不变，原生产D0/D1、原Stage26官方行情reader、workflow设置和旧Stage152/153源码均未更改**。仍无schedule、真实Gmail、Mac部署、Frank、Stage99或交易调用。

## 独立审核确切反例与修复结果

原Codex独立fault probe（用户提供）针对已发生合成`WATCH=1`、`D1_completed=1`、`LATE=0`的正常历史基线，只把本候选首次D1会读的一根5m K线`HIGH`改为字符串`"0"`，保留SQL主键、行数、完整`c[0]`开盘和`c[6]`收盘毫秒。旧源码仅核`len(candles)==8`及`c[6]`连续匹配，使数据通过reader；原生产`evaluate_closed_5m`抛`ValueError:INVALID_HIGH`，被`process_queue`的正式retry逻辑捕获，研究最终输出`D1_completed=0,LATE=1`而未报错。**历史坏来源不等于真实迟到**。

现新`verified_closed_5m_for_original_d1`在同SQLite的历史reader返回之前核验全部8根：
- JSON结构必须是恰好8项的数组，无法解码JSON本身失败；
- 开盘毫秒/收盘毫秒必须为整数、5min闭合UTC完整连续网格，close==open+299999ms、每根close<当时tick；
- open/high/low/close均为有限正Decimal、low≤open,close≤high；聚合源中的volume有限且非负，报价成交额quote有限且**正数**（与原生产`positive(CLOSED_QUOTE)`契约相同）。真实零成交额分钟若进入被选D1也**作为当前历史研究评价不可支持而fail closed**，不得误称数据伪造或正常deferred；
- 重用**原未修改生产`evaluate_closed_5m(candles,tick)`**做无副作用的特征预校验，确保还有原核心特征不合法时也先失败。
- 结构、数据、JSON或算法合法性失败转成研究`RuntimeError("SHARED_SPOT_ORIGINAL_D1_SOURCE_INVALID_CANDLE")`，**不在冻结生产retry catch范围**，向上退出研究，不能写伪正常队列摘要；不修改原生产D1的`ValueError`重试行为。

新增`test_20_real_production_queue_high_zero_same_clock_is_fatal`实际调用未经mock的`production.process_queue`并真实跑整个3360tick窗口：先断言`D0_watch_new=1,D1_completed=1,D1_late=0`；再同一个source SQLite只改初次D1读取的HIGH为`"0"`，验证行数不变和close毫秒完全不变，新整段回放必须抛指定`RuntimeError`；无法错误返回`LATE`的机器报告。新增`test_21_cached_closed5m_shape_open_clock_nan_and_quote_fatal`将HIGH=0、LOW异常、quote NaN/Inf/zero、volume负数、开盘时钟/收盘时钟错位、结构短缺、JSON损坏分别注入缓存，失败必须由reader抛研究致命异常，恢复原JSON后合法读取仍成功。旧`test_17`按新统一致命码更新，不删除原语义。

## 真实CI证据（不是作者口头自评）

[**GitHub Actions #38835269851**](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38835269851)：实际固定`head_sha=1154e97a25648dbf58c181be62076e4c1d406dde`，`completed/success`、**5/5 Job success**。原Ubuntu24.04与macOS各`Ran 22 tests`、OK、py_compile通过。外部源Job重新从原GitHub按artifact ID下载Stage26 36份ZIP并逐份对封装ZIP和内部JSON双SHA验证、Census真实758×6=4548，其中source-complete2719、CENSORED1829，六日期eligible`433,440,445,438,478,485`；另一Job重新使用原Stage26下载与校验官方Binance Spot 1m BTC/ETH各10天20份发布者ZIP+CHECKSUM，又匹配此前二次Git SHA锚点，在同一SQLite真实3360分钟快照轮，BTC/ETH零WATCH、D1无事件，并保留原758人口分母的2026-02状态：2来源已回放、443原来源完整未回放、313缺源/不完整。机器Git证据写回Job打印真实`MONSTER_SHARED_SPOT_REAL_ORIGINAL_SOURCE_PROOFS_PINNED_GIT_PASS`，归档前4源码/test/workflow Git blob与此确切触发SHA一致，未因后续PR HEAD前移而漂移。

CI自动机器存档：[36份原Stage26来源人口证据](evidence/monster_shared_spot_stage26_36_source_census.json) 新的`trigger_commit_sha=1154e97a...`；[BTC/ETH 20份逐日SHA及原共享D0/D1实测](evidence/monster_shared_spot_real_BTC_ETH_20260204.json) 新`trigger_commit_sha=1154e97a...`，`shared_replayer_sha256=23793c2ddd031cb3e31a88eb34c20bd62b52b3b3125d8f8deaffa49e8755c363`。两项机器 evidence **不是高压445币全市场真实重放**，也不能代表策略收益。活动WAL SQLite-SHM只读状态限制与此research SQLite无冲突。

## 接下来

**待另一AI独立固定 SHA `1154e97a...` 复审**；只有独立复核确认上述高为0、闭合时间保持的真正`process_queue`反例关闭、原旧P1边界没倒退、真实源记录与本SHA匹配且没有新增P0/P1/P2，才可记录局部`APPROVE`。当前只能准确写**作者已修复，22项两OS+来源CI通过，独立复审NOT_DONE**。随后回到2026-02源完整445币高压同SQLite D0→D1真实因果回放（未测）、对照2025-11完整433对照（未测）；仍没有全758历史完整source、真实PIT上市、跨Spot/Futures竞争、实际成交净利或真实报警送达。原Stage152/Stage153各自固定SHA独立批准不受影响。

禁令`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`，`G0 PARTIAL / G1 NOT_SCORABLE / G2/G3 NOT_PASSED / G4 UNKNOWN / G5_RELEASE NOT_PASSED / G6 NO_GO`；PR继续Draft，Frank/Stage99不改。
