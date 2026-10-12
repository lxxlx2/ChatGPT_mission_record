# Monster Stage94：305条D1当时特征 vs 24/72h真实分钟价格代理的因果对照（预注册）

冻结日期：2026-10-13，原Monster PR #30。**禁止按这份已经曝光的回报优化阈值、训练前瞻模型、部署或假称可成交净利润。**

## 数据与样本固定

只取[Stage85官方SHA验证的完整305条D1真实as-of量价特征](evidence/monster_stage85_all305_official_D1_asof_features.jsonl)（Git blob `622299fec16400e189cb8fa668ecbc8bc31ec630`）和[Stage88官方SHA验证的305条D1+1分钟入场价格、固定24/72h退出价](evidence/monster_stage88_all305_D1_post_signal_24h72h_price_paths.jsonl)（Git blob `86e96b726f677a15f5a7c8d740e3caca5c83e3fc`）。按 `date + symbol + D0 first UTC + D1 first UTC + D1 path` 五键严格连接；任何1条不匹配或两种时长K线不完整必须源缺档报告，不能从分析名单排除造成美化。

全305包括164 DIRECT、141 REIGNITION、没有锚点2×的普通币、乘数映射不明、已确认的非Crypto及混合USD-M交易对。正式产品Crypto-only人口未验证，不能把结果转为可执行胜率。

## 事先锁定的评估，不做优化

未来**价格标签仅作事后诊断**，不是当时可观察输入，且不是包含费用的收益：

- `24h_fixed_exit_gross_up`、`72h_fixed_exit_gross_up`：从信号后延迟一分钟的K线open入场代理到固定退出K线close，分别涨幅 `>0%`。这不是盈利交易率。
- `24h_fixed_exit_gross_ge50pct`、`72h_fixed_exit_gross_ge50pct`：单币固定退出毛价差 `>=+50%` 的右尾，样本少时明确不足。
- `24h_fixed_exit_gross_ge100pct`、`72h_fixed_exit_gross_ge100pct`：`>=+100%` 的极端右尾，同样不等于实际可买可卖。
- `24h_exit_loss_at_least20pct`：固定退出价低于延迟入口 `<=-20%` 作为风险标签，单独列出。
- 附加后验MAE和最大close-to-close回撤仅描述风险，不拿未来最低点设计止损或兜售策略。

先冻结**所有六个**信号时已真实可见单变量（原样，不挑赢家）：
`asof_D1_ret60_pct`、`asof_D1_quote15_USDT`、`asof_D1_trade15`、`asof_D1_normalized_quote15_prev45`、`asof_D1_ret_from_first_D0_pct`、`from_first_d0_delay_minutes`。

每个标签用正负组进行同日期点对点 **AUC**（大特征排前定义的方向事先固定），如果日期没有同时正例/负例，该日期在宏AUC中记`null`并列出总数，不能设AUC=0.5充数。报告每日期（含全部无正例日期）、可评价日期等权宏AUC、全样本跨日期全局AUC、所有点对样本数，未有同日期正负对照就`INSUFFICIENT`；不同日期相关/同币跨日非独立、只允许说`DESCRIPTIVE_EXPOSED`，不能把0.6之类经验数字称为盈利alpha。

主线验收仍需`G2_MAJOR_UPSIDE>=80%`、`G3_D1_LOAD mean<=5/day peak<=12`、真正新OOS、完整市场Crypto身份与真实交易额净收益；本Stage94禁止根据已知赢家设筛选阈值回测后宣称通过。旧Stage79维持G3`REJECTED`。

终态：`PRICE_ONLY_PROXY`、`OOS_NOT_DONE`、`REAL_EXEC_NET_PNL_UNKNOWN`、`NO_NEW_THRESHOLDS`、`OTHER_AI_REVIEW_NOT_DONE`、`DEPLOY_NO_GO`、`GMAIL_OFF`、`AUTOTRADE_NO_GO`、`FRANK_UNCHANGED`。
