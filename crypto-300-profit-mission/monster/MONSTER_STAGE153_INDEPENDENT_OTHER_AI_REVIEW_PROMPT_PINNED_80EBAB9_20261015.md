# Monster Stage153：直接复制给 Claude/Codex 的固定 SHA 独立审核提示词

你是另一独立AI审核员，请对 Monster 新增的**真实Stage28历史 D0→D1共享队列1128事件容量与迟到审计、独立SQLite只读压力工具**进行实际源验证、负向测试和代码审查。请不要直接相信本提示词的结果，不要把本阶段称为模型盈利或者正式上线通过。

**仓库**：https://github.com/lxxlx2/ChatGPT_mission_record
**唯一草稿PR**：https://github.com/lxxlx2/ChatGPT_mission_record/pull/30
**分支**：`research/monster-v4-local-discovery-20261010`
**本次仅审核代码与workflow精确固定Git SHA**：`80ebab9a6f3533103858de9e321f037384e86fde`，无论PR HEAD如何变化，后续研究报告、历史输出文件只用于独立证据验证，不能将HEAD静默换成审核SHA。
**上轮不同范围已获Codex审批**：Stage152 `APPROVE@71a041405352c9e2210d93dff9c2685149809e52`，只覆盖6h/24h汇总P2，不自动批准本次Stage153代码。

### 研究目标和事前范围

项目意图是真正捕获官方目标全市场重要币在最早可见时刻的WATCH，不在D1深查服务排队时沉没、不用过期买卖机会假装当前可跟、不挤坏Frank与通知。原Stage27/28已报告6日期共1132 WATCH（独立Spot D0导出）经真实原生产 `process_queue` 单个共享SQLite，1128条队列记录、123 LATE、828 SETUP，2026-02-06 00:36 UTC突发98 WATCH中91 LATE、7 EVALUATED；旧一次服务即可完成的乐观模型只预计至少50在15m内无法得到首轮评估。

