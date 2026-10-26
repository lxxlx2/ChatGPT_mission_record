# Frank C2A F1 — 失败证据先持久化、再模拟回滚（离线候选）

日期：2026-10-26（Asia/Bangkok）

**本轮仅代码／离线 fixture：`NO_MAC_PRODUCTION / NO_LAUNCHCTL / NO_DEPLOY / NO_RESTART / NO_RPC / NO_CA_POST / NO_TRADES / NO_MERGE`。**

## 证据来源、任务范围

- [Issue #165 F0 实际只读取证 #6404091375](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6404091375) 已证明：首次新版 Dashboard `bootstrap` 返回非零，但原操作器没有保留 returncode/stdout/stderr；只有两条不能唯一解释失败的 launchd 生命周期日志。**根因仍是 `F0_READONLY_UNRESOLVED`。**
- 上次 C2A 真实生产切换失败并成功回滚（[Mac 回执 #6403966947](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6403966947)），当前按 Mac 报告旧版 `914e9e47fed2e60bc24690fcb083413a64d4e681` 运行，Loop/V1/D2 未改变。旧 C2A 和 F0 单次授权均已消费。
- [PR #210](https://github.com/lxxlx2/ChatGPT_mission_record/pull/210) 文档只读阶段已经完结，没有发现足以证明代码、签名、权限或时序错误的直接证据。**本 F1 不主动修复启动错误，不重新取证、不再次运行新版。**
- C1 业务代码仍以 [PR #205](https://github.com/lxxlx2/ChatGPT_mission_record/pull/205) 固定 `4fdf2238a4db2347975689913e49142b760dc091` 独立离线审核为准；本 F1 分支不是发布产物，也不修改 PR205 产品源码。

## F1 离线工程交付

1. `crypto-300-profit-mission/local-agent/scripts/frank_c2a_f1_evidence.py`：**只接受外部注入的 `subprocess.CompletedProcess`**，模块自身绝不调用 `subprocess.run/Popen`、`launchctl`、服务、网络或 CA。内置唯一允许的 `DASHBOARD_BOOTSTRAP` 事件类型。只在失败返回码（非零整数）时写证据。**不记录原始 argv**，避免记录 plist 私有绝对路径、敏感 CLI 参数；只记录固定命令类别、UTC 时间、退出码及两路输出。
2. stdout/stderr 最多各保留首 **8192 bytes** 的原始 bytes，以 base64 编码保存至**本机私有证据文件**；记录每路完整输出的 byte 长度、SHA256、是否截断。**不代表超过截断长度时保留了全部正文。** 证据文件中可能有敏感值，绝不可上传 Git/日志，公示只能给哈希、长度、类别、固定 SHA 和脱敏片段。
3. 证据目录必须事先存在，owner 为当前用户且 mode **0700**，最终证据文件 mode **0600**；拒绝 symlink 证据根和已存在的记录。通过目录 fd 与 `O_NOFOLLOW/O_EXCL` 创建临时文件，文件 `fsync` 后原子 no-replace 链接成最终单次记录，目录 `fsync` 并 readback 字节比较之后，才允许离线模拟回滚回调。任何持久化错误触发明确异常，不能记为保存 PASS。
4. `tests/test_frank_c2a_f1_evidence.py` 使用临时 0700 目录和**假的 CompletedProcess**、模拟 callback，测试：有 stderr/空 stdout、精确失败退出码、fsync 在回调之前、磁盘同步失败、拒绝覆盖/符号链接、拒绝不安全权限、输出边界截断、成功时无错误记录/无回滚、非 UTC/无效返回码、全局 subprocess.run 被封禁仍可离线运行。
5. `.github/workflows/frank-c2a-f1-offline-evidence.yml` 只安装 pytest 并运行本测试。CI 是 GitHub 合成环境，**不是用户 Mac、真实 launchctl、生产 bootstrap 或真实启动失败重现。**

## 必须独立复审的安全与可用性条件

- 重点检查在真实 Apple APFS/macOS Python3.14 语义下 `dir_fd/O_NOFOLLOW/os.link/fsync` 的可用性和证据持久性：Linux CI 通过不能证明所有 macOS 文件系统和平台边界。**可先代码审核，之后如确需 Mac 离线测试，另行取得明确 Mac 沙箱授权**，不得擅自拿用户的“继续”作为 Mac 访问许可。
- `checkpoint_then_simulate_rollback` **只是测试辅助入口**，回调必须是无副作用 spy。它现在若遇到 `EVIDENCE_PERSIST_FAILED` 会阻止回调，**不能直接套用到生产**：真实未来已授权的发布器，即使无法保存证据，也应有独立的、最小的紧急 Dashboard-only 恢复安全路径和明确 `EVIDENCE_CAPTURE_FAILED` 状态，不得因此放任生产停机。
- 测试用的是已返回的合成 `CompletedProcess`；还**没有保证**真实 `subprocess.run` 被信号中止/超时/kill 时会返回可捕捉的对象，也不保证已丢失的原 stderr 可恢复。未来发布前须设计并离线审查 try/finally、TimeoutExpired、进程被中断与退出码缺失分支。
- 测试已验证 raw `args` 不写入记录，但 captured stdout/stderr 仍**可能包含 RPC URL/凭据/私有路径**。因此严格只在受保护 0600 私有文件内部保存，脱敏总结独立处理，**不得原样粘贴到 Issue/PR**。
- `CAPTURE_LIMIT` 是“证据大小/隐私界限”，不是 launchctl 输出本身的内存上限。若实际运行器的 `capture_output=True` 对无界输出没有外部限制，则还需要单独的 I/O 上限设计。此轮不触碰生产执行器。
- 不能仅凭错误证据模块的离线 PASS 将 `F1_RELEASE_READY`、`C2A_PASS`、`C2B_QUICK_AUTHORIZED` 或 `ROOT_CAUSE_EVIDENCED` 写入 GitHub。

## 后续门禁

**当前状态：`F1_OFFLINE_CODE_CANDIDATE / INDEPENDENT_REVIEW_PENDING / MAC_PROD_UNCHANGED / C2A_RELEASE_NOT_AUTHORIZED / C2B_NOT_AUTHORIZED`。**

仅在新固定 SHA 的本增量独立代码审核（P0/P1/P2）与具体失败注入测试通过后，才可另行设计整合到单独发布执行器的 F1b，并测试“任何日志保存故障下仍优先受控回滚”。最终新一次 Dashboard-only 发布、服务短暂重启、任何 CA POST 或真实 RPC 均需要**新的单次显式用户授权**。保留原 PR205 业务代码 SHA 不变，Issue #165 继续 OPEN。
