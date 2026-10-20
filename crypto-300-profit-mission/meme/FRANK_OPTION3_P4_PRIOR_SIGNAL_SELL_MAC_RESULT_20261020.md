# Frank 方案 3 · P4 后续卖出与已有买入信号的关联核查（Mac，2026-10-20）

## 精确版本与实际执行

- 已批准的原产品 PR #146 固定 SHA：`72cf75c61fdb220a01b98df0abe81ebc5d248fd4`，仍为 OPEN/Draft，**没有合并或部署**。
- 本次用户**实际执行** QA SHA：`76fd75e90c71141eefb9bc8b071e49e156ea23c5`。
- 真实 Mac 采样时间：`2026-10-20T10:31:56.745763+00:00`。
- 输入：老 Frank 8766 HTTP 只读本地索引 10 条交易；已有 `forward.sqlite` 和 `mission-control.sqlite` 的 `mode=ro` + `PRAGMA query_only=ON`。
- 用户原样提供的结果见本对话（未在 GitHub 公开 CA/签名/路径/地址），本文只存汇总信息。
- 该次运行标准库定向自检真实输出 `FRANK_P4_STDLIB_SELFTEST: 3/3 PASS`，为独立的模拟 SQLite 场景；不是完整回归测试或独立 AI 审核。

## 已经确认的本地事实

| 核对项目 | 用户 Mac 实测 |
| --- | --- |
| 10 条交易的签名+mint+side+time 与 SQLite 源精确一致 | **10/10** |
| BUY/REENTRY | 5 条，均确切模型评估过 |
| 这 5 条本次交易触发的新 ACC/MULT 信号 | **0** |
| SELL 类记录 | 5 条：3 EXIT + 2 SELL_POSITION_UNRESOLVED |
| 有同一轮次、卖出前已产生 V1 ACC/MULT 信号的卖出 | **0/5 已证实** |
| SELL 中已定位轮次但无匹配此前信号 | **3** × `NO_EARLIER_SAME_EPISODE_V1_SIGNAL_PROVEN` |
| SELL 中轮次本身未知，无法建立精确关联 | **2** × `SELL_EPISODE_UNVERIFIED` |
| 本次交易签名对应的原 V1 新信号→控制库决策 | 0/10；这不表示旧信号根本不存在 |
| 真实通知送达与历史时点实时可观察性 | **未验证** |
| 完整链覆盖、当前钱包余额和跟单可执行收益 | **未验证** |

**明确结论：** 用户 Mac 结果证实本地交易采集和 5 条买入的模型评估正常运行，不支持因没有新信号就把它说成“漏监控”。这 5 条卖出样本没有足够证据归属“原买入信号的后续风险事件”，**不能**为了产出提醒而直接使用“同 mint 老信号”或忽略缺失交易轮次。也不能从本样本推断所有历史卖出都没有前置信号。

## 主线影响、停止无效重复

当前 `DashboardState.frank_intelligence()` 仅读取 `self.frank.candidates()` 的当下模型候选；旧交易轮次可能已退出候选。若目标是“此前确实发过原信号→后来卖出”，接下来应当以**历史真实 V1 已生成信号**为锚点、再寻找同轮次后来卖出，而不是不断抽最近五条卖出期望出现信号。

后续优先：
1. 仅从现有 forward.sqlite **只读**做一次有界的 `source-signal-first` 关联调查，以 `person_id=frank`、policy、signal_id、episode、时间为联合依据，再核实同 episode 后续 SELL；不新增链上 RPC 或邮件。
2. 严格区分 `信号已产生`、`已排队/已发送`、`此前通知确实送达`，不能仅因为 signals 表有记录就称“用户之前收到过提醒”。
3. 如果真能找到一条有证据的先信号后卖出回合，再设计风险展示、历史和模拟提醒；找不到则如实 BLOCKED，而不是扩大采样、编造信号。
4. QA 模拟 `SELL_POSITION_UNRESOLVED` 文案必须表达“观察到卖出，剩余仓位未核实”，不声称退出或当前零余额。

**当前范围：** `3/3_STDLIB_TEST_PASS / TEN_LOCAL_SOURCE_CASES_PASS / PRIOR_V1_SIGNAL_SELL_EVIDENCE_0_OF_5_SELECTED / P4_SIGNAL_FIRST_NEXT / P5_NO_GO`。所有正式 Gmail、系统通知、账户交易、合并与生产部署继续禁止。
