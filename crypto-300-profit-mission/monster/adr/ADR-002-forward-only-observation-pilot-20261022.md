# ADR-002 — Monster BSC 新池前向只读证据试验（2026-10-22）

状态：`OFFLINE_PROTOTYPE_APPROVED_TO_PREPARE / LIVE_MANUAL_RUN_NOT_YET_APPROVED / NO_DEPLOY`。本 ADR **不取代** ADR-001 免费来源、功效停止和统一治理；2025-07-01 冻结母体、P0/P1 门槛以及 2026-11-02 历史来源截止均不变。用户同意继续规划前向验证，但没有授权定时采样、实际购买或生产切换。

## 为什么要开这条独立验证路径

2025 年 BSC V2 已有 30 个按 Factory 时序选出的历史样本，Four.meme 日内有 538 个 launchpad 索引，部分交易和卖出为真实历史链上事实。但现在读取旧区块只能证明历史事件存在，不能凭 `block.timestamp`、`milliTimestamp` 或 2026 年 `ingested_at` 推断 2025 年当时普通用户实际收到事件的 `available_at`。这不是再扩大事后迁池样本能解决的问题。

新方案只对 **2026-10-22 以后真实发生且当场收到响应**的事件留下机器记录；不修改 2025 研究标签，也不宣称观察样本为真正的 2025 OOS。阶段状态仍 `P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`。

## 一次性前向观察最小合同

1. **发现源**：BNB Smart Chain 主网 Chain ID 56；PancakeSwap V2 Factory `0xca143ce32fe78f1f7019d7d551a6402fc5350c73`。先复用仓库已有的 Factory `allPairsLength()` 和按索引 `allPairs(index)` 只读调用，不依赖禁用的免费公共长窗 `eth_getLogs`。没有证明 V3、Four.meme 或整条 BSC 同样可覆盖。
2. **一次性样本**：仅一次前台调用，两个有明确时间的链头快照；两次间隔上限 3 秒；最多20次只读RPC；相邻块校验 parentHash、同一块在查询前后的 blockHash，看到链重组或 RPC 状态不一致就 fail-closed。新增索引超过3个仅完整记录总差额并明确 `PARTIAL`，不能吞缺失。
3. **证据**：对每次 RPC 留本地原始 HTTP **响应体字节**、SHA256、调用开始 UTC、完整响应处理完成 UTC、单调时钟耗时、请求方法及经过处理的参数、固定区块高度和hash。manifest 仅做有限摘要；**不得把用户私有 RPC URL/API key、原始大文件上传 Git**。当前不是第三方可信时间戳服务，时钟安全/本机时间校准需要独立审核。
4. **PIT语义**：`local_response_completed_at_utc` 是“此观察者最迟此刻已获取该响应”的**本地记录**，不是网络首次公开时刻、服务器生成时刻、可供所有普通用户执行的 `T_entry`；链上`timestamp`与本机完成时间永远不同列。既有历史`available_at`仍`UNKNOWN`。哪怕首次计数增长也不能据此证明交易可买、可卖、税率或资金利润。
5. **安全边界**：只允许 `eth_chainId`、`eth_blockNumber`、`eth_getBlockByNumber`、`eth_call`；无send/sign/approve、无私钥、无默认购买金额、无付费RPC，严禁后台cron/launchd和自动复跑。新样本计数为0时只能写“两个观察快照之间未见Factory计数增长”，不能写“全市场无新币”。
6. **验收**：交付可复现的离线负例与原始响应/manifest回放、SHA校验、只读限额和错链/重组/缺页 fail-closed；真实前台运行必须有用户单独明确批准。独立代码/来源审核前，不把捕获到的 `observed_at` 直接升级成正式 `PIT_VERIFIED`，也不允许进入P1建模。
7. **止损/后续**：若接口无可用响应、样本计数长期不足或发生本机时钟和RPC异常，保留失败事实，**不要**为凑正例改母体或增加默认交易金额。只有获得前向真实收包证据、完整源覆盖及经审查的买卖执行成本后，才另行讨论 P1。

## 当前真实性核对

