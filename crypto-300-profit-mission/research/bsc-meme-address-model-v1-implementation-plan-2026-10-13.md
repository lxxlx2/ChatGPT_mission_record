# BSC Meme 地址分析模型 V1 — 分阶段实施计划与真实进度（2026-10-13）

**Authority:** `bsc-meme-address-model-v1-requirements-2026-10-13.md` (G0 frozen); `MISSION_SPEC.md`; `docs/REPOSITORY_STRUCTURE.md`; `README_BSC_MEME_TOP_TRADERS.md`.  
**Change safety:** 研究只读；不重扫历史 437 个转账组合；不更改 Frank/Monster、Mission runtime、state/current、交易/通知；`NO_GO`。  
**Development process:** 数据调查 → 模型/技术方案 → 研究分支开发 → 其他 AI 独立 Review → 单元/集成/链上验证 → 只读本地部署验收（仅获授权才进行） → 修复 → 复核。每个阶段 Git 留可复算证据和 blockers。

| Phase | What / deliverable | Reuse / evidence | Gate | Initial state |
| --- | --- | --- | --- | --- |
| **P0 Freeze** | 还原并固定用户真实目标、样本/收益/漏买/跟单门禁；建立独立 research branch & Draft PR | README + V21 + Stage17–26 + repo rules | G0 | **DONE（Git + CI）** |
| **P1 Baseline** | 确定性只读 `23×19` 对照 manifest；每个地址 19 CA 状态/2026 major/未知标记；证据来源版本；单元测试、防误判 | 423KB V21 真实冻结矩阵（437 complete）和原 Stage17–26 摘要 | G1 + G2 structure | **DONE（确定性 P1 + CI）** |
| **P2 Cross-wallet economics** | 23 地址都进入同一张经济证据表；按“原始闭合且已结算 / 账户余额范围 / 混合报价 / 未确认”区分，保留亏损、前两大机会占比；对现有文件逐项映射 | Stage16/17/18/23–26, 239E/DDAC/5C0C etc | G2 evidence tiers + G3 | **PARTIAL: 25 closed rounds/4 wallets/19 unknown; source pinned + CI PASS** |
| **P3 2026 priority** | 冻结 2026 年重大行情币（牛来/MARSCOIN/龙虾/我踏马来了等）及候选真实本人买卖/最新 UTC，**最近 30 天** 真实 Swap 三态 | 全覆盖转账 + 原 tx/receipt，最多补查关键原始事件 | G4 | TODO |
| **P4 Wallet clustering / eligibility** | 逐笔原始出入账追踪与账户关联，不用共同交易对/收币地址直接推断同控；可执行机会 vs UNKNOWN miss | 23 wallet funding + first-buy venue / true first tradable moment | G3/G4 | TODO |
| **P5 Frozen real follower replay** | 观察者首次能看到签名/交易时刻，延迟 **1/5/15 分钟**，固定小额/合理费用/池容量与真实退出；加入全部亏损/缺席机会和不可成交情形，2026 untouched 期间独立验证 | Follow V0/V1 作为警告基线，不将 24 条 what-if 算实际成交 | G5 | TODO |
| **P6 Independent review/test** | 请另一 AI 审查核心代码、来源、时间因果、阈值/样本泄漏、证据标签、所有失败项；修复后全套 tests + CI，QA 复核 | 本分支 Git 证据 + CI | G6 | BLOCKED until P1–P5 |
| **P7 Read-only local UX** | 若用户授权才进行只读研究结果展示与 Mac 实测，不触碰现有 Frank dashboard/交易信号路由 | 仅 G6 review/test 通过 | Separate user authority | BLOCKED / NO_GO |

## P1 数据契约（先实现，禁止先编造算法收益）

脚本建议：`bsc_meme_address_model_v1.py`，pytest/unittest 用 `test_bsc_meme_address_model_v1.py`。仅标准库、确定性离线输入，且**不导入/执行**已废弃的 GMGN 脚本，不联网、不用 RPC key。

输入：
- 冻结原始 `BSC_MEME_23_EOA_19_CA_EVIDENCE_COMPLETENESS_OVERLAY_V21_2026-10-12.json`（23×19）；
- 与用户明确批准的重大币子集的 YAML/JSON 静态参数（当前严格使用原已确认 exact CA）；
- 后续经济证据 **只允许 verified claim record 显式 source/proof 类型加载**。P1 没有 full PnL 证据时输出 `UNRESOLVED`，不能默认为亏损。

