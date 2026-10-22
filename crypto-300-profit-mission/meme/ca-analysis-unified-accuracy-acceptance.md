# Meme CA 链上尽调统一查询：准确性改造与验收标准

**Current 2026-10-22 status: ORIGINAL_SINGLE_MODE_REQUIREMENT_STILL_BINDING / PARTIAL_CA_CODE_INSTALLED / REAL_DEEP_QUERY_FAILED / COMPLETE_REAL_RESULT_NOT_ACCEPTED / DOCS_REVIEW_ONLY** — see section 8
Original 2026-10-11 status (archival, not a claim about today): PRODUCT REQUIREMENTS / IMPLEMENTATION NOT DONE / PRODUCTION UNCHANGED
Date: 2026-10-11 Asia/Bangkok
Owner: Mission 300-3000 overarching product governance. Engineering handoff: Frank/Meme module.
Authority: `WALLET_CLUSTER_ANALYSIS_SPEC.md`, `../MISSION_SPEC.md`, `../local-agent/config/follow_policy_v1.approved.json` (Frank *follow-decision only*).
Observed regression: user-provided four screenshots of localhost `CA 链上查询`, token `Agency`, showing multiple `未确认`, three scan presets, missing external narrative and an expired `$30` quote.

## 1. Product decision and scope

The user requires **one complete, evidence-backed query** with the same practical data categories and clarity they can expect when looking at GMGN/FOMO/OKX Wallet, while using **no paid GMGN API**. A successful result must help decide whether this exact contract is risky, how holders/funders/LPs are connected, what first buy and dev activity occurred, whether market liquidity is credible, and what verifiable external narrative is spreading.

- Remove the user-facing `快速 / 标准 / 深度` choice in the **CA research UI only**. Preserve automatic internal lightweight preview and progressively deeper indexed/on-chain collection, but a preview **cannot be titled completed analysis**. The user does not select completeness vs speed; final output must be completeness-governed.
- Preserve the separate live Frank wallet-follow signal/decision system. **Do not alter Frank frozen BUY/WAIT policy, historical signals, follow quote size, source writer, trading state or delivery.**
- The manual CA query is **pure read-only due diligence**, available for any valid Solana CA independent of Frank and not an investment order.
- Success = truthful coverage, correct definitions, independent source reconciliation, useful structured conclusion, and real-device verification. A high test count, a fast placeholder, a healthy service banner, 500 raw signatures or a green “分析已更新” with many gaps **does not satisfy success**.
- Do not silently replace unknown results by unsupported values, insist that every wallet has one controller, or claim impossible universal certainty. If required evidence cannot be obtained, mark `INCOMPLETE_EVIDENCE` with exact missing rows, cause, alternative attempted and next source; **not** `ANALYSIS_COMPLETE`.

## 2. Verified defects in currently committed main

The following are **code/document findings**, not claims from fresh running Mac logs:

1. Current `server.py` includes user-facing `CLUSTER_PRESETS`. The highest `deep` preset visits up to 20 holder owners with at most **100 target-token address signatures + 50 funding signatures each**. No current-data invariant establishes that these arbitrary caps reach wallet birth, first acquisition or actual first funding. `WALLET_CLUSTER_LOCAL_TOOL.md` still describes three bounded modes.
2. `cluster.py` calls official Solana `getTokenLargestAccounts`, which returns the top **20 token accounts** rather than the top 20 beneficial owners or an exhaustive holder list. The code then filters special addresses **inside that same 20-row list** to compute provisional exclusion Top10. If enough LP/vault addresses occupy top ranks, the resulting ten free-holder accounts must be drawn from positions beyond that raw Top20. Hence `KNOWN_EX_LP_TOP10_PCT` is **not generally the actual exclude-LP Top10**; a numerically tidy “已识别池后Top10” may be incomplete.
3. Strict `EX_LP_TOP10_PCT`, `EX_SPECIAL_TOP10_PCT`, `CLUSTER_ADJUSTED_TOP10_PCT` are unresolved absent registry `normalization_complete`. The provisional values displayed alongside the strict unknowns can mislead users into thinking all special-address normalization was done.
4. `LARGEST_PROBABLE_CONTROL_CLUSTER_PCT = 0` currently means **no qualifying control group established by this finite investigation**, not proof of zero hidden coordinated ownership. A sampled possible relation share (e.g. 23.77%) is not equivalent to proved common controller; both belong in appropriately qualified, distinct facts.
5. The dashboard `app.js` explicitly says `未接入 X/FOMO 外部叙事检索`. It only outputs DexScreener supplied website/social hints. This does not meet requested narrative research.
6. Generic CA query in `server.py` and `app.js` displays `execution_quote_30_usdc` and `$30 实际可成交价`. This is inherited from `follow_policy_v1.approved.json` with `quote_usdc_amount: 30` and does not belong in generic token due diligence. Its archived 30-second quote expires by design and becomes an overprominent useless headline.
7. UI status `分析已更新` appears even with `UNRESOLVED` roles, `errors`, incomplete normalization or funding coverage. This conflates an HTTP/job success with a verified analysis completion.

