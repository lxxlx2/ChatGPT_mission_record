# Frank C2A F1c — Dashboard-only 发布门禁状态机：纯合成验收（不是执行器）

日期：2026-10-26（Asia/Bangkok）

**`CODE_OFFLINE_ONLY / PLAN_FOR_REAL_EXECUTOR / NO_LAUNCHCTL / NO_DEPLOY / NO_RESTART / NO_CA_POST / NO_RPC / NO_NOTIFICATIONS / NO_TRADES / NO_MERGE`**

## 历史事实与冻结版本

- [Issue #165](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165) 已记录一次真实 C2A Dashboard-only 发布在首个新版 `launchctl bootstrap` 返回非零后仅重启 Dashboard 回滚旧版，`C2A_DASHBOARD_ROLLED_BACK`。随后 F0 历史日志取证未找回原始 CLI returncode/stdout/stderr，故 `ROOT_CAUSE_UNRESOLVED`。**不要猜测是 launchd 竞态、签名或源码问题**。
- 旧 Dashboard 上一次真实 Mac 验证来源 `914e9e47fed2e60bc24690fcb083413a64d4e681`；原始已审 C1 代码 `4fdf2238a4db2347975689913e49142b760dc091` [PR #205](https://github.com/lxxlx2/ChatGPT_mission_record/pull/205)，仍**未成功部署**。
- F1 离线证据保存模块独立 `APPROVE` 的 SHA `0fd028ee443e677f07d968679e159a817b02e378`，[PR #212](https://github.com/lxxlx2/ChatGPT_mission_record/pull/212)。F1b 仅离线恢复 spy 独立 `APPROVE` 的 SHA `9c74df6ef6ad6748f6f957813f7de9fb6495dfde`，[PR #214](https://github.com/lxxlx2/ChatGPT_mission_record/pull/214)。F1b P3 `return in finally` 警告保持原批准 SHA 不改；本 F1c 不为此扩展旧模块。
- F1c 从 **F1b 已审 SHA** 新起独立分支，绝不修改 PR205 正式产品代码或 Mac 文件。旧 C2A、F0 单次生产/只读 Mac 授权都已使用完毕。

## 交付内容与能证明什么

新增 `scripts/frank_c2a_f1c_offline_supervisor.py`。它**只有数据类、比较函数和 `rehearse_release` 纯合成流程**，**没有真实 subprocess.Popen/run、launchctl、HTTP、Mac 安装、服务或网络操作**。唯一可能的本地文件写入，是对 *调用方提供的测试专用 0700 证据目录* 调用既有 F1 记录器，把**合成的**失败 `CompletedProcess` 保存为 0600 测试证据；不可传入生产目录/旧恢复证据或在生产上调用。

- G0：模拟旧来源固定 SHA、旧 manifest/runner 指纹、sole loopback `127.0.0.1:8766`、Dashboard 健康与 Loop/V1/D2/通知/其他监听指纹齐全。缺失/漂移 → `FIXTURE_BLOCKED_NO_CHANGE`，不模拟任何切换。
- G1：模拟 448 文件候选 manifest 已验、解释器只导入已验、Dashboard runner 唯一来源行可逆；这些都是**fixture 提供的 bool**，模块不能替代真实 Git 文件逐条校验、macOS 签名/目录/venv 路径检查。
- G2：模拟切换前二次旧状态一致性、一次 `bootout` 结果与一次 `bootstrap` 已有结果；**不执行任何命令**。从 bootout 尝试开始，状态可能改变，故任何失败/异常都必须安排一次独立模拟恢复，不能只因为错误是非零就声称生产已停/已启。
- F1/F1b：仅当模拟 bootstrap 返回非零整数时，使用已经审核过的私有 F1 证据保存，且证据失败**不阻断 F1b 单次恢复 spy**。未采集 stderr/stdout、超时、异常不得伪造成功证据或 returncode。模拟恢复后必须以旧 SHA、旧 manifest、旧 runner、原 8766、完整 Loop/V1/D2/通知/其它监听指纹校验，**非字面 True/异常不能冒充完成回滚**。
- G3：即使模拟 `bootstrap` 返回 0，若目标来源/manifest/runner 不匹配、Dashboard 无健康证明、旧 Frank GET/D2 GET/Chrome 只读界面任一标注失败、受保护指纹漂移，也**模拟回滚**。此次不伪造 bootstrap 错误日志：`NO_BOOTSTRAP_RESULT` 表示后置验收失败没有新的失败 bootstrap 结果，**不代表没有历史启动事件**。
- G4：模拟关闭前复核受保护指纹一致，全部通过才得到 **`FIXTURE_RELEASE_PASS`**。此标签**不是** `C2A_DASHBOARD_CODE_ONLY_RELEASE_PASS`、真实浏览器/GET PASS、恢复保证或生产授权。

对应 `tests/test_frank_c2a_f1c_offline_supervisor.py` 的矩阵覆盖预检漂移、候选未就绪、二次校验失效、bootout/bootstrap 返回异常、stderr 未采集、TimeoutExpired、G3 HTTP/Chrome 或来源/受保护身份变化、一次恢复失败、一次恢复后旧来源身份/通知/D2 校验失败、成功条件及完全禁止 subprocess 创建。全量 CI 组合 F1 24 项、F1b 29 项与 F1c 新测试。**通过只能证明传入数据下代码判定与模拟回调顺序，不证明系统真实事实。**

## 生产集成仍缺少的硬条件（不能省略）

1. **没有真正的 F1c 生产 launcher 或 rollback adapter。** 后续必须独立实现和评审不可复用外部权限的 Dashboard-only 命令执行、精确 plist/runner/immutable manifest、签名/策略及对受保护 Loop/V1 的隔离，并单独申请用户生产授权。不得把 `Fixture` 中的布尔量和指纹视为来自真实 API 的凭据。
2. **真实 stdout/stderr 的有界读取尚未实现。** `CompletedProcess` 合成数据并不保证真实 child 的内存限额。未来应确保子进程启动超时、pipes/EOF/partial output、退出码和命令证据在有限内存中可记录；stderr 仍可能包含密钥，F1 的 base64 不是脱敏。
3. **异常与崩溃边界。** Python 捕获异常/finally 无法在 SIGKILL、失电或 kernel crash 下保证回滚。生产要有可恢复的、精确旧 runner 原字节备份和离线恢复手册；没有独立的守护者就不能宣称 crash-safe。
4. **真实控制面身份。** 旧产物 446 文件，新候选 448 文件，版本 SHA/文件模式与 manifest 必须实际在 Mac 验证；固定 Dashboard label、PID/start/cwd/argv/127.0.0.1:8766/D2 哈希/通知计数、Loop/V1 运行身份必须做到 *切换前和切换后* 均可证明，环境变量、launchd plist 以及安装源不可漂移。
5. **真实 G3。** 只读 GET 和 Chrome 需要明确合法本地白名单与超时，不能自动触发 CA POST/RPC。未知/部分结果视为失败并回滚；不能把合成 PASS 当真实业务结果。
6. **失败停机与权限。** 真实回滚失败时只报告 `RECOVERY_INCOMPLETE` 并 STOP，不自动切换其它服务、重试 launchctl 或恢复旧策略发送队列。需要独立用户许可才可在 Mac 上试一次真实切换。不能借此开启 C2B Quick/Standard/Deep 或交易/通知。

**状态：`F1C_OFFLINE_CODE_CANDIDATE / INDEPENDENT_REVIEW_PENDING / PROD_UNCHANGED / NO_NEW_MAC_AUTH / C2B_NOT_AUTHORIZED`**。本轮不修改旧版业务产品源码，不合并任何 Draft PR，不运行 Mac、生产 HTTP/RPC、CA POST、真实 release 或 cron。原 Issue #165 继续 OPEN。
