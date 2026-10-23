# Frank D2 独立私有目录与端口固定方案 — 2026-10-24

## 授权与状态

用户确认推进 D2 独立私有子目录设计，同时要求尽量只用必要端口，不要反复调整。本分支仅为**代码候选、合成测试与独立复核准备**，从 PR #178 固定 SHA `ea9a7715beb4d2a55ae956bf993828cbddcb50e5` 创建，未修改原 PR HEAD。

**当前状态：CODE_ONLY_UNTESTED / INDEPENDENT_REVIEW_PENDING / PROD_UNCHANGED。** 本文件不是 Mac 验收证据，未授权生产修改、导入、部署、合并、重启、新 RPC、通知或交易。

## 固定数据位置

- 已有 Frank 共享 `control_root` 继续保持 `0755`，不得为了 D2 对它执行 `chmod`。
- D2 唯一读取目标：`control_root/frank-d2-private/frank-d2-owner-at-slot.json`。
- 新子目录 `frank-d2-private` 需由同一 owner 创建并为 `0700`；新文件 `0600`，独占创建、防止软链接和覆盖。读写均拒绝 Git/worktree、非目标来源。
- 旧版 `control_root/frank-d2-owner-at-slot.json` 不回退读取；文件不存在意味着 **SOURCE_NOT_IMPORTED/UNKNOWN**，不代表余额为零。
- 只有在**后续单独明确授权**后，才可创建生产子目录和执行一次冻结历史来源导入。既有旧导入许可已经结束，不可沿用。
- 原始 PR178 `frank_d2_export_ingress.py` 仍接受显式 `--output`；本分支不改 exporter，不访问真实私有余额或 RPC。用户授权的新路径须由执行合同明确指定并再次验证。

## 端口治理：少、固定、复用

用户新增的强制约束：**生产业务能共用端口就共用，不为了新功能再开端口，更不能频繁换端口。**

1. D2 继续作为**现有 Frank Dashboard** 的 GET 子路由 `/api/frank-d2-at-slot`，以后需要独立部署授权；唯一目标为目前 Mac 正式 Dashboard 的 **127.0.0.1:8766**。
2. D2 不得创建第二 HTTP 服务、第二端口、额外 LaunchAgent、轮询服务或新后台进程；不修改 Dashboard runner、`dashboard_port`、plist、8766 或其他现有服务配置。
3. `mission_meme_v1.py` 源码中的 `8765` 是参数默认值，不证明当前监听此端口；曾使用的随机高端口可能属于已结束的隔离测试，**不能直接认定它们仍被占用**。
4. 本分支单元测试调用原始 reader、`query_d2`、内存 `Handler.do_GET`，**不绑定任何 socket，不创建新端口**。将来真实浏览器隔离测试仅在确有必要时使用临时端口，并严格清理，不保留后台监听。
5. 对 Mac 当前“端口很多”的真实占用状况，需要**另行只读**枚举 LISTEN socket → PID/启动时间/进程/launchd 服务；区分监听与出站连接、历史截图/日志与目前状态。只形成脱敏表、明确必要/冗余/未知；**不得**直接 kill/停用、移动或合并任何尚未核实的服务，Loop/V1 和 Monster/地址分析模块不受 D2 改动影响。
6. 对其他模块的端口整合必须评估生命周期、地址空间、职责和安全边界，不能为了数字上只剩 1 个端口就合并不相关进程。

## 代码与测试验收

变更范围：`wallet_d2_ingress.py` 固定子目录路径 + 两个相关合成测试文件 + 本设计记录。按既有仓库测试规范执行定向 Python unittest 和无 socket 的 HTTP handler 用例，再做独立 review。至少确认：

- 共享父目录 `0755` + D2 子目录 `0700` + D2 文件 `0600` 正常查询，不改变共享父目录；
- 共享目录组/其他人可写、软链接；子目录 `0755` 或软链接；文件 `0644` 或软链接；旧根目录同名文件不被回退读取；缺源、异常数据均 fail closed；
- 原始源 schema、观察时间、两个 finalized slot、零余额/无账户语义、100 条分页、GET-only/同源限制均保持不变；
- 原始 exporter 的 `O_EXCL` / `0700` / `0600` / 非 Git 限制不回退；不能编造当前持仓或把历史快照当实时；
- 实际测试记录必须来自 Mac/CI 真正执行，不得把本分支的“编写测试”写成“测试通过”。

**下一关**：执行隔离离线测试和独立源码复核 → 如通过，另外请求生产新子目录和单次历史文件导入的授权 → 更后面如需要 Dashboard 展示则单独授权 Dashboard-only 切换。

严格遵守：`NO_NEW_LISTENER / NO_NEW_PORT / KEEP_8766 / NO_DEPLOY / NO_MERGE / NO_RESTART / NO_NEW_RPC / NO_TRADES / NO_NOTIFICATIONS`。
