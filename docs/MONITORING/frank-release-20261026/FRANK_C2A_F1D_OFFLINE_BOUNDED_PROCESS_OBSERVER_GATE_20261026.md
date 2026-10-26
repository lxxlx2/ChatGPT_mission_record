# Frank F1d — 有界子进程输出与退出事件的纯离线观察契约

2026-10-26 (Asia/Bangkok)

**状态：`F1D_SYNTHETIC_CODE_ONLY / NO_MAC / NO_LAUNCHCTL / NO_DEPLOY / NO_RESTART / NO_REAL_RPC / NO_CA_POST / NO_MERGE / NO_NOTIFICATIONS / NO_TRADES`**

## 目的与不可误认的事实

用户曾单次授权 Mac C2A Dashboard-only 发布，新的 `launchctl bootstrap` 非零退出；后续一次授权回滚使旧版 Dashboard 恢复。实际失败的退出码、stdout/stderr 未被原始执行器保存，F0 历史只读查询仅见不可唯一归因的 launchd 生命周期事件，**故故障根因仍为 `UNRESOLVED`**。[Issue #165](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165)

已独立批准的离线组件：F1 [PR #212](https://github.com/lxxlx2/ChatGPT_mission_record/pull/212) `0fd028ee443e677f07d968679e159a817b02e378`，F1b [PR #214](https://github.com/lxxlx2/ChatGPT_mission_record/pull/214) `9c74df6ef6ad6748f6f957813f7de9fb6495dfde`，F1c [PR #215](https://github.com/lxxlx2/ChatGPT_mission_record/pull/215) `dd1035ca29c1d3c4e778325a9d5fd67ed3ed95f3`。F1c 的 G4 独立 `protected_after_g3` 快照与合成状态机已经获得新 SHA 的独立审核通过，**仍然不是实际 OS 观测、真实启动或恢复执行器**。F1d 新分支从该完整固定 HEAD 出发，不修改上述已审核源文件，也不修改 Dashboard 或 PR205 的 CA 业务代码。

## 交付：只有合成输入的 F1d 输出观察器

新增 `scripts/frank_c2a_f1d_offline_process_observer.py`，接受仅由离线测试生成的 `PipeData`、`PipeEOF`、`ChildExit`、`DeadlineReached` 与 `Interrupted` 事件。模块不运行子进程、shell、launchctl、网络、浏览器、生产接口或钱包 RPC；**没有可绑定到生产服务的 CLI entrypoint**。

- 固定最大单事件字节量 **4096 B**；两路 stdout/stderr 各最多保留 **8192 B**；最多解析 **256** 条事件，定义合成时间截止 **30000 ms**。
- `PipeEOF` 和 `ChildExit` 必须同时齐备，才可能得到 `COMPLETE_FAILURE` 或 `COMPLETE_SUCCESS`。缺少任何 EOF、退出码、延迟、合成中断、事件不合法/顺序倒退、超出大小或事件数，均独立输出错误状态，不将缺失信息视为实际空串。
- 原始缓冲区虽然会保留已观察的合成字节，但允许转为 F1 `CompletedProcess` 的条件**严格限于** `COMPLETE_FAILURE`（两个 EOF、已知非零整数 returncode、未截断）；不能拿只保存的前缀伪造完整 stdout/stderr 的长度或 SHA。正常退出码 0 不能转为失败证据。
- `safe_status` 只输出固定阶段、状态、是否知道退出码、EOF、事件计数和合成耗时，不含私有路径、原始 argv、原始输出或 bytes 数据。本模块不把敏感 stdout/stderr 上传 GitHub；**返回的原始 Observed 本身不可公开**。
- 可在隔离 fixture 中用 `to_f1_failed_result` 把完整失败事件交给已批准 F1，然后用已批准 F1b **无副作用**的恢复 spy 复验顺序。对不完整输出，测试只能传入 `None` 做合成 F1b 恢复，并同时保留 F1d 独立的 `INCOMPLETE_*`、`STREAM_BUDGET_EXCEEDED`、`DEADLINE_REACHED` 等状态，不能将它记成取得完整 CLI 证据。

## 安全限制与生产集成缺口

1. **有界的是消费合成事件后内部保留的字节数，不是实际子进程 stdout/stderr 的进程级内存上限！** 测试代码已事先创建 `bytes` 输入；外部事件生成器如果卡住不会被此模型的合成时间戳强制终止。未来生产 pipe 读取器必须另行设计有界 `read`、真实单调时钟、子进程/进程组停止与 reap、避免 deadlock、部分 EOF、超时和信号中断处理。任何声称“真实 launchctl 有界”的话目前都不成立。
2. F1 的私有 0600 文件可保存前 8192 字节原始错误内容；base64 是编码，不是脱敏或加密。不能将 `Observed`、`CompletedProcess`、F1 私有路径或完整异常消息公开。
3. 若真实执行超过上限，不能仅把被截断的数据交给 F1 生成看起来完整的 digest/byte count；需要未来单独的、明确 `PARTIAL/TRUNCATED` 标记证据格式与对应审核。暂时只能拒绝转为 F1 完整证据。
4. 本 F1d 没有真实 launchd 调用的命令允许清单、受保护 Loop/V1 身份验证、真实旧版 runner 原字节备份、immutable release 构建、部署事务、实际 Dashboard 8766 只读 GET、Chrome、G4 现场复核或物理应急恢复路径。不可向其注入真实 `launchctl` callback 并当成生产发布器。
5. `F1c` 的 G0-G4 是合成状态机；F1d 只是对**命令结果是否有资格被当成完整证据**的独立前置环节。此次不接入真实执行器，也不扩大先前单次 Mac 授权。
6. 未来若要做到真实生产安全切换，必须另行评审固化 Mac 机器/用户/label 身份、受保护服务的完全隔离、可验证回滚、输出/超时/无故障抑制的恢复机制，并在真实操作前获得新的、严格单次的用户授权。SIGKILL/断电仍不受本模型保证。

## 独立复审门禁

请审查新固定 SHA 相对 F1c 已批准 SHA 的实际增量、事件时序、对空字节/缺失 EOF/退出码/负值信号/超时/超大 chunks/事件预算等反例，验证**被截断前缀不能用于 F1 完整证据**，以及合成结果是否会泄露私有字节。离线运行 F1、F1b、F1c、F1d 的 CI；不能用 GitHub CI 代替独立 Mac fixture 检查，也不能把离线 PASS 算为生产发布 PASS。

**`F1D_CODE_CANDIDATE / INDEPENDENT_REVIEW_PENDING / F1C_APPROVED / ROOT_CAUSE_UNRESOLVED / C2B_NOT_AUTHORIZED`**。Issue #165 继续 OPEN，所有 PR 保持 Draft，不合并、不部署、不重启、不调用 RPC 或 CA POST。
