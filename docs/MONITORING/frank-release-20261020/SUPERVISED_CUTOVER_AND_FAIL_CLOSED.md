# Frank Mac 发布 / 安全退出操作设计（**仅纸面方案，不执行**）

2026-10-20，`OPTION_3_SELECTED / PRODUCTION_NO_GO`。用户已选择保留原始买入提醒、开发新的无默认金额智能分析与风险提醒，见 [新的功能开发计划](./FRANK_AMOUNT_INDEPENDENT_INTELLIGENCE_PLAN.md)。旧的无金额 WAIT-only 技术候选不满足已选目标：`SUPERSEDED_FOR_OPTION_3 / DO_NOT_SIGN`。与 [RELEASE_DECISION_SHEET.md](./RELEASE_DECISION_SHEET.md) 同属 Draft 审阅资料。**不得把这份文件视为用户授权、安装脚本或完成的现场恢复演练。**

## 0. 目前确切事实

- 代码最后一个独立审查修复 SHA 为 PR #139 `938fd5cae3aea7d5a1931fa89f2e7999aaa8cbcd`，来源联合代码 PR #138 `a34d64c7661175742928bcea7652991640796998`。本审阅分支的文档提交会形成**不同的新 HEAD**；只有在最终实际 checkout SHA 固定以后，才能填写正式签名清单。
- 2026-10-20 05:58 +07 只读：生产 Loop 36070、Dashboard 35963、V1 52300；安装旧策略 SHA 前缀 `355336f2`。不是当前状态的持续保证。
- 当前仓库运行配置 `config/follow_policy_v1.approved.json` 仍为 `REVIEW_ONLY/false`。置于 `docs/` 的旧技术候选虽然包含 `FROZEN_APPROVED/true`，但现在**已被方案 3 淘汰为发布对象，不得签署/安装**；仅保存历史审阅字节与证据。新分析功能完成后另出真正满足目标的策略字节与 SHA。
- 经代码验证的 `mc_loop_only_safe_stop.py` 是 **Loop-only STOP**，不是 Loop live-delivery toggle。需要真实 Mac 授权后才可 `--apply`；成功必须回读 launchd absent 及原 PID 不存在，否则 UNKNOWN，绝不算停机成功。

## 1. 用户批准前：只读 / 离线准备

1. **用户已选择 A3（方案 3）**，无需再询问 A1/A2。先按 P1–P4 建立能够独立使用的金额无关信息分析：Frank 原始信号保留，增量风险提示必须有数据依据；新通知先在假通道演练。当前代码不能在没金额时产生可执行 BUY/SMALL_BUY，不能拿旧 WAIT-only 候选冒充新功能。
2. 完成新功能及独立审查以后，再根据**新策略实际完整字节**计算 SHA-256，供用户独立审核；旧 `c1e8d9822bb6a95e744e56d0d71092cef86b102771b0433a38f7eb30882ee013` 只用于识别历史技术候选，**不得签署为方案 3 正式版本**。签名清单的 `integration_sha` 必须与最终实际安装 checkout HEAD 一致（merge/squash 后重新核对），`quote_usdc_amount` 必须不存在。
3. 用户在仓库外、AI 无法写入的可信设备/渠道自己持有 RSA 私钥。使用个人确定的 `approved_by`、带时区起止时间，填写模板（`schema_version=1`, `scope=FRANK_MC_DECISION_LOCAL_AND_GMAIL_ONLY`, `deployment_approved=false`），对整个 manifest 原始字节签名。用户/管理员独立将对应公钥部署到根保护 trust anchor 路径。未布置/不匹配/过期 → **不安装**；GitHub 评论、shell 中自算 candidate SHA、AI 写文件都不是签名。
4. 在 Mac **只读**重看真实 Loop + Dashboard + V1 PID、plist Label/ProgramArguments、真实 runner、installed policy SHA、队列状态数量和健康记录（只做受控快照，不导出凭据）；旧 `355336f2...` 若仍为活动策略，确认没有与新策略混用。
5. 使用隔离 worktree、独立临时 HOME、SQLite backup API 的一致性副本、假 Gmail/本地 utility/RPC/Jupiter/launchctl 完成最小停机-异常与通知恢复 mock 演练（已有代码模拟曾通过；生产实际 restart 仍 NOT_TESTED）。禁止在未获授权时用完整 installer 试运行“验证”，因为它会修改状态/重启服务。
6. 两份授权记录必须分开：**策略 SHA/通知范围授权** 和 **安装/Loop+Dashboard 重启的时间与操作者授权**。记载每份记录的不可替换证据；不得在策略审批 manifest 中将 `deployment_approved` 改为 true。

