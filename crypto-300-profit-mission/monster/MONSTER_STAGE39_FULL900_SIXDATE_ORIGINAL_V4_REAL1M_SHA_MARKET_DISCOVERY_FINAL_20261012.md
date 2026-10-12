# Monster Stage39 — USD-M 900符号×6七日窗口完整市场原V4真实分钟发现研究（2026-10-12）

## 状态和设计约束

**已验证事实：Stage39 36个原始源码分片全成功 + 36份ZIP/JSON SHA重新下载验收 + 5,400币日期逐行审计 + 原Stage38全部172试点信号时间原样一致，完成全市场历史研究归并并写入原Draft PR #30。** [长期开发规则](MONSTER_MODULE_DEVELOPMENT_RULES.md)优先级未改变：妖币尽早发现、真正有效提前量、普通币噪声、真实可交易性；BTC不作为目标交易策略，不研究任意固定持仓时间来替代妖币发现。不改V4生产、Frank、Gmail、Mac和自动交易。

冻结合同：[Stage39事前全体900×6研究协议](evidence/monster_stage39_usdm_full900_sixdate_1m_original_v4_prereg_20261012.json)，原提交 `2cb70d611395c0f74816aeab19628d7f9d81e8d2`。研究日期：2025-01-19、04-19、07-19、10-19、2026-04-19、07-19，均UTC06:00起点至未来168h，覆盖[Stage37源完整及缺档底册](evidence/monster_stage37_sixdate_all5400_usdm_source_and_GT.csv)冻结900个USD-M归档原始USDT符号，每日期900、没有使用未来价格挑观察币。

**原样运行的生产规则**：每个官方逐日1分钟ZIP发布者SHA检验，连续1440分钟/日，24h热身 + 168h 3m轮询3360次；实际调用未改动的生产 `observe_snapshot(...,venue=futures)` / `process_queue` 及原5m收盘K线。每币日期一独立SQLite，所以**没有**复现跨币全局8并发D1队列/实际通知时延；不得称是真实本机运行/盈利验证。回放源码：[Stage39全量1m真实扫描](../local-agent/scripts/monster_v4_stage39_usdm_all900_sixday_original_1m.py)，[Stage39原始36份ZIP和GT完整汇总器](../local-agent/scripts/monster_v4_stage39_original36_source_sha_full_market_aggregate.py)。

## 正式验收链和永久Git资料

