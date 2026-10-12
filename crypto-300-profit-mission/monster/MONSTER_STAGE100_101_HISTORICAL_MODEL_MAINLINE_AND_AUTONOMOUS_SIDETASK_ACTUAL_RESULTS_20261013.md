# Monster Stage100–101：以旧数据建模为主线，新市场名单作为独立后台采集

日期 2026-10-13 Asia/Bangkok；原 Monster [Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。用户再次明确：**先针对已有历史数据做一套真正可回测的模型，有问题继续改；未来新数据只为额外检验，不能阻挡主线**。Stage99错误的“本地Claude CLI review-install”已撤回。本轮未要求用户在Mac运行任何命令，未触碰Frank、发邮件或下单。

## A. 本轮真实历史建模：Stage100，第一个完整日期前推的D1优先级模型

- [先冻结的策略和技术口径](MONSTER_STAGE100_HISTORICAL_D1_PRIORITY_MODEL_WALK_FORWARD_PROTOCOL_20261013.md) → [按时间训练的D1优先级模型代码](../local-agent/scripts/monster_v4_stage100_historical_d1_priority_walkforward.py) → [Stage100真实GitHub CI #38323388816](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38323388816) **SUCCESS** → [完整原始305/历史前推逐币机器结果](evidence/monster_stage100_real305_D1_chronological_walkforward_priority_results.json)，Git blob `6eb2bf3367f0bdf103a076b7e6b99abb68234fd0`。
- 特征仅使用实际D1时刻当时已完成的 1m quote/trades/ret60/相对D0发展与DIRECT/REIGNITION，标签固定D1后24h实际分钟K线open-to-close价格是否上涨。训练只有更早的旧日期，每折训练期自身分数确定阈值，不允许测试期硬cap或事后挑赢家。四个不同更晚的历史日期用于诊断，**属于已曝光日期上的严格历史时间前推，不是新OOS**。
- 305原始D1完整保留（早期91样本训练，后214测试）；候选在214条测试中保留148条，原24h固定退出毛中位`-4.4848%`→候选`-4.3507%`，原72h`-5.3347%`→候选`-5.8754%`；历史提前5min重大2×`27`个中只保留`20`，**74.07%未过原≥80%门槛**；原4测试窗候选日均`5.2857`、峰值16仍不满足`≤5/天`、`≤12/天`。右尾72h≥100%的5例只留4例，重大漏报包括`A2Z, MAGIC, MEMEFI, VELVET, BROCCOLIF3B, 1000RATS, GIGGLE`，以及一个72h大涨`HFT`。**候选REJECTED，不应部署或进一步靠测试日期调这个版本的阈值。**

## B. 本轮直接检验交易退出：Stage101，全部305官方一分钟的真实历史退出路径

- [先冻结的退出经济与逐分钟因果协议](MONSTER_STAGE101_HISTORICAL_D1_EXIT_PATH_RESEARCH_PROTOCOL_20261013.md) → [官方单分钟真实退出程序](../local-agent/scripts/monster_v4_stage101_exit_minute_backtest.py) → [305样本全量汇总代码](../local-agent/scripts/monster_v4_stage101_aggregate_exit_paths.py) → [Stage101真实GitHub CI #38323758365](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38323758365) **26/26 SUCCESS** → [每币OHLC路径退出证据](evidence/monster_stage101_all305_real1m_historic_exit_paths.jsonl)和[真实全量比较表](evidence/monster_stage101_real305_exit_time_stop_comparison.json)，汇总Git blob `a7bd2b37fa9f8cd3e5f53d65c30303ec170b5317`。每个新请求都重新核对与Stage88完全相同Binance官方每日1m发布者ZIP SHA，305/305源一致、无缺人、无新D0/D1逻辑变更。
- 首次CI #38323712860仅因一处Decimal的`"0"`与`"0.00"`字符串对比导致合成用例失败，**不是经济结果或官方1m来源问题**；修复为精确Decimal数值比对后重新跑真官方源，26/26成功。保留失败CI审计记录。

| 305条全部原始D1信号（价格代理） | 固定6h | 固定12h | 原固定24h | 原固定72h | -15%硬止损、先涨25%后20%追踪、最长72h |
|---|---:|---:|---:|---:|---:|
| 单币毛价格中位 | -2.25% | -2.43% | -2.80% | -6.35% | **-9.57%** |
| 固定退出价格上涨条数 | 119 | 134 | 133 | 103 | 112 |
| 跌幅至少20%的价格代理 | 10 | 13 | 22 | 57 | 0 |
| 价格代理上涨至少100% | 1 | 2 | 5 | 5 | **1** |

保护型算法虽然把价格代理单笔≤-20%的数量压到0，但**牺牲了4/5个极端右尾案例**，并使中位毛价差恶化到-9.57%；用`MAX_HIGH`构造完美止盈会更严重地高估可交易利润，已禁止。止损触发以当前真实MINUTE LOW和此前完成分钟HIGH推算，但不是实盘真实Bid/Ask/费率/滑点/成交证据；存在两个退出价格所在分钟无实际成交记录，必须单列，不能声称真实最大损失确定受到保护。

分D1旧入口后观察到很重要的**仍已曝光**差异：
- DIRECT 164条，固定12h毛中位`-4.36%`、固定24h`-4.69%`，简单缩短时间没有修复。
- REIGNITION 141条，固定12h毛中位`+2.19%`，固定24h`+0.62%`，但长期72h`-6.15%`；这提示**两种入口应当视为不同持仓状态研究，而不应以一个新阈值过滤所有D1**。这只是历史描述，不能根据它直接上线12h交易策略。

## C. 用户指定的后台新数据采集（与历史主线独立）

现已在ChatGPT侧实际创建每隔14天、总共三次的**定时后台任务**：曼谷时间2026-10-14、10-28、11-11，每次12:48。该任务的目标是在有效点时窗口中通过已连接GitHub工具在**同一Monster PR分支**提交`monster_stage97_one_shot_capture_request.json`并附`[MONSTER_USDM_CAPTURE]`触发已有Stage97 GitHub Actions，让CI在UTC05:45–06:00内采Binance USD-M `/fapi/v1/time → /fapi/v1/exchangeInfo → /fapi/v1/time`原始HTTPS字节和 SHA，写回同一PR `monster_stage97_point_in_time_usdm_YYYY-MM-DD_raw_https.json`。三次到期任务自动停止；不用Mac、Claude本地CLI、Cron、其他持久后台Daemon。不启动Monster D0/D1生产监控、Frank或真实交易。
`SCHEDULED`只证明任务已排期，并**不能保证**GitHub排队按时、权限可写、Binance可达、SHA验证成功、文件确已push。应在每个日期用实际PR远端文件及CI证据判定`CAPTURE_SUCCESS`或`MISSED`，严禁事后补抓伪造时间。起始快照只能部分证明当时的市场名单，不能代替整个7日内上市/退市变化，亦不代表7日价格资料或完整Crypto-only验证。

## D. 研发决策与顺序

1. 维持原V4 D0 WATCH完整覆盖与Stage79 D1实际信号不变；Stage100排序研究模型 **REJECTED**。
2. Stage101完整实分钟价格研究揭示简单提前卖出或机械止损都可能牺牲少数极端右尾；下一版需要重点分析 DIRECT 与 REIGNITION 的不同经济角色，在**历史日期按时间训练/跨日期测试**中研究可复现的入场确认/持仓计划，同时完整保留普通币与巨大盈利例，而非根据已曝光单币赢家调整某个止损百分比。
3. 任何新D1候选需重新定义预注册策略、技术口径、真实回测、其他AI（用户采用Claude**对话**）真实审查和修复才允许讨论Monster本地部署；历史样本开发不需等待未来日期。
4. 即使某一历史退出价格毛中位转正，真实bid/ask、成交深度、显式名义订单额、费用和新Crypto身份仍缺；`REAL_NET_PNL=UNKNOWN`。不得把研究WATCH升级BUY，更不得自动下单。

当前状态：`HISTORICAL_D0=KEEP`、`STAGE100_PRIORITY=REJECTED_REAL_4FOLD`、`STAGE101_EARLY_EXIT_AND_STOP=ACTUAL_ALL305_DATA_REPLAY_COMPLETE_NOT_ADOPTED`、`STAGE97_BACKGROUND=TRIGGER_SCHEDULED_PENDING_FIRST_EXECUTION`、`D1_G3=REJECTED`、`G0_CRYPTO_ONLY=PARTIAL`、`OTHER_AI_REVIEW=NOT_DONE`、`MONSTER_DEPLOYMENT=NO_GO`、`GMAIL=OFF`、`AUTOTRADE=NO_GO`、`FRANK_UNCHANGED`。
