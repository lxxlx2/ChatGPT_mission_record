# Frank D2 — R2 最终 BLOCKED 后的 Dashboard-only 发布风险决策（2026-10-24）

**本文件是新的代码/证据审查与发布决策，不是 R2 PASS、实际发布授权或生产变更。**

## A. 固定证据与可信性边界

- **产品候选 SHA**：`914e9e47fed2e60bc24690fcb083413a64d4e681`（`research/frank-d2-private-child-port-stable-20261024`）。原产品 PR #178 Draft HEAD `ea9a7715beb4d2a55ae956bf993828cbddcb50e5` 仍与其不同；原版 reader 指向 shared root，不可拿原 PR HEAD 替代这个私有子目录候选。
- **当前已安装 Dashboard SHA**：`656ed2c96f4210d106d7b1129ec6cf8d7c4586f3`（PR #168，已有 437 文件原位 manifest 和专用单服务可逆切换报告）。正式监听 **127.0.0.1:8766**，不能加端口/监听器。
- **R1 通过**：全 446 个候选文件与 Git 源完全匹配；完整规范化 manifest SHA256 `9a06f5f29fce05ccade8caa2b90d6d6c0c4248d2e6ab4e45aa26fa9d3f401062`；Mac Python3.14.7 使用实际 venv、`-B` import-only 通过，固定私有子目录绑定一致。R1 是2026-10-24 已保存的 Mac 报告；协调器没有直接访问 Mac 复测。
- **D2 实际私有数据导入已完成**：[Mac 导入 PASS](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6382863583)，独立 GitHub 读回 [#6382892169](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6382892169)。原 shared root `0755`、私有 child `0700`、唯一 JSON `0600`、893189 bytes、SHA256 `d24d73d13a5ab9740eed7d1f06a6226aa9650004ccd756458b579c9e2ee2e284`。该 JSON 仅代表2026-10-23 14:46:32.787921 UTC（曼谷21:46）的**两个非同槽 finalized 历史观察**（SPL slot460482174／Token2022 slot460482176）；4148 Mints，3275非零，42页（41×100+48）；绝非当前资产、美元估值或 PnL。
- **既有源代码审查/离线测试**：上一轮固定生产代码 blob 的55 Python＋6 JS Mac 合成测试通过，文档 P2 修复独立批准。现存 `test_frank_d2_ingress.py` 检查来源权限/哈希/失败关闭、同槽含义、分页/零 vs 不存在；`test_frank_d2_http_route.py` 使用原始 Handler 的无 socket 状态模拟检查请求头/Host/参数/返回；`test_frank_d2_ingress_ui.mjs` 使用原始 JS 的 VM 合成上下文检查仅手动 GET、数字精度、竞态及缺失来源。**这些不是一次真实浏览器端到端通过。**
- **最后授权的一次实际 R2**：[Mac 执行结果 #6385584653](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6385584653)，证据 commit [`8d2bf3b40a0dc081f0b846f500d6a326ec4a9115`](https://github.com/lxxlx2/ChatGPT_mission_record/commit/8d2bf3b40a0dc081f0b846f500d6a326ec4a9115)。Gate P 首个不满足的测试是对**不存在**的越界 Unix socket 路径 `connect`，返回 `ENOENT`（预期策略拒绝 `EPERM`）。源码 `gate_p.py` 明确构造 `R.parent/(R.name+'-outside.sock')`，没有建立该路径的监听端点。故 **`BLOCKED_NETWORK_POLICY_NOT_PROVEN` 是真实的“证据门禁未过”，但测试设计使这个结论不能推断为已发生越权连接或安全策略失效**。其他八项IP/子进程检查没有执行，Chrome启动0，页面0，真实生产GET0。按首失败停止的授权约束执行正确。
- **被独立保存的旧 R2** 同样无 browser 成功，原因是 `(deny network*)` 拒绝 Chrome ProcessSingleton AF_UNIX bind；之前 Chromium Mac `MAC_CHROMIUM_TMPDIR` 修正只是候选环境方案。本轮虽将变量透传至 Python 探针，Chrome 未启动，仍未证明实际 ProcessSingleton。
- **被报告保持不变**：Dashboard、MC Loop、V1、runner/plist、已有8766及其它未知监听、私有JSON字节/权限、无新增 RPC/HTTP/通知/交易/部署/合并。

## B. 真正的改动与功能风险

Git diff 从已安装 PR168 到候选914e9e47包含43个叠加提交/17个文件；运行关联实际重点是`server.py`、`static/app.js`、`static/index.html`、`wallet_d2_ingress.py`、`wallet_owner_at_slot.py`五个文件。原 CLI、通用安装器、CSS、Loop/V1 信号与通知策略保持原源码不变。

- `wallet_d2_ingress.py` **固定子目录读取**，检验 `0755/0700/0600`、owner、O_NOFOLLOW/文件身份、来源格式/校验和、每页100条、精确Mint，失败返回 UNKNOWN/REJECTED 而非伪造零；无文件写入、RPC、SQLite、通知和交易。需要注意该 SHA 下读取器没有普遍的 Git 边界/所有祖先 symlink 保护承诺，operator 预检是必要补充。
- `server.py`复用现有 Dashboard 127.0.0.1:8766，新增 `GET /api/frank-d2-at-slot`；需自定义 `X-Frank-D2-Read:1`、Host loopback 与 Origin/Sec-Fetch-Site 限制（有时这些字段不存在）。这属于 **同源浏览器防护，不是针对同机其它进程的身份认证**；任何具有本机回环访问能力且可自设请求头的进程仍可能查询最多100条/次的历史Mint信息。该行为必须在仅本机可信使用场景下明确接受，**不得将8766绑定到公网/0.0.0.0**。
- `index.html/app.js` D2 面板只在显式点击后读取，页面说明两个 finalized slot 非原子/非实时；无定时自动RPC/POST。旧CA、Frank观察池的 JS逻辑未通过新 Chrome 实机回归，但既有旧版本及源差异已检查。
- **残余不可消除的未测行为**：真实 Chrome 页面初始化是否受新DOM/脚本影响；真实同源 header/cookie/请求路由、真实 handler & private JSON GET 和响应UI；JavaScript 与旧 Frank CA控件的实际集成；发版后页面加载失败如何直观恢复。R1 import-only 不能替代完整 `DashboardState` 初始化或实际服务 HTTP 验收。
- `G03B_INTERPRETER_ORIGIN=UNRESOLVED` 是已记录的发布资格限制，不被 R1/D2 离线结果自动消除。

## C. 发布选项与明确建议

**结论：`NO_UNCONDITIONAL_GO`。默认保持 PR168 不动；可以选择 `CONDITIONAL_DASHBOARD_ONLY_CUTOVER_CANDIDATE`，但必须把 R2 真实浏览器覆盖缺失作为显式风险豁免并取得用户对**单次生产切换及短暂8766中断**的独立批准。**

|选项|得益|风险与代价|决策|
|---|---|---|---|
|A. 严格 NO-GO，保留当前 PR168|生产无需变动/最低操作风险|D2 历史数据已在磁盘但页面无法使用；真实浏览器缺口继续悬而未决|用户不接受任何 R2 覆盖豁免时选 A|
|B. **受控 Dashboard-only 条件发布**|能让已导入的历史 D2 数据用于本地人工核查；只影响 Dashboard|**未知真实 Chrome/生产 GET 集成行为**；需要真正的服务中断、上线后读取和明确的失败回滚|**推荐候选**，只在用户显式接受这个未测风险并另批发布时执行；此前不可操作|
|C. 继续无限制 Chrome 沙箱调试|有机会补齐离线真Chrome证据|已连续多次环境阻断且没有业务验证、消耗开发精力，并偏离 Frank P1 核心目标|**不推荐，不再自动授权/排期**|

**B 不等同于历史 `R2_PASS`，绝不能悄然把 `R2_NOT_TESTED` 改成成功。** 这是一个用户有意识接受剩余界面风险的“有限制先交付+能回滚”发布选择，而不是技术证明补齐。没有用户对 B 的授权，当前状态仍然是 NO-GO。

## D. 若未来用户明确选择 B：精确的单次上线与回滚门禁（本文件绝不授权执行）

1. **先核实已安装真实 Mac 当前态**，不要用历史 PID：Dashboard/Loop/V1 的 PID+启动时间/runner/plist/source/manifests、仅 127.0.0.1:8766 服务入口；私有源原路径、0755/0700/0600、893189字节及SHA完全不变；候选914e9e47和446文件 manifest复验。失败即 `CUTOVER_BLOCKED_NO_CHANGE`。不重新导入、不新RPC。
2. **在有独立明确 user consent 后**，保留旧 PR168完整只读 release及其manifest和用户私有离线 rollback bundle，验证仅能替换现有 Dashboard runner 中的 **一行 `LOCAL_AGENT`**，其它字节/环境变量/端口/策略/plist不变；本地 rollback 必须精确可逆。禁止使用同时重启 Loop+Dashboard 的通用 `install_mission_meme_launchd.sh`。
3. 仅在用户批准一次短暂8766中断后，更换 Dashboard-only immutable新版本/runner，然后仅对其既有 `com.jerson.frank-meme.dashboard` label做所需短时 restart。**不改变**Frank V1、MC Loop、其它8765/48721等真实存在但未证明可关的监听；不创建第二HTTP服务、后台定时任务或新端口。
4. **仅已授权的本机只读验收（不是旧R2 PASS）：**9个原有 GET 回归+静态HTML/JS/CSS hash匹配；新 D2 GET `X-Frank-D2-Read:1`，验证page0=100/page41=48、状态只标明Oct23历史、两个slot、Mint观察到零 vs不存在分开、不包含真实 Token Account pubkeys；实际 Chrome 在本机现有正式8766仅进行 GET/人工读取/分页，无 CA POST、新RPC、未知域流量；不上传真实响应/地址。
5. **先设 STOP/ROLLBACK 条件**：当前8766不再唯一回环监听、启动import失败/manifest不一致、任一原9 GET故障或旧CA操作不可用、D2新GET不正确/私有数据校验失败、真实Chrome出现页面严重错误或不准确的实时资产表述、V1/Loop identity/通知策略或计数变化、源文件意外改变、发现新增写入/外网调用/监听或无法独立恢复旧runner → 立即进行**仅Dashboard**原runner+PR168不可变构件恢复，再做回滚后只读检查。原 `frank-d2-private` 数据目录与JSON必须保留，不删除也不重复导入。
6. 成功只可记 `PRODUCTION_D2_DASHBOARD_PASS_WITH_EXPLICIT_R2_WAIVER`，且必须记录真实GET/浏览器测试实际通过哪些场景；未测仍标未测。失败记录 `PRODUCTION_D2_DASHBOARD_FAIL_ROLLED_BACK` 或 `CUTOVER_BLOCKED_NO_CHANGE`，若回滚无法证实则标 `RECOVERY_INCOMPLETE`。无源代码自动修改、无PR合并。
7. 后续 **Frank P1 当前持仓与 CA Deep问题继续 OPEN**：上线 D2 历史余额面板并不等于完整/当前钱包核实，亦不代表CA分析请求失败已修复。继续按无默认买入金额、原提醒保留的功能目标推进。

**本评估没有在 Mac 启动 Chrome、获取生产数据、变更端口、部署、合并、修改服务或创建定时任务。**

`R1_PASS / D2_HISTORICAL_IMPORT_PASS / R2_NOT_TESTED / GATE_P_PROOF_FLAW_IDENTIFIED / CONDITIONAL_GO_CANDIDATE_ONLY / CURRENT_PROD_UNCHANGED / OWNER_PROD_RELEASE_APPROVAL_REQUIRED / ISSUE165_CORE_P1_OPEN`。
