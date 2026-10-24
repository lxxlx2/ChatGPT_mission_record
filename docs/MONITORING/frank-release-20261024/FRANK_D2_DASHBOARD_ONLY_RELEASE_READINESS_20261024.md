# Frank D2 — Dashboard-only 上线准备与冻结发布决策单（2026-10-24）

## 状态与权限边界

**RELEASE_PLAN_READY / PREDEPLOY_BROWSER_AND_MAC_PREFLIGHT_PENDING / USER_DEPLOY_APPROVAL_NOT_GIVEN / PRODUCTION_UNCHANGED。**

这是用户“继续”要求下的 **代码只读审计和发布方案**，不是批准部署或执行。目标：将已经验收并保存在生产私有目录中的 **2026-10-23 历史 D2 Token/Mint 余额证据**，在既有 Frank Dashboard 的 **127.0.0.1:8766** 上以用户手动点击的方式显示。不要把历史观察当实时账户资产，不修改现有监控、提醒、投资金额或交易权限。

- 现有 Dashboard 真正运行的已核实版本：`656ed2c96f4210d106d7b1129ec6cf8d7c4586f3`（PR #168，Mac 安装版，437 个 Git 源文件）。
- 唯一代码候选：`914e9e47fed2e60bc24690fcb083413a64d4e681`（私有子目录 reader，D2 UI、服务端 GET）。此版本在独立研究分支固定；原 PR #178 `ea9a7715beb4d2a55ae956bf993828cbddcb50e5` **仍为 Draft、未合并、且其原 root-level reader 不可用于已成功导入的 private-child 路径**。
- 2026-10-24 Mac 数据导入执行和 GitHub 读回证据：[PR178 #6382863583](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6382863583)、[协调复核 #6382892169](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6382892169)；9/9 PASS。已保存在原有效 `control_root/frank-d2-private/frank-d2-owner-at-slot.json`；父目录 `0755`，子目录 `0700`，文件 `0600`。不重新导入、不覆盖、更不重新采集。
- 同一候选源中的 Mac 既有测试 55/55 Python + 6/6 JavaScript PASS，最后一个文档 P2 在 `914e9e47` 独立复核关闭；**这并不是新 Dashboard 在真实 Chrome 中的发布前端到端验收，更不是生产上线许可**。
- 历史批准过的 [PR168 Dashboard-only 实机发布](https://github.com/lxxlx2/ChatGPT_mission_record/pull/168#issuecomment-6362421248) 是发布方法的依据；该历史许可**不自动授权**本次发布。

## 真实运行差异，不能用“只有几行改动”掩盖发布范围

GitHub `compare 656ed2c96f4210d106d7b1129ec6cf8d7c4586f3...914e9e47fed2e60bc24690fcb083413a64d4e681` 已核实：**43 个堆叠提交、17 个受影响文件**（含研究脚本、测试、CI、文档），不是 17 个运行服务。

部署运行阶段影响的 5 个文件：
1. `crypto-300-profit-mission/local-agent/mission_agent/mission_control/server.py`：新增 /api/frank-d2-at-slot 手动 GET 路由、查询参数和同源限制。
2. `crypto-300-profit-mission/local-agent/mission_agent/mission_control/static/app.js`：手动 GET、时间/分页/精确 Mint、原始整数高精度渲染及竞态控制。
3. `crypto-300-profit-mission/local-agent/mission_agent/mission_control/static/index.html`：D2 历史证据面板。
4. `crypto-300-profit-mission/local-agent/mission_agent/mission_control/wallet_d2_ingress.py`：原 control root 之下固定的私有子目录、0700/0600/owner/格式校验，最多100行/GET。
5. `crypto-300-profit-mission/local-agent/mission_agent/mission_control/wallet_owner_at_slot.py`：纯离线数据/32-byte Mint 验证，无运行时 RPC。

原本的 `scripts/mission_meme_v1.py`、`scripts/install_mission_meme_launchd.sh`、`styles.css`、Frank Loop/V1 业务逻辑及通知策略的 Git blob 相对已安装 PR168 **不变**。新增的离线 exporter、研究工具、工作流、测试、文档 **不应作为单独运行进程**。即使要组装完整不可变候选 release tree，也必须按 Git 精确完整清单验证，不能宣称只是修改了5个源文件后仍是原 437-file manifest。

**严重发布边界**：`install_mission_meme_launchd.sh` 会 bootout/bootstrap/kickstart **Loop 与 Dashboard 两个 launchd job**，并要求生产策略签名批准，绝不能用于本次 Dashboard-only 目标。无论脚本 SHA 是否未变，都不代表可安全执行它。

## 发布前必须完成的两个准备门禁（无生产修改、无新常驻端口）

**R1 — 代码/依赖与固定构件审查：**
- 对比上述17文件及确切5个运行文件的 fixed Git blob；确认不是 root-level reader，源读取路径与已经导入的数据相符，`wallet_owner_at_slot.py` 不依赖 PR60 研究端依赖或在线调用。
- 在 Mac 独立不可写于原主工作区的临时 checkout 中，使用**已有** Python venv 和 `-B` 做 server/reader/入口模块 import-only 验证；只在内存中构建 synthetic `DashboardState` 或通过 fake state 的直接 `Handler.do_GET`，不要启动服务，禁止写生产 SQLite；若 import 需要构造真实状态则仅允许受控合成状态。
- 以固定 SHA 制作候选完整 local-agent 只读构件、生成排序 filename→SHA256 manifest、校验 100% 文件内容和可执行位，**不得覆盖现有正式 release**。保留固定候选 Git SHA 及 manifest SHA；任何不一致立即 STOP。
- 核验当前正式 runner/loop/V1 进程真实身份和受保护的 D2 文件 metadata：`0755/0700/0600`、893189 bytes、SHA256 `d24d73d13a5ab9740eed7d1f06a6226aa9650004ccd756458b579c9e2ee2e284`；**只 hash**，不得上传内容、再次运行 exporter 或读原始回执。

**R2 — 离线、无新增监听的端到端面板证明：**
- 使用候选原始 `index.html/app.js` 和真实已审核的 Handler 路由代码及 **合成** D2 受限 fixture（不接触 Mac 私有 JSON），模拟用户显式点击“读取已导入快照”、上一页/下一页、Mint 精确查询、ZERO_AT_SLOT、无观测账户、非法 Mint、缺失/损坏来源、HTTP/JSON 错误、旧请求后到的竞态。
- 优先利用 Chrome/Playwright 的独立 `file://`/内存路由拦截进行 browser acceptance 和直接 Python Handler no-socket 测试；**禁止**为此另起常驻 HTTP 端口。若无 socket 的真实页面验收技术上无法保留完整产品行为，应记录测试覆盖不足，不要把 DOM/mock 结果冒充完整浏览器验收；要用短时临时本地 fixture socket 须另行申请授权。
- 检查初始加载时新 D2 GET = 0、用户点击后才 GET、不会 POST/RPC/自动循环；D2 页面明确显示 2026-10-23 **21:46 曼谷时间**及 SPL slot460482174、Token2022 slot460482176 的 **非原子历史证据**；不会称作今日实时、不会推导 USD/PnL。
- 旧版 Frank V1 信号/MC智能分析、CA Quick/Standard/Deep 入口和其它 UI DOM/GET 控件保留；无新增自动邮件/通知/金额预设；其他已有 P1 不可假称已修复。
- 最终出具严格实测的 `MAC_D2_PREDEPLOY_READINESS_PASS` 或 named `BLOCKED`，带清理证明、原文件/提交身份、实际覆盖用例、全部零生产写入/零监听统计；必要时独立 reviewer 只看**发布适用性、差异、私有源路径和旧服务保护**，不重做已通过的历史数据导入。

## 未来独立授权后方可执行的“Dashboard-only”单次上线

**此节是未来受限决策单，不是本次操作授权。**

0. 再次询问用户授权一次 **仅 Dashboard** 的版本发布及短时 `8766` 中断；若没有显式批准则 STOP。解释器 `G03B_INTERPRETER_ORIGIN=UNRESOLVED` 仍需披露，不得冒称 PASSED。用户需了解 D2 接口是**loopback-local browser barrier**（同源/自定义请求头），不是对本机任意进程的强身份认证；不要扩展监听到 0.0.0.0。
1. 开始前从实际 current `com.jerson.frank-meme.dashboard` runner/control pointer 提取当前 `LOCAL_AGENT`/控制目录/8766/Python/运行参数，验证当前 Dashboard 实际运行 PR168 437文件版本、原 runner SHA256 `a7cf3df2308535a3de8f5b723a4a373eaece5f8ac54a2f7350db28e3adf3c4b0` 或者如有变化先 STOP、不得盲目覆盖。核对 Loop/V1 当前 PID/start及通知策略/递送计数，禁止假定昨天 PID 不变。
2. 保留原 PR168 完整不可变 release tree 437/437 及私有 rollback 包。建立新候选完整只读 release tree `dashboard-only-releases/<pinned-candidate-SHA>`，文件 manifest 100% 核对、import-only 测试通过；不要覆盖原目录/复用相同版本标签放未审核 patch。
3. 预先证实仅将 **现有** `dashboard.sh` 中 `LOCAL_AGENT` 的一行由 PR168 目录替换成新 immutable candidate 目录后，其他字节完全一致且可逆；禁止修改原 `PORT=8766`、production/control roots、venv、policy、launchd plist、Loop runner、V1 runner、默认投资金额。
4. 再次读 GitHub fixed SHA、真实 Mac 原 PID/port/manifest/保护文件。经独立正式发布授权后，原子更换 Dashboard runner，然后只执行目标 Dashboard label 的 `launchctl bootout` + `bootstrap`，不使用通用 installer，不 kill 未知进程，不动 8765/48721，不起第二 HTTP listener/launchd job。
5. 真实端口 `127.0.0.1:8766` **单一** listener、新 Dashboard source/cwd/pid/runner matching；先做原9项无写 GET regression、原静态资源 hash 一致；随后仅在 8766 做显式 D2 GET（正确 header），页0最多100条、页41有48条，精确 Mint 返回 0/非零/缺少账户等准确状态，历史时间/slot与私有文件 checksum吻合。仅 bounded read-only response，避免把真实响应 body 上传到 Git。
6. 真实 Chrome 用新生产页面显式点击查询并验证时间/提示/分页；不调用 CA POST/新 RPC、不发送邮件/通知、不下单。验证 MC Loop/V1 运行源、PID/start/策略/通知计数跟上线前一致；如发现 protected service identity changed, API failure, D2 private source invalid, 8766 非单监听或无法恢复，则立即 STOP，执行**仅 Dashboard** 回滚。
7. 回滚只恢复原 Dashboard runner 的精确字节/模式和原 PR168 immutable release，且只对 Dashboard label 执行必要的服务切换；**保留新 D2 私有子目录与 JSON 原样**（它们已是独立验收通过的安全数据）。真实回滚若未执行不可写 `ROLLBACK_TEST_PASS`，只能称 `ROLLBACK_READY`。不要在代码回滚时删/覆盖私有源文件。
8. 发布脱敏 `PRODUCTION_D2_DASHBOARD_PASS` 或 `PRODUCTION_D2_DASHBOARD_FAIL_ROLLED_BACK` 或 `CUTOVER_BLOCKED_NO_CHANGE`，记录固定 SHA/manifest、无新端口/服务、旧提醒计数与回滚状态。仍不证明当前实时持仓及 CA 深度分析 P1 完成。

## 当前明确禁止

`NO_DEPLOY / NO_MERGE / NO_DASHBOARD_RESTART / NO_LAUNCHCTL_CHANGE / NO_NEW_RPC / NO_TRADE / NO_EMAIL_OR_NOTIFICATION / NO_SCHEDULER / NO_NEW_LISTENER / NO_PORT_MIGRATION / NO_SHARED_ROOT_CHMOD / NO_PRIVATE_DATA_REIMPORT / NO_PROD_SQLITE_WRITES`。

**本文件所在仅是发布规划分支**；所有实际生产变更与未来服务中断均需独立授权，且不能用用户此前仅允许历史数据导入的权限替代。

## 2026-10-24 R1/R2 实机反馈 — R1 PASS，Chrome IPC 限制导致 R2 阻断

固定产品 SHA 仍是 `914e9e47fed2e60bc24690fcb083413a64d4e681`，不是下述文档提交。证据：[PR #178 执行报告 #6383051314](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6383051314)，脱敏提交 `cfc5c1b2fe62ab57ce5b61be20e334ac8c3c6f62`。

- **R1 已完成，无需重复**：446 Git 文件完全一致，完整规范化 manifest SHA256 `9a06f5f29fce05ccade8caa2b90d6d6c0c4248d2e6ab4e45aa26fa9d3f401062`；当前 Mac Python3.14.7 import-only、原 PR168 437文件及服务、0755/0700/0600 已导入 JSON SHA 均 PASS。
- **R2 仍未执行任何页面用例**。原 Chrome profile 是新建的；阻断并非确定“Chrome profile 被占用”，而是 Chrome 进程在 `(allow default)(deny network*)` 下连自己的 ProcessSingleton **AF_UNIX** `bind()` 都被拒绝，exit21、无 page。原 R2 `BLOCKED/COVERAGE_LIMIT` 记录不可改成 PASS。
- R1 的 446 文件临时候选包已清理，若后续检查使用必须从固定 SHA 重新组装并比对已经证实的 manifest。不得再次执行 importer/exporter 或读取原始私有回执。

### 本轮唯一建议补测：先证明“只准独立临时路径的本地 AF_UNIX，禁止所有 IP 网络”，再试一次 R2

这是一份**设计/交接**，不等于用户授权放宽沙箱或运行第二次 Mac 浏览器。后续须由用户明确认可**这一条最小 R2 离线补测**；仍不授权生产部署、重启、新服务/端口或 RPC。

1. **准备隔离和检验策略**。Mac 执行器使用新建 owner-only `0700` Git 外临时根，同时放置全新的 Chrome `user-data-dir`、`TMPDIR`、合成 JSON、pipe/本地 IPC 及私有测试证据。设置受限且不泄露真实 profile/path 的环境。**只在这个规范化临时根下面许可 AF_UNIX 创建与连接**，不许可对 `/var/run`、ssh-agent、Docker、其他用户/应用本地 socket 的连接；不随便 `(allow network*)` 或 `(allow network-outbound)`。
2. **Seatbelt 候选应精确区分网络族**：保留原来的对所有 IP `network*` 拒绝，仅增加 `(allow system-socket (socket-domain AF_UNIX))`，并用 `network-bind (local unix-socket (subpath ...))` 和 `network-outbound (remote unix-socket (subpath ...))` 限定到**此单次临时根**；如 Chrome 实际 `listen/accept` 也被拒绝，只有在受控 AF_UNIX 合成实验证明必要且同样 path-scoped 时才考虑 `network-inbound`。Seatbelt SBPL 语法及路径匹配具体以**当前 Mac 实际编译和 deny 日志为准**，不得基于外部示例推定已经生效。可以参考 [OpenAI Codex Seatbelt path-scoped Unix-socket generation](https://github.com/openai/codex/blob/main/codex-rs/sandboxing/src/seatbelt.rs)。绝不全域放行 Unix-socket bind/connect。
3. **最少四个策略实测断言**（合成短进程，非 Chrome，安全清理）：(a) 允许在这次私有临时根创建 AF_UNIX 并 bind/listen/connect；(b) 对另一个独立合成目录的 AF_UNIX bind/connect 均拒绝；(c) AF_INET/AF_INET6 bind 和对隔离验证端点 connect 被内核策略拒绝，**不请求正式 8766**；(d) 所有子进程继承同样拒绝 IP 的沙箱，结束后不存在额外 TCP LISTEN/持久 Unix 端点。必须记录内核实际拒绝/允许证据；不以 `ECONNREFUSED`/DNS失败冒充策略拒绝。如果连策略语法或四断言无法通过，`BLOCKED_IPC_POLICY_NOT_PROVEN`，停止，不启动 Chrome。
4. **仅在 1–3 PASS 后，重建最小 R2 synthetic browser harness**，最多一次新鲜 Chrome launch；实际 Chrome ProcessSingleton Socket 路径必须在单次临时允许根内，否则 `BLOCKED_CHROME_IPC_OUTSIDE_ALLOWLIST`。保留原候选 `index.html/app.js` byte-for-byte（以及 CSS）；Browser 所有请求先行拦截，静态 asset 全部取自固定构件，D2 GET 请求通过**现有 stdin/stdout pipe**送到原始 `Handler.do_GET` 加**合成 reader**；未列入白名单请求一律 abort。HTML 使用合成 origin、无真实网卡通信；禁止让浏览器向现有 `127.0.0.1:8766` 发送任何 HTTP 请求。若浏览器原始 Host/same-origin 校验在这种 in-memory route 下不能真实覆盖，则如实标明 `COVERAGE_LIMIT`，不能模拟一个过强的 PASS。
5. **R2 一次性验收范围**：真实 Chrome 创建 page 成功；初始加载 D2 GET=0；点击后才同源 GET，最多100条/页、page0/page41、精确 Mint 的非零/零/缺失；2026-10-23 曼谷时间和两个 finalized slot 的非原子/非实时声明；丢包/坏 JSON/无私有来源、旧请求竞态；原 CA Quick/Standard/Deep 和 Frank 信号面板 DOM/渲染无退化。检查 GET/POST/RPC/通知尝试账本和 browser console；如有产品功能真实缺陷，则 `REQUEST_CHANGES` 并记录最小复现，不修改产品/重试以硬凑 PASS。
6. **严格一次收尾**：关闭本次 Chrome、pipe、子进程和合成源，清理临时 Unix socket/Chrome profile，固定 manifest 比对不变；只提交脱敏 scalar 状态、经过证实的所覆盖用例和安全否定证据。原 `R1_PASS` 与这次 `R2_BLOCKED` 都保留不可重写，后续新增独立 `R2_BROWSER_SYNTHETIC_PASS` 或清楚的 `BLOCKED`。此为离线合成 UI 验收，不是正式生产 D2 HTTP/Chrome 通过，也不提升 `G03B_INTERPRETER_ORIGIN=UNRESOLVED`。

### 强约束与时间盒

**只修复一个已识别的 Chrome 本地 IPC 环境阻断；不重新调查 446-file/R1/D2 数据导入。** 拒绝任何额外 TCP 监听、额外端口、持续进程、后台调度或测试服务器。若此唯一策略修正后的有界运行仍无法启动 Chrome，则停止并报告具体原因，不围绕沙箱进行无止境迭代；再作产品主线取舍，不为了技术边界问题反复拖延功能交付。

`R1_PASS / R2_BROWSER_NOT_TESTED / IPC_PATH_SCOPED_RETRY_DESIGN_READY / MAC_NEW_RETRY_NOT_AUTHORIZED / PROD_UNCHANGED / KEEP_8766 / NO_NEW_TCP_LISTENER / NO_DEPLOY`。
