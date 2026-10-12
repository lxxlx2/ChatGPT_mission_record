# Monster Stage85–87：全部305条D1源时点证据核查与单特征降噪实验止损结论

日期：2026-10-13 Asia/Bangkok。原唯一 [Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)，不改变旧Stage79核心规则，不部署、不启用Monster邮件、Frank不变。

## 一、官方输入事实与实际执行记录

- 已基于[Stage83全部519首次D0真实官方1m连续回放](evidence/monster_stage83_all519_source_and_D1_result.jsonl)固定全部305条有D1研究升级的原始样本。原519人群、305 D1、164 DIRECT + 141 REIGNITION、日期/身份/此前2×时间全部保留，不挑上涨赢家。
- [Stage85 24分片全部305条真实Binance USD-M官方日1m ZIP + 发布方SHA重验CI #38309132844](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38309132844)实际 **26/26 SUCCESS**，305/305无404、无与Stage83原SHA冲突、无与原Stage64首次WATCH61m特征差异，且所有305条在D1当时符合冻结Stage79原双入口条件。原始[全部305条D1真正升级当时特征](evidence/monster_stage85_all305_official_D1_asof_features.jsonl) Git blob `622299fec16400e189cb8fa668ecbc8bc31ec630`，包含每次真实quote15、交易笔数、ret60、量比、当时close与发布者SHA，旧D0不动。另有[全量摘要](evidence/monster_stage85_all305_official_asof_summary.json)。
- [Stage86固定六个特征的实际同日期描述性鉴别力 CI #38309442823](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38309442823) **SUCCESS**；[逐日全部结果](evidence/monster_stage86_full305_asof_D1_date_matched_diagnostic.json) Git blob `ed6424a8773c2e5b48651160e2f33a1813fc7378`。
- [Stage87同期市场相对收益/相对量比协议](MONSTER_STAGE87_CAUSAL_MARKET_RELATIVE_D1_RESEARCH_PROTOCOL_20261013.md)在下载BTC/ETH参考行情前冻结，**BTC/ETH仅是Monster研究价格背景的同期标尺，无新BTC/ETH监控或交易**。六日期发行者SHA分片重放全部305条，并严格在每个D1的t之前读取BTC/ETH已闭合1m。第一次聚合[CI #38309827835](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38309827835)失败，因为旧519混合USD-M人群居然含有一条`ETHUSDT` D1，而代码错误要求305条不能有任何参考资产；该断言已修复，**保留全部305**并显式标注这一条ETH身份重叠。修复版[Stage87 CI #38309963774](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38309963774) **8/8 SUCCESS**，305/305参考数据源完整、无404。成果已实际提交Git：[305条市场相对特征](evidence/monster_stage87_all305_market_relative_D1_features.jsonl)和[同期对照机器结论](evidence/monster_stage87_full305_market_relative_diagnostic.json) Git blob `8869ede406c929a04178b28e5109b7799f215fb6`。

## 二、固定分母与同日期配对对照

Stage83旧开放历史中，519个首次D0中28个原本至少提前5min察觉七日OPEN→HIGH2×；Stage79 D1保留27/28，但产生305候选（平均7.26/日，峰值52/日，G3拒绝）。本次Stage86/87只做已曝光负正例诊断：27个D1在未来第一次2× HIGH前至少5min，277个D1属于不达锚点2×的普通标签，**另一个2×仅在后来/接近第一次HIGH之后D1，不参与正负组配对**。只在4个同时具有两类案例的历史日期做**日期等权AUC**；两个没有历史2×正例的日期仍完整记录，绝不删除个体数据。

| 用已闭合1m当时信息排序的单一特征 | 同日期宏AUC |
|---|---:|
| D1当时60m原始涨幅 | **0.426901** |
| D1当时15m quote交易额 | **0.504047** |
| D1当时15m实际交易笔数 | **0.504488** |
| D1当时15m相对先前45m归一交易额比 | **0.485389** |
| D1当时相对首次D0 close涨幅 | **0.548565** |
| 同时刻D1涨幅减BTC60m涨幅 | **0.415591** |
| 同时刻D1涨幅减ETH60m涨幅 | **0.426354** |
| 同时刻D1涨幅减(BTC+ETH)/2的60m涨幅 | **0.419461** |
| 同时刻D1量加速比减(BTC+ETH)/2的量比 | **0.477868** |

AUC=0.5是该配对排名任务的随机排序水平，<0.5表示「越大越像赢家」这个排序方向效果更差。数据来自**已曝光样本**，一个日期多币交易并非独立同分布；只有27个正例、四个具备同日正负对照日期。因此AUC不意味着真实前瞻能力或置信很高的统计结论，不能为了好看就反过来把弱反向AUC当稳定alpha。这批结果足以拒绝「这些单指标可以轻松解决52条拥挤信号」的无证据假设。

## 三、拥挤来源与模型价值界限

最拥挤的2025-02-03 UTC06 24h出现52条D1，51条重评、1条首次直通；52条历史固定锚点HIGH都未达到2×，但**不能**据此判定52笔如果入场都会亏损。当天D1的60m涨幅中位6.4396%，15m归一量比中位1.5785；305总样本分别11.2856%和3.9541，日状态差异大。Stage86进一步证实在控制日期后，单一量价强度排序仍不稳定。结合Stage87的市场背景修正未改进，当前没有证据支持只靠调高原8%/5%等涨幅阈值、quote/trades限制或减BTC/ETH涨幅即可稳定满足D1召回≥80%同时平均≤5/日且峰值≤12/日的目标。

历史混合USD-M人群包含3条已知TradFi股票类样本、乘数映射不明者，以及至少1条大市值ETH D1参照本身。**真实 Crypto-only、低市值Monster标的的正式分母尚未确认**。Stage87保留ETH原记录并显式标记，禁止未来Monster业务把它当新妖币买入。

## 四、主线研发决定

**本阶段禁止继续用这27个已曝光2×赢家试不同组合阈值或通过硬前5/日消失剩余有价值WATCH。** 原Stage79连贯代码保留为失败对照并记 `G2_PASS_EXPOSED_ONLY / G3_REJECTED_EXPOSED`。此时首先应恢复投资价值导向：
1. 沿真实305个D1时间分别固定明确可实现的观察后结果标签，如下一段真实已收盘价格路径的24h/72h价差、最大不利波动、最差退出、源缺档等；直接衡量**从D1之后**的价格路径，不能再仅按旧锚点从七日前OPEN到未来HIGH打赢家标签。用户未规定单笔金额，历史固定30U/300U不能作为本轮成交金额。没有历史真实盘口与手续费滑点证据，任何交易代理都只能标`PRICE_ONLY_PROXY / EXECUTION_UNKNOWN`。
2. 随后设计一个真正可证伪的双阶段升级：D0全留存，D1_SETUP可检索，再依据**独立确认、真实交易资格和新观察后成本/回撤标签**判定高优先级，验证和收益以新时期或未见样本为准；不再对已见2×赢家逐轮找阈值。
3. 预先冻结的未来起点仍是`2026-10-14`、`2026-10-28`、`2026-11-11` UTC06，当前2026-10-13，未来行情无法提前得到。不得偷换为OOS PASS。实盘口深与真实净收益G4、独立其他AI Review仍未完成，不能部署Mac、发Gmail或交易。

**当前状态**：`D0_HISTORICAL_DISCOVERY=PROMISING`；`D1_G2=PASS_EXPOSED_ONLY`；`D1_G3=REJECTED_EXPOSED`；`STAGE85_305_OFFICIAL_FEATURES=PASS`；`STAGE86_305_SAME_DATE_CAUSAL_DIAGNOSTIC=PASS`；`STAGE87_305_BTCETH_ASOF_REFERENCE=PASS`；`SINGLE_FEATURE_DENOISE_CONFIDENCE=LOW`；`CRYPTO_ONLY_G0=PARTIAL`；`REAL_EXECUTABLE_PNL=UNKNOWN`；`OOS=NOT_DONE`；`OTHER_AI_REVIEW=NOT_DONE`；`DEPLOY=NO_GO`；`GMAIL=OFF`；`AUTO_TRADE=NO_GO`；`FRANK=UNCHANGED`。