## 2. 仅在未来另行批准后：全量监督式切换路径

此段是**待审批步骤**, 当前不得执行。

1. 操作者重新检查两份用户批准、源 Git HEAD、工作区干净、实际候选文件 SHA、签名验签结果和策略字段；固定实际生产计划的时间及操作人。
2. 备份生产策略、LaunchAgent、Loop/Dashboard 状态和生产控制库为**可回读的一致性副本**，确认 V1 source 数据与邮件 outbox 单独备份/不变。保护隐私，备份只能作为证据，不自动恢复不兼容历史可发送队列。
3. 检查服务启动器的真实输入文件与安装根目录。当前 `scripts/install_mission_meme_launchd.sh` 是**重装 Loop + Dashboard**的脚本，调用 Gmail `ready` 预检；其正常执行会改写 Application Support，含 `bootout/bootstrap/kickstart`，**绝不可当作只读验证命令**。
4. 已授权执行时，只有同时满足外部 RSA 签名、候选 policy_sha256、实际 integrated code SHA、签署有效期、另行确认 restart 及预检全部通过才可进行 install。真实 restart 可能造成 Dashboard 暂时不可用；V1 源服务不在该 installer 定义的 Loop+Dashboard 操作范围内，仍需人工回读健康状态。
5. 新 Loop 启动后重新读 `ps` / `launchctl print` / 实际政策字节 SHA / health 与 outbox；确认其启动参数对应新代码和签名，D1/D2 仍标注数据时间，旧策略 pending/retry/uncertain 不被发出；本地和 Gmail **不得发送测试真消息**，只能使用签名/状态审计和假通道验证到正式启用为止。
6. 记录真实观察，才可按**实际上线是否成功**签收。没有真实运行证据不得标 `PRODUCTION_PASS`。

## 3. 异常与回退必须安全关闭，而不是恢复旧 $30

- **不回滚到旧 `355336f2...` 的 LIVE 策略**。该策略可能包含已被用户否定的隐式资金金额；其存在不能作为新的通知授权。
- 安全失败路径目标是：**V1 源监控维持 + MC 评估/决策投递停止或明确不可发送**，Dashboard 尽可能继续可读。旧历史通知不得“恢复队列并补发”。
- 未来由用户**另外批准真实 MC-only stop** 时，使用经过审查的工具先验证正确 Loop plist 与 PID，再只作用于该 Loop；需要 `launchctl print` 返回服务不在、旧 PID 不在。任一结果 UNKNOWN/PARTIAL（如 disable 成功而 bootout 失败），都必须立即人工读回并报告，**不能擅自 kill、强启旧版本或重启 Dashboard/V1**。
- 如果全量 installer 在写入部分文件后失败，不能仅凭“失败退出”假定已经回滚；必须把实际运行配置、策略 SHA、runner 参数和服务进程逐项核实。**当前没有经真实 Mac 测试证明的自动恢复流程**。
- 如果签署有效期在运行中到期，送信 guard 已验证关闭，但 MC loop 的非投递评估仍可能继续；这不等于生产服务进程停止。

## 4. 验收与范围

`CODE_APPROVE` (#138/#139) + `MAC_LAYOUT_READONLY_MATCH` ≠ `REAL_STOP_TESTED` ≠ `NEW_POLICY_USER_APPROVED` ≠ `INSTALL_AND_RESTART_APPROVED`。

当前状态：`OPTION_3_PRODUCT_PLAN_ACTIVE / NEW_INTELLIGENCE_FEATURE_NOT_IMPLEMENTED / OLD_UNSIGNED_CANDIDATE_SUPERSEDED / FINAL_CODE_AND_POLICY_SHA_PENDING / OWNER_SIGNING_PENDING / ACTUAL_STOP_AND_RESUME_UNVERIFIED / PRODUCTION_NO_GO`。任何真实 `sudo`、launchctl 改动、签名密钥创建、Gmail 系统发送、RPC/Jupiter 或交易，均不在本次用户“只准备”的授权范围内。
