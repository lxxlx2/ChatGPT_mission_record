# Monster Stage108：305条真实分钟双路径退出回测（已完成，策略拒绝）

2026-10-13 Asia/Bangkok，原 [Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。依开发规范**先Git冻结**[策略/技术合同](MONSTER_STAGE108_DUAL_PATH_EXIT_AND_G3_BASELINE_PREREG_20261013.md)，再 [Python同一核心规则](../local-agent/scripts/monster_v4_stage108_path_exit_replay.py)计算，得到[完整305条逐币机器证据](evidence/monster_stage108_real305_dual_path_exit_comparison.json)，本轮实际两个系统CI均成功：[Stage108 #38411075317](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38411075317)。其中第一次过渡CI #38410943819 曾因新脚本目录索引错误找不到源文件，修复后最终精确源复算通过；不得把第一次失败伪称成功。

## 不可变历史事实

Stage101 305条全部真实 Binance官方发布者SHA日度1m退出数据 `monster_stage101_all305_real1m_historic_exit_paths.jsonl` 固定 Git blob `19dfc89ab10aaf23f068bee924cddc85d5bcc3e1`；原D1入口164 DIRECT、141 REIGNITION；原2×重大提前机会27（只评价，不训练）。所有305个事件和六个七日研究窗口均保留；旧D0/D1信号完全不修改；未来价格只能用于**退出后评价**，策略只用D1时刻已有的入口路径。

| 策略（D1后下一分钟open作为入场价代理） | 全305毛价格中位 | 价格上涨数 | ≥+100%价格个数 | ≤-20%价格个数 | 各边20bps费用情景后中位 | 各边100bps费用情景后中位 |
|---|---:|---:|---:|---:|---:|---:|
| 原统一24h退出 | -2.7992% | 133 | **5** | 22 | -3.1872% | -4.7240% |
| 统一12h敏感性对照 | -2.4338% | 134 | 2 | 13 | -2.8233% | -4.3658% |
| **预注册：DIRECT24h / REIGNITION12h** | **-2.3304%** | **136** | **2** | **20** | **-2.7203%** | **-4.2645%** |

来源：[Stage108全量机器结果](evidence/monster_stage108_real305_dual_path_exit_comparison.json)。每边20/100bps只是**统一研究假设**，没有历史真实bid/ask、成交金额、实际手续费/滑点/冲击，更不是可实现净利润或组合回报；亏损与未来最大HIGH不代表可真实止盈。

- 双路径候选毛中位略改善但仍负，退出的100%价格右尾**2/5 = 40%**，低于预先冻结至少80%（至少4/5）。不能因为价格上涨数量从133升136就采纳。
- 虽未改D1入口所以27个2×提前机会全部保留，但D1关注负载**仍305/42个UTC06日，7.2619/day、峰值52/day**，Stage77 G3 **FAIL**，并非实际高优先级可用提醒。
- 后四个按历史时间靠后的窗口共214条（这些日期仍早已曝光，并非新OOS），统一24h毛中位 **-4.4848%**、双路径 **-3.5549%**，仍然负；对应可核对的全部逐币输出保存到Git而非只报几个幸运赢家。
- **正式判断**：`REJECTED_HISTORICAL_PRICE_OR_RIGHT_TAIL_OR_G3`，机器记录三原因：`PATH_EXIT_GROSS_PRICE_MEDIAN_NOT_POSITIVE`、`PATH_EXIT_LOSES_MORE_THAN_20PCT_OF_BASELINE_100PCT_RIGHT_TAIL`、`UNCHANGED_D1_G3_ALERT_LOAD_FAILS`。不能把Stage108当部署策略。

## 从失败回归到下一步策略

这次在已曝光的305条退出价中，单双路径固定短退出**均无法保留少数重要右尾并稳定转正**，说明不能单靠缩短REIGNITION持仓时间修复D1。下一主线优先**改变哪一批D1事件真正升级到高关注 PRIORITY**，而不是再调6/12/24/72h出场参数。保留原D0发现、全部D1_SETUP、全部519个原D0观察，并对两种D1入口单独训练/验证。新的研究应引入**D1时点之前全市场已出现的拥挤程度**，按时间递进独立训练；不得由未来2×赢家标签制造模型特征，且不能把“每天强裁剪前五条”冒充自然G3。

Stage99本地官方市场名单采集器已由用户授权独立安装，但它**不提供完整D1信号或价格回测数据**，不阻止本地旧历史模型开发。本报告未修改或启动Stage99/Frank，不发Gmail，不交易。

状态：`STAGE108_STRATEGY=REJECTED`、`REPLAY=COMPLETE_ALL305_SOURCE_LOCKED`、`G2_EARLY=27_OF_27_UNCHANGED_BY_EXIT`、`G3=FAIL_AVG7_26_PEAK52`、`REAL_EXECUTION=UNKNOWN`、`OOS=NOT_DONE`、`OTHER_AI_REVIEW_NEW_D1_MODEL=NOT_DONE`、`MONSTER_DEPLOYMENT=NO_GO`。
