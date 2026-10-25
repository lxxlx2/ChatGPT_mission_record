# Frank P1-A — CA 真实用户流程与 RPC 总预算门禁（2026-10-25）

状态：**SOURCE_AUDITED / PLAN_ONLY / NO_MAC_PRODUCTION_DIAG_AUTH / NO_NEW_CA_OR_RPC_AUTH / NO_PRODUCTION_CHANGE**。仅针对 [Issue #165](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165) 中的 Deep `Failed to fetch` 与 Quick/Standard/Deep 真实结果验收。**不是**新扫描、部署、写入策略或历史 D2 重验授权。

## A. 先清理已经解决的事项，保持原需求

- [2026-10-23 D0 真实 Mac 只读诊断 #6347259929](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6347259929)：历史 Deep 页面 `Failed to fetch` 是浏览器读取本机 `GET /api/cluster-analysis?job_id=...` 的失败表现；同 Mint 已保存一份 Deep 历史报告且当时缓存 GET HTTP 200。**原失败请求的 job_id/精确 TCP 原因没有保留**，禁止声称已证明原始连接重置原因。
- 原 D0 已定位的页面“单次 GET 出错后不再恢复”问题，已由现有正式源码的有限 GET 退避、手动原任务恢复、session job ID 与历史缓存读回解决。既有 `test_frank_ca_get_resume.mjs` 包含只 GET 重试、失效身份、404、迟到响应等离线测试。**不得再重新开发同样按钮/退避，或重复无关 503 / Safari fixture。**
- 2026-10-22 保存报告：历史报告约 1,997,937 字节，`deep_holders_scanned=20`、`top_accounts_resolved=20`、`transaction_errors=0`、`rpc_endpoint_failures={}`、`special_normalization_complete=false`，历史 `rpc_calls=1733`。**这些均为原历史报告自载值，不是今日 RPC 或本次任务的结果，无法证实它关联最初失败的那个 job。**
- 2026-10-25 P1-B **D2 私有来源切换已由真实 Mac 回执报告成功**：[Issue165 #6397398919](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6397398919)，生产 JSON 为 Oct25 dated 4305 Accounts/4305 Mints/3432 非零/873 零，只有一次实际 D2 GET 接口验收、没有新的 Chrome 页面验收。D2 一次性授权已消耗；旧 [`FRANK_P1_CA_AND_CURRENT_OWNER_ACCEPTANCE.md`](https://github.com/lxxlx2/ChatGPT_mission_record/blob/cd1842a33e04ed81877d9729cb1aec1a2d77f465/docs/MONITORING/frank-release-20261025/FRANK_P1_CA_AND_CURRENT_OWNER_ACCEPTANCE.md) 中“Oct23 仍为已导入最新源”等叙述已过时。**不再重复 D2 采集、回放、备份或切换。**
- 保留 Frank 原买入提醒、V1/Loop、G1 策略、历史模型信号；不能从历史 D2、历史 CA 或非零余额推出最新持仓、主动买入、实时估值或 PnL。

## B. 固定源码事实（不把仓库代码当成已完成生产验收）

依据既往 Mac 验证的 446 文件产品 SHA `914e9e47fed2e60bc24690fcb083413a64d4e681`，本文件编写时只读核查了对应 GitHub 固定源码；正式执行时仍须在 Mac 重新验证安装 manifest/进程身份。

| 位置 | 实际行为 | 门禁后果 |
|---|---|---|
| `mission_control/static/app.js` `pollClusterJob`（约 L1728） | 对已有 `job_id` 轮询 GET，遇到非终态错误最多追加 3 次 GET-only 重试（1.5/3/6 秒）；session 可保留 job+mint；手动恢复原 GET、历史 report GET，不自动重新 POST | 只读恢复能力 **CODE_PRESENT**，不是原旧 job 的身份级完成证明 |
| `mission_control/server.py` `ClusterJobManager.jobs`（约 L157、L528） | job 字典是**进程内存**；GET `/api/cluster-analysis?job_id=...` 查该字典，缺失返回 404 | 服务更换后旧 job 不可重新构造。**没有真实原 ID 就不做无意义随机 GET** |
| 同一 `server.py` `latest` 和 GET `/api/cluster-latest?mint=...` | 读取 `cluster-reports/<Mint>/latest.json`，键是 Mint 而不是 job ID | 同 Mint 报告不独立证明属于浏览器所提交的那一任务；必须标时间、预设/覆盖、关联未知 |
| 同一 `server.py` POST `/api/cluster-analysis`（约 L952）与 `ClusterJobManager.submit` | 真正排队启动 `WalletClusterAnalyzer.analyze()`，可能写本地 `cluster-reports`、RPC 缓存，并发起链上 RPC | **不是只读本地 GET**；必须另获允许实际 CA/RPC/本地报告写入的明确授权 |
| `mission_agent/meme/cluster.py` `SolanaReadOnlyRPC.call`（约 L320） | 单逻辑 RPC call 在未命中缓存时 `max_attempts=max(6, len(endpoints)*3)`；默认 4 endpoint 则**最多 12 次网络尝试/逻辑请求**，且按冷却切换后备源 | 现有代码没有在整个 CA job 上限制网络尝试总数；不能用 Quick/Standard/Deep 名称当总预算 |
| 同一 `cluster.py` `WalletClusterAnalyzer.analyze`（约 L802） | Top20 holder、各 holder 历史交易及资金来源查询；Standard 可追加自适应 deepen。各次 transaction 可能是单独 RPC 调用 | Deep `deep_holders=20, history_per_holder=100, funding_lookback=50` **不是** 20+100+50 次总调用的上限；历史 1733 次印证成本不可忽略 |

源码固定参数：Quick `6/8/4`；Standard `6/12/8`，自适应 `30/12`；Deep `20/100/50`。数字依次为 holder 数／holder 历史上限／funding 历史上限，不能用作真实全局调用限制。历史 1733 次 **不作为未来预算**。

## C. 决策和执行先后（每个带生产行为的门禁需要独立明示授权）

### C0 — 下一步唯一优先事项：旧报告恢复路径的最小真实诊断（待授权）

**权限尚未提供。** 必须先取得用户特指 CA-only 的 **一次 Mac 生产只读** 授权，内容限定当前现有 8766 服务/已有 Chrome/现有日志/已保存 `cluster-reports`；不允许新 POST、RPC、报告写入或服务重启。明确在用户批准前，只能读 GitHub 公开仓库代码和旧脱敏回执。

批准后 Mac 执行方按顺序：

1. 比对实际 Dashboard product 446-file manifest、PID/launchd、监听 `127.0.0.1:8766`、既有 control-root，验证没有同一台 Mac 上的源码/端口漂移；漂移则 `RUNTIME_DRIFT_BLOCKED`。
2. 仅核查指定旧 Deep Mint 对应**既有** `latest.json` 是否存在和是否属于原历史日期；若当前 Chromium/Chrome session 真正保留了可认证 job ID，允许**至多一次**受控同源 `GET /api/cluster-analysis?job_id=...`，记录 200 的实际 job status/stage 或 404；无原 ID 则**不请求此路由**。绝不能猜测/构造 job ID。
3. 为避免复制约 2 MB 的敏感 report 到终端/Git，优先在原 Chrome 页面操作**一次**“查看已有历史报告”，或者在本机只读方式对**已有** `GET /api/cluster-latest?mint=<既知 Mint>` 执行最多一次请求；两者择一，不得自动重试为新任务。仅在内存提取 HTTP status、timestamp、coverage、hash、内容关联标记与渲染 PASS/FAIL，禁止记录 raw body、Mint、job ID 和交易/地址明细。对已保存 JSON 只能读取，不得“修复”或覆盖。
4. 单独核对浏览器 Network 对应本次 GET 的 HTTP/transport/DOM 渲染结果，区别 `NETWORK_FETCH_FAILED`／`HTTP_404_JOB_LOST`／`WORKER_ERROR_WITH_ID`／`CACHE_MISSING`／`REPORT_RENDER_FAILED`／`GET_ONLY_CACHE_RECOVERY_PASS`；**不要试图用无法保存的旧浏览器异常证明当前网络根因**。
5. 每种失败记录对应真实证据、准确时间、固定源、是否原任务 ID 确认；保留 1 个受控会话，不打开新监听器、无新扫描/RPC。公开 Git 仅发脱敏结论、统计、SHA 和状态，不上传原 report、HAR（可能含 URL/查询）、Mint/持币名单、job ID、token/密钥。

**C0 通过标准**：实际 Mac 的旧缓存 GET 与页面恢复路径可用，能展示报告**历史日期、不完整覆盖、与旧失败任务关联未知**；若失败，则有确切的 transport/HTTP/render 状态。仅 `GET_ONLY_CACHE_RECOVERY_PASS`，**不是** `NEW_CA_DEEP_PASS` 或 P1-A 总完成。

### C1 — 新 CA 之前的离线预算与 fail-closed 设计（未来 code-only，未实施）

独立 code-only 阶段必须先给 `SolanaReadOnlyRPC` 的所有网络 wire attempts 设计**全局、线程/作业级硬上限**，计数包括 fallback/retry、失败调用；缓存命中可以记 0 新网络尝试但必须记录命中及实际采样过期情况。还要有总耗时/单请求超时上限及用户停止/取消语义；不能只在 UI 隐藏新按钮当作保护。若预算耗尽，必须明确 `RPC_BUDGET_EXHAUSTED_PARTIAL`／`SOURCE_INCOMPLETE`，保留已核实的 partial 结果、stage、数量，而不把部分扫描标 DONE/可交易。

需要先检查特殊情况下 retry/GET 与 worker 取消的相互影响；提出安全的 runner 级方案（必要时隔离测试 runner）和策略，**不得私自修改现有生产 worker**。针对标准 Quick/Standard/Deep 各自评估理论 request 上限、合理的**总 wire call** 和实际成本/费用上限、对应已连接 provider 额度。先用 fixture 校验缓存命中、连续 429、备用 endpoint、partial 报告、报告时间、断线状态、退出和不重复 POST。任何新代码形成独立固定 SHA、CI、独立代码审核、必要 Mac 本地隔离测试和新的部署授权；此文档不直接放行。

C1 验收应避免武断写死少量请求以至无法完成 Deep；先测量**无 RPC 的仿真请求预算**，提交可信预算与结果覆盖率再让用户决定。不得擅自开付费 Key、新 provider、新常驻线程或每小时轮询。

### C2 — 真实 Quick→Standard→Deep 端到端（未来新批准，未实施）

仅当 C0 诊断完成、C1 的网络**全局预算控制与费用边界**（无自动付费）有审核和本机隔离验收证据后，才请求用户另行批准**明确的 Mint、预设、最大总 wire calls、提供者/费用上限、超时、不得二次扫描、失败停止和只读 UI/RPC 范围**。

逐个 preset 做单次前台验证，不因 Quick 成功自动连跑 Standard 和 Deep。新任务必须有：
- POST 接收与固定 job ID；进程/页面异常时原 job GET 恢复，不重复 POST。
- 进度阶段、HTTP/transport/worker 错误可区分，并记录有限次数 GET 恢复。
- 报告实际完成时间、固定 preset、来源、RPC 调用数/失败/缓存命中、Top20 holder、资金来源/交易与 `special_normalization_complete`、`transaction_errors` 的真实覆盖；历史缓存不可冒充该次 job。
- 如未达到完整归一化或数据一致性门禁，明确 `REPORT_PARTIAL`，不能把报告存在、Top20 或 `DONE` 等同“完整分析准确”。
- 不部署/重启 V1/Loop、发 Gmail、交易、推送信号；如产品服务需重启，必须单独授权，不能为完成本验收偷换运行代码。

## D. 责任、状态和停止条件

| 路径 | 可做与否 |
|---|---|
| 当前 GitHub 固定源码、历史 Issue 回执审查、研究文档 | **可以**；不得改生产 |
| C0 单次 Mac 8766/Chrome/历史报告生产 GET | **待用户单独明确授权** |
| C1 隔离 code-only 预算原型与模拟测试 | **先完成细化设计、固定 SHA 审核**，不自动部署 |
| C2 真实新 Quick/Standard/Deep POST/RPC | **独立另行授权**；无总预算控制时 STOP |
| D2 二次私有来源切换、实际钱包密钥、交易、通知或后台监控 | **本计划不允许** |

当前结论：`P1B_OCT25_DATED_D2_RELEASE_PASS / P1A_CA_OLD_GET_RECOVERY_CODE_PRESENT / P1A_REAL_FLOW_UNVERIFIED / NEW_CA_RPC_BUDGET_UNENFORCED / C0_MAC_DIAG_NOT_AUTHORIZED / NO_TRADES / NO_DEPLOY`。Issue #165 保持 OPEN。此文档仅记录源码风险、历史依据和可执行门禁，**没有实际生产 HTTP/CA POST/RPC、Mac 执行、写生产报告、更新代码、部署、合并或启动定时任务**。
