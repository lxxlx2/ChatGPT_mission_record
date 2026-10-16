# Frank F01/C02/F02 Mac 隔离只读业务验收：下一阶段固定检查清单

日期：2026-10-15 Asia/Bangkok。
状态：`DESIGNED / MAC_NOT_RUN / USER_AUTHORIZATION_REQUIRED / NO_MERGE / NO_DEPLOY`。

## 1. 已确认的版本与限制

- [PR #73](https://github.com/lxxlx2/ChatGPT_mission_record/pull/73) 审核版本 `5755b8b96080f21635eaa5354588cbb8f6561ab0` 外部独立 `APPROVE`：仅批准固定版本隔离Git组装、**外部assembly回执**验证和安全清理。外部审查用户转发文字：[PR评论](https://github.com/lxxlx2/ChatGPT_mission_record/pull/73#issuecomment-6191845518)。原PR #72 `f9b0082aca2944ec6430bee173018924a6578721` 仍为 `REQUEST_CHANGES`。
- 临时组合来源严格为冻结main `662ba4aceb9d53cb7a541ad3f251f9e12b8c09ea`、PR73、F01 `516e3335a134c608f477019b79027982f43af32a`、C02 `8898134a8a302e1187138f7fb3da87a554567e6d`；真实历史Git证据 ref `refs/remotes/origin/evidence/frank-ca-local` = `b9fb6e6df9032a0e6f49c1274bb4ba61c9e4c2da`（须在用户 Mac 本地再次核对）。
- PR73 Git组装器不会启动服务，也不会创建/读取真实私有Sidecar。F02 `scripts.frank_f02_readonly_positions_api` 要求 `--bundle`、`--sidecar`；来源审查完成后只可读取曾获授权的既有完整原文，不允许新RPC或重新导入私有SQLite。
- 联合桥 `scripts.frank_joint_readonly_http` 通过已有 F01/C02 `GET /api/follow-opportunities`、`GET /api/cluster-latest?mint=<exact Mint>` 和研究F02 `GET /api/research/positions`，不是任意CA新分析，也不负责自动启动上游。
- 历史 2026-10-15 13:10 Bangkok 32目标归档9非零/23零，已远超300秒TTL。**正确的新查询结果须遮罩历史所有数量**，不能称为实时 Frank 持仓、已卖出或成本/PnL。用户若另行批准真实新RPC，属于下一轮独立采集授权，不是此次验收条件。

## 2. 用户 Mac 只读预检（尚未执行；需明确授权）

同一轮一次性记录以下事实；只保存**聚合与布尔检查结果**，不要上传私钥、完整用户个人路径、钱包私有原文、生产 SQLite 或其他人信息：

| 项目 | 预检必须记录 | 失败处理 |
| --- | --- | --- |
| 版本 | 源本地仓库存在、Git HEAD/branch、五个固定对象可解析、历史证据ref SHA、源工作区是否有未保存数据 | 缺ref/脏目录不重置、不stash、不覆盖，仅报告 |
| 隔离目录 | 拟用的独立临时root无符号链接跳转，和生产工作树/数据库目录不重叠；源组装本身默认为 `PLAN_ONLY` | 不自动清理 |
| 外部回执 | assemble stdout的完整候选SHA、原始64位manifest摘要另存于**临时checkout之外**；verify以独立外部回执验证 | 不从可变marker自行重取期望 |
| 私有F02 | 既有bundle、Sidecar只读存在性和一致性；完整来源/最后采集时间/TTL，不泄露私有原文；**不创建或重导入** | 缺失/过期应拒绝显示余额 |
| HTTP进程 | 事先识别现有生产端口/进程及另行批准的3个本地空闲端口；所有服务绑定127.0.0.1，日志不得包含敏感数据 | 若不能区分现有生产服务则停止 |
| 上游可用性 | 独立控制台真实已审核F01与C02 GET路由，F02研究API使用真实既有Sidecar；没有新POST/API任务、自动CA扫描、RPC/Gmail/交易 | 不能用合成上游顶替真实Mac验收 |
| 退出 | 手动启动的隔离进程停止并验证端口关闭；生产pid/文件前后状态保持一致；临时证据未删除 | 若产生ignored文件，cleanup必须拒绝并留待人工归档 |

## 3. 明确的业务验收用例

1. 用完整Solana CA查询一个 F01当前有资格的条目与另一个非资格条目：F01 必须按真实现场冻结筛选，不以历史BUY恢复资格；无法访问则是 `F01_SOURCE_UNAVAILABLE`，不是不跟。
2. C02报告命中：必须真实 exact Mint；未查则 `CA_NOT_QUERIED`，原归档 report 不能宣传为刚完成的综合CA尽调。
3. F02原来源如果过期：`STALE_ARCHIVED_SOURCE` 或 `SOURCE_UNAVAILABLE`，所有32行数量、账户数隐藏；`0.000000` 只在原文新鲜且验证观察账户为零时可独立表示 `OPEN_ACCOUNT_ZERO`。
4. F01/C02/F02任意一个断联或错误来源不提升其他来源的可信程度。损坏F01资格结构和HTTP提前EOF的审查回归必须继续拒绝（PR71）。
5. `combined_trade_permission=false`，不展示美元现时总持仓、已卖出、PnL；不发交易、不发Gmail、不调RPC。
6. Mac浏览器/同域产品UI仍不是本轮已有功能：本轮是原生实际GET业务验收；页面4功能、完整CA8页在真实产品开发与后续验收中完成，不以HTTP JSON接口视为整站已完成。

## 4. 后续业务开发顺序与完成标准

- **先完成Mac隔离端到端HTTP**：验收三来源与真实既有数据，记录时间戳/来源SHA/生命周期及退出码。只有另行明确授权才可运行手动进程，严格不动生产Dashboard与Frank V1。
- **之后以单模式任意Solana CA查询为主要开发目标**：官方X/官网精确Mint认证、叙事时间证据、市场池子/LP-vault与holder集中度/Dev-funder、原始资金和交易追踪、风险与不确定项，按源是否实际可取分别登记；不以单纯C02 identity称完整分析。
- **同步定义A05/A06/F02当前全钱包与多钱包**：覆盖全部token accounts、Token-2022、多ATA、last-attempt、真实交易活动与可验证历史成本；没有新的获批链上采集时不可宣称实时持仓。
- 经过真实用户Mac操作与其他AI产品审核后，才进入明确授权的生产合并/部署流程。

持续：`NO_MERGE / NO_DEPLOY / NO_NEW_REAL_RPC / NO_TRADES / NO_GMAIL / NO_PRODUCTION_SQLITE_WRITE / NO_NEW_AUTOMATION`。