2026-10-22 在已连接的、先前已使用过的 Alchemy 免费 BSC 只读应用中，`eth_chainId`实际返回`0x38`；`eth_blockNumber`返回`0x7b2afc1`；在**同一固定高度**调用 Pancake V2 Factory `allPairsLength()` 返回`0x35e3aa`（3,531,690）。这是“可读取状态”的单点验证，**不是**已在用户 Mac 原字节归档、持续观察或跑通双快照。无法把这次连接器调用的时间戳当成用户 Mac 网络可见性/成交时延。此证据只授予离线原型方向，不变更历史P0结论。

研发版本审查、任何运行本地命令以及是否建立独立长期前向试验，需要后续固定Git SHA与单独决策。

## 2026-10-23：零密钥的前向Mac环境准备路径（仅准备、未实际采样）

**准备状态：`CODE_APPROVED_OFFLINE / MAC_PUBLIC_RPC_PREFLIGHT_NOT_RUN / PILOT_NOT_AUTHORIZED`。**固定通过离线审核的运行源码为`c646d438ebdd33183e047e47323315d78aab2869`，证据提交`6403be0909e51fa3b87414ea0e71e5dc7dc10130`有115项真实Mac离线PASS和独立二审；二审不等于真实网络收包、Mac配置就绪或P0结项。

**发现不需要暴露私有密钥的更简单路径**：Alchemy官方公开的BNB Smart Chain mainnet HTTPS RPC `https://bnb-mainnet.g.alchemy.com/public`，官方页面明确标注“Free access, no key required, best for prototyping and wallets”（https://www.alchemy.com/rpc/bnb）。这**不是**已连接Alchemy私有应用`/v2/{api-key}`的Mac凭据拷贝；不要写入、下载、输出或提交任何私有key。不更改原账户设置。该公开节点限流/方法支持和Mac实际连通尚未验证，**不宣称一对双快照采样已可运行**。与历史P0的免费RPC盲试止损不同，本方案只试**唯一已核官方公开入口，用于前向单次源可达性**，失败不遍历其他候选。

Alchemy目前公开价格页（https://www.alchemy.com/pricing）列Free **30M CU/月、25 req/s**，这是供应商商品价目而**不是当前用户订阅额度的认证**。连接器独立查询到既有已连接Alchemy app确有`BNB_MAINNET`，2026-10账期团队至当前查询时累计81,352 CU、显示USD 0.00，响应**未提供团队订阅等级/剩余额度/硬封顶信息**；该私人应用CU并不证明公共端点有相同配额。所有真实采样仍以用户原`$0`预算为硬约束。

**Mac单次环境预检查命令，仅用于用户明确同意的read-only连接性检查，绝不是运行采样器；命令无任何私有凭据：**
```zsh
curl --proto '=https' --tlsv1.2 --silent --show-error --fail --connect-timeout 5 --max-time 10 --header 'Content-Type: application/json' --data '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}' 'https://bnb-mainnet.g.alchemy.com/public'
```
成功前置条件是：实际返回带`jsonrpc:"2.0"`、`id:1`、`result:"0x38"`的有效JSON。HTTP 200本身、网页结果或其他chainId都不算通过；连接中断、限流、缺陷或付费要求一律标`MAC_PUBLIC_RPC_PREFLIGHT_BLOCKED`，不得扩容、充值或降级真实数据门禁。本命令尚**未在Mac执行**，不允许填写假回执。

**通过预检查后也不得直接采样。**如用户另行明确授权一次性前台捕获，在隔离worktree和私有新目录、重新确认Mac CPU/内存以及Git固定SHA后，才可以在该唯一进程内临时传入公用无钥URL：`MONSTER_BSC_ARCHIVE_RPC_URL='https://bnb-mainnet.g.alchemy.com/public'`。不能默认执行`--manual-once`、定时器、CI、launchd、交易、邮件或模型训练。原15/24项离线测试、2025母体、`2026-11-02`历史止损日、`P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`均不被本环境准备改变。

## 2026-10-23：Mac公开BSC RPC第一道链身份检查已通过（用户回传）

