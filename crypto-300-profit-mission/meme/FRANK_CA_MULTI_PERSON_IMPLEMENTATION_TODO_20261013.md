# Frank / CA / 多人物钱包可扩展性 — 实施 TODO 与验收清单

- 日期：2026-10-13 Asia/Bangkok
- 状态：`DESIGN_ONLY / ALL_TASKS_NOT_STARTED_IN_THIS_PLAN / CURRENT_MAIN_UNCHANGED / RELEASE_NO_GO`
- 核查基线 main：`17a71c863b44c67f7a1a47639fd482958e56ee4b`（仅审计时，开工时重检）。
- 技术方案：`FRANK_CA_MULTI_PERSON_TECHNICAL_DESIGN_20261013.md`。
- 原始需求：`ca-analysis-unified-accuracy-acceptance.md`、`frank-wallet-monitor-dashboard-v2-design-2026-10-11.md`、`WALLET_CLUSTER_ANALYSIS_SPEC.md`、`MISSION_MEME_CURRENT_STATUS_2026-10-07.md`、`../MISSION_SPEC.md`。
- **本清单不是任务已完成证明。** 每条 `[ ]` 只有证据齐全才能转 `[x]`，记录实际实现 SHA、测试运行、独立审查、Mac 证据，不能以“PR 合并/CI PASS”替代真实业务验收。

## 2026-10-13 首次实际开发进度（不是发布验收）

