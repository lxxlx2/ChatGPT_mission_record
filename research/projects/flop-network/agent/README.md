# FLOP / Mac 本地 Agent 收益研究、看板与首次验证

## 2026-11-28：首次真实直连回执与重复领取接续

- 用户终端实测 CLI 0.10.3：一次外部矿工 force-open / Qwen3-1.7B / 0.005 Test FLOP escrow / 1200s / 32 output tokens，cooperative=true、verified_turns=1、exit=0，实际链上 channel list 返回 closed，余额由 10 变为 9.986563858475。此为用户实测回执；自动核账仍须独立确认 exact finalized extrinsic 与 Settled 事件，不能把该日志直接计入已验证收益。
- manual_import.py 一次性把已有本地 CLI JSON 回执关联当前已核验 grant，落库为待核验，重跑同一交易幂等；不签名、不开新通道、不创建钱包。不覆盖不同的已有 session。
- 旧代码遗漏 settle_tx 字段且假定 validator/audit fee 同在 Settled 事件。依据官方 https://docs.flop.network/docs/send-to-specific-miner 的 D-0403 cooperative close 全额消耗 escrow，核验 exact tx、成功事件、同一 channel、minerPaid>0、cooperative=true、closed storage、付款及矿工地址、openedAt、escrow 和预算。先定位 closed 状态变化的 finalized block，失败再按原有 bounded scan cursor 回退。未知数据不计分或重付。
- CLI 0.10.3 已纳入明确版本表；新版 session 使用 1200s lifetime、32 tokens。公开 offer discovery 不可用时，仅使用本钱包已经核验成功过的 operator-opted-in 路由；每次读取新 info-proof 并对比 chain account/genesis/model/enclave fields。该 preflight 不独立做密码学签名验证，CLI/SDK 会在会话中校验 finalized channel key 和收据；只允许单次 0.005 测试 FLOP escrow 加手续费，不盲重试或扩大付款。已知路由不可用时等待。
- 24h 与已核验消费满足且 Faucet 当前允许时，原 tick 才推进下一轮 nonce；官方拒绝则按原错误状态处理。Testnet 计分仍未确认，无历史补计。不得将测试消费视为收益。
- 2100s direct-session subprocess 限时；看门狗仅在存在近期提交 journal 且原 runtime 锁实际被占用时接受较长 tick，超时或锁消失仍报警。既有 launchd 与 08/20 Asia/Bangkok 邮件不变。
- 基线 9697832044f1a99cd302d6870a09bfac4a4931a5 已有用户 55/55 离线 PASS。新增代码尚未在 Mac 运行，不声称新测试或第二次领取通过；不要重新 bootstrap（历史文档的旧 CLI pin 过时）。先验收代码、导入现有回执，再恢复原服务。无需手动再支付一次。


## 2026-11-24 当前线上修复：端口冲突与 launchd 退出码 1

实际 Mac 诊断：
- 8765 和 8766 均有其他或旧进程监听，调用 /api/health 都返回 HTTP 404，不能当作 FLOP Agent 在运行。
- 原有 FLOP dashboard LaunchAgent 为 spawn scheduled，执行次数 105，最近退出码 1。
- 禁止再反复改旧端口、kill 未确认进程或重装全部任务。

当前正式修复命令为从 GitHub 固定 SHA 检出后执行 python3 rebind_dashboard.py --apply。它只检查且原位重载已存在的 com.<uid>.flop-agent.dashboard，保留已存在的 tick / Gmail / 测试钱包 / Technocore。脚本从 18766 至 18795 选择当前未占用的本地端口，写入原 dashboard plist 的 FLOP_DASHBOARD_PORT 环境变量。启动后必须证明：
1. 首页带 ?utm_source=chatgpt.com 返回 HTTP 200。
2. /api/health 返回 service=flop-dashboard, build=flop-dashboard-dynamic-port-v3, source_path 为稳定 Git checkout, port 等于选择的端口, git_head_sha 为固定 SHA，PID 为正在响应服务的进程。
3. 验收成功后才写入 chmod 0600 的 ~/.local/share/flop-agent/dashboard-bind.json。失败则恢复旧 dashboard plist 并报告具体状态，绝不宣称服务成功。
4. 原有每 5 分钟的 tick 任务会根据 dashboard-bind.json 独立检查 HTTP 健康；服务不可用或身份不匹配，生成去重 Gmail 故障告警。摘要及首次测试邮件仍在原先独立 outbox 中。