用户在Mac执行本ADR上一节唯一`curl`连通性命令后，回传原样单行JSON：`{"jsonrpc":"2.0","id":1,"result":"0x38"}`，末尾`%`是zsh shell提示符。**将该用户实际回传记为`MAC_PUBLIC_RPC_CHAIN_ID_56_PASS_USER_REPORTED`**，不是我方直接读取Mac原始HTTP/TLS流量，也未验证来源IP、签名或内部应用密钥。根据该回执只确认：在这一次请求中，公开端点有响应并声称正确的BSC主网Chain ID 56。不能把它等同`eth_blockNumber`、固定区块`eth_getBlockByNumber`或历史/当前`eth_call`的成功，更不能提升为两次前向计数采样。

**下一顺序**：仅用该相同无钥HTTPS端点做`eth_blockNumber`获取一个块高、在**同一块高**做`eth_getBlockByNumber`和Factory`eth_call(allPairsLength)`，分别验证JSON-RPC envelope、固定高度、Factory ABI整数、无凭据和HTTP错误；这是有限的环境预检查**不是**`--manual-once`的两快照试验。预检查用户实际返回前保持`MAC_PUBLIC_RPC_PINNED_READ_UNVERIFIED`，也不填造Factory计数。公开端点通过单次chainId不保证后续调用限流或零费用用户账户额度，禁止在失败时循环试其他无名供应商。真实`MANUAL_FORWARD_READONLY_PILOT_BLOCKED`保持，除非环境核查完整且用户**另外单独明确批准**一次性真实采样。

不修改2025样本、P0/P1门槛、Free $0预算和`2026-11-02`历史来源终止日；不部署、不定时、不自动交易。

## 2026-10-23：Mac固定区块公开RPC读取已通过（用户回传）

**接收回执（用户Mac终端输出，尚非我方直接核验的原HTTP归档）**：

```text
CHAIN: BSC Mainnet (previously verified)
BLOCK: 129174690
BLOCK_HASH: 0x6ad7014c12f6f0fc9305e76a7d915216ced1e3423736b6e507a0d73a7a2bc98b
PANCAKESWAP_V2_TOTAL_PAIRS: 3532598
STATUS: PINNED_READ_PASS
```

用户执行的是此前列出的独立前置检查（**3次同步只读RPC**）：`eth_blockNumber`取得高度；在同一高度`eth_getBlockByNumber`校验回传区块号；在**同一高度**对Pancake V2 Factory `0xca143ce32fe78f1f7019d7d551a6402fc5350c73`读取`allPairsLength()`，并检查合法64位ABI word。此前单独`eth_chainId`回执是`0x38`。据此将该公开节点的Mac基础功能标记为`MAC_PUBLIC_RPC_PINNED_READ_PASS_USER_REPORTED`；**不假称原始HTTP响应、节点签名、独立时间戳已进入Git或PIT可信来源完整通过**。

**含义必须严格区分**：
- `3,532,598`是截至区块129174690该**单个Factory的累计Pair索引数量**，不是独立代币总数、最近新区块新增数、盈利样本或可交易池数量。
- 与此前另一高度既有连接器回传3,531,690相比累计计数差908；两者不是同一单次前向观察窗口的快照，**不可**拿来冒充两次三秒内新池发现、实时进入时间或完整V2/V3/Four.meme覆盖。
- 固定区块静态读取能力成功，不等于前向采样器在Mac完成了真实原字节采集、时钟/延迟验证和20请求预算验证。

**更新的准入判断**：无钥公共端点`eth_chainId`与Mac`eth_blockNumber + eth_getBlockByNumber + eth_call`前置检查已按用户回报通过，因`MONSTER_BSC_ARCHIVE_RPC_URL`缺失造成的**静态读取能力阻断已消除**；正式运行时仍只能通过一次性进程内环境变量传入公开无钥URL，不需要创建`.env`、配置私钥或改变现有Alchemy账户。但真实一次性前向`--manual-once`仍**尚未授权、尚未执行**；开始前必须重新检查当时Mac CPU/内存与私有数据目录、确认限流/失败止损，并由用户明确单独批准。因此状态为`APPROVE_OFFLINE_CODE / PINNED_RPC_PREFLIGHT_PASS_USER_REPORTED / MANUAL_PILOT_AWAITING_EXPLICIT_AUTHORIZATION`；不能声称`PIT_VERIFIED`、P0来源已过门槛或P1可启动。历史`2026-11-02`终止日、免费$0预算与`NO_DEPLOY/NO_SCHEDULE/NO_TRADE`不变。

