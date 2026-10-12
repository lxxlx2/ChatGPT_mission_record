# Monster Stage38：USD-M合约真正1分钟行情，原版V4提前预警与普通合约对照

日期2026-10-12（曼谷）｜研究专属[原 Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)｜本轮严格遵守 [Monster模块长期开发与放行规则](MONSTER_MODULE_DEVELOPMENT_RULES.md) 第一阶段事实/模型能力数据分析。**没有修改原V4阈值、没有BTC交易、没有持仓时间、没有Mac部署、新邮件或自动交易。**

## 一、基线、先冻结再读真实官方分钟数据

- 前序[Stage37官方USD-M全部900符号×六日期GT与源审计](MONSTER_STAGE37_FUTURES_FULL900_SIX_DATES_2X_5X_10X_GROUND_TRUTH_20261012.md)已确认5400符号日期尝试、3333个发布者SHA且连续七日1h源完整、52个七日事后2×高价事件。原[全5400行情身份与源分类CSV](evidence/monster_stage37_sixdate_all5400_usdm_source_and_GT.csv) Git blob为 `4b02019195a7a48ef6d33606db9b57d6a3429f4b`。
- 在读本轮分钟行情**之前**先提交[Stage38 52赢家+6日期各20普通非2×对照共172案例冻结合同](evidence/monster_stage38_futures_original_v4_causal_pilot_prereg_20261012.json)，commit `447d82d20530c9d48a1d1add14c408cc81e0b642`。普通对照从每个日期原3333完整1h币日期中的非2×集合，使用 `SHA256(date|symbol)` 升序取20，未用其它未来指标挑普通币；**整体是事后已知赢家的富集样本，绝不是均匀抽全市场，也不是新样本外收益验证。**
- [Stage38真实原生产函数调用源码](../local-agent/scripts/monster_v4_stage38_usdm_original_v4_1m_pilot.py)强制验证原 `monster_v4_shadow.py` 代码 Git blob `bc958b3d90a8a52afa51515cb53f7e5fafaffaaa`；一个合约一份持久168小时SQLite，3360次原3分钟轮询，分别调用生产 `observe_snapshot(db,"futures",...)` 与 `process_queue`。用每次已经闭合的1m close和此前1440根真实1m quote成交额代理，1m→闭合5m原函数构建D1输入。**场内不同合约的共享D1排队容量未重现，不得冒称全球队列真实模拟。**
- 每个完整案例需要实际从官方Binance `data/futures/um/daily/klines/[SYMBOL]/1m/`读取**9个日度1分钟档案+各自官方`.CHECKSUM`**，每档严格连续1440根、微秒时间戳规范化；提取精确192h：24h滚动成交额热身+168h探测。不能拿原Stage37 1h GT代替一分钟扫描，未来HIGH仅用于扫描后独立评分。首次2×真分钟HIGH时间严格小于WATCH时才算真正提前，同分钟视为不提前。
- 首版 [Stage38源CI #38207595586](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38207595586) **10/12通过、2/12失败**：四个股票/RWA代码命名的合约出现官方1h和官方1m的起始开盘价冲突，含ASMLUSDT、HIMSUSDT、TZAUSDT、ZMUSDT；不能改动原始价格或硬塞到普通币基线。修复 commit `d666c5377dbf7fdb5d75dd13e5a15fe6351f73bb`：保存真实1h、1m原价及每份官方分钟SHA，分类 `CENSORED_PUBLISHER_VERIFIED_1H_VS_1M_PRICE_CONFLICT`，**不记作漏报、非涨、普通负例**。
- 修复后[真实Stage38原始12分片CI #38207816084](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38207816084) **12/12 SUCCESS**。聚合层 [#38207887934](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38207887934) **SUCCESS**，按官方Artifact重新下载全部12份ZIP重算官方ZIP SHA和原JSON SHA、完整源收据、冻结52+120配额和GT因果时间，且将全部证据自动推送回原Monster研究分支 `a4fc39bd1922231aec8e9b33346e9a3c5908013f`。
- 长期[Stage38 SHA审计+指标总表](evidence/monster_stage38_original12_sha_full172_causal_summary.json)，[全部172币日期、逐个原V4 WATCH与SETUP时刻、9天官方分钟发布者SHA、冲突基准证据](evidence/monster_stage38_original12_full172_futures_causal_cases.jsonl)。独立聚合原Artifact `11727978310`，ZIP SHA256 `419203466bffc1f212e9bc6541b2cefe6c062fa33f770e69859b8d43fc084407`。请以此与Git永久原始明细为最终数据；**失败的旧run不得混用**。

## 二、实际妖币发现结果（固定历史2×定价基准）

| 研究类别 | 符号×窗口币日期 | 官方双来源一致、分钟源完整 | 原V4真实3m WATCH提前情况 |
|---|---:|---:|---|
| 源完整1h、已知未来7日2×的USD-M机会 | 52 | 51 | **48严格提前**、1同分钟、1晚、1没有WATCH |
| 同日期固定哈希挑选非2×普通合约 | 120 | 116 | 15个至少有WATCH，共21条WATCH |
| 源冲突/分钟缺档 | 5 | 不纳入评价 | 1个2×标签（TRUMPUSDT）和4个普通RWA符号 |

`48/51 = 94.1176%`，只表示**本次有完整官方1m和1h一致数据的52笔已知合约2×机会中的发现率**，不等于2026年之后的真实表现。48个严格早报：离真2×分钟HIGH前最近的WATCH中位提前 **107分钟**；≥5分钟 46/48，≥15分钟 39/48，≥60分钟 30/48。

额外对照Stage36旧Spot758：事后52个合约2×中，**21个合约符号不在旧Spot名单**；这21个的官方1m/1h均可一致核对，**21/21被原V4严格提前WATCH**。剩余31个同名Spot研究名单：30个分钟可用，27个提前、1个迟、1个无WATCH、1个同分钟；TRUMPUSDT因2025-01-19窗口的官方日1m连续性不满足要求被排除。**21不是21种独立合约专属加密货币**，1000×合约命名、RWA标的/真实合约身份仍未认证。

## 三、漏报/迟报事实而非事后调阈值

| 日期 | USD-M合约 | 首次真实2× 1m HIGH | 原V4 3m WATCH | 判断 |
|---|---|---|---|---|
| 2025-04-19 | CETUSUSDT | 2025-04-25 01:10 UTC | 06:30 UTC | **晚320分钟** |
| 2025-04-19 | PENGUUSDT | 2025-04-25 13:09 UTC | 整个168h没有 | **未发现** |
| 2025-10-19 | FUSDT | 2025-10-21 05:12 UTC | 同分钟05:12 UTC | **没有真正提前** |
| 2025-01-19 | TRUMPUSDT | 月度1h GT为2× | 日1m档案缺连续性 | **未评分，不当成漏报** |

这些与此前Spot Stage31 对CETUS、PENGU的漏报症状一致；此次**真正重放的是不同venue=futures的原始K线和生产函数**，不能把两笔相似结论包装成额外独立验证的收益。FUSDT不在流动性推测层面解释，后续应查其当时的量价门槛、交易状态。原则是不因已经知道未来会翻倍就偷偷改原始信号阈值。

2026-07-19的4个普通对照价格冲突，特征是官方1小时和1分钟**共同有SHA证据但起始open不一致**；解析层拒绝将其当成可评分的「无2×正常币」或神奇行情。其合约代码含非纯加密标的/股票概念，后续真实标的类型必须独立审核。

## 四、普通合约对照说明了什么、不能说明什么

120个在Stage37 1h完整、事后没有达到冻结七日2×的普通对照中，116个在Stage38 1m官方源完成且没有价格冲突；其中15个（12.93%）至少被V4 WATCH，一共21次WATCH。**这只是事后挑选非2×、每日期仅抽20币的对照，不能据此计算正式假阳性率/信号Precision**。此前Stage35 Spot 1,141个有WATCH但无2×的统计也不能直接与该120个对照组简单合并。

WATCH触发 ≠ 真实可买、且未达到固定起点2× ≠ 涨幅可操作价值为零。目前没有历史盘口深度，也没有资金进入或卖出数据。对普通币噪声研究下一步真正需要的是**全部3,333个USD-M官方1h完整币日期逐分钟原生产V4重放**，使收益标签分母和WATCH数完整对齐，而非不断放大只看赢家的选择偏差。

## 五、研发下一步：保持主线，不能因试点成功就上线

Stage38取得了**USD-M分钟源 + 原生产逻辑跨市场可运行的真实证据**，这解除了一项重要技术不确定性。其验收仍是`PILOT_PUBLISHER_SHA_12/12_PASS`，而**USD-M原V4完整普通币WATCH负担、全样本召回和前瞻净收益都仍为 PARTIAL/NOT_DONE**。下一步应把已验证的源码扩展到原Stage37锁定的全900符号×六日期（完整1h的3333需实际1m验证）并保留2067源删失；另外审查RWA股票代码、非Crypto和乘数命名，按官方元信息排除不适用的可交易推荐对象。

直到完成完整事实数据、策略方案、技术方案、真实历史/样本外回测、**真实其他AI独立Review**、最终集成和必要的用户Mac授权前，**Monster = DEPLOYMENT_NO_GO；Frank = UNCHANGED；Gmail = OFF；AUTO_TRADE = NO_GO**。