- 实施分支：`dev/frank-ca-registry-a00-a02-20261013`
- [Draft PR #42](https://github.com/lxxlx2/ChatGPT_mission_record/pull/42)，固定提交 `37db294926565069f506e7d61c2bcd0a2c879954`；未合并、未部署。
- A00：基线与关联 PR 差异已**记录**，见 `meme/FRANK_CA_A00_CURRENT_MAIN_BASELINE_20261013.md`（在 PR #42 分支）；真实 Mac 当前指纹未在本轮读取。
- A01：12 项截图问题已转成回归输入清单，见 `meme/evidence/frank-ca-a01-screenshot-regression-fixtures-20261013.json`（在 PR #42 分支）；**F/C 的真正旧代码红灯、修复后绿灯测试仍未执行**，保持未完成。
- A02：研究侧 Registry v1 兼容/v2 预留代码及 13 项测试已提交；[CI #38391776145](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38391776145) **13 targeted + 1,440 complete PASS**。代码尚未独立 AI Review，也未接入任何生产服务，因此 A02 仍为 `CODE_READY_REVIEW_PENDING`，不能标最终 [x]。
- A03 及后续：`NOT_STARTED`。生产 Frank V1/Loop/Gmail/SQLite 和 Mac 均未改变。下一关独立 Review，之后继续 A03/A04 与 F01/C01，严格按本清单。
- 本分支仅更新 TODO 进度链接；实际代码在 PR #42 分支。**旧 main SHA 的测试不能作为未来新 main 发布依据。**

## 0. 启动前原则与依赖

四条并行但有依赖的工作线：
- `R`：真实数据、注册表、多人物多钱包事实层。
- `F`：Frank 跟单筛选、真实余额/PnL、观察/退出信息架构。
- `C`：通用 CA 单模式、身份、资金/持有人、叙事、市场。
- `S`：老通知和部署安全研究成果的当前 main 集成。

**当前 live 只有 Frank**。新增 person/wallet 默认 `RESEARCH_ONLY / signal=false / delivery=false / trade=false`；后续多人 `PERSON_PATTERN/TOKEN_CONSENSUS` 只是接口占位，未经新策略回测/授权不得生产启用。禁止无授权交易、签名、发信、重启、数据库迁移/写入和自动化；研发环境只能隔离/只读。

代码开发需要在每个阶段遵循 `数据调查→设计方案→技术方案→实现→另一 AI review→测试→隔离部署/实际核验→修复→Git 证据`，不要先部署再补回测或依赖论文式无真实数据的绿色断言。用户此轮**只批准设计及 Git 记录**，开发和 Mac release 要分开决策。

## 1. 里程碑 A：权威数据、审计基准和多钱包接口（阻塞 B/C/D 完整验收）

- [ ] **A00 — 冻结实际基线（P0）**：开工时拉取 main 完整 SHA、PR #28/#30/#31/#32/#33/#35/#37/#38/#39/#41 及研究分支；基于已合并源做路径+语义差异矩阵。读取最新 Mission/Frank 运行约束和 Mac 只读 release 来源、scanner/Loop/Dashboard hash，不以 10/11 状态记录覆盖 10/13 的 Git。产出来源对照 `baseline_manifest.json`（仅公开可披露散列）、明确基线/待修缺陷清单。**验收**：任何功能被标为已合并，必须有当前 main 具体路径/函数/commit 证据。
- [ ] **A01 — 冻结 12 条截图问题的红灯样本（P0，依赖 A00）**：固定 Frank NO_BUY+SELL+未知仓位用例、Agency exact mint、GOMO 已知钱包分仓/公共基础设施误关联、PR39 前后历史成本腿、CA 名称重复、过期 quote、前20 holder 未归因、叙事缺失。保存脱敏输入、交易签名/slot/时间、旧页面及预期事实。**验收**：旧 main 上核心回归必须真实失败，不能只 assert 字符串不存在。
- [ ] **A02 — 人物/多钱包 Registry v2 + 权限不扩大（P0，依赖 A00）**：升级既有 `config/frank_local_registry.json` 解析器而不是另建身份源；定义 person_id、wallet_id、chain、role、valid interval、source evidence、capability；支持一人两钱包、两人一币、不同时间钱包归属，旧 v1 注册无损读取，所有钱包通过注册表加载。**验收**：`FrankReader` 当前历史行为完全一致，禁止任意 API person_id 获得生产信号/发送权限；新增 person/wallet 默认 research-only；不更改冻结政策或已有身份键。
- [ ] **A03 — 拆除研究层硬编码 Frank（P0，依赖 A02）**：检查 `FrankReader`、`MissionControl`、`wallet_watch.PERSON`、`server.py`、各查询及 UI 的常量/隐式单人过滤；以 `PersonRegistry + WalletFactsProvider` 注入研究目标，Frank 实时旧入口保持显式 `person_id=frank`。**验收**：两个研究人物分别查询同 mint 返回独立数据；旧 Frank V1 算法和通知一致；移除对单地址的静默依赖。生产中选择额外人物不引发扫描/LaunchAgent/投递。
- [ ] **A04 — Sidecar 规范化原始事实账本（P0，依赖 A02/A03）**：`chain+wallet+signature+instruction/inner+leg` 主键，保存钱包签名、授权、ATA owner、余额 delta、Token2022、路由 legs、主动买卖 vs 被动转入/转出、失败交易、Slot/finality/raw hash、RPC cursor；不写 `forward.sqlite`。**验收**：相同 tx 跨两钱包只记一次链上事实，内部转账不算市场买卖；掉线/429 恢复后重放幂等且缺口可量化；成本不明不伪造 0。
- [ ] **A05 — 32-mint/ATA/真实钱包持续对账（P0，依赖 A04）**：以已归档 32 mints（历史 10 非零/22 零为旧 slot 样本，不是现在）、J7/BPxx 及被动-only 资产为回归，对所有实质性钱包 token account/owner/decimals/supply/last slot 查询并登记完整度；覆盖 Token 和 Token-2022。**验收**：model OPEN、CLOSED、chain snapshot、inventory status、last transfer 分离；若未扫描全部 ATA，结果只能 `PARTIAL`；不以余额归零推断 SELL。
- [ ] **A06 — Wallet→Person 持仓/资金成本/盈亏契约（P1，依赖 A04/A05）**：补齐多钱包内部划转去重、成本 lot、路由多资产收支、已实现/未实现、当前参考价及流动性；费用独立扣除。`PersonPortfolioAggregator` 只聚合核实归属的 Wallet。**验收**：同人两钱包、不同人同币、未知被动转入成本、部分退出、零余额转出、无价资产均有算例；不能算的 USD/PnL 为 null+原因而非 $0；与 GMGN 同窗口横向对比至少 5 个重要 mint 并标明口径差异。
- [ ] **A07 — 多人物只读 API 与隔离（P0，依赖 A02-A05）**：实现/试用 `/api/v2/people`、`.../{person_id}/positions/activity/watchlist/follow-opportunities` 的 versioned 契约，cursor/time/source/complete 元数据、allowlist、只读认证/权限；当前 Frank 旧 API 不破坏。**验收**：新增测试人物无通知/无决策、人物/钱包隔离、重名和错链拒绝、旧客户端兼容、页面可切人但未审核人物清晰标研究。
- [ ] **A08 — 数据来源/脱敏同步安全门（P1，依赖 A04）**：沿用已有 Frank 本地研究证据上传能力，设计局部导出授权、敏感数据脱敏、公共 Git allowlist、失败后重试哈希与版本；不得默认发布完整公开人物钱包轨迹、邮件 ID、个人真实地址。**验收**：public/private 目标错误、网络断线、冲突提交、重复上传、敏感字符串扫描均 fail closed，实际 Mac 授权单独进行。

## 2. 里程碑 B：Frank 当前机会与账本用户体验

- [ ] **F01 — 真实可跟的首屏列表（P0，依赖 A01/A03）**：只读派生 `BUY/SMALL_BUY + frozen decision current validity`，过滤 `NO_BUY/WAIT/SELL/EXIT/CLOSED/expired/updated contradictory`，将历史/不跟迁移展示到独立面板，数据库原记录、邮件不删除不重写。**验收**：截图中 “多次强加仓（本轮历史模型记录）+ 卖出 19 小时 + 不跟”不占据“当前跟单机会”；0 真正候选时显示 0；同一决策版本下底层邮件/信号字节与未修改 main 一致。
- [ ] **F02 — 当前真实仓位证明与模型状态并列（P0，依赖 A05/A07）**：当前/历史 token 数量、ATA、chain snapshot slot、时间、最新主动动作、验证差异和查询重试入口；不能核实时列出具体哪个账户/历史缺口，并给继续核对任务，不把“仓位不明”放首屏。**验收**：链上余额与模型 CLOSED 不一致时报警为差异，不自动卖出/买入；截图相关案例每一事实点有可点原始证据。
- [ ] **F03 — 完整活动/PnL/时间窗（P1，依赖 A04/A06）**：支持 24h、7d、30d、全部可用；主动买/卖、被动 token 转入、内部划转、未知路由分开；展示平均成本/已实现/未实现利润/持仓周期仅在有完整数据时；原 10/9 三笔交易重放。**验收**：不能将 24h 活动为 0 当历史总交易 0，历史与当前金额/美元价值有各自来源，重要 5+ mint 与公开 GMGN/FOMO 同窗口差异可解释。
- [ ] **F04 — 观察池状态持久化与 PR38 差异审查（P1，依赖 F01/F02）**：独立 `WATCH/HELD/EXITED/ARCHIVED/FOLLOW`，收藏/备注与变更历史可持续，数百研究对象默认折叠/可检索，退出物不挤占首屏。复核未合并 PR #38，不直接套用陈旧分支。**验收**：同一个 mint 即便信号为 NO_BUY 仍可在历史/观察检索；变更只有读取/UI 不改 V1 策略；各范围数量没有重复与错漏。
- [ ] **F05 — 历史买入/最新卖出文案与 PR37/39 回归（P1，依赖 F01/F02）**：对齐最新已合并 PR39 中 `latest_buy_amount_predicate`、历史复杂 quote 资金腿与新 Gmail 模板；评估未合并 PR37，禁止覆盖已校验的 immutable Gmail 或误触重发。**验收**：复合路由金额无确切证据不写全成本，SELL 优先于历史 MULTIPLE 出现在当前摘要，新决策 Gmail 仅在另行授权的受控发布后启用，旧 outbox hash 原样。

## 3. 里程碑 C：CA 单模式全面尽调（与 Frank 信号完全隔离）

- [ ] **C01 — One-mode CA job/进度/完成门槛（P0，依赖 A01）**：删除用户可见“快速/标准/深度”选择，默认渐进深扫并持久化 source cursors；`FETCHING/PARTIAL/INCOMPLETE_EVIDENCE/COMPLETE/ERROR` 与 HTTP DONE 分开。**验收**：重要事实未核验、RPC 429 或历史尚未到源头时不能亮“分析已更新/完成”；运行压力可控，进度分来源。
- [ ] **C02 — CA token 身份和名称正确（P0，依赖 C01）**：mint/program/metadata/name/symbol/market base-quote 核对，去重“Agency Agency”，同名代币不同 CA 不混淆。**验收**：可核实 exact mint→metadata→pair 关系；遇到 pair 异币/冲突字段时 fail closed 并标明证据，浏览器测试截图通过。
- [ ] **C03 — 合约权限/Token-2022/池与市场独立来源（P0，依赖 C02）**：核对 mint/freeze/update/transfer fee/hook/permanent delegate，交易池真实 base/quote、LP 状态、MC/FDV/流动性/24h 成交/价；同义指标与不同数据源对齐。**验收**：Token2022 风险样本、假池/多池、行情异常、不同流动性定义不会给无依据“安全”。
- [ ] **C04 — 真正前10大受益 owner 和 LP/特殊地址调整（P0，依赖 C03）**：不能用 Solana `getTokenLargestAccounts` 原 Top20 accounts 截断后过滤。引入合法可取得的完整 owner/Token account 枚举/索引 + 链上核对，动态识别 LP/vault/escrow/burn/router/CEX。**验收**：raw top10、excluding LP top10、excluding all special top10、cluster-adjusted、可确认自由流通份额有明确分母/有效 slot；LP 占前20的样本须读取更深名次；无法证实时不展示伪精确数。
- [ ] **C05 — Top20 owner 完整经济交易与 funder 追溯（P0，依赖 C04/A04）**：按重要性对 holder 完整分页，获取 first *acquisition*、first *market BUY*、被动收入、最早资金来源、SOL/USDC/WSOL 转账、复杂路由和每阶段签名；不能 100+50 截断后当全量。**验收**：超过 100/50 才出现的首买/funder 回归、历史 provider limit、未知/已故障 Token2022 都被准确记录，已查清者从未知转成带交易链接的事实。
- [ ] **C06 — 关系、分仓、控制组、公共基础设施排除（P0，依赖 C05）**：直接交易/资金关系、共同 funder、同步动作、Dev/treasury、归集与路由分层；GOMO 真分仓和 FOMO fee-payer 公共链路为逆向用例。**验收**：32.93% confirmed relationship 不被写成 32.93% common controller；0% 控制组标“未建立证据”而非“安全”；重大无法归因 13.6204% 必须继续查可得来源，停止原因具体可追溯。
- [ ] **C07 — 项目叙事/官方认领/热度来源置前（P0，依赖 C02）**：先讲“项目是什么”，然后 launchpad/官网/X 实际叙事、官方 exact-mint 认领、时间/发帖方、独立社区讨论和可能诈骗冒名；与行情和持有人风险并排展示而不是页尾一句“未接入”。使用可合法访问的公开数据；GMGN/FOMO/OKX 可作字段/使用体验对照，不要求付费。**验收**：三个不同 CA 样本均有可点来源或逐项完整合法来源检索失败记录，外部帖子不包含 exact mint 不当作官方背书。
- [ ] **C08 — 通用 CA 清理 $30 快照与陈旧报价（P0，依赖 C01/C03）**：从 CA 页和 CA job 移除 `execution_quote_30_usdc` 及两次自动请求；Market 参考价按真实时间展示。若用户**明确**填入成交金额才独立触发即时 Jupiter read-only quote，响应/显示都做 TTL 校验且支持重新取得；现有 Frank V1 $30 frozen quote 不修改。**验收**：无指定金额时 CA 绝不请求 $30 报价；请求时不会把已过期返回为可成交；Frank 价差/quote 单测原样通过。
- [ ] **C09 — 统一结果：重要数据可核实才显示“完整”（P0，依赖 C03-C08）**：项目/叙事与关键结论置顶；中间市场、链上 holder/聚类、前20交易；详细 raw evidence 折叠；不可获得数据集中列 `source attempted + exact blocker + materiality`，不向用户展示无意义的 30 个“未确认”卡片。**验收**：Agency 截图的 5–12 全部有复现+修复后真实浏览器证据，不能靠隐藏未知让看板显得准确。
- [ ] **C10 — CA 跨来源实测、缓存/429 与性能（P1，依赖 C09）**：近期 pump.fun 毕业币、成熟高成交币、LP-heavy、Token2022、疑似多钱包 Dev 至少五类；与公开 GMGN/FOMO/OKX 及另一可用合法链上/池源同 mint/同窗口比对，区分天然口径差异。报告请求时间、缓存命中、失败/中断恢复、查询结果更新时间和缺口变化。**验收**：数据源 429/403/timeout 时明确 PARTIAL/INCOMPLETE 并自动按规则切换或停机；不必付费 GMGN，不无限等待，不将截图当作实时链上结果。

## 4. 里程碑 D：通知正确性、发布安全和历史研究 PR

- [ ] **S01 — PR33 多轮安全研究成果与最新 main 三方审查（P0，依赖 A00）**：核实现有投递状态 SQL、`PENDING`、`PERMANENT_ERROR`、`RETRY_*`、`CREDENTIAL_BLOCKED`、`local/COMMAND_ACCEPTED`、跨渠道假成功、SQLite 锁、前后端缺字段、分类器异常/HTTP 断开；逐一对照 H-5/H-6/M-8–M-13 研究分支并确认是不是已由其他 merge 修好。**验收**：对当前 main 未修缺陷作旧绿/红复现和新代码绿验证，不重写历史邮件，不让本地命令成功等于 Gmail 发送。
- [ ] **S02 — 基于 main 的最小安全后续 PR（P0，依赖 S01）**：以新的 immutable main 产物修复真实缺陷（queued/blocked/channel whitelist/legacy contract/classifier exception 等）；设计迁移/回滚，明确涉及 Loop 或仅 Dashboard；复用经 Review 的研究测试，但不得直接 cherrypick 一整个过时研究树。**验收**：真的 SQLite、live HTTP、Node DOM、stale heartbeats、旧版混合与状态错配、无额外 Gmail 发送；current outbox rows 与 Message-ID/hash 原样。
- [ ] **S03 — PR39/41 恢复发布 + PR37/38/28 冲突账（P0，依赖 A00/S02）**：审查已合并 PR39/41 的发布授权与运行态来源；核对未合并旧 PR37/38/28，按现有 main 逐项选择“已覆盖/择取/作废重做”，不是强制合并；实际 Mac 如仍为 legacy/mixed runtime，保持专用受审的 fail-stopped controlled cutover 原则。**验收**：安全排程不会引用 mutable checkout，scanner 不被重启/重置，受保护 DB 备份及身份追踪可验证，旧 Loop 不可信时不自动重启。
- [ ] **S04 — 真实 Gmail 与运行恢复残留项（P1，依赖 S03）**：已记录待验证真实 SOL/WSOL 归一化、NO_ROUTE、sustained 429、重启/login/launchctl、Gmail Sent 最终回读/未发送不重试等项，独立于 UI/研究代码。**验收**：Mac 上只读实测、与当前精确版本绑定；需要 live Gmail 时再次另行明确批准，不能仅用数据表 SENT_VERIFIED 字段代替真正 Sent readback。

## 5. 里程碑 E：交付、独立 Review、真实机部署（逐关卡）

- [ ] **E01 — 数据合同及技术方案审查**（P0，依赖 A01–A03）：另一 AI 独立审多人物身份、链数据、历史兼容、资金归因和冻结 Frank 策略影响；审查报告需 exact SHA、相反样本及真实可行性。需要修复则先修再复审。**验收**：没有 Critical/High，或明确 BLOCK。
- [ ] **E02 — 各代码 PR 的独立 AI Review**（P0，依赖每个 PR）：每个研究/修复工作流均提交 API/SQL/前端/迁移的 diff、实际取证、对抗性案例，请其他 AI 独立 Review 并处理请求的变化；不用同一 AI 直接自我签字。**验收**：审查人和精确模型记录；审查的是最终代码而非旧 SHA；剩余主要风险列出。
- [ ] **E03 — 红绿 + 完整回归 + 合并树**（P0，依赖各相关 PR）：每个缺陷在旧 main 真失败、修复后绿；全 pytest、real Git、Solana 原始交易/lot、Node/JS/浏览器、SQLite 不变性、权限/429/断链/时效/ENOSPC/SIGTERM/SIGKILL/回滚。要测试同一人在多钱包、不同人在同一 mint 且各自关闭/重新进入；最后固定最新 main + 全部候选 PR 的合并树提交与三产品 blob。**验收**：CI 在准确固定 head 成功，不自动把较早分支 CI 说成最新。
- [ ] **E04 — 单独的 Mac 只读现状/计划验收**（P0，依赖 E02/E03）：冻结 Mac 前版本、scanner+Loop+Dashboard 源指纹、当前 wallet 档案、现有 outbox/email 身份、SQLite WAL/备份及页面事实；按真实 on-chain slot 对照 Agency、GOMO 和 Frank 新数据。**验收**：任何尚不明确的 runner/PID/保护文件均 BLOCK；真实 Mac 读数据不足先继续调查，不以台式 CI 替代。
- [ ] **E05 — 单独明确授权的受控发布**（P0，依赖 E04+用户另行批准）：只发布用户明确同意的范围；迁移前备份和 fail closed；部署/回滚中不得影响 scanner、交易、Gmail 旧状态或不相关钱包；发布后验证进程、HTTP/SQLite、浏览器、真实权限及最新链上数据一致。**验收**：失败有保留 journal 的安全恢复证据，完整应用后的身份/slot/数据契约真通过；没有授权时永久保持 `NOT_DEPLOYED`。
- [ ] **E06 — 前向效果和 GMGN 同口径验收**（P1，依赖 F03/C10/E05）：记录真实前向信号+延迟/净可成交性，分别报告 5m/15m/1h/6h/24h、费用/滑点、真实漏扫、重要钱包 PnL；至少一个持续观察窗口完整评估。**验收**：样本不足或失效则只能 `INSUFFICIENT_EVIDENCE`，不得称收益模型已证明有效或替换冻结 V1。
- [ ] **E07 — Git 当前状态、证据索引、治理归档**（P0，每阶段）：每个阶段提交 `design / decisions / evidence manifest / review / tests / Mac acceptance / release`，更新现有 `MISSION_MEME_CURRENT_STATUS_2026-10-07.md` 的当前指针（保留历史，不假冒已验证），再核对分支 PR SHA、内容 blob 与浏览器源文件。**验收**：能从 Git 重构任何“已完成/未完成”的真实依据，而非只看前一聊天结论。

## 6. 覆盖用户 12 条截图问题：明确责任归属

| 截图 # | 问题短名 | 主任务 | 端到端验收可观察结果 |
| --- | --- | --- | --- |
| 1 | NO_BUY 还在机会首屏 | F01 | 真实当前机会只含 actionable；不跟仍留历史 |
| 2 | 模型仓位不明 | A04/A05/F02 | owner/ATA/真实当前样本+slot 有据，缺失具体追查 |
| 3 | 仓位不明且无买入结论仍展示 | F01/F02 | NO_BUY 从机会退出，观察研究不误作推荐 |
| 4 | 大量不核实数据 | A05/C05/C09 | 关键数据深查，有统一覆盖率和缺口来源 |
| 5 | Agency Agency 名称重复/同名错币 | C02 | exact mint+metadata+pair 校验，去重身份 |
| 6 | 选 deep 仍集群未确认 | C01/C05/C06 | 单模式，重要归因充分扫描，不再假装上限等于完整 |
| 7 | 32.93%关系和13.6204%未归因 | C05/C06 | 区分关系与控制，重大未知继续追可得证据 |
| 8 | $30 报价莫名出现 | C08 | 默认通用 CA 不请求/显示 $30，Frank frozen 不变 |
| 9 | 报价过期 | C08/C10 | 明确金额时 on-demand+TTL，历史仅标快照 |
| 10 | LP/集中度大量未证实 | C04/C06 | 足额排名/owner/pool 验证，否则 INCOMPLETE |
| 11 | Top20 first buy/funding 未查 | C05 | 交易链/首次获取/首次市场买与资金源都有证据 |
| 12 | 缺叙事/叙事最后 | C07/C09 | 顶部讲清项目、来源、真实叙事和 exact-CA 官方关联 |

额外来源确认：
- 单独通知安全研究：S01–S04。
- 完整 Frank 账本/PnL/连续观察：A04–A06、F02–F04。
- 多人物钱包可扩展而不启用其他人物信号：A02/A03/A07 + E01–E03。

## 7. 技术验收数字与硬阻断项

**不预先填造测试通过率或预估完成时间。** 以下是发布验收门槛，而非声称当前通过：

- [ ] 重要 holder/source/full-acquisition/funder 有可审计 `source+signature/slot+coverage`；可知而未读取不能“完整”，超出 RPC 可达性可明确 `INCOMPLETE_EVIDENCE`。
- [ ] 同人双钱包/双人同 mint/同一 tx 双钱包/公共 CEX 误集群/20 accounts 不足 Top10/复杂多资产路由均有红绿真实链上固定样本。
- [ ] 旧冻结 Frank BUY/WAIT/NO_BUY、Source Writer、Gmail 历史身份及发信资格 hash/deterministic fixtures 无漂移。新人物 signal/delivery/trade 默认否，生产只有 Frank。
- [ ] 通用 CA 无默认 `execution_quote_30_usdc`，叙事有真实来源；页面“完成”状态与任务真完整度一致。市场报价与持仓余额按真实时间标记，过期不会显示为即时。
- [ ] 现在 main + 最终真实集成产品文件 pin + 非冲突已合并 PR 差异 + 另一 AI 受审最终 SHA 对齐。
- [ ] Mac 原生 Safari/Chrome UI 验收与真实链数据核对成功，数据库及通知原始身份保持不变，扫描器持续工作；部署/恢复必须有之后的明确授权。

## 8. 执行跟踪模板（每个 TODO 完工填写，缺失不得标 DONE）

`
Task ID:
State: NOT_STARTED | INVESTIGATING | DESIGN_REVIEW | IMPLEMENTING | EXTERNAL_REVIEW | TESTING | MAC_PREFLIGHT | RELEASED | BLOCKED
Main base SHA:
PR / branch / final code SHA:
Real evidence case id, source / slot / timestamp:
Test commands, exit codes, exact-head CI run:
Review AI/model, final verdict, final reviewed SHA:
Mac readonly acceptance (if required):
Authorization / deploy / rollback SHA (if required):
Remaining verified gaps / dependencies:
`

**下一执行入口**：A00 + A01 + A02 数据合同调研；建立红灯/链上取证基准后再做任何源代码修改。本轮仅写入设计与 TODO，不应创建生产定时任务、加多人物 alerts 或启动真实 Mac 部署。
