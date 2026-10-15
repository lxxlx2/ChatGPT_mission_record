# Stage145 — Claude / other AI fixed-SHA independent re-review prompt (copy all text below)

请作为另一名严格独立AI审查员，对 Monster 妖币研究模型进行**第三轮修复后代码审查**。必须真正读取**固定代码SHA**、复现先前 Claude 的 P1 错误、运行模型源代码，不要只看 CI 结论或这份提示词。

**仓库**：https://github.com/lxxlx2/ChatGPT_mission_record
**原 Monster Draft PR**：https://github.com/lxxlx2/ChatGPT_mission_record/pull/30
**分支**：research/monster-v4-local-discovery-20261010
**本次修复代码审核固定 SHA（必须 checkout）**：`51f2eca3646db72158c42e7cfca5322c76e58c83`
**上次 Claude 返回 REQUEST_CHANGES 的 SHA**：`baf48e2022910ab9212f27ccb9e6a09b1f6586da`
**上一轮修复但未正式过独立批准的 Stage143 SHA**：`5fd3138702a3caef69ce2d48696059bceeefd6f9`
**最早 Stage142 Claude REQUEST_CHANGES SHA**：`ff711ebef8367635871004f27a98838f7aa8c4f3`

须报告你实际审核的 Git HEAD、模型身份和模型确切版本（若不知道写 UNVERIFIED）。PR 浮动 HEAD 若在本提示词文档提交后前移，**不准用它冒充你检出的固定源码 SHA**。

