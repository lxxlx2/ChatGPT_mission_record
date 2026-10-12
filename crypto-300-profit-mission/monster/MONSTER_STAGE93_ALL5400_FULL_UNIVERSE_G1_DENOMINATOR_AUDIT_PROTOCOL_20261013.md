# Monster Stage93：原900×6全市场发现分母复核（事前审计规则）

冻结日期：2026-10-13。唯一Monster Draft PR #30。**不触碰冻结D0/D1、不选择新交易策略、不部署/通知/交易。**

## 原因和精确研究范围

Stage92发现 Stage83/Stage52 的519首次D0观察样本，历史未来2×中的28/29提前，只是**已经触发D0的条件提前率**，不含源有效但永不触发WATCH的2×机会，不能称作全市场召回。仓库已有较早独立取得的 Stage39 全900币×6个日期×7天 USD-M 原始V4回放（`monster_stage39_all5400_usdm_real1m_originalV4_cases.jsonl` Git blob `a2f66aa2331d02d14c0276b446381dc6856cba0e`），要先回到它**完整的5400条attempt**复算召回，而非继续重复优化D1排名。

- 固定六个 Stage39 源日期：2025-01-19、04-19、07-19、10-19、2026-04-19、07-19；每日期900符号，共5400。真实分钟有效源分母及删失必须合计5400，缺完整1h、日1m和官方数据相互冲突都单列，不把缺档当不涨。
- 只对`COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4`计算：七日固定OPEN→首次1m HIGH>=2×的原始标记与首次 `WATCH_UTC[0]`，分别计算`strictly_pre`、`first_watch_lead_ge5min`、`same_minute`、`late`、`NO_WATCH`；即便一个symbol还有第二、第三次WATCH也不能用未来最近一次结果覆盖首次D0。
- 2×中**没有任何WATCH的币日期必须保留**，同时完整保留源有效但没有2×的普通标的。5×/10×同理逐案，不把 Stage39 的`nearest prior WATCH lead>=5m`误当成首次WATCH提前5m。
- 合同核对Stage39原总结 `monster_stage39_36original_SHA_all5400_futures_discovery_summary.json` Git blob `d4dae1d2a2cd4e43bd8f1cb0fcb16b0724240080`：5400尝试、3283完整1m来源、51个历史2×、48个严格提前、51个2×分类与1个同分钟/1个迟到/1个完全未见WATCH闭合；GT5/GT10按来源闭合。任何矛盾fail-closed。
- 输出同时标`EXPOSED_900_FIXED_UNIVERSE`：900个符号来自后来归档人口，不证明当时完整实时交易所Crypto人口；股票、ETF、乘数资产、当时未挂牌状态尚未完全验证。至少2117例删失。**不能**仅用此实现正式 G0/G1 `PASS` 或称 `OOS`。新三前瞻时间窗仍按Stage91。
- 本研究用一次现成Git文件流式复算无公网新请求。保存每个重大遗漏的币、时间与来源状态以供后续验证；旧Stage39/52报告不覆盖不删除。

验收：机器结果记录条件 `source_complete_only` 的2×召回与删失下界，同时 `formal_full_crypto_market_G1=NOT_SCORABLE`、`new_OOS=NOT_DONE`、`D1_G3=REJECTED`、`REAL_NET_PNL=UNKNOWN`、`OTHER_AI_REVIEW=NOT_DONE`、`MONSTER_DEPLOY=NO_GO`、`GMAIL=OFF`、`AUTOTRADE=NO_GO`、`FRANK=UNCHANGED`。