与其他项目发生端口冲突时，必须优先查询监听 PID 和命令，禁止杀死 Technocore 或其他无关服务。端口由本次实际成功返回决定，不要猜测一定是 18766。

正式一次性 Git 命令以及固定 SHA 以最终对话中的实际已验收提交为准。


## Mac 一次性升级入口（2026-11-24 新版）

一条完整的 Mac 命令块完成一次性更新，基于固定 Git SHA 从 GitHub 建立稳定 checkout。
- 固定源码目录：用户目录的 Library/Application Support/FLOPAgent/mission；
- 重用现有 ~/.local/share/flop-agent 的 OAuth 指针、独立邮件队列和 SENT_VERIFIED 首次测试，不重复发送相同测试邮件；
- 首次创建专用、持久、加密的 sr25519 测试网签名账户，密码以 chmod 0600 保存在本机，绝不输出助记词。重复运行不能更换账户；
- 原位升级现有两个 FLOP launchd 标签，加入 NVM PATH 并将原临时目录更新为固定目录。失败时尝试恢复旧 plist，不创建额外监控；
- 使用 CLI 0.8.0 的 Network Status JSON：曼谷 14:00 起检查真正的 Testnet。仅官方页面标记为 live、RPC genesis 严格匹配、Faucet ready 且 matches_rpc 后自动尝试首次 Faucet；提交前记录不可重复身份，结果不明确绝不盲重试；
- 现有看板服务兼任独立健康看门狗：超过 15 分钟没有调度 tick 时发错误邮件。08:00/20:00 摘要在 Mac 睡眠后补发最新未发送时段；
- 首次真实推理成功邮件要求独立链上 payer、Miner、实际消费、最终结算的完整证据，不能仅依赖 CLI 退出码。

**仍未完成的真实网络环节：** 官方 Testnet 目前仍标 planned，实际可用的 Miner 直连 Endpoint、模型报价、完整 Agent 身份积分归属 API 尚未公布或核实。当前实现可以自动等待开网、创建本地钱包并首次请求 Faucet；实际付费推理、最终性核验和之后的长期有效消费尚未通过，必须在官方发布可验证数据后继续验收，不能声称全部自动赚钱已完成。

一次执行的 Mac 命令（正式完整 SHA 以最终交接消息为准）：

    set -e
    SHA=REPLACE_WITH_VERIFIED_FULL_SHA
    DEST="$HOME/Library/Application Support/FLOPAgent/mission"
    mkdir -p "$(dirname "$DEST")"
    if [ ! -d "$DEST/.git" ]; then
      git clone --filter=blob:none --no-checkout https://github.com/lxxlx2/ChatGPT_mission_record.git "$DEST"
    fi
    git -C "$DEST" fetch origin "$SHA"
    git -C "$DEST" checkout --detach "$SHA"
    cd "$DEST/research/projects/flop-network/agent"
    python3 -m unittest discover -v -p 'test_*.py'
    python3 bootstrap.py --apply
    python3 runtime.py status

如果首次生成账户，结果只输出公开 SS58 地址和状态，无助记词/密码。Mac launchctl 接受启动不等于真实付费推理成功，必须以本地 tick 及有效结算证据为准。无额外 OpenAI、Claude 或 Gemini API 要求。

## 历史分步说明

后文更早的手动操作仅供审核。已有 FLOP launchd 时不要再次执行 install.py --apply；请用上面的 bootstrap.py --apply 原位升级。


状态（2026-11-23）：READ_ONLY_OFFLINE_PASSED / REAL_TESTNET_NOT_EXECUTED / NO_DEPLOY。
这是阶段 A 的只读观察与首次验收工具，还没有通过真实 Testnet 支付与计分验收，不能称作已上线的空投机器人。

