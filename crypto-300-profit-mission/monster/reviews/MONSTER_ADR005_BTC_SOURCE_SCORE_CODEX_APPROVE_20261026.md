# Monster ADR-005：D0与研究RBTC D1 来源依赖拆分 P2 独立 APPROVE（2026-10-26）

**用户带回真实外部审查结论：`APPROVE @ 08340771a46e37856bad0b2b58cc4bdc97f37813`，严格仅限原评分来源准入层的BTC基准依赖修复。**

审核主体：Codex主代理；底层具体模型型号 **UNVERIFIED**；用户Mac，macOS27.0.1 arm64，Python3.14.7；独立detached只读worktree固定代码SHA，与上轮拒绝版 `3cab91ba45e68ce2e05e963b9d75da7e2afb4ff3` 比较，无修改/push、市场采样、Frank、后台任务/部署/邮件/交易。

**实际执行**：T0归档14 PASS、每日来源10 PASS、评分来源20 PASS，**44/44 PASS，0 FAIL/ERROR/SKIP**。审查者独立运行5种 `join_census()` 合成的全量自洽BTC来源场景，查明输入未变：
1. AAA全部15日有效、BTC 11/04观察日缺失 → AAA自身原D0来源就绪、研究RBTC D1**阻断**，报`D0_SOURCE_READY_RBTC_D1_BLOCKED`。
2. T0原名单无BTC → 不自动添加/删除，人口/attempt数保持原样，AAA D0就绪、D1阻断。
3. BTC基线及观察全恢复 → 研究D1源技术就绪 `SOURCE_COMPLETE_OFFLINE_REPLAY_ONLY`。
4. BTC缺最初24h基线 → D0源就绪、D1阻断。
5. BTC仅缺未来GT标签 → D1源仍就绪，但`all_source_15days_complete=False`。BTC本身`research_d1_target=False`、是来源人口基准而非策略购买目标。

独立读取 [GitHub Actions #40238490187](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40238490187) 成功+SHA+44项日志。读取Artifact **`12615773413`**，原ZIP SHA256 `7bb131f94639446253afb297084c1f58624efbac2cbd831c654b802e445cf8cf`，CRC检查完好；固定代码复算3份无源JSON与Artifact逐份解析相同，三窗 `WAITING_FOR_PRESTART_SOURCE_WINDOW`，`original_t0_symbols_total=null`、`btc_benchmark_in_t0_source_census=null`、`G1 NOT_SCORABLE/G6 NO_GO`。

**P2 = CLOSED；本次增量范围无新可操作P0/P1/P2。** 与旧拒绝版本比，T0归档、15天每日源、D1 V2、D2微秒代码Git Blob都未改；原D0/D1阈值、未到11月三个冻结UTC窗口、历史曝光数据未改。合成完整源证明程序分层正确，**不能**证明未来真实市场来源存在、G1/G2提前2×召回、G3未来提醒密度或G4可执行净收益。

门禁：`G0 PARTIAL (未来真实T0人口 UNKNOWN) / G1 NOT_SCORABLE / G2 UNKNOWN / G3 FUTURE NOT_SCORABLE, OCT EXPOSED_NOT_PASSED / G4 UNKNOWN / G5 SCOPED_BTC_SCORE_PATCH_APPROVED_ONLY / G6 NO_GO`。此批准不自动批准完整Monster策略或下一步增量源码。

**NO_MERGE / NO_DEPLOY / NO_MAC / NO_AUTOMATIONS / NO_GMAIL / NO_TRADES / NO_NEW_RPC**。此文件是用户实际提供Codex审查记录的Git归档，不冒充Codex在PR上亲自签名评论。