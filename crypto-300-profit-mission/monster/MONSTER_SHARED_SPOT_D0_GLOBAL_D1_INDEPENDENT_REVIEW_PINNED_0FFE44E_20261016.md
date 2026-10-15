# 发送给另一个独立 Codex/Claude 的审核任务：Monster真实共享Spot D0+原生产全局D1，严格只审核固定SHA

**仓库** https://github.com/lxxlx2/ChatGPT_mission_record
**原唯一 Draft PR** https://github.com/lxxlx2/ChatGPT_mission_record/pull/30
**开发分支** `research/monster-v4-local-discovery-20261010`
**待独立审核唯一代码/测试/CI固定 SHA** `0ffe44ece8644443757b5f6ac0cd19e0f5d1999e`。后续机器数据或文档 Git 提交可以用于外部校验，但不能把PR当前HEAD当成新代码审核SHA；最好采用detached worktree。上一局部Stage153 `Codex APPROVE@4553cb6...`、Stage152 `APPROVE@71a04140...` 均是旧范围，**不自动批准当前共享D0引擎**。审核身份准确底层模型字符串无凭据写`UNVERIFIED`。

## 背景和本次真正业务目标

原Stage26按758币逐币各一个SQLite回放168h产生1132 WATCH、826 SETUP；Stage28只拿Stage26已经得到的WATCH到达时刻注入**一个共享SQLite**后运行原生产D1，产出1128队列、123 LATE、828 SETUP，2026-02-06 00:36 UTC历史98同刻WATCH中91 LATE/7 EVALUATED。这不等于同一全市场真实D0扫描曾完成；旧Stage137虽然调用原D0，也仍每币一个数据库/不同期货Stage80研究规则。本轮冻结协议[见Git](MONSTER_NEXT_SHARED_D0_TO_D1_FULL_SPOT_MARKET_CAUSAL_REPLAY_FROZEN_20261016.md)，事前先于任何新代码；禁止把旧1132历史WATCH填入新D0，也不许隐瞒缺失资料。

本轮新模型研究的正确称谓是 **“共享Spot原生产D0/全局D1核心实现 + 全源资格审计 + 官方二币实际同SQLite源验证”**，**不是完整758全市场168小时共享回测DONE，也不是策略成功**。

## 请按仓库AGENTS及Monster规则核查这些文件

- `crypto-300-profit-mission/monster/AGENTS.md`
- `crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md`
- `crypto-300-profit-mission/monster/MONSTER_MANUAL_COLLECTION_AND_DEVELOPMENT_CADENCE_20261014.md`
- 原冻协议 `crypto-300-profit-mission/monster/MONSTER_NEXT_SHARED_D0_TO_D1_FULL_SPOT_MARKET_CAUSAL_REPLAY_FROZEN_20261016.md`
- 新代码 `crypto-300-profit-mission/local-agent/scripts/monster_v4_shared_spot_d0_d1_original_core.py`
- 源资格 `crypto-300-profit-mission/local-agent/scripts/monster_v4_shared_spot_stage26_original_source_census.py`
- 新回归测试 `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_shared_spot_d0_d1_original_core.py`
- 新CI `.github/workflows/monster-v4-shared-spot-d0-global-d1-official.yml`，确认**无schedule**、不改Frank/旧生产代码/Stage99/真实Gmail/交易；
- 原Stage26/28/137源、原Stage26 36 Artifact双SHA manifest、上述新真实数据报告，**不能仅看报告就宣布批准**。

## 必须验证的真实数据和CI

