# Frank 发布决策单（待用户审阅，**不构成授权**）

日期：2026-10-20。状态：`POLICY_PROPOSAL_UNSIGNED / NO_MERGE / NO_DEPLOY / PRODUCTION_NO_GO`。

## 1. 唯一当前候选与已验证来源

- 代码基线：已独立审查的 PR #138 `a34d64c7661175742928bcea7652991640796998` 与 PR #139 `938fd5cae3aea7d5a1931fa89f2e7999aaa8cbcd`。后者为当前**工程行为基线**，包含“停止后必须回读 PID”的修复。
- 本 Draft 分支只增加供用户审阅的候选和文档，因此最终 **Git HEAD 必须在本 Draft 所有文档提交后重新读取**。将来若 merge/squash/rebase/cherry-pick 修改了 HEAD，原 SHA 不再代表真实安装代码，必须以**最终实际 checkout HEAD**重填签名清单并重新签署；不可继承先前 SHA 的批准。PR #128/#132/#134/#138/#139 的审核固定 SHA 均不因这些文档被修改。
- 技术性 LIVE 策略候选：[`unsigned-live-policy-candidate.json`](./unsigned-live-policy-candidate.json)；原始 UTF-8 **完整文件字节 SHA-256**：`c1e8d9822bb6a95e744e56d0d71092cef86b102771b0433a38f7eb30882ee013`。**未签名、未批准、未安装**。
- 签名清单待用户填写的**无效占位模板**：[`owner-signature-manifest-TEMPLATE-DO-NOT-SIGN.json`](./owner-signature-manifest-TEMPLATE-DO-NOT-SIGN.json)。模板中的 `integration_sha`、签名人、时间、有效期是占位字段，当前不具备任何授权作用。
- 仓库原有运行配置 `config/follow_policy_v1.approved.json` **没有被替换**，依旧是 `REVIEW_ONLY / live_delivery_approved=false`；其文件名“approved”不等于用户授权。

重要解释：为使技术候选具有**未来可签署的确定字节**，该独立 docs 目录中的 JSON 含 `status=FROZEN_APPROVED`、`live_delivery_approved=true`。这是**应用代码要求的布尔门禁测试输入**，不是用户签字、部署许可，也不是仓库运行配置变更。仅有这些字段和候选 SHA 无法通过真实安装入口的可信 RSA 签名门禁；严禁将此文件自签或填入环境变量直接尝试安装。

## 2. 真正的通知/数据行为（不能宣传为已经实现了无金额买入建议）

| 事项 | 当前代码/候选的真实行为 |
| --- | --- |
| Frank V1 ACCUMULATION/MULTIPLE | **独立原始信号路径**，保留既有本地及 Gmail 规则；与新 MC 签名审批、报价金额和队列不同。 |
| MC `quote_usdc_amount` | **不存在**。用户自己决定何时交易、交易多少；不将金额、报价阈值或订单注入策略。 |
| MC 对候选请求 Jupiter 的 USDC→token 执行报价 | `_quote()` 见不到金额即返回 `USER_ORDER_AMOUNT_NOT_SPECIFIED`；不会因策略而访问 Jupiter 执行报价。历史 outcome exit quote 数量上限为 0。 |
| MC 决策 | 合格 Frank 模式也可能得到 `WAIT / EXECUTION_NOT_ASSESSED_USER_AMOUNT_MISSING`，而不是可执行的 `BUY/SMALL_BUY`。不把 `NOT_ASSESSED` 写成无流动性/不可买。 |
| MC 本地 / Gmail 发送 | 两通道在目前 MC 代码里一起入队；相同状态去重、初次信号年龄要求、`_transient_wait` 抑制未先前可执行 BUY 的暂态 WAIT。**不保证会给出新的可操作买入邮件/提醒**，不能把 V1 原始通知视为 MC 决策通知已恢复。 |
| 原始/历史数据 | 继续保留可核实的签名、活动、候选、D1 索引、注明采集日期的 D2 持仓；旧数据不应伪装为当前 NAV/PnL 或凭空补发历史通知。 |
| 老策略的待发送通知 | 联合代码使用来源策略 SHA 隔离、逐发送检查签名到期与消息年龄（初次通知最多 600 秒）；旧策略 PENDING/RETRY_PENDING/不确定发送不得在新策略下自动释放，保留人工核验回执。 |
| 交易和金额 | 无自动交易、无默认 `$30`、无钱包签名、无策略私钥、无强制建议用户仓位。 |