## 2026-10-23：用户明确授权恰好一次 Mac 前台真实只读采样（待Mac实际执行）

用户在知悉两次 Mac 公共 RPC 预检查分别已回报 `eth_chainId=0x38`、固定块 `129174690` 与 V2 Factory计数`3,532,598`，并在上一轮被明确询问“是否授权执行这一次 Monster 前台只读采样”后，**明确回复“授权”**。因此本条将前次`MANUAL_PILOT_AWAITING_EXPLICIT_AUTHORIZATION`限定性更新为`ONE_MANUAL_FOREGROUND_PILOT_USER_AUTHORIZED_NOT_EXECUTED`，不是常驻监控、扩大母体采集或自行多次重试的授权。

**唯一许可的执行边界**：
- 固定已实际通过115项Mac离线测试且独立二审APPROVE的运行源码提交：`c646d438ebdd33183e047e47323315d78aab2869`（`forward_observation.py` blob `5e41458eb199599a861498260bda895f525fb1b6`）；不使用后续未经审核的代码替换它。
- Mac 终端中**一次**`python3 -m mission_agent.early.forward_observation --manual-once --out-dir <新建且不存在的私有子目录> --pause-ms 0`；进程专用、无需API Key的公开URL `MONSTER_BSC_ARCHIVE_RPC_URL=https://bnb-mainnet.g.alchemy.com/public`。0ms仅表示两次快照之间不额外休眠，实际采集会计算并强制不超过3秒的计数响应间隔；无后台daemon、无重试，无其他Provider fallback。
- 最多20个白名单`eth_chainId/eth_blockNumber/eth_getBlockByNumber/eth_call`调用；单次HTTP请求完整截止20秒。只接受正确链、同块状态与祖先一致性；链重组、实际窗口超限、HTTP限流或响应缺损应明确生成`failure.json`，**绝不**因此默许重试第二次采样。
- Mac运行前重新检查CPU/内存/剩余磁盘，保证只读且不干扰现有项目；归档写入`~/Library/Application Support/MonsterResearch/forward-observation/`之下独占新目录（0700）和私有原响应（0600）。不将原HTTP响应文件、全部manifest或任何RPC凭据直接推Git；仅在检查完全不含秘密后贴脱敏计数与失败代码。
- 不安装/更改launchd或cron，不付费，不签名/交易，不转账，不合并，不部署、不重启任何生产服务，不修改历史P0样本或买入金额。失败则结束，继续分析现有证据，不因本条授权再次实跑。

**重要真实性状态**：截至记录本段时，由于ChatGPT会话无法直接控制用户Mac，**尚未执行**上述采样命令，也没有任何真实本地原HTTP响应归档得到验证。用户随后实际回传的单次运行产物（成功或失败）必须按固定SHA、每请求sha256、接收完成UTC与单调间隔离线审查；任何`Factory`计数变化只能解释为此次短窗的单源观察，不得冒充可交易新币、完整母体或PIT来源终审。历史2025`available_at`仍UNKNOWN，`P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`及2026-11-02历史来源停止日不变。

## 2026-10-28：用户批准下一次有界前台只读BSC新池观察研究（非持续监控）

用户上传本日Mac的15份原始RPC回执，15/15响应SHA一致，130232809→130232814五块父hash连续，两次Factory累计Pair均3575553，2.210秒有效计数窗delta=0。用户获知2秒短窗不足以积累新池证据，并同意下一轮固定时长、固定RPC预算、手动启动的前瞻试验。本次授权限于**在现有模块准备该一次性前台研究与离线验收**；不授权本助手访问/后台运行用户Mac、自动定时、生产部署、交易、邮件、付费或改变旧2025历史P0。之前2026-10-22的审批历史事实原文保留。

