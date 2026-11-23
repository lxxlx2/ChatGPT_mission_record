# FLOP / Mac 本地 Agent 收益研究、看板与首次验证

状态（2026-11-23）：READ_ONLY_OFFLINE_PASSED / REAL_TESTNET_NOT_EXECUTED / NO_DEPLOY。
这是阶段 A 的只读观察与首次验收工具，还没有通过真实 Testnet 支付与计分验收，不能称作已上线的空投机器人。

经济研究见 ../flop-network-agent-earnings-due-diligence-20261123.md 。

## 目标与功能

真正的收益目标是尽可能多地获得属于自己钱包、已经最终结算且能够符合官方计分规则的 Testnet 推理消费。不得臆造每日四次等上限；Testnet Faucet 配额、评分非线性限制和最终可卖出收益目前未知。

现有代码只有 Python 3 标准库，无需额外付费 AI API。可以：
- 只读查询官方 GitHub commits 与 releases，记录去重的技术证据及 SOURCE_GAP。
- 用用户本机 SQLite 记录观察项和未经独立核验的支付报告；导入的收据始终标为 UNVERIFIED，不可冒充积分。
- 在 http://127.0.0.1:8765 提供本地看板，展示来源、收据、验收状态、未知收益以及按实际 Faucet 配额和 Miner 报价动态计算的理论可执行次数。
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
