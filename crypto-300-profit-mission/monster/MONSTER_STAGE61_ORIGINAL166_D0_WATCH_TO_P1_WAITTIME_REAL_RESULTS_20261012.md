# Monster Stage61：首次D0到P1的历史等待与后信号价格下跌

2026-10-12 Asia/Bangkok。只属于原Monster Draft PR #30，当前Monster NO_GO；不改变原P1v0.3 75%失败结论，未选择新时间阈值和固定交易金额。

## 真实数据和程序证据

- [预先冻结Stage61全166诊断](MONSTER_STAGE61_D0_TO_P1_DELAY_166_PREDECLARED_DIAGNOSTIC_20261012.md) commit 00b7ffc53d90961ea004d70717dde8977b2f3bbe。
- [研究代码](../local-agent/scripts/monster_v4_stage61_first_d0_to_p1_waittime_all166.py) commit a22c1c8e4c53a327ded9b79197e13350bd5a3fd6。
- [GitHub Actions Stage61 #38258132829](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38258132829) SUCCESS。全部166条锁定原Stage55候选 Git blob dca780246adb28e045ed77f0f96eb4bd034fb2e7；原Stage60连续官方1m来源证据 Git blob c76b9b73c11924cb3fdc36fb852074ff9b49b3b8。
- [全166逐币首次D0重建时钟与真实后P1的24h价格记录](evidence/monster_stage61_original166_firstD0_to_P1_latency_and_24h_proxy.jsonl)，Git blob 89634d4b8d049ad607be1f553515d11ff6e82573。
- [Stage61完整机器汇总](evidence/monster_stage61_original166_D0_to_P1_waittime_summary.json)，Git blob c7f8dbcd4921b81f4d136033cffe0d0269cd0f51。

采用原Stage51真实P1算法的每3分钟持续扫描时钟：first_D0_UTC = P1_eligible_UTC - 3分钟*(polls_until_eligible - 1)。均检查UTC06起点七日扫描内、原46条首次点火与120条后续点火区分、源SHA和原预算状态完全一致。这是对原始算法事件时钟的无未来重建，不是猜测首报时间。历史固定未来2×标签只作事后分组。

## 关键实际结果（只针对全166个曾达到P1条件的币）

| 历史P1子集 | 数量 | 第一次D0 WATCH到P1中位等待 | P1后24h期货close价格代理收益中位数 | P1后24h close正收益数量 |
|---|---:|---:|---:|---:|
| 全166 | 166 | 418.5分钟 | -5.58% | 62 |
| 首次D0即P1合格 | 46 | 0分钟 | -2.33% | 19 |
| 随后3分钟连续观察才触发P1 | 120 | **808.5分钟** | **-6.69%** | 43 |
| 等待超过60分钟 | 108 | 948分钟 | -6.57% | 40 |
| 等待超过360分钟 | 87 | 1170分钟 | **-8.52%** | 30 |
| 等待超过1440分钟 | 30 | 3156分钟 | **-10.17%** | 10 |

另有120条后续点火候选，在P1触发之前，相对首次D0已闭合分钟收盘价累计涨幅的**中位数为+19.71%**。这些数字体现有较高追涨程度，但不同币走势和行情环境可能造成相关性，绝不能断言“等待本身导致亏损”或只据此设置TTL删除妖币。

全部166个候选均已经是“最终符合P1”的已曝光子集，不包括没有达到P1的其他D0 WATCH；因此不能推断所有D0 WATCH的胜率、早期可买净利润或预测精度。

## 下一步工程主线

优先对同一166个币真实重新抓取首次D0以后24h的官方分钟价格与SHA，和Stage60首次P1以后24h进行**严格同方法成对比较**；目的是测定第一次WATCH是否更早出现，以及是否有更好的后续可观察价格空间。须包含两者相同时点的46条即时样本、延迟的120条和普通币对照，不得只挑5×赢家。

然后再设计更可靠的WATCH／升级产品：早期D0保留，二次点火如果已迟到须正确标示，所有入场金额、真实现货/Alpha/DEX可执行性依旧UNKNOWN。设计任何新阈值都必须冻结独立未使用日期全市场回测，不能修改原失败历史结论。

状态：STAGE61_REAL166_SOURCE_LOCKED_PASS；NEW_ALERT_TIME_RULE_NOT_SELECTED；OTHER_AI_REVIEW_NOT_DONE；MONSTER_NO_GO；GMAIL_OFF；AUTOTRADE_NO_GO。