Evidence: `local-agent/mission_agent/meme/cluster.py`, `local-agent/mission_agent/mission_control/server.py`, `local-agent/mission_agent/mission_control/static/app.js`, `local-agent/config/follow_policy_v1.approved.json`, and uploaded user screenshots. The screenshot's displayed percentages should be treated as **historical screen observations**, not independently re-verified current-chain percentages.

Official data capability references:
- Solana `getTokenLargestAccounts` = **20 largest token accounts**: https://solana.com/docs/rpc/http/gettokenlargestaccounts
- DexScreener public token-pairs, token profiles and community takeover endpoints: https://docs.dexscreener.com/api/reference
- Solscan holder pagination is documented but requires Pro API authorization and must **not** be treated as free by default: https://pro-api.solscan.io/pro-api-docs/v2.0/referenc/v2-token-holders

## 3. Single-mode user-visible result contract

One CA input, one `查询` action, background progress/provenance, one completed evidence report. Present **verified fact / supported inference / third-party claim / prediction** separately.

The headline must answer, with evidence:
- Contract identity: exact CA, mint owner program, mint/freeze/update authorities, Token-2022 sensitive extension risks and on-chain burn/lock/transfer controls. Never infer creator authority absence from null mint authority alone.
- Market: actual selected pool/pair, source timestamp, price, market cap vs FDV and denominator, liquidity, 24h volume, current buy/sell activity; independently compare a second source where available. Historical ATH must be accurately dated and its source and calculation defined. Do not confuse DexScreener reported market cap, FDV, main-pair liquidity and direct DEX pool reserves.
- Holder ownership: supply at a controlled slot, current largest *token accounts*, resolved **wallet owners**, all known pool/vault/CEX/router categories, accurately computed “excluding special addresses Top10”, percent remaining, and distinct eligible holder counts.
- Wallet concentration and relationships: real direct transfers, funding and multi-hop provenance where material; dev/treasury/insider links, common control **only with adequate non-public independent evidence**; public router/fee payer/CEX false cluster exclusions. Show dominant wallets with confirmed acquisition type, amount, price/quote, transaction URL, timestamp and wallet role.
- Trading provenance: first verifiable token **acquisition** vs first **market buy** must be distinct; the earliest buy found *inside a 100-signature window* may not be the true first buy. Reconstruct complete material purchase/sale movements when data allows and identify hops, transfers, unsupported routed swaps, and unpriced flows without pretending to know realized PnL.
- Token narrative: what the meme or project is about, earliest identified origin, actual official/team account, current X/community/launchpad discussion, narrative catalysts, concentrated KOL/community coverage when supported, timing and links. Explicitly separate **external narrative exists** from **its owner adopted this exact CA**. If verified official recognition is absent, say so in that one field without blanking the whole narrative section.
- Final assessment: specific chain contract risk, LP/liquidity, holder manipulation/insider risk, market tradeability, narrative authenticity/traction; evidence status and concrete warning conditions. Never give an unconditional “安全/可买” based on a superficial score.

