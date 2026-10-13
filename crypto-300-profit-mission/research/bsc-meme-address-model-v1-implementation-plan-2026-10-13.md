# BSC Meme 地址分析模型 V1 — 分阶段实施计划与真实进度（2026-10-13）

**Authority:** `bsc-meme-address-model-v1-requirements-2026-10-13.md` (G0 frozen); `MISSION_SPEC.md`; `docs/REPOSITORY_STRUCTURE.md`; `README_BSC_MEME_TOP_TRADERS.md`.  
**Change safety:** 研究只读；不重扫历史 437 个转账组合；不更改 Frank/Monster、Mission runtime、state/current、交易/通知；`NO_GO`。  
**Development process:** 数据调查 → 模型/技术方案 → 研究分支开发 → 其他 AI 独立 Review → 单元/集成/链上验证 → 只读本地部署验收（仅获授权才进行） → 修复 → 复核。每个阶段 Git 留可复算证据和 blockers。

| Phase | What / deliverable | Reuse / evidence | Gate | Initial state |
| --- | --- | --- | --- | --- |
| **P0 Freeze** | 还原并固定用户真实目标、样本/收益/漏买/跟单门禁；建立独立 research branch & Draft PR | README + V21 + Stage17–26 + repo rules | G0 | **DONE（Git + CI）** |
| **P1 Baseline** | 确定性只读 `23×19` 对照 manifest；每个地址 19 CA 状态/2026 major/未知标记；证据来源版本；单元测试、防误判 | 423KB V21 真实冻结矩阵（437 complete）和原 Stage17–26 摘要 | G1 + G2 structure | **DONE（确定性 P1 + CI）** |
| **P2 Cross-wallet economics** | 23 地址都进入同一张经济证据表；按“原始闭合且已结算 / 账户余额范围 / 混合报价 / 未确认”区分，保留亏损、前两大机会占比；对现有文件逐项映射 | Stage16/17/18/23–26, 239E/DDAC/5C0C etc | G2 evidence tiers + G3 | **PARTIAL: 50 curated signed closed rounds/7 wallets/16 unknown; CI 65 unit tests PASS; no lifetime PnL rank** |
| **P3 2026 priority** | 冻结 2026 年重大行情币（牛来/MARSCOIN/龙虾/我踏马来了等）及候选真实本人买卖/最新 UTC，**最近 30 天** 真实 Swap 三态 | 全覆盖转账 + 原 tx/receipt，最多补查关键原始事件 | G4 | **IN_PROGRESS: 71/71 original hashes read (70 parsed, 1 truncated); 38 owner / 36 third-party / 1 unknown wallet×tx pairs; 1 A83B/TST confirmed signed Pancake V3 swap; economic and other wallet activity pending** |
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

## 2026-10-13 P2 second batch: cross-wallet IFML/Lobster, 2026 pending queue

- Added `239E` to P2 economic model from **existing** complete originals: `BSC_MEME_239E_TWO_MAJOR_FULL_SIGNED_FLOW_SOURCE`, both exact-CA owner signer/receipt QA, and zero-inventory native balances. **27/27 owner signed and receipt SUCCESS, seven complete zero-to-zero rounds: 5 positive and 2 negative original wallet native N-1/N block scopes, net +0.296492314017711706 BNB**, NOT fully trace-isolated causal PnL. Four representative original transactions and account deltas independently rechecked via read-only BNB archive RPC; 3 complete receipts and one success header only.
- P2 whole 23 EOA now **32 selected completed episodes, 21 positive, 11 negative across 5 wallets; 18 wallets have no imported economic evidence, never counted as zero profits**. Existing 19 CA data coverage frozen unchanged. The 32 are post-selected studied episodes, not a trading win rate.
- New `bsc-meme-address-model-v1-p2-2026-eligibility-blocker-queue-2026-10-13.json`: eight source-SHA-pinned economically INELIGIBLE/incomplete cases spanning A83B, ADFF, 0ABB, 877AF, DDAC, 2ADF, 8E6B, 5C0C. Examples: ADFF IFML partial exit, 877AF MARS partial first exit, DDAC Niulai full token inventory with signer unaudited, 8E6B Niulai still open, 5C0C MUBARAK native 66BNB untraced with plain transfers. CI must reject accidental promotion into economic complete episodes.
- Expanded P2 unit tests for **27 original tx signer/success/proof round partition** + cross-wallet positive/negative signs and eight blocker statuses. Dedicated CI regenerates JSON and checks every declared source Git blob SHA. See `bsc-meme-address-model-v1-p2-batch2-239e-and-2026-blockers-2026-10-13.md`.
- **Next required priorities:** resolve ADFF and A83B owner-signed 2026 IFML/Niulai/MARS/Lobster and 877AF MARS *complete* round costs, then DDAC/2ADF Niulai; maintain breadth. P3 last 30d true signed swap, independent Other AI review and G5 causal executable lag remain blocked. **NO_GO**.