**硬上限**：原 `forward_observation.py --manual-once` 仍是20请求/两快照的旧模式。新增 `--manual-bounded` 为一次前台、最多180秒目标观察、最多180个只读RPC调用、每12秒轮询、最多12条Pair身份且每相邻区间最多3条。沿用原有 `eth_chainId`/`eth_blockNumber`/`eth_getBlockByNumber`/`eth_call` 白名单，无钱包签名交易。单次HTTP最长20秒，所以最后一次在途请求可能使实际进程超过180秒；原始单调时钟与完成UTC必须真实记录，不能宣传严格180秒绝对截止。免费公开RPC若限流，停止且不换来源、不自动重试。

**有效性**：同块计数与header两次检查、上一观察块在下一周期再次核对、两块之间逐区块parentHash关联（间隔超过24块直接 fail-closed）。新增Factory索引身份仅在后一观察的固定块上读取 `allPairs(index)`、`token0()`、`token1()`。每个原始RPC响应体以私有权限保存，伴SHA256、调用UTC、完成UTC、单调时钟；任何错链、重组、超预算、时钟异常和截断只留下 `failure.json` 而非可评分manifest。超出身份额度的索引**保留未读起止与计数**，不能把未读计为零；索引范围采用常数空间记录，不展开大列表。原raw只存用户Mac，不上传Git。

**阶段状态**：代码与离线假RPC反例已在既有 `mission_agent/early/forward_observation.py` 和 `tests/test_monster_forward_observation.py` 增量提交；尚未取得该新模式的真实Mac单测PASS、独立外部审核或真实前台新池样本。不得把已写代码当作上线成功。其专用子类请求上限不会放宽原Four.meme共享传输的50调用限制。旧2025-07-01历史P0仍 `INSUFFICIENT_COVERAGE`，P1 `BLOCKED`，Monster `G6 NO_GO`，Frank不动。

## 2026-10-28：Mac 35/35 PASS 后发现并纠正 BSC Fermi 0.45s 出块速率与预算冲突

用户实际在Mac对首次有界模式固定SHA `89427e1644d0eec23bbe72bf3cf509c1dd610dbf` 执行35项离线测试，提供逐项 `ok` 与 `Ran 35 tests in 0.055s / OK`。这是用户原终端报告，不代表本助手独立执行测试，也不覆盖真实链上出块频率压力测试。

来源一手核验：BNB Chain Fermi 主网已采用约0.45秒出块间隔，官方 https://docs.bnbchain.org/bnb-smart-chain/overview/ 与 https://www.bnbchain.org/en/blog/fermi-hard-fork-accelerates-bsc-to-0-45-second-block-times 公开说明。此前默认12秒采样会跨约27个区块（不含网络延迟），与 `MAX_BOUNDED_ANCESTOR_BLOCKS=24` 直接冲突，故 **35/35 不能授予真实3分钟采样运行放行**。

不削弱实际跨区块父哈希完整性条件的限量修复：`--manual-bounded` 默认间隔从12秒缩短为 **5秒**，24区块祖先最大深度、180总RPC/180秒最大目标观察时长、12个Pair身份与单段3个身份限制不变，显式拒绝传入12秒间隔。根据0.45秒估算5秒内约11块，但节点请求耗时及限流可能超24块，届时依然必须 fail closed。**重要：180次读取无法保证完整核验3分钟内约400个区块，必须允许在 `RPC_BUDGET_SAFETY_RESERVE` 触发时提前停止，并如实展示已验收区间、实际耗时与未覆盖尾段；不能宣传‘已经持续覆盖3分钟’，也不能借此放宽PIT。**

新代码固定提交 `31f875e2b31c4f9e48002958e1020286266a1914`，专项测试数量增加为37，新增模拟0.45秒出块与拒绝旧12秒间隔。**截至本文撰写，新37项尚未有Mac真实运行PASS；不得启动新实测，也不得因GitHub其他Baseline CI PASS冒充这37项成功。** 该修复属于来源覆盖完整性的必要定向改动，待本地专项测试与必要独立审查，不新增workflow、调度或交易。

