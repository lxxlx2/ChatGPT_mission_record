# Frank 方案 3 / PR #157：只读 Dashboard 生产切换决策单（2026-10-22）

**决策：`P4_MAC_INTEGRATION_PASS / PRODUCT_READONLY_SCOPE_REVIEWED / RELEASE_PREPARATION_GO / PRODUCTION_INSTALL_NO_GO`。**

这是供用户审阅的**操作前决策文件**，不授权合并、安装、重启、发邮件、配置修改或交易。本文件所在的规划分支 SHA **不是**已审核的产品运行 SHA；原始审查、CI、Mac 验收仍仅针对以下指定版本。产品功能验收阶段已结项，禁止无新证据重复历史样本或截图测试。

## 1. 固定版本与已核实真实证据

| 证据 | 精确身份/结果 | 边界 |
|---|---|---|
| 方案 3 已获用户选择 | 保留原始 Frank ACCUMULATION/MULTIPLE 提醒；增加金额无关的分析/风险观察 | **不是**新通知及安装的授权 |
| PR #146 产品依赖 | `72cf75c61fdb220a01b98df0abe81ebc5d248fd4`；OPEN/Draft、未合并 | PR #157 依赖此功能，不能漏装 |
| PR #157 集成产品 SHA | `31dd598df248ca15f731913a5cbf82e88b981874`；OPEN/Draft、未合并 | 审核与验收只绑定此 SHA |
| PR #157 CI | Actions [39412845883](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39412845883) SUCCESS，81 focused tests；独立 Claude fixed-SHA code APPROVE、47 tested | 不是全部 local-agent 回归或生产安装验证 |
| Mac 实验环境 | QA source `7d4143d0233758cfb3776d5f35b86e53e9eb749e`，只相对产品增加隔离脚本+workflow | 隔离端口 18766、非 8766 正式安装 |
| Mac 实测 | `PRE_FLIGHT PASS` + `PR157_STAGED_PRODUCT_GET_AND_UI_SMOKE: PASS`；4 组 pytest 47 PASS，node check PASS；真实浏览器默认卖出、筛选、CA 查询/复制通过 | 只在 Mac in-app browser 实测 |
| 快照统计 | 最新索引交易 100 唯一签名、43 Mint、当前候选 Mint 7；BUY 类 40、SELL 类 60，仓位未知卖出 23，候选外卖出 40 | `LOCAL_INDEX_ONLY`，不能代表全链、实时余额或收益 |
| 隔离事实 | `PRODUCTION_MODIFICATIONS=0`、`REAL_NOTIFICATIONS_SENT=0`；测试 PID 60545 已停止，端口 18766 关闭；老生产 8766 PID 35963 前后不变 | 只证明该次测试，不构成将来生产状态保证 |

