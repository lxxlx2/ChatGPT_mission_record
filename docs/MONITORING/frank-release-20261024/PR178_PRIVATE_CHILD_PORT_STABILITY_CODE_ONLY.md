# Frank D2 独立私有目录与端口固定方案 — 2026-10-24

## 授权与状态

用户确认推进 D2 独立私有子目录设计，同时要求尽量只用必要端口，不要反复调整。本分支仅为**代码候选、合成测试与独立复核准备**，从 PR #178 固定 SHA `ea9a7715beb4d2a55ae956bf993828cbddcb50e5` 创建，未修改原 PR HEAD。

**验证记录：** 2026-10-24 代码候选 `06cb3597c70a68ee8b3ba91b74fcfa98cc08a828` 已由 Mac 执行 4 个 Python unittest 模块 **55/55 PASS**、D2 UI JavaScript **6/6 PASS**，均未新开监听端口；独立审核指出本文原有读/写 Git 边界表述不准确（P2，REQUEST_CHANGES）。本次后续提交仅修正文档承诺，**尚未获得对新 SHA 的增量独立 APPROVE**，不以原始 61 项通过替代新提交验收。**PROD_UNCHANGED**。未授权生产修改、导入、部署、合并、重启、新 RPC、通知或交易。证据：[PR #178 审核评论](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6377036902)。

## 固定数据位置

- 已有 Frank 共享 `control_root` 继续保持 `0755`，不得为了 D2 对它执行 `chmod`。
- D2 唯一读取目标：`control_root/frank-d2-private/frank-d2-owner-at-slot.json`。
- 新子目录 `frank-d2-private` 需由同一 owner 创建并为 `0700`；新文件 `0600`，独占创建、防止软链接和覆盖。
- **Git/worktree 防护按职责划分：** 原始 `frank_d2_export_ingress.py` 通过 `_private_create` 在**写入时拒绝任何 Git 仓库及 linked worktree 目标**；正式导入前置核查须再次确认目标共享目录及私有子目录均不处于 Git/worktree 内，禁止通过其他手段绕过 exporter。**`read_d2_source` 当前不运行 Git 检测**，仅针对固定子目录/文件执行权限、类型、owner、末级 symlink、文件身份及 JSON 验证，不能把它说成读侧也拒绝 Git。实际合成 Git 仓库中的合法模式、合法 schema 文件曾被 reader 接受，此行为已在审查证据中披露，不作为新发现的已部署安全漏洞。生产配置仍应保持 Git 外路径；以后若要把 Git 排除升级成 reader 的运行时保证，必须独立设计、测试并审核。
- 已知边界：本次 reader 对**共享根自身、子目录和源文件末级**的 symlink 拒绝有测试证据；对更上层路径中 symlink 别名的合成观察显示其可接受，不能声称“所有祖先 symlink 都已被 reader 拒绝”。生产路径的规范化及组件校验由单独的导入前置核查负责。
- 旧版 `control_root/frank-d2-owner-at-slot.json` 不回退读取；文件不存在意味着 **SOURCE_NOT_IMPORTED/UNKNOWN**，不代表余额为零。
- 只有在**后续单独明确授权**后，才可创建生产子目录和执行一次冻结历史来源导入。既有旧导入许可已经结束，不可沿用。
- 原始 PR178 `frank_d2_export_ingress.py` 仍接受显式 `--output`；本分支不改 exporter，不访问真实私有余额或 RPC。用户授权的新路径须由执行合同明确指定并再次验证。

## 端口治理：少、固定、复用

用户新增的强制约束：**生产业务能共用端口就共用，不为了新功能再开端口，更不能频繁换端口。**

1. D2 继续作为**现有 Frank Dashboard** 的 GET 子路由 `/api/frank-d2-at-slot`，以后需要独立部署授权；唯一目标为目前 Mac 正式 Dashboard 的 **127.0.0.1:8766**。
2. D2 不得创建第二 HTTP 服务、第二端口、额外 LaunchAgent、轮询服务或新后台进程；不修改 Dashboard runner、`dashboard_port`、plist、8766 或其他现有服务配置。
3. `mission_meme_v1.py` 源码中的 `8765` 确实是默认参数，**但 Mac 于 2026-10-24 06:45（曼谷时间）的实际 LISTEN 快照已证明另一个 `dashboard_server.py` 进程正在监听 127.0.0.1:8765**。其必要性尚未验证，所以保持不动；旧隔离测试随机端口未观察到监听，不得以历史日志推定仍在占用。
4. 本分支单元测试调用原始 reader、`query_d2`、内存 `Handler.do_GET`，**不绑定任何 socket，不创建新端口**。将来真实浏览器隔离测试仅在确有必要时使用临时端口，并严格清理，不保留后台监听。
5. **只读端口盘点已执行**：2026-10-24 06:45（曼谷时间）观察到 15 条 IPv4/IPv6 LISTEN 记录、**12 个不同 TCP 端口、8 个进程**；已证实冗余监听为 **0**。8766 属 Frank 正式 Dashboard；8765 属另一 Dashboard、48721 属用途尚未明确的 Python；其余涵盖系统服务、网易云音乐和开发工具。只有核实冗余及影响后才考虑另行申请清理，**不得**直接 kill/停用、移动或合并任何尚未核实的服务，Loop/V1 和 Monster/地址分析模块不受 D2 改动影响。证据：[只读盘点评论](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6377036902)。
6. 对其他模块的端口整合必须评估生命周期、地址空间、职责和安全边界，不能为了数字上只剩 1 个端口就合并不相关进程。

## 代码与测试验收

变更范围：`wallet_d2_ingress.py` 固定子目录路径 + 两个相关合成测试文件 + 本设计记录。按既有仓库测试规范执行定向 Python unittest 和无 socket 的 HTTP handler 用例，再做独立 review。至少确认：

- 共享父目录 `0755` + D2 子目录 `0700` + D2 文件 `0600` 正常查询，不改变共享父目录；
- 共享目录组/其他人可写、**共享根本身为 symlink**；子目录 `0755` 或 symlink；文件 `0644` 或 symlink；旧根目录同名文件不被回退读取；缺源、异常数据均 fail closed。更上层祖先 symlink **不属于已验证的 reader 拒绝行为**；
- 原始源 schema、观察时间、两个 finalized slot、零余额/无账户语义、100 条分页、GET-only/同源限制均保持不变；
- 原始 exporter 的 `O_EXCL` / `0700` / `0600` / 非 Git 限制不回退；不能编造当前持仓或把历史快照当实时；
- 实际测试记录必须来自 Mac/CI 真正执行，不得把本分支的“编写测试”写成“测试通过”。

**下一关**：针对本次**仅文档的修复提交**做独立差异复核、确认 P2 已关闭，必要时引用已通过的 55+6 项同代码版本测试作为背景证据；新 SHA 如继续复用原代码，应明确引用同一产品 blob 未变。通过后另行请求生产新子目录和单次历史文件导入授权；以后若需要 Dashboard 展示，再另行批准 Dashboard-only 切换。

严格遵守：`NO_NEW_LISTENER / NO_NEW_PORT / KEEP_8766 / NO_DEPLOY / NO_MERGE / NO_RESTART / NO_NEW_RPC / NO_TRADES / NO_NOTIFICATIONS`。
