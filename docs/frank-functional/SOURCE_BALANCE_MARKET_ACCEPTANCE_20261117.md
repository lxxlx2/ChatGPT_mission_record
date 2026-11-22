# Frank 来源合同、全钱包余额与行情接线：实施与本地验收

日期：2026-11-17 Asia/Bangkok。用户授权免费本地实施、真实来源只读、免review、Chrome统一验收后在8766安装。本轮结论：**这三条功能路径 PASS；可得行情覆盖 PARTIAL；Frank整体仍 PARTIAL。**

当前运行/完整回归源码：`9f115cbe383da67b8893fb876d122d04bae22c7a`；此前来源/行情版本为`d6b71231f1b3eb43364e0bc075acd70da8cbf2c9`。主分支产品比较基线仍`ee81a0f44c27eb539c3c874963d311d4e4d5761f`；规划输入`c2e2d8d7bd522cdcfa28249d41029e2ee684dd1d`。全量实源矩阵在`da7c6b3ca2ce351e433ecd9eff0eec3545bd71ae`执行，其后对静态来源年龄显示及USDC/USD参考换算作了必要修复；d6执行完整回归和Chrome实测后，又发现页面重载丢失恢复任务ID；9f补齐并重新执行完整回归及真实中断/重启/Chrome同任务恢复。不能把旧实源报告的code_sha改成d6。

## 实现内容与接口

- `source_evidence.py`：原始HTTP响应字节hash、规范请求hash、opaque provider ID、slot/commitment、捕获/接收时间、私有凭据ID；精确u64/Decimal字符串、分维覆盖与错误脱敏。hash证明字节身份，不自证提供方诚实或全链完整。
- `wallet_refresh.py`：复用既有RPC transport，显式全Owner双Token Program加原生SOL，finalized且后续请求继承minContextSlot；全量账户、重复/错Owner/program/slot回退/精度冲突拒绝，原始凭据保存成功后才承认阶段。不同slot单列，开放账户不等于全部关闭账户或终身历史。
- `research_data.py`：用户触发、应答前持久化、幂等键/在途合并、重启PAUSED及显式恢复、失败不替换上次完整余额、固定snapshot分页与明确来源年龄。GET不创建来源任务或询价，不写逻辑状态。
- `market_observations.py`与既有`meme/market.py`：所有选定Mint分别留下成功/无币对/无价/失败记录；原始HTTP凭据可回放；同一免费提供方30地址批量，处理完整目标集合；CA单地址token-pairs路径保留全部返回候选，不再前8截断。批量返回币对不冒充独立或穷尽池枚举。
- 行情接入现有只读分析与估值；明确USD，USDC/USD参考也必须实际捕获、同链/币种/hash/时效验证，使用`目标USD价 ÷ USDC的USD价`得到USDC参考，不预设1美元锚。两条观察的hash/原件引用随转换结果保留，过期、未来、篡改或缺汇率均不比较。
- 现有页面增加必要的刷新/读结果/恢复/翻页/Mint筛选绑定；沿用既有本地时钟显示来源年龄，无新增来源定时采集。原始信号、默认金额、sender和冻结策略不改。

已接通：`POST/GET /api/frank-balance-refresh`、`POST /api/frank-balance-refresh/resume`、`GET /api/frank-positions`、`POST/GET /api/frank-market-refresh`、`GET /api/frank-market-observations`；现有`GET /api/frank-intelligence`读取已捕获行情。新GET需`X-Frank-Research-Read:1`；新POST要求精确同源Origin、JSON、字段白名单和重复字段拒绝。缺header/跨端口Origin403已实测。

工程决策：自有派生表放在control-root新`frank-research.sqlite`，与旧`mission-control.sqlite`/通知outbox及Scanner源库分开；本轮以通用`frank_refresh_jobs`/`frank_research_results`承载逻辑余额和市场快照对象，`frank_refresh_keys`保存幂等别名，`frank_market_stage`逐批保存中间结果；保护旧投递记录，迁移只影响自有文件。余额、原始凭据与job在重启后保留。SQLite只读查询可能创建空WAL/共享锁侧文件；测试核对主数据及非空WAL/逻辑记录，不能将SHM锁字节变化误判成业务写入。

`scope=positions`行情目标是该余额快照**全部非零Mint加原生SOL的WSOL市场参考**，零余额账户仍完整保留在余额结果。`scope=signals`是全部源候选Mint加USDC/USD转换参考；`observed`保留全部已观察Mint；`mint`支持明确单Mint。它们是查询定义，不是前N个截断。原生SOL与Token估值单列；无价资产仍为null，部分已估值小计不冒充钱包净值。持仓有效期300秒/参考60秒是有效性语义，不是采集配额，GET不会重置时间。

## 实际执行的测试

最终固定9f detached checkout：**333 Python通过，socket审计事件0；218 Node通过，无失败/跳过。** Python实际隔离runner调用pytest.main并拦截socket；完整参数记录在脱敏验收JSON。下列为在local-agent目录可复跑的等价命令：

```sh
python -B -m pytest -q -p no:cacheprovider \
  tests/test_frank_source_evidence.py tests/test_frank_wallet_refresh.py \
  tests/test_frank_market_observations.py tests/test_frank_research_data.py \
  tests/test_frank_activity_paging.py tests/test_frank_g2_d1_d2_dashboard.py \
  tests/test_frank_wallet_watchlist_v2.py tests/test_frank_wallet_inventory_v2.py \
  tests/test_frank_activity_watch_dashboard.py tests/test_frank_intelligence_dashboard_integration.py \
  tests/test_frank_amount_free_intelligence.py tests/test_mission_control_dashboard.py \
  tests/test_frank_d2_http_route.py tests/test_frank_d2_ingress.py tests/test_meme_market_and_rpc.py
node --test tests/test_frank_ca_get_resume.mjs tests/test_frank_ca_report_render.mjs \
  tests/test_frank_d2_ingress_ui.mjs tests/test_frank_ca_rpc_budget_ui.mjs tests/test_frank_research_ui.mjs
```

