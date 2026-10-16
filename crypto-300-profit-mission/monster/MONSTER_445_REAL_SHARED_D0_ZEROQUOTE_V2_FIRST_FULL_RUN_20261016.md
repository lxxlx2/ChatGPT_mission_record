# Monster 445真实原始分钟源同SQLite共享D0和实验V2 D1：第一次完成（2026-10-16）

## 身份与范围

- 仓库 [Mission](https://github.com/lxxlx2/ChatGPT_mission_record)；当前研究主线[Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)，不合并。
- **固定源码/执行SHA**：`9b32f8debe6a4246f91f56a84aa7539884f5f857`，真实Actions [#38898752712](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38898752712) 于2026-10-16T12:15:29Z结束，`completed/success`，Ubuntu/macOS测试及单台Ubuntu完整回放3/3 Jobs成功。
- 摘要真实Git自动封存提交：`4a351658c2e4d44e7980b4f10a85ccb2ea5d7f4d`，路径 `evidence/monster_feb445_all445_one_sqlite_replay_actual.json`，Git blob SHA `532d887a78f0d225132959731ea166d13767bf9c`。
- 完整原始CI结果 Artifact ID `12044872933`，名称 `monster-feb445-all445-real-original-shared-D0D1-once`（名字来自CI，**并不意味着原生产D1通过**），截至本轮`expired=false`，将于2026-12-15T12:15:22Z过期。包含 `monster_feb445_all28_source_audit.json`、`monster_feb445_all445_one_sqlite_full_result.json`、`monster_feb445_all445_one_sqlite_summary.json`。全量JSON SHA256 **`370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf`**，已从Artifact实际原字节重新核对与Git摘要完全匹配。SHA不得用输出文件名替代。
- 研究群体：2026-02-04原758历史尝试，445个原Stage26 source-complete历史样本，另外313 CENSORED；28/28原1m源分片、18个原Artifact、每币12960个1m源bar、每币10个Binance当日源publisher sha，总4450份；并非独立OOS、当年真实PIT名单、758币回放或可成交净收益。
- **重要区别**：原生产`monster_v4_shadow.py`及`monster_v4_shared_spot_d0_d1_original_core.py`源码均未改。原生产D1直接使用原K线时真正失败于`SHARED_SPOT_ORIGINAL_D1_SOURCE_INVALID_CANDLE`（此前CI [#38897425342](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38897425342)），本轮成功的是**同一SQLite原始D0 + 已有zeroquote V2研究语义的实验D1**。它保留原8 slots选择顺序，但把零quote候选标注为`SOURCE_UNSUPPORTED_D1_ZERO_QUOTE`，不能宣称原生产D1通过。

## 真实共池结果（未独立他AI审查）

| 字段 | 实测 |
|---|---:|
| 真实source-complete成员 | 445/445 |
| 同一SQLite上的3m统一轮询 | 3360轮 |
| 原生产D0发出WATCH_EARLY | 269 |
| 最大同轮WATCH_EARLY | 98 |
| D1每轮原容量上限 | 8 |
| D1总selected（含重复尝试，不是独立候选数） | 753 |
| D1 completed | 169 |
| D1 deferred（重复重试事件） | 488 |
| D1 late事件 | 93 |
| D1队列终态 EVALUATED | 169 |
| D1队列终态 LATE | 93 |
| D1队列终态 INVALIDATED | 4 |
| D1队列终态 SOURCE_UNSUPPORTED_D1_ZERO_QUOTE | 3 |
| D1 zeroquote总消耗attempt slots | 16 |
| D1实验真实最大单tick selected slots | 8 |
| D0事件表 SETUP_ACTIVE | 120 |
| D0事件表 INVALIDATED | 78 |
| 报告 G4 / G6 | UNKNOWN / NO_GO |

**独立事件+队列归因（全量源Artifact读取实测）**：

- **2026-02-06T00:36:00Z** 单个真实共享D0 tick产生 **98 WATCH**；对应同一`first_seen_ms`的98条唯一候选，**91个最终LATE，7个EVALUATED**。原Stage28注入测试曾出现“98 WATCH/91 LATE”，但只有本轮真实共源SQLite才构成该数的非注入式观测；两者不可混为同等级证据。
- 全局93个LATE中的 **91个（97.85%）** 来自上述1轮峰值；其余171个非峰值候选中只有 **2个（1.17%）** LATE。候选中总LATE占 **93/269 = 34.57%**，主因应优先研究**原8槽FIFO队列与15分钟候选期限**；这不是实际错失盈利交易或净利润测算。
- 零quote实验终态3个：`ACAUSDT=2`、`GUSDT=1`，未将零额补为正，也不当作LATE或可交易信号。
- 首先验证原8-slot、重试、截止时钟和候选状态转换是否准确；**先设计多个不篡改旧门槛的候选处理方向**，再独立OOS和真实价差、盘口、手续费、滑点、成交与通知时延验证。绝不能因曾观察到一个98集中冲击便事后调参报盈利。
- 早期01源原Git proof曾被遗留workflow的普通push监听触发重采重写（Git SHA `d16a2c...`），后核实逐币原真实内容与publisher-day SHA完全相同，仅打包manifest SHA、ZIP SHA与trigger变了；已于源码提交`6d3eae56c28f141914a3d549b7b1e55f0143f49d`停用该旧研究分支自动push recapture并拒绝已有proof覆盖，Git提交`57716f01a5c6321dffbba30997baf7e8e03835c2`恢复原冻结与Artifact配对的旧proof。历史错误/重采证据仍在Git，不得删除。

## 未达到的关口与下一步

**G0 PARTIAL**：有官方历史源真445，但313/758删失、历史listing PIT未证实；**G1 NOT_SCORABLE**：没有独立未来全样本召回/真实目标事件判定；**G2-G3 NOT_PASSED**：本次真实拥堵存在91峰值LATE；**G4 UNKNOWN**：无在信号时间可执行盘口、双向费用、滑点和净PnL；**G5 RELEASE NOT_PASSED**：新的445研究结果未完成**另一独立AI审核**、Mac隔离及邮件投递验收；**G6 NO_GO**。源码CI success并非另AI approve。严格`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。未经用户明确批准不得创建ChatGPT Automations、GitHub定时任务、cron/LaunchAgent，不操作Frank或其他项目。

审核焦点：28个Artifact取回和旧源run失败但源job成功的窄例外；legacy shard01重采覆盖与关闭；来源完整性、全445真实共SQLite；实验V2 8槽和零quote分类；98/91峰值是不是源数据真实且因果；D1不同终态、队列总数严格闭合；所有数据不可声称交易盈利。需要另一AI在**固定SHA**独立审查/重验后才能考虑后续策略实验，不批准生产。
