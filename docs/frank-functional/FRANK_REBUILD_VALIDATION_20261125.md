# Frank 买入、通知与查询联动回归

2026-11-25（Asia/Bangkok）。分支 `codex/frank-rebuild-spec-20261122`，比较基线 `42d5911a663c8d8219751abbf14e237f49e08101`。以本文件所在提交为验收版本。真实数据覆盖与本机发布仍待验收。

| 反查编号 | 本次验证 | 还需实际验收 |
| --- | --- | --- |
| S01、S05–S07 | 默认页只读买入事实，按账本身份和筛选条件翻页。更换账本或资格变更会使旧游标失效，追加数据不会移入已打开的分页。金额以有效数字呈现，原始对价和时间可回查。Chrome 已核对界面和进入 CA 查询的动作。 | 用真实钱包与已同步的独立区间核对展示覆盖和追赶水位。 |
| S02–S04、S09–S10 | 同一准入判断用于候选 Scanner、Gmail 和本地提醒。以原始签名事件和完整 Mint 核实触发买入。合成交易分别走已核实 Meme、被误标 Meme 的 Backpack Mint 和未知 Mint。核对锁定的策略、出站队列、模拟发送和回执，未决发送只读回执。 | 复杂、多腿或委托买入仍需原件证明及补齐解析。真实钱包的漏报、误报、追平和送达缺独立样本。 |
| S08 | 在对账反例中，独立标签认为某笔应排除，但 Scanner 只掌握一次未定类别的买入。新版归为 `UNRESOLVED`，已核实排除的 BP 与这笔记录分开计。 | 独立标签的原件和账本仍需固定到同一真实区间。 |
| C04、C11 | K 线按报告、币、池和周期读取，向前翻页只读 K 线，保留已显示成交。页面能回到较新一页。来源返回空页时保留当前页和相应状态。冲突或不可解析的非空成交页不能覆盖同池有效缓存。 | 已有公开逐笔来源的 24 小时、300 笔边界依旧适用。需新 CA 的同池、同时段实源对照、流量与延迟数据。 |
| C01–C03、C12 | 既有中文首屏、认领分列、报价侧识别和原报告入口纳入 Node 回归。同一 Chrome 会话的两个不同合成 Mint 通过 A→B→A 切换且未提交新查询。 | 中文叙事须继续用不同真实情形核验来源、引用和认领。 |
| C05–C10、F05–F08 | 本轮证据覆盖买入、通知准入及分池行情继续读取。 | 独立同槽持有人及池全集、开盘买家和钱包深查的真实证据覆盖，服务器复原及多人物隔离仍按原反查要求验收。运行切换维持 NO_GO。 |

## 来源和发布依赖

