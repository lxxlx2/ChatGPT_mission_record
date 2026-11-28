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

## 2026-11-27 独立流水与真实美元报价

买入页和报价接入在集成分支固定源码 `ba44d31b96d8253056490a94e78ef77436095670` 上验证。对照的冻结账本 SHA-256 为 `c5353d07d6640a4f31845a5592c4104462006def1da953c00f26ad67cb607f71`。本节补充已有历史窗口的实证。新证据仅写入隔离暂存目录。

### S08 钱包签名覆盖

Mac Chrome 使用 Solscan 的 Transactions 页，筛选 UTC 2026-11-24 00:00:00 至 23:59:59。保留垃圾及失败交易，关闭额外 Token Account 展开。公开页面以 40 条每页返回 40、40、15 条，最后一页禁用下一页。首尾交易分别核实为 finalized，槽位 `473138616` 至 `473522449`，对应 UTC 00:10:48 至 23:06:10。 [Solscan 原始交易时间过滤](https://info.solscan.io/solscan-supports-full-historical-data-search/)

对两边完整签名按 ASCII 排序并用换行连接，无末尾换行，摘要均为 `4320c00a988d3fc6a3e0e7300b28f23dd18c0ee28841b9e840e1bf3362eb135d`。Solscan 95 个唯一签名与冻结账本 95 条索引完全相同。本机检测证据用账本内的 `signature_detections` 按钱包和签名连接，95 笔的槽位及区块时间也与索引相符，时钟数据齐全。

| 实证范围 | 样本数 | P50 | P95 |
| --- | ---: | ---: | ---: |
| 区块时间到本机首次检测 | 95 | 16.120 秒 | 31.420 秒 |
| 区块时间到本机入库 | 95 | 16.303 秒 | 31.610 秒 |

结论为该日公开源可见的 95 笔中漏入库 0，额外索引 0。本机时钟统计覆盖全部 95 笔。模型策略和收件端尚待独立证据。

同一 UTC 日的 Solscan Activities 页显示 7 笔 Swap。逐笔打开 Raw，展开交易签名数量对应的签署账户，核对完整 `signer` 标志。5 笔由 Frank 签署，均已入库。这 5 笔包括 3 笔已核实 Meme 买入、1 笔已核实 Meme 卖出、1 笔 WSOL 与 USDC 兑换。2 笔 PNP 活动由第三方签署。其中 1 笔在原始流水内并被本机识别为被动转入，另 1 笔仅由 Activities 索引到所属代币账户，本机直接签名窗口未收录。已入库 6 笔的本机交易原件按槽位、时间、签名和哈希复算，3 笔 Meme 买入、卖出与被动分类一致。报价资产兑换保留为待核，买入准入未通过。活动页所有可见候选中未发现遗漏的主动 Meme 买入，协议的全覆盖仍待证据。 [Solscan 交易详情字段说明](https://info.solscan.io/solscan-transaction-details/)

同样的排序和拼接规则下，Solscan 可见的 5 个由 Frank 签署的活动签名摘要为 `529dd1612452a3b47928d5b7833307a4b6b245e01da027ff2bd93f9d230e04d1`。与冻结窗口相交的 6 个活动签名摘要为 `b8db05fcc1d429a1e547c1bd40741bb22277dfe8039a88d128d403a1ccffb710`。两组摘要均从各自来源算出并逐组匹配。

### S07 成交秒 USD

以冻结账本内有原币支付证据的 26 笔为分母，使用已有 Kraken 公开 Spot PostTrade 获取 26 个不同的 USDC/USD 精确秒响应。26 次 GET 均为 HTTP 200，3 个成交秒有价格一致的成交观察，23 个该秒无成交。请求只传支付币种和对应 UTC 秒。原始响应和抓取清单在私有暂存区，清单 SHA-256 为 `6f16aa289358af0f53b6313dc012c052bc778427bbe5f07465b94a12663c5b07`。 [Kraken PostTrade 公开接口](https://docs.kraken.com/api/docs/rest-api/get-post-trade)

用新版本既有离线命令 `python -B -m scripts.frank_build_usd_evidence` 打包 3 份已核验原件。版本 2 的暂存文件权限为 `0600`，SHA-256 为 `2f11470b6bba568bcf422da6d64266426688d2329cb3e93e6f8db6aa2b6f8973`。用原币实付乘该秒汇率并除以代币数量，对三个结果分别复算。隔离 Mac Chrome 158 通过实际本机 HTTP 读取两页共 34 笔，看到 2 个 Mint 的 3 笔各显示两项 `≈$` 估算。31 笔缺估算，精确美元实付仍为 0 笔。页面无异常，隔离 Dashboard 无外部请求，冻结备份哈希一致。 [现有打包规范](../../crypto-300-profit-mission/local-agent/docs/FRANK_BUY_USD_EVIDENCE.md)

### C09 归档持有人与池

在 `dfa32dcb666abb8b3efff49af659c1643417d8e4` 上，从 3 枚不同 Mint 的 5 份已完成报告逐条反查已保存的主源和第二来源原始响应。用 DONE 标记核对报告哈希。检查点仅使用 finalized `getMultipleAccounts` 的成功 `jsonParsed` 响应，第二来源匹配最近未配对、顺序相同的主源地址批次。重算原始响应 SHA-256、目标 Mint、账户身份、所有者和原始余额。112,980 次地址观测中 112,977 次匹配，3 次缺失均发生在两边槽位不同的批次。实际同槽部分为 1,318 批的 13,180 次观测，覆盖 12,653 个唯一 Mint 与代币账户组合，全部匹配。各批次的槽位不同，3 次独立全 Mint 枚举仍收到 HTTP 403。

3 枚 Mint 的 PumpSwap 池原件都能重算绑定的池、两侧金库和余额。池观察分别比各自首批持有人快照晚 276、96、182 个槽位，完整同槽池与持有人证明仍待取证。六份池读取散列组合的 SHA-256 为 `db51d3f96a5fe8274873e2e3aa5e4dbec21d12e29a838dc12bbf1773f660c0f4`。

### 最新源码的回归

在 `crypto-300-profit-mission/local-agent` 执行以下测试，第一组 66 项通过、1 项 Chrome 个案筛除，另以真实数据运行隔离浏览器。第二组 48 项通过，涵盖执行器和来源预算。Node 定向回归 210 项通过。实际 Mac Chrome 并行夹具也通过，完整任务执行时另一 CA 的摘要和钱包明细完成，显式刷新遇到限流后保留旧观察，读取报告绑定正确。

```zsh
uv run --isolated --offline --no-project --with pytest==8.3.5 python -B -m pytest -q -p no:cacheprovider \
  tests/test_frank_historical_usd_tick.py tests/test_frank_build_usd_evidence.py tests/test_frank_rebuild_buys.py \
  tests/test_frank_rebuild_delivery.py tests/test_frank_historical_holder_compare.py tests/test_frank_staged_person_scope.py \
  tests/test_frank_ca_series_single_flight.py tests/test_frank_shared_provider_pacing.py tests/test_frank_dex_market_pacing.py \
  -k 'not browser_default_entry'
uv run --isolated --offline --no-project --with pytest==8.3.5 python -B -m pytest -q -p no:cacheprovider \
  tests/test_frank_parallel_ca_scopes.py tests/test_frank_ca_market_series.py tests/test_frank_ca_job_rpc_budget.py \
  tests/test_frank_ca_scoped_analyzer.py
node --test --test-reporter=tap tests/test_frank_ca_report_render.mjs tests/test_frank_ca_get_resume.mjs
node tests/test_frank_parallel_ca_browser.cjs
```

Chrome 入口使用本机已安装的 Node Playwright，可通过 `FRANK_PLAYWRIGHT_MODULE` 指定。它使用随机回环测试端口，数据来自隔离夹具。USD 实证的浏览器另用上述冻结账本和真实报价暂存文件。

### 仍待生产验收的范围

买入估算和指定 UTC 日的签名入库覆盖已有实证。新 CA 行情样本选取时，已有 DexScreener 的公开 profiles 入口实际返回一次 HTTP 403，未重试该入口。本轮没有实源完整 CA 查询的首屏或深查耗时。完整独立持有人全集、池和持有人同槽、覆盖更多日期的严格买入分类、真实通知送达仍待证据。整体 `PARTIAL`，本地 8766 未切换，生产 `NO_GO`。

## 2026-11-27 通知重放、独立钱包对账与新 CA 行情

通知修复源码为 `e0b754f557a74fcaa06b47c81693ed85e2e11e48`，直接基线为 `4cde54fe0ec6cb489235ea9cbb347c0170f31035`。故障在 `c5ec30c85f8e12168644731a89aeb8cc0dd4c3b4` 的隔离副本复现。从该故障基线到直接基线，运行代码的变更仅涉及持有人证据界面。

### 通知入队、发送前校验与恢复

- 用冻结账本和归档原件重新运行真实 Scanner、Engine、本地与 Gmail 队列，逐笔核对 Scanner 使用的规范化原件 SHA-256。共处理 10,895 笔，槽位 452750502–473771260。游标追到归档末端，第二次扫描及模型消费均为 0。归档账本 SHA-256 为 `c5353d07d6640a4f31845a5592c4104462006def1da953c00f26ad67cb607f71`。分类器识别 125 笔主动买入，26 笔（6 个 Mint）通过严格事实准入，8 笔（3 个 Mint）只有可列入历史的买入证据、缺少可归属买价，6 笔 BP 被硬排除，其余 85 笔未获准入。严格准入数字指买入事实，通知还受原策略与投递时效约束。
- 同一归档以实际验收时钟重放。故障版本把 3 个 PRECONFIRM、2 个 MULTIPLE 过期阶段写入通知队列，模拟投递实际接收 5 次本地调用、2 次 Gmail 调用。两个 MULTIPLE 阶段来自 UTC 11 月 11 日和 19 日。候选版本五个阶段均记录 `BUY_NOTIFICATION_EXPIRED`，队列为空，模拟调用均为 0。历史买入及原件继续可读。归档中的 5 条 Gmail 已验证回执与 17 条系统命令接收回执属于旧运行；本次真实归档重放使用替身发送器，拒绝外网及通知命令。
- 入队与首次投递都以绑定原始买入的链上时间计算上限。PRECONFIRM 使用 V1 的 60 分钟窗口，MULTIPLE 使用 V1 的 3 小时边界。恰好到边界可送，超过即停止。等待 Gmail 回执时过期的队列记录仍保留。已经接受但尚未落库的 Gmail 或本地通知继续走旧回执核对路径。
- 之前因过期或资格待核从未建队列的阶段，若同一轮有一笔更新的已核实主动买入且再满足原策略，旧拦截记录原样存入评估审计，新买入沿用原阶段身份生成一次通知。仅补资格或重跑旧事件不触发该路径。此前已有队列、邮件内容或 Gmail 记录的阶段不走这条准入路径。
- Mac 执行命令为 `PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 /tmp/frank_offline_archive_FLeKN4oZ/replay.py`。离线运行器 SHA-256 `d5ea95a69616595ed54c791790e83abbca18593be558449fb4c80619177e6bc9`，基线汇总 `d60cc799ec8b66d660e04edd692de463f8cc243f68b0dd0439d7aaf821871a36`，候选汇总 `cd74d284530a6d976a7abd8082b5c2204cf1b61b2391553fcb522924cf6be2b0`。运行器和汇总副本存入 Mac 私有验收目录 `notification-replay-e0b754f5`，Git 仅记录汇总和原件散列。

### 11 月 19 日 UTC 整日独立对账

在 Mac Chrome 打开 Solscan 公开交易列表，关闭隐藏失败与代币账户扩展，取同一钱包 UTC 00:00:00–23:59:59 的九页，最后一页 22 笔且下一页禁用。342 个唯一签名、0 重复。本地冻结 Scanner 数据库独立 SQL 筛选得到相同的有序签名集合，逐集合 SHA-256 为 `5fae9605f04a66ff947ef3648c848922139c1c9fb3fc1994f629d89ace130387`。两个边界交易在详情均为 finalized，分别是 00:18:15 的槽 471132155 和 23:52:43 的槽 471526431。加上此前独立核对的 95 签名，两个整日窗口的直接钱包交易合计 437／437 入库。11 月 19 日的 342 笔均有同槽、同区块时间的本机检测记录，区块到首次检测 P50／P95 为 19.540／30.549 秒，区块到判定入库为 19.832／31.097 秒（最近秩）。这里的分母是直接钱包交易签名。完整买入分类、资格认定和实际送达各需自己的独立分母。

### 三枚未用于此前验收的新 CA

| 市场样本 | GeckoTerminal 公共 GET 实读 | 隔离 Mac Chrome 回放 |
| --- | --- | --- |
| Pump.fun | 5 分钟 K 线 2 根、近期成交 299 笔，两项冷读共 1.821 秒；热读 0 次外部请求 | 从 CA 查询表单到选池、K 线和成交通过 |
| PumpSwap | 5 分钟 K 线 1 根、近期成交 171 笔，两项冷读共 1.386 秒；热读 0 次外部请求 | 从 CA 查询表单到选池、K 线和成交通过 |
| Meteora DAMM v2 | K 线读取 0.143 秒返回 HTTP 429，共享限流短路后续成交 | 显示“来源限流，本次未访问来源”，无空结果误报 |

先从已有 GeckoTerminal 新池入口挑选三个不同协议的新 CA。实际访问共 5 次 HTTP 200 与 1 次 HTTP 429（含新池发现）。实源读取运行于 `abdc304ac23a17bc9bb1447f31f30d81fb6e8d57`；到候选源码，市场适配器和服务接口无变化。官方公开行情端点提供的是近期数据，计时只覆盖市场 K 线和成交读取。原件清单 SHA-256 为 `04a7729c77afe09c3012338474604ed471fcadc17bbf1f1dfdd4cfa50d27db82`。Mac Chrome 158.0.8127.38 用实际 CA 表单、任务管理与行情 HTTP 服务重放三个场景，使用存档原件和隔离链上分析响应，共 3 次 K 线与 2 次成交夹具响应，外部请求与页面异常均为 0。 [GeckoTerminal 公共 API](https://api.geckoterminal.com/docs/index.html)

### 候选版本实测命令

在 `crypto-300-profit-mission/local-agent` 执行。完整 Python 执行在进程内拦截外部 DNS 和套接字连接，允许隔离 HTTP 夹具使用回环地址。Chrome 个案单独启用实际 Mac Chrome。

```zsh
uv run --isolated --offline --no-project --with pytest==8.3.5 python -B -m pytest -q -p no:cacheprovider \
  tests/test_frank_rebuild_delivery.py tests/test_frank_gmail_delivery.py tests/test_frank_v1.py \
  tests/test_frank_staged_person_scope.py tests/test_frank_independent_sample_identity.py \
  tests/test_meme_independent_check_lifecycle.py tests/test_meme_independent_error_evidence.py \
  tests/test_meme_launch_origin.py tests/test_frank_ca_market_series.py \
  tests/test_frank_ca_series_single_flight.py tests/test_frank_shared_provider_pacing.py
node --test tests/*_ui.mjs tests/test_frank_ca_get_resume.mjs tests/test_frank_ca_report_render.mjs
FRANK_TEST_CHROMIUM='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' \
  uv run --isolated --offline --no-project --with pytest==8.3.5 --with playwright python -B -m pytest \
  -q -p no:cacheprovider tests/test_frank_rebuild_buys.py::test_browser_default_entry_filters_and_prefills_ca
```

最终候选通过定向 Python 149 项和 Node 266 项。全量 Python 用 `uv run --isolated --offline --no-project --with pytest==8.3.5 --with numpy python -B -` 启动上面的网络护栏，调用 `pytest.main(["-q", "-p", "no:cacheprovider", "--tb=short", "tests"])`，3,051 项通过，1 项 Chrome 可选用例随后以真实 Mac Chrome 单独执行并通过。全量首次运行发现一个旧调用缺少新增的 Engine 参数，最终 SHA 恢复兼容默认值并重新跑完。真实归档在最终 SHA 重跑，汇总文件 SHA-256 与上文一致。

**结论。通知回归和两日签名覆盖通过，CA 行情验收为 PARTIAL，发布 NO_GO。** 实际收件、完整买入分类漏报率、完整独立持有人与池同槽证据，以及完整 CA 首屏和深查的实源耗时仍待证明。本地 8766 本轮没有切换。

## 2026-11-28 买入分类对账与发布前检查

候选源码固定为 `2b4ab7425bb359252b98eae76ac5b8e5a6fa4008`，直接基线 `066c5142dfb63beceb76267184ba2bb478933996`。候选增加了买入检测与入库的 P50／P95。当前候选的买入展示、通知及 CA 业务代码和上一次验收源码一致。

### S08 两个完整 UTC 日的买入对账

Mac Chrome 读取 Solscan 钱包 Activities，时间过滤为两个 UTC 整日，分页设为每页 100，两个窗口各在一页结束。11 月 19 日 13 笔兑换里有 8 笔符合范围的买入和 5 笔卖出。11 月 24 日 7 笔兑换里有 3 笔符合范围的买入、1 笔卖出、1 笔 SOL／USDC 换币和 2 笔由其他钱包发起的兑换。一笔第三方交易也在签名索引中，实际 Frank 钱包未签名。浏览器原始活动向量的 SHA-256 分别为 `8136d09120eafffd57aa83da49bb166d84478fa17d1b4da7b1de2056e6244e0c` 和 `3923861aac691756e94c97db01075f3a2178725bb65c0313e24679f36cd48f1f`。另用两个独立的交易日期签名集合绑定 437 份归档原件。 [Solscan 历史日期筛选](https://info.solscan.io/solscan-supports-full-historical-data-search/)

- **买入历史通过。** 对所有 437 份原件，独立按实际签名人、成功状态、钱包原始余额和兑换日志判断方向。已证实 Meme 的 11 笔买入均能在候选页面使用的 `read_buys` 分页入口查到，完整 Mint、方向和目标币原始数量一致。10 笔通过严格买入准入，另外 1 笔路由买入可见，金额留空。两日内这批独立可核买入漏 0、额外 0。另有 1 笔公开卖出在候选分类中待核，余额变化确认目标资产减少、稳定币增加，没有混进买入。
- **钱包扣款口径。** 11 笔买入的 Solscan 活动表输入金额均小于归档证实的钱包实际 USDC 扣款。逐笔解析内部代币转账，Solscan 输入金额对应其中一腿，其余同笔转账组成差额，全部有原始凭据。上述 1 笔路由买入能证明钱包总扣款，仍缺将总支出全部归属到目标 Mint 的证据，因此使用原有的留空规则。未将 USDC 当作成交时点的美元价格。
- **这 11 笔的采集耗时。** 区块至首次检测 P50／P95 为 18.824／30.441 秒，至判定入库为 20.692／30.623 秒。均使用冻结 Scanner 时钟，按最近秩计算。这个买入分母和 437 笔签名分母分别报告，实际投递时延另行核对。
- 同一冻结账本 SHA-256 固定为 `c5353d07d6640a4f31845a5592c4104462006def1da953c00f26ad67cb607f71`，资格证据 `39920968b6795f442b1d1f186f2d3558ec813b731cb8508eadfb9e69759a4e3d`。基于独立交易原件计算的两日摘要为 `c96f3fc1dab7ae66d756e654792c93f5d7b9c7a6e04723426ee00a8e8387eacf` 和 `66b55184a21ede5165f3b5404c9e8cea1611fb19af90c297031f81634e52d311`。复核浏览器活动、原件、展示以及时延的运行结果 SHA-256 为 `9346841fd8d7817ea7ffb3c097eea60ef90f188bbfca59d223dab741ed6df5e2`。原件及明细保留在 Mac 隔离证据目录。

### C09 持有人与池逐槽反查

在候选源码上重新验证 3 枚 Mint 的 21 份 DONE 报告及其检查点，18 份池快照能用两份绑定原始回执重算池和金库，1 份缺一侧原件，2 份没有发布池快照。16 份同时包含主来源完整持有人快照与池快照的报告，二者同槽计数为 0。独立来源 1,318 个同槽持有人批次中 13,180 次观测全部匹配。已验证的独立持有人槽位和归档池槽位交集为 0，最接近的一组仍差 10 个槽。三次独立全 Mint 枚举返回 HTTP 403。此证据支持批次核对，完整同槽快照仍为 `PARTIAL`。

报告及回执组合清单 SHA-256 为 `6dddad599ff4d92eb7f3143f2b547bd6afea0bea054f81b047ecc5bb0e409d35`。三份不同 Mint 的既有深查从来源开始至报告落盘的历史用时分别为 958.843、2,786.984 和 21,050.918 秒。这些是归档深查时钟。最新候选的实源首屏与完整深查用时仍待取证。

### 投递与运行前检查

只读使用候选 `check_snapshot` 和冻结策略检查独立备份。SQLite 完整性、外键、策略指纹均通过。1 个钱包游标在槽 473771260，模型待处理为 0，备份 SHA-256 前后一致。23 条旧 outbox 记录的信号哈希与原交易关联全部匹配，17 条本地命令回执和 5 条 Gmail Sent 回读可与原信号或冻结邮件内容核对，另 1 条为演练记录。Gmail 的观测 Message-ID 在 5 条历史记录里均有改写，既有验证以内容、信号标记和回执绑定。当前候选的收件验证仍待完成。

本机只读对照运行目录、已安装 Git blob 与 Scanner 源码指纹。8766 Dashboard 为 `fd06df4fbbc25721e0a87a3721571f0dc34cca75`，566 个文件匹配。唯一 Scanner 工作进程为 `1f2c6afc28b9988eaacdc896562ff9a71b78f801`，318 个文件和实际加载源码指纹匹配。已查明本机旧版本基线，候选的受控同机切换和回退仍待真实验收。

### 实际运行命令

以下命令均在固定源码的 `crypto-300-profit-mission/local-agent` 目录运行。两个只读取证脚本使用独立备份、浏览器收集的公开活动和既有归档回执。

```zsh
PYTHONPATH=. python3 -B "$private/two-day-buy-recount-066c5142/solscan-check.py"
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 -B "$private/joint-slot-2b4ab742/check.py"
uv run --isolated --offline --no-project --with pytest==8.3.5 python -B -m pytest -q -p no:cacheprovider \
  tests/test_frank_buy_latency_percentiles.py tests/test_frank_scanner_reconciliation.py \
  tests/test_frank_rebuild_buys.py tests/test_frank_rebuild_delivery.py tests/test_frank_gmail_delivery.py
uv run --isolated --offline --no-project --with pytest==8.3.5 python -B -m pytest -q -p no:cacheprovider \
  tests/test_frank_independent_sample_identity.py tests/test_meme_independent_check_lifecycle.py \
  tests/test_meme_independent_error_evidence.py tests/test_meme_independent_full_accounts.py \
  tests/test_meme_pool_holder_roles.py tests/test_meme_pool_vaults.py
```

两组 Python 分别 100 和 126 项通过。第一组的 1 项可选 Chrome 用例以真实 Mac Chrome 单独启动并通过。两日买入历史验收通过，完整同槽与当前实源深查、候选实际收件仍未通过门禁。整体 `PARTIAL`，本地切换和生产发布为 `NO_GO`。

## 2026-11-28 池与持有人联合抽样

候选源码 `72f1bc3b0c613535a5361f97175fa80efd817e6e`，直接基线 `e75376f66200815f6e7c94d000ec9f735f160dac`。上一轮归档的池快照和独立持有人复核来自不同请求，实测交集为 0。完整尽调在原有逐地址核对完成后，使用已核实主池和同一主／第二来源执行联合抽样。

每个来源读一个 finalized `getMultipleAccounts` 批次，地址按同一顺序发送。池、两侧金库和两侧 Mint 占 5 个地址，剩余地址用于抽样持有人，单批遵守现有免费第二来源的 10 地址限制。原全量枚举和逐批地址核对继续执行。只有两边实际返回的槽位相同才给出同槽一致或同槽差异。第二来源请求使用第一来源返回的槽位作为下界。池和金库按最新同批原件复验身份，抽样账户的 Token Program、完整 Mint、所有者、原始余额及状态须可重算。缺失账户计入缺失。报告记录两个响应 SHA-256 和实际槽位，页面在持有人证据内展示抽样结果。 [Solana getMultipleAccounts 接口](https://solana.com/developers/docs/rpc/http/getmultipleaccounts)

本机归档重新执行上一节 21 份 DONE 和回执重放。18 份池原件继续通过，独立持有人同槽槽位与已有池槽位交集仍为 0。组合清单 SHA-256 为 `6dddad599ff4d92eb7f3143f2b547bd6afea0bea054f81b047ecc5bb0e409d35`，归档重算结果 SHA-256 `93322b02fcd9e9d058cf570f15cdb72b0ee0917d6e401f8905bc128d1a02c460`。真实归档还没有池和抽样账户在同一批的双来源响应，联合抽样的正例由隔离回归覆盖。

在 `crypto-300-profit-mission/local-agent` 实际执行：

```zsh
uv run --isolated --offline --no-project --with pytest==8.3.5 python -B -m pytest -q -p no:cacheprovider \
  tests/test_meme_pool_vaults.py tests/test_ca_secondary_checkpoint.py tests/test_ca_job_checkpoint.py \
  tests/test_frank_independent_sample_identity.py tests/test_meme_independent_check_lifecycle.py \
  tests/test_meme_independent_error_evidence.py tests/test_meme_independent_full_accounts.py \
  tests/test_meme_pool_holder_roles.py tests/test_meme_wallet_cluster.py
node --test tests/*_ui.mjs tests/test_frank_ca_get_resume.mjs tests/test_frank_ca_report_render.mjs
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 -B "$private/joint-slot-2b4ab742/check.py"
uv run --isolated --offline --no-project --with playwright python -B "$private/joint-slot-72f1bc3b/chrome.py"
```

Python 定向 215 项、Node 269 项通过。Mac Chrome 158.0.8127.38 打开真实前端并展开持有人面板，在四份独立的隔离报告中验证同槽一致、同槽差异、跨槽和矛盾字段省略。0 个页面异常及外部请求，浏览器请求由测试拦截器直接返回，未建监听端口。报告 SHA-256 `71ef01e976971f2a1180a4e132484f1a31528c114fda527f0ed07d6cb75dee79`。同版本检查点用原响应重放两次读取，外部调用为 0。

全量 Python 用 `uv run --isolated --offline --no-project --with pytest==8.3.5 --with numpy python -B -` 启动进程内外连护栏后执行 `pytest.main(["-q", "-p", "no:cacheprovider", "--tb=short", "tests"])`，3,069 通过，1 项 Chrome 用例从全量分开。用 `FRANK_TEST_CHROMIUM='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'` 和 `--with playwright` 运行 `tests/test_frank_rebuild_buys.py::test_browser_default_entry_filters_and_prefills_ca`，该用例通过。

联合抽样源码及隔离验收为 `PASS`。实际双来源联合响应、独立持有人全集、完整 CA 查询的实源时延和候选实际收件仍为待验。整体 `PARTIAL`，本地 8766 切换与生产发布为 `NO_GO`。


## 2026-11-28 Mac Chrome 路径复验与新样本预筛

复验基于 `f68e4490daa2fba246746d2cbd3e2d2639eefb57`。Mac 独立暂存目录的 508 个源码、脚本、测试及项目配置文件逐个与 Git 对象核对，0 个不符。隔离入口使用随机回环端口和已有 `tests/fixtures/frank_parallel_ca_browser_server.py`；只接受合成 CA，分析及行情使用本地预置响应，外连被测试夹具禁止。没有访问或切换生产 Dashboard。

在 Mac Chrome 158.0.8127.38 实际操作：合成 CA A 的摘要和行情来源先显示；把 A 的完整尽调保持在运行中，再提交合成 CA B。B 显示自己的代币身份和两处行情数据来源时，A 仍保留自己的身份且完整尽调继续运行。B 刷新后恢复同一份历史报告，K 线和成交都标记为本机缓存，保持原观测时间。解除夹具等待后，A 完成且没有被 B 的数据替换。此过程验证实际入口的并行、缓存和任务绑定，不是实源延迟测试。对同一暂存源码的定向 Python 139 项、非浏览器 Node 271 项通过。

另用 exact Mint `63jDWWFwp25ChLvsofbVRMprRbhiXuWoWVxrwFfypump`、候选 PumpSwap 池 `6h2yPTQ4CaXcUjMYr6B6MkDmLqTzuLkZuh25aT4thrbZ` 做新样本预筛。只读检查 22 个相关归档目录中的 255 份完成标记和配套报告（21 个唯一任务），未发现该 Mint 或池，范围之外不作保证。公共索引匹配是候选线索而非 finalized 链上证据；本轮测试环境无法直取行情原始响应，未通过另一通道绕过。未运行真实新 CA 提交，也未报告真实冷／热耗时。池与全体持有人同槽、实际双来源联合、候选通知真实送达仍待核实；整体 `PARTIAL`，生产 `NO_GO`。

扩展复验：在正确的仓库目录布局中，另核对 `local-agent` 全部 597 个文件及同级 `meme`、`state` 的 108 个已跟踪证据或状态文件，均与候选树相符。禁外连的全套 Pytest 通过 3,066 项、跳过 4 项。把独立读取确认的 `evidence/frank-ca-local` 固定到 `b9fb6e6df9032a0e6f49c1274bb4ba61c9e4c2da` 后，单独重跑 3 项历史 Git 证据回放，全部通过。合计 3,069 项通过；专用 Playwright 浏览器项未计入。这里不是 CI，也不改变发布门禁。

另在实际 Mac Chrome 的隔离报告中展开持有人面板，分别看到第二来源的已知错误 `HTTP_429` 和未识别错误的通用提示，并明确写明不能给出同槽结论。两个样本均没有显示原始传输地址、人工测试标记或成功的同槽结论。仍是本地合成证据，不代表任何真实来源本轮返回 429。

## 2026-11-28 主线合同复核

复核源码固定为 `544880ab71f1913290069a011b7537b2a8eec380`，按重做反查的 S01–S12、UI01–UI05、C01–C13、F01–F09 对照技术方案和前序 W14 记录。当前分支交付多项实现，仍有实现缺口和发布验收缺口。 [反查清单](FRANK_REBUILD_REQUIREMENTS_20261122.md) · [技术方案](FRANK_REBUILD_DESIGN_20261122.md)

| 编号 | 已有证据 | 未完成或待验收 |
| --- | --- | --- |
| S01–S03、S08–S10 | BP、非 Meme 和失败/被动事件的准入反例已测。两日 437 笔签名、其中 11 笔 Meme 买入独立对账一致。归档重放覆盖游标、过期拦截及回执恢复。 | 更广钱包窗口、复杂交易、不同来源限制下的漏报、链上到真实收件时延及当前候选真实送达待验。 |
| S04 | 分类器保留复杂路由的原件和未决原因，单笔单目标的买入可准入。 | 多个目标币净变化仍整笔进入 `AMBIGUOUS_USER_EXCHANGE_ASSETS`。交易存储以钱包和签名为主键，每签名仅一个交易条目。能逐条归因的同交易多笔独立买入仍无独立输出。已有真实样本表明净扣款与市场对价不同，普适的对价、费用和租金分列仍需逐腿证据。 |
| S05、UI01–UI02、UI05 | 统一「Meme 研究台」、两个主入口和美元格式在隔离 Mac Chrome 验过，旧审计入口可单独回查。 | 买入 HTTP 响应只有本地结果、时间和游标。未追平时的空结果仍写“这段时间没有买入记录”。 |
| S06–S07、S11–S12 | 买入页只显示原计划字段。存在一次性资格采集及历史 USD 旁车读写，未核实价格留空。 | Scanner 消费已存在的资格旁车，新 Mint 的发现和补证仍靠外部调用手动流程。美元批次 34 笔只有 3 笔为可复算的同秒估算，精确美元实付原件为 0，日常数据生成和覆盖验收仍未完成。 |
| C01、C04、C11–C13、UI04 | 精确地址绑定、切池和周期、缓存与回读、隔离的查询并行和反向行情均有证据。 | 已有真实样本的成绩只覆盖行情。新 CA 的首个可用页面、指定钱包及完整尽调仍缺实际实源时延和同池同口径对照。 |
| C02–C03、UI03 | 有中文原文时可以呈现摘要，有可核回帖和引用时分列，CA 认领与叙事分开。 | 仅有外语原件时可显示有限中文主题或来源入口，尚未形成可复核的通用中文摘要链路。真实认领、结构化互动与起源的代表样本待验。 |
| C05–C10 | 已实现若干池布局、原始金库、排名、开盘和钱包历史证据。双来源联合抽样已过隔离回归。 | LP 锁／烧归因、闭户账户全集和终身首买、六类池与不同规模 Mint 的真实代表矩阵、第二来源独立全集和池与持有人的同槽实证仍缺。独立全量来源曾返回 HTTP 403。 |
| F01–F04 | 原有钱包、余额、关注、备注和原币 FIFO 路径保留。索引接口已具备筛选和分页能力。 | 旧签名流水页仍只显示前 200 条，未接分页。真实整仓成本／估值和关闭账户覆盖仍须按证据范围验收。 |
| F05–F06 | 可显式指向既有 RPC 配置，冻结备份和单实例旧版本已核查。按人物与钱包分隔的读取、隔离演练和测试已实现。 | 目标服务器安装、完整状态恢复、续跑、唯一实例和回退无本候选端到端证据。生产 Scanner 与发件准入仍限定 Frank，现有轮询循环中的其他钱包失败可中断同轮后续钱包处理。 |
| F07–F09 | 源码、计划、测试及脱敏验收记录可从 Git 复查。三个草稿 PR 已建。 | 统一验收脚本只在草稿 #257。当前分支执行 `python3 -B -m scripts.accept_frank_rebuild --source-sha 544880ab71f1913290069a011b7537b2a8eec380` 返回缺少模块。同一 HEAD 无 GitHub check run，验证结论使用本机证据。 |

两项页面反例在 Node 中直接执行该版本的实际渲染函数。其一，传入空结果及未追平标记，页面仍写“这段时间没有买入记录”。其二，传入 201 条本地签名，页面渲染 200 行，入口无下一页。同一候选的定向 Python 124 项、CA 渲染与恢复 Node 218 项通过。Mac Chrome 和禁外连全量通过记录见上一节。8766 实际静态资源的 SHA-256 与旧候选一致。本次只补充状态与审计记录。

## 2026-11-28 固定版本验收入口与旧流水页修正

在固定干净检出中，从 `crypto-300-profit-mission/local-agent` 运行：

```sh
python -B -m scripts.accept_frank_rebuild --source-sha "$(git rev-parse HEAD)"
```

默认退出码 2 代表本地检查通过但真实验收仍不完整；退出码 1 代表失败。只在想单独运行本地检查时显式加 `--allow-partial`，这不会改变 JSON 中的 `release.status=NO_GO`，也不会跳过显式指定的窗口或时延门禁。发布应读取真实 CA、池与完整持有人同槽、受众送达等独立字段，不可仅以进程退出码判定。可附独立已终结窗口、冻结 SQLite 快照和资格文件及其 SHA-256，以及可信绝对归档目录。旧买入仅按待审核原始证据与钱包、签名、槽位、交易时间及不可变摘要匹配后重放；未知成本继续不进严格准入。检测和入库仍各用原有最近秩 P50/P95 和独立未知分母。未发送实际通知。

买入结果为空时，页面说明本地暂无符合筛选的核实记录且不能推断链上没有买入。旧签名页改为每页最多 200 项，可前后翻页，搜索仍覆盖同一份已装载的本地时间窗口，不增加 RPC 或分页 HTTP 请求。405 条合成记录在隔离 Mac Chrome 验证可进入显示 201–400 条和 401–405 条的页面，并全范围查回第 405 条。校验命令在隔离干净 Git 检出中执行，364 项定向 Python、219 项定向 Node 通过，JSON `PARTIAL`、退出 2；独立 Node 扩展共 272 项通过。实际 Chrome 为人工隔离验证，不计为 runner 中的 `--chrome`。生产未切换。

F06 本地隔离补验：一钱包时钟失败时仍请求同轮其他钱包，扫描失败后仍保留其他钱包各自持久化结果。任何失败仍令整轮进入重试，不推进共享模型，不尝试通知，也不写成功首轮标记；全部成功才用最早的 finalized 时钟。真实 Scanner、临时 SQLite 与合成 RPC 复现首个钱包游标缺口、后一个钱包入库且 outbox 空；另测时钟失败与成功顺序。定向 Python 99 项通过。未更改启用人物范围、未运行服务或真实来源、未部署。

### S04 同签名多笔直接买入：一期证据

一期只认同一成功签名中多个独立的 Raydium CPMM 直接 swap 调用，且使用经典 SPL Token。逐条核对顶层指令 discriminator 和参数、签名付款人、对应的输入/输出金库、两条直接内部转账、各账户前后余额，以及精确目标 Mint。两笔可共用钱包报价账户，但每笔扣款必须能绑定到各自调用，账户合计必须守恒。不支持共用路由、Token-2022、关户/临时账户、缺原始角色或余额。只增加按签名和指令序号定位的离线研究凭据；不改原交易表、买入列表、持仓或通知。 [Raydium 原始指令源码](https://github.com/raydium-io/raydium-cp-swap/tree/3d69122790e97cd6aff24e8ba95940793773f58c/programs/cp-swap/src/instructions)

隔离夹具确认同签名第二笔也有自身支付与数量、原账本持久化仍只有一条签名和零笔交易/通知；通过路由、重复 CPI、错误金库、错签名、金额或余额不对、额外转账等反例。冻结原件 10,895 条逐条核对哈希后回放，本归档没有包含两个顶层 CPMM 调用的样本，真实正例覆盖为 0，不据此估计总体漏报率。定向 Python 152 项通过，1 项专用浏览器测试未运行。是否有足够真实正例，以及独立买入的投影、入库和页面，从本轮开始分别跟踪。