User-facing cards should show useful results, not nine repetitive `未确认` badges. One compact `尚缺哪些证据` section lists missing data with blocker and attempted sources, while uncertainty intrinsic to ownership remains honestly explicit.

## 4. Data acquisition and computation plan

1. **Canonical snapshot + source provenance**: timestamp + slot/block identity for on-chain balances/supply/owners, timestamp and provider for markets, report run ID, exact CA; non-synchronous reads need captured slot divergence/staleness and reconciliation. Use decimal raw units and avoid floating point rounding in holder percentages.
2. **Full holder-rank sufficiency**: get complete *top eligible owners* required for each requested metric. The raw first 20 token accounts **alone cannot prove** top10 ex-LP/ex-special or ownership grouping when special addresses push eligible owners past rank20. Prefer reproducible mint-account enumeration/indexer pagination and on-chain spot checks. If no permitted pagination/indexing exists, do not display a purported exact filtered Top10; identify the bound and classify it as a partial lower-rank sample.
3. **Special-address evidence registry**: dynamically identify DEX pool / vault / token program / escrow / lock / burn / liquidity, owner/authority and known router/exchange public infrastructure, with address/contract/transaction evidence. Version and date every label; unknown addresses cannot be auto-reclassified by name. Do not require a human-created special-address tag before attempting on-chain role attribution.
4. **Progressive holder funding/history**: follow target-token account, owner, separate SOL/USDC funding, routed swap, related addresses and documented transfers. Page beyond initial 100/50 when evidence still material. Stop only at chain-verified relevant origin/first event, complete pagination, a demonstrable irrelevant branch or a reported provider coverage/budget limitation. Put observed oldest/newest times, pages, signatures and explicit completeness state per owner into report.
5. **Cross-holder relationships**: distinguish exact transfer/transaction link, probable owner from multiple independent non-public indicators, common *execution* bot and coincidental public infrastructure. No blind merger from common CEX or popular router. A `0%` confirmed-control result must read “在已覆盖样本中未建立共同控制证据” and show unresolved owner share separately.
6. **Official/public data first**: Solana finalized RPC, protocol/DEX program accounts, launchpad token-page data and verified program instruction semantics; DexScreener for market/pair hints; independently compare GeckoTerminal/other accessible public indexed data plus raw pool accounts where feasible. GMGN/FOMO/OKX public visible data are **comparison references**, not paid API requirements, not authoritative proof of controller identity. Never require GMGN paid access, deposits or private GMGN keys.
7. **Narrative enrichment**: exact CA lookup in official launchpad/pump.fun pages, token profile URL and public project sites, X posts/official accounts where publicly accessible, then credible third-party community reporting. Persist link, author identity, publication UTC, text synopsis, first-seen vs updated date, whether it names the exact CA, whether official affiliation is verified, and evidence classification. Promotional placement/boost must be distinguished from organic discussion. Sources blocked by access controls should be marked and a non-Chinese alternate source attempted; never fabricate unseen X posts.
8. **Audit & resilient caching**: raw evidence/response hash, normalized derivation, per-source retry/page cursor and freshness policy; requery older cached data only where meaningful, and do not rebrand old quotes as live. Public RPC limitations warrant alternate legitimate endpoints and batching, not indefinite waits or a superficial report silently returned as DONE.

No unapproved wallet action, monitor, scheduler, Gmail delivery, trade or paid data purchase.

## 5. $30 quote removal and module isolation

- **Remove `$30 实际可成交价`, `$30 可成交报价` and `execution_quote_30_usdc` from the generic manual CA analysis output and job execution path.** No expired snapshot in a headline. If price exists, show dated market reference and main-pool metrics. Contract transfer restrictions, tradability and pool depth may be displayed as independent risk evidence without a user-invented order amount.
- **Historical-vs-current authority correction (2026-10-22):** the old `follow_policy_v1.approved.json` and its $30 Jupiter quote existed in the prior runtime; that is **NOT a currently user-authorized default amount**. The user expressly rejected predefined trade size, and frozen G1 PR #114 supersedes that old assumption. This CA requirements change grants **no permission** to preserve $30 as a live new-decision default, to activate it, or to change the running V1/MC policy or delivery. Any separate removal/deactivation of obsolete live fixed-amount MC behavior requires a tightly scoped source/notification audit, independent review, and explicit user authorization; no unreviewed policy mutation here.
- If a future user explicitly asks a concrete trade size, a separate on-demand trade quote can use that size; it is not a default CA requirement.

