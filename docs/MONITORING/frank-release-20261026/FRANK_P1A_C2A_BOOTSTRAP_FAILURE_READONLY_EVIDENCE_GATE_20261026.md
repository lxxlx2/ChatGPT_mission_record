# Frank C2A — 首次 launchctl bootstrap 失败后的只读取证门禁（2026-10-26）

**状态：`PLAN_ONLY / C2A_ROLLED_BACK / NEW_RELEASE_NOT_AUTHORIZED / FORENSIC_MAC_READ_NOT_AUTHORIZED / NO_BOOTSTRAP_RETRY / NO_CA_RPC`**

## A. 为什么需要本门禁

正式一次 C2A 用户授权 #6403908654 已由 Mac 执行者使用完毕。其实际回执 [Issue #165 #6403966947](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6403966947) 报告：

- G0：在运行原始 Dashboard `914e9e47fed2e60bc24690fcb083413a64d4e681` 的 446 Git 文件、manifest、唯一 loopback 8766、Loop/V1 服务与既有 Oct25 D2 JSON 身份上 PASS。
- G1：新候选来自已通过独立代码审核的 `4fdf2238a4db2347975689913e49142b760dc091`，**448 个** Git 文件，完整只读构件 normalized manifest SHA256 `709f00730dc4913080415bca936fd43428339976a9477fd1e65f2d36afc806ca`；-I -B import-only 和不联网的导入审计通过。这不代表可启动服务。
- G2：**恰好一次**新版 runner 的可逆 LOCAL_AGENT 替换，Dashboard-only `bootout` 成功、首次 `bootstrap` 失败；执行器未保存这一失败的**退出码/stderr**，因此 `ROOT_CAUSE_UNRESOLVED`。这既不是已证明的产品代码问题，也不是已证明的签名/权限/时序问题。
- G3：新版 production GET/Chrome **NOT_STARTED**，未验收新版。
- 随即仅 Dashboard-only 执行一次原字节 runner 恢复和恢复启动；原版本 `914e9e47...` / 446 文件验证、`GET /api/runtime` 和 `GET /static/app.js` HTTP200；原 Loop PID36070、V1 PID80447、通知计数与 Oct25 D2 JSON 文件哈希 `a1c3fcce95a8271baf585e30ea7348424eb4799cb2a26d513a142270253890d0` 均按 Mac 执行记录保持不变；回滚后 Dashboard PID35919。**这些 PID 只对应当时观察。**
- 授权已使用、rollback success。未重试新版启动。不能把 CLI 进程非零退出当作“确定的 launchd 故障原因”，更不能把备份存在当作第二次回滚测试。

以上为**已公开的 Mac 执行者回执，经 GitHub 读取核对**，本计划不声称另行直接观察原本的失败现场。

## B. F0：单次旧证据只读查证（未来须另获明确授权）

为了避免再次无证据地付出一次生产重启，下一步先只寻找**现有历史证据**，不做任何启动尝试；用户尚未授予此项 Mac 访问许可。

允许的 Mac 本地操作 **仅在用户明确单独批准后**：

