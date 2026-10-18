# Monster Stage163 — Claude Haiku 5.5 定向审核 REQUEST_CHANGES → 官方后置报价 V2 修复（2026-10-18）

## 结论及唯一有效证据

**本轮作者修复与 CI：PASS；其他AI对新固定代码的独立复审：NOT_DONE。** 上轮 Claude 聊天审核 V1 固定 SHA `e860c1aa6485c453f99a1a17c207670a3685eb85` 为 `REQUEST_CHANGES`，审核底层模型自述 Claude Haiku 5.5，准确底层版本`UNVERIFIED`。报告指出 P1=1/P2=2：不能把T0之后才收到的BBO称为可在T0使用的盘口、不可将511个Spot/USDT TRADING合格分母称为所有Binance Spot、行情端点与交易对目录不一致的3项身份不应静默丢弃。旧报告没有被修改或重新写币价，它在本PR仅作为历史V1不可用于T0交易因果证据。

**本轮唯一V2固定代码/测试/工作流SHA：`4c6bff916bb432ba778c59e6283c5a75e2902293`。** 定向比较基线选上轮V1报告发布完成的Git SHA `0bc71dc9642023371d362bca435f909e721f5e01`，固定diff只包括**3个可执行文件**：
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage163_spot_t0_quote_friction.py`
- `crypto-300-profit-mission/local-agent/tests/test_monster_v4_stage163_spot_t0_quote_friction.py`
- `.github/workflows/monster-v4-stage163-offline-spot-t0-511-friction.yml`

运行新固定 [GitHub Actions #39083479916](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39083479916) **SUCCESS**、10/10实际测试PASS、严格打开存Git原 ZIP和6份HTTP原始SHA回执、计算全511行并由真实CI回传新文件（原V1不覆盖）。独立保存全量机器JSON： [**V2 post-T0 511逐币证据**](evidence/monster_stage163_spot_post_t0_original511_quote_friction_v2_actual.json)，Git Blob精确`0f6e63829c39ff28ce41b02e5ae08ed536414f2c`，`schema=MONSTER_STAGE163_SPOT_POST_T0_RECEIPT_BOUNDED_511_FRICTION_NO_TRADES_V2`。V1历史存Git文件 `evidence/monster_stage163_spot_t0_original511_quote_friction_actual.json` 保留原字节和Git Blob `d2df270708b48d1b374aa314b25e848ae12cbd75`，但其T0标签的因果含义**已被此V2明确纠正**。

## 一、P1：所有盘口报价均发生在exchangeInfo T0 **以后**

原时间锚点是**Binance exchangeInfo.serverTime = 2026-10-17T22:04:40.094Z**，并非所有REST行情接口收包时刻。读取同一永久归档ZIP并由 `source_receipts.json`实际`start_utc/end_utc`计算出：

| 端点 | 客户端请求起点（相对于交易所T0） | 响应全部接收（相对于交易所T0） | 真实回执UTC |
| --- | ---: | ---: | --- |
| `bookTicker` | **+2561.682毫秒** | **+4349.393毫秒** | 22:04:42.655682Z ~ 22:04:44.443393Z |
| `ticker24` | **+4349.727毫秒** | **+6835.464毫秒** | 22:04:44.443727Z ~ 22:04:46.929464Z |

**跨客户端UTC与交易所serverTime比较属于近似，以上是HTTP接收区间而非交易所逐币事件/逐笔报价时间戳**；不知道请求接收之前报价形成了多久，不能宣称每一币的盘口年龄或每币种自身更新于上表起止内。整份quote+b24h资料可供下游读取的保守收包下界为 **2026-10-17T22:04:46.929464Z**，T0时刻绝不可提前利用。新JSON明确：
- `post_t0_receipt_windows_vs_exchangeinfo_t0_approx`两端点四个偏移量（同时保存原start/end UTC）；
- `quote_bundle_not_available_until_client_receipt_utc`；
- `receipt_offsets_are_cross_clock_approx_not_exchange_quote_event_timestamps: true`；
- `t0_causal_quote_at_t0_proven: false` 与 `eligible_for_t0_asof_executable_execution_or_signal_backtest: false`；
- `historical_post_t0_quote_receipts_once_not_forward_live_signal: true`，原误导性的 `historical_T0_observed_once_not_forward_live_signal` 不再输出；
- 时间校验遇到倒序、或声明post-T0的收包早于T0，fail-closed拒绝；没有用硬设「1秒以内」阈值强行伪装真正T0。以**准确改名与禁止T0因果使用**履行Claude建议的二选一修复方式。

即使整批所有行以同一个被校验的bookTicker原HTTP响应计算，不能把它解释成T0已有买入报价，也不是11:00行情、现时报价或交易所认证的每笔订单可成交深度。

## 二、P2：清楚区分511合格USDT现货对、所有USDT、所有Spot及跨端点新增代码

直接从 `exchangeInfo.symbols`的原3729身份逐级复算，**不是代码写死展示True/借511代表所有Spot**：

| 实际exchangeInfo人口 | 数量 |
| --- | ---: |
| 全部身份记录（包含各种币对） | 3729 |
| quoteAsset=USDT（各种现货许可与状态） | 765 |
| USDT且TRADING且isSpotTradingAllowed不为false | **511** |
| USDT但BREAK（全部许可状态） | 254 |
| 其中BREAK且允许Spot | 214 |
| BREAK且明确不允许Spot | 40 |
| USDT、TRADING、明确不允许Spot | 0 |

V2输出逐项 `population_counts_from_exchangeinfo` + `population_definition`、`population_scope_is_all_binance_spot=false`，`complete_archived_exchangeinfo_t0_eligible_cohort_represented` 通过**511输出币集合与从来源推导的 eligible币集合一致**得出，不再硬编码一个会被误读为全市场的`True`。代码保留 `EXPECTED_ACTIVE=511` 只是**本次单一已锁定真实source档案的人口漂移拒绝门槛**，不能当作未来任意Binance市场永远511的业务假设。

进一步把仅在后续 bookTicker/ticker24 列表出现、exchangeInfo当时身份缺失的精确 `AXSBIDR`、`NBTBIDR`、`NBTUSDT` 以 `excluded_market_symbols_not_in_exchangeinfo` 字段**逐端点留痕**，绝不默认为新上市时间已由这些端点证明（跨端点不同时间只能说明人口不一致）。这些项目不进入原固定T0合格511分母，分类漂移可供以后判断上新/暂停变化，不能随意改写原T0人口。

## 三、P3与原统计保持

新测试覆盖从真实官方ZIP复读、精确偏移、相对T0时序倒置/提前拒绝、BREAK两种Spot许可、TRADING禁止Spot、非USDT、只在bookTicker出现符号留档、无档/重复、锁定盘口`ask==bid`或买卖档数量为0/异常值拒绝、显式研究金额等。原6项+4项=**10项**全通过。可选金额展示字段更名 `research_notional_displayed_top_level_size_coverage_only`，明示**仅旧单点顶层显示数量检查**，并非实际可成交保证。没有用户授权金额时 `UNKNOWN_NOT_SPECIFIED`，没有隐含30U/300U交易量。

在**相同真实原始511个币和报价**下，数学输出不变：bookTicker价差 `p10/median/p90 = 2.060793 / 11.217050 / 28.971511 bps`，同一报价`ask→bid`理论摩擦中位 `11.210762 bps`，卖一/买一显示金额中位 `357.509800 / 332.814150 USDT`。它们是**T0后单批REST旧价差分布**，绝不是T0同时全市场可以买的行情。不能将旧档案与Stage30/152历史WATCH入场或Stage163未来SETUP成交时间拼成伪样本。

本研究的全部资产业务结论均未改变：`G4 UNKNOWN / G6 NO_GO`，`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。真实历史出场L2、手续费阶梯、实际成交回执和连续市场信号均不存在。未启动任何定时采集、Mac程序、Frank、Gmail、交易。Stage163固定7日未来Spot分钟窗口 `[2026-10-17T22:06Z,2026-10-24T22:06Z)` 仍未成熟，单点旧价差不得升级其G4/G6。

