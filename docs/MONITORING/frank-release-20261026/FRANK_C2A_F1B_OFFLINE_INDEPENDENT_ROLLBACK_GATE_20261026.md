# Frank C2A F1b — 启动失败与证据保存失败时的独立恢复模拟（代码/离线）

日期：2026-10-26（Asia/Bangkok）

**状态：`F1B_OFFLINE_SIMULATION_ONLY / NOT_REAL_RELEASE_EXECUTOR / NO_LAUNCHCTL / NO_DEPLOY / NO_RESTART / NO_CA_POST / NO_RPC / NO_TRADES / NO_MERGE`**

## 目标和范围

[Issue #165](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165) 中 C2A 首次真实发布的新版 `bootstrap` 失败；原 Dashboard 已回滚恢复，首次失败的 returncode/stderr 未保存。F0 只读取证记录 `F0_READONLY_UNRESOLVED`，并没有查明是权限、签名、代码还是启动时序问题。

独立审核已通过的 F1 [Draft PR #212 固定 HEAD `0fd028ee443e677f07d968679e159a817b02e378`](https://github.com/lxxlx2/ChatGPT_mission_record/pull/212) 实现私有文件 0600、目录 0700、原子无覆盖与 fsync/readback 的 **合成错误证据保存**。它有一个必须保留的限制：未采集 stderr/stdout、fsync 失败或者目录异常时，F1 的**模拟回调不会执行**，因此不能直接把该模拟回调当生产紧急回滚控制器。

本 F1b 分支严格从 F1 已批准的完整 SHA 建立独立代码增量，**不改变 F1 已批准代码**，不改变 C1 已批准 CA 业务代码 `4fdf2238a4db2347975689913e49142b760dc091`，不修改旧运行 Dashboard `914e9e47fed2e60bc24690fcb083413a64d4e681`。

## 已实现的离线恢复状态机

新增 `scripts/frank_c2a_f1b_offline_recovery.py`：

1. 输入必须是**已经提供**的模拟 `CompletedProcess`、`TimeoutExpired`、异常或缺失结果；模块自己 **不调用 subprocess、launchctl、网络客户端、Mac Dashboard、文件导入或生产 runner**。
2. 非零整数 returncode 的结果交由原 F1 `persist_failed_bootstrap` 尝试保存；不伪造丢失或超时场景的退出码。证据成功与失败有独立状态；raw stdout/stderr 不进入安全摘要。
3. 使用独立的恢复 **test spy**。即使 F1 拒绝 `None` 流、文件写入失败、fsync 失败、已有证据禁止覆盖、fixture 捕获到 KeyboardInterrupt/SystemExit，也尝试**一次**模拟恢复。证据保存异常不包含在对外摘要中。
4. 恢复 spy 返回后，必须另外运行校验 spy 并严格取得 `True` 才报告 `ROLLBACK_VERIFIED`。失败/抛错报告 `ROLLBACK_FAILED_STOP`；校验失败或异常报告 `ROLLBACK_UNVERIFIED_STOP`。禁止自动第二次恢复或把启动后的服务身份猜为健康。
5. 明确的 `CompletedProcess(returncode=0)` 不被处理为启动失败，不应无故触发回滚。本状态机**不处理**“成功 bootstrap 后后续运行时健康失败”，那属于未来另行评估的真实发布器 G3 门禁。

对应离线合成测试 `tests/test_frank_c2a_f1b_offline_recovery.py` 和 GitHub CI 一起运行已批准 F1 的 24 项测试与 F1b 的恢复逻辑。每个测试仅使用临时目录、合成返回对象与**无副作用**回调，不访问任何用户 Mac 生产目录、真实 launchctl 或 Solana RPC。

## 审核关注与部署硬门禁

- **当前模块不是可执行生产发布器，也没有 CLI entrypoint。** `restore_spy` 是受信任的 fixture，不是可以把真实 `launchctl` 注入后直接使用的生产接口。真实 C2A 需要严格固定唯一 Dashboard label、runner 源码字节、plists/签名、回滚备份、当前 PID/进程身份和其它服务安全边界，不能靠这个状态机直接保证。
- 捕获失败后继续尝试回滚只是 **可捕捉 Python 异常**与控制流中的证明，不等于对 SIGKILL、OS 重启、失电等有强制恢复保证。不要写“任何中断都保证回滚”，不要使用无限重试。
- 当前的调用方已经拿到 `CompletedProcess`，没有真实执行/监护外部进程的 I/O 限流器。未来必须独立设计 `TimeoutExpired`、无 returncode、stdout/stderr 全量内存占用、被中断进程组/子进程处理，并防止任何机密输出外传。
- 错误证据保存模块的 `CAPTURE_FAILED` 不等于完整丢失了所有本地痕迹：fsync 第二/第三阶段失败时最终私有文件**可能已存在但未证明持久化完成**。本状态机不会为了捕获证据覆盖它。不能以“记录存在”冒称成功，模拟回滚仍可进行。
- 未来恢复动作失败或者无法证明旧 Dashboard 在唯一 127.0.0.1:8766 恢复健康时，必须保持 STOP，不能继续 CA Quick/Standard/Deep，也不能重启 Loop/V1 或擅自发通知。
- `F1b` 整合为真实专用发布器前，需要**另行的代码设计、独立 SHA 复审、Mac 离线沙箱检查和用户明确的单次发布/重启授权**。本轮“继续”仅表示继续离线代码研发。
- [PR #205](https://github.com/lxxlx2/ChatGPT_mission_record/pull/205) 的 CA RPC 预算代码已经离线审核，**正式 Dashboard 仍运行旧版本**。C2B 真实 Quick/RPC、部署、通知、交易均无新的授权。

## 当前交付门禁

代码审核者应从新固定 HEAD 对比批准的 F1 `0fd028ee443e677f07d968679e159a817b02e378`，实际运行合成失败结果、证据 fsync 异常、证据缺失、恢复失败、恢复校验失败、异常和正常成功各路径；确认未添加任何可调用真实启动器或真实服务的逻辑。

**结果须严格分开：`OFFLINE_RECOVERY_FIXTURE_PASS`（可能）≠ `PRODUCTION_BOOTSTRAP_RECOVERABLE` ≠ `C2A_DEPLOYED`。**

`INDEPENDENT_F1B_REVIEW_PENDING / ISSUE165_OPEN / NO_MERGE`。
