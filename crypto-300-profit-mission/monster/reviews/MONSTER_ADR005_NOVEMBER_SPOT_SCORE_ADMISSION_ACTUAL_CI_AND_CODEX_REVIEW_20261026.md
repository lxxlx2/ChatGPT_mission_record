# Monster ADR-005：已通过 T0+15天来源门禁后的 D0/D1→G1/G2/G3 评分准入层（2026-10-26）

**阶段**：`OFFLINE_SOURCE_TO_SCORE_ADMISSION_IMPLEMENTED_AND_REAL_CI_PASS`；增量**独立其他AI复审待完成**，G6继续`NO_GO`。这是实际已提交代码、测试与真实 CI，不只是计划；但**不承诺从未产生的数据算成绩**。

## 1. 新增代码与不可混淆的已批准范围

用户带回的独立Codex主代理审查、固定`48bf87fd0721071d8347f7f47df71253f2a835fc`，真实Mac Python3.14.7下T0 14 PASS、daily 10 PASS，加额外合成30份完整ZIP/CHECKSUM双币×15天通过，确认**APPROVE，严格只限原始HTTP归档准入及官方15天来源门禁**，未发现该增量可操作P0/P1/P2。真正11月实时市场身份未获得，不升级总体G0/G5/G6。该结论已[归档](MONSTER_ADR005_FORWARD_T0_DAILY_CODEX_SCOPED_APPROVE_20261026.md)。

下一工程缺口是：资料缺失时，任何后续D0/D1 replay 或G1/G2/G3计算入口必须知道**哪些symbol缺了基线、信号观察或未来2×标签**，不能仅依赖全局`verified_complete_all_15days`，更不能从后验获利币中选择出列。本轮新增：

- `local-agent/scripts/monster_v4_adr005_forward_spot_score_admission.py`，固定源码Git Blob **`a2f3fbd4c51b7ef7e6da88ace98db27a72ce7302`**
- `local-agent/tests/test_monster_v4_adr005_forward_spot_score_admission.py`，固定测试Git Blob **`04a5507eeac06045204393a3dac0923db3254931`**
- 一次性、**仅自己路径push触发且没有schedule**的离线CI入口 `.github/workflows/monster-adr005-november-source-to-score-admission-once.yml`

**固定本轮代码+测试审核 SHA `3cab91ba45e68ce2e05e963b9d75da7e2afb4ff3`**。本次后续文档提交不替代审核SHA。原已获外部批准的D1 V2源码Blob`d7afa1053f82fb5c6b13b91ef41d0836e4ca8094`和D2微秒源码Blob`c80dc799074e63230d88ebaf81bf573a870b91e1`均未改。

## 2. 可执行链路与数据分层

命令入口真实调用`t0.preflight(...原HTTP ZIP、逐端点回执)`，再用源准入结果`daily.census(...原官方ZIP与CHECKSUM)`验证**每个源字节及日历**，最终`join_census()`覆盖原T0符号全分母（必须每币15个唯一symbol/day）。不可缺行、复制行、丢失symbol、伪造success总数或segment计数；三窗日期锁死，Spot与单独USD-M Stage91不同，禁止混用。合成fixture只做本地单元测试，没有资格升级为2026年11月真实发行方来源。

每币独立记录三段完整度：
1. `BASELINE_24H`：前1日官方1m ZIP完整SHA且1440根；
2. `D0_D1_OBSERVATION_7D`：7日每份来源全验；
3. `FUTURE_2X_LABEL_7D`：事后7日各份来源全验。

分类：
- 基线/观察有任何缺失、未闭日或损坏：`D0_D1_SOURCE_BLOCKED`；
- 基线+观察齐全、未来7天GT标签有未取：`D0_D1_SOURCE_READY_GT_LABELS_BLOCKED`（**仅技术上具离线D0/D1源条件，G1/G2仍不能算**）；
- 15日来源全部齐全：`SOURCE_COMPLETE_OFFLINE_REPLAY_ONLY`（仅可推进后续**独立离线计算**，**不代表已调用真实D0/D1原模型，不代表完整动态市场或交易所签名回执**）。

每个币保留`original_d0_watch_event_id=None`、`original_d1_research_event_id=None`、`gt2x_label_event_id=None`、`original_d0_core_executed=False`等，直到后续真正产生且独立审查真实派生事件，不能靠日历/来源齐全产生虚假的WATCH或2×赢家。所有`G1 NOT_SCORABLE / G2 UNKNOWN / G3 NOT_SCORABLE / G4 UNKNOWN / G6 NO_GO`；在元数据只**引用**冻结规则，不根据十月已曝光失败样本调整阈值：`G1>=20个独立2×、>=3独立窗口、strict>=90%、提前5m>=85%；G2>=80%留存；G3平均<=5/day、峰<=12`。

