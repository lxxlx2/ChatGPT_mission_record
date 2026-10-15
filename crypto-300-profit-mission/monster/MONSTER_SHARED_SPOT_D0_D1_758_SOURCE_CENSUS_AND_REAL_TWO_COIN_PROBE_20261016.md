# Monster V4 真实共享Spot D0→全局D1：36原Stage26来源双SHA人口核验、原生产共SQLite双币历史回放

日期：2026-10-16 Asia/Bangkok。原[Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)，禁止部署。**本报告是首个实际新共享D0+原生产全局D1引擎验证，不等于全部758币已完成真正全市场连续168小时回放，不等于策略通过。**

## 事前冻结及原历史材料

研发合同已在任何本阶段新代码前提交 [原冻结方案](MONSTER_NEXT_SHARED_D0_TO_D1_FULL_SPOT_MARKET_CAUSAL_REPLAY_FROZEN_20261016.md)，冻结于 `9a15080e5f75c49ca7f962f01e032539e894d1db`。上一局部审查已完成的 Stage153 仍为 `Codex APPROVE@4553cb6b18c5aaf723072d17a39f9ad92f0629c9`，并保留活动SQLite WAL模式只读可能更新SHM索引的真实限制。

**本轮唯一固定代码/测试/工作流 SHA**：`0ffe44ece8644443757b5f6ac0cd19e0f5d1999e`。源码实现、测试和真实CI已全部Git存档，但**该SHA尚未取得另外独立AI审核意见**。