经济研究见 ../flop-network-agent-earnings-due-diligence-20261123.md 。

## 目标与功能

真正的收益目标是尽可能多地获得属于自己钱包、已经最终结算且能够符合官方计分规则的 Testnet 推理消费。不得臆造每日四次等上限；Testnet Faucet 配额、评分非线性限制和最终可卖出收益目前未知。

现有代码只有 Python 3 标准库，无需额外付费 AI API。可以：
- 只读查询官方 GitHub commits 与 releases，记录去重的技术证据及 SOURCE_GAP。
- 用用户本机 SQLite 记录观察项和未经独立核验的支付报告；导入的收据始终标为 UNVERIFIED，不可冒充积分。
- 在 http://127.0.0.1:8766 提供本地看板，展示来源、收据、验收状态、未知收益以及按实际 Faucet 配额和 Miner 报价动态计算的理论可执行次数。
- 运行完全离线的 first-test 和 4 项单元测试，检查持久化、去重、数据完整性。
- 以只读 FLOP CLI preflight 尝试读取 Testnet 网络状态，不能将“接口响应”当成实际参与成功。

没有实现、不会偷偷执行：DID/钱包创建、Faucet 请求、链上签名、真实推理、支付、私钥读取、任务定时安装、邮件通知和资产交易。

## Mac 命令：从 Git 固定 SHA 隔离执行

把最终报告中的完整 40 位提交 SHA 填入两处 FIXED_SHA，命令兼容 macOS zsh；不要在正在运行的 Mission/Frank 原工作区执行：

    WORK_DIR="$(mktemp -d -t flop-agent)"
    git clone --filter=blob:none --no-checkout https://github.com/lxxlx2/ChatGPT_mission_record.git "$WORK_DIR/mission"
    git -C "$WORK_DIR/mission" fetch origin FIXED_SHA
    git -C "$WORK_DIR/mission" checkout --detach FIXED_SHA
    cd "$WORK_DIR/mission/research/projects/flop-network/agent"
    python3 agent.py first-test
    python3 -m unittest -v test_agent.py
    python3 agent.py collect
    python3 agent.py status
    python3 agent.py preflight
    python3 agent.py dashboard

前六个 Python 命令中只有 collect/preflight 会访问公网，只读且无付费或链上写入。最后 dashboard 前台运行，以 Ctrl+C 停止。不会在机器上安装 launchd。

## 首笔真正的 Testnet 推理验收（尚未执行）

1. 官方 Public Testnet 实际激活，获取 canonical genesis、RPC、spec 版本、CLI 发布版及实测功能；2026-11-24 计划时间不算上线证据。
2. 用官方工具在 Mac 上创建独立测试钱包与 DID，密钥仅保存在本地加密目录和 Keychain，绝不与现有资金钱包/Claude/Codex 复用。
3. 查询 Testnet Faucet 当时真实额度和流控，定位健康、独立且可连接的 Miner 与精确模型哈希/会话报价，核实当前 CLI 的 session run 参数。
4. 获得一次单独的测试币消费授权，以用户钱包为付款人，提交一次有明确上限的真实推理，不走无法归属积分的 Gateway。
5. 核对 finalized channel、opening account、payable、签名回执、实际费用、退款及是否进入计分记录。任何超时/未知结算必须停止和核账，绝不自动重试付款。
6. 只有首笔端到端 PASS 后才可开发直接支付适配器、动态 Faucet 获取、自动消费与最终性核验；正式 macOS launchd 常驻部署需要另外授权。每次先保留证据，在可归属和流控范围内提高有效消费，绝不为次数刷任务。

## 成本与接口

Mac M4 Max 48GB 作为 Agent 客户端足够，不需要本地 NVIDIA GPU。当前源码调用 Python 标准库与公开 GitHub API，不需要自己的 OpenAI、Claude、Gemini API，也不产生 FLOP 费用。正式推理会消耗 Faucet 提供的非可交易 Testnet FLOP，并可能消耗链手续费；最终配额未公布。若你使用 Claude/Codex 协助编程，其订阅/API 消费是可选的、和 FLOP 推理不同。真实 FLOP 价格与最终空投的可售价值未知。