## 2026-10-13 P2 Stage3: cross-wallet ADFF/2ADF three signed rounds, 25 unsigned raw-only segments

- Reuse exact source sha pinned `ADFF_WOTAMALA_FULL_CURSOR_BALANCE_QA`, `ADFF_LOBSTER_FULL_CURSOR_BALANCE_QA`, `2ADF_NIULAI_FULL_CURSOR_BALANCE_QA`. Offline raw token ledger segmented **114 ERC20 logs into 28 nonnegative zero-to-zero inventory cycles**. This is **NOT 28 signed economic trading returns**.
- BNB mainnet read-only RPC independently fetched original signer and receipt status **8/8**, wallet historical N−1/N original BNB deltas **8/8**, and six first/last block UTC headers. Only **4/8 receipt bodies full**, other four status confirmed without full trace/gas. Three qualified owner signed cycles:
  - ADFF IFML first: 2025-12-29 UTC, four owner tx, wallet native block scope **+0.015276607477319522 BNB**. First partial exit was eventually closed by two more sells; true inventory closure;
  - ADFF Lobster fourth: 2026-02-27 UTC, two owner tx, **+0.004522437855804654 BNB**;
  - 2ADF Niulai first: 2026-08-14 UTC, two owner tx, **−0.022303778278468502 BNB**.
- All three import into `bsc-meme-address-model-v1-p2-evidence-ledger-2026-10-13.json` as `SIGNED_NATIVE_BLOCK_SCOPE`, **NOT fully causally traced settled PnL**, no wallet profit ranks. The other **25 raw inventory cycles stay UNKNOWN** even though inventory zero. Source-rich machine sample: `bsc-meme-address-model-v1-p2-stage3-adff-2adf-owner-closed-rounds-2026-10-13.json`; report: `bsc-meme-address-model-v1-p2-stage3-adff-2adf-signed-trades-2026-10-13.md`.
- P2 now **23 wallets represented**, of which **6 have selected source-signed economic episodes**: **35 selected rounds, 23 native/historical-quote positive, 12 negative, 17 wallets P2 economic evidence UNKNOWN**. This is not 23/35 a statistically meaningful win rate.
- 8-case `bsc-meme-address-model-v1-p2-2026-eligibility-blocker-queue-2026-10-13.json` resolved earlier ADFF IFML partial and first 2ADF Niulai case, replacing with ADFF MARSCOIN + Niulai still-open net inventory; prevent stale blockers colliding with new proven sample. Original immutable history preserved as Git.
- Dedicated Github Actions **42 offline regression tests passed**, source manifest pin checks, blocker exclusions, and source JSON determinism verified at `https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38319768111`. Independent *other AI* review NOT performed.
- P2 **NOT DONE**: prioritize remaining A83B / ADFF 2026 major / 877AF MARS / DDAC & 2ADF Niulai signed quote settlement, then P3 true recent signer and P5 historically executable follower lag. No GMGN payment, Frank/Monster changes, emails, monitor or deployment. **NO_GO**.

## 2026-10-13 P2 Stage4 — precommitted breadth-first 2026 negative controls

- Frozen BEFORE fetching relevant original transaction/cashflow via `bsc-meme-address-model-v1-p2-stage4-precommitted-2026-10-13.json` (immutable prior Git blob `c4477d02dac3de5fda2435c8a1ba226313a3c52c`): for two frozen source pairs A83B/Niulai and 877AF/MARSCOIN select the first chronological raw-token 0→0 cycle AFTER R1 with no more than three distinct original transaction hashes, with no PnL-aware threshold changes.
- The exact selected **A83B/Niulai R2 (2026-08-15)**: three EOA self-signed successful tx, two buys occur in ONE original block. Native BNB account N−1/N changes across TWO UNIQUE blocks **−0.213598956812665039 BNB**; do NOT double count the same block for two buys.
- The exact selected **877AF/MARS R4 (2026-07-27)**: three EOA self-signed successful tx, three unique blocks **−0.026064663781901692 BNB**. All six receipt success headers visible, all six receipt bodies truncated, NO causal internal accounting or full Gas attribution.
- Original frozen full two-way raw inventories **A83B/Niulai 158 transfer logs, 12 raw zero cycles**; **877AF/MARS 170, 21 raw zero cycles plus final 68,700,271,596,483,656,647 raw token units remaining**. Not 33 realized trading PnL cases. Any untested raw cycle remains unknown.
- Evidence `bsc-meme-address-model-v1-p2-stage4-two-negative-2026-signed-rounds-2026-10-13.json`; stage4 report `bsc-meme-address-model-v1-p2-stage4-a83b-877af-negative-control-2026-10-13.md`.
- Structural correction: previous absolute `wallet×CA` blocker would incorrectly forbid a valid separately confirmed round if other cycles/remaining tokens unresolved. Now block at **wallet×CA×episode** and permit exactly `A83B/Niulai R2` and `877AF/MARS R4` while **11 and 20 other respective raw cycles remain unproved**, both whole-CA PnL `UNRESOLVED`, all 8 blocker rows retained.
- P2 selected closed original signed episodes now **37 total: 23 positive /14 negative in 7 wallets, 16 wallets not yet economically curated**, no lifetime wallet PnL rank. Fully source-pinned, deterministic unit regression `test_bsc_meme_address_model_v1_stage4.py`, GitHub Actions **47 tests PASS** `https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38321361849`. Other independent AI Review still NOT DONE.
- Next: cross-wallet breadth (not 8E6B-only), finish additional 2026 major wallet negative/positive settlements with bounded attribution, then P3 true last-30d owner signer and P5 causal follower lag. Production/runtime/monitoring/trades **NO_GO**.

