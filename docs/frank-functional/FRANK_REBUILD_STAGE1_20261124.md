# Frank 重做第一阶段：买入入口与离线准入

基线：`4382bab130d005aa039402876da736edb47eaf30`。范围为 S01–S04、S06–S07、S10 的首段实现，不是整阶段或生产验收。

| 编号 | 首段交付及可重复证据 | 剩余 |
| --- | --- | --- |
| S01、S06–S07 | 默认进入「Frank 买入」。同一只读流水按链上时间、完整 Mint 和稳定游标读取，原币金额不换算；可复制 CA、进入既有 CA 查询及打开原交易。旧信号入口改为「历史与审计」，仍可回查。HTTP 测试走真实 Handler，浏览器脚本测试检查默认布局、空态、转义、查询按钮和无行情请求。 | Mac Chrome、真实同步水位和真实钱包覆盖未验收。 |
| S02–S04 | 资格以 Solana 完整 Mint 及本地核定证据为准；同名、BP、未核定、被动转入、交易失败、卖出、归属冲突、原件摘要不符或对价无法绑定不会入列。复用已有单目标分类，不把费用、租金或路由残量当成支付额。 | 实际资格记录待核，未证明原 BP 邮件根因；多经济腿、委托及复杂路由不被宣称已覆盖。 |
| S10 | 干跑模式启用同一准入规则，并在已有 Engine 出站队列写入前重查事件身份。测试让既有策略返回同一个候选阶段，验证合格样本的 Gmail/本地只有 `DRY_RUN_AUDIT`，负例无候选、重启不重复。 | 现有运行模式未切换，真实策略对账、旧投递和实际收件皆未修改。 |

资格记录位于 Dashboard 控制目录的 `frank-buy-qualifications.json`。形状为 `{"version":1,"records":[...]}`；每条含 `chain="solana"`、完整 `mint`、`status`（`VERIFIED_MEME`、`EXCLUDED` 或 `PENDING`）、`source`（本机已核对的证据说明或来源）、`observed_at`（Unix 秒）、可选 `name`。同一 Mint 重复、格式错误或观测时间在未来时拒绝读取，缺文件时明确显示未核实。仓库不预填真实币、不根据名称或场所自行标为 Meme，不把示例导入运行目录。

复现：在 `crypto-300-profit-mission/local-agent` 运行 `python -m pytest -q tests/test_frank_rebuild_buys.py tests/test_frank_local_signals.py tests/test_frank_scanner_source_integrity.py tests/test_frank_scanner_reconciliation.py tests/test_mission_control_dashboard.py tests/test_frank_activity_watch_dashboard.py tests/test_frank_intelligence_dashboard_integration.py` 与 `node --test tests/test_frank_ca_report_render.mjs tests/test_frank_f01_source_only.cjs`。可在隔离机器安装 Playwright 后指定 `FRANK_TEST_CHROMIUM`，测试仅使用临时账本、合成数据与随机本机端口。云端本次真实 Chromium 启动受限；不计作浏览器通过。

保持 **NO_DEPLOY / NO_REAL_RPC / NO_REAL_EMAIL / NO_TRADE**。下一段优先用已存、可审计的交易原件与独立钱包快照量化 S08–S09，再按清单推进 C01–C07、C11–C12。