## 已做和未做的验收

- 在隔离 Python 环境跑过 first-test：PASS_OFFLINE。
- 4 个离线 unittest：PASS。
- 本地 dashboard GET / 与 GET /api/state：HTTP PASS。
- 没有用你的 Mac、钱包或真实 Testnet 做测试；没有验证链上最终性、Faucet 或空投积分。
- 不将源代码通过 ZIP/附件交付，只用 Git commit/PR + 固定 SHA。

官方依据：
https://docs.flop.network/docs/agent-onboarding
https://docs.flop.network/docs/testnet-and-timeline
https://docs.flop.network/docs/agent-integration
https://flop.finance/intro/yellowpaper/
https://github.com/flop-labs/network/issues/229
https://github.com/flop-labs/yellowpaper/issues/172

仓库权限边界：AGENTS.md；docs/DEVELOPMENT_RULES.md；crypto-300-profit-mission/PROJECT_ANALYSIS_EVIDENCE_WORKFLOW.md。NO_GO 仍有效。


## 2026-11-24 FLOP 本地自动检查、真实邮件与首次测试通知

本目录新增：
- runtime.py：曼谷 2026-11-24 14:00 起自动检查是否真正开放 Testnet。每 5 分钟执行一次，无实测网络配置时不做链上写入。只有官方网络状态、RPC finalized genesis 与用户专用本地配置一致，才可能尝试首笔真实推理。
- mail.py：复用用户 Mac 已有的 OAuthGmail 授权，通过 Gmail 实际 SENT 标签及完整消息内容回读验收；独立邮件队列，不影响 Frank；发送过程不明确时不自动重复。
- install.py：显式 --apply 在 Mac 创建两个独立 LaunchAgents（定时 tick、只读看板）。安装前强制发一封邮件测试，必须 SENT_VERIFIED 才可安装。
- test_runtime.py：模拟 Gmail Sent/失败/去重、危险结算停止和首次测试成功通知条件。GitHub CI 工作流自动检查。

邮件：
A. 首次邮件测试：安装时发一封 [FLOP] 邮件通道首次验收；核对 Gmail Sent label、唯一身份标记和正文哈希；通过才会安装启动任务。
B. 首笔真实测试成功：仅在自有钱包付款、独立 Miner、实际推理消费、真实 finalized settlement 及完整链上证据通过后发一封 [FLOP] 首次真实推理测试成功。此事件没有在现实中发生；当前源码虽有状态转换与邮件代码，但尚无正式 Testnet 可用的独立链上验证适配器，因此不能把 CLI 0 返回码冒充成功。
C. 正常状态报告：曼谷 08:00 和 20:00 发送，含实际已核验消费、成功和未知结算次数、最近成功时间、Faucet 额度是否可查、关键异常和邮件投递状态。错误每个 5 分钟 tick 检查，首次发现尽快发告警，相同错误按小时去重。

看板：http://127.0.0.1:8766 。它显示实际验证后的结果，始终将未知余额/收益标为未核实。

## 从固定 Git SHA Mac 隔离检出后执行

请先用本机已经授权的 Frank Gmail OAuth 文件配置 FLOP 邮件。现有 Frank 本地配置 gmail-existing-source.json 中记录现有 existing_oauth_file 路径。Mac Codex 可在本机读取，不得将令牌、密钥或文件正文发到聊天或 Git。以下 OAuth 文件路径必须是本机真实路径：

    python3 install.py
    python3 install.py --apply --existing-oauth-file "$EXISTING_OAUTH_PATH"
    python3 runtime.py status

运行 install.py 不带 --apply 只有规划展示，没有副作用；带 --apply 会发送一封真实邮件并进行 Sent 回读，通过后才创建本地 launchd，故只在明确授权并备好 OAuth 时执行。

有独立的 Testnet 钱包和正式网络数据后，在 Mac 的私有文件 ~/.local/share/flop-agent/private-testnet.json 创建 chmod 600 的配置。字段 network=testnet, expected_genesis=官方 0x 64位哈希, wallet=自有地址, keystore=本机私有钱包文件, miner=公开独立 SS58, endpoint=真实 HTTPS Session endpoint, model=已登记模型 slug, max_flop=经实测报价确定的单笔上限, total_test_flop_budget=单独授权的测试币预算。CLI 从系统 Keychain service flop-agent-wallet-password 读取私钥密码，只在当前进程内存中使用。