## 2026-10-28 14:32 (Asia/Bangkok)：37/37 Mac 离线PASS，但真实有界源测试被跨块速度阻断

**实测用户终端**：冻结提交 `8c8da2f2b5ad8e2eeb89ab7719ec76a4f68aecc0` 的 `test_monster_forward_observation.py` 37/37 PASS（`Ran 37 tests in 0.067s / OK`）；紧接着按其 `--manual-bounded` 在真实Mac前台采集返回 `ForwardProbeError: ANCESTRY_EXCEEDS_BOUNDED_DEPTH`。用户另传原始本地 ZIP：`monster-bsc-bounded-20261028T073230Z.zip`，大小 **122910字节**，SHA256 `692a5119a83f29b2370f6fe13ce410926e751e34a527dc379994724a723b4925`，包含29个原RPC JSON以及 `failure.json`，而非成功manifest。本人在本回合离线读取29/29原文件，逐个核对`raw_sha256`、`raw_bytes`、递增ID、响应体，**29/29均一致**；这证明用户文件内部一致，不是来源数字签名认证。按照早期原raw本地不进Git边界，此处仅登记原包SHA/范围，不上传含逐请求回执的ZIP。

**可归因的失败路径**：实际固定块计数序列 `130241864:3575982`，`130241879:3575982`，`130241910:3575982`。第一段跨15块，原原始回执 `130241865..879` 父hash连接且前后头锚重查一致，但逐块核查耗费约6秒；其间BSC继续生产区块，第三次head比上一点跳增31块，超过 `MAX_BOUNDED_ANCESTOR_BLOCKS=24`，脚本在第29次RPC后 fail-closed，只输出 `failure.json`。**当前不能把前段局部成功包装为整轮 `PIT_VERIFIED`，真实新池身份/流动性/成交仍0**。文件内29次方法：1 `eth_chainId`、3 `eth_blockNumber`、3 `eth_call(allPairsLength)`、22 `eth_getBlockByNumber`，没有交易发送/签名。此问题不是简单将轮询从12秒调至5秒就能根治：串行多次约0.42秒HTTP耗时造成新块增长。

**净新增信号只作后验范围统计**：此前2026-10-28约06:24UTC的单次V2 Factory计数3575553，与此次约07:32UTC的计数3575982相差 **429 Pair索引**。两次均为真实原响应但相隔约68分钟、没有连续块日志覆盖，不能称为当时已捕获429个token、429个可交易机会，不能声称任何profit信号。

**根因优先下一个验证**：为保留完整ParentHash链与0美元来源，需先单次前台只读确认原BSC公共RPC是否接受小规模（例如2个显式高度）的`eth_getBlockByNumber` JSON-RPC batch。Geth官方 `https://geth.ethereum.org/docs/interacting-with-geth/rpc/batch` 描述batched请求能节约网络延时，但**不能据此认定此BSC公开端点已通过验收**。若实测支持，再在现有观察器/测试内做严格每子请求编号、响应条数、hash链、总方法调用次数与原raw SHA的限额实现；若不支持，接受严格连续观察在180请求内难覆盖3min的硬限制并停止此方案，不通过跳过父hash/加付费或抬请求额度掩盖PIT缺口。此轮未执行新批量网络测试。

**操作侧独立错误**：先前给Mac打包命令用了 `status=$?`，而zsh的 `status` 为只读特殊参数，故另见 `zsh: read-only variable: status`；这与链上RPC失败没有因果关系，今后用 `capture_exit_code=$?`。保留失败ZIP、不重采伪造成成功。

**不变门禁**：旧历史P0 `INSUFFICIENT_COVERAGE`，P1 `BLOCKED`，G6 `NO_GO`；新模式 `LIVE_BOUNDED_FAILURE_CONFIRMED / BATCH_PROVIDER_SUPPORT_UNVERIFIED`。不启动定时、付费、生产邮件/交易，不改Frank。