输出：
- `bsc-meme-address-model-v1-baseline-2026-10-13.json`：source path/sha、全 437 分类/每个地址 19 状态、unknown 概率**绝不评分**、查漏优先队列；
- 一份人可读校验报告，强调**research priority ≠ profit rank**；
- 单元测试：确切 437、148、有/无正值、缺失状态不会被误解成零 PnL、非本人转账不会变成买入、2026 年关键 CA 对齐、确定性排序、未知最近活动不会被判不活跃、零假胜率。

**P1 放行的必要条件：** 23 wallets、19 CA、437 unique cells、148 present、289 absent、无原始字段拼接重号；所有经济、主动交易和近期字段默认 `UNRESOLVED`，只从来源中已有强证据升级；测试输出/输入 Git SHA 记录一致。此模型最初只提供**全体钱包覆盖和后续经济调查优先级**，不能自行发布盈利排行。

## P2/P3 的唯一正确推进方式

先横向 **23/23** 生成一页可信证据表，先标注谁在 2026 年主要币“直接主动签名已证明”、谁只转账、谁真实已兑付、多大比例利润来自头号大胜币；随后选证据质量最高且近期交易最相关的 **3—5** 个地址，集中完成必要的 quote/gas 查漏，不能再因为 8E6B 有未审计币就只研究 8E6B。

排序**仅限研究优先级**：2026 重大 token ERC20 有正值作为待核查线索、跨币覆盖、来源完整度、负控制存在。排名标注 `RESEARCH_PRIORITY_ONLY`；最终交易收益排行榜必须通过 G3。

## 当前已证实而不得误报为模型完成

- V21 原始转账分页/代币数量：**437/437、148 observed、289 absent**；**不是** 437 个交易 PnL。
- Stage26 对 8E6B 选择的 6 重大币，有 **17** 个已选完整库存回合，**10 positive /7 negative**（混合单位须另算），**不能**称全市场胜率。
- 2026 active signed meme swap、所有候选的统一 PnL、真实 missed eligible denominator、真正延迟成交回测 **未完成**。
- 原 Follow V0/V1 属于事后样本、部分非因果历史池报价模拟，**不能并作正式 G5 通过**。

## 证据源被更新的处理

源数据更新只创建新版本 manifest 和新的审查提交；不原地替换旧冻结证据。原始人可读历史报告不批量迁移。每轮开始先核对 PR base HEAD/当前引用文件 sha，所有例外显式放入 blocker 字段。结论必须区分 `CONFIRMED / INFERRED / UNRESOLVED / SPECULATIVE`。

## 本分支交付状态更新规则

本计划阶段状态仅由相应 Git 提交 + 可重复校验 + 明确未完成缺口推进；不得因为打印报告就宣称通过独立 AI Review 或实际部署。外部独立 Review 应另留 SHA、审查者、问题、修复和复查链接。

## 2026-10-13 P2 first batch committed (reproducible)

- P0 requirement freeze and Draft PR #40: **DONE**.
- P1 23×19 source-pinned baseline: **DONE**, 437/437, 148 ERC20 present, 289 absent, eight V21 null-merge count caveats; no fake PnL.
- P2 importer first pass: `bsc_meme_address_model_v1_p2.py` + `test_bsc_meme_address_model_v1_p2.py` + `bsc-meme-address-model-v1-p2-evidence-ledger-2026-10-13.json` + `bsc-meme-address-model-v1-p2-economic-comparison-2026-10-13.json` + `bsc-meme-address-model-v1-p2-cross-wallet-economics-review-2026-10-13.md`.
- **Actual first import: 25 signed completed episodes in only 4 of frozen 23 wallets**. 16 positive, 9 negative within selected studies; 4 WBNB/gas direct proof, 19 native wallet event-block only, 2 mixed BNB/USDT historical spot valuations. Remaining 19 **UNRESOLVED**, not zero profit, no ranking.
- CI check `BSC address model V1 (read-only research)`: P1+P2 offline unit regressions and source/blob/manifests/committed JSON exact deterministic comparison passed on code/evidence commit `9e5c000ffa62c4ebbfb97ac5653eaaf243715c9b`, GitHub Actions run `38314235399`. Independent other-AI review remains **NOT DONE**.
- **NEXT REQUIRED**: expand comparable P2 settled evidence to A83B, ADFF, 2ADF, 0ABB, 877AF, 239E, and DDAC (2026 major opportunities, source signer/receipt); evaluate stale/active signed trades, then P4/G4 opportunity denominator and P5 follower replay. Do not optimize returns on these already handpicked positive episodes.
