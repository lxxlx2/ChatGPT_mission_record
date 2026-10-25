# Monster ADR-005：11月 Spot 官方 1m → 原 D0 / 固定 RBTC D1 输入适配，70 项 CI 通过（2026-10-26）

**交付类型：实际代码与集成测试**，不是无数据计划；`RESEARCH_ONLY / REAL_NOVEMBER_T0_NOT_COLLECTED / EXTERNAL_REVIEW_PENDING / G6_NO_GO`。

## 1. 已完成上一轮 Codex 闭环

用户带回Codex主代理（型号UNVERIFIED），Mac macOS27.0.1 arm64/Python3.14.7、detached只读固定SHA `08340771a46e37856bad0b2b58cc4bdc97f37813`，确认BTC基准来源漏检P2 **CLOSED / APPROVE**，独立执行T0 14、日源10、score20共**44 PASS**；另独立合成5种BTC缺档/不在T0/恢复/基线/仅未来GT缺失后证明原D0与RBTC D1来源分开就绪。真实Artifact12615773413逐个三窗复算相同，原Git Blob不变。**仅该BTC source-admission局部批准**；不能把其APPROVE直接升级到本轮新的minute tape代码或整个Monster。

已[单独归档Codex原APPROVE](MONSTER_ADR005_BTC_SOURCE_SCORE_CODEX_APPROVE_20261026.md)。

## 2. 为什么新增独立November Spot tape而不复用October Spot511

旧`monster_v4_spot511_d0_d1_tape.py`正确复用Stage166验证，但硬编码**2026-10-16..24九天**、原511 T0分母与3m复查起点；不可直接冒充2026-11-02/11-16/12-01三个冻结样本外窗口。本轮在其原D0/D1数学接口基础上新增只读**真实已验证原文件适配**：

- `local-agent/scripts/monster_v4_adr005_forward_verified_minute_tape.py`，固定Git源码Blob **`bd540a8656805f6d036dd84776d950fe1399758c`**；`local-agent/tests/test_monster_v4_adr005_forward_verified_minute_tape.py`，测试Blob **`b5e5b3da28693bf00f4ae1ccb473763e8dafcdb0`**。
- **固定待独立代码审核SHA：`957a04e2f715bb1e376218021b75b99d76a01e19`**；此后文档SHA不替代固定代码版本。

### 真实可执行接口

`run(start,asof,source_zip,receipts,publisher_root,symbol,tick_ms)`先运行已经独立批准的`score_admission.run()`，每次原样重新检查6路Binance Spot T0原HTTP原始ZIP/回执/SHA与窗口前微秒时间，然后通过Stage166核对新T0原名单每个symbol×15UTC日官方ZIP/CHECKSUM来源账本和BTC独立来源依赖。之后选**一个原T0候选symbol与同期BTCUSDT**构建只读价格输入；输入早已被准入只是条件，适配器仍会**再次打开并逐日重新验算Publisher ZIP/CHECKSUM**，不会直接相信用户手工声称`VERIFIED`的行。来源根路径缺档/坏SHA/软链/未闭UTC日全部拒绝；窗口本身与冻结UTC3m栅格之外的tick拒绝。

`VerifiedForwardSpotMinuteTape.original_d0_context(tick_ms)`严格重建 **[T-24h,T)** 共1,440根已闭合1m交易额代理、最后一个已闭合一分钟收盘价，输出与未修改的`monster_v4_shadow.observe_snapshot`相容的`symbol,lastPrice,quoteVolume`。**它是后来官方分钟数据重建的代理，并非当时真实API返回的24h ticker或事件时点可用时间**。

`six_closed_5m(tick_ms)`对t时已闭合30分钟内的每5根真实分钟OHLCV求开/高/低/收、成交量、quoteVolume，返回**连续六根精准UTC5m收盘**原`monster_v4_shadow.evaluate_closed_5m`与固定`monster_v4_d1_rbtc15_last5_research.evaluate_research_candidate`所需数组格式。所有原观察时间、5m闭合截止和BTC时间栅格一致，不向前读未来或假补前后K线；`original_d1_fetch(spot,symbol,tick)`可直接作为旧原引擎fetch回调。BTC在同T0来源名单/真实1+7天不齐时，可单独创建本币D0输入，但不会伪造BTC六根5m或RBTC D1已ready。

### 与实际原代码的集成