- Dashboard 可从控制目录的 `frank-buy-qualifications.json` 读取。部署时给 Dashboard、Scanner 和独立 Gmail 进程配置同一个来源文件，使用绝对路径的 `FRANK_BUY_QUALIFICATIONS_PATH`。两个命令行服务也可显式给出 `--buy-qualifications`。文件不存在或无法采信时，新买入无法通过通知准入。现有签名原件、采集和游标仍可核对。
- 本机控制目录未找到该资格文件。资格数据需要来自可核查的真实 Mint 记录。合成记录仅用于隔离测试。缺乏同范围独立钱包快照，仍无法计算真实漏报率。
- 某个旧 BP 真实误报已有历史证据，见 [11 月 24 日回归](FRANK_REBUILD_CA_OVERVIEW_20261124.md#mac-chrome-隔离验收与-scanner-旧证据)。本次复核候选代码的拦截和队列恢复，无真实投递回执。新候选通知使用买入名称、时间、数量、实际支付和交易链接，历史内容仍可通过原回执核对。本地 Dashboard 的 8766 安装版本和 Scanner 服务均未切换。

## 复现

从本提交的 `crypto-300-profit-mission/local-agent` 运行。Chrome 用例使用本机 Chrome 和已安装的 Playwright，默认加载 Chrome 的常规安装路径。可按需设置 `FRANK_CHROME` 和 `FRANK_PLAYWRIGHT_MODULE`。

```sh
python -B -m pytest -q -p no:cacheprovider \
  tests/test_frank_rebuild_delivery.py tests/test_frank_rebuild_buys.py \
  tests/test_frank_gmail_delivery.py tests/test_frank_gmail_health.py \
  tests/test_frank_gmail_template_upgrade.py tests/test_frank_v1.py \
  tests/test_frank_configured_rpc.py tests/test_frank_local_signals.py \
  tests/test_frank_ca_market_series.py tests/test_frank_ca_scoped_analyzer.py \
  tests/test_meme_narrative_story.py
node --test tests/*_ui.mjs tests/test_frank_ca_get_resume.mjs tests/test_frank_ca_report_render.mjs
node tests/test_frank_rebuild_browser.cjs
```

Python 专项 224 通过，备用 Chromium 用例跳过。Node 257 通过。Mac Chrome 158.0.8127.38 单独运行浏览器脚本通过。两个合成 CA 共触发三次行情 GET，由测试脚本直接返回数据。外部请求、POST、页面异常和监听端口均为 0。

## Mac 本地证据重建

产品代码固定为 `1b9e2c05a973fcf0a621fa53cfc7fe882874fa50`。检索 Mac 的 Frank 验收目录、运行控制目录及可见 Git 分支历史，找到了旧的单代币账户归档、单页和派生转账审计。在检查范围内未找到来源可核的 Meme 正资格，或与当前 Scanner 槽位窗口匹配的完整独立逐笔参考。[旧单账户采集](https://github.com/lxxlx2/ChatGPT_mission_record/commit/3937b125d0dc358419ac73145053bc13012972f7)与[历史回放](https://github.com/lxxlx2/ChatGPT_mission_record/commit/9b101aac1cccda952366a587fa666978ab1a25ce)可用作定点反例。

- 从 Mac 正在运行的 Scanner 账本按 SQLite 只读模式创建独立备份，完整性校验通过。冻结文件只留本机，校验时哈希一致。此快照含 10,895 条已索引签名，125 条本地买入候选涉及 51 个 Mint。候选口径包含有待核对资格的买入。
- 按现有 Scanner 规则解码原件、复算交易哈希并绑定签名、槽位和时间，对快照内 6 笔 Backpack 买入逐笔复算。6 笔可核原件都与快照匹配，6 笔在故意模拟错误 Meme 资格时仍被拒绝。测试仅涉及准入。私有试验资格文件记录官方来源明确的 BP 排除，余下 50 个 Mint 保留为待核。当前控制目录和运行服务未使用该试验文件。
- 锁定一个有多个买入 Mint 的已落库窗口供后续逐笔对账。本地账本在该窗口有 95 条索引、3 条买入候选、2 个 Mint。窗口边界取自同一只读备份，独立侧须覆盖整个槽位区间并提供完整性证据后才能将它用于漏报率。私有文件固定了请求边界和快照摘要，独立参考状态仍是 `NOT_CAPTURED`。

实际执行 `python -B -m pytest -q -p no:cacheprovider tests/test_frank_rebuild_buys.py tests/test_frank_rebuild_delivery.py tests/test_frank_scanner_reconciliation.py -k 'not dashboard_endpoint and not browser'`，36 通过，2 筛除。独立对账和真实渠道验收仍待实际原件，运行切换保持 NO_GO。

### GMGN 钱包活动对照

在 Mac Chrome 打开同一钱包的 GMGN「活动」，通过页面类型筛选保留买卖。待对账窗口所见 9 行买卖对应 4 个唯一 Solana 交易签名，其中 3 笔买入、1 笔卖出。4 笔均能与冻结账本按完整签名匹配，并用本机归档重新绑定槽位、时间、哈希及钱包经济方向。窗口内本地记录的 3 个买入签名均出现于本次 GMGN 对照。GMGN 对同一签名有重复行和多资产行，不能用行数计算买入笔数。

这一结果覆盖本次实际读到的 GMGN 买卖。页面未提供完整槽位区间及总体覆盖凭据，95 条本地索引的独立验收仍未完成。代币是否属于 Meme 另看完整 Mint 的项目出处。公开记录使用汇总数据，逐笔签名和交易哈希留在 Mac。

## 2026-11-26 确认币种并恢复旧账本买入

本段以 `eb8c0f82c85004a822a356949cbfd3470e392923` 为比较基线。锁定窗口的 ANSEM 和 NIO 均按完整 Solana Mint 核对：The Black Bull 的发行页和 CoinMarketCap 的 Meme 分类指向同一地址。NIO 的 Pump 创建者资料说明源自在社交平台传播的图片和视频，Solscan 对同一地址标为 Meme。用这些证据制作的资格文件供隔离回放。 [ANSEM 发行页](https://pump.fun/coin/9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump) · [CoinMarketCap](https://coinmarketcap.com/currencies/the-black-bull/) · [NIO 创建者资料](https://pump.fun/coin/7SL2VnfYsChvog5oQY9Nmtqu1wceaMiQzWoqoLQpump) · [Solscan 同 Mint](https://solscan.io/token/7SL2VnfYsChvog5oQY9Nmtqu1wceaMiQzWoqoLQpump)

旧账本的 3 笔真实买入缺少现版路由字段。加入来源已核实的资格后，基线买入页仍显示 0 笔。候选版本在旧记录有签署买入证据时从可信本机归档只读复算，核对原件哈希、签名、钱包、槽位、时间和同一 Mint，再按买入准入校验。窗口内由 0 笔恢复为 3 笔，其中 2 笔有可核支付金额。1 笔 ANSEM 的多跳原件能核实最终买入数量，支付金额仍未核实，页面省略该字段。该展示规则仅用于买入页。邮件和本地提醒继续使用原支付证明条件。

Solscan Chrome 的钱包原始交易表可以打开，时间列提供 UTC 自定义日期。浏览器操作未取得覆盖完整窗口的分页结果，当前的独立证据仍是此前 GMGN 对上的 3 笔买入和 1 笔卖出。原始证据、资格文件和备份留在 Mac 隔离目录，8766 切换仍待全范围验收。 [Solscan 原始历史说明](https://info.solscan.io/solscan-supports-full-historical-data-search/)

专项回归 `python -B -m pytest -q -p no:cacheprovider tests/test_frank_rebuild_buys.py tests/test_frank_rebuild_delivery.py tests/test_frank_scanner_reconciliation.py tests/test_frank_archived_wallet_facts.py` 为 60 通过、1 项备用浏览器测试跳过。Node 界面回归 257 通过。Mac Chrome 158 使用由 `DashboardState` 从冻结备份读出的 3 笔结果进行隔离回放，验证 2 笔显示原币支付、1 笔只显示数量，以及按完整 Mint 筛选。测试未监听端口，也无外部请求、POST 或页内异常。冻结账本哈希保持一致。

## 2026-11-26 全量原件复算与分类型查询

比较基线 `7d8fb155397155fb79141fbdc91999c479377deb`。按冻结账本的全部记录复算和对照结果使用以下口径。

| 项目 | 结果 |
| --- | --- |
| 买入原件和钱包流水 | 冻结的 10,895 条索引全部与本机归档核对签名、钱包、槽位、时间和标准化交易哈希。复算的 125 笔买入与索引逐笔一致，覆盖 51 个 Mint。另复算出 119 笔卖出、5,688 项普通转账、4,119 项创建代币账户、313 笔失败及 531 项未定。该比对覆盖账本已有记录。 |
| 真实资格与隔离分页 | 6 个 Mint 有公开来源支持 Meme 资格，2 个有明确排除依据，另有 43 个仍待核。真实资格文件在隔离账本上显示 34 笔，26 笔有直付证据；余 8 笔仅显示取得数量。分页压力场景暂按其余 43 个为合格并保留已知排除，Chrome 读完 49 个 Mint 的 117 笔、4 页，无重复缺页，并测了 3 个完整 Mint 筛选。 |
| 45 个不同 CA 的行情 | 排除可查验收归档已有的 CA 和此前已核实样本，使用已有 DexScreener 免费 GET 两批取回行情，42 个有基础侧主池、3 个无可用基础侧交易对。主池来源标记覆盖 PumpSwap 29、Raydium 7、Meteora 5、Orca 1。Mac Chrome 用冻结的原始行情和模拟已核 Mint 状态走 45 个报告回读，42 个有价、3 个不可用，无串币、页面异常或外部请求。链上持仓和合约状态未通过此行情回放验收。 [DexScreener 公开接口](https://docs.dexscreener.com/api/reference) |
| 迁移预检 | 在真实冻结备份跑现有 `check_snapshot`，数据库完整性、Frank 游标与模型版本衔接通过，备份哈希一致。目标服务器安装及运行切换未验收。 |

新核实的公开类别涵盖社区币、同名不同 CA 和明确的协议代币。示例可按原始发行资料核对。 [JEANPHIL 发行](https://pump.fun/coin/GTBxUiw6wJdmmkCGZgRHLyYxqu1vG4KtRpeox6yDpump) · [DCTY 合约](https://solscan.io/token/9hjBLBrc7WZW2H8UQvBAvG5WiTZotXUv2Bdcn4f4pump) · [另一个 Dacity 合约](https://solscan.io/token/nxPqZ4F7ux8Vph5NFu25rEP6Kx9Gr1U6Fmj36Rjpump) · [Metaplex 官方白皮书](https://whitepaper.metaplex.foundation/whitepaper.pdf#page=14)

跨协议离线回归后修正两处错误。Token-2022 二进制持仓核对会将截断扩展、零填充后的非零数据、重复或未知扩展类型保留为未核实，旧报告缺新校验字段时保留数据与来源，撤下由旧二进制证明生成的精确比例。Pump.fun 发行读取只有在收到明确带槽位的空账户或已核对的账户归属时才说明该槽位的状态，残缺响应保留为不可用。 [Token-2022 上游扩展定义](https://github.com/solana-program/token-2022/blob/main/interface/src/extension/mod.rs)

独立钱包参考的公开 GET 仍未补齐。Solscan 增强交易入口返回 HTTP 401，SolanaFM 返回 HTTP 403。待补范围仍包括同钱包完整交易分母、独立同槽持有人和池、复杂协议真实样本及端到端通知覆盖。运行切换保持 NO_GO。 [Solscan 增强交易入口](https://pro-api.solscan.io/pro-api-docs/v2.0/playground/v2-account-transactions-enhanced) · [SolanaFM 钱包交易说明](https://docs.solana.fm/reference/get_account_transactions)

复现命令为 `python -B -m pytest -q -p no:cacheprovider tests/test_meme_holder_binary.py tests/test_meme_launch_origin.py` 和 `node --test tests/*_ui.mjs tests/test_frank_ca_get_resume.mjs tests/test_frank_ca_report_render.mjs`，分别通过 56 和 259 项。全量 `pytest -q -p no:cacheprovider --tb=no tests` 在拦截外部网络的进程内完成，2,973 通过，1 项备用 Chromium 测试跳过。Mac Chrome 的 45 个市场卡和 117 笔买入分页验收单独执行，证据范围见上表。

## 2026-11-26 研究台界面重做

以 `744498c801a58913228c2dbcc513524f913bb9db` 为基线，完成反查 UI01–UI05 对应的页面和查询分流。操作审计保留旧地址，从主导航移除。普通 CA 摘要只读身份、行情、叙事及轻量持有人样本，样本不用来计算或展示全局 Top10。选定交易池后自动读取 K 线和近期成交；切池和周期仅重读相应市场数据。首次读取全 Mint、开盘和独立来源在完整尽调。现有单任务队列中，已开始的完整尽调仍可能占用队列。

买入页面不显示原币和数量。可选美元证据文件位于 Dashboard 控制目录的 `frank-buy-usd-evidence.json`。其版本为 `1`，记录键为钱包、交易签名、槽位、区块时间、交易原件哈希、目标 Mint 和支付币。证据同时记录来源、原件哈希和成交时点，并提供已核实美元花费或该时点的支付币美元折算价，二者填其一。美元花费和单价保持十进制原精度，页面才舍入。现有冻结账本的 125 笔候选主动买入都没有存入成交时点的美元字段，运行目录尚未导入这份外部证据。历史记录的两列对缺失数据留空，仍可进入原交易。

本轮离线 Python 全量 2,992 通过、1 项备用 Chromium 测试跳过。Node 界面与查询恢复 259 通过。Mac Chrome 158.0.8127.38 用两个合成 CA 走通默认 K 线、切池和周期、历史翻页、CA 切换、无美元证据、键盘焦点和 320／390 px 布局。1440／390／320 px 的独立预览复核同时检查关键控件对比度（5.13:1 以上）。两次浏览器验证都使用模拟响应，无真实外部请求、POST 或页面异常。真实美元原件和实时 CA 验收保持待完成，原 8766 运行切换保持 NO_GO。

## 2026-11-26 审核交接与隔离 HTTP 验收

基线 `737348a0fd272fdd8ecc25fa7abd63a1af62b46f`。将核实后的缺口和验收准则写入[技术方案第 6 节](FRANK_REBUILD_DESIGN_20261122.md#6-11-月-26-日审核后的实施顺序)及[审核反查表](FRANK_REBUILD_REQUIREMENTS_20261122.md#11-月-26-日审核反查)。报价侧反例使用两个绑定同一目标 Mint 的池，第一池失败、第二池有价，基线未访问第二池。当前概览单工作器、资格依赖与报价来源分别按源码核对。实链数据和生产切换门禁仍待完成。

更新并启用此前默认跳过的 `test_browser_default_entry_filters_and_prefills_ca`。Mac Chrome 通过真正的本地 Dashboard HTTP 服务读取隔离 SQLite 与合成美元证据，验证 USD 两列、BP 筛选、进入 CA 及钱包账本哈希不变。只放行隔离服务的预期 GET，运行结束关闭临时服务。测试使用合成交易与价格证据。

实际命令从 `crypto-300-profit-mission/local-agent` 执行。**140 通过，包含上述 Chrome 用例**。

```zsh
FRANK_TEST_CHROMIUM="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  uv run --isolated --offline --no-project --with pytest==8.3.5 --with playwright \
  python -B -m pytest -q -p no:cacheprovider \
  tests/test_frank_rebuild_buys.py tests/test_frank_rebuild_delivery.py \
  tests/test_frank_v1.py tests/test_frank_scanner_source_integrity.py \
  tests/test_frank_ca_market_series.py tests/test_frank_ca_scoped_analyzer.py \
  tests/test_frank_ca_launch_flow.py
```