**当前候选的实际发布适配性提醒**：如果用户期待“不输入金额也要收到 MC 可执行 BUY/SMALL_BUY 实时建议”，当前逻辑做不到，不能以签署候选来掩盖这一缺口。要实现“金额无关的 Frank 情报通知”需要单独定义其信号、通道和内容，然后另行做产品设计/代码审核；可以直接依赖现有 V1 原始信号通知，而不伪装成 MC 已实现此功能。

## 3. 用户应单独做出的三个决定

**决定 A — 生产运行目标（目前未选择，不得默认替用户选择）**

- **A1：V1 信号优先、MC 实时决策通知暂不启用**。保留原始 ACCUMULATION/MULTIPLE 通知。是否停止旧 MC Loop（会同时停止新 MC 判断更新）由用户另行授权；不允许为了消除旧 `$30` 逻辑而偷偷执行 `launchctl`。
- **A2：允许现有无金额 MC 策略的 LOCAL + Gmail 两通道**。接受它主要产生观察/WAIT 和其他状态转换，不能等同有真实执行报价的 BUY；V1 保持原样。当前签名清单固定 scope 为 `FRANK_MC_DECISION_LOCAL_AND_GMAIL_ONLY`，**尚不支持“只本地”或“只 Gmail”的独立审批**。
- **A3：要求新的金额无关 MC 情报提醒**。先批准行为规格，再研发、测试、固定新的代码和策略 SHA。当前候选不得假装已经满足 A3。

**决定 B — 签名策略授权（A2 满足条件后，用户另行批准）**

用户自行控制独立 RSA 签名私钥，通过用户可信渠道完整核对 **真实策略字节 SHA-256 + 最终 Git SHA + 唯一 MC 通道范围 + `approved_at` / `expires_at` + `deployment_approved=false`**。用户本人签署整个 manifest 原始字节，不能让 AI/安装器生成私钥、代签、或从策略自动计算摘要伪造认可。验签公钥由用户/管理员自行布置在 `/Library/Application Support/FrankMeme/release-approval-public-key.pem`，文件和直接父目录 root 拥有、组/其他不可写、不可为符号链接。**当前没有布置任何真实公钥，也没有任何用户签名。**

**决定 C — Mac 生产操作（必须独立于 B，再批准）**

列明未来实际 Git HEAD、安装文件 SHA、需要的私有快照、时间窗口、受影响进程（全量 installer 将同时重启 Loop 和 Dashboard；V1 源进程应保持独立）、潜在短暂中断，以及故障处理和回退。**策略签名仅允许应用验证规则，不构成运行 `launchctl` / `CONFIRM_MISSION_LOOP_RESTART=1` 的许可**。

## 4. 当前生产事实与未完成条件

2026-10-20 05:58 +07 的 Claude **只读快照**：MC Loop PID 36070、Dashboard PID 35963、V1 源 PID 52300 均在运行；安装策略 SHA 前缀 `355336f2…`，属于更早的运行配置，**不是本次候选**。这些 PID 只作为当时证据，未来操作前必须重新读取。

PR #139 审查结论 `CODE_DELTA_APPROVE`，Mac `MAC_LAYOUT_READONLY_MATCH`，**不代表真实 Mac 已停机/重启**。PR #138 代码 APPROVE；其余 Draft 均未合并。本次仅保存 GitHub Review 资料，不触碰 macOS、密钥、网络、生产数据库或真实消息通道。

**当前下一道门禁**：先由用户选择 A1/A2/A3 并确认真实通知范围；如果选 A2，再固定安装 SHA、准备用户独立签名与操作清单；如果选 A1，用户另外授权 MC-only STOP 之前不要执行。全部保持 `PRODUCTION_NO_GO`。