## 2026-10-13 P2 Bulk 16 completion — full batch before moving to P3

- **Precommitted fixed economic evaluation** of 16 previously unadmitted ERC20 zero-inventory source cycles from 7 frozen wallet+major-CA pairs, exactly 39 original tx hashes; source-only selection committed before examining signer/receipt/cashflow. Evidence: `bsc-meme-address-model-v1-p2-bulk16-precommit-2026-10-13.json`.
- 34/39 original owner signers, 38/39 readable success receipts. **13 fully signed/successful cycles** (31 owner tx), **3 excluded/UNKNOWN**, including a raw original tx truncated and two cycles with other parties' original tx; no replacement samples.
- 31 unique `wallet|block` historical original N−1/N wallet BNB balances **all verified** with de-duplication and positive/negative results: **9 native-positive /4 native-negative**; some internal quote/gas traces still unverified. Ten of thirteen admitted rounds started in 2026; three ADFF/IFML rounds started on 2025-12-29 UTC and must not be mislabeled 2026.
- Machine truth: `bsc-meme-address-model-v1-p2-bulk16-gate-decisions-2026-10-13.json`, seven `bsc-meme-address-model-v1-p2-bulk16-tx-part*.json`, four `bsc-meme-address-model-v1-p2-bulk16-native-part*.json`, and `bsc-meme-address-model-v1-p2-bulk16-verified-outcomes-2026-10-13.json`. Full report `bsc-meme-address-model-v1-p2-bulk16-complete-review-2026-10-13.md`.
- **Current P2 evidence matrix 23 wallets /50 selected signed closed episodes: 32 positive,18 negative across 7 wallets; 16 wallets have no imported economic verdict, NOT zero-profit.** No complete comparable lifetime wallet PnL, ROI rank, or followable alpha. 877AF/MARS R4/R5/R6/R10 source-audited while other same-CA rounds/residual inventory UNKNOWN; blockers are by `(EOA,CA,episode)`.
- CI source SHA, 31 unique balance blocks, duplicate avoidance, 16/16 all outcome accounting, 2025 vs 2026 and 50-row deterministic output verified at https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38374956363 (56 plus 9 = **65 unit regression tests**, separate workflow test steps).
- **NEXT:** freeze P3 current 30-day **original owner-signed real meme swaps** for all 23 EOA and classify last observed signed action; then P4 qualifying opportunity and independent P5 first observable 1/5/15-min follower replay. Other-AI review and local read-only acceptance pending. No paid GMGN, no production trading, Frank/Monster untouched. **NO_GO**.

## 2026-10-13 P3 takeover — evidence separation and reproducible gate