覆盖：raw精度与隐私、双程序/原生SOL、低Decimal precision和超过单账户u64聚合、部分失败/中断/恢复、源绑定变化、幂等合并后重启、同键异body、75Mint分页、错Mint/币对/链、过期/未来/NaN/篡改参考、非1汇率、65Mint按30/30/5全部处理、GET隔离、真实Handler分发、页面无自动POST/全部行情页/晚返回隔离和内容转义。

运行中发现并修复：合并任务的重试key未持久化、恢复进度重复累计、显式snapshot与cursor冲突、源绑定变化仍可能复用旧key、大数scaleb随全局precision舍入、SQLite连接未及时close、行情进度整数组反复写导致平方写放大。每项已有反例。初次Node通配命令包含独立Playwright浏览器脚本，因本环境无该依赖失败；没有把它算通过或安装额外浏览器。之后明确执行上述218个Node场景，真实浏览器用本机Google Chrome完成。

GitHub在9f上查询statuses和PR-triggered workflow runs均为空；CI为**未运行/无记录**，不作为本次Mac证据。

## 真实来源、HTTP与Chrome结果

| 层次/固定版本 | 实际结果 | 证据边界 |
|---|---|---|
| 初次Owner实源281b57f | 3次wire尝试，1.577秒，6418账户/Mint，5524非零；两程序2160/4258 | 独立原始响应重算通过；不是全历史 |
| da7全量集成 | 6419账户/Mint；原件整数重算与全部137条分页对账通过，连同对账4.359秒 | 变化来自不同采集时点，不覆盖旧报告身份 |
| da7全量行情 | 全部5526目标，185容量批次，103.534秒；385有USD价、5138无base币对、3无价；每目标均留记录 | 全部目标已处理，但来源市场覆盖部分；103秒内来源时间不同，不能称全部同时新鲜 |
| da7信号行情 | 5个源候选均捕获并进入分析 | 后续d6补实际USDC/USD转换依赖 |
| d6 Chrome/HTTP | 手动余额刷新DONE，6420账户/Mint，两程序2160/4260；47页×容量137完整集合，无重无漏且独立原件重算相符 | 固定快照；两个slot470325359/470325361，不是原子same-slot |
| d6 Chrome查询 | 翻页成功，完整排序第3494位Mint精确查到，显示数量与原始raw/decimals精确一致；读/翻页/筛选私有原件数保持197 | 首100行不是总数据；未将无记录当零余额 |
| d6 Chrome行情 | 5个信号Mint加USDC实际免费来源刷新DONE；5项显示带来源换算的参考价变化；本地部署后再次DONE及显示复核 | 参考变化，不是执行收益；60秒后正确不再比较 |
| Chrome时钟 | 余额年龄305秒时显示过期/当前余额未知；手动刷新后回到有效期；GET不改源时点 | 本地时钟显示，无自动来源采集 |

原件、私有DB、Chrome完整画面留在本机，不上传公共仓库。公开摘要与源响应hash见[机器验收记录](source-balance-market-acceptance-20261117.json)。公开方法合同来自[Solana getTokenAccountsByOwner](https://solana.com/docs/rpc/http/gettokenaccountsbyowner)与[DexScreener API reference](https://docs.dexscreener.com/api/reference)；提供方容量30及300请求/分钟用于分块/节奏，不限制总目标。

追加恢复验收：9f上用真实刷新任务在应答后重启Dashboard，任务持久状态为PAUSED且上次成功快照保留；Chrome重新载入并显式读取后恢复按钮可用，点击只恢复同一ID，最终DONE取得6447账户/Mint。最新HTTP按137分页48页与原始响应独立重算相符；首次从无成功快照恢复的场景另由故障注入与Node重载测试覆盖。随后6个实时源候选加USDC参考刷新并在Chrome显示参考价变化。读取/重载不自动POST。

## 本地发布、回退与剩余项

当前已安装源码9f到独立release；619个tracked文件逐一与Git blob核对。只使用原8766端口；先同端口候选验收，随后**实际恢复旧ee81启动入口并读回旧app.js精确字节**，再固定d6到原Dashboard LaunchAgent入口；随后同一入口更新到9f恢复修复版，并重新完成333/218回归及Chrome真实恢复/行情验收。最终进程release身份、响应code_sha、静态字节一致；Chrome部署后再次验收，标签页保持打开。

Scanner保持`1f2c6afc28b9988eaacdc896562ff9a71b78f801`且运行PID不变，LIVE/source_drift=false/errors0；Loop未加载。旧control/投递文件hash不变；没有签名、交易、通知、报价、CA POST、新来源提供方、新Key、付费升级、监控或端口。`INVEST_NO_GO / TRADE_NO_GO`保持。

仍未完成：不可变历史事实manifest及全链覆盖API与W06共同推进；持久收藏备注、版本化复杂交易事实、成本/FIFO/PnL、持久风险更新/通知fake可靠性，以及CA多协议/生命周期/规模矩阵。当前全钱包仅开放账户；无价/无币对资产不强求免费来源编造价格；其他CA来源能力与完整历史阻断不能被本轮PASS覆盖。本次不再用CRAWL单案例作为整体分母。