先阅读这些当前 Git 路径：
- `crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md`
- `crypto-300-profit-mission/monster/MONSTER_STAGE145_EXTERNAL_CLAUDE_REVIEW_INTAKE_20261015.md` （第二轮 Claude 真正的 REQUEST_CHANGES）
- `crypto-300-profit-mission/monster/MONSTER_STAGE145_FROZEN_P1_CAUSAL_D1_VISIBILITY_AND_ALL_COHORT_MISS_BOUND_PROTOCOL_20261015.md` （修改前冻结）
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage137_dynamic_t0_original_core_causal_replay.py`
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage138_manual_evidence_scorecard.py`
- `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage137_dynamic_t0_original_core_causal_replay.py`
- `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage138_manual_evidence_scorecard.py`
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_shadow.py`（原冻结 D0；Git blob `bc958b3d90a8a52afa51515cb53f7e5fafaffaaa`）
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage80_dual_entry_core.py`（原冻结 D1）
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage134_t0_population_readiness_bridge.py` / Stage135/Stage136 及相应测试
- `.github/workflows/monster-stage143-claude-p0-p1-remediation-integrated-offline.yml`

**最重要检查：上轮 P1-1 已发现新币即使延迟5分钟才可见，D1却读了发现前的3根一分钟K线。**
真实 repro：来源首次2026-10-28 06:21 UTC、假设可见06:26（延迟5m）；Stage144 A读回历史版 D1=07:24，即首次可见58分钟后，未到61分钟。Stage145 现在对每个 0/1/3/5m 发现假设分别保留 A 和 B：
- A = 启用 publisher 过去已经公开的1m历史读回假设，之前的代码路径；这只是可得性乐观假设，**不是真实实时到达证据**。
- B = 严格从合约第一次可见分钟开始积累源；原D0的自然UTC完整5m queue只接收OPEN>=可见时间的bar，冻结 Stage80 D1 仅当从可见时间开始有至少61个真实已闭合一分钟bar时才允许 features；不足时必须 `features=None` 保留D0。上述06:26 case严格D1不得早于**07:27**，第一根允许5m必须从06:30 OPEN开始，不能夹带06:25已开始的5m。
- 两套必须对同一个官方格式source、同一UTC原 D0/D1策略和固定首次未来HIGH×2进行独立SQLite重放；不能修改原策略阈值、重贴标签或用后验 2x 选新候选名单。首次poll>=首次可见+3m并对齐原3m全局钟。请检验 B是否可能偷看发现前的D1输入、5m或quote24，A/B费用与真实收益是否被错误暗示。**A/B不能在无额外假设下被称为数学意义的召回率上下界**；不能自称真实发现时延。
- 对比0m模式的A/B D0/D1必须相同。对1/3/5m模式，分别检查 D0/D1（某个场景可不触发）、first tick，D1原评估路径、首5m源、固定首×2，缺源应 NOT_SCORABLE。Unicode代理只能在隔离SQLite，不能泄漏至交易所真实请求。特别检查原D0同一门槛100k quote24、冷却和队列准则完全未改变。

**P1-2：原悲观场景漏了新币2×。**
Stage138旧 `population_coverage_sensitivity` 的 `gross_2x`/ `D0_early5_2x` 只属于 PREEXISTING; 旧悲观率只算 `preexisting_early/(preexisting_2x+censored)`。当前版本加入新 IN_WINDOW 与最近 preT0 各自 2x/high 和 D0 early5，总和源齐全 all-three-cohort 分子/分母，再加所有 source-censored 或 unsupported 人口当成“假设漏报2x”的分母。请独立检查合成案例：已存在币 1个2x且提前发现1个，新上市1个2x漏报，preT0新近上市1个2x漏报，另CENSORED一例 => old preexisting-only 100%，全来源已知1/3=33.333%，全部缺档均为漏报2x的悲观假设1/4=25%。**这不是统计置信下界，也不是验证过的Crypto G1召回率**。要分cohort展示，未知结果不能被改为实际亏损或确认无信号。检验 cross-window synthetic aggregator 与 manifest 自一致性校验没有使用旧缺漏字段、SOURCE_CENSORED不会偷偷消失。

**请顺带复核其他先前重要事项，但不要凭空制造边界问题**：
- Stage143 T0前6h才上市初始合约不再强制需要上市前24h publisher日ZIP；首归档和T0 onboardDate有差异时继续CENSORED；它还是PIT未确认；
- 新上市币 D1 应纳入G3日负载总数（所有原有+窗口内+T0前短龄cohort），不过这不是实际邮箱投递成功率；
- 旧 Stage144 FASTUSDT 原D0的0m和1/3m可在06:30发现，5m错过初涨 baseline 吸收，无交易净收益或实际市场 Alpha；
- 原冻结 Stage116 2026-10-14 06:00 UTC首源失败不可倒补，Stage118/127已拒绝，Stage132追涨即买负收益，Stage140仅一次性初始525 Binance WWW-mirror USDT永续原快照（523 COIN typed/2 INDEX，issuer/PIT未证实，源嵌入时钟约落后8h44m，标准fapi地区451）。尚无完整7日前瞻官方publisher归档与真实 `!contractInfo` 实时上市事件、实际盘口深度和真实可买卖退出后的净收益。正式 G0 PARTIAL，G1 NOT_SCORABLE，G2/G3 NOT_PASSED，G4 UNKNOWN，G5 旧审查为 REQUEST_CHANGES、新代码未审，G6 NO_GO。绝不能称模型已验收可交易。
- Reviewer P2 的首 poll 实际延迟与名义N折叠、首次HIGH2x早于可能poll、持续上涨和回落path可作为非阻断建议；优先实际影响真实机会早发现或被高估的功能问题，不因低价值边界扩大范围。

**GitHub Actions实际源码测试日志**（两次均固定 `51f2eca3646db72158c42e7cfca5322c76e58c83`，请自己独立获取）：
- Stage134–138全链路 https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38696256023 — macOS和Ubuntu各80/80 PASS，原 V4 D0/Stage80 D1/原 source ZIP+CHECKSUM/mock fixture，且未授权HTTP/无任务/Gmail/交易/Frank变动门禁PASS。
- Stage138 https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38696255943 — macOS和Ubuntu各33/33 PASS，真实跨窗口代码+合成输入，其中源缺档未冒充模型负例。
在固定SHA检出的 `crypto-300-profit-mission/local-agent/scripts` 目录自行执行：
`python3 -m unittest -v test_monster_v4_stage134_t0_population_readiness_bridge.py test_monster_v4_stage135_full_market_publisher_minute_coverage.py test_monster_v4_stage136_manual_publisher_archive_acquisition.py test_monster_v4_stage137_dynamic_t0_original_core_causal_replay.py test_monster_v4_stage138_manual_evidence_scorecard.py`

**回答格式**：审查模型身份和精确固定 SHA、`APPROVE | REQUEST_CHANGES | BLOCKED` 代码审查结论、先前两P1逐条已修复/未修复及复现结果、新发现的P0/P1/P2问题（准确文件+行号+最小复现、对真实早报/延迟/漏报/可执行的影响、最小修复建议）、原D0和D1源是否保持冻结；把未知事实写 `UNVERIFIED`。不得将代码 APPROVE 升级为 G0–G4 PASS；无论结论是否通过，保持 **NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE**、FRANK_UNCHANGED、手动采集节奏不变。G5只有实际独立复审反馈处理完才能更新，提示词本身不是审批。