[GitHub Actions #38809121359](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38809121359) 已经`completed/success`，触发SHA **`0ffe44ece8644443757b5f6ac0cd19e0f5d1999e`**，`5/5 Jobs PASS`，Ubuntu/macOS Python3.12各 `13/13 unittest PASS` + py_compile。第一源Job从原 Stage26 固定manifest列举的**全部36份**历史GitHub artifacts真实按ID下载，各自核对原 ZIP SHA和内层 JSON SHA，用真正4548原始Symbol-Day而非历史报告截断统计6日期的全部758名单、2719完整分钟、1829不完整；期间保存每个日期完整758币的真实身份及来源状态，不允许减少分母。全部758实际字符串组成的Roster SHA256 `cea49caae4245dad910cc096bdaea953387bdfea64667a49916756d12297074a`。源Census Git blob `a558766de7514a87a4d2bca7555d4ac37efbb086`。

第二真实源Job从 **data.binance.vision官方Spot1m ZIP+CHECKSUM** 经原Stage26已审reader取得 BTCUSDT/ETHUSDT 2026-02-03 至 2026-02-12的各**10份**完整日数据，所有日SHA256和原始验证日期已逐币放入[机器证据](evidence/monster_shared_spot_real_BTC_ETH_20260204.json) blob `8b58e95bb2758c27e8ab08a875f7a50970fb5c2f`。两币各12960分钟、每币3360个3m tick缓存、共6720 source symbol-tick，原共享SQLite一次全市场观测+一次原global D1评价每tick，真实该日期两币无WATCH和SETUP（**零信号控制，非原98爆发正例**）。源机器`shared_replayer_sha256=9d09626f7425524bd374d3295c36e4e5a81f66347e4e7db89246387532314404`、`trigger_commit_sha=0ffe44e...`、`true_full_758_replay=false`。CI归档Job实际打印 `MONSTER_SHARED_SPOT_REAL_ORIGINAL_SOURCE_PROOFS_PINNED_GIT_PASS`，Git写入前分别对4个源/test/workflow Git blob重新校验与固定SHA相同。请独立核对这些全部真实运行日志、下载回执及源 SHA，不要直接信我的声明。

## 必须独立审的源码、因果和安全风险

1. **真实原生产调用**： `monster_v4_shadow.py` 的 Git blob必须是`bc958b3d90a8a52afa51515cb53f7e5fafaffaaa`；对每个完整global tick **一次**`observe_snapshot(db,"spot",tick,全部可见币ticker rows)`，随后 **一次**`process_queue(limit=8)`，同一个SQLite持久化不重置。不能在共享代码里调用独立新评分器、不能每币开一个SQLite或拿Stage26 WATCH结果充当共享信号。
2. **来源严格因果**：原官方1m历史必须恰好12960连续bar、24h预热、报价额来自过去1440个已闭合分钟，1m信号price为最后已闭合CLOSE，原5m同一原函数严格仅在end_ms小于观察时钟返回，**禁止未闭合bar、未来成交额/价格泄漏**。官方十日ZIP/CHECKSUM的每币每天原SHA应保存且每个真实源日顺序与冻结日期一致；缺1min、伪造一天SHA、错日期、缺一个币任何tick时模型全部fail closed，不输出本该是758的截断结果。
3. **原758分母**：从原36份源ZIP+内部JSON独立复算 **4548=758×6**、日期完整分钟合格`433,440,445,438,478,485`（合计2719）；缺失`325,318,313,320,280,273`（合计1829），必须保持CENSORED并说明source现况与旧Git研究范围。新`full`标记不能只看`len==758`，还要与源锁定的真实758 roster一致；评估接口能否被任意人工`frozen_verified_roster`绕过，若能影响实际输出可信等级，请记录缺陷与最小修复建议。不要只推荐增加API限额或改阈值来掩盖源缺失。
4. **两币真实试运行与合成正例区分**：BTC/ETH真实20日源回放零WATCH，是正常控制组而不是D0前瞻盈利证明。合成AA/BB能独立核对原Stage26逐币`WATCH_EARLY`发生时钟与新共享原D0一致，且原D1才共享；请用新增13个单测与自拟负例核查过期、重复符号、来源篡改、未来5m，确认新真正98币源实验尚未做，不把旧91 LATE的数当作新D0发现。
5. **实际可用性界限**：冻结为758个历史Spot USDT币；仍不含完整真实PIT listing、真实HTTP ticker原响应和Spot+Futures共同竞争、真正真实下单成交深度、净收益、用户Mac测试、邮件实际送达。来源缓存是本地研究中间文件，不能改生产SQLite/Frank或默启任务。真实数据库WAL只读可能更改SHM索引（上轮Codex对Stage153已实测），本轮新的输出不会覆盖输入生产DB。
6. **下一高价值实现评价**：判断能否用完整源已核验的2026-02历史445个币重建同SQLite共享D0/D1，与同**445名单**旧Stage26/28结果对照；这只能叫`SOURCE_COMPLETE_SUBSET`，不能称758全市场完成。无实测官方源不得以旧WATCH注入替代。

## 审核交付

请给出审核者身份及精确模型版本（不能核验写`UNVERIFIED`），**唯一SHA `0ffe44ece8644443757b5f6ac0cd19e0f5d1999e`**，实际运行单测、双SHA官方/历史来源是否真的自己重验及其证据，对P0/P1/P2逐项文件行号/复现步骤/业务风险和建议，在 `APPROVE | REQUEST_CHANGES | BLOCKED` 中明确独立结论。**即使给APPROVE，也只限双币实验代码与原36源资格核验**；Full-758全市场因真实来源1,829不完整且高压445未共享回放仍未完成，G0 PARTIAL/G1 NOT_SCORABLE/G2/G3 NOT_PASSED/G4 UNKNOWN/G5_RELEASE NOT_PASSED/G6 NO_GO，**NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE**。