- [Stage39全部36分片真实源CI #38208358036](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38208358036)：**36/36 SUCCESS**。原源包括官方USD-M 9天每日1m发布方ZIP SHA与Stage37月度1h官方SHA，不从1h虚构3m/24h成交额/原V4信号。
- [Stage39下载全部36原Artifact再算SHA、校对前一阶段172案例和汇总CI #38208549727](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38208549727)：**SUCCESS**，已提交PR分支Git `ab62c20a487e73a79f5abd2b725283b91925a50f`（数据固定版）。
- 长期可复查的三份机器证据：[原始36 SHA收据/完整类别及日期统计](evidence/monster_stage39_36original_SHA_all5400_futures_discovery_summary.json)、[全5400币日期逐条原始状态/分钟1m SHA/V4 WATCH+SETUP时间](evidence/monster_stage39_all5400_usdm_real1m_originalV4_cases.jsonl)、[原52个1h历史2×机会与实际1m越线/WATCH分类CSV](evidence/monster_stage39_realminute_gt2x_event_registry.csv)。
- 原CI聚合Artifact ID `11728582164`，ZIP SHA256 `4198dbc73d352209c96756a24e0d983714cf31c6647a51ad53b3d3df9a23d817`；另从GitHub下载，独立检查ZIP CRC全部PASS、解压5400行并重新计算如下全部主指标，与Git汇总相符。原36份ZIP/内部JSON SHA全保留在汇总证据。

## 全市场实际结果 — 不能再用赢家富集样本当假阳性分母

| 历史币日期/事件 | 实测 | 精确定义 |
|---|---:|---|
| 六周内的USD-M归档USDT符号日期 | **5,400** | 每周900个，包含缺档，不能称5400个真实可交易永续币 |
| 1h源完整（Stage37） | 3,333 | 尚未排除逐分钟缺源冲突 |
| 真实官方1m及1h连续且结果一致 | **3,283** | 真实原V4可评分分母 |
| 不可评分 | 2,117 | 其中2067旧阶段1h源缺、3个日度分钟缺档、47个1h与1m正式来源价格冲突 |
| 未来168h小时HIGH触及2× | **51** | 首小时open为定价基准，未来 HIGH是事实标签，不是成交价 |
| 严格首次2×的1m HIGH之前WATCH | **48** | 48/51=94.1176%，本研究范围/历史口径 |
| 同分钟才WATCH / 晚WATCH / 无WATCH | 1 / 1 / 1 | 不能当提前发现 |
| 未来5× / 10× | 1 / 0 | ALPACAUSDT未来5×提前WATCH；无10×召回分母 |
| 非2×且源完整的币日期 | **3,232** | 所有历史普通对照，不再只是抽样120 |
| 普通对照中至少一次WATCH | **433** | 433/3232=13.3973% |
| 有WATCH的全部源完整币日期 | **483** | 其中50个事后2×（含2个过晚/同分钟），433个未达窗口起点2× |
| 全部WATCH事件（重复计入） | **1,108** | 6×7=42天里历史理论平均26.38条/天；非实际投递数 |
| 每币独立状态机的D1 SETUP | **895** | 历史独立状态机事件，跨币并发全局队列未复现，非真实邮件 |
| 最近一条真正提前WATCH距首次2×的中位提前量 | **107分钟** | 48个提前事件；46个≥5m、39个≥15m、30个≥60m |

**核心区分：** 50/483=10.35%只表示「WATCH过的币日期里，未来168h的HIGH曾触及该窗口*固定起点*2×」；48/483=9.94%为其中真正提前WATCH事件占所有WATCH币日期的比重。**二者都不是WATCH价格买入后翻倍的概率、分类器正式Precision、真实亏损概率或正收益**。433个无日历2×的WATCH并非433个完全无交易机会的骗局；可有较短、更低涨幅，仍需因果行情分析与当时盘口验证。

## 不同日期的噪声与暴涨机会

| UTC06窗口 | 1h/1m双源完整 | WATCH事件总数 | WATCH币日期 | 未来2× | 严格提前2× | WATCH而未达日历2× |
|---|---:|---:|---:|---:|---:|---:|
| 2025-01-19 | 384 | 78 | 36 | 0 | 0 | 36 |
| 2025-04-19 | 433 | 241 | 100 | 19 | 17 | 82 |
| 2025-07-19 | 493 | 129 | 75 | 8 | 8 | 67 |
| 2025-10-19 | 572 | 197 | 80 | 10 | 9 | 70 |
| 2026-04-19 | 663 | 261 | 113 | 9 | 9 | 104 |
| 2026-07-19 | 738 | 202 | 79 | 5 | 5 | 74 |
| **合计** | **3,283** | **1,108** | **483** | **51** | **48** | **433** |

**风险不能忽略**：虽然2026-04这一周出现9个2×，普通WATCH仍104个币日期；且共261条WATCH事件，简单全部发邮件会造成明显负担。只做增强排序、不改D0基础早发现，后续需要独立衡量用户实际处理能力和多次重复触发。

原Stage36识别出428个名字不在现货758研究名单的USD-M历史档案：本阶段在有效分钟数据中，**21个该类符号实际2×均严格提前WATCH**（21/21）。这些并非已核实21种**合约专属加密货币**；部分2026年档案出现股票名称、ETF/RWA及1000倍单位命名。禁止通过符号字符串做合约乘数或经济标的身份确证，也不应直接合并到现货可买名单。

## 主要漏报、迟报以及数据冲突（仅服务事实可信度）

- 2025-04-19 CETUSUSDT：2025-04-25 01:10 UTC真正1m HIGH达2×，06:30才WATCH（晚320分钟）。
- 2025-04-19 PENGUUSDT：2025-04-25 13:09 UTC真越线，整个168h无WATCH。
- 2025-10-19 FUSDT：2025-10-21 05:12 UTC同分钟才WATCH，不是提前。
- 2025-01-19 TRUMPUSDT：源1h归档有2×标签，但历史分钟连续性不通过，**不计为V4漏报或正确命中**。
- 47个官方1h和1m价格源互有冲突，**2026-07-19一周45例，其他2025-10与2026-04各1例**。不只有RWA/股票代码，亦包含AIXBT/ANIME/LINEA等加密符号；根因未证实，保留真实双方价格及官方源SHA、不人为「纠正」至一致、不纳入负例或胜率。另有3个真正分钟缺档。由于该缺口小于全3,333个1h完整数据但具有日期集中性，不能称所有Crypto都无此问题。

上述症状与Spot阶段部分例子相似，但不同venue同symbol的样本不应伪装成真正独立的跨日期验证。

## 开发顺序与下一步主线

**Stage39 = 源36/36 + 独立SHA聚合 + Stage38 172例原样比对PASS；第一阶段核心Spot及USD-M官方历史发现/普通币数据已具备足量研究事实。** 但是**整个Monster模型验证仍未完成**：518?（注意：本报告没有声称其它链或point-in-time全交易所覆盖）、历史上市资格/股票RWA真实合约类型、真正订单簿/成交、全市场共享D1的排队压力、未知日期样本外收益仍缺失。不得把这些研究缺口涂成PASS。

下一步优先从事实转入**正式WATCH/D1/IGNITION分层及指标方案（先明确预期发现率、有效提前量、重复消息负担、净可实现收益条件和弃用条件）**。不能因这18日期Spot和6日期USD-M已经曝光就直接在相同历史片段改阈值并宣称优选成功；应冻结新策略候选，锁定额外事前未看标签的日期用于真正独立回测，测量从WATCH当时价格到后续high的因果涨幅、可得盘口深度、拥挤和成本，而不是把回测中的最高价视为可成交卖出价。之后严格进入技术方案、同代码回测、真实其他AI独立Review、修复测试、授权Mac隔离部署。

状态：`FULL_STAGE39_DISCOVERY_HISTORICAL_DATA_ANALYSIS=PASS`；`MARKET_WIDE_REAL_FUTURES_1M_REPLAY=PASS`；`NEW_IGNITION_OR_BUY_RULE=NOT_DESIGNED_OR_VALIDATED`；`TRUE_FORWARD_EXECUTABLE_PROFIT=UNVERIFIED`；`OTHER_AI_REVIEW=NOT_DONE`；`MONSTER_DEPLOYMENT=NO_GO`；`GMAIL=OFF`；`AUTO_TRADING=NO_GO`；`FRANK=UNCHANGED`。
