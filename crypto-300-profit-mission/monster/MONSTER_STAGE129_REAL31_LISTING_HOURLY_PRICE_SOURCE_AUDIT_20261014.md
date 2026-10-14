# Monster Stage129：31个窗口内潜在新上市合约，真实历史行情来源全覆盖及2个遗漏2×候选

2026-10-14 Asia/Bangkok。唯一 [Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。**来源为 Binance 官方连接器返回的历史 USD-M 一小时 K 线结构化数据，覆盖原历史窗口，而不是本轮实际新的市场即时快照。没有批准任何自动化、交易、Gmail或Mac部署。**

## I. 先冻结31个案例，再读取涨跌

首先从 Stage128 固定文件 [31个窗口内 later-onboard 与15个历史时钟冲突](evidence/monster_stage128_31_later_listings_and_15_historical_clock_conflicts.json) 中选择全部且仅选择31个类别为 `IN_WINDOW_LATER_ONBOARD_NOT_HISTORICALLY_PROVEN` 的 symbol-date 组合，**没有读取其未来行情或赢家再筛样本**。正式先验计划 [Stage129 全31历史1h研究合同](MONSTER_STAGE129_FROZEN_31_IN_WINDOW_ONBOARD_HISTORIC_HOURLY_TRIAGE_20261014.md) 已提前提交，SHA `044a5f63f2da3621b600d8e5131ddb393105e328`。

全部31个合约均请求 Binance USD-M 原生官方连接器 `get_futures_usds_kline_candlestick_data(symbol, interval=1h, startTime=锚点06:00 UTC, endTime=锚点+168h-1ms, limit=500)`，实际返回数据保存为六个历史锚点独立 Git 原始**结构化**源文件，没有遗漏平盘、负例或 TradFi：
- [2025-01-19 5个](evidence/monster_stage129_20250119_fixed_listing_candidate_usdm_1h_source.json)
- [2025-04-19 5个](evidence/monster_stage129_20250419_fixed_listing_candidate_usdm_1h_source.json)
- [2025-07-19 5个](evidence/monster_stage129_20250719_fixed_listing_candidate_usdm_1h_source.json)
- [2025-10-19 4个](evidence/monster_stage129_20251019_fixed_listing_candidate_usdm_1h_source.json)
- [2026-04-19 4个](evidence/monster_stage129_20260419_fixed_listing_candidate_usdm_1h_source.json)
- [2026-07-19 8个](evidence/monster_stage129_20260719_fixed_listing_candidate_usdm_1h_source.json)

**数据证明级别限制：** connector 提供原始字段的结构化数组，并没有 HTTP/TLS 原始 byte receipt 和 Binance Data Vision publisher SHA。后来的 Stage123 Binance `onboardDate` 只用作后验参照，不是2025年的 point-in-time listing certificate；不能通过现有时间对齐就声称正式 G0 验收。

## II. 真实数据结果

原先 Stage37 使用“整个168小时从窗口起点连续有1h”的条件，因此中途才有 K 线的合约被 Stage37 标成 `CENSORED_NOT_168_CONTIGUOUS_HOURS`，无法进入后续完整分钟 D0 / 2× 统计。此次新研究保留**上市后首次实际观测1h→原七日窗口结束**的独立价格样本，不擅自把新合约的首次开盘当成七日锚点不存在的开盘价。

| 指标 | 结果 |
| --- | ---: |
| 固定真实来源查询案例 | **31/31** |
| API 查询返回非空历史1h | **31/31** |
| 首次有资料的小时到原七日窗口结束，无1h缺口 | **31/31** |
| 以上区间最高1h HIGH相对首次1h OPEN ≥2× | **2/31** |
| 相同口径 ≥5× 或 ≥10× | **0/31** |
| Stage93 冻结旧51 2×分母新增的已认证病例 | **0**（原分母原样保留，不能合并两种起点） |
| 新正式 G1 实证通过 | **未完成 / NOT_SCORABLE** |
| 真实手续费净利润 | **UNKNOWN** |

发现两个原 Stage37 整周准入看不到、但此后历史小时价格确实达到 2× 的具体候选：

| 合约及历史七日锚点 | 1h资料首次起点 / 首根 OPEN | 首次≥2×的小时（仅小时内HIGH） | 全段实际最高HIGH | 倍数 |
| --- | --- | --- | ---: | ---: |
| `VINEUSDT` 2025-01-19 | 2025-01-24 10:00 UTC，0.2019400 | 2025-01-25 04:00 UTC | 0.4356000 | **2.1571×** |
| `APRUSDT` 2025-10-19 | 2025-10-23 10:00 UTC，0.3130000 | 2025-10-23 23:00 UTC | 0.7500000 | **2.3962×** |

两次涨幅与时间仅来自实际已返回且 Git 保留的一小时 OHLC。**OHLC 的 HIGH 不意味着在该价可买卖，更不能证明 D0 已早报。** 先发现它们的原因是对“中途上市被排除”作固定全量来源审查，不允许把它们事后作为新策略 OOS 胜利。

根据已经归档 Stage123 交易所**后来的标签**：31个内20个 `underlyingType=COIN`、7个 `EQUITY`、4个 `HK_EQUITY`。其中 VINE 当前标签 `COIN/Meme`，APR `COIN/Alpha,Crypto`；股票/港股相关11个属于本研究 Crypto 范围之外的 **潜在**候选，但仍需其历史时点类别来源核实，不能直接依赖今天字段删改历史分母。准确 Crypto 发行方和1000合约基础量纲仍未独立认证。

## III. 离线复算与工程状态

- 源严格冻结后实现 [Stage129 31源小时检查程序](../local-agent/scripts/monster_v4_stage129_new_listings_hourly_recovery.py) 及 [测试](../local-agent/scripts/test_monster_v4_stage129_new_listings_hourly_recovery.py)。核对 6 原日期，全部31个 exact symbol、请求参数、12列1h K线价格合法性、无重复/无时间缺档、卖高点相对首根open的价格代理，来源不足时 `CENSORED`，未观测不当 0、没有现货成交结论。
- 六份实际源文件在 Git 中有各自确切 blob SHA，并由两平台 CI 的 `git hash-object` 验证后才能运行分析。
- [macOS + Ubuntu CI #38562865049](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38562865049)，测试代码 SHA `bdc21fe2cee8f8cd16a7a329b05395ea32913d7e`，实际两个 OS job 均 **SUCCESS**；全部31行与 gross 2×=2 的对账跑通；两系统机器 summary 完全一致。
- 机器摘要永久 [Stage129 完整原31统计](evidence/monster_stage129_fixed31_historical_hourly_exposed_source_machine_summary.json)。完整31行分析记录在 CI artifacts，可依 Git 的六份真实来源和已提交同代码独立重放。
- 旧 Stage93 51个源完整两倍机会、48个首次早5分钟和旧 Stage118/127 REJECTED 保持原样。

## IV. 核心意义与下一步

已经发现一个**真实业务层面的早报样本缺口**：对新上市币实行“过去168小时完整行情”门槛，会把真实进入窗口后才上市、之后可能上涨2×的候选直接排除，至少有2个实际历史涨幅代理案例。若要真正提高Monster早期发现能力，需要在全市场人口账本中独立引入 **D0_NEW_LISTING / FIRST_LISTED_MINUTE** 研究支路，并从官方最早1m/3m的源时间严格因果计算，不假设已有60分钟/24小时暖机行情，更不能降低旧原模型阈值声称成绩提高。

下一阶段先针对 VINE、APR 以及完整31个固定候选取得 publisher-SHA 验证的一分钟片段和历史上市时间证明，核查首次可见一分钟到2×的实际先后，判定早报能否提早5分钟、有没有可执行的深度及后续退出。所有普通币和负例继续保留；只有在事先预注册新策略、取得真正未知完整市场日样本并满足 Stage77 G0–G4后才能宣称策略有效。

`STAGE129_FROZEN31_BINANCE_HOURLY_HISTORICAL_SOURCE=ARCHIVED`; `STAGE129_31_CONTIGUOUS_HOURS_TO_WINDOW_END=YES`; `STAGE129_EXPOSED_NEWLISTING_GROSS_1H_GT2=2`; `INDEPENDENT_CRYPTO_ASOF_G0=PARTIAL`; `TRUE_G1=NOT_SCORABLE`; `G2_G3_STAGE118_STAGE127=REJECTED`; `G4_EXECUTABLE_NET=UNKNOWN`; `OTHER_AI_REVIEW=NOT_DONE`; `MONSTER_DEPLOYMENT=NO_GO`; `FRANK=UNCHANGED`; `GMAIL=OFF`; `NO_AUTOMATIC_MONITOR_CREATED`.