官方 Testnet 目前仍为 planned，正式 genesis、RPC、Faucet 限额、Miner 身份尚未核实。禁止用 Devnet 的虚拟值或历史配置填充测试网配置。Mac 睡眠、关机或未登录会使本地 LaunchAgents 无法在预定时刻执行。所有实际钱包签名要以 Testnet 固定身份、预算和已通过邮件通道为前置门禁。

当前实现的长期自动运行包括只读开放状态检查、Gmail 半日摘要、错误告警与看板；真实自动推理在首笔独立链上核验前保持阻塞。它尚不具备真实的长期赚钱能力，严禁声称已经开始计算空投。仍保持 NO_GO 交易环境，不触碰其他监控。

## 2026-11-26: signed first-grant adapter (pending isolated verification)

Pinned official CLI 0.9.0 supports signed D10 faucet request with --nonce. Existing test-only encrypted wallet is preserved. Current official Testnet page parser recognizes the live/unscored format. First grant uses a persisted nonce and 15-minute minimum reconciliation delay; legacy attempts without nonce require review. A CLI finalized report is not independent chain verification. No subsequent grant or inference is authorized by this adapter; scoring, miner discovery, independent settlement and spend eligibility remain unimplemented. Existing launchd cadence and mail remain unchanged. Review and run isolated tests before deployment. Source: https://www.npmjs.com/package/@flop-labs/cli?activeTab=dependencies ; https://docs.flop.network/docs/network-testnet .

## 2026-11-26: claim visibility

08:00 and 20:00 Bangkok digests and the current dashboard show the persisted first-claim status, transaction hash, reason, wallet balance sampled via pinned CLI, public faucet budget and pending grants. A reported balance or a CLI-finalized receipt does not prove independently verified transfer attribution. No new scheduler or new wallet. When the HTML page cannot be parsed, the canonical faucet chain and limits plus pinned CLI may establish funding readiness only; no scoring or paid inference promotion. Prior ad164086 isolated Mac tests: user supplied 44 PASS; new changes not yet tested. Deployment of prior SHA and faucet recovery reported by user; first grant not verified.

## 2026-11-26: first funded balance and finality fallback

User local CLI reported 10 free Test FLOP; initial nonce receipt still unresolved (exit 1). This proves a reported positive wallet balance, not independently finalized faucet transfer attribution. The WS finality probe had no observation; the official HTTPS RPC is now a fallback with fresh genesis/head/header verification. Positive balance produces a deduplicated first-funding notification distinct from claim finality. Existing same-nonce-only policy, schedule and wallet preserved. New tests authored, not run here. Previous deployment b0b855bf confirmed by user; no new claim or spending executed from research.

## 2026-11-26: recurring Testnet cycle implementation candidate

Existing scheduler now calls cycle.py after funding observations. Original initial nonce is retained. Independently verify a finalized faucet transfer and actual settlement extrinsic using chain_verify.cjs (official HTTP RPC and installed CLI's @polkadot/api dependency). Discover signed offers on the Testnet explorer only, require venueVerified, exact registry identity, explicit quote units and public HTTPS endpoint; offer-only sessions, 0.1 Test FLOP cap and 0.2 reserve (pilot engineering defaults, not protocol requirements). Preserve all session attempts and halt on unknown payment. A second nonce is allocated only after verified qualifying spend and a rolling 24h cooldown; the server remains final arbiter of eligibility. No new service, wallet or real funds. Official current guide states no Testnet inference and no scoring block; live offer/schema and settlement adapter are not verified. Missing schemas/dependencies fail closed. New tests not run by author; user local 44 PASS refers to ad164086 only. No claim of unattended live success until real finalized cycle and rollover are observed.

Sources: https://flop.network/llms.txt ; https://docs.flop.network/docs/send-to-specific-miner ; https://github.com/flop-labs/network/issues/229 .

