# Frank P1-A C2：仅 Dashboard 代码发布与一次真实 Quick 验收门禁

日期：2026-10-26（Asia/Bangkok）

**状态：`PLAN_ONLY / C1_INDEPENDENT_CODE_APPROVE / C2A_DEPLOY_NOT_AUTHORIZED / C2B_CA_RPC_NOT_AUTHORIZED / NO_MERGE / NO_RESTART / NO_TRADES`**

## 0. 目标与已关闭范围

C2 的唯一实际目标是让用户能够可靠得到新的、明确标注覆盖范围的 CA Quick 结果，再按实测而非猜测决定 Standard / Deep。不得重复已完成的 D2 导入、历史缓存 GET 修复、PR #205 两项 P1 的固定 SHA 独立审核或 Mac 离线回归测试。

- P1-B：Oct25 D2 **带日期的历史来源**已通过真实生产文件替换与 API GET 回执，来源 4,305 accounts/Mints、3,432 非零、873 零（[Issue165 #6397398919](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6397398919)），非实时、非 PnL；现有源不得被新发布过程更改。
- P1-A C0：2026-10-25 生产已有 CA 历史缓存 GET **HTTP200**、老 job_id 缺失、未做 Chrome DOM，旧报告 `special_normalization_complete=false`（[Issue165 #6400369303](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6400369303)）；不把已有同 Mint 报告当原任务完成证据。
- P1-A C1：Draft [PR #205](https://github.com/lxxlx2/ChatGPT_mission_record/pull/205) 固定独立审核 `APPROVE` 仅代码/离线增量，HEAD **`4fdf2238a4db2347975689913e49142b760dc091`**，审核 [#6400746248](https://github.com/lxxlx2/ChatGPT_mission_record/pull/205#issuecomment-6400746248)，独立 CI **39 Python/15 JS PASS**。旧 P1 重定向绕过/最后失败错误 DONE 均在该 SHA 关闭。仍非生产批准。
- 实际现有 Dashboard 上次 Mac 核验的产品 SHA **`914e9e47fed2e60bc24690fcb083413a64d4e681`**、独立完整 446 Git 文件；已有 D2 私有 JSON 整字节哈希 `a1c3fcce95a8271baf585e30ea7348424eb4799cb2a26d513a142270253890d0`。**上次证据不能代替执行时现场复核**。

## 1. 固定产物 / 最小影响比较

| 项目 | 锁定要求 |
|---|---|
| 代码来源 | **只允许** PR205 已审 HEAD `4fdf2238a4db2347975689913e49142b760dc091`；不能拿本 C2 文档 SHA 或将来 rebase/merge SHA 直接替代审核版本 |
| 安装基线 | 已安装 `914e9e47fed2e60bc24690fcb083413a64d4e681`；执行前比对真实 Mac checkout、runner、plist、venv Python、唯一 127.0.0.1:8766 listener、服务身份、策略与通知计数 |
| 新版本内容 | GitHub 固定 Git Tree 核对：旧 local-agent **446 个 blob**，C1 新版本 **448 个 blob**（多两份测试）；必须逐条从最终产物生成包含路径、内容 SHA256、Git 执行模式的**新 448 文件 manifest**，不能复用旧的 `9a06f5f2...` 446-file manifest |
| 源码增量 | PR205 相对 installed 基线只有 7 项：cluster.py、server.py、static/app.js、两份测试、一个离线 workflow、一个文档。实际 local-agent 内只有 3 个现有产品文件改动 + 2 个测试文件新增 |
| 保留内容 | Oct25 D2 私有 JSON、旧全量只读代码构件及已验证恢复副本、Loop、V1、control DB、通知策略/队列、launchd plist 和其它服务不变 |
| 独立发布方案 | 沿用 [PR178 已执行且独立核对的 Dashboard-only 发布 #6388948971](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6388948971) / [#6388984821](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6388984821)：新只读候选目录、仅 Dashboard runner `LOCAL_AGENT` 一行字节可逆变化、仅 Dashboard label 的 bootout/bootstrap，受控短暂 8766 中断；这是将来需用户签字的发布门禁，**现在不执行** |
| 禁用 | **不得使用** `install_mission_meme_launchd.sh`：它会改写策略、runner、plist、启动配置并重启 Loop + Dashboard，且会做 Gmail 预检，范围过宽 |

本门禁仅从 Git Tree 证明源文件计数；没有实际创建、签署、运行 448 文件 Mac 安装构件或新 manifest。实际构件的 normalized SHA **TBD by future Mac execution**，不可编造。

## 2. C2A：仅 Dashboard 代码更新（**尚未授权**）

**明确分离部署许可和真实 CA 扫描许可。** C2A 需要新的用户授权，点名固定 SHA、允许运行状态预检、一个 Dashboard-only 短暂停服/重启、仅 8766 上旧安全 GET/Chrome 读取、发生失败时仅 Dashboard 还原。C2A **不包含** CA POST、新 RPC 或新扫描。

若获明确同意，Mac 执行代理必须：

1. G0：一次严格只读预检，核对固定 PR205 HEAD/已安装真实 446 文件 + manifest + 现有 Dashboard 唯一 PID、启动时间、argv/cwd、runner/plist、socket 8766、venv/解析器、实际环境来源；并记录 Loop/V1 的身份、原买入通知规则和计数、现有 D2 JSON SHA。任一漂移、不完整、权限/签名不明 → `C2A_RUNTIME_DRIFT_BLOCKED`，不进行切换。
2. G1：从**固定 Git**生成完整独立 Git-external 新 448 文件只读发布目录，逐文件核对 Git blob、SHA256 和可执行 mode；Python `-I -B` **只导入** server/cluster/static 的新版本，不实例化 DashboardState，不开端口，不造报告、不调用 RPC/CA。新旧产物与 rollback 映射同源明确，准备仅 Dashboard runner 旧原字节/mode、旧目录与 manifest 的私有备份；失败 `C2A_CANDIDATE_NOT_VERIFIED`。
3. G2：获得*第二次当场确认*服务未漂移，runner 仅一处 `LOCAL_AGENT` 行严格字节匹配，变化可逆，无其它文件/变量/策略变化。只对 **Dashboard** runner 原子替换，并只对**原 Dashboard Label**做受控 bootout/bootstrap；不触碰 Loop/V1 的 launchd 及 PID，不改任何 DB/JSON/策略，禁止 full installer、端口变更、新监听器。若用户没有明确允许 Dashboard 重启，**在 G2 前 STOP**。
4. G3：同一原有 127.0.0.1:8766 只读 smoke：固定新版源码及静态哈希、runtime 和旧 CA 历史缓存 GET / known safe endpoints；D2 源仍必须是 Oct25 新哈希/数量/分开的 finalized slots，旧历史数据不冒充实时；既有 GET-only recovery/Quick/Standard/Deep 控件只能**显示或读取**，绝不点击提交表单。真实 Chrome 可行时进行明确受限的只读 DOM 核验并标注是否确实做过，不能以 API 代替浏览器。
5. G4：检查仅 Dashboard PID/启动身份发生经授权的切换，其它 Loop/V1 PID/启动/runner/plist/策略/原提醒通知计数、D2 文件、其它监听端口都不变。成功 `C2A_DASHBOARD_CODE_ONLY_RELEASE_PASS`；否则 **仅 Dashboard** 恢复旧 runner 原始字节和旧不可变代码目录 + 必要的**仅 Dashboard** 重启，验证恢复服务 8766。回滚不是上线 PASS；任何无法证实恢复 → `C2A_ROLLBACK_FAILED_STOP`，不得重试或扩大操作。

只允许 GitHub 发布脱敏证据（固定 SHA、文件数量、hash、代码和服务身份、GET 结果/时间/状态），不提交进程敏感路径、私有响应、钱包、完整 Mint、RPC URL/key 或历史报告。

## 3. 免费 RPC 事实、预算与 C2B 判断（**没有实时调用**）

已核对截至 2026-10-26 可读的**官方公开文件**（非用户 Mac 当前 provider 账户状态）：

| 来源 | 已证实 | **未证实，不得当作承诺** |
|---|---|---|
| [Solana 公共 RPC 集群说明](https://solana.com/docs/references/clusters) | 当前文档例示 Mainnet 100 requests/10s/IP、单方法 40/10s/IP；403/429 可能发生，官方明确不建议公共节点承载生产业务 | 限制会变、基于共享 IP/所有应用，并无 C2 单次稳定 300 请求或历史交易完整性的 SLA |
| [PublicNode Solana 官方页面](https://solana.publicnode.com/) | `https://solana-rpc.publicnode.com` 为公开的 Solana 入口 | **没有可引用的该入口明确、固定、可保证的每 IP/每方法配额**；archive 能力及本次所需 getTransaction 历史覆盖需实际证实 |
| [Ankr 官方服务计划](https://www.ankr.com/docs/rpc-service/service-plans/) | Public 为免费，文档展示 Solana Public 约 1800 req/min 的供应商聚合说明；Freemium 须登录、额度和付费层分开 | 不代表用户 Mac 当前使用的匿名 Solana 路由仍允许所有方法/相同额度；具体部署配置是否使用个人收费 key、当前余额和费用还未知 |
| [Ankr 官方价格](https://www.ankr.com/docs/rpc-service/pricing/) | Premium PAYG 对 Solana 请求公示每次 500 API credits / $0.00005 | 这**不是**现有匿名 Public 请求收费证明，也不构成批准开通 PAYG、充值或使用已有付费密钥 |

固定 C1 代码中的**候选安全停止界限**：Quick=300 wire attempts / 600s；Standard=1200 / 1800s；Deep=2500 / 3600s。实际所有 fallback/retry 都计入 wire 尝试，HTTP 重定向拒绝；错误重试耗尽不允许错误 DONE。**这些数字尚未按当前真实 provider 配额审核，不是服务配额或新扫描授权。**

**C2B 禁止条件：** 未能读清现有 Mac 的有效 provider 列表与计费模式、存在付费 key/PAYG 但无独立用户费用授权、不知道免费限制/可用历史方法、其它并发业务可能共享 IP 限额、发现账户或平台主动阻断 403、策略需要新 endpoint/密钥或收费 → `C2_PROVIDER_OR_COST_UNVERIFIED_BLOCKED`，不得发送任何新 CA POST/RPC。仅凭 C1 300 次代码上限也不能证明**美元总成本为 $0**，如果路由未知则 fail-closed。不自动调高限额，不自动扩大 fallback。

**时间和费用的真实边界：** C1 的 600 秒只是 RPC 适配器边界的单任务 elapsed gate，**不是**整个 Worker 强制在 10 分钟杀停；token market HTTP、流式读取、SQLite、CPU、报告写入都不能被其强制取消。一次成功 CA 也不意味着风险地址识别完全准确。

## 4. C2B：唯一首次真实 CA Quick（**尚未授权**）

须先有通过的 **C2A 实际发布证据**以及单独的**C2B 用户授权**，点名原先已核实的一个历史目标 Mint（完整地址仅在 Mac 本地可信来源取得，不能在公开 Git 明文）、仅 **Quick**、当前已确认零收费的已存在 provider、最多 **300 次 on-wire Solana JSON-RPC 尝试**且脚本/产品自有时间界限如上、一个 POST、无自动重试/续跑/升级 preset、失败立即停止。若确实还存在预算/费用不确定性，拒绝执行，不要暗中改走收费 provider。C2B 单次权限在首次提交尝试后即消耗；即使 429 或 ERROR 也不得重试 POST。

真实验收明确区分：
- **GET/浏览器**：原始唯一 job_id 可由当前进程查询和恢复；POST 一次成功接收后用已有 GET-only bounded polling 追踪同 ID，记录提交/任务/传输和渲染错误；无凭据/地址原文外传。
- **业务结果**：至少审查 source/observed_at/preset、实际 top_accounts/holders、funding/history采样上限、`special_normalization_complete`、`transaction_errors`、`rpc.calls`/失败/缓存命中、输出是否属于**本次 job**；`DONE` 只表示代码工作流完成，不能取代完整准确性、全部钱包受益所有权归属或 PnL 的证据。
- **限额**：若 `RPC_BUDGET_EXHAUSTED`，必须 status ERROR、无新成功报告、旧 latest 原字节不变、无 `ca_done` 通知/发布；其它 HTTP429/403/断网对应准确原因，不得转为“已完整分析”。
- **隔离业务影响**：Loop/V1 原提醒、政策/通知计数、Dashboard、D2 JSON 及不相关端口无变化，无实际交易、邮件、钱包签名、控制库更改（CA 既有报告/缓存写入在独立 C2B 明示范围内才允许）。
- **阶段级止损**：Quick 实际完成且被独立认可后，再提出 Standard/Deep 下一次**单独**授权，不能把一次 C2B 许可自动延伸或把历史 1733 RPC 当作下一轮必需量。

## 5. 当前决策单（PLAN_ONLY）

| 门禁 | 当前决定 |
|---|---|
| PR #205 精确 SHA 代码离线审核 | `APPROVE_CODE_OFFLINE_ONLY`；保留 Draft，**不合并** |
| Git 448 文件完整性 | 源 Git Tree 计数已核实；新 Mac 独立安装物/manifest **未制作** |
| 历史 Dashboard-only 操作方法 | 以前有经 Mac 报告的成功回执，但新 C2A 的 Mac 预检/恢复**未执行** |
| provider 免费/可用历史方法、当前 Mac 账户 | **部分公开资料支持，不足以定量承诺 / 未验收** |
| C2A：Dashboard-only release | `WAIT_NEW_OWNER_EXPLICIT_DEPLOY_RESTART_AUTH` |
| C2B：1 次真实 Quick | `WAIT_NEW_OWNER_EXPLICIT_CA_POST_RPC_AUTH_AND_PROVIDER_PROOF` |
| Standard / Deep | `NO_AUTHORIZATION` |
| 当前已运行的 Oct25 D2、V1、Loop | **原样保留**，不采集、不重启、不改策略、不补发通知 |

**本 C2 文档仅整理源码、Git Tree 及公开官方 provider 资料，未访问 Mac、运行 GitHub Actions 新工作流、调用新 RPC、执行生产 HTTP/CA POST、写入生产、创建/重启后台服务、部署、合并或交易。** Issue #165 保持 OPEN；PR #205 SHA 和独立审核结论不因这份文档变化。