## 四、固定SHA独立其他AI局部复审任务（尚未完成）

**请将下文复制给Claude（聊天窗口）或另一独立审核者。此次只审其上轮三个问题与直接回归，旧的独立重算价差无须无意义地重做无关研究。**

> 请定向独立复审 Mission `lxxlx2/ChatGPT_mission_record` 的 Draft PR #30，分支`research/monster-v4-local-discovery-20261010`。**唯一新代码审核固定SHA `4c6bff916bb432ba778c59e6283c5a75e2902293`，定向比较基线 `0bc71dc9642023371d362bca435f909e721f5e01`**；上一次由Claude Haiku 5.5聊天窗口审 `e860c1aa6485c453f99a1a17c207670a3685eb85` 给 `REQUEST_CHANGES`，实际CLI/统计均正确但P1是T0后2.56~6.835s的报价被误说成T0价；P2是511范围错误暗示全Spot，另3个只出现于行情端点的币被静默忽略。请使用固定SHA checkout+git diff实际核对三个可执行文件：`crypto-300-profit-mission/local-agent/scripts/monster_v4_stage163_spot_t0_quote_friction.py`、`crypto-300-profit-mission/local-agent/tests/test_monster_v4_stage163_spot_t0_quote_friction.py`、`.github/workflows/monster-v4-stage163-offline-spot-t0-511-friction.yml`。原官方Binance Spot HTTP ZIP SHA256 `b47e206345c0a04b16b37c38795d726553ef83ca679f443f9fba89805483216b`、receipt六份HTTP SHA不变，**绝不覆盖**原V1 JSON。验证原T0为`2026-10-17T22:04:40.094Z`，bookTicker client start/end相对T0+2561.682/+4349.393ms、ticker24+4349.727/+6835.464ms，输出真实UTC与收包bundle可用下界22:04:46.929464Z；这是跨本机与交易所时间的估计、非逐币事件时钟，不得暗示T0因果可用。检查`t0_causal_quote_at_t0_proven=false`和`eligible_for_t0_asof_executable_execution_or_signal_backtest=false`；构造回执日期倒序、假post-T0反例，应fail-closed。验证人口总3729、USDT765、TRADING Spot-eligible511、BREAK254（允许214、不允许40），其它Spot现货不在511分母，`complete_archived_exchangeinfo_t0_eligible_cohort_represented`需由源码真实集合检查推导而非写死；核验多端点出现但T0身份不存在的`AXSBIDR`、`NBTBIDR`、`NBTUSDT`被逐项输出。核验原始源报价价差数值未变、`research_notional_displayed_top_level_size_coverage_only`不能推成成交、lock/0 qty被拒绝。真实运行`python3 -B -m unittest discover -v -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_stage163_spot_t0_quote_friction.py`和只读`python3 -B crypto-300-profit-mission/local-agent/scripts/monster_v4_stage163_spot_t0_quote_friction.py`，独立看CI `https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39083479916`是否真实10/10通过及job成功；V2机器源码结果Git Blob `0f6e63829c39ff28ce41b02e5ae08ed536414f2c`，历史V1 Blob `d2df270708b48d1b374aa314b25e848ae12cbd75`，确认旧文件未被覆盖。报告固定SHA/Reviewer和底层准确模型版本（无法核实填UNVERIFIED）及 `APPROVE / REQUEST_CHANGES / BLOCKED`、P0/P1/P2、可重复反例和准确文件行号。上轮既有价差算术无需重复排查无关问题；若访问CI失败标`UNVERIFIED`，不可推测已运行。不得宣称模型盈利、T0 BUY、真实盘口可执行、邮件/Frank/Mac上线。保持G4 UNKNOWN、G6 NO_GO及NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE。

**当前状态**：`AUTHOR_FIXED=YES / ARCHIVED_SOURCE_AND_CI=PASS / NEW_EXTERNAL_REVIEW=NOT_DONE / T0_CAUSAL_QUOTE=NO / G4=UNKNOWN / G6=NO_GO`。只有独立复审真正反馈并写入Git后才能对新SHA写`APPROVE`。