无T0情形完全不访问分钟目录也不会产生旧511或其他臆造人口：同时调用已审核`t0.preflight`、`daily.planned_source_readiness`，仅输出三段日历与`POPULATION_UNKNOWN/NOT_SCORABLE`。运行不会请求交易所、生产DB、Frank、用户Mac、Gmail、交易账户，也不会创建cron或后台任务。

## 3. 实际CI和GitHub真实Artifact

[GitHub Actions #40237630315](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40237630315)绑定固定源码SHA **`3cab91ba45e68ce2e05e963b9d75da7e2afb4ff3`**、Ubuntu Python3.11，已**SUCCESS**，实际日志读取为`14 + 10 + 14 = 38 PASS`（0 fail）；其中新14项真实验证源分母、30个symbol×day的合成完整覆盖标签仍不得冒充G1通过、未来标签缺失、基线缺失、观察缺失、重复/缺少symbol/day、篡改source status总账、未登记日期、真实10月Stage163源拒绝、无T0目录拒绝和冻结门槛元数据。**从未向真正未来11月发出实时数据请求**。

真实GitHub Artifact **`12614699385`**（`monster-adr005-3window-g1g2g3-source-admission-unknown`）本会话通过接口下载，zipfile原生重新解包、全部JSON解析后核对三份：
- `2026-11-02.json`、`2026-11-16.json`、`2026-12-01.json`
- 都是`WAITING_FOR_PRESTART_SOURCE_WINDOW`、原T0人口`null`、15个未来UTC源日历、G0`POPULATION_UNKNOWN`、G1`NOT_SCORABLE`、G2`UNKNOWN`、G3`NOT_SCORABLE`、G6`NO_GO`，没有假装已采集或已产生2×事件。
- ZIP外包SHA256 **`b524376353e02cba090fa041dc6110722dce93ff7be7284737084aed2b50a5f0`**，ZIP CRC`testzip()`通过。请外审不要将此证据当成交易所真实11月T0或未来label验证。

## 4. 待其他AI独立增量审查清单

在**固定SHA `3cab91ba45e68ce2e05e963b9d75da7e2afb4ff3`** 的独立detached只读worktree中比对前获批T0/daily SHA `48bf87fd...`增量，执行：
```sh
PYTHONPATH=crypto-300-profit-mission/local-agent/scripts python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_adr005_forward_spot_t0_gate.py -v
PYTHONPATH=crypto-300-profit-mission/local-agent/scripts python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_adr005_forward_spot_daily_gate.py -v
PYTHONPATH=crypto-300-profit-mission/local-agent/scripts python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_adr005_forward_spot_score_admission.py -v
```
独立复现`15/15全部来源完整但仍不得G1评分`与`只有未来label缺一天时D0源可用但G1/G2不可评分`；检查symbol/day覆盖、原T0字节SHA/receipt重新进入真实CLI而非接受伪造census、未来源精度、旧10月T0拒绝、无T0不产生人口与事件。**重点找新代码入口是否可以误接受假包、伪成功或未经模型执行就标为G1/G2/G3达标**。审查输出`APPROVE|REQUEST_CHANGES|BLOCKED`，绑定型号/环境、测试与Artifact原值、文件行号及P0/P1/P2。确认前本新增source-to-score适配器的G5只记`REVIEW_PENDING`。

## 5. 真实剩余里程碑和安全

还缺真正**前瞻源采集时钟证据**（无用户另授权后台运行）、完整原D0/D1 same-core实时/离线重放、客观未来2×赢家的独立评分、跨三窗≥20事件有效性、可执行实际双侧盘口及净费率证据。下一代码模块应再将已验证的发布方1m严格适配原D0→D1逐3m/5m回放；但不得以Stage92的旧USD-M分母或人工合成事件代替真实Spot全市场研究结果。

门禁保持`G0 PARTIAL / G1 NOT_SCORABLE / G2 UNKNOWN / G3 OCT_EXPOSED_NOT_PASSED,NOV_NOT_SCORABLE / G4 UNKNOWN / G5 PREVIOUS_PATCHES_APPROVED_AND_NEW_ADMISSION_REVIEW_PENDING / G6 NO_GO`。**NO_MERGE / NO_DEPLOY / NO_MAC / NO_AUTOMATIONS / NO_GMAIL / NO_TRADES / NO_NEW_RPC**。