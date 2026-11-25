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