一个独立的**明确标记为本地合成**的实验创建AAAUSDT、BTCUSDT两币各8个UTC日、总16份Stage166格式、发行方形态合法且包含每分钟1,440根的ZIP/CHECKSUM，调用**真正Stage166发行方文件校验器**，然后：
1. 在两个UTC3m时点构造AAA/BTC的`lastPrice + quoteVolume`，原模型`monster_v4_shadow.observe_snapshot()`直接在隔离的**内存SQLite**中运行，合成AAA首个baseline后第二轮上涨>5%触发 **1条原`WATCH_EARLY`**。这证明输入与原D0实际函数形状兼容，**绝不作为真实前瞻WATCH事件**。
2. 用同一合成源得到币+BTC相同UTC的六根已闭合5m，实际调用`monster_v4_shadow.evaluate_closed_5m()`和预注册研究比较器`evaluate_research_candidate()`，无BTC缺档/未来5m读入，结果仍`OFFLINE_RESEARCH_ONLY_NOT_BUY`。
3. 单独测试少一份BTC官方ZIP、某日ZIP篡改、完整最后一日结束前**1微秒**、非UTC3m时点、错误场所/非原T0候选/BTC作为研究目标、BTC缺位只能建D0输入不能建研究D1。
4. **此处并未执行整个7日×全市场原D0事件扫描、完整D1 FIFO8并行队列、真正未来2×标签或G1/G2/G3回归。** 上述属于下一步主线。未把合成事件混入旧研究SQLite或真实候选名单。

## 3. 实际 Actions 和 Artifact

- [首次 Actions #40239481606](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40239481606)：开发中FAILED，是本轮合成测试夹具的`datetime.combine(day,datetime.min.time)`漏掉`()`，导致7个测试错误；已修复且保留真实失败事实。
- [**最终 Actions #40239537298**](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40239537298)：**SUCCESS 70 PASS**，固定SHA `957a04e2f715bb1e376218021b75b99d76a01e19`，Ubuntu Python3.11；具体T0 14 +官方日源10 + BTC/score20 +本轮1m桥8 +原D1比较器18，总数**70**，所有组0失败。
- 真正GitHub Artifact `12616031265` `monster-adr005-future-verified-minute-input-no-pit`，本会话已下载并用原生zipfile CRC、三份JSON解析核验，ZIP SHA256 **`c4530440838dc0fdfbdd3eb41246020c293aafd90f932b0b41449a958e58a24c`**。三份真实报告对应冻结11-02、11-16、12-01，都是`WAITING_FOR_PRESTART_SOURCE_WINDOW`、原T0 symbol数null、研究BTC技术源就绪null、G1`NOT_SCORABLE`、G6`NO_GO`。**报告没有宣称已采集或执行真的未来原D0/D1引擎**。

先前独立批准的T0/day`b2512a393594254633c371a6e576dcec001aa009` / `9250a815ab80bc3335800b8cc90d2f5097bae1fd`，原D1 episode`d7afa1053f82fb5c6b13b91ef41d0836e4ca8094`、D2微秒`c80dc799074e63230d88ebaf81bf573a870b91e1`原代码Git Blob保持未变；受限批准的score BTC修复源码Blob`1686bfbe0684d0ba47ea527715850977fcad12d7`亦未改。

## 4. 需要新一轮Codex独立增量复审

在独立detached只读worktree固定 **`957a04e2f715bb1e376218021b75b99d76a01e19`** 审核相对用户本次APPROVE `08340771a46e37856bad0b2b58cc4bdc97f37813`之后的新增内容，**请只对本轮新1m桥源码/测试/单次workflow批准，不替换移动PR HEAD**。

复审必须分别运行：
```sh
PYTHONPATH=crypto-300-profit-mission/local-agent/scripts python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_adr005_forward_spot_t0_gate.py -v
PYTHONPATH=crypto-300-profit-mission/local-agent/scripts python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_adr005_forward_spot_daily_gate.py -v
PYTHONPATH=crypto-300-profit-mission/local-agent/scripts python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_adr005_forward_spot_score_admission.py -v
PYTHONPATH=crypto-300-profit-mission/local-agent/scripts python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_adr005_forward_verified_minute_tape.py -v
PYTHONPATH=crypto-300-profit-mission/local-agent/scripts python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_d1_rbtc15_last5_research.py -v
```
独立攻击分钟越界（`t=00:03`只能读到`T-1m`、最后一根完整5m）、跨UTC午夜、伪造score report/原T0来源、BTC缺观察/不在T0、提前读UTC未闭日或未来GT标签、日源SHA/软链、原D0完整人口扫描约束。实际核对新Artifact `12616031265` 与旧真实三窗无源报告合理一致。明确`ValidatedIssuerData != PIT_AtActualTick`。如果发现任何P0/P1/P2，请给具体源码行与可重复反例；输出`APPROVE|REQUEST_CHANGES|BLOCKED`、固定SHA、真实运行测试/环境/G0-G6。

## 5. 安全与待完成下一主线

`G0 PARTIAL / G1 NOT_SCORABLE / G2 UNKNOWN / G3 NOV NOT_SCORABLE, OCT EXPOSED_NOT_PASSED / G4 UNKNOWN / G5 NEW_NOVEMBER_MINUTE_TAPE_REVIEW_PENDING / G6 NO_GO`。没有任何真实11月原盘口/分钟来源、全体候选回放、G1/G2/G3可用统计或账户交易。**NO_MERGE / NO_DEPLOY / NO_MAC / NO_AUTOMATIONS / NO_GMAIL / NO_TRADES / NO_NEW_RPC**，Frank不动。