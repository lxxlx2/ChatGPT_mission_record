# Monster Stage161 — 真实445共池首服务/重试占槽诊断（完成，研究-only）

## 固定证据与可信范围

原始官方source 18份GHA Artifact/28片原ZIP+Git proof，445币各12960分钟，原758中313历史source缺失维持CENSORED，研究日期2026-02-04开始。原始全445成功V2回放 Run #38898752712，Artifact 12044872933，full JSON SHA256 `370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf`。

本次冻结Stage161设计 `MONSTER_445_STAGE161_FIRST_SERVICE_TRACE_DESIGN_FREEZE_20261017.md` → 实施`local-agent/scripts/monster_v4_445_first_service_trace_replay.py`、5项真实SQLite侧路仪表测试、一次性仅request push触发workflow `.github/workflows/monster-v4-445-first-service-trace-one-shot.yml`。真实GHA [#39012150858](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39012150858) **2/2 Jobs SUCCESS**，触发源码SHA `f5c2fd8ad9b5ee9e85fb9835cab3bb85525785ea`，复验原来源28片再逐币读回，仅在原研究zeroquote V2 handler外层做一次before/after SQLite只读观察，没有改生产 `monster_v4_shadow.py`、原共享核心或原zeroquote V2字节。新执行结果的`execution_counts`、`queue_status_counts`、`event_type_counts`、全部269个`queue_rows`和560个`events`**逐字段与原445冻结Full JSON严格一致**，失败会hard-stop，不存在换模型拿结果。新原始trace GHA Artifact ID **12093253053**（zip名`monster445-real-first-D1-service-fairness-28shards-once`，60天至2026-12-16T07:05:40Z），内部`monster445_first_service_trace_full.json` SHA256 `44fb0bec7ac0df9b86eebbc923e9e589eb0d07c523dd311758ccec44bf67928f`。Git摘要 `evidence/monster_feb445_real_first_service_trace_actual.json` Git blob `c54f677f3dcd8c045f03add14795eb87dceae9e9`。

以上是**事后已接触样本的真实历史研究实验**，不是新的前瞻OOS或历史PIT上市池，也没有真实BBO/L2、滑点、手续费或可执行交易净收益。模型准确性G4 UNKNOWN/G6 NO_GO，任何信号/交易/邮件/发布不得启用。

## 一、定量结果：旧最终attempts不能代表D1首次服务

- 原旧full JSON 269候选的`attempts`全部为0，然而同一原运行全球`D1_selected=753; D1_deferred=488; D1_completed=169; D1_late=93`。生产`attempts`仅部分ValueError失败时增加，正常重试/无新闭合K线等待不会计入。因此**不能依attempts=0断言没有被选中**。
- 新trace记录3360个共享市场poll ticks，其中仅**534轮有D1选中**，所有槽位753，**269次为各自首次selected**，**484次为历史候选重复selected（64.3%）**；此“重复”可能是等待第一根收盘5m、尚无SETUP的正常重复评价及零quote研究保护，不能直接称为浪费或错误。
- **269个候选最终全部曾获一次selected**，但**93个是在自己的15m有效期过去以后才第一次selected**。晚到者进入D1只记录LATE，而没有在时限内形成合法D1有效评价；不能据此推出这93个会获利或有SETUP。

## 二、98币同时WATCH的因果时间序列（UTC2026-02-06 00:36:00Z）

当轮实际99个PENDING（1个早先、98个新），FIFO前8为1旧+7新。原V2固定每tick8槽，按`first_seen_ms,id`排序，只要8个较早PENDING没有完成便持续优先重试。

| 自高峰偏移 | 实际selected | 此轮首次selected | 重复selected | 结果特点 |
|---|---:|---:|---:|---|
| +0m | 8 | 7 | 1 | 7个刚WATCH等待首根后验闭合K线 |
| +3m | 8 | 0 | 8 | 7个峰值仍AWAIT_POST_WATCH_CLOSED_5M |
| +6m | 8 | 0 | 8 | 7个峰值首次真正D1特征评估，仍NO_SETUP_YET |
| +9m | 8 | 0 | 8 | 同一组继续NO_SETUP_YET |
| +12m | 8 | 0 | 8 | 同一组继续NO_SETUP_YET |
| +15m | 8 | 0 | 8 | 8个NO_SETUP_WITHIN_WINDOW转EVALUATED |
| +18m | 8 | 8 | 0 | 新被轮到的候选已超过15m有效期，直接LATE |
| +21…+48m | 每轮8 | 每轮8 | 0 | 后续候选只拿到过期后的首服务 |
| +51m（相对峰值00:36） | 5 | 5 | 0 | 3个峰值币 + 2个在峰值+3分钟后WATCH的普通币，此轮均超期关闭 |

原98中 **7个在+0m首次selected且+6m首次真实有效D1评价**，最终EVALUATED但从未SETUP；其余**91个在+18至+51m才首选中、全部LATE、全部没有有效D1评价**。相邻轮的GPSUSDT与LUNAUSDT从各自WATCH时间计算延迟48分钟、即峰值后+51分钟才首选中并LATE，因此全量93个LATE中**0个在15m内获得过第一次服务**。98峰值前6轮共6×8=48个槽，实际**仅7个槽是这次市场冲击中的首次服务**，其余41个选中为旧候选/同组重复服务；所以观察到的“首服务覆盖率”低于前文48个不同候选的*无重试容量上限*，但不能从这里直接断言换公平策略一定能达到48个有效D1评价。

## 三、非突发WATCH和重试资源占比

- 其余171 WATCH全部最终selected；169人在WATCH当轮首次selected、2个在48m首次selected（这两个也是LATE）；其它171中EVALUATED162、INVALIDATED4、零quote不支持3、LATE2（162+4+3+2=171），原V2实验终态不改。
- 其它171共有620个selected槽：171首次，449重复，说明正常非峰值也需要持续追踪后续5m或等待/延期。新的比较方案**不能简单取消所有449次重复**，否则可能让120个已确认SETUP事件消失。
- 本轮`slot_trace`总753条，后置error字段频数包含`AWAIT_POST_WATCH_CLOSED_5M=240`、`NO_SETUP_YET=232`、`NO_SETUP_WITHIN_WINDOW=49`、`SOURCE_UNSUPPORTED_ZERO_QUOTE=19`、`None=213`。这里是**每槽事后队列字段**，不是可直接相加的独立业务失败分类；生产原`attempts`仍0不影响重服务证据。
- **根因是优先顺序与重试准入的耦合**：原生产 `AWAIT_POST_WATCH_CLOSED_5M` 与 `NO_SETUP_YET` 统一设置 `retry_after_ms=now+60_000`，低于下一次全局3分钟poll间隔；旧PENDING候选每轮重新满足资格，按 `first_seen_ms,id` 进入前8槽。只修改同优先级排序、与让没有新5m可评估的候选先不占槽，是两个不同的反事实改法，不能混称“FIFO单一错误”。本历史峰值只出现一次，不能因此宣称改顺序能普遍提高可交易机会或净利润。

## 三点五、理论首评容量和真实零新增有效K线重试的边界

- 此前“6轮×8=48”是 **WATCH 首次被 D1 选中** 的无重试最大容量，不是首次有效5m评价容量。峰值 00:36 后在 +0m 和 +3m 并没有 WATCH 后已闭合可评价的5m线；仅 **+6/+9/+12/+15m 四轮**可进行有效首次评价。每轮最多8槽，对本峰值组的 **首次有效评价槽位理论上限是32**。旧V2真实7个峰值币取得有效D1评价，因此在假设替代调度不损失这些7个、所有32槽均可用于不同候选的最宽松情况下，**额外首次有效评价数量上限25**。这不是可保证挽救的25个币、SETUP或盈利，上限不等于实际可达到结果；期限处于边界的零报价、其它既有SETUP复查等约束可使实际上限更低。
- 从旧固定Stage161完整`slot_trace`原始字节重算：484次重复D1选中，其中 **190次未推进`last_evaluated_bar_ms`**（PEAK_98=14，OTHER_171=176），**294次推进了有效5m评价标记**（PEAK_98=21，OTHER_171=273）。190次再按处理后状态字段划分：`AWAIT_POST_WATCH_CLOSED_5M=68`、`NO_SETUP_YET=93`、`SOURCE_UNSUPPORTED_ZERO_QUOTE=15`、`NO_SETUP_WITHIN_WINDOW=14`。这190次应准确描述为**实际占用D1处理槽位，但有效5m评价游标没有推进**，而不是仅仅写“重复重试”。按处理后的类别区分：68次仍等待WATCH后收盘5m，93次仍NO_SETUP_YET（这161次可能包含重复检查同一已知评价窗口）；15次属于历史V2的零报价来源保护，不能当作市场合法可交易的新信号；14次属于15m期限结束的状态终结服务，即使游标没有增加，仍有明确队列生命周期作用。**未推进游标不等于当时没有新行情，更不等于190次都安全可删或存在190个SETUP/盈利机会**。精确可归因字段需要新instrument代码直接生成并与原source逐条核对，原版本旧hash保持不变。
- P2安全（Claude再次复审提出的幻影服务）：只检查selected=8且非预计前8 ID不变，仍可能**只有7个/0个预测行真的改变却声称8槽已处理**。现补强为对所有预测选中行也必须观察到处理前后持久队列字段至少一项变化；在原冻结生产/V2处理路径下，每次被选中都要推进`status`、`retry_after_ms`、`last_error`或`last_evaluated_bar_ms`等状态之一。非预测行完全不变、整表ID集合完全不变、预测行必须改变三组约束缺一不可；新增真实SQLite 7/8和0/8幻影负例，及实际deadline不等于+15m的边界反例。若将来生产支持合法只读服务，该不变式会fail-closed，需要先明确新完成凭证，不能悄悄把幻影服务当成功。旧V1/V2历史证据不得覆写。

## 四、后续业务性实验设计（不能盲目改产线）

下一阶段先冻结再研究“首次D1服务公平性”，保留 **同一个8槽/3分钟、候选15m期限、源完整性、D0 WATCH因果规则不变**。预定义至少两组只读离线实验：Baseline原FIFO重服务；候选若已选但仍待新收盘5m，则只在成熟后复查，并给从未服务但已拥有至少一根WATCH后闭合K线者合理第一次评价名额。需要真正重放**同一源码之外的隔离研究处理逻辑**并测正常171币SETUP、错过的合格闭合K线、峰值首次评价次数、峰值与正常信号互相干扰、误报、零quote与成本，以及后续前瞻新市场。必须严格防止未来OHLC、98个事后LATE或赢家身份进入当时排序。此实验证明“覆盖能力”的上限，不证明这些币有资金收益。研究问题必须先得到实际阈值/评估条件的技术冻结，代码提交与结果再交别的AI独立review，未经批准不发布任何Mac/Frank/Gmail/交易或定时任务。

**当前Stage161 = REAL_SOURCE_TRACE_DONE、MODEL_OUTPUT_IDENTICAL_VERIFIED、OTHER_AI_INDEPENDENT_REVIEW_NOT_DONE、PRODUCTION_NOT_AUTHORIZED。**
