# Frank P1-B — 2026-10-25 私有 D2 来源切换门禁（仅发布准备）

状态：`PLAN_ONLY / SOURCE_OFFLINE_VERIFIED / NO_PRODUCTION_SWITCH_AUTHORIZATION / NO_MAC_ACTION_BY_THIS_PLAN`。

本文件是 Issue #165 的 P1-B 离线验收后续决策单。**本次仅新增此 Git 文档**；不能将本文件、PR、既往 10 月 24 日/25 日 Dashboard 代码发布批准解释为新的私有 D2 数据切换授权。不运行 Mac 命令、生产 HTTP、RPC、文件导入、服务重启、部署、合并、通知或交易。

## 1. 固定依据和现状

- Issue #165 新来源实际 Mac 离线回放与对账：[6394913720](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6394913720)。本计划编写者只核实公开的执行回执及仓库代码，不重新读取 Mac 私有原件。
- 已安装正式 Dashboard 来源（既往 Mac 生产报告）：`914e9e47fed2e60bc24690fcb083413a64d4e681`；只读证据见 [PR #178 发布报告](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6388948971)。现有 127.0.0.1:8766 是此前报告的状态，实际切换时须在 Mac 重新确认，不能当作持续在线证明。
- 保留旧 Dashboard 发布/回滚源码：`656ed2c96f4210d106d7b1129ec6cf8d7c4586f3`。**该代码回滚包与 D2 私有 JSON 数据回滚是两个不同对象**；此次计划只涉及 JSON 来源。
- PR #178：`ea9a7715beb4d2a55ae956bf993828cbddcb50e5`，Draft/unmerged，不是已安装 SHA。PR #174：`a14846f16e68fd0899ab5506d8c2f0c91272df48`。PR #60：`e4529ba7069e5499d12323a7160ceac08c481fae`。
- 现有代码位置：`crypto-300-profit-mission/local-agent/mission_agent/mission_control/wallet_d2_ingress.py` 与 `server.py`，均以实际安装 SHA 为准。固定 `SOURCE_SUBDIR=frank-d2-private`、`SOURCE_NAME=frank-d2-owner-at-slot.json`，大小上限 4,000,000 字节；`read_d2_source` 每次 GET 重新读取并验证私有文件，未证明会在整个多页用户会话中锁定同一个版本。单页最多 100 行，GET 需要同源检查和 `X-Frank-D2-Read: 1`；该 HTTP 头不构成本机进程之间的用户身份认证。
- 既有生产 D2 历史源：2026-10-23 14:46:32 UTC，两个 finalized slots `460482174/460482176`，4,148 Accounts / 4,148 Mints / 3,275 非零 / 873 零；曾报告文件整体 SHA256 `d24d73d13a5ab9740eed7d1f06a6226aa9650004ccd756458b579c9e2ee2e284`、文件 893,189 字节。执行时必须重新核对**完整文件字节 SHA**、权限和来源，不能只凭历史报告。
- 已验收的新来源：2026-10-25 07:06:02 UTC，finalized slots `461166205/461166207`，4,305 Accounts / 4,305 Mints / 3,432 非零 / 873 零；source capture SHA256 `7b07a0298cb2209a244cb2103883bff54e3c7a8487985321fdfb29d7a1eb2f5e`，**文档内部** `document_sha256=0f051e88853679d9cbd66b1852d5be88b04bca680209edb7dcbe578ae5b6a27e`。本地离线回执报告的紧凑序列化 927,253 字节；格式化 JSON 文件 1,280,402 字节。**文档内部 digest 不等于格式化磁盘文件的完整 SHA256**，生产门禁必须分别验证。
- 固定 32 Mint 名单映射新回放：8 非零/24 零/0 未观察到；历史 Oct11 原私有索引没有在本轮重新回放。新旧集合：shared=4148，old_only=0，new_only=157；共同 Mint 增 5 / 减 1 / 不变 4142。资产交易归因和 PnL 均未核实。
- 离线定向测试报告 38/38 PASS，真实 RPC=0，正式 D2 未替换。**此 PASS 仅证明离线候选有效，不证明生产切换成功。**

## 2. 推荐的最小改动发布方式

在用户**另外明确批准**后，优先采用一次性、人工、有回滚证据的**仅替换固定私有 D2 JSON**。不创建新 UI、新 API、后台进程或定时采集；不部署新版代码、不重启 Dashboard、Loop、V1 或通知服务；不触碰 CA。任何 Mac 环境检查与既有受控只读 GET 的许可范围也需包含在这次单独授权中。

本方案可行性的**源码条件**已经满足：当前 `DashboardState.frank_d2_at_slot` 调用 `query_d2`，`query_d2` 每次调用 `read_d2_source` 并从磁盘获取数据。但这不代表实际 Mac 运行身份、文件系统、启动脚本和当前占用的文件路径已重新确认。只有下面的 Mac 预检通过才可执行。

## 3. 按顺序执行的硬门禁（供后续得到授权的 Mac 执行方）

### G0 — 授权与身份核对，禁止抢跑

1. 在 Issue #165 确认存在**晚于本计划**的用户单独明确授权，覆盖：本机生产配置只读预检、保留旧来源、一次原子 D2 私有 JSON 切换、必要的本机只读 GET 与 UI 验收、失败时仅对 D2 JSON 回滚。
2. 没有新授权：`PRODUCTION_SWITCH_NOT_AUTHORIZED`，立即停止；不执行 Mac 生产预检、导入或 HTTP。
3. 严格比对实际 Dashboard 发布源码 446 文件 manifest、runner 的原始 PID/launchd 服务/监听地址与权限、当前 D2 control-root 路径和服务用户。任一不匹配：`RUNTIME_DRIFT_BLOCKED`。不得借此进行服务重启、自动修复或代码升级。
4. 检查 Loop、Frank V1、通知策略及计数器的原始身份，只读记录切换前后是否未变化。权限不足则停止，不尝试提权。

### G1 — 私有数据及备份的字节级准入

1. 定位 Issue #165 对应的**已存在的 Mac 私有离线候选**，不全盘搜 Home，不重复 RPC、不重新采集、不给 Git 上传钱包数据。
2. 只以 Mac 指定控制目录、确定性固定 basename 操作：shared root 必须由运行 UID 持有且不允许 group/world write；D2 private child 必须 0700、同 UID，文件必须 0600、regular、no symlink。检查路径组件安全、`lstat` 与 `fstat` 一致；按当前程序的真实 `read_d2_source` 规则执行。候选与旧源均做**整文件** SHA256 和现有 `validate_d2_document`。
3. 原始旧数据的整文件 SHA256 必须等于 `d24d73d13a5ab9740eed7d1f06a6226aa9650004ccd756458b579c9e2ee2e284`，否则判 `OLD_SOURCE_DRIFT_BLOCKED`；不能靠文档中记录的 Mint 数判定同一文件。
4. 候选应为与已验收新 D2 文档**完全一致**的内容，内部 `document_sha256` 和 `source_capture_sha256` 与上一节固定值完全相符；观察时间、2 slots、4305/3432/873、程序身份及 4 MB 限制必须重新验证。记录实际候选的**磁盘整文件** SHA256，不在没有证据时用内部 digest 代替。
5. 在**同一受控私有文件系统**创建 mode 0600 排他备份和待切换临时文件，目录 0700；备份中保存旧源**原始字节**而非重新序列化，校验与原始文件同 SHA；创建过程失败必须在切换前停止。仅写到 Git 外位置，不显示原始路径、owner、Mint、余额或私有原文。

### G2 — 最多一次最小原子切换

1. 用户的新授权与 G0/G1 全通过才可以执行。对原子操作前的旧来源状态再做一次验证，防止在检查与交换间发生未知修改。
2. 临时文件创建必须排他、拒绝链接，校验 owner/模式/完整 SHA 后 `fsync`；在控制目录的同一文件系统中，仅对固定 D2 JSON 目标执行一次 `os.replace` 类原子替换，并同步父目录。**不能按字节覆盖、截断旧文件或修改服务代码/runner**。
3. 切换成功后再次读取并通过原始 `validate_d2_document` 验证。文件整体 SHA256 应与准备的新文件 SHA256 一致，且与备份中的旧文件不同。
4. 不重启任何服务。出现重启需求或端口异常，立即按已授权回滚范围处置，不擅自扩大权限。

### G3 — 有界生产只读验收

1. 仅访问本机既有 `127.0.0.1:8766`，只使用所需同源 D2 GET，不允许 POST、CA submit、RPC、后台任务或新开放端口。
2. 验证 `GET /api/frank-d2-at-slot?page=0` 返回已知来源 digest、2026-10-25 的采集时间、两程序 slots、4305 Accounts / 4305 Mints / 3432 非零、最大 100 行、`current_chain_balance_verified=false`、`pnl_verified=false`。如使用脚本，显式设置同源头且避免记录响应中的 Mint/余额。
3. 必要时一次真实浏览器手动只读点击验证 UI 显示来源日期和时效标记；不触发 CA/通知。若浏览器不可用，可返回 `BROWSER_NOT_VERIFIED`，不能假报 Chrome PASS。
4. 检查其他保护中服务、runner 与通知计数未变化。注意多个 GET 之间无全局快照锁定，混合页面必须刷新并重新核对 `source_document_sha256`；不能宣称跨请求事务一致。
5. 无法完成必要门禁、数据错误或明显展示缺陷时，按 G4 回滚，并保留脱敏失败原因；不能改代码补救再悄悄重试。

### G4 — 仅 D2 JSON 的回滚与停止

1. 根据 G1 排他保留的旧**原始字节**构造同目录私有临时文件，重新检查模式、UID、完整 SHA 和 validator，`fsync` 后对相同固定 D2 JSON 路径进行原子替换。仅这一文件可回滚；不回滚或重启原本正常的 Dashboard/Loop/V1。
2. 回滚后通过纯本地文件读取、且在已授权条件下通过一条只读 D2 GET 验证原来的 2026-10-23 来源 digest/4148/3275 已恢复。任何失败明确标 `ROLLBACK_FAILED_NEEDS_MANUAL_RECOVERY`，不隐藏故障。
3. 不自动二次部署、不新增新的进程或保底 RPC，不删除私有证据。

## 4. 通过标准、回报与边界

- `RELEASE_READY_FOR_OWNER_DECISION`：此**文件**审查通过，但**不代表** Mac G0~G4 已运行或用户同意切换。
- `D2_PRIVATE_SOURCE_SWITCH_PASS`：实际 Mac 执行全部所需预检、单次原子替换、只读 D2 GET/页面接受标准、受保护服务不变、可逆旧源备份同时通过。
- `D2_PRIVATE_SOURCE_SWITCH_ROLLED_BACK`：曾执行切换但失败且已证实旧字节与原始展示恢复。
- `PRODUCTION_SWITCH_NOT_AUTHORIZED` / `RUNTIME_DRIFT_BLOCKED` / `OLD_SOURCE_DRIFT_BLOCKED` / `BROWSER_NOT_VERIFIED`：原样记录，不将不执行/未验证翻译为 PASS。

只向 Issue #165 发公开**脱敏摘要**：执行时间、固定 Git SHA、旧/新 source/document/file digest、聚合数量、读回状态及有无回滚。Mint 地址、owner、数量明细、原始 JSON、绝对私有路径、凭证以及 UI 原始响应均不能进入 Git。发布后通过 GitHub API 读回确认。

保持 Issue #165 OPEN：该 D2 工作只解决**带日期、两程序各自 finalized slot** 的完整 owner Token Account 可核对展示，不保证原生 SOL、其它 Program、实时资产总值、成本或 PnL。P1-A CA Quick/Standard/Deep 真实新扫描仍为独立未验收项；任何 CA POST / 新 RPC 需要另一项明确授权。G1 的独立策略收益验证、既有 V1 通知与交易权限保持原状。

## 5. 本轮事实声明

本计划完成时仅有 Git 文档变更。**Mac 生产文件切换、只读 HTTP 验收、重新部署、RPC、CA POST、回滚、数据库操作、通知、交易均未执行。**
