# Frank / CA / 多人物钱包可扩展性 — 实施 TODO 与验收清单

- 日期：2026-10-13 Asia/Bangkok
- 当前状态（2026-10-14）：`ACTIVE_RESEARCH_DEVELOPMENT / A04_VERSIONING_CODE_REVIEW_APPROVED / A05_AND_F02_BUSINESS_ACCEPTANCE_PENDING / NO_MERGE / NO_DEPLOY`。原始 2026-10-13 设计基线与各阶段历史记录仍保留；CI PASS 不代表勾选 41 项需求。
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

## 2026-10-13 A02 独立审查整改续报（保留待验收勾选）

- 原 PR #42 代码头 `37db2949`：Claude 审查结论 `BLOCK`，本地未推送的旧审查修复提交不能当作远端已提交。
- 重新核对原 PR 源码确认关键数据契约缺陷：base58 地址缺少 32-byte 解码、v2 没有明确起始 Slot、历史重归属共用同一个 `wallet_id`、schema 类型模糊、disabled 空钱包占位兼容。
- 2026-10-13 在**同一 Draft PR #42 开发分支**实际提交整改：`c7c54690`（产品），`38af418d`（旧夹具），`2c5c6ea2`（新增独立回归），`4d68fdb8`（CI 明确纳入新回归），`22f7b8f7`（原 checkpoint 审查与主线说明）。
- [GitHub Actions #38413246796](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38413246796) 在精确 `2c5c6ea29f30623a42b5bfa52dbedca4bb8a144d` 上实际通过原专项 13 项、完整 1,455 项。**这是中间提交的成功，不能宣称最终 PR 头通过**；以最终 HEAD 的 CI 为准。
- A02 当前为 `CODE_REMEDIATED / EXACT_HEAD_CI_PASS / INDEPENDENT_REREVIEW_REQUIRED`，**保持 [ ]**，没有合并、Mac 部署、Gmail、生产数据修改。最终 PR 代码和 checkpoint HEAD `22f7b8f760fea62f1f713d5aaccb9391cae1a26a` 对应 [Actions #38413672331](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38413672331)：28 项专项 PASS，完整 1,455 项 PASS，pyflakes/compileall/Node 均 PASS。
- R-1：现存 `signals/registry.py`、`meme/registry.py`、研究 `PersonRegistry` 的授权/验证语义仍必须隔离；新增测试只对齐当前注册表的钱包→人物标识，绝不能提升 ownership status。
- R-2：v2 现在允许显式登记绑定来源、研究批准状态和 funder/controller **证据引用**，但还没有 A05 的实际链上账户归属/受益控制证明。研究批准也不等于可聚合已核实资产。
- Claude 认为 CI `push` 触发错分支的结论与远端 `37db2949` 源文件不符，已按实际工作流更正。其他高优先级实质缺陷按原审查处理。

**主线优先次序保持不变：** A02 经他 AI 最终 SHA 复审后，进入 A03 研究读取接口、A04/A05 可核实 ATA/交易事实，然后 F01/F02 首屏过滤与真实仓位；C01/C02/C07/C08 通用 CA 核实/叙事/报价可在独立分支并行；S01 检查最新 main 安全缺陷。不能以 A02 测试绿灯替代 12 项截图业务修复。

## 2026-10-13 A03 + F01 实际开发续报（保持未完工审查门槛）

- **A03**：[Draft PR #43](https://github.com/lxxlx2/ChatGPT_mission_record/pull/43)，基于未合并 #42 的 `22f7b8f7` 分支建立独立堆叠 PR，HEAD `0010a7b8114bc87728bec3bb8eb9efdff9c1cbe9`。已实现 `PersonResearchReader + WalletFactsProvider` 注入契约和隔离测试，允许两个人查询同一 Mint、一人两钱包、Slot 区间研究，源缺失返回 null，不输出虚构 PnL。 [CI #38416486957](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38416486957)：51 项重点测试与 1,478 项完整测试 PASS。**A03 是接口阶段的部分开发，尚未完成 Sidecar 原始事实、真实 ATA 归属与生产硬编码系统解耦，不应标 [x]。**
- **F01**：[Draft PR #44](https://github.com/lxxlx2/ChatGPT_mission_record/pull/44)，基于当前已核查 main `449edcf1` 独立修复当前机会首屏；精确 HEAD `516e3335a134c608f477019b79027982f43af32a`。[原红灯 CI #38416881805](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38416881805) 真实报缺少 F01 实现；增加后端只读跟单筛选、`/api/follow-opportunities`、报价格时间戳、独立可折叠历史/不跟区域。旧 DOM 测试兼容问题保留真实失败记录并修复。[最终 HEAD CI #38418188923](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38418188923)：27 项重点测试和 1,454 项完整回归 PASS。**F01 仍待其他 AI Review、实际 Mac 只读页面验收及另行发布授权，因此 [ ] 不可改 DONE。**
- 这两条 PR 没有合并、不改 main、没有重启 Mac、不动冻结 Frank V1 决策/已发邮件/outbox/生产 SQLite/LaunchAgent/自动交易。现有 PR #42 的 A02 新 SHA 仍需他 AI 复审才能合并。
- 后续业务优先顺序：A03 现实数据读取器 → A04 原始链上事实侧账本 → A05 真实 ATA/余额核对 → F02 真实仓位 → A06 PnL；并行 C01/C02/C07/C08 通用 CA 实用修复。每一阶段围绕可用性、完整来源、真实 Mac 与链数据确认，禁止对单一边界反复扩展；各 PR 的测试通过只证明对应源码/fixture，不等于生产业务验收。

## 2026-10-13 A04/A05：真实数据源与离线账本进度

- [Draft PR #45](https://github.com/lxxlx2/ChatGPT_mission_record/pull/45)，基于尚未合并 A03 PR #43 堆叠继续开发。最终本轮测试 HEAD `92fbacbc411fb29a628c32d42bc5b6889603b7f6`。[GitHub Actions #38422305664](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38422305664) 在**该完整 SHA**：81 项专项、1,508 项完整 local-agent 回归及 compileall/pyflakes/Node PASS。属于代码门禁，**尚未经过另一 AI 独立 Review**。
- A04 已实现部分：可核实交易 token-balance delta、outer/inner SPL/Token-2022 parsed transfer、不同钱包同签名去重、被动 receipt 与未知市场成交分离、独立 immutable SQLite sidecar。未完成：实际交易完整指令/路由/funder/费用归因、source cursor/429 resume、本人完整历史链上的成本闭合。**保留 [ ]。**
- A05 已实现部分：正确官方 Token-2022 程序号 `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb`，并列 finalized Token/Token-2022 owner-account 枚举和双 Slot/non-atomic/partial coverage、raw ATA/mint/owner 校验、多 ATA 与人物注册表研究只读连通，手动 plan-only 脚本与只读单 Mint sidecar 输出。未完成：本地 Mac 全量真实账户采集、32 Mint 与 Token2022 的同源覆盖/未决缺口、F02 页面验收。**保留 [ ]。**
- 本轮实际读取 Frank 链上**两个 mint 过滤后的独立结果**：SPL `9N6ZV2DgCBeArFckZCBzyhwF2LdfMtEvYmLJ2EY9e4Rd` slot 456489219 raw 8140000/6，Token-2022 `HfAFNsnjmbWMMRkwNeUUoHJ8V6UnUGFzkpu3Seajpump` slot 456489222 raw 0/6。未达到全钱包 coverage，不可推定出售/PnL。此前 Token2022 RPC 错误确有错误程序号；这项已在代码修复、测试锁定。原始私有数据未提交 public Git。
- 原 #42、#43、#45 均 Draft，main/Mac/Gmail/forward.sqlite/launchd/Frank V1 policy 没有发生本轮变动，release 保持 NO_GO；待他 AI 审查、真实 Mac 验收与另行明确授权。
- 产品主线随后继续 F02 真仓位显示、A06 人物聚合和 C01/C08 通用 CA 清理；不能把 CI 通过当完整功能可用或将长期缺口记录为已完成。

## 2026-10-13 C01/C08：统一查询与无默认 $30 报价（独立 Draft PR）

- [Draft PR #46](https://github.com/lxxlx2/ChatGPT_mission_record/pull/46)，基于 main `4ac0b1612e8d238ab9189de066ea16a6f6e66455`，与 A02/A03/A04/A05 的堆叠 PR 独立。用户通用 CA 前端移除 quick/standard/deep 选择，只保留一个 CA 入口；后台仍通过已存在的 `standard` 预设兼容旧读取，当前数据深度**尚不能算 C01 完整验收**。
- 通用 CA 后端已删除 BASE_READY 和最终报告中的两次自动 Jupiter `$30` 报价，前端已删除对应卡片和报价时效计时器。新报告保留 DexScreener 来源行情与时间，旧历史报价只作为 `ARCHIVED_NOT_LIVE` 保存，不会重新宣称为即时交易价。**Frank V1 冻结的 $30 跟单报价、`MissionMemeService._quote`、Gmail、outbox、生产 Mac 均保持不变。**
- 原本 8 项关联测试假定用户必须选择扫描深度且无条件请求 $30；经真实 full-suite 红灯，已将**原测试**逐项迁移到当前需求，保留关键信息门禁、异常预览、历史报价不能复活、null 不当零、真实 Mac 验收脚本等保障。最终 [CI #38424959476](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38424959476) 在精确 PR #46 HEAD `e2fdb48e1e7d98a3f39d3153997b3b76f4d413ae` 成功：旧 main 用同一新测试得到预期断言红灯 `OLD_MAIN_EXPECTED_RED_PASS`；新 HEAD 5 项专项、1,432 项全量回归、语法及 lint 均 PASS。仅为代码验收，仍须另 AI 独立 Review，当前不得合并或部署。
- C08 的“用户明确填买入金额后单独临时报价”尚未实现，C01 的 Top20/首买/funding 全链深扫需 C05 继续；因而 **C01 与 C08 都暂保持 [ ]**，不可宣称已经通过端到端完整业务验收。合并/部署仍需他 AI Review、真实 Mac 验收与明确发布授权。

## 2026-10-14 A04 历史分页 / 断点恢复：实际执行进度

- 本任务由 ChatGPT 接手；Codex 并行负责 C02，不修改 C02/PR #46 代码与工作区。本轮新 [Draft PR #48](https://github.com/lxxlx2/ChatGPT_mission_record/pull/48) 堆叠于未合并 PR #45（后者依赖 #43 和 #42）；PR #48 精确 HEAD `26c40912c146dca3e85eb15d69570999dcc7e24f`。
- 新 `wallet_history_replay.py` 已实现 finalized `getSignaturesForAddress` 真实 `before` 分页、最多 1000 条/页、一页全部待处理签名和 cursor 同一 SQLite 事务落盘、`getTransaction(jsonParsed)` 原始事实+按钱包视角同一事务落盘、来源中断后先恢复 pending 再继续下一页、多钱包同签名全局原始交易只保存一份、来源变更证据不覆盖旧事实。
- 新手动研究 CLI `scripts/frank_research_history_readonly.py` 默认 `PLAN_ONLY`，不访问 RPC、不创建 Sidecar；只有显式 `--execute` 才经研究 allowlist + 批次上限请求 finalized RPC 并写独立研究 Sidecar。429/403/超时/null transaction 均形成可重试来源缺口，不将失败当零。
- [精确 HEAD CI #38499432278](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38499432278) **SUCCESS**，43 项重点及 1,525 项完整 local-agent（含真实 Git 回放）PASS；Python/Node 静态与语法检查 PASS。真实合约端只验证了 Frank 研究钱包两页各四笔 finalized signature、无重叠和其中一笔 `getTransaction` 的匹配 Slot/Signature，**不是**本地 Mac 全历史已入账。
- 证据和限制：`meme/FRANK_CA_A04_HISTORY_PAGINATION_RESUME_CHECKPOINT_20261014.md`，随 PR #48 保存。只确认来自 RPC 的可用历史分页尾部，不认定创世/全链完整；owner 主地址以外的 ATA 历史、首次 market BUY / funding 路由、完整成本/PnL、重新扫描新 HEAD 均未完成。继续保留 **A04 [ ]**，不标记 DONE。另 AI 审查、Mac 本地真实 Sidecar/32 Mint 验收和发布授权均未完成。
- 无主 main 合并、Mac 部署、LaunchAgent 重启、冻结 Frank V1 策略/投递/Gmail/生产 SQLite 的任何改动。产品主线下一步是 A04 verified ATA 地址范围历史、A05/ F02 精准仓位和独立 Review，不为边界处理长期停滞。

## 2026-10-14 阶段性 Review 与跨 PR 集成闸门（不可跳过）

- 原始审查矩阵、业务文件重叠、各自 SHA 与下一步顺序：[`FRANK_CA_PR_REVIEW_INTEGRATION_GATE_20261014.md`](./FRANK_CA_PR_REVIEW_INTEGRATION_GATE_20261014.md)，该文件是**新增开发与集成的入口**，直到整套 PR 完成联合 CI/另一 AI Review/Mac 只读验收。代码 CI、源数据验证和 Mac 生产上线三个状态必须分开。
- [PR #47 C02](https://github.com/lxxlx2/ChatGPT_mission_record/pull/47) 在 `c4073f69` code CI 1,445 PASS；Gemini 报告 model **`gemini-3.5-flash`**、审查产品 SHA **`3ed4755e`**，到 HEAD 只更新了文档与证据（GitHub 已 compare）。Claude 独立复查发现 R-a 预览无 exact Mint、R-b capitalization 假冲突，需要处理，而不是直接标无条件 APPROVE。
- R-a/R-b 在 **[Draft PR #49](https://github.com/lxxlx2/ChatGPT_mission_record/pull/49)** 作为 #47 的子分支修复，绝不修改已审查的 #47 HEAD。精确 Mint 同时在扫描进度和预览显示；链上来源及市场来源的大小写冲突比较规则和展示规则一致；实质性冲突仍阻断。精确 HEAD `9c16829e3d699741af23a9c02aee0816b3a64f2d` 的 [CI #38501128406](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38501128406) **SUCCESS：17 项重点、1,449 项完整 real-Git PASS**，6 真实保存案例的 Node 实际 `app.js` 渲染、编译/pyflakes/JS 语法 PASS。**需重新独立 Review #49 最终代码 SHA，不能以 CI 代替 Review。**
- [PR #48 A04](https://github.com/lxxlx2/ChatGPT_mission_record/pull/48) 43 项专项、1,525 项完整测试 PASS；独立 Review 仍未完成，应重点验证断点、429、raw tx/按钱包视图去重与交易入库事务。PR #42/#43/#45 整条上游数据分支也需覆盖；[#44 F01](https://github.com/lxxlx2/ChatGPT_mission_record/pull/44) 需要与 C01/C02 的同一 `server.py`/`static/app.js` 整合回归。
- 实际 GitHub REST 在 2026-10-14 复查 `#42/#44 mergeable=true,mergeable_state=clean`，此前连接器摘要的 `false` 不能当实际冲突。**合并可行性≠整合后的产品和数据正确性。**
- 合并前顺序：先收敛每条分支已有 Claude 问题 → 本分支精准审查门禁 → 创建一次性整合集成分支（#42→#43→#45→#48 + #46→#47→#49 + #44）→ 联合完整测试和浏览器/链证据 → 用户明确授权的 Mac 受控发布。未经过该门禁，保持 `DRAFT / NO_MERGE / NO_DEPLOY`。
- C02 文档中的“20 个分片”仅在归档投影中保存 provenance/计数，分片原文**未随 C02 PR 一并提供**；第三个 Agency 同名 Mint `H4UH4ypR3nTqDHJPJurYL2GsDWzotKzzU1Kmj3XiqFkj` 已归档；两种截图相似 Mint 都是可解码公钥，不得猜名字自动纠正；Codex 浏览器数据回放≠生产 Mac 用户查询。

## 2026-10-14 Claude 第二轮 REQUEST_CHANGES 实际整改与新审查门禁

- 用户提供的完整 Claude 对抗性报告，在旧 HEAD 上给出 **PR #49 `9c16829e` REQUEST_CHANGES（Medium Unicode 误判）**、**PR #48 `26c40912` 及 #45 `92fbacbc` REQUEST_CHANGES（High 单侧 owner 缺失制造假流出/流入）**。原先各自 CI 绿色不代表无 bug。保留报告与风险顺序。
- **C02 原 #47 不动；原整改 PR #49** 继续修复 casefold 的 `Straße / STRASSE` 静默合并，换成非 Unicode 扩张 `lower()`，既允许 `Agency / AGENCY`，也阻断真实名称差异；新增 metadata authority 不同仍冲突用例；`ClusterJobManager.validate_mint` 改为校验 base58 解码精确 32 字节，不再只凭字符长度。最新 PR #49 HEAD `8898134a8a302e1187138f7fb3da87a554567e6d`，对应 [CI #38503360215](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38503360215) **20 专项、1,452 全量 PASS**；须 Claude **重新**独立审查该 SHA，不能沿用旧请求更改结论。
- **A04 另建子 Draft [PR #50](https://github.com/lxxlx2/ChatGPT_mission_record/pull/50)** 继承 #48，**不覆写** #45/#48 原始已检验 HEAD。先保留 pre/post 所有 token 账户 owner/raw 记录再配对；单侧缺失且数量未变记录缺口而非假收支，单侧缺失且数量变化时阻断归因并将签名留待补采；双侧 owner 缺失显式 gap；原生 SOL 转入转出在当前模型中标为 `NATIVE_SOL_FLOW_UNCLASSIFIED` 而非 0；误导的 `NOT_MARKET_TRADE` 标签改为 `UNVERIFIED_TOKEN_DELTA`；Solana SPL/Token-2022 解析指令证据现接入 A04 采集视图，但不自动推断 BUY/SELL。给派生视图加 `SOL_TOKEN_VIEW_V2`/research_wallet，单独归档 `WALLET_TX_VIEW_V2`、支持从不可变 RAW_TX 显式重建，旧视图不覆盖。
- PR #50 HEAD `4cef47ac63d1a0a2beb9ec7924214a127c97e32f` 对应 [CI #38503749827](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38503749827) **52 专项、1,534 全量 PASS**。Claude E1a/E1b/E1c 与版本化回放覆盖，但**仍需另一 AI 复审 #50 最终 SHA**，后续真实 Mac owner 缺失频率、ALTs、ATA 历史、人物 PnL、完整 SOL 资金流尚未验证。不要将 A04、A05、F02 状态直接标完成。
- 两条整改线均保持 **DRAFT / NO_MERGE / NO_DEPLOY**。下一次任何共用代码更改后，先对 #49、#50 独立审核，随后合并到**临时整合工作区**做 F01 #44 + C01/C02 #46/#47/#49 + A04 #42/#43/#45/#48/#50 的完整回归，不得丢 F01 屏显或 Frank V1 原跟单约束。
- 本轮 GitHub 评论与长期审查闸门：`FRANK_CA_PR_REVIEW_INTEGRATION_GATE_20261014.md`，所有 PR/CI 明确关联精确 SHA。Mac/生产未部署，用户不需要重复跑本可在 CI 自验的命令。

## 2026-10-14 多 PR 联合临时 CI 真实结果

- 本轮新增只在 Actions 容器进行的**临时合并演练**：[Workflow #38504090624](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38504090624)，完整 `success`，分别融合继承 #42→#43→#45→#48→#50 的 A04 分支、继承 #46→#47→#49 的 CA/C02 分支和 F01 #44；全部 Git merge PASS、联合专项 **48 PASS**、全量 real-Git local-agent **1,586 PASS**，无远端 PR/main 合并或部署。与过去的单独 PR 绿灯不同，现已验证这些版本可在同一份源码里运行既有测试。
- 该证据只覆盖暂存 Git 工作区和 Node/pytest，不是本机 Mac 页面实际点击或完整链上历史。仍需 Claude 对修改后的 PR #49 `8898134a`、PR #50 `4cef47ac` **再次独立 Review**，最后才是完整真实 Mac 只读预检与单独生产授权。F01/CA/A04 开发 TODO 不直接标 [x]，no-go 保持。

## 2026-10-14 Claude 第三轮精确 SHA 独立审查 / A04 P2 P4 P6 修复

- 用户提供的完整 Claude 精确 SHA 审查：**PR #49 `8898134a8a302e1187138f7fb3da87a554567e6d` 得到 `APPROVE`**，重跑 1,452 全量/27 项包含 F01 布局专项，实际 `app.js` 同 VM 联合渲染无串号。Low：土耳其语 `İstanbul` 保守冲突、F01 使用缩写 Mint；不阻断但仍不是生产 Mac 验收。**PR #49 代码保持不变。**
- **PR #50 `4cef47ac63d1a0a2beb9ec7924214a127c97e32f` 的新审查为 `REQUEST_CHANGES`**（旧修复不能自动视为通过）。High P2 非零 owner 缺失且两边都不属于已知跟踪钱包时漏记、P6 历史 V2 重建阻断未持久化且旧 v1 仍可能污染、P4 失败交易解析转账被写成已确认；Medium P5 原生 SOL 未观测没进入 `state()`、P7 新 v2 同旧 kind 混放。
- 新子 **[Draft PR #51](https://github.com/lxxlx2/ChatGPT_mission_record/pull/51)** 在 #50 之上修复 P2/P4/P5/P6/P7：未知归属非零 token delta 一律不允许完成采集、留 `PENDING` 并记录 `TOKEN_OWNER_UNRESOLVED_DELTA`；旧 `CAPTURED` 的 v2 重建出错持久写入 `v2_error_code`，`state()` 必须显示 `v2_missing_count` / `v2_blocked_count` / `PARTIAL_ECONOMIC_EVIDENCE`；`meta.err != null` 解析指令标 `FAILED_TRANSACTION_INSTRUCTION_NOT_EXECUTED`，不再确认为转账；原生 SOL 未解析增加独立覆盖计数；新 view **只保存为 `WALLET_TX_VIEW_V2`**、原 v1 不覆盖。对抗性 P2/P4/P5/P6/P7 真 SQLite 测试和完整回归已补。**PR #51 精确 HEAD `c2cf581196d19e61306148cdfb85ce4857d8f02f`** 的 [CI #38543947263](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38543947263) **57 项专项 + 1,539 项全量 PASS**；[临时联合 CI #38543947345](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38543947345) 将当前 main 与 A04 #51、C02 #49、F01 #44 依序合并，**53 项联合专项 + 1,591 项全量 PASS**。但这仅是代码验证，不是新 SHA 的 Claude Review 或 Mac 验收。
- 真链调查：Alchemy finalized RPC 实际采到 Frank 研究钱包连续 25 条签名，含 slot `456780885` 的失败交易状态，实际完整 `getTransaction` 被插件返回截断；另两笔成功交易 slot `456789461` / `456789273` 的 RPC 完整读取，均未出现 owner 字段缺失。**真实 owner 缺失及失败指令完整原始交易 fixture 仍是未确认缺口，不得以合成测试替代。**
- PR #51 在未合并 #50 上单独推进，**要求 Claude 对最终新 SHA 重新独立 Review**，同时独立检查与 F01 #44、C01/C02 #46/#49 的最新合并树，不得重写已通过审查的 #49。各 PR 保持 Draft、Mac/生产/Gmail/SQLite/launchd 均未变，业务任务 A04/F02 不标 [x]。

## 2026-10-14 Claude 第四轮 REQUEST_CHANGES：PR #52 N1 / 原生 SOL / 真实 ATA 采样

- Claude 在精确旧 HEAD `c2cf581196d19e61306148cdfb85ce4857d8f02f` **再次对 PR #51 给出 `REQUEST_CHANGES`**，同时通过对比确认 P2/P4/P6 High 修复成立，P7 V1/V2 分离与旧表迁移手工试验成立。新增 Medium：纯 Token 手续费交易一律标原生 SOL 不明、无关 owner 缺失使历史永久阻断；旧 SQLite `ALTER TABLE` 缺自动回归，真实失败交易/owner 缺失链上样本不足。**保留 #51 已审查 SHA，不覆写。**
- 新子 [Draft PR #52](https://github.com/lxxlx2/ChatGPT_mission_record/pull/52) 从 #51 创建：真实 `preBalances/postBalances` + 手续费 + 仅与 tracked 钱包有关的 System 指令来区分 `NO_NATIVE_SOL_FLOW_OBSERVED` / `NATIVE_SOL_FLOW_UNCLASSIFIED` / `NATIVE_SOL_BALANCE_EVIDENCE_MISSING`；`state()` 分别计数，纯 Token 只付手续费不会错误标不可用。
- **N1 采用研究侧显式运维方案**：默认仍然严控归属未知的非零 token delta 并保持 `PENDING`；只有用户明确调用 `--execute --continue-on-owner-gaps`，才允许将真实 `RAW_TX` 不可变入库，`WALLET_TX_VIEW_V2` 继续缺失，`v2_error_code` 持久表明 `TOKEN_OWNER_UNRESOLVED_DELTA`，覆盖必为 `PARTIAL_ECONOMIC_EVIDENCE`，同时可继续查更旧签名。绝不把该笔记作市场买卖、可用仓位、成本或 PnL。
- **真实链上数据进展**：已从 Alchemy finalized `getTransaction(jsonParsed)` **完整提取** Slot `456789461` 的 Frank Token-2022 ATA 创建响应，保存在 #52 的 `local-agent/tests/fixtures/solana_finalized_ata_creation_slot456789461.json` 并加入回归。实际付款人是另一 signer，Frank Wallet 的 lamports 未动；内层 System createAccount 并不意味着 Frank 的 SOL 流出。该证据不是失败交易，也不是缺失 owner 的真实样例。Slot `456780885` 真实失败签名已观察，完整响应受接口截断，owner 缺失发生频率未核实，维持 **UNVERIFIED** / Mac 验收未完成。
- 已新增正常手续费纯 Token 反例、真正非手续费 SOL 流动、显式 N1 历史分页恢复、真实旧 Sidecar `ALTER TABLE` 升级及旧 RAW/v1 保留、真实 ATA fixture 解析的自动化回归。代码证据与报告见 PR #52 `FRANK_CA_A04_CLAUDE_N1_SOL_AND_REAL_ATA_20261014.md`。
- PR #49 的 `8898134a` 已获独立 Claude `APPROVE` 且**没有改动**。PR #52 最终代码 HEAD `e547203c6e4b00c80372c125785c9feb72fb8e87` 的 [独立 CI #38549340254](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38549340254) **64 重点 + 1,546 完整 PASS**；[F01/C02/A04 临时联合 CI #38549339806](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38549339806) **三分支合并无冲突、51 重点 + 1,598 完整 PASS**。**此为代码验收，仍需另一 AI 对 #52 精确 SHA 重新 Review / 实际 Mac 验收**。Mac / 生产 DB / Gmail / launchd / 冻结策略未动，所有 PR 保持 Draft / NO_MERGE / NO_DEPLOY；F02/A04 业务验收不标 [x]。

## 2026-10-14 Claude 第五轮审查：旧 V2 身份碰撞及 #53 可复现升级

- 独立 Claude 审查 [Draft #52](https://github.com/lxxlx2/ChatGPT_mission_record/pull/52) 的固定 SHA `e547203c6e4b00c80372c125785c9feb72fb8e87` 返回 **REQUEST_CHANGES（P2）**：原生 SOL 经济归因算法已改变字段与分类，却复用了历史 V2 `SOL_TOKEN_VIEW_V2 / WALLET_TX_VIEW_V2 / :v2` 不可变身份。旧 V2 Sidecar 重建因此出现 `DERIVED_V2_EVIDENCE_CONFLICT`，原视图无法升级。SOL fee-only、N1 手动缺口归档、真 ATA 出资人和 Frank 归属逻辑复审 PASS，但**#52 仍不得合并/部署**。
- 新独立子 [Draft **PR #53**](https://github.com/lxxlx2/ChatGPT_mission_record/pull/53) 从 #52 SHA 建立，精确最终代码 HEAD **`166bdaa133d7ed799870ca963d2dfa55f2736b17`**：当前派生视图采用 `SOL_TOKEN_VIEW_V3`、schema 3、`WALLET_TX_VIEW_V3`、`:v3` 及 `v3_error_code`。覆盖逻辑只以 V3 为准，并另报旧 V2 计数及历史 V2 错误；RAW_TX / 旧 V1 / 旧 V2 的 payload、hash 和 cursor 不修改。显式重建 V3：首次新增、二次 `already_present`，不向历史身份写入新内容。
- **跨 SHA 实测**：新 CI 分别检出旧 PR #51 `c2cf5811` 和旧 PR #52 `e547203c` 的**原始代码**（对运行时导入的 Python 文件路径作核验），分别生成真实旧版 Sidecar V2 SQLite 文件，再用 #53 新版本打开、迁移、重建两次，原始 RAW/V2 哈希和逐字节 payload / 游标完全保留，V3 覆盖与 SOL fee-only 得到正确结果。不是仅在新代码内伪造 V2。验收可复现的工作流 [#38555422999](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38555422999) **SUCCESS：65 项重点、1,547 项完整 real-Git**。所有链上原始样本仍以真实/合成分别标记。
- **实际联合 CI** [#38555423226](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38555423226) **SUCCESS：47 项跨模块重点、1,599 项完整测试**，一次性工作区将当时 main + A04 #53 链 + Claude 已批准的 C02 #49 链 + F01 #44 合并测试，无冲突，不改变 main/真实 Mac 环境。
- **下一闸门必须是另一 AI 对 #53 最终 HEAD 的独立代码审查**；不要复用已经拒绝 #52 的结论或把 CI 绿灯视为代码批准。之后继续真实 Frank 钱包 32 Mint/ATA/历史资金和本地 Dashboard 业务验收。失败交易完整 parsed receipt、真实 owner 缺失和 ATA-close 原始证据仍未核实；**NO_MERGE / NO_DEPLOY**。

## 2026-10-14 Claude 第六轮 REQUEST_CHANGES：通用 TX 身份冲突，PR #54 修复

- **PR #53 `166bdaa133d7ed799870ca963d2dfa55f2736b17` 第六轮独立 Claude 结论是 `REQUEST_CHANGES`（1 P2）**。HistoryJournal 的 V2/V3 原始数据保留、真实 PR51/PR52 跨 SHA 升级、重复重建、V3 覆盖已复核通过，但通用 `WalletEvidenceStore.record_transaction()` 仍把 V2/V3 都写入未分版本的 kind `TX`、identity=`solana:<signature>:<slot>`。旧 PR52 V2 文档与新 V3 在同一身份上发生 `IMMUTABLE_EVIDENCE_CONFLICT`；**禁止将 #53 标记 APPROVE 或直接合并**。
- 子 [Draft **PR #54**](https://github.com/lxxlx2/ChatGPT_mission_record/pull/54)，基于 **未更改**的 #53 HEAD，最终 SHA **`6e1f8cec197bab30703fb4524c9710191dc25522`**。旧 `SOL_TOKEN_VIEW_V2` schema 2 的 `TX` 仍保持 unversioned `solana:<signature>:<slot>`；新 `SOL_TOKEN_VIEW_V3` schema 3 的 `TX` 独立保存 `solana:<signature>:<slot>:v3`，同版本相同内容幂等、同版本不同 SHA 直接拒绝，未知/不匹配版本拒绝，不覆写历史证据。
- **跨版本真实源码复现**：精确 [CI #38560775862](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38560775862) 通过（65 专项、**1,555 全量**），其中 CI 从真实旧 PR52 `e547203c` 的工作树调用**其原始** normalizer 和 `WalletEvidenceStore.record_transaction()` 写入 SQLite 的旧未分版本 `TX`，再用新代码插入同签名同 Slot V3，新旧证据哈希与 payload 均保持原样，V3 重复导入不增加记录，篡改同版本被拦截。
- [临时联合 CI #38560775878](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38560775878) **SUCCESS：55 项重点 + 1,607 项完整**，从 CI 运行时最新 main 合入 A04 #54 完整子分支、Claude 已通过 C02 #49 代码和 F01 #44 代码，三个 Git 合并步骤无冲突。具体业务功能/真实 Mac 未在该 runner 部署。
- 当前**仍需独立 Claude 对 #54 最终 SHA 复审**，然后再推进 A05/F02 的 32 Mint/ATA 真实历史数据及 Dashboard 本地验收。没有新增已确认真实 owner 缺失、失败指令完整 getTransaction 和 ATA-close 档案；继续明确缺口，研究未完成不算生产资产/PnL。所有 PR Draft，**NO_MERGE / NO_DEPLOY**，未改 Frank V1 / Gmail / Mac 生产 SQLite / launchd。

## 2026-10-14 Claude 精确代码审查 PR #54：APPROVE，解除 A04 版本冲突代码门禁

- 用户提交独立 Claude 对 [Draft PR #54](https://github.com/lxxlx2/ChatGPT_mission_record/pull/54) **精确 HEAD `6e1f8cec197bab30703fb4524c9710191dc25522` 的 `APPROVE`**，严格限于相对父 SHA `166bdaa133d7ed799870ca963d2dfa55f2736b17` 的代码变更，无新增 P2/High。与独立审查报告的完整测试、旧 PR #52 真 SQLite 迁移、新旧 TX 文档逐字节保持、反向插入、只读连接和冲突守卫全部一致。**这是用户转交的外部 Claude 报告，不是假冒 GitHub 原生 APPROVE**（实际 GitHub Review 列表为空）。
- 最终通用 `WalletEvidenceStore.record_transaction()` 身份门禁：历史 `SOL_TOKEN_VIEW_V2`/schema2 仍用 `TX/solana:<signature>:<slot>`，V3/schema3 用 `TX/solana:<signature>:<slot>:v3`；严格 `type(schema_version) is int` 配对；同版本重复幂等、有效冲突不得覆盖。HistoryJournal `WALLET_TX_VIEW_V3` 与泛用 `TX` 的版本路径独立。PR #53 曾获 `REQUEST_CHANGES` 的通用 TX P2 在 #54 的精确代码审查中**正式关闭**，不再对该补丁继续循环修补。
- 复核真实 GitHub：PR #54 仍 `open/draft/unmerged`，HEAD 未变；[Actions #38560775862](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38560775862) **SUCCESS 65 专项 + 1,555 全量**， [Actions #38560775878](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38560775878) **SUCCESS 55 联合专项 + 1,607 全量**，两次触发 SHA 完全一致；main 当前查询时为 `1071d232278ceecbe28c28e1a809989bf5e87726`，该 main SHA 仅作为此轮快照，集成和发布前必须再查。
- **状态严格分离**：`A04_VERSIONING_CODE_REVIEW_APPROVED / CROSS_SHA_CI_PASS / COMBINED_CI_PASS`；`A04_CHAIN_SOURCE_COVERAGE_PARTIAL / A05_FULL_ATA_NOT_DONE / F02_ACTUAL_POSITION_NOT_DONE / MAC_ACCEPTANCE_PENDING / NO_MERGE / NO_DEPLOY`。原 41 项产品 TODO **不能仅凭代码审查通过而全部打勾**。
- **后续主线恢复**：A05 真实 SPL+Token-2022 owner token-account 全量枚举，核对多 ATA/32 Mint/slot 新鲜度及尚未取得的历史账户证据；连接 F02 展示有证据的最新实际仓位，缺失 `null`，不将余额 0 当清仓或成本已知；后续 A06 和 CA C03–C07 再推进真实成本、资金流和叙事。第一阶段应采用独立手动采集及隔离证据与另一 AI Review，**不请求合并或部署生产 Mac**。
- 未满足的外部证据不隐瞒：失败交易完整 `getTransaction` parsed receipt、真实 owner missing nonzero、ATA-close fixture、32 Mint 和真实浏览器闭环。代码批准没有关闭这些数据和业务门禁。

## 2026-10-14 新增 A05→F02 最新快照只读研究模块（Draft #56 / 新模块独立 Review 待执行）

- [正式开发规范 Draft PR #55](https://github.com/lxxlx2/ChatGPT_mission_record/pull/55)：`docs/DEVELOPMENT_REVIEW_POLICY.md` + `MISSION_SPEC.md` + 根 README。确立**单模块完成即另一 AI 精确 SHA Review → 跨模块组合另行 Review → 全部模块完成后再做一次总体完整独立 Review → Mac 真实业务验收 + 用户另行部署授权**；Review 结果需记录实际代码 SHA、base、测试、风险、来源与影响范围。审查规范本身仍是 Draft，不代表已合并 main。
- [A05/F02 新子 Draft PR #56](https://github.com/lxxlx2/ChatGPT_mission_record/pull/56)，从已获外部 Claude 代码批准的 A04 #54 HEAD `6e1f8cec` 堆叠；新增 `wallet_inventory_snapshot.py`、只读 `scripts/frank_research_latest_inventory.py` 与独立回归。目标是**永不拿历史旧正余额当当前仓位**：先选最新 finalized 研究账户快照，再查询精确目标 Mint；新双程序快照无账户只报 `ABSENT_IN_LATEST_DUAL_PROGRAM_SCAN`，不伪造卖出/余额 0；新快照部分来源失败则报 `UNKNOWN_MISSING_PROGRAM`，不可借旧快照补齐；过期则掩盖数值。记录 capture_sha256、UTC 时间、slot 范围、非原子程序查询、多 Token Account 原始量、目标 Mint 数、无价格/PnL；拒绝重复/非法 Mint 和篡改源 SHA。
- CLI 只读现有**隔离 Sidecar**与用户提供的准确 Mint JSON 数组，不能 RPC、不能创建伪零数据库、不能启动 Scheduler、不能读取生产 SQLite 写入。测试覆盖最新缺失/部分/多 ATA/过期/32 Mint/旧快照错误回退/手动 CLI 只读。**该工作只是 A05→F02 的研究桥接，不是实际全 32 Mint 采集，也没有向生产 Dashboard 接入实际仓位**。
- **PR #56 精确代码 HEAD `55b430608d9048360f922a453f77cced479ac810`**：[模块 CI #38565541835](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38565541835) **41 项重点 + 1,569 项全量 PASS**；[临时联合 CI #38565541852](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38565541852) **66 项联合重点 + 1,621 项全量 PASS**，合并本轮 main + A04/A05 代码 + C02 #49 + F01 #44 无冲突。已在 #56 PR 留独立 Review 清单。**仍须另一 AI 对这个最终 SHA 给出 APPROVE/REQUEST_CHANGES**，目前 `A05_RESEARCH_INVENTORY_REVIEW_PENDING`，A05/F02 原始业务 TODO 不勾完成。F01 #44、上游 A02/#42 A03/#43、A05/#45/C01/#46 不得因为 A04 #54 或 C02 #49 的审查通过而概括成全部已审查。
- 真实验收下一步仍需用户 Mac 上实际可核实的 **32 Mint 名单与同时段（非原子）SPL + Token-2022 finalized 全量账户查询**，随后才可接 F02 Dashboard 显示并重新审核。失败交易完整 receipt、真实 owner missing/ATA-close 和成本/PnL 仍未完成。

## 2026-10-14 独立 Claude 审查 #56：两个 P2 实证成立；#57 修复并待重新 Review

- **外部 Claude 对 PR #56 精确 SHA `55b430608d9048360f922a453f77cced479ac810` = `REQUEST_CHANGES`（两项 P2）**。第一项 `latest_inventory` 错将 Sidecar `read_wallet_captures(limit=100)` 以 SQLite rowid 导入顺序先截断再选最高 Slot；实际 1 份真正最新 Slot 1001 缺席 Mint 的快照在早期导入、随后 100 份旧正持仓入库，会错误返回旧余额 2500000。第二项 `capture_owner` 合法双 RPC 均失败时 `PARTIAL_SOURCE/slot_max=null`，旧读取逻辑把它当损坏而抛错，较旧失败会永久阻断随后健康快照。
- 保留旧 #56 审核 SHA，新增子 [Draft PR #57](https://github.com/lxxlx2/ChatGPT_mission_record/pull/57)，代码精确 HEAD `b70245f189a4940eab62288e2da23551f9e31129`。专用 `iter_wallet_captures` 使用 SQLite `fetchmany(256)` **遍历整个 wallet source 历史**，按真实 Chain Slot 选最高有效快照，不再受 rowid 100 条截断；旧有限历史展示接口保持不变。合法双失败无 Slot 采集与有 Slot 快照按观测时间判断，新健康晚于旧失败→正常显示新健康；最新双失败晚于旧健康→`SOURCE_ATTEMPT_FAILED_NO_SLOT`、数量 `null`，绝不复用老正余额或推断卖出。
- [精确 #57 CI #38568196200](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38568196200) **SUCCESS: 46 focused / 1,574 full tests**。实测 121 份乱序有效源，最多 Slot 1001 先导入、120 份低 Slot 的 2500000 正余额后导入，准确选择最高 Slot 且缺席金额为 `null`；另验证双失败→健康、健康→最新双失败、乱序导入旧失败以及 stale 失败。 [联合 CI #38568196197](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38568196197) **SUCCESS: 71 focused / 1,626 full**, 当前 main + A05 #57 栈 + C02 #49 + F01 #44 仅隔离 runner 合并回归。
- **仍须另一 AI 对 #57 这一精确 SHA 重新模块代码 Review 才能标记 `CODE_REVIEW_APPROVED`**；两次 CI PASS 不等于 Review。真实 32 Mint/ATA 来源、Mac 实机和 F02 页面、成本 PnL 仍为业务验收缺口。保留 Draft / NO_MERGE / NO_DEPLOY，并按开发规范做后续跨模块 Review、全功能完成后整体 Review。

## 2026-10-14 PR #57 外部 Claude 第三次 A05/F02 模块审核：1 P2；PR #58 单独修复

- **外部 Claude 对 [Draft PR #57](https://github.com/lxxlx2/ChatGPT_mission_record/pull/57) 精确 SHA `b70245f189a4940eab62288e2da23551f9e31129` = `REQUEST_CHANGES`（1 P2）**。先前两项旧余额复用与旧双失败阻断 P2 已由 Claude 独立用 601 份来源重放确认关闭，但无 Slot 失败记录的 `missing` 只核对长度 2，没证明分别属于 SPL Token 和 Token-2022。合法哈希、两条相同 SPL 错误的合成异常来源被错误当作两个不同程序都失败；不是实际链上余额，也不应当作真实完整失败证据。
- 新 [Draft PR #58](https://github.com/lxxlx2/ChatGPT_mission_record/pull/58)，保留 #57 已审查 SHA 不覆写；实现 `_valid_unavailable_dual_program_capture`：两个官方 Program ID 各一次，`reason=TOKEN_ACCOUNT_QUERY_UNAVAILABLE`、`error_type` 合法类名且失败字段结构精确；`program_coverage=[]`、`mints=[]`、账户和 Mint 计数为严格整数 0、Slot 双 null，及无原子/历史/受益人/总余额证明和无 USD/PnL 的必要一致性条件。异常重复程序/未知程序/损坏类型/内容矛盾直接拒绝，不能被归类为双程序失败；真正的双 TimeoutError 仍隐藏更早正余额，而更早失败不覆盖更新健康来源。
- 研究侧 SQLite 自动化对抗测试包含重复 SPL、重复 Token-2022、缺少或无效错误字段、未知/不可哈希程序、非字典失败项、非空账户/Mint、计数和资产验证矛盾、第三条失败项，另保留早期 121 份乱序采集及 601 份人工独立审查证据。**测试数据是合成异常来源，明确非真实 RPC 完整失败样本**。
- 维护既定流程：#58 **精确最终 SHA** 模块专项/全量 CI → 联合 F01/C02 CI → 新独立 Claude 审查 → 真实 A05 32 Mint/ATA 与 F02 页面 → 跨模块单独审查 → 所有模块完成后最终总体独立审查。未获新的独立 Review 前**不能标记 A05/F02 REVIEW_APPROVED**；所有 PR Draft / NO_MERGE / NO_DEPLOY，生产 Mac 数据与 Frank V1/Gmail/launchd 不修改。**PR #58 最终 SHA `063e8bada37534c13e801ea6f63e97d8f5586f4b`** 的 [模块 CI #38571793733](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38571793733) **65 focused / 1,593 full PASS**，[临时联合 CI #38571793773](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38571793773) **90 focused / 1,645 full PASS**，合并当前 main + A05/F02 #58 + C02 #49 + F01 #44 无 Git 冲突。**另一 AI 尚未对 #58 最终 SHA Review，仍不可标记代码审核通过。**

## 2026-10-14 PR #58 两份独立代码 Review 均 APPROVE；转入真实 A05/F02 来源主线

- **PR #58 固定 HEAD `063e8bada37534c13e801ea6f63e97d8f5586f4b`、父审查基线 PR #57 `b70245f189a4940eab62288e2da23551f9e31129`**。用户提交 GPT-6.1 Sol 的独立审查 `APPROVE`，本轮另读取 Gemini 3.8（用户标识）的完整独立审查附件，结论亦为 `APPROVE`。两份审查均针对 PR #58 **源代码补丁**，分别独立复现哈希合法但重复 SPL 失败记录在旧版的误判，以及新版对双程序 Program ID、failure structure、Slot/null、空账户/数量/经济证据的严格检查；没有发现新的 `REQUEST_CHANGES`。
- 独立验证区分：6.1 Sol 审查补做 25 个有效哈希异常来源、601 条 SQLite 多批次、107 个定向回归、全量 1,593 PASS；Gemini 审查附录记录临时 SQLite 重放、真实格式 TimeoutError、pyflakes/Node、全量 1,593 PASS、组合源树干净合并。**模型标签与本地证据属于用户提供的外部报告，不伪装 GitHub 原生 Review 或可远端访问的审查日志**。原始附件中 Mac 私有路径不复制到仓库。代码整改在 #58 闭合，不再对固定已批准 SHA 追加产品补丁。
- 此轮再次核实 GitHub：#58 为 `open/draft/unmerged`，HEAD 不变；[精确模块 CI #38571793733](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38571793733) `SUCCESS`，65 scoped / 1,593 full；[精确联合 CI #38571793773](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38571793773) `SUCCESS`，90 focused / 1,645 full。联合 CI 运行时实际合成 SHA 为 `2dd51f5a633cfcedaf5d7edef6b87defe9a75690`（来自独立报告），分支仍可变，后续总体集成必须重新固定全部 SHAs。
- **现阶段状态**：`A05_F02_LATEST_SNAPSHOT_RESEARCH_CODE_REVIEW_APPROVED`，绝非 `A05_32_MINT_BUSINESS_ACCEPTED` 或 `F02_DASHBOARD_FINISHED`。按主线继续真实 32 Mint 目标名录、SPL + Token-2022 finalized owner 全账户、非 ATA、最新 Slot/时间、实际 F02 可核实仓位与 Mac 只读浏览器验证；单模块独立审核→跨模块独立整合审核→所有模块完成后总体独立审核不变。
- Review 凭据写入 [PR #58 评论](https://github.com/lxxlx2/ChatGPT_mission_record/pull/58#issuecomment-6170047772)。**NO_MERGE / NO_DEPLOY / NO_TRADES / NO_GMAIL / NO_PRODUCTION_SQLITE**。F01/#44、A02/#42、A03/#43、A05 链上真实数据、C01/#46 等仍需自己对应模块的验收，不因 #58 局部通过而称全仓库审核完毕。

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

## A05→F02 主线强制验收顺序（2026-10-14 新增，不能跳步）

**依赖顺序固定：`A05-R1 完整 RPC 来源证据 → A05-R2 精确 32 Mint/ATA 对账 → F02-R1 真仓位只读查询 → F02-R2 Dashboard 浏览器实测 → F02-R3 Mac 隔离验收 → INTEGRATION_REVIEW → FINAL_OVERALL_REVIEW`。** 本节为正式开发进度要求，不是可选备注；重启新对话必须先检查下列未完成项。任何步骤未达标不得勾选后续业务完成。

- [ ] **A05-R1 保存完整原始 RPC**：只读、手动触发，按官方 Solana `getTokenAccountsByOwner` 分别查询 SPL Token 与 Token-2022，`finalized`、`jsonParsed`；显式保存每个**完整** JSON-RPC `result/context.slot/value` 的不可变原始文件/哈希、钱包、Program ID、UTC 采集时间、字节数及完整性状态，再以现有 `capture_owner` 生成规范化 Sidecar。传输被截断、JSON 不完整、响应 ID 不匹配、RPC error 或只成功一个 Program 时只允许记录 `PARTIAL_SOURCE`，不能将缺席的 Mint 置 0。限制文件大小并拒绝写生产 SQLite、任意密钥、私有 URL 到 Git/日志。因现有 Alchemy 连接器输出约 8KB 截断，**必须换用可保存整份响应的采集通道**，不可凭连接器可见片段声称 RPC 完成。
- [ ] **A05-R2 核对 32 Mint 与全部 ATA**：从明确版本的真实 Frank 业务 registry/历史已冻结目标名录读取**准确 32 个不同 Mint**，记录原文证据、实际来源 SHA、检查时间及新旧增删差异，不能随意凑满 32 个，更不能只用当前持仓 Mint 代替历史目标。对每个 Mint 对齐两程序全部 Token Account（包括非标准 ATA），记 token account/pubkey/mint/owner/program/raw amount/decimals、两个 finalized Slot、账户数和缺失/冲突；针对已关闭 ATA / 过往 Token Accounts 的历史缺失另列 `UNVERIFIED`，不能用现时 `0` 推断卖出。只有两份完整可验 RPC 和准确名录才可标 `A05_SOURCE_ACCEPTED`。
- [ ] **F02-R1 接真实研究仓位查询**：仅消费 A05 完整原始证据经规范化后最新一次 Sidecar 状态，用已审过的 PR #58 快照来源校验；返回独立人物钱包、Mint、raw/quantity、来源 Slot/时间/哈希、最新尝试失败或来源过期状态，未知保持 `null`，未证实价格/成本/收益不计算、不显示虚构 `$0` 或“仓位不明”可交易结论。不直接混用普通 `TX` 归档或读未审核的生产状态。
- [ ] **F02-R2 Dashboard 页面业务联调**：真实 UI 中仅展示已核实/最新且可执行的对象，研究“观察/不跟/历史”单独区域；用户可点开准确 Mint/CA、钱包归属、仓位、资产来源、更新时间、未知原因，必要时有明确重新采集入口；错误/空状态不可冒充清仓，不更改冻结 Frank V1 跟单决策、邮件与订单。
- [ ] **F02-R3 Mac 隔离验收**：新代码固定 SHA、独立只读研究 Sidecar / 临时端口，对照 Mac 实际 RPC 完整响应与页面数据；覆盖查询缺失、超时、旧余额复活防护、多 ATA、非原子 Slot 与 32 Mint，审查截图/浏览器交互和源文件哈希。不得读取/修改生产私有库进行试验，生产切换须另行显式授权。
- [ ] **独立模块审核与整体审核**：A05-R1/R2、F02-R1/R2 达到实用模块检查点，各自先执行精确 SHA 专项+全量 CI 和另一 AI `APPROVE`；代码改变要重新审核受影响模块。F01/C02/A05/F02 合成真实固定 SHA 集成树后另做**一次独立跨模块 Review**；所有 41 项业务内容真实完成，再做**额外一次全系统独立 Review**；真实 Mac 验收、回滚及用户明确部署授权是独立发布门禁。仅 PR #58 局部 `APPROVE` 不等于 A05/F02 完成。

**已确认阻塞（不许静默跳过）**：官方 owner RPC 在此前连接器输出被截断；目前还未取得完整原始 SPL/Token-2022 同次文件、真实完整 32 Mint 名录与 Token Account 明细，故 `A05-R1/R2 = NOT_ACCEPTED`，`F02-R1/R2/R3 = NOT_STARTED_OR_UNVERIFIED`。来源检查另见 `FRANK_A05_F02_CHAIN_OWNER_SOURCE_PREFLIGHT_20261014.md`。本路线不包含生产合并/部署许可。

## 2026-10-14 A05-R1 完整原始 RPC 保存模块：代码检查点与实证限制

- 从双独立外部代码审查通过的 #58 固定 SHA `063e8bada37534c13e801ea6f63e97d8f5586f4b` 建立**独立新子 [Draft PR #59](https://github.com/lxxlx2/ChatGPT_mission_record/pull/59)**；精确测试代码 HEAD **`9b6f7a90fe92ae6eea497d364ebc7f9bf109f042`**，未修改 PR #58。新增 `wallet_full_rpc_evidence.py` + 手动 CLI `frank_capture_owner_full_receipts.py`：在独立研究目录完整写入两次 RPC 原始响应字节及各自 SHA-256/长度/Program/Slot/UTC，然后可全离线、无网络、无副作用验证重放，仅双程序完整时才允许显式研究 Sidecar 导入。工具默认计划模式无网络/文件写；响应截断、空/错 JSON、错误 ID、一个 Program 无效时标 `PARTIAL_SOURCE` 而非空仓/全钱包。
- RPC wire source 大小上限每条 12,000,000 bytes，Program ID 与 owner、`finalized`、request/response ID、`minContextSlot`、非原子 Slot 均受检查；原始数据写入 Git 仓库路径被禁止，RPC URL/密钥不落盘。人工完整源目前仍未成功采集；**本代码只解决“如何保存完整证据”的开发问题，未达到 A05-R1 实际业务验收**。
- [精确 #59 模块 CI #38580093962](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38580093962) **SUCCESS: 73 focused, 1,602 full**，测试包含 >8KB 原始响应、不截断原文/校验原始 SHA、离线重放、partial/截断和非法来源拒绝、隔离 sidecar 幂等性；[固定输入联合 CI #38580093851](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38580093851) **SUCCESS: 99 focused, 1,654 full**，CI 真正合入当时 main `8afe6049` + #59 `9b6f7a90` + C02 `8898134a` + F01 `516e3335`，集成树确切 SHA **`fdc25bccfbd6319320a570fbda1f7d997fa7f02c`**，全部回归通过。早期 lint 失败的真实日志保留。
- **新模块独立 Review 等待中**：在 [PR #59 评论](https://github.com/lxxlx2/ChatGPT_mission_record/pull/59#issuecomment-6170681886) 冻结 final HEAD 和专项审查清单；另一 AI 给出 `APPROVE` 才能将 A05-R1 **代码**门禁标通过。不要拿上一模块 #58 的 APPROVE 或 CI 绿灯复用成 #59 审查批准。
- 后续仍按本文件“ A05→F02 主线强制验收顺序”执行：在可保存完整响应的通道做一次真实手动采集（目前连接器仍限制输出）→ 核对真实历史 32 Mint 名录 / 全 Token Account/非 ATA/关闭账户风险 → F02 只读接口和 Dashboard → Mac 实机只读验收 → 各模块独立/集成/最终全系统审核。**NO_MERGE / NO_DEPLOY，未触发用户 Mac 或生产来源采集**。

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

## 2026-10-14 A05-R1 reviewer-confirmed transport defects and child CI checkpoint

- External review of frozen Draft [PR #59](https://github.com/lxxlx2/ChatGPT_mission_record/pull/59) code SHA `9b6f7a90fe92ae6eea497d364ebc7f9bf109f042`: GPT-6.1 Sol **REQUEST_CHANGES**, reporting real TLS/HTTP reproductions of two blocking P2s (HTTPS 302 downgraded to plaintext HTTP GET; valid JSON received with shorter bytes than HTTP declared Content-Length). Gemini 3.8 **APPROVE** covers existing synthetic/regression behavior but did not reproduce those transport failures. Decision: keep original #59 `NOT_APPROVED`. Do not claim A05-R1 business completion.
- Scoped [Draft child PR #60](https://github.com/lxxlx2/ChatGPT_mission_record/pull/60) on fixed initial HEAD `e4529ba7069e5499d12323a7160ceac08c481fae` changes only RPC transport and regression tests, and CI triggers/checkpoint documentation. Redirect refusal, entity length equality, chunk-abort handling and oversize refusal; five real localhost HTTPS/HTTP socket tests. Parent #58/#59 source preserved.
- Exact-child GitHub [module CI #38589789392](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38589789392) **SUCCESS**: 78 scoped, 1,607 full. [Combined F01/C02 CI #38589789906](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38589789906) **SUCCESS**: 104 scoped, 1,659 full; CI main at run `eb245396014ae840f00c7132975dbe0d40764637`, source `e4529ba7069e5499d12323a7160ceac08c481fae`, approved C02 `8898134a8a302e1187138f7fb3da87a554567e6d`, F01 `516e3335a134c608f477019b79027982f43af32a`; disposable combined SHA `87fe8805e2421e8f59321ffeebc3c28724d6a4b4`. No code conflicts. Exact code/CI PASS is not independent Review.
- **Still unchecked:** another-AI independent exact-head code review of #60, then user-approved manual full actual Frank SPL/Token-2022 wire capture and accurate historical 32 Mint/current Token Account reconciliation. Only after actual evidence proceed to F02 read-only API, browser Dashboard, Mac isolated acceptance, independent integration review and final all-system review. **NO_MERGE / NO_DEPLOY / NO_TRADES / NO_GMAIL / NO_PROD_SQLITE**.


## 2026-10-14 A05-R1 exact SHA review closure and next factual source dependency

- **Code review checkpoint now passed for child [PR #60](https://github.com/lxxlx2/ChatGPT_mission_record/pull/60) SHA `e4529ba7069e5499d12323a7160ceac08c481fae`**: user-provided independent GPT-6.1 Sol `APPROVE` and Gemini 3.8 `APPROVE` on same immutable head; both independently reported R1 TLS-to-HTTP redirect and R2 HTTP entity truncation fail closed. External reviews are recorded as external (not GitHub-native formal approval), with reviewer labels as reported. See [PR #60 exact review ledger comment](https://github.com/lxxlx2/ChatGPT_mission_record/pull/60#issuecomment-6172383516). Parent PR #59 at SHA `9b6f7a90fe92ae6eea497d364ebc7f9bf109f042` retains `REQUEST_CHANGES`; no patch/approval transfers back to old code.
- Exact-head [module CI #38589789392](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38589789392) `SUCCESS` 78 scoped/1,607 full; [combined CI #38589789906](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38589789906) `SUCCESS` 104 scoped/1,659 full. GPT-6.1 Sol reported 19 extra real TLS/HTTP tests and independent 1,607 full, 104 combined focused but **did not rerun independent combined full**. Gemini reported local suite 1,580 PASS/3 SKIPPED, not to be confused with exact GitHub CI. P3 JSON-RPC envelope strict version check remains nonblocking and deferred; do not prolong primary line for hypothetical P3 without impact proof.
- **Business evidence is still PENDING**: `A05-R1_CODE_REVIEW=EXTERNAL_APPROVE`, `A05-R1_REAL_FULL_DUAL_PROGRAM_RPC=NOT_ACCEPTED`, `A05-R2_EXACT_32_MINT_AND_ALL_TOKEN_ACCOUNTS=NOT_ACCEPTED`, `F02=NOT_ACCEPTED`, `MAC=NOT_TESTED`. Initial canonical registry at this reviewed SHA only identifies Frank research wallet; it does not define the historical 32 Mint roster. Previously truncated connector output must not be patched into a full count. The sandbox HTTP environment could not reach public Solana JSON-RPC (DNS resolution failure during isolated probe); this is a tool-environment limitation, not a claim about Frank source or user's Mac.
- **Next execution boundary**: run the already-reviewed manual `frank_capture_owner_full_receipts.py` from exact PR #60 code in an isolated environment with working HTTPS RPC, archive both full original finalized Token program responses and offline replay, then obtain the actual frozen historical 32 Mint roster and current/closed ATA coverage. Keep private raw/source URL outside public Git, persist only redacted verifiable status and checksums. Continue F02-R1 real read-only API → Dashboard → Mac isolation → independent combined and final overall review after source acceptance. **NO_MERGE / NO_DEPLOY / NO_TRADES / NO_GMAIL / NO_PROD_SQLITE / NO_NEW_AUTOMATION**.


## 2026-10-14 A05-R1 manual full RPC result received; immutable 32 Mint roster discovered; A05-R2 started

- **User Mac actually executed reviewed PR #60 SHA `e4529ba7069e5499d12323a7160ceac08c481fae`** from a separate checkout with plan-only then manual `--execute`. User-provided stdout `FULL_DUAL_PROGRAM_SOURCE_REPLAY_VERIFIED`; wallet `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`, source capture SHA `a91fed6fae63f51557ab88fb9ae892247cc32deccd26c631d765ff27aff03261`, finalized slots `456895319..456895320`, observed `3,233` Token Accounts across `3,233` currently visible Mints; `same_slot_atomic=false`, no research Sidecar import or protected SQLite write. Private raw bundle remains under Mac `~/.local/share/frank-owner-full-rpc-evidence/owner-f537013b8a094e608cf9657622b627d6`. **This is user-provided CLI output, not an independently downloaded/rehashed raw payload here**, so raw-source external readback remains pending; never treat 3,233 as 3,233 FOLLOW targets.
- **Frozen original 32 sources FOUND in actual Git:** `meme/evidence/frank-v2-thirty-two-mint-finalized-2026-10-11.json`, Git blob `c6f43e4a63ea9daa1c9b820b8faed8ccefcdb2d1`, precisely 32 distinct `EXACT_32_MINTS_FROM_MAC_D0_LOCAL_TRADE_AND_MODEL_UNION`, historical 10 nonzero/22 zero at old multiple finalized slots 455426889..455430371. **Do not treat old balances as current.** A separate 33rd later Mint exists in `frank-v2-33-mint-mac-ledger-gap-analysis-2026-10-11.json`; retain exact 32 freeze and reconcile later Mint separately.
- New [Draft PR #61](https://github.com/lxxlx2/ChatGPT_mission_record/pull/61) starts A05-R2 offline, **based on externally reviewed PR #60**. The new standalone CLI verifies original dual-program bundle with existing approved replay, validates old 32-list immutable Git identity, groups only those 32 current account balances including noncanonical/multiple Token Accounts, differentiates PRESENT_NONZERO / PRESENT_ZERO / NO_OPEN_ACCOUNT_OBSERVED and emits 32-only local research JSON or limited summary. Never map absent account to historical market SELL or proven PnL. No RPC, no Sidecar import, no production reads/writes by new CLI. New code must have exact-head targeted/full/integrated CI and independent other-AI Review **before code gate accepted**; tests do not replace actual Mac bundle vs roster reconciliation.
- On first PR #61 CI, static check reported **three unused imports**. Tracked failure not hidden; child fixed imports only and reruns exact-head tests. No changes to reviewed PR #60 source/parent commit. Until final code review and real 32-file reconciliation, `A05-R2=IN_PROGRESS / F02=NOT_STARTED / NO_MERGE / NO_DEPLOY`. Next stage after 32 data acceptance remains F02 read-only source-backed position API → Dashboard actual browser → Mac isolated QA → independent cross-module integration and whole-system Review.


## 2026-10-14 A05-R2 PR #61 exact CI checkpoint and review gate

- New [Draft PR #61](https://github.com/lxxlx2/ChatGPT_mission_record/pull/61) source HEAD **`076f9cabb58cac2d0890fa15cf9906cafe37423b`** on approved-parent #60 SHA `e4529ba7069e5499d12323a7160ceac08c481fae`; adds frozen 32 list immutable Git blob validation, whole 3,233-account source replay and per-32 live Token Account aggregation. Real dataset is **not** uploaded or consumed by CI. **No external independent module review yet**, keep `REVIEW_PENDING`.
- Initial [CI #38594499429](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38594499429) had **static failure** caused by 3 unused imports (module failed); the concurrent original-head combined job passed. Two controlled import-only fixes were committed; no evidence altered. Final fixed exact SHA [CI #38594640833](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38594640833): **module SUCCESS** 60 focused/1,615 full, pyflakes/compileall/JS syntax PASS; **combined SUCCESS** 94 focused/1,667 full on then-current main `d16840bb3a1f508af48c6a3080e384c82d3d9e3d` + A05-R2 `076f9cabb58cac2d0890fa15cf9906cafe37423b` + C02 `8898134a8a302e1187138f7fb3da87a554567e6d` + F01 `516e3335a134c608f477019b79027982f43af32a`, disposable integrated SHA `806c7492a83fe946ca1dc28557fbc0ed81d2e2be`.
- **Next exact gate**: another independent AI review of #61 fixed SHA against #60 and original Git evidence: old 32 frozen file sha/owner, full original raw bundle replay, no-open-account `null` vs zero, multiple ATAs, negative price/PNL assertions, no production SQLite/Gmail changes. Only then manually run the reviewed **offline** 32 target reconciliation on the actual user Mac raw bundle, keep detailed report private and share only aggregate and evidence hash. This is A05-R2 code-ready/review-pending, **not** real 32 account balance business acceptance. F02 remains downstream.


## 2026-10-14 A05-R2 both external code reviews APPROVE; actual dual raw files and real 32 reviewed; F02-R1 next

- Immutable [PR #61](https://github.com/lxxlx2/ChatGPT_mission_record/pull/61) SHA `076f9cabb58cac2d0890fa15cf9906cafe37423b`: two independent user-forwarded reviews GPT-6.1 Sol `APPROVE` and Gemini 3.8 Flash High `APPROVE` (no P0/P1/P2). Actual CI module 60 / 1,615, combined 94 / 1,667 SUCCESS. External report recorded [PR #61 comment #6173101555](https://github.com/lxxlx2/ChatGPT_mission_record/pull/61#issuecomment-6173101555). No GitHub-native formal review claimed; PR remains Draft, no merge or deployment.
- **Actual Mac source reviewed beyond stdout by GPT-6.1 Sol:** privately available two finalized full RPC reply originals: SPL 945,282 bytes/1,785 token accounts/slot 456895319, Token-2022 848,980 bytes/1,448 accounts/slot 456895320, archived at `2026-10-14T15:54:15.873036Z` (22:54:15 BKK), exact capture SHA `a91fed6fae63f51557ab88fb9ae892247cc32deccd26c631d765ff27aff03261`. Report says raw SHA/length/manifest and independent aggregation rechecked. Real historical frozen 32 at this time: **9 nonzero/23 zero/0 absent/32 open target token accounts/0 multiple-account targets**, every target checked against original raw aggregation. Other 3,201 accounts are not automatically actionable. Gemini checked code, but reported actual Mac business run pending: reviewers have different evidence access, **do not claim two independent real raw reviews**.
- Historical 10 nonzero / 22 zero in 2026-10-11 frozen 32 evidence vs 2026-10-14 9 / 23 cannot prove SELL or USD PnL; no fresh live balance, no 33rd minted target retroactively in 32. Closed ATA/full ownership history and user business acceptance still unverified. Private raw bundle/reports stay off public Git.
- **Mainline next:** F02-R1 isolated read-only wallet snapshot API from manually authorized complete original bundle/isolated research Sidecar, honoring exact person/wallet binding, immutable 32 target, capture freshness and newest failed attempt, no stale positive resurrection, provenance sha/slot/time and null-unknown vs observed zero; on-disk read-only, no prod listener change. After module independent review: F02-R2 actual Dashboard browser and F02-R3 Mac isolated acceptance, then separate combined and overall independent reviews. `NO_MERGE/NO_DEPLOY/NO_TRADES/NO_GMAIL/NO_PRODUCTION_SQLITE/NO_AUTOMATION`.


## 2026-10-14 F02-R1 isolated local read-only API begun (Draft PR #62)

- New [Draft PR #62](https://github.com/lxxlx2/ChatGPT_mission_record/pull/62) **child of externally reviewed A05-R2 PR #61**; source branch `dev/frank-f02-r1-isolated-readonly-position-api-20261014`. Adds an isolated standalone localhost HTTP route `GET /api/research/positions`, manual PLAN_ONLY / probe / serve; **does not change actual production `mission_control/server.py` or Dashboard**, Writer, Gmail, LaunchAgent, trade policy or production SQLite.
- Binds Registry person and exact wallet (multi-wallet requires explicit wallet), validates frozen historical 32 Mint Git identity, validates *actual original complete dual-program RPC bundle* at startup, then reads manually authorized isolated research `ACCOUNT_CAPTURE` Sidecar **SQLite read-only**. Exposes a quantity only if the **latest** archival capture hash matches this verified original-wire SHA and is age-fresh. New failure, partial, stale or unverified-newer capture returns all raw/quantity **null**, preventing old-position resurrection. No open account is `NO_OPEN_ACCOUNT_OBSERVED` with null raw, separate from an observed zero account. Source UTC, slots, non-atomicity, wallet identity, capture SHA, age, explicit historical/non-trading label and full observed target Token Accounts preserved; no USD/PnL claimed.
- Pre-existing user Mac bundle is still private; user CLI initially recorded `research_sidecar_imported=null`. **F02-R1 source-backed serving cannot be marked actually Mac-operational until a separately authorized research-only import and isolated same-SHA real Mac probe.** No automatic import and no listener deploy.
- New F02-R1 code and tests/workflow started; initial CI discovered two modified synthetic capture fixtures had used the wrong fingerprint function, correctly rejected by immutable Sidecar. An isolated test-only fix changed to the approved Sidecar fingerprint. Original failed tests retained. Fixed-head targeted/full + disposable F01/C02 integration CI and separate other-AI code review are mandatory before F02-R1 code acceptance; next stage F02-R2 page integration and F02-R3 Mac product verification.


## 2026-10-14 F02-R1 initial exact-head CI passed; independent module review pending

- [Draft PR #62](https://github.com/lxxlx2/ChatGPT_mission_record/pull/62) fixed tested HEAD `c24119989b7e752ee925e38c777ceb376ac97f81`, child of approved PR #61 `076f9cabb58cac2d0890fa15cf9906cafe37423b`. No changes to existing production Dashboard server or Frank V1.
- Initial source tree CI `69ae28a42858c9fd1dbc0855e5409b6ea6e1c5e1` failed 2 tests: altered synthetic snapshots were hashed using the wrong fixture fingerprint and correctly rejected by immutable Sidecar. Test-only correction uses official `wallet_inventory_snapshot._fingerprint`, no production algorithm change. First failed CI [#38598963722](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38598963722) retained.
- Final exact-SHA [CI #38599128708](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38599128708): module `SUCCESS` **69 targeted / 1,624 full**; disposable joint `SUCCESS` **103 targeted / 1,676 full**. Combined input then-main `d16840bb3a1f508af48c6a3080e384c82d3d9e3d` + F02 `c24119989b7e752ee925e38c777ceb376ac97f81` + approved C02 `8898134a8a302e1187138f7fb3da87a554567e6d` + F01 `516e3335a134c608f477019b79027982f43af32a`; disposable merged SHA `f560bd6ec817220206379e8f88855369e1ac3bee`.
- Next gate: independent another-AI exact-head F02-R1 review including *actual isolated HTTP* response, fresh/stale/failed/partial/unverified SHA masking, latest immutable Sidecar, wallet identity, archived semantics, frozen 32, no writes; then separate authorized user Mac manual Sidecar import and isolated probe. CI is not F02 Mac product validation; no operational current holdings claimed. `NO_MERGE / NO_DEPLOY`.