## 6. Milestones and pass/fail gates (in this order)

**Release authority vs development increments:** Gates A–D below remain the **full product correctness/acceptance contract**, not an instruction to repeat every adversarial CA case, market scenario, external comparison, or browser screenshot for each bugfix. Section 8.3 is the **current bounded implementation ordering within this same contract**: diagnose one real failed job first, fix the proven critical path, add independent factual checks required for that path, and only then complete any remaining Gate A–D coverage relevant to declaring the *whole CA product* COMPLETE. Passing an 8.3 incremental milestone cannot waive an unpassed Gate A–D requirement or authorize production deployment. If required external sources or access are unavailable, record the concrete missing evidence and stop with PARTIAL/BLOCKED, rather than chasing every nonblocking P3 case or falsely claiming COMPLETE.

### Gate A: source/data semantics

- Token account vs owner, raw vs eligible holder Top10, pool/vault classification, precision, same-slot supply, and `0 no detected evidence` vs `proved none` test cases.
- Chain-verified synthetic and real historical cases with leading pool/vault holders forcing lookback past rank 20. Wrong Top10/ex-special metric must fail, not downgrade truth silently.
- Arbitrary owner with first acquisition/funding **older than 100/50 signatures**, including a swap-route intermediary, must be traced with honest pagination or flagged specifically `incomplete`.
- Reproduce both `GOMO` historical known wallet-split/public-infra examples and the **Agency** screenshot scenario with the exact mint from the original submitted CA input. Screenshots alone are visual evidence, not a verified ground-truth balance.

### Gate B: independent data parity and narrative

- Compare the **same CA, same time window, same definitions** against accessible GMGN/FOMO/OKX Wallet views, DexScreener and at least one independent pool/holder data method; save case IDs, timestamps, raw evidence and explain materially different numbers. Market cap/FDV/LP vs liquidity/Top10 definitions may differ legitimately; explain definitions instead of blindly forcing exact agreement.
- Three required distinct market situations: recent pump.fun graduation, mature active token and LP-heavy/vault-heavy token, plus at least one Token-2022 extension-risk case and one suspected multi-wallet-funded token.
- For every test CA, public narrative section includes **specific externally attributable posts/site evidence**, or a documented exhaustive accessible-source attempt. Narrative must never be dropped solely because official owner recognition is unproven.
- No public-site scraping bypass or paid GMGN API. If a source is not legally/technically accessible, use another allowed source and record coverage difference.

### Gate C: single-mode working UX

- Only **one query mode**; no quick/standard/deep control. Historical filters/caps are no longer exposed as accuracy choices.
- Progress UI may update immediately but must label output `FETCHING/PARTIAL`; `COMPLETE` requires all mandatory facts covered or a documented explicit `INCOMPLETE_EVIDENCE` outcome. HTTP 200/job DONE is not a product PASS.
- No overprominent red/green “safe” judgment unsupported by evidence; compact primary conclusion with drilldown evidence; no `$30` quote in CA.
- User can copy exact CA, inspect chain transaction signatures and source links, read timestamp and missing coverage without hunting through raw 500-transfer lists.

### Gate D: independent review and real Mac acceptance

- Submit real code diff + actual result JSON/HTML of sample CAs for **independent AI review** (e.g. Claude/Codex), including adversarial scenarios and source parity. Review must explicitly cover algorithms and data truth, not screenshots only. All substantial reviewer findings repaired and retested.
- Run unit/integration tests, representative full real CA queries, source-outage/fallback test and repeat-query cache invalidation; report elapsed time and unresolved data by **importance**, not just counts.
- Demonstrate on the user's actual Mac Dashboard that the new **one-mode** output materially resolves formerly unknown LP Top10, wallet first acquisition/funding, quoted-market definitions and external narrative where data exists. Validate no Frank writer/signals/delivery regression.
- **No merge/deploy/production change solely because CI passes.** Get explicit rollout authorization for any new Mac installation/restart; preserve snapshot/rollback path. `PRODUCTION_TRADING=NO_GO`.

