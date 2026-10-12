# Monster Stage91–92：前瞻数据准入、D0/D1同核回放及完整519来源历史指标回归

日期：2026-10-13（Asia/Bangkok） | 原 [Monster PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。Monster保持研究未放行，Frank生产运行不变。

## 本轮真实交付与CI

1. [Stage91未来三窗口冻结合同](MONSTER_STAGE91_FORWARD_OOS_CENSUS_AND_REPLAY_FROZEN_CONTRACT_20261013.md)已在2026-10-14首窗前提交，冻结2026-10-14、10-28、11-11 UTC06，各七天，不根据历史赢家改日期。源码 [Stage91只读市场人口/原D0＋Stage79 D1回放准入器](../local-agent/scripts/monster_v4_stage91_forward_oos_replay_gate.py) 已提交。**实际[Stage91 CI #38314008876](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38314008876) SUCCESS**；测试了原production源码Git blob一致、Stage79冻结合同、被修改的历史/未来截面时间、重复市场symbol、伪造原始SHA、合成192h行情改未来HIGH而不改变过去D1时钟。不改变原V4和Stage79。
2. [Stage92评分计算口径冻结合同](MONSTER_STAGE92_G1_G2_G3_FORWARD_SCORING_AND_LISTING_COVERAGE_FREEZE_20261013.md) 和 [Stage92同口径G1/G2/G3全日期评分器](../local-agent/scripts/monster_v4_stage92_forward_oos_scoring.py) 已提交，使用Stage83锁定原始519条真实D0人群的Git blob `c76b3a137c8dbe56feed3a79a63adcc0752f5e2e`作为**仅回归**来源，自动计算提前5m、所有首次D1按完整UTC06日桶21/42日口径、5×/10×及重大漏报。实际[最终Stage92 CI #38314469731](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38314469731) **SUCCESS**；原记录[Stage92完整机器复算结果](evidence/monster_stage92_exposed519_G1_G2_G3_regression_20261013.json) Git blob `9bb0289cb2f011a3050f0a9466cc4658634d592d`，CI已将真实复算文件提交至原分支。
3. 在第一次Stage92测试通过后继续审查了样本分母，发现Stage83的519条属于**已有D0 WATCH的人口**，并未包含完整USD-M市场中无WATCH的全部标的，因此原G1 `28/29`只能是**已经WATCH的子样本条件提前率**，不得宣称“全市场G1召回已过线”。已修正Stage92代码，让完整人口/窗口内新上市和身份未证明时 `G1.research_thresholds_numerically_met = null`，保存独立的`observed_subcohort_thresholds_descriptive_only`。随后真实复测CI成功并回写机器结果，完整审计线索保留。

## 不改变来源和旧策略得出的历史结果

| 已曝光旧519条D0人群 | 实际结果 | 正确解释 |
|---|---:|---|
| 未来七日历史达到固定锚点2×、且已出现在WATCH子人群的 | 29 | 缺少**无WATCH的全市场2×**，所以不是完整市场分母 |
| WATCH在第一次2× HIGH前至少5分钟 | 28/29 = 96.55% | 已WATCH的条件早报率，**正式全市场G1=NOT_SCORABLE** |
| D1对于原D0提前5分钟的2×再次提前至少5分钟 | 27/28 = 96.43% | Stage79 G2 **仅已曝光历史子样本**；唯一漏项 SOONUSDT |
| D1研究升级 | 305 | 真实完整519人群中的唯一D1首次升级 |
| 完整UTC06 42天中的平均D1数量 | 305/42 = **7.26/天** | 超出历史冻结 G3 ≤5/天，REJECTED |
| 42天内单日最多D1 | **52** | 超出历史冻结 G3 ≤12/天，REJECTED |
| 历史5×及10×已出现WATCH与D1至少早5分钟 | 3/3、2/2 | 只限已观察人口中的旧例，非独立前瞻结果 |

当前`Stage92 OOS_verdict=EXPOSED_HISTORICAL_ONLY`；CI PASS证实算数/来源锁/闸门正确，**不表示G1全市场通过或G3策略通过**。不改变 Stage79、Stage83、Stage88 任何先前真实回放或损失指标。

## G0真实后续数据仍有两个缺口

1. 目前没有2026-10-14 UTC06开始前15分钟由真实官方USD-M接口取得且独立留存的完整交易所`exchangeInfo`快照。因此当前无法确定完整的Crypto-only市场当时名单，更不可能使用未来7日未生成的官方1m ZIP、订单簿和成交结果。
2. 即使窗口开始快照真实取得，后续七日还有**新上架、恢复交易、下线及状态变化**，只固定开窗当时名单会遗漏关键新币。Stage92评分器额外强制`full_window_listing_coverage`，若无实际及时归档的官方上市/状态变化资料，则前瞻全市场资格仍BLOCKED，不能因这几个币没有出现在初始列表就说“没有漏报”。

这些是**完成真正前瞻验证所必需的市场人口事实**，与建立新研究指标无关。不能用旧900个随时间变化的BINANCE USD-M档案币列表或2026-10-13之后取得的`exchangeInfo`冒充2026-10-14T06:00前的point-in-time清单。Stage91保存原始字节/sha只是防篡改，并不能在没有原始HTTPS采集来源证明时单独证明数据真来自交易所。

## 模型及工程权限

- D0：沿用原V4核心，研究价值继续保留；未验证新窗口完整市场召回。
- D1：沿用冻结Stage79双入口；G2在已曝光样本具有早报潜力，G3已经在真实回放中失败，未来不允许因为Stage92打分器正确而解除`REJECTED`。
- D2：沿用Stage90真实市场证据核验代码；历史305真实双向盘口、正式身份、用户下单额与双边真实成交缺失，`REAL_EXECUTABLE_NET_PNL=UNKNOWN`，不把瞬间模拟VWAP或历史HIGH当作实赚。
- 后续只允许遵循仓库开发流程：真实前向源采集与可验证人口 → 新模型策略是否可以在未知时期降低负载并保留右尾 → 其他AI独立实审、修复重跑 → 满足放行门槛后另行获得本机隔离部署授权。**本次没有开启任何计划任务/监视程序/本地采集/生产邮件/自动交易。**

最终：`STAGE91_FORWARD_TOOLING_CI=PASS`、`STAGE92_SOURCE519_HISTORICAL_SCORE_CI=PASS`、`G1_FULL_MARKET=NOT_SCORABLE_FROM_WATCH_ONLY`、`G2_EXPOSED=27/28`、`G3_EXPOSED=REJECTED`、`G0_FORWARD_POPULATION=NOT_DONE`、`FORWARD_OOS=NOT_DONE`、`OTHER_AI_REVIEW=NOT_DONE`、`DEPLOYMENT=NO_GO`、`GMAIL=OFF`、`AUTOTRADE=NO_GO`、`FRANK=UNCHANGED`。
