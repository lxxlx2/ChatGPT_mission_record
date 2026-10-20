# Frank 方案 3：P3 本地证据页和模拟提醒预览（2026-10-20）

状态：`P3_OFFLINE_PREVIEW_IMPLEMENTED / CI_AT_NEW_SHA_UNVERIFIED / DASHBOARD_RUNTIME_INTEGRATION_NOT_STARTED / MAC_ACCEPTANCE_NOT_STARTED / PRODUCTION_NO_GO`。

## 已实际提交的独立能力

- `local-agent/mission_agent/mission_control/intelligence_preview.py`：新的单独离线入口，复用 #146 的 `analyze_candidate()`，生成本地独立 HTML 证据卡片；显示 CA、V1 来源信号、已核实最新方向与时间、模型 episode 状态（显式声明不是链上当前余额）、可用的同币种价格参考差异、行情来源时间和无法核实的数据。支持离线筛选、CA 复制、严格格式限定的 Solscan 链接。
- 入口须由用户**明确**指定已有候选 JSON，或明确提供现存 Frank production-root 后只读访问 `forward.sqlite`。没有自动生产目录探测。CLI 在用户运行时生成静态文件，不会启动服务，不会访问网络、Jupiter、RPC、Gmail、macOS 发送器或生产 outbox，也不会修改现有 SQLite、V1 提醒、策略或通知规则。
- `fake_intelligence_updates()` 只输出模拟对象，不实现任何真实通知提供方；首批只针对**有来源签名、在显式新鲜度窗口内的 SELL** 标记 `INTELLIGENCE_UPDATE / FAKE_PREVIEW_ONLY_NO_SEND / send_allowed=false / channels=[]`。原 ACCUMULATION/MULTIPLE 不被转发到此预览。无主动核实的卖出、过期、价格缺失不推送假警报。以 mint + signature + 事件时间 + 事件类别生成稳定指纹，批内去重；可使用 `--previous-fake-json` 对历史模拟结果进行跨次去重（只读以前结果，无正式 outbox）。
- `local-agent/tests/test_frank_amount_free_preview.py` 新增定向测试覆盖卡片价格与缺口、BUY 不重复提醒、已核实 SELL、过期与未来时点、去重、危险 HTML 输入及本地 CLI 文件生成。

## 在仓库内运行（必须有合法本地数据，独立运行）

```zsh
cd crypto-300-profit-mission/local-agent
python3 -m mission_agent.mission_control.intelligence_preview --candidate-json /absolute/path/to/your-local-candidates.json --output "$HOME/Downloads/frank-intelligence-preview.html" --fake-out "$HOME/Downloads/frank-intelligence-fake.json" --max-market-age-seconds 300 --max-event-age-seconds 600
```

替换上面的候选 JSON 实际绝对路径。此参数只读用户显式指定的文件；输入是 `FrankReader.candidates()` 返回的候选对象列表。需要引用本地**已存在**运行数据库时，改用 `--production-root /actual/Frank/root`，不需要、也不应创建新 RPC 配额或实时网络采集。可选 `--market-json` 接受以 mint 为键的来源化离线参考行情对象，缺省一律为 PRICE_UNAVAILABLE。

命令中的 300 和 600 是本次离线查看者**显式输入**的数据新鲜度界限，仅决定比较或模拟预览，不是已批准的交易、策略、自动发信阈值；可以按演练需要更改，不能擅自上线这些数值。

```zsh
python3 -m pytest -q tests/test_frank_amount_free_preview.py tests/test_frank_amount_free_intelligence.py
```

上述为可执行的测试命令，**本次创建文件之后尚没有验证其真实输出**；必须以后续真实 CI 或本地执行记录为准。

## 未完成 / 真实阻断等级

1. **P3 PARTIAL**：现有本地 HTML 已实现，但尚未加入运行中的 Dashboard 路由。此时不能说用户 Mac 已有新页面。要与已有 D1/D2 Dashboard 集成时须再核对 PR #128/#138/#139 文件归属，避免覆盖冻结 V1 和受保护通知代码。
2. **P3 PARTIAL**：模拟提醒是只读 JSON 与 HTML 展示，不等于已获新提醒发送授权；独立实际发送队列尚未设计、审核、安装。首批只覆盖 SELL，不会自行 invent 价格追高/流动性风险等级。
3. **P4 NOT_STARTED**：尚未完成至少 10 条有证据的端到端历史案例、新 HEAD CI、独立 SHA 审核、用户 Mac 隔离运行与视觉验收。
4. **P5 BLOCKED_BY_AUTHORIZATION**：无任何用户正式新策略签名、合并、部署、重启或真实本地/Gmail 发送授权。

## 文件责任和下一轮

本轮只写新 P3 `intelligence_preview.py`、`test_frank_amount_free_preview.py`、本进度文档。#146 原有 `intelligence.py`、`test_frank_amount_free_intelligence.py` 和 P1 历史调查文档均未修改；Codex 所在 #117 及既有 PR #111/#112/#138/#139/#142 未改。

下一轮先取得本次 HEAD 的真实 CI/test 结果，核对 HTML 在隔离 fixture 的真实输出，再按固定 SHA 组织一次独立审核。仅在确认现有 Dashboard 的文件所有权及集成契约后接入只读路由；正式消息队列和生产切换继续独立审批。不重做 G1/D1/D2，不扩大 RPC，不修改或重发旧通知。
