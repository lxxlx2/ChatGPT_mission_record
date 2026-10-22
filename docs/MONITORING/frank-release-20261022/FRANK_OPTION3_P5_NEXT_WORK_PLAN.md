# Frank 方案 3：2026-10-22 生产 Dashboard 上线后的原计划进度与 P5 工作包

状态：`P0_P1_P2_BASELINE_DONE / P3_DASHBOARD_PROD_PASS / P4_READONLY_ACCEPTED / P5_INFORMATIONAL_NOTICES_NOT_YET_AUTHORIZED`。
基线：用户于 2026-10-20 已选择方案 3；原计划 `docs/MONITORING/frank-release-20261020/FRANK_AMOUNT_INDEPENDENT_INTELLIGENCE_PLAN.md`。
本文件属于 **独立 P5 规划/交接分支，不改变生产程序**。已部署 Dashboard 固定 SHA：`31dd598df248ca15f731913a5cbf82e88b981874`，生产切换验收见 [PR157](https://github.com/lxxlx2/ChatGPT_mission_record/pull/157#issuecomment-6343957300) 与固定 [证据报告](https://github.com/lxxlx2/ChatGPT_mission_record/blob/cb6187a8df2c611693d4030555b194501006b24d/docs/MONITORING/frank-release-20261022/production-cutover/REPORT.md)。

## 一、严格按原定 P0–P5 判断

| 原阶段 | 实际证据 | 结论/保留边界 |
| --- | --- | --- |
| P0 方案 3、V1 保留、无默认金额 | 原计划与原策略签名范围区分；原 V1 新旧通知不改 | DONE |
| P1 真实来源、字段、样例 | `FRANK_OPTION3_P1_HISTORICAL_EVIDENCE_INVENTORY_20261020.md` 中六个历史 lot + 六个 dated balance；随后 Mac 实测已有 V1 源信号及最近索引交易 | DONE（bounded）；不代表新鲜价格/全链收益 |
| P2 金额无关分析 | `intelligence.py` 纯函数与 Dashboard `/api/frank-intelligence` 已上线，缺价格则明确 `PRICE_UNAVAILABLE`；本次生产未接可靠实时报价 | BASE_DONE / PRICE_RISK_NOT_PROVEN |
| P3 页面及模拟信息 | 原 `intelligence_preview.py` 只生成 fake notice；新的 `frank_activity_watch.py` 与正式面板已上线；生产 2026-10-22 记录最近 100 条（38 买、62 卖、48 候选外卖、25 仓位未知） | READONLY_DASHBOARD_PROD_PASS / NEW_NOTICE_NOT_SENT |
| P4 历史回放、CI、固定审核、Mac 实测 | PR146/157、P4 10 条回放/QA 信号先验核对/CI、真实 Mac 页面及产品切换验收均归档 | READONLY_PRODUCT_GATE_CLOSED；不得重复旧样本 |
| P5 用户审核消息及通道、独立策略批准、生产监督切换 | Dashboard-only 生产切换已获授权并完成；**新增风险消息的传输、接收、幂等、审批尚未完成** | NEXT_MAINLINE_WORK |

注意：原计划 P5 曾写过“Loop+Dashboard 监督式切换”；此处 **Dashboard-only 已实际安装**，不能因这一部分完成就认定 P5 的新提醒授权或完整方案完成。PR146、PR157 目前仍是 Draft/unmerged；已安装代码不是合并状态的推断。

## 二、下一阶段唯一主线：有用且真实的 `INTELLIGENCE_UPDATE` 消息，先假发送、再审批

### P5-A. 固定第一批事实与发送前字段契约（NEXT）

**先调查再设计，按 8–12 条真实、有签名且发生时点明确的 Mac 已有索引记录取样，采用一份只读快照，不做新 RPC 或大规模补采。** 实际样本须覆盖 BUY/ADD/REENTRY、SELL、EXIT、SELL_POSITION_UNRESOLVED，候选内与候选外、来源新鲜与过期、原 V1 来源存在与不存在。若某类事件在有界数据里没有，标 `UNAVAILABLE`，不得造真实样本。只保留脱敏公用证据及可在 Mac 只读复核的签名映射，不上载私有数据库。

消息至少包括：事件类别及可验证签名、事件链上时间与**首次可得时间（若可核实）**、发送评估时间、mint/CA、来源/覆盖范围、已核实的风险变化、`UNKNOWN` 字段、不需要买入金额的下一步动作。不要把事件时间当作用户收到提醒的时间；不得宣称覆盖完整链。

三类不同消息语义：

1. `V1_RAW_SIGNAL`：现有 ACCUMULATION/MULTIPLE 原路径、渠道及去重不动；只作“引用来源”，**不重发**。
2. `INTELLIGENCE_BUY_CONTEXT`：若出现真实新的购买事实，只输出新增的、有事实依据的情报信息；若与 V1 原买入消息同内容，**不发送第二条重复通知**。买入信号来源可证实，但 **V1 实际送达**不能凭 `signals` 表猜测。
3. `INTELLIGENCE_SELL_OBSERVED`：有真实签名、已识别方向的新卖出事实时，可单独标“Frank 出现卖出，当前剩余仓位未核实”，即使不在候选集合中；但不得声称“已清仓”“你此前收到买入提醒现需卖出”“收益变化 X%”。要把 SELL/EXIT/仓位不明的语义区分。任何此前推荐/送达关联都必须独立验证，不因同 mint 自动成立。

`DATA_STALE`、`PRICE_UNAVAILABLE`、`LIQUIDITY_UNVERIFIED` 等缺失状态 **优先留在 Dashboard/审计**，不能把缺数据主动转换成“危险/卖出”强提醒；只有事前定义的、可重复的真实变化及用户批准的消息类型才有资格未来进入通知。

**价格追高提醒的条件性缺口：** 当前 Dashboard 没有证明可靠新鲜可比的实时同 mint 市价，`market_observations=None`。没有独立来源与观察时间时，价格涨跌/止损/流动性风险必须保持 `UNAVAILABLE/NOT_VERIFIED`。若未来要接入新行情 API 或扩大 RPC，请另立数据/调用预算和用户许可，不能为了 P5 擅自触发联网调用。

### P5-B. 假提供方端到端测试（在独立草稿分支）

- 在隔离环境实现 **无真实通知** 的消息模板/事实验证/预览，复用已审核 `intelligence_preview.fake_intelligence_updates` 的纯分析能力和原去重约束，不改原 V1 决策、发送、生产队列及策略。
- 对 8–12 条真实来源历史事件做按当时可见事实回放，演练本地/Gmail 两种渠道的**模拟格式**，以及重复、迟到/过期、无来源和同币种但不同 episode 情况。后验事实不得回填历史消息。
- 每条模拟消息打印 `NO_SEND`；只产生本地脱敏草稿，禁止连接 Gmail、本地通知/系统消息、outbox、launchd 或交易。
- 必须先确定源事件唯一键、同 episode 与真实已送达 V1 的不同资格，再定义幂等去重；没有可靠送达事实时一律写明 `PREVIOUS_V1_DELIVERY_UNVERIFIED`。
- 以用户信息价值验收为主：明确何事、依据、时效、风险/未知、一次操作可查看 CA/交易证据；不为了达到某个测试数强行制造风险。
- 独立 AI 固定 SHA 审核，测试及 Mac 隔离假投递 PASS，再邀请用户审批消息样式、触发范围与通道。

### P5-C. 用户审阅消息与授权（必须后置）

- 交付 **真实事实来源、未发送的**本地提醒和 Gmail 示例（新买入变化、独立 SELL 事实、无数据时只 Dashboard），列出触发/过滤、渠道及是否会与原 V1 重复。
- **用户自己选择新增提醒类型和通道**；没有选择不默认开启。旧 V1 local/Gmail 保持原样。
- 如涉及 MC live delivery，还需单独冻结新完整策略字节/hash、实际代码 SHA、签名范围、可信公钥、独立用户签名及生产启动/重启授权；PR142 旧 `unsigned-live-policy-candidate.json` 已 `SUPERSEDED / DO_NOT_SIGN`。
- 原产品只读 Dashboard 当前已经在 8766，**不因准备新通知重装或重启它**。不得使用会同时修改 Loop/Dashboard 的通用安装器绕过审批。
- 旧过期待复核消息不得作为历史补发队列释放；2026-10-22 生产快照 MC 过期未发送待复核为 15、actionable/pending 为 0，只是有时间戳的旧观察。

## 三、验收、停止与所有权

**现在立即做**：P5-A 证据与消息契约，小批次 8–12 条有界真实来源、明确不可知字段、提出两种本地/Gmail **模拟**消息样本；这一环节只读，不涉及上线授权。紧接着 P5-B 独立 fake sender end-to-end。无阻断即进入用户审批，不重复 P4 Mac UI 100 事件和临时版本切换。

**原则**：宁可减少消息类型，也不要做不可信的 SELL→已通知清仓假关联；对用户未指定的买入金额不作要求、不预设金额。不要把用户从只读面板扩展至实盘交易权限。

**状态门禁**：`P5_A_SOURCE_CONTRACT_READY_TO_START / P5_B_FAKE_SENDER_NOT_YET_BUILT / P5_C_OWNER_NOTIFICATION_AUTHORIZATION_REQUIRED / V1_AND_DASHBOARD_PRODUCTION_FROZEN`。