1. G0：再次读 GitHub 固定 SHA 和回滚后实际 Dashboard PID/start/argv/cwd、唯一 127.0.0.1:8766 listener、旧 446 source manifest/runner/plist hash，确认 Loop/V1/D2 与原策略仍保持应有状态；不以历史 PID 当现值。检查已知私有恢复证据目录及新 448 文件候选构件**只读元数据**（stat、路径所有者/权限、父目录可穿越性、code-sign 信息如当前方法可只读获得）。**不要重新生成构件或重写 runner。**
2. 锁定真实事件时间：**2026-10-25T22:02:54.442330Z 至 22:02:55.949600Z**，曼谷 2026-10-26 05:02:54–05:02:55；最多扩到 UTC **22:02:45–22:03:10** 的统一日志与**已存在**的 Dashboard launchd 标准输出/错误日志，以 label 与已知进程身份过滤，只读提取与这次首次 bootstrap 相关的系统诊断。不得扩大到整日/全盘搜索或读取密钥环境变量。
3. 独立核查当时执行器已保存的安全私有报告/状态证据中是否包含原版 runner 以及**bootstrap 返回码、stderr、所执行的 launchctl 命令结构**。原回执明确没有保存返回码/stderr；如找不到必须保留 `BOOTSTRAP_RC_STDERR_MISSING`，禁止猜测或以 rollback bootstrap 的成功输出代替第一次失败。
4. 对可能存在的 launchd/unified log 行只在本地进行时间、service label、来源/错误码关联；区分 `BOOTSTRAP_SUBMISSION_FAILED`（launchctl 调用失败）、`SERVICE_SPAWN_FAILED`（launchd 允许注册却服务无法启动）、`HEALTH_CHECK_OR_LISTENER_FAILED`（启动但未通过健康门禁）。不能从一个非零返回就断言是哪一类。仅当真实日志有直接同一时刻/label 的证据才提升为 `ROOT_CAUSE_EVIDENCED`；否则保留 `ROOT_CAUSE_UNRESOLVED`。
5. **只读**比对新版候选是否对启动环境引入不可见的差异：Git exec mode 和物理 0444/0555、目录 0555、所在路径 ACL/quarantine/签名和父目录访问性、候选是否改变入口或依赖的导入，仅作核对；严禁 chmod、xattr -d、签名修改、启动源模块、编译写磁盘或在已有服务内导入未安装代码。审查该候选与成功安装 446 文件版本已存在的两个入口文件差异，优先证明/否定具体启动前置条件而非猜测。
6. 输出一份**脱敏证据对照表**：证据原始时间、来源、是否与本次首次 bootstrap 直接对应、进程/服务是否实际创建（需要证据，不作假设）、错误类别（支持/否定/未知）、可能的最小修复（`HYPOTHESIS_ONLY`），仍需要哪一份证据。无需确保找到根因；没有证据时结论是 `F0_READONLY_UNRESOLVED`，而不是建议立即重启再次试错。
7. 只将摘要（SHA、固定文件计数、脱敏状态、时间、证据文件散列、允许公开的错误分类）发布 Issue #165，并 GitHub API 读回；**不上传**未经脱敏的统一日志、完整 private path、argv、进程 env、plist 里的 secret、RPC key、钱包、Mint 明细、系统用户信息、浏览器数据、完整 JSON/SQLite。

**绝对禁止：** 新的 `launchctl bootstrap/bootout/kickstart`、重新安装、新 runner 替换、执行/试运行 candidate 服务、访问 CA POST、新 RPC、生产新写入、任何数据库修改、启动新 HTTP 监听器、Loop/V1 操作、运行常驻监控/定时任务、合并 PR、通知邮件/交易。**不进行真实重现失败**；没有首次 stderr 就没有事后可恢复的首次 stderr。若只读日志不可得，保留证据缺口并停止，不增加范围。

## C. F1：日后独立决策的“证据完整”再次发布，不是本授权

只有在 F0 完成、有具体根因/风险证据和对应最小修复后，再起草**独立固定 SHA、单次用户授权**的 Dashboard-only 发布复审。所有候选代码如需要改动必须由独立代码审核覆盖，不能沿用旧 PR205 的固定 SHA 批准冒充新修订。只有纯执行器的日志记录纠正、未改产品字节时，仍需单独的 Mac 只读或部署前演练批准。

为防止再次因证据丢失导致反复停服，任何新**获授权**的执行器应在改变 live runner 之前，使用私有 0600 / 用户独占目录预先确立原子、失败不丢失的 CLI 命令/返回码/stderr 记录机制；**首次失败时先持久化最小证据、再进行仅 Dashboard 受控回滚**，不可把记录错误替换为再次尝试启动。运行前用不接触 launchctl 的纯 fixture 模拟 `subprocess.run` returncode/stderr 两种状态并检查私有 fsync 和敏感字段脱敏策略，确保输出不会泄露其他本地环境。此项只适用于未来另行授权，不是立刻可执行命令。

## D. 当前关口 / 决策

| 事项 | 准确状态 |
|---|---|
| PR #205 `4fdf2238...` C1 源码 | 独立代码/离线测试 `APPROVE`；产品本身的启动故障 **未证明** |
| C2A 新版真实发布 | `FAILED_BOOTSTRAP`、新版生产 GET **NOT_STARTED** |
| C2A 回滚 | `C2A_DASHBOARD_ROLLED_BACK`，Mac 回执报告当前原 Dashboard 运行健康 |
| 第一次失败的退出码、stderr | `MISSING / NOT_RECOVERABLE_FROM_ORIGINAL_EXECUTOR_REPORT` |
| 根因 | `UNRESOLVED`，既不能归因权限也不能归因源代码 |
| F0 历史系统/现有日志只读检查 | `PLAN_ONLY / NEW_MAC_READ_AUTH_REQUIRED` |
| F1 二次切换、C2B CA Quick/任何 RPC | `NO_AUTHORIZATION`，失败后不要自动推进 |
| 受保护 Loop/V1、Oct25 D2、通知、交易 | 维持回滚回执所报告状态，未来执行前需再验证 |

此文件是基于 GitHub 回执的**文档方案**；其自身 SHA 永远不是产品代码 SHA 或用户生产授权。PR #205、PR #208 必须继续 Draft、不合并；Issue #165 继续 OPEN。