原始完整报告：[Mac 验收记录](https://github.com/lxxlx2/ChatGPT_mission_record/blob/b4571e589034bc555e5bd6be245e1fcc0eae2e2d/docs/MONITORING/evidence/frank-pr157-mac-20261022/REPORT.md)。正式 PR 验收评论：[issuecomment-6335175946](https://github.com/lxxlx2/ChatGPT_mission_record/pull/157#issuecomment-6335175946)。证据 commit `b4571e589034bc555e5bd6be245e1fcc0eae2e2d` 只增加脱敏报告/截图/checksums，不是新的产品 SHA。

## 2. 需要严格区分的两个上线目标

### 2A. 本次**已完成研发和 Mac 隔离验收**的只读产品

- 原始 `/api/frank-intelligence`：只读候选智能分析，缺价格/余额则明示未知。
- 新 `/api/frank-activity-watch`：读取本地最近最多 100 条已有索引交易，原候选集合之外的卖出也可见。
- 中文 Dashboard、15 条紧凑列表、筛选/CA 搜索、复制、签名证据链接。
- 不新增 RPC、交易、默认金额、策略 V1 改动或任何实际通知投递；原 V1 独立提醒保持原有来源和通道。

**这只是一项 Dashboard/产品功能上线候选**，不是“方案 3 包含的新智能风险**通知**已经交付上线”的证明。历史假的 SELL 预览既没有被授权投递，也没有获得与先前真实 V1 通知关联的全链证据。

### 2B. 未来真正的新增智能风险通知

仍需要独立的消息样例、事实/新鲜度/去重/渠道边界、签名/策略和授权；不得将只读观察里的 `SELL` 直接转为本地/Gmail LIVE 风险提醒。若引用“此前已提醒买入”，必须另证信号生成与**真实投递**，不可仅凭同 mint 或旧交易轮次。

2026-10-20 Mac 单独有界调查：过去 60 天原 V1 新信号 5 条、按严格同轮次后续 SELL 有证据关联 0 条；不能为增加提醒而放宽。策略收益与可跟单性 `NEED_MORE_DATA`，不影响只读产品验收。

## 3. 版本链 / 发布包要求

PR 叠加关系（均未合并）：
`release/frank-no-default-amount-policy-review-20261020` → **PR #146** `72cf75c6...` → **PR #157** `31dd598d...`。

未来需要以唯一可复现的集成产品 SHA/文件清单审查装载来源：不能只取 #157 的 7 文件而忽略 #146；也不能把叠加分支全部自动合并主分支。若 merge/squash/cherry-pick 改变**真实最终安装 SHA**，需重新核对完整 diff、审核状态及发布文件 hash；现有 APPROVE 不自动迁移至未知改动。

不能把证据分支 commit `b4571...` 或本文档提交 SHA 当作获准安装的新程序版本。

## 4. 已找到的真正生产切换阻断项

仓库现有 `crypto-300-profit-mission/local-agent/scripts/install_mission_meme_launchd.sh` **不是 Dashboard-only 更新器**：

- 明确要求 `CONFIRM_MISSION_LOOP_RESTART=1`、外部策略 SHA、可信签名 manifest 等。
- 会改写/安装运行策略与 Runner，并对 **MC Loop 和 Dashboard 两个 LaunchAgent** 执行 `bootout/bootstrap/kickstart`。
- 不能以“这次只是只读页面”为理由执行该完整安装器；它会碰到未授权的投递 Loop/签名策略和旧队列。
- 已有旧政策候选 `docs/MONITORING/frank-release-20261020/unsigned-live-policy-candidate.json` 明确标为 `SUPERSEDED_FOR_OPTION_3 / DO_NOT_SIGN`；不得为了安装网页而启用/签署它。
- 当前生产根目录、Dashboard runner、Loop runner、plist、PID、实际安装代码/策略 SHA 与端口必须在**真正执行前**于 Mac 只读复核。2026-10-22 历史 PID 35963 等不等于将来恒定 PID。
- **目前尚未有一次证明独立 Dashboard-only 更新/原版本回滚有效的真实 Mac 隔离演练和固定流程**。不能先重启再想如何恢复。

**因此：`RELEASE_MECHANISM_BLOCKED`，与 `PRODUCT_MAC_PASS` 并不矛盾。**

## 5. 下一阶段合理且有界的准备任务（不需运行生产变更）

1. **生产只读审计**：在经用户允许的 Mac 仅读当前 `8766`、launchd `com.jerson.frank-meme.dashboard` / `com.jerson.frank-meme.loop`、V1 进程、runner 路径和依赖、不可变 release 目录、健康/快照新鲜度、待发/不确定旧消息计数；不导出秘钥或完整私有 DB。确认其运行 code/policy 与审批版本的关系。
2. **最小只读 Dashboard-only 发布机制设计/隔离演练**：提供固定源 SHA、完整代码依赖文件 manifest 和 hashes，使用新独立目录做镜像及真实静态/API 检查；未授权时**不得**改正式 runner、plist、符号链接、端口或 PID。建议保留 MC Loop 与 V1 原进程完全不动。必须确认部署依赖不会偷改 Loop 行为或通知状态。
3. **预备回退证据**：记录现用 Dashboard 的可恢复 package/runner/进程来源；排查是否存在仅 Dashboard 的安全切换及回切方式。仅在隔离环境模拟切换和故障，不写正式目录。不允许回滚到含被否决默认 $30 的旧 LIVE MC 策略，不补发旧 Pending/Retry 队列。
4. **审核**：以上发布机制及其失败处理必须由独立 AI 按固定新 SHA、真实文件差异审查；若发布过程需要新的代码或生产行为变更，这些没有包含在已审核 PR157 产品代码里，必须独立验证。
5. **切换审批单**：只在完成 1–4 后，把“受影响服务、实际目标代码 SHA 与包 hash、允许的单次 Dashboard 重启/预计中断窗口、备份和失败动作、验收及回滚条件”提交用户单独审批；**任何此前“授权 Mac 隔离验收”均不包含本操作**。

## 6. 真正上线时的操作门禁（**只是未来条件，不是操作命令**）

- 双重用户独立批准：明确代码/只读功能范围以及具体 Dashboard 运行变更时间、操作者、回退边界。新 MC/Gmail 风险投递与策略签名需要另外单独授权；本次不申请。
- 启动前记录全套旧 Dashboard 状态、独立保留旧版本、检查 V1 信号原发送/来源是否保持、确保 MC Loop 不被重启，明确旧 outbox 不因切换而释放。
- 只切已批准 Dashboard 构件，重启范围限制到唯一确定身份的 Dashboard 进程；过程观察非预期端口、Loop/V1 PID 或 outbox 变化立刻停止并报告。
- 上线后核对 `8766` 原 `/api/runtime`、`/api/candidates`、`/api/trades`、`/api/frank-intelligence` 与新 `/api/frank-activity-watch`；检查本地索引口径、真实时间戳、用户页面搜索/复制及 15/100 条明示，读取健康和错误日志。**不发真实邮件作为“测试”**，不产生测试交易。
- 新 Dashboard 无法启动、错误展示数据时：在身份和版本均可核对的前提下**仅回切到原 Dashboard 构件**，不得连带重启旧投递 Loop；回切条件不满足即 `ROLLBACK_UNVERIFIED / NO_UNCONTROLLED_RESTART`，人工处理。真实服务恢复要有进程、端口和健康的读回证据。
- 验收分离：`PRODUCT_READONLY_PRODUCTION_PASS` 仅说明页面正确，绝非新风险实时通知 PASS，亦绝非跟单盈利 GO。

## 7. 本阶段停止规则

`P4_MAC_INTEGRATION_PASS` 已结案。**停止**重复同一来源历史样本、反复拼装截图和 P3 不影响使用的 EXIT 文案微调。下一步只填补 Dashboard-only 安全发布路径这一真实生产工程缺口；不因缺真实跟单收益而阻止只读页面的发布准备，也不以界面功能通过绕过用户生产授权。

下一阶段准备结论：**`GO_PREPARE_DASHBOARD_ONLY_MECHANISM`；当前执行结论仍为 `NO_GO_DEPLOY`。**