- Reviewed `MISSION_SPEC.md`, `PROJECT_ANALYSIS_FRAMEWORK.md`, `token_trading_principles.md`, root `docs/REPOSITORY_STRUCTURE.md`, the V1 requirements, original P2 bulk16 report, and source manifests. Earlier P2 remains **50 selected closed inventory rounds (32 native/quote-mark positive; 18 negative), 7 curated wallets, 16 UNKNOWN**. These are not full attributable lifetime wallet profits.
- P3 locked snapshot remains `2026-09-13T08:37:36Z` through `2026-10-13T08:37:36Z`; frozen 23 EOAs × 19 CAs, all **46 directional scans fully paginated**. Within this exact scope, **89 ERC20 Transfer events**, **8/23 wallets with transfers** and **15/23 without**. Zero observed on those exact CAs never proves the wallet inactive on other tokens.
- P3 precommitted frozen original transfer candidate manifest has **75 wallet/transaction pairings but only 71 distinct original hashes**. The two preserved original-signer source parts cover **16/71 hashes**: **10 owner-signature wallet/tx pairings; 7 third-party pairings; 58 pairings not originally signed/fully readable** including hashes not yet fetched. Neither receipt success nor an actual attributable market swap can be inferred from an original tx sender alone.
- Persisted fully source-blob-pinned `bsc-meme-address-model-v1-p3-signer-evidence-overlay-2026-10-13.json`, deterministic stdlib model `bsc_meme_address_model_v1_p3.py`, and adversarial `test_bsc_meme_address_model_v1_p3.py`. Tests protect against wrong time cutoffs, duplicated pairs, wrong source signer/wallet, absent frozen CAs being mislabeled inactive, and signed transfers masquerading as executed market swaps or profits.
- CI `https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38382233378` completed **SUCCESS** on `4d13d3cb127a23d217fd8162ab6ba2fabf354adf`; unit suites **66 + 9 = 75 PASS**, P3 independently regenerated and compared to committed JSON. This passes **offline P3 partial QA only**, not final P3 owner-signed Meme swap gate, G4/G5, independent other-AI review or production.
- **Next concrete batch:** fetch remaining **55 distinct original transactions** with complete original `from`/block matching, then success receipts, exact swap/quote-route linkage, UTC latest owner action per EOA and actual DEX pool venue. Preserve truncated receipts as partial; source `from` mismatch stays third-party. Summarize all 23 wallets, including UNKNOWN and negatives. Following this, P4 opportunity entry eligibility and P5 real 1/5/15-minute causal replay. **Do not** change frozen window, paid API, production/Frank/Monster, launch any monitoring, merge PR or declare alpha. **NO_GO**.

## 2026-10-13 P3 extended owner-source batch and first true Meme swap witness

- **Read-only original transaction coverage complete for frozen exact-CA candidate set:** 71/71 unique tx hashes queried, 70 complete original signer payloads and 1 previously truncated; 75 wallet-hash pairings split into **38 owner-signed, 36 third-party initiated, 1 unreadable**. This is scoped to **23 existing wallets, exact 19 CAs and frozen 30-day window**, not every coin ever traded by these EOAs. Eight immutable 7/6-record part files added as a single atomic Git commit `55ee47ea9bb7b2218f345430134d2ac4d16ec465`. No PnL or completed market swap inferred from signer alone.
- `bsc_meme_address_model_v1_p3.py --full-source` loads all 10 source shards with pinned Git blobs, verifies original hash/wallet/block match, and conservatively keeps full-source Swap, PnL and Alpha unknown before receipt/pool evidence. Regression CI `https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38383351985`: **79 offline unit tests PASS**, including forged signer, missing original hashes and duplicate cases.
- **First strict positive P3 market swap:** A83B `0xa83b73f5644cde337b61da79589f10ea15548811` self-signed successful BNB mainnet transaction `0xcfcc99e6a8d6900fa805cf5b8da72761e9d175455914772ebf394778d9d8aed4` at `2026-10-12T07:57:23Z`. Complete original receipt has TST (frozen CA `0x86bb94ddd16efc8bc58e6b056e8df71d9e666429`) transferred FROM original EOA INTO pool `0x16969fa79651bae11736f2f6576a86fe2726b42b`, pool's WBNB transferred to router `0x1de460f363af910f51726def188f9004276bf4bc`, and matching Pancake V3 pool Swap event; independent historical `token0`, `token1`, `fee` contract calls confirm TST/WBNB at that block. Verifiable source: `bsc-meme-address-model-v1-p3-a83b-tst-true-owner-swap-witness-2026-10-13.json` with original raw logs and exact block. It is an **owner signed actual TST sell Swap**. The WBNB pool-to-router leg does **not** prove final settlement to EOA, PnL, trader repeated success, or someone else's executable lag returns.
- `bsc_meme_address_model_v1_p3_swap.py` + `test_bsc_meme_address_model_v1_p3_swap.py` validate that single full-receipt witness against 71-hash pinned original and 23-wallet source, returning only **1 confirmed recently signed true Meme Swap wallet, 22 wallet verdicts still UNKNOWN**. All final economic/replicable returns remain UNRESOLVED. This is a partial G4 positive witness, **not** P3 completed signoff, independent AI review, or production authorization.
- **Next:** batch verify the other **37 owner wallet×original tx associations** with complete receipt or contract-filtered log evidence where the provider truncates receipts. Classify true swaps vs other owner-initiated operations with temporal ordering, then P4 eligible BSC major events + wallet funding, P5 causal 1/5/15 minute follower replay. Never use postselected profit rates, no production, paid GMGN, new monitors, merge, or unrelated Frank/Monster changes. **NO_GO**.
