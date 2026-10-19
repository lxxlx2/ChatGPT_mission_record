# Frank PR #112 — 无默认交易金额的新策略审批与 Mac 受控切换准备

Date: 2026-10-20 (Asia/Bangkok)  
Status: **PREPARATION_ONLY / NO_USER_LIVE_POLICY_APPROVAL / NO_MERGE / NO_DEPLOY**  
Evidence authority: [PR #112](https://github.com/lxxlx2/ChatGPT_mission_record/pull/112), [独立代码审核](https://github.com/lxxlx2/ChatGPT_mission_record/pull/112#issuecomment-6275141450), [Mac PARTIAL 验收](https://github.com/lxxlx2/ChatGPT_mission_record/pull/112#issuecomment-6275682020), [GPT 复核](https://github.com/lxxlx2/ChatGPT_mission_record/pull/112#issuecomment-6275760620)。  
产品代码固定 SHA: `bb3b9996f97e0cebc2fdf183ca22dac255dd7976`；PR #119 D1/D2 验收 SHA: `3e8eb8bbd2e84762578fda09e03091cc47d8adb7`；本准备文档以 `main` `34c85703dccf6fc7e3288c36e32fc6cf8138b870` 为基线。

**本文件仅保存用户可审核的发布边界与未来演练步骤。不是候选的实际可运行 approved JSON，也不生成新的授权摘要、部署文件、launchd 任务或邮件。** 未经新的用户明确许可，不能因为本文存在就运行安装脚本或操作生产。

## 1. 产品目标与必须向用户解释的行为差异

Frank 是钱包行为观察工具，不是自动交易器。买不买、怎么操作、买多少，完全由用户决定；废止过去未获认可的固定 `$30` 下单/报价假设。保留按源证据显示的真实买卖动作、数量、时间、Mint、来源风险和信号，不伪造当前持仓、报价、执行收益。

| 通道 | 当前有依据的行为 | PR #112 无金额后的目标与限制 |
| --- | --- | --- |
| **冻结 Frank V1 源信号** | ACCUMULATION 本地通知；MULTIPLE 本地 + Gmail；源 `signals/outbox/email_content` 独立记录 | 继续按已授权 V1 源信号工作，不需用户下单金额；不改 V1 代码、阈值、队列或历史邮件 |
| **Mission Control 决策** | 旧独立的 quote-dependent BUY/SMALL_BUY 与判断通知，可能引用已否决的默认金额 | 未输入用户选择的金额时：`WAIT` + `execution_assessment_status=NOT_ASSESSED`；Jupiter 执行报价不请求，不制造 `BUY`、`NO_ROUTE`、价格冲击或虚假 quote timestamp |
| **Mission Control 通知** | 与 V1 源信号的邮件/本地通知不是同一通道 | 新鲜的首条未评估 WAIT 不额外送一条可能重复的决策通知；历史已有 BUY 等状态的转变仍需在临时副本中核验实际状态转换、过期/去重；**不能承诺旧 MC BUY 邮件仍以原样发送** |
| **Dashboard D1/D2** | PR #119 已完成限定范围的 Mac Chrome 只读验收 | 集成时仍需显示已核实活动和带日期的非实时持仓，不得因新策略缺报价就隐藏钱包事实、信号或观察池 |
| **用户手动 CA 调查** | 不应自动请求固定金额的 Jupiter quote | 显示有来源、有时间戳的池子参考价/流动性和历史交易；只有用户明确要求某一研究金额时才可另行按权限求报价，无自动成交 |

**产品 GO 与策略收益 GO 是两回事。** 本准备步骤不批准任何自动交易、策略盈利结论或新的常驻服务。

## 2. 三份策略身份，禁止混淆

| 身份 | 当前事实 | 后果 |
| --- | --- | --- |
| 已安装生产 Mission Control | Mac 执行者报告 loop PID 36070 的 `--approved-policy-sha256` 为旧摘要 `355336f2…`；安装的旧策略可能仍包含未认可的 `$30` | **生产尚未修改**，不应错误声称运行端已取消默认报价；也不能把旧安装版当成可接受的回滚目标 |
| PR #112 仓库候选 | `config/follow_policy_v1.approved.json` 虽有历史“approved”文件名，实际为 `REVIEW_ONLY`、`live_delivery_approved=false`、`basis=PR112_NO_DEFAULT_AMOUNT_POLICY_PENDING_EXPLICIT_USER_LIVE_APPROVAL`，没有 `quote_usdc_amount` | 即使传入新文件自身摘要，`live_delivery_policy_authorized()` 仍应拒绝 LIVE。**这是正确的临时阻断** |
| 未来新的正式 live 策略 | **尚未生成、审核或获用户批准**。只有在冻结行为与整合测试后，才可以在单独隔离候选中提出 `FROZEN_APPROVED/true` 的字节精确文件，并计算新的策略文件 SHA-256 | 要求用户针对**完整文件内容与该 SHA-256** 签字；Git commit SHA 与政策文件 SHA-256 不同，不能互换；任何自我计算/自我批准都不构成授权 |

当前新策略不应在仅为获得 PASS 的情况下擅自改成 `FROZEN_APPROVED` 或从旧 2026-10-07 basis 继承许可。保持 PR #112 的审核 SHA 不变。

## 3. 现阶段已经有的证据，以及必须诚实保留的缺口

- PR #112 GitHub Actions `#39307423435`、1428 离线测试通过；独立 reviewer 对固定 SHA 判定 `CODE_REVIEW_APPROVE`，P0/P1/P2 无。
- 真实 Mac 只读快照：V1 `signals=5`（ACC 4 / MULT 1）、源 `outbox=6`、`email_content=1`，Mission Control 无金额周期后源表逻辑哈希不变，新 Jupiter 请求数 0，新增 MC decision outbox 0。
- 七项 fake local/Gmail 通知路径通过，包括重复、过期、重试、Gmail DRY、模糊发送与重启去重；未执行真实 macOS 弹窗或 Gmail，这是正确的安全边界。
- **缺口**：快照里无同时满足 `runtime LIVE + open + 新鲜 ACC/MULT` 的候选，真实数据没有命中 `NOT_ASSESSED`，仅合成用例覆盖；正式 live 迁移、回滚、跨 PR 整合均未演练。状态继续 `MAC_NOTIFICATION_ACCEPTANCE_PARTIAL`，不用长时间等待自然信号来刷 PASS。
- 执行者报告 MC 数据库历史 `MANUAL_REVIEW=15`；这不是 15 封未送达邮件的证据，更不是允许自动重发的名单。需检查每条状态和原始冻结内容身份，但不得无证据地变更或清空。

## 4. 下一步唯一受控准备：Mac 隔离 release/rollback dry-run（未来单独授权执行）

由 Claude 在 Mac 独立 worktree 及临时 HOME / 控制目录完成；当前**只制定方案，不启动**。避免再次跑一遍 1428 项来代替真实迁移证明。

1. **锁版本并记录拓扑**：记录现有 Loop/Dashboard/V1 三个进程身份与服务关联、仅只读查看其 runner 中的策略路径及外部摘要；精确记录 PR #112、#119、运行版、文件摘要与现有源码来源，脱敏本机绝对路径和个人身份。
2. **一致性只读快照**：生产 DB 用 `mode=ro` + SQLite backup API，所有后续写入仅发生于独立私有副本；不要对生产源执行 WAL checkpoint/PRAGMA 写操作。健康文件采样单独标注时点，不要求 WAL/SHM 运行时哈希固定。
3. **启动与通知全部假替身**：隔离加载当前旧策略与 PR #112 的 `REVIEW_ONLY` 策略，断言候选自身 SHA、旧 SHA、空 SHA 均拒绝 LIVE；Gmail/osascript/terminal-notifier、Jupiter、RPC 必须在入口被 fake/deny，明确实际外部发送/网络请求计数为 0。
4. **模拟新策略未来授权的 gate**：可以在内存或临时目录构造假设性 `FROZEN_APPROVED/true` 文件，仅用于验证由独立提供匹配/不匹配摘要时的 gate 行为；不得复制到运行路径，不得将本次测试用 digest 当用户批准。测试缺 SHA、错误 SHA、旧 SHA、自身 SHA 与 `REVIEW_ONLY`、假设新批准状态的正反例。
5. **复核真实历史队列**：在快照中仅统计 15 条 `MANUAL_REVIEW` 的 decision_id（允许仅摘要/hash）、通道、年龄、未确认/重复状态、冻结 presentation/receipt 存在性。不得把已过期、`SENT_UNVERIFIED`、`MANUAL_REVIEW` 记录自动重新入队或发邮件。模拟升级后首次 cycle 对历史 event 的动作，特别关注之前 BUY → 无金额 WAIT 的去重/失效通知。
6. **数据保持与延迟路径**：隔离周期必须复核 V1 源 outbox 独立、新候选/历史候选的 NO_BUY/WAIT/NOT_ASSESSED、Jupiter 0 新请求、无真实 OS/Gmail。检查 `OutcomeTracker.sample_due` 对旧 `ACTIVE` forward tracks 的 quote 路径，防止误称“无金额后整个服务永远不会调用任何 Jupiter”；若真实历史 active tracks 存在，只在替身中验证，不访问 API。
7. **集成验证**：PR #112 与 PR #119 都涉及 `server.py` / `static/app.js`；未来应在**单独 main-based 集成候选**人工选择已审核的最小变更，不能机械互相 merge 或覆盖。以用户可见 D1/D2、CA 入口、源信号/通知和无默认金额行为作联合 smoke。PR #119 / #112 的固定 SHA 审核结论不能自动继承到新集成 SHA。
8. **审计清理**：临时实例退出后仅核实由测试启动的临时端口/假替身结束，保留必要脱敏证据；不停止生产服务，不触碰现有 Chrome、钱包或 Gmail。
9. **结果报告**：只给 `MIGRATION_ISOLATED_REHEARSAL_PASS / PARTIAL / FAIL`、完整测试窗口、每项实际输入/输出、7 项旧矩阵是否复用、15 条状态分析、受影响服务、哈希和回滚可行性。无测试不得标 PASS。

**重点危险路径**：原 `scripts/install_mission_meme_launchd.sh` 要求 `CONFIRM_MISSION_LOOP_RESTART=1` 和外部批准摘要，但它不仅复制策略，还更新运行脚本及 Loop/Dashboard LaunchAgent。**不得将其作为“只换策略”的无风险演练命令。**

## 5. 未来正式切换 / 回滚（此处不执行）

须另有**明确审批后的**专门发布 runbook，事前记录部署集成 SHA、实际策略 JSON 的 SHA-256、生产应用源码版本、外部授权摘要、通知去重基线和测试证据，避免一边更换服务一边猜配置。

- **切换前**：用户确认新的通知行为及审核过的精确策略文件/摘要；对集成候选做受控 Mac 影子验证、回滚演练、必要的独立增量 review；所有受影响启动脚本/双 LaunchAgent 的副作用逐项列明，单独获得用户部署许可。绝不能自动沿用旧摘要 `355336f2…`。
- **受控切换**：以后另行核准单点操作窗口、留有旧运行状态和通知状态的可核验记录。禁止修改冻结 V1 源事实和历史消息内容；禁止“批准状态不匹配时先跳过摘要检查”。
- **检查**：V1 ACC 本地与 MULT Gmail 仍有独立接收条件；MC 无用户金额不产生 Jupiter 进入价或误导性 BUY 通知，故障不抹除 D1/D2 原始事实；检查刷新、去重和过期门禁。
- **出现错误时的回滚选择**：优先保持 V1 源监控/既有通知不变，将有问题的**新 MC live decision delivery** 安全禁止并标注 DEGRADED（具体操作先独立审核/经用户批准），而非直接恢复带旧 `$30` 的旧策略；如需回滚代码，也必须配套无默认金额的经核实配置。旧策略不能作为“不改行为”的回滚基线。
- **判据**：发送重复、发送过期、无来源 BUY、金额被默认为 $30、策略摘要绕过、真实生产写入越权、V1 通知中断、D1/D2 数据失真任一成立，立即停止后续放量并提交证据；不可把重启成功或 CI green 当作业务 GO。

## 6. 用户签字前的简明决策单（目前全部待批准）

以下是**建议的最小新行为**，不等于已批准：

1. 继续收到冻结 V1 的 ACCUMULATION 本地提醒和 MULTIPLE 本地 + Gmail 提醒；源事实、交易与观察池保持独立。
2. 没有由用户明确指定的研究金额，就不请求 Jupiter 执行报价，不作买多少或“可跟单 BUY”的执行结论。MC 仅保留审计/观察，不发送未经授权金额衍生的旧 BUY/SMALL_BUY 类型判断邮件；现有 V1 源通知不因此取消。
3. 不自动重发或删除 15 条 `MANUAL_REVIEW`，应以通知队列原始状态逐条审计；后续有需要再单独授权处理。
4. 先审核未来确切 `FROZEN_APPROVED/true` 策略候选、全量文件字节及 SHA-256，再由用户明确批准；之后另请一次部署批准。**批准新策略不等于批准安装，更不等于批准交易。**
5. 正式集成时只选择 PR #112/#119 已审查功能，并在全新的集成 SHA 上进行最小必要测试；不引入 F01/其他历史 Draft 的未经批准旧逻辑。
6. 只允许不含旧 $30 默认金额的回滚目标。若无法做到，停止 MC 新投递比恢复用户拒绝的旧交易假设更安全。

**当前唯一可用的发布决定：`POLICY_APPROVAL_PENDING / MIGRATION_DRY_RUN_NOT_STARTED / INTEGRATED_RELEASE_NOT_BUILT / PRODUCTION_NO_GO`。** 不要把上面的签字项目自行改为 `APPROVED`。

## 7. 外部策略摘要的带外批准机制（2026-10-20 演练发现；仅设计）

来源：[PR #126 第一轮 Mac 演练](https://github.com/lxxlx2/ChatGPT_mission_record/pull/126#issuecomment-6276065034)。测试证明 `live_delivery_policy_authorized(policy, sha256(policy), sha256(policy))` 对临时合成 `FROZEN_APPROVED/true` 文件可返回 True。**这验证了函数检查字节匹配，并不验证批准者身份**。它是既有 API 的信任边界；不是密码学哈希校验失效，也不代表 PR112 当前 `REVIEW_ONLY/false` 可被放行。

**必须将“批准源”与“候选字节”隔离；仅 GitHub PR 评论（包括机器人以用户账号代发的评论）、候选 JSON 自身字段、commit SHA 或安装脚本自算的 policy SHA，都不能单独构成带外签字。**

建议未来正式上线前设计并审核下述机械化控制，**本 PR 只定义验收合同，不实施、不部署**：

- **独立可信批准记录**：由用户在独立于仓库/自动化代理的审批动作中生成。记录字段至少包括：`policy_content_sha256`（策略文件**原始字节**的 SHA-256）、`release_code_commit_sha`（实际集成提交 SHA）、`scope=FRANK_MC_LIVE_NOTIFICATION_ONLY`、V1 源通知保持不变、MC 无默认交易金额与决策通知变化、批准人身份、审批时间、唯一审批 ID、审批是否允许重启/部署（默认 **false**）。可设失效时间，任何行为/字节/代码更改需重新审批。
- **授权来源不可由候选自签**：上线实现应优先验证带有**用户独立受保护签名**的批准记录（如需设计 macOS 用户在场签名，需评估 Keychain/硬件保护并单独审核），公钥/信任锚固定于受保护的已安装验证器而不是随候选自动替换；代理和部署脚本不得持有可无交互签名的审批私钥。若第一阶段仅采用人工核对的带外确认，也必须明确它是**流程控制而非可由现有布尔谓词自动证明的身份验证**，不能声称实现了机器可验证的防自批准。
- **发布前校验**：运行版的候选真实策略 SHA 必须匹配批准记录，运行代码 SHA 必须匹配批准记录；`status=FROZEN_APPROVED`、`live_delivery_approved=true` 只是必要条件，**绝非充分授权**；审批记录范围仅 MC live notification，不批准 Gmail 的新收件人/频率、资金和交易。旧 `355336f2…` 不能复用。
- **负向演练**：缺少签字、审批记录与政策 hash 错配、代码 commit 错配、未批准草案、自身 SHA 冒充带外批准、旧审批、过期签名、修改后策略都必须拒绝切换。正向演练只在**隔离私有副本**中使用模拟/测试签名，绝不认为测试签名是用户 live 授权。
- **切换与安全降级**：即使事后策略获批，仍需独立的部署/重启授权与回滚计划。回滚目标只能是“V1 保持 + MC 新决策通知停用/安全降级”或另一个经过审核且无旧 $30 默认金额的版本，不能复活旧策略。

**两阶段实际决定**：（A）现在允许 Claude 完成原有授权内的**短时隔离回放和假的请求计数**，不依赖真实批准记录；（B）仅在完成 PR112/PR119 集成、审查可信批准记录的实现方式之后，另行请用户批准真实策略文件哈希。未来机器验证器和审批流程**均未实施**，生产继续 NO_GO。

## 8. Mac 隔离回放补完范围（批准的测试，不含生产动作）

沿用 [原授权](https://github.com/lxxlx2/ChatGPT_mission_record/pull/126#issuecomment-6275981208) 和本地报告的 30 分钟快照，不再次等待自然新信号，不重复此前七项 A–G 矩阵。仅在临时可写副本中模拟 `prior BUY→WAIT`、`WAIT→WAIT`、新鲜 ACC/MULT、过期候选，两个摘要切换顺序，以及 V1 保持而 MC 禁用投递的回滚路径。对 `MissionMemeService._quote`、`OutcomeTracker.sample_due` 及实际底层 Jupiter/RPC 入口分层计数：假对象允许记录被调用次数但不得实际网络访问，报告必须标注伪造候选与真实快照各自覆盖度。对 15 条旧 `MANUAL_REVIEW` 只做跨演练前后不变性/不会重发的核验。

须提供每个场景**真实执行的输出/断言**，明确失败与因安全限制跳过的步骤。若缺项仍 `PARTIAL`，不要为获取 PASS 扩展到真实 Gmail、macOS 提醒、安装/切换或生产数据写入。