## 7. Status and engineering handoff

**Current state: `REQUIREMENTS_RECORDED / CODE_NOT_CHANGED / TESTS_NOT_RUN_FOR_THIS_SPEC / NOT_DEPLOYED`.**

The module implementation conversation should first reconcile this requirement against actual head and propose an evidence-oriented design; then implement, independent review, test and request rollout approval. The 300-3000 general-governance conversation will review evidence, completion gates, provenance and priority, not pretend the engineering milestone has been executed. No new automation, Gmail, runtime task or Git PR was created by this requirements record.

---

## 8. 2026-10-22 CA 单模式方案修订与真实故障验收门槛（待 Claude 审核）

本节沿用第 1、3、6 节的**一个 CA 输入、一个分析按钮、内部渐进深入、统一完整性验收**，不另起查询模式。第 5 节现已直接修正 $30 权限用语，原始历史事实另在 Git 旧版保存，不赋予现时固定金额权限。Issue #165 在重述 10 月 13–14 日问题时提到“快速/标准/深度”，描述的是当时**已有三个界面档位的使用诉求/故障范围**，并非一条附有用户明确批准、可推翻第 1 节单模式产品决策的正式变更记录。最近用户明确要求“原来确定的原则不要变”，因此本次**暂沿用原 CA 单模式规范**；如 Claude 找到真实更晚的用户明确批准档位变更，应单列证据并暂停相关 UI 实现，由用户作架构/需求变更决定。无论界面档位，Issue #165 的只读失败原因定位都不受影响。

### 8.1 现状不能误报为完成

2026-10-22 用户实际 Mac（运行 PR157 产品 SHA 31dd598df248ca15f731913a5cbf82e88b981874）在一个 Mint 的 Deep 模式先看到基础行情/部分 token 权限/Top10 提示，随后出现“查询状态读取失败 / Failed to fetch”。基础信息出现在页面**不等于**资金链追踪完成，前端 fetch 报错也**不证明**免费 RPC 429。尚未读到这次失败的浏览器 Network、后端 job ID、worker 错误、实际报告保存证据，根因状态为 REGRESSION_OPEN、NOT_REPRODUCED_CAUSE。

当前 ClusterJobManager 的队列/结果状态主要在 Dashboard 进程内存保存，进程重启可能令轮询无法找到工作；历史已完成报告另存 control_root/cluster-reports/Mint/latest.json。不能把丢失的内存 job 当作“完整扫描失败”，也不能用已有历史报告冒充正在执行完成。报告只呈现经验证的部分数据和其原时点，不补填无来源的市场价。

### 8.2 维持原权威要求，恢复“可用而准确”的单入口

- 用户只提交一个明确 Mint 并点一次分析，页面返回一个稳定可查询 job ID；服务内部可经过 BASE、TOKEN_AUTHORITIES、HOLDERS、FUNDING、REPORT 阶段，只有完整性验收过关才称 COMPLETE
- 每个阶段结果附上源标识、采集/事件时间、Solana slot、返回覆盖/分页、独立核验状态；行情还需 Mint/chain/pair/quote 与报价时点，不能用历史参考价冒充现价
- 若浏览器轮询 GET 中断，保留原 job ID 和已验证部分，前端“继续读取”只恢复 GET，不自动再次 POST/发起昂贵扫描；页面状态显示“分析请求已提交，读取结果中断”而非泛化 Failed to fetch
- 若 server/worker 重启，需有可审计的最小持久元数据及报告引用，明确 JOB_INTERRUPTED、已有阶段保存情况和可续读范围；生产写入/新 schema 需要独立代码与用户明确授权，不能本设计直接启动
- RPC 403/429、超时、请求内容不全、owner账户/Top10 证据不足、结果持久化写入失败是不同错误；保留已完成阶段，同时把未完成部分标为 INCOMPLETE_EVIDENCE，**不得出现全量完成绿灯**
- 市场基础信息可用不代表精确排除 LP 后 Top10、控制关联、首次真正买入、Token-2022 扩展风险和 X 叙事已经核实；这些原第 3–4 节准确性要求绝不降低
- 真正查询必须以数据正确性与最终报告为目标；不得假设每个持有人只能属于一个控制者，不得用交易所公共资金源误连鲸鱼，未核实关系不输出具体风险概率

