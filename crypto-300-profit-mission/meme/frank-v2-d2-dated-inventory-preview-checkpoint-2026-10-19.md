# Frank V2 D2：已有 32 币历史链上余额与当前观察池独立对照预览

Date: 2026-10-19 Asia/Bangkok
Status: **DATED_SOURCE_AVAILABLE / READ_ONLY_HTML_PREVIEW_CODE_ADDED / REAL_MAC_RENDER_PENDING / NO_PRODUCTION_CHANGE**
Authority: `docs/DEVELOPMENT_MAINLINE_RULES.md` on PR109. Original functional spec: `frank-wallet-monitor-dashboard-v2-design-2026-10-11.md`.

## 为什么不是继续修 D1 旧信号

独立 Codex 审核 PR109 固定 SHA `f5369e30b324b2a9b414030dff8be31994284dbd` 并在真实 Mac 只读打开现存两份库后确认：参考 2026-10-19 08:56:26 UTC 24h **273 个本地已索引签名、2 条 BUY**，两条均 `TRADE_EVALUATED_NO_TRIGGERED_SIGNAL`；现有控制库最后评估 09:39 UTC，并非整体停机。**两条没有形成正式新信号不是缺失模型评估的证据。** 冻结信号的具体谓词 FAIL/UNDETERMINED 值尚未提取，不得凭数量推断是哪条阈值失败；D1 *这项买入因果归因*结项，**全部钱包账本 D1 仍 PARTIAL**（ATA 缺口、成本等未核）。

接下来优先 D2 的真实可见持仓来源，与 F01 交易资格无关。

## 当前已经存在的业务数据/实现，不重复开发

- 主线 `mission_agent/mission_control/wallet_inventory.py::reconcile_watchlist` 已提供严格的来源、finalized、wallet/mint/slot 校验，并把**历史快照**与模型观察状态分开；当前只因 Mac `frank-inventory-snapshot.json` 未安装而不展示这些历史余额。
- `meme/evidence/frank-v2-thirty-two-mint-finalized-2026-10-11.json` 已在 Git：**32 个公开 mint** 的 2026-10-11 finalized 分币查询，**10 个当时非零、22 个当时为零**，不同 mint 读取 slot 可不同；非完整钱包清单，未核实价格、成本与当下持仓。
- 用户 2026-10-19 Mac 观察池 GET 曾返回 **926 行**，其中 5 模型 OPEN、3 需核库存及大量被动交易/其他账户活动，但完整 926 条与 32 个 old mint 的最新匹配数量尚未由实时 HTML 证明。

## 本轮 D2 最小业务能力

独立脚本 `local-agent/scripts/frank_d2_dated_holdings_preview.py` 只执行：

1. 读取仓库已存在的 32 币证据文件；用固定 localhost 既有 `GET /api/frank-observed-watchlist` 读取原 Dashboard 观察池，最多 2MB JSON、总时限约 15s。
2. **直接复用** `wallet_inventory.reconcile_watchlist`（不复制持仓规则），将二者生成单个 Finder 本地 HTML：默认保留全部观察项目并将当时非零/有模型冲突样本置顶，可搜公开 CA，过滤非零/零/矛盾/无历史证据。公共 Solscan token 链接只在用户主动点击时打开。
3. 明确顶栏 `2026-10-11 已终结区块历史样本/非当前持仓`、距今天日数、不同 slot、成本/现价/PnL 未核实。任何缺少证据的行是 `NOT_QUERIED_IN_SNAPSHOT`，**不会自动当成 0**；MODEL_OPEN/CLOSED 也不是链上当前余额。内容转义、防注入。
4. 文件在用户 Downloads 下随机命名，原子不覆盖，Finder 可直接选中。此功能为**独立只读预览**，不是对生产 Dashboard 下载安装的请求；不读写生产数据库，不改变正在运行的 Frank/F01/C02/通知。
5. 禁止新链上 RPC、GMGN 付费 API、自动交易、Gmail、署名交易，页面只是事实比较，不提供当前 F01 买入资格。

## 完成标准和停止

- 测试用真实 Git 32-mint evidence + 926 条合成 watch rows，验证 10/22/其他未知、模型与样本冲突、未核实的市场价值、真实 localhost HTTP、HTML 注入控制、源码只读和一次 HTML 文件输出。
- 再在 Mac 上**一次性**实际 GET 与本地 HTML 预览（需要先代码审核），核实当日 926/历史 32 的实际重叠条数和分类差异，不能用合成测试代替真实结果。
- 仅当浏览器筛选确实有用户价值才考虑受控集成正式 Dashboard；必须由用户单独批准部署；不反复制作 C02/503 截图、不强求所有 926 行今天链上重新扫描。
- **D2 全量当前持仓与 GMGN PnL 仍 BLOCKED**，此工具只解决“已有可信历史库存证据未在观察池呈现”的可用性问题。

Gate: `NO_MERGE / NO_DEPLOY / NO_NEW_RPC / NO_GMAIL / NO_TRADES / NO_PRODUCTION_SQLITE_WRITE`.
