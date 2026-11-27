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
