# Monster下一主线冻结协议：同一个全市场 Spot D0→持久队列→原生产D1 的因果时钟（2026-10-16）

此处是 **Stage153最终独立Code Review APPROVE后下一个真正业务缺口**的开发协议，**不是该业务任务已完成**。原Monster PR #30继续Draft/Open；不得为了填表制造不必要新Stage小工具。本协议在任何下一主线新代码更动之前先单独Git冻结。

## 当前已独立确认的真实缺口（不可混同）

- Stage153已由用户提供Codex独立`APPROVE@4553cb6b18c5aaf723072d17a39f9ad92f0629c9`，**只**对源锁定1128队列审计、SQLite CLI安全P1和2P2代码审核通过。正常WAL查询可能更新`-shm`索引，不是覆盖主数据库，不得声称所有sidecar绝对不变；参[独立review归档](MONSTER_STAGE153_CODEX_FINAL_APPROVE_FIXED_4553CB6_WITH_SQLITE_WAL_SHM_LIMIT_20261016.md)。
- Stage26 `monster_v4_stage26_continuous168h.scan_continuous()` 的**事实**：758币×6曝光历史日期逐币单SQLite循环`observe_snapshot(db,"spot",...,rows=[ONE symbol])`、`process_queue`，每币使用官方CHECKSUM日1m、前24小时warmup、每3min tick与rolling quote24**归档分钟成交额派生量**；其 `1132 WATCH/826独立SETUP` 不是全市场一库。
- Stage28 `monster_v4_stage28_real_shared_sqlite_d1.shared_production_replay()`的**事实**：原1132 WATCH来自Stage26逐币产物、统一按3min时间注入每日期一库，然后原`process_queue(limit=8)`，六日期`1128候选、1005评价、123 LATE、828 SETUP`，98同时WATCH里91 LATE/7 EVALUATED。它没有重放`observe_snapshot`在同一个SQLite的动态D0判断、冷却/INVALIDATED或跨Spot/Futures争用；SETUP来源producer_id没保留，不能被Stage153补出来。
- Stage137 `monster_v4_stage137_dynamic_t0_original_core_causal_replay.replay_original_d0_d1()`的**事实**：现有另一路官方历史USD-M和Stage80新D1研究，原`observe_snapshot`仍是 isolated 每instrument SQLite，而不是旧Stage28生产共享Spot D0+D1事件流。**两路不能合并成“已通过全市场shared复验”。**

## 只能选一个高价值真实交付

在**同一历史分钟因果时钟**、**同一个真实SQLite**、**同一份冻结原Shadow生产D0/D1核心**上执行 `observe_snapshot(db,"spot",tick,full_758_rows)` → `process_queue(db,tick,read_only_official_closed_5m)`；每一时点输入含`758`原冻结Universe所有同时间可见符号，不允许按未来盈利机会只选那些WATCH币、也不能逐币重置排队状态。每个tick闭合1m price + 24h quote-context由已验证分钟源当时可见的prefix构造，全部758个原冻结宇宙成员及其实际可观测范围由原Stage26/source冻住并严格对账；**禁止把由分钟源推算的24h成交额说成真实历史24h HTTP ticker响应**。合约USD-M和交易所listing真PIT身份另列，第一迭代只宣称原758 Spot主流固定宇宙；不宣称交易所最新全部上市币或跨场所统一竞争。

### 不可倒改的执行与源合规

1. 先确认原Stage26每日期**758完整成员**、36原真实artifact证据以及Stage28六日42压缩文件SHA可再次取得的来源和原源Git固定指纹；要获取全部真实1m 216h历史时，复用Stage26官方 daily archive `.CHECKSUM`下载器，每symbol每day SHA、行数和UTC连续性强制检查。不使用已知赢家名单或Stage26结果代替分钟行情，也不使用Stage28最终WATCH事件作为本次入队输入。
2. 冻结时间戳合同：每3min整轮tick、调用前一分钟必须已经闭合、源quote24仅过去1440根分钟（不能看入场后整根）、真正5m`bar close <= now`且具体旧Stage26和Stage28源粒度差异单列，严格冻结 `process_queue=8`、原D0`min_quote24=100k`、原15min有效、retry和强制过期；不因为研究旧日期盈利标的而修改业务阈值。
3. 官方1m数据大（原758×6×10 day archives，source断网/缺币只能`CENSORED`或FAIL）。**先核对真实数据可得性与重放成本**，做自有冷启动、时间/多币并发、批次全量与单字节SHA变动的负向单测，再跑至少已冻结的2026-02-04高压历史窗口和2025-11-04普通对照窗口；CI实际来源数据通过且性能满足后，自动一次跑齐原六日期，不用每个币单独研究再停下来汇报。若无法在承诺上下文验证实际源就`BLOCKED_SOURCE`，不得拿旧1132固定WATCH注入伪装已完成全共享D0。
4. **必须比较同源同证据级别的三条链**：Stage26逐币原D0→独立D1、Stage28原D0到达时间注入→共享D1、真正新原D0全部758一次性扫描→共享D1。逐分钟记录`WATCH_NEW / WATCH_INVALIDATED / D1_QUEUE_INSERTED / D1_FIRST_SUCCESSFUL_BAR / D1_LATE / D1_SETUP / D1_NOTIFIED_UNKNOWN`；对每个真实候选对齐 `symbol,venue,first_seen,deadline`，所有多次WATCH和SETUP需要原事件ID，不凭缺失的producer字段做确定性映射。对已确认原始2x/5x events的召回、WATCH时钟领先/迟到和通知密度分别披露。
5. 独立记录**真实模型可用性**而非只看吞吐：多少WATCH由原D0共享状态改变、其中多少D1实际首次闭合bar得以评价/过期、原因是否确实为抢占8深查/等待下一根5m、多少已经属于源missing/无可用成交额/无法执行；不可把旧98事件的91 LATE解释成91个可盈利买单，也不可自动增加API限额和交易建议。
6. 若真实Spot一库同源重放成立，再设计新DATE的事前冻结样本外测试以及USD-M混合venue（Source/PIT Unicode、上市退市、工况）而不随意混用Stage137的Stage80不同D1规则。Mac和发信仍是后置，只有模型业务G0–G5门禁通过且用户再次明确授权才能部署/启用；Frank不动。
7. 工程按原规则一次源核实→设计→实际脚本与回归→真实GitHub CI原始发行者SHA重放→其他AI固定SHA审核→再决定Mac，且每一个证据等级写清。不能凭本协议文档把此任务写DONE，不创建新schedule或ChatGPT Automation。

## 下一执行首个具体动作（不用用户重复解释需求）

在原PR分支上核对Stage26/Stage28的36+6原证据可下载状态与出版者minute source成本，然后实现共享D0全宇宙**单次tick→SQLite**原生产同一核心注入的自动负向测试，并实际运行可源锁定的历史高压日期；优先给出真实WATCH与D1生命周期对照。若所有full source无法取得，阻断真实样本而不是用stage26的历史WATCH列表冒充新重放。

全程 `G0 PARTIAL / G1 NOT_SCORABLE / G2/G3 NOT_PASSED / G4 UNKNOWN / G5_RELEASE NOT_PASSED / G6 NO_GO`、`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`，Frank/Stage99 unchanged。