新交付：
- [原D0及D1生产代码，同一个SQLite + 同一完整poll ticker输入 + 全局D1 limit8](../local-agent/scripts/monster_v4_shared_spot_d0_d1_original_core.py)，基于 Stage26 **同一份原本SHA冻结的`monster_v4_shadow.py`**，每时钟仅一次`observe_snapshot(db,"spot",t,ALL_SYMBOLS)`、一次`process_queue(db,t,source,limit=8)`，不改D0参数。
- [Stage26原36份源ZIP及内层JSON完整758名单/来源资格审计](../local-agent/scripts/monster_v4_shared_spot_stage26_original_source_census.py)，直接复用 Stage26已经建立的严格Artifact解析、双SHA核对代码，不用Stage26过去WATCH列表作为新D0运行输入。
- [共享代码13项精确负向/比较测试](../local-agent/scripts/test_monster_v4_shared_spot_d0_d1_original_core.py)：包括源码Git blob固定、两个符号共享一次全市场poll、旧逐币原D0首次WATCH时钟对照、758只允许证据齐备才可称FULL、缺失时点拒绝、官方来源十天错位/伪SHA拒绝、5m因果收盘、冷启动/完整来源阻断等。
- [新GitHub CI](https://github.com/lxxlx2/ChatGPT_mission_record/actions/workflows/monster-v4-shared-spot-d0-global-d1-official.yml) 仅手动/对应源码push触发（**没有schedule**），Ubuntu/macOS双平台13测 + 真实原36份GitHub研究源 + 原官方BTC/ETH各十日历史数据 + Git SHA源锁定结果回写；不启动Mac/Frank/交易/真实Gmail。

## 真实GitHub Actions完整5任务验收

[**真实CI #38809121359**](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38809121359)：已由GitHub再次读回 `completed/success`、**5/5 Job SUCCESS**，真实触发源码SHA `0ffe44ece8644443757b5f6ac0cd19e0f5d1999e`。Ubuntu24.04、macOS Python3.12各`13/13 unittest PASS`、py_compile PASS。数据组从原GitHub Stage26历史研究CI产物按每份artifact ID实际下载**36个源ZIP**，同时校验36份原封装ZIP SHA和内部JSON SHA、逐币/逐日期/逐shard来源资格。另一Job从`data.binance.vision`经原 Stage26 `read_complete_216h` 核验BTCUSDT/ETHUSDT **各十天1m ZIP及对应CHECKSUM** 后运行真正同SQLite共用D0+D1，返回准确机器摘要；保存**20份每币每日期的真实发行者SHA256**，并带动源码SHA256。最后 `MONSTER_SHARED_SPOT_REAL_ORIGINAL_SOURCE_PROOFS_PINNED_GIT_PASS` 实际打出，表明研究证据回写前检查所有四个源码/test/workflow固定blob无漂移。

机器存档：
- [完整原758名×6日源资格（36个原Artifact的ZIP及内JSON双SHA验收）](evidence/monster_shared_spot_stage26_36_source_census.json)，blob `a558766de7514a87a4d2bca7555d4ac37efbb086`，原758完整名单SHA256 `cea49caae4245dad910cc096bdaea953387bdfea64667a49916756d12297074a`，触发SHA与本轮一致。
- [原官方BTC/ETH两币共用一SQLite的真实历史3360时钟机器行证据](evidence/monster_shared_spot_real_BTC_ETH_20260204.json)，blob `8b58e95bb2758c27e8ab08a875f7a50970fb5c2f`，本轮引擎SHA256 `9d09626f7425524bd374d3295c36e4e5a81f66347e4e7db89246387532314404`，触发SHA精确等于 `0ffe44e...`。

## 真正的历史完整来源覆盖（这是核心发现）

固定来源人口为758个Spot USDT币、六个已经曝光的168小时历史日期；Stage26原下载结果并没有使每币各日期都有完整216h分钟archive。

| 冻结回放开始日 UTC | 原冻结宇宙 | 有完整官方分钟来源的币种 | 来源缺失或不完整 |
|---|---:|---:|---:|
| 2025-11-04 | 758 | 433 | 325 |
| 2025-12-04 | 758 | 440 | 318 |
| 2026-02-04（原98币高压窗口） | 758 | 445 | 313 |
| 2026-04-04 | 758 | 438 | 320 |
| 2026-08-04 | 758 | 478 | 280 |
| 2026-09-04 | 758 | 485 | 273 |
| **全部六日币种×日期** | **4548** | **2719** | **1829** |

这一不足不是依靠WATCH零值或缺失币的后验分数可以填补的。缺失原因在 [机器Census](evidence/monster_shared_spot_stage26_36_source_census.json) 的 `source_status_counts` 原样披露。原Stage26总1132次WATCH是已核对历史逐币结果，不构成当前共享引擎实际发出的全市场1132次WATCH；**严禁把Stage26/28的历史WATCH当本轮共享D0回放输入**。

## 新引擎已验证和真实尚未完成的范围

同一源码具有**完整市场共同读取的正确结构**：对某一冻结日期，要每个币的全部`12960`个UTC连续一分钟bar和十天正确日期的publisher SHA齐全，才预先在独立SQLite缓存构造`3360`个三分钟ticker观察时点和已闭合5m。从每个3min tick一次取`ALL_SYMBOLS`，缺一项即fail-closed，绝不使用缺币部分市场运行后宣称FULL。所有源量来自当时已闭合一分钟的CLOSE与过去1440分钟报价总额；**后者是由官方1m汇总出来的quote-context代理，并非当年真实HTTP ticker**。5m信号仍由已闭合的原始minute通过冻结原函数聚合，不使用未来信息。

实际真实历史二币试运行：
- 2026-02-04 06:00 UTC—2026-02-11 06:00 UTC 168h，BTCUSDT与ETHUSDT各十份官方原始日ZIP+CHECKSUM验证、每币12960源分钟、3360三分钟轮、每币2592根聚合5m。
- 共**6720份币×tick**全时点源缓存记录，**一个共享SQLite**每tick只调用一次原生产D0+全局D1。此时间片BTC和ETH并未触发模型原D0 WATCH，真实 D0 WATCH=0、D1=0；如实保留**零信号控制组**，不能拿它证明高压98币路径已在真实来源下复现。
- 合成正向的两个币同期模拟测试采用逐币**同一源分钟时钟的原Stage26`scan_continuous`**核对WATCH时间完全匹配；另测试缺分钟、缺币、十日源收据缺失/错日期/坏SHA，全部在发信前拒绝，不是实盘命中率或独立OOS。
- 当前源码在高质量证据层面实现并验证了双币共享时钟、来源完整性及原核心同规则；**没有**真实回放758共同D0，**没有**真实复现445币subset历史高峰到D1，**没有**复现全部六日期全市场时间轴、实际Spot+Futures争用、真实交易净利润或Mac本机运行。

## 后续工程主线（不为凑Stage数量而停在报告）

1. 依据已SHA锁定的真实完整`445`名2026-02原高压窗口名单，先只对**SOURCE_COMPLETE 子集**运行真实同SQLite共享D0+D1回放；每个币重新取得官方minute ZIP/CHECKSUM，提前写清不包含313币的选择偏差，不能把445冒充758完整全市场。不推荐全同时在线逐币HTTP重采样导致超限；可将下载、每币特征预处理和真正全局共享D0时间轴分开，并行但锁定原source。
2. 在高压445结果实际得到后，同源、同市场成员列表比较旧Stage26每币WATCH/SETUP与新共享输入/输出，核心关注原98同时WATCH中91 LATE的因果差异，以及状态撤销和新的98 WATCH是否都在共享队列。若新D0时间线因旧逐币D0和全市场同一时钟而变化，必须原样报告，不能以旧91直接替代新结果。
3. 扩大普通对照日（2025-11 433个完整币），再验证六日期总体，**同时保留原758尝试、1829来源CENSORED**、不做后验赢家选币或冷却/成交额阈值调优。实际成本/行情缺口与新日期PIT、真实book/费用和通知送达仍独立GATE。
4. 仍必须交给**另一AI独立固定SHA审查**，仅允许离线代码与历史来源校验，不因本次5个CI Job全绿而自动升为`APPROVE`或开始真实Mac部署。

继续 `G0 PARTIAL / G1 NOT_SCORABLE / G2/G3 NOT_PASSED / G4 UNKNOWN / G5_FULL_RELEASE NOT_PASSED / G6 NO_GO`；`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE / FRANK_UNCHANGED / STAGE99_STOPPED / NO_NEW_SCHEDULE`。