本轮**预先冻结协议提交** `833182273558a53acd5050b4ba3d8beb44e651ce`，[协议](https://github.com/lxxlx2/ChatGPT_mission_record/blob/research/monster-v4-local-discovery-20261010/crypto-300-profit-mission/monster/MONSTER_STAGE153_FROZEN_FULL_QUEUE_LIFECYCLE_AND_PRESSURE_AUDIT_20261015.md)。新代码不修改生产原 `monster_v4_shadow.py`，不调3%/1%/120m历史策略参数、不新建定时采集；只做已发生全分母历史源锁定审计和用户未来可用的只读压力量化，非新交易策略。

### 需要审阅的准确内容

- `crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md`
- `crypto-300-profit-mission/monster/AGENTS.md`
- `crypto-300-profit-mission/monster/MONSTER_MANUAL_COLLECTION_AND_DEVELOPMENT_CADENCE_20261014.md`
- `crypto-300-profit-mission/monster/MONSTER_STAGE27_SHARED_D1_QUEUE_AND_CASH_LEDGER_ACTUAL_RESULTS_20261011.md`
- `crypto-300-profit-mission/monster/MONSTER_STAGE28_REAL_SHARED_SQLITE_D1_826_828_PAIRWISE_ACTUAL_RESULTS_20261011.md`
- `crypto-300-profit-mission/monster/evidence/monster_stage28_original_six_real_shared_sqlite_artifact_proof_20261011.json`
- **新增源**：`crypto-300-profit-mission/local-agent/scripts/monster_v4_stage153_source_locked_d1_queue_lifecycle.py`
- **新增9项测试**：`crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage153_source_locked_d1_queue_lifecycle.py`
- **新增workflow**：`.github/workflows/monster-v4-stage153-real-shared-d1-queue-lifecycle.yml`
- [真实源验证执行报告](https://github.com/lxxlx2/ChatGPT_mission_record/blob/research/monster-v4-local-discovery-20261010/crypto-300-profit-mission/monster/MONSTER_STAGE153_ORIGINAL1128_GLOBAL_D1_QUEUE_CAPACITY_ACTUAL_SOURCE_AUDIT_20261015.md)（不要仅看这个自述作审查结论）。

### 实际GitHub数据和应独立复现的验证

GitHub CI [#38737110644](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38737110644) 原trigger SHA=`80ebab9a6f3533103858de9e321f037384e86fde`，3/3 jobs PASS：Ubuntu24.04/macOS Python3.12各9/9单测成功；第三job访问仓库自己原 run [#38146403662](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38146403662)，获取六份原Stage28历史共享D1归档 ZIP，按Git源证明清单的 `artifact_id`，**逐个验证封装 ZIP SHA256 和内部JSON SHA256**，不是新下载独立官方Binance分钟ZIP。再原样读取6份真实生产 `queue_final`、`events`、`setups`、`late_events`，对账6×日期合计全1128 candidate queue记录、全部1132 WATCH、1005 EVALUATED、123 LATE、828 SETUP；总3,542次选取、2,414次deferred。98个真实source WATCH时钟`2026-02-06T00:36:00Z`，实际 91 LATE/7 EVALUATED。源结果核心摘要提交Git：[Stage1531128机器摘要](https://github.com/lxxlx2/ChatGPT_mission_record/blob/research/monster-v4-local-discovery-20261010/crypto-300-profit-mission/monster/evidence/monster_stage153_stage28_1128_queue_lifecycle_summary.json) blob `0f24fb56b6cd9a3166f43ac7eed6ce9b3cc77e9a`，以及[1128逐候选源锁定清单](https://github.com/lxxlx2/ChatGPT_mission_record/blob/research/monster-v4-local-discovery-20261010/crypto-300-profit-mission/monster/evidence/monster_stage153_stage28_1128_queue_lifecycle_rows.jsonl) blob `beb066d13ed1bf9656a1d9153f003c4363aa849c`；机器摘要中的审计脚本SHA256应为 `8a73308acd9e2098334cbe03fed9209af2da500929ffcabbe3442f5568994e7f`，trigger SHA为原pin。新分支Git文档HEAD较pin已前移但源码没有改动；请独立确认。

可独立执行：
`cd crypto-300-profit-mission/local-agent/scripts`
`python -m py_compile monster_v4_stage153_source_locked_d1_queue_lifecycle.py test_monster_v4_stage153_source_locked_d1_queue_lifecycle.py`
`python -m unittest -v test_monster_v4_stage153_source_locked_d1_queue_lifecycle.py`

真实六份原run每个Artifact的ZIP + CHECKSUM引用，在同一 repo GitHub Actions CLI有读取权限时可重下源ZIP并`python scripts/monster_v4_stage153_source_locked_d1_queue_lifecycle.py --stage28-original-artifact-dir <dir> --out <dir>`，重新校验6/6 raw和解压JSON SHA，逐日和全1128事件排查。不允许使用**后续已转储的1128行**冒充自己独立取得六份源文件。如果缺少授权/原源则对独立原JSON校验标 `UNVERIFIED`，但仍可审查既有CI、程序逻辑与输出统计。

### 必须检查的新真实功能、边界与缺陷

1. 队列全分母：每个源candidate_id、symbol、first_seen_ms、deadline_ms、status和历史WATCH/SETUP/LATE必须一致，不能只对98突发或已知盈利币抽样；原1132个WATCH并非1132独立queue候选，队列数1128不应报为数据丢失（部分未处理队列更新）。
2. 时间与结论：15min TTL为原研究设置、8次/3min 6轮乐观容量48和原突发98中最少50不可首次服务只是吞吐上界；生产91个LATE不等于91笔未赚到的交易。Stage28最终`last_evaluated_bar_ms=null`不等于没有发过HTTP请求，重试`attempts`计数不能代表有无成功特征；本轮有123 LATE没有记下完成5m bar，其中只有部分记录非零请求错误重试。
3. 原始证明：六份GitHub Artifact外壳ZIP和JSON必须双SHA一致，原Stage28真正Spot publisher5m校验是过去原CI完成，本次并非重新获得1,421个官方源，不可扩大证据含义。历史D0输入仍为逐币Stage26导致全市场共享D0及实际Spot+Futures共用源、真实通知均 NOT_VERIFIED。
4. read-only：`queue_pressure(db,asof_ms)`及命令行`--sqlite-readonly`必须既不会SQLite UPDATE也不会修改原数据库；验证98 PENDING同一时间完整显示、不静默top3、当前eligible vs backoff vs 3/6m到期、过期和最乐观6×8预算，旧审核不涉及实际Mac服务；真实未来 first call、Gmail receipt、成交时间和PNL均标 UNKNOWN。
5. 真实反例：任一来源Artifact ZIP SHA、内层JSON SHA、日期/身份/队列状态/候选删损，必须拒绝或明确独立未知，不能补造数据；单测应不依赖Binance实时访问，不能用mock表代替全部原始源核对。
6. 其他系统安全：没有修改旧经锁定的生产shadow和Stage28代码，不创建外部定时任务/Monster后台服务、发真实邮件/交易、也不改Frank。判断输出足以指导下一高价值早发现/队列改造，**不能直接让旧D1买入成立**。

按固定格式返回：**APPROVE | REQUEST_CHANGES | BLOCKED**、审核者/真实模型版本（如无法核实`UNVERIFIED`）、固定SHA、代码diff和触发workflow SHA、实际运行单测和源下载证据、逐项P0/P1/P2的行号/负例/修复方案、目前完全完成与尚未完成的服务链路。特别强调 `G0 PARTIAL / G1 NOT_SCORABLE / G2_G3 NOT_PASSED / G4 UNKNOWN / G5_FULL_RELEASE NOT_PASSED / G6 NO_GO`，`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`，即使代码审核通过也不能说历史净盈利、生产时效或部署通过。
