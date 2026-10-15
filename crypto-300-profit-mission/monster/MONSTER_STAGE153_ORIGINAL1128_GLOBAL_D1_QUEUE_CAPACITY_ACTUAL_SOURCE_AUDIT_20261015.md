# Monster Stage153：源锁定真实共享D1队列1128个候选，98币同轮压力和只读诊断

2026-10-15 Asia/Bangkok，原唯一 [Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。本研究**原真实历史数据完全重新核对，未调整任何正式D0/D1阈值、没有新调度和Mac部署**。本轮外部独立其他AI新SHA代码审核**未收到**，本文只能填写自有CI验收，不能借Stage152的独立APPROVE。

## 代码与原始市场研究证据级别

[Stage153严格先冻结协议](MONSTER_STAGE153_FROZEN_FULL_QUEUE_LIFECYCLE_AND_PRESSURE_AUDIT_20261015.md) 的预先Git commit `833182273558a53acd5050b4ba3d8beb44e651ce` 早于全部本阶段代码。

新代码固定审核 SHA `80ebab9a6f3533103858de9e321f037384e86fde`；两份新脚本：
- [原Stage28六原始Artifact SHA锁定全队列审计 + sqlite只读压力探针](../local-agent/scripts/monster_v4_stage153_source_locked_d1_queue_lifecycle.py)
- [9项真实格式/压力98币/拒绝篡改/本机只读SQLite检验](../local-agent/scripts/test_monster_v4_stage153_source_locked_d1_queue_lifecycle.py)
- [Stage153专用GitHub Actions source-job+双系统单测](../../.github/workflows/monster-v4-stage153-real-shared-d1-queue-lifecycle.yml)，无schedule，审计仍只访问历史原artifact。

[真实CI #38737110644](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38737110644) `completed/success`，触发exact源码SHA `80ebab...`，3/3 Jobs PASS：Ubuntu24.04/macOS各9项单元测试和py_compile通过；第三个数据job从GitHub官方Actions原run [#38146403662](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38146403662) 下载**6份仍可获得的、已归档真实原Stage28生产共享SQLite结果ZIP**，对照预保存 [六个原始Artifact manifest](evidence/monster_stage28_original_six_real_shared_sqlite_artifact_proof_20261011.json) **同时核验6份封装ZIP SHA256和解压的6份JSON SHA256**，按全原队列输出1128行，并实际Git回写 `MONSTER_STAGE153_REAL_STAGE28_SOURCE_SHA_AND_GIT_PUSH_CONFIRMED`。

**数据来源严格分层**：
1. Binance Spot每日5m原始K线 + .CHECKSUM是在**既有Stage28原始CI**中下载验证和生产process_queue真实历史共享SQLite写入；Stage153此次**没有再次下载全部1421份官方K线**。
2. Stage153此次验证并复算原Stage28 **6个原始GitHub Artifact ZIP＋内层JSON字节**，与原CI固定proof完全一致；新计算只来自这些source-locked JSON里的原始队列final rows、events、真实historical setup。
3. Stage28原WATCH timestamp是Stage26**逐币独立**V4 D0原历史研究的入队列表，Stage153没有补做全体Spot+USD-M同SQLite `observe_snapshot` 的重新回放；没有D0撤销注入，没有逐次HTTP请求和成功确认的日志细节，不能凭记录反推实际第一HTTP调用时刻、真实Gmail送达或损益。

本轮实际归档：
- [Stage153六日期真实1128生命周期机器摘要](evidence/monster_stage153_stage28_1128_queue_lifecycle_summary.json)，Git blob `0f24fb56b6cd9a3166f43ac7eed6ce9b3cc77e9a`，绑定 `trigger_commit_sha=80ebab9a6f3533103858de9e321f037384e86fde` 和审计源码SHA256 `8a73308acd9e2098334cbe03fed9209af2da500929ffcabbe3442f5568994e7f`。
- [原Stage28全部1128条真正SQLite候选的逐行未删减诊断](evidence/monster_stage153_stage28_1128_queue_lifecycle_rows.jsonl)，Git blob `beb066d13ed1bf9656a1d9153f003c4363aa849c`，每条含原first_seen/deadline/status/last_evaluated_5m/attempts/last_error和没有证据的真实时钟UNKNOWN。该文件是派生研究证据而不是SQLite写入。

## 六日期逐候选真实结果

| Stage26原连续168h起始日期 | 原WATCH事件 | Stage28实际队列候选 | SETUP | LATE且最后未记录完成D1 5m | 最大入队时点 PENDING | 累计选取次数 | 延期/重试选取次数 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2025-11-04 |260|260|220|2|6|819|559|
| 2025-12-04 |133|133|113|2|4|431|298|
| 2026-02-04 |269|267|121|96|101|744|477|
| 2026-04-04 |181|181|150|9|5|567|386|
| 2026-08-04 |182|180|147|3|3|624|444|
| 2026-09-04 |107|107|77|11|13|357|250|
| **全部** | **1132** | **1128** | **828** | **123** | **最大101** | **3542** | **2414** |

**123/123原LATE事件的最终 `last_evaluated_bar_ms` 全是null，表明截至过期时**没有记录任何成功完成的5m D1特征评价；其中仅 **27** 个 LATE 记录包含 `attempts>0` 的错误重试迹象（2+2+3+9+3+8）；其余不能武断称从未做过任何 HTTP请求，因为成功拉取旧K线、等待下一根已闭合bar的尝试不会增加错误`attempts`，该原研究没有每次服务调用的时间序列。区别 `WATCH已写出` 与 `完成D1` 对用户更重要。旧Stage27所谓50未首评是**一次评价完成的乐观上界**；本轮真实生产路径中98突发有91最终LATE，7 EVALUATED。

2026-02-06 00:36 UTC 同轮98 WATCH -> **91 LATE, 7 EVALUATED**。原8条/3min、15min TTL（允许在WATCH+15m临界仍进队列）在6轮内单次服务最多48，乐观容量至少50不可能首次处理，真实生产还需重复计算、不一定一轮确认；这不证明91件有利润的买单损失，也没有交易时L2和可验证用户下单金额。

**不隐瞒原证据的另一个问题**：所有1128队列候选来自已经曝光的2025/26历史日期，不是新样本外，用户真实所处市场的2026-10月现时D0/D1延迟和新版真实Spot/Futures共同挤压未知。旧Stage28对不同行情粒度有可能产生SETUP时点差异，不能把所有错过都归因于队列。

## 可供后续真正本机用户状态页面的只读queue_pressure

`queue_pressure(db, asof_ms)` **不触碰数据库写入**，字段：PENDING总数/从未有D1 5m评价数/曾有bar重评数/eligible和backoff数/已过期待处理/未来3及6分钟待到期/最近deadline余量、假设从今15分钟仅6次×8个**单次评价最乐观容量阈值**。离线实测同一poll注入98个全量PENDING的只读sqlite，明确输出98个候选、最乐观48容量和至少50压力缺口，**不会直接改变任何正式排队执行的顺序或尝试次数**。

此探针目前只提供代码和测试，尚未在用户Mac实际数据库上运行，也没有挂载到正式Dashboard、HTTP API或持续后台服务，不能称用户打开页面就可以看到指标。

## 高价值后续而非回到无穷边界修补

Stage153可据真实原记录**明确下一开发选择**：要改善可用性，不是无理由增大每轮8的HTTP容量，更不能改变已审Stage27/28原策略参数来让曝光旧数据的赢家更多；应围绕共享D0全市场可观察WATCH事件时间、已闭合5m、D1首次有效评价及短TTL之间的真实调度占用，以冻住的源事实设计可复验的 **一次首评 vs 多次重评** 的统一队列生命周期与延期资源预算。只在不同市场高压/普通场景及无外加真实API权重前提下实证能避免过去重大错过、保持WATCH、不提高数据源风险时，才提出正式新的队列顺序/吞吐方案，且必须独立其他AI新SHA审核。

长期门禁仍 `G0 PARTIAL, G1 NOT_SCORABLE, G2/G3 NOT_PASSED, G4 UNKNOWN, G5_FULL_RELEASE NOT_PASSED, G6 NO_GO`，`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`，Frank不变，Stage99停止，用户手动采集参考Oct28/Nov11且不恢复自动化，Monster研发测试与Mac安装许可分离。