### 8.3 先调查再开发（Issue #165），每步给定业务验收

**唯一门禁映射**：第 6 节 Gate A–D = CA 整体产品最终验收；下表 A–E = 本轮开发动作的局部次序，**不是另外一套能绕过 Gate A–D 的产品验收**。本轮第一优先级只要求 A 的一份真实只读故障诊断；B/C 只针对已证实的根因；D 补回 Gate A/B 的数据完整性，E 走 Gate C/D 与冻结 G1 的 G3 独立审查。必须完成的 CA 完整性范围没有因为先修 Failed to fetch 而降低。未获允许的额外案例/外部来源在当前局部诊断阶段先标待验收，不进行无界补采。

**前置来源可行性门（仅设计和现有证据审计）**：先列出已经可用的 owner 全账户/双 Token Program 数据与 slot/供应商、分页完备性和免费额度；任何为证明完整余额或资金源而新增的实际 RPC/索引器调用，须先提交节点、预计请求数、上限、成本和失败停止条件，获独立用户批准后才准探测。未经验证的 RPC 可行性只能标 BLOCKED_BY_SOURCE，不能写已完成。

| 顺序 | 一次有界真实证据 | 授权与写入边界 | 结束条件 / 第 6 节映射 |
|---|---|---|---|
| A Mac 只读根因 | 已有失败 CA/job 的请求地址、HTTP 码/耗时、Dashboard/worker 状态及已存报告；不新发 CA 分析 POST | 已有本地信息只读，不增加 RPC 或修改生产状态 | 找到主要失败阶段或精确缺少的单一证据；Gate A 前置 |
| B 隔离复现 | 使用旧 Handler 与轮询在临时端口验证断线、job 丢失、worker/source/保存错误 | 仅私有临时 fixture；不连接生产 writer/DB/未批 RPC | GET 失败不等于链 RPC 失败且不自动重 POST；Gate C 故障部分 |
| C 最小根因修复 | 按可复现失败修复轮询与状态读回，优先重用现有报告缓存；设计持久 job 元数据 | 任何真实 control-root/SQLite 新写入、schema、定时任务或 Dashboard 重启另行审批；先隔离 dry-run | 同 CA 真浏览器得到有完整度区分的报告或明确 INCOMPLETE_EVIDENCE；Gate C 局部 |
| D 核心数据正确性 | 真实 CA 的 owner/LP、Token-2022、资金来源和市场叙事，按同一币种与来源口径复验 | 新 RPC 或外站数据读取的预算/请求上限先经用户批准；无授权不调用，记录来源 blocker | 满足第 6 节 Gate A/B 与未做的必要覆盖；不能靠单例宣布全产品 COMPLETE |
| E 独立审查与 Mac | 固定 SHA 独立 AI、CI 与 Mac 真实成功和断线恢复 | 新代码安装/运行、生产数据写入、任何投递修改须分别取得对应用户授权；不自动合并 | Gate C/D 与 G1 G3 通过后可请求单独部署许可；未通过则 NO_GO |

所有真实新 Solana RPC 读取必须另经用户批准调用预算、节点、最大次数、预期费用和超限停止条件；不得因此新增本机常驻扫描或影响旧 V1、MC Loop、邮件、数据库、钱包执行。部署权限与本设计审核权限独立。

本节状态：**DESIGN_REVIEW_ONLY / USER_REAL_FAILURE_OPEN / NO_NEW_RPC / NO_PRODUCTION_WRITES / NO_DEPLOY**。
