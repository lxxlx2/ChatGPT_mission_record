# BSC Meme 地址分析模型 V1 — 开发与其他 AI 复核交付规则

**版本**：2026-10-15 / **性质**：BSC 模块必须遵守的开发交付规则。仅补充流程要求，**不更改**已冻结的投资目标、23 钱包、19 个 exact CA、成功门槛、分级证据或历史测试样本。

## 规则优先级与主线

1. 遵从 `crypto-300-profit-mission/MISSION_SPEC.md`、`docs/REPOSITORY_STRUCTURE.md`、`crypto-300-profit-mission/research/bsc-meme-address-model-v1-requirements-2026-10-13.md`（G0 冻结目标），及 `bsc-meme-address-model-v1-implementation-plan-2026-10-13.md`（P0–P7 计划）。本文件只规定 BSC 开发/审核交接。
2. 主线是 **跨钱包、跨 2026 重大 Meme，确认真实重复盈利与亏损，识别观察者能首次得知的可执行机会 U，完成真实历史可成交的 1/5/15 分钟跟单对照**。ERC20 转账、历史 spot 报价、钱包原始交易盈亏、P2 的采样正向余额、PR CI 成功均不等于跟单策略盈利。
3. 以完成完整用户价值功能为目标：先横向批量（多钱包、多 CA、正负控制），避免单钱包单异常与无限补边界；优先重用源 SHA 冻结证据，必要时只读补查。无实际收益增加的边界工作需明确停止条件。
4. 流程固定为 **数据与现状核对 → 技术设计及批次预冻结 → 研究分支开发 → 其他 AI 独立 Review（到触发门禁时） → 单元、回归、链上证据核对 → 授权后的 Mac 只读实测 → 缺陷修复及复验 → 下一批主线**。针对低风险中间研究批次可以先做源证据和 CI，但不能将本方 CI 冒充其他 AI Review。
5. 保留同一个 Mission BSC 研究 Draft PR，数据不可篡改，写来源 Git blob SHA 与固定代码 SHA。不得私自合并、改变资金、发邮件、发送交易信号、部署或触碰 Frank/Monster，保持 `NO_GO / NO_MERGE / NO_DEPLOY`。

## 必须执行：其他 AI Review 时直接交付提示词

**触发场景**：阶段评审门禁（P4-C 经济模型升级、P4-B 机会 U 判定或 P5 算法）到达；跨样本/经济口径/核心算法的变更；从研究部分通过改为 `GO`；准备 PR 合并、用户 Mac 验收、实际部署；或发现决定性数据解释争议需要独立专家核验。独立 Review 尚未完成时必须显式说 `PENDING_OTHER_AI_REVIEW`，不可提前宣称通过。

当应由另一 AI 审核时，**不得只说「需要其他 AI review」或让用户找旧消息**。在**同一条对用户的回复**中直接提供一段**完整、可复制、无需补填信息**的其他 AI 审核提示词，要求：

- Mission 仓库**完整 GitHub 地址**、原 Draft PR **#40** 完整 URL、待审**固定 40 位 commit SHA**及比较基线（如有）；
- 本轮实际代码、原始来源、源 SHA、阶段计划/冻结要求、对应研究报告与 CI 链接；使用**准确存在的文件名、URL**，不生成尚不存在的链接；
- 用审计语气要求审核者**亲自读 Git 源和原始链上/固定证据，不能信本模型自述**；复算统计/资金和事件时间因果、真签名、退出、费用、Gas、quote token、分页、抽样偏差、样本泄漏及 `NO_GO` 安全边界；
- 说明**只读**，不得擅自合并 PR、修改生产、发真实交易/钱包签名、重启 Mac 服务或发送通知；
- 明确输出 `APPROVE` / `REQUEST_CHANGES` / `BLOCKED_INSUFFICIENT_EVIDENCE`，逐项问题、严重性、精确文件行号、可复现证据、修复意见；审核对象固定 SHA，后续修改需重新审新 SHA；
- 单独列出 **审查通过 ≠ 可合并/可部署/可跟单**。不能仅通过测试、正收益样本就移除 `NO_GO`。

**审核提示词模板**（每次调用必须用当次真实固定 SHA、真实 PR/证据/CI 文件链接替换字段，不得把未替换的模板直接交给用户）：

> 请作为独立 AI 技术审计员，对 GitHub `https://github.com/lxxlx2/ChatGPT_mission_record` 的 Draft PR `https://github.com/lxxlx2/ChatGPT_mission_record/pull/40` 中我指定的**固定 commit SHA**进行只读复核，禁止只审最新可变 HEAD。先读取 `crypto-300-profit-mission/research/bsc-meme-address-model-v1-requirements-2026-10-13.md`、`bsc-meme-address-model-v1-development-rules-2026-10-15.md`、`bsc-meme-address-model-v1-implementation-plan-2026-10-13.md`，再读取本轮代码、全部被引用原始来源的固定 Git blob SHA、报告和 CI。重点独立重算真实签名人、原始完整成功回执、转账库存闭合、BNB/WBNB/非原生报价、税费与 Gas、唯一钱包区块、正反例覆盖、23×19 分母及 1/5/15 分钟观察者可执行 U。特别核验研究者原始钱包盈利**没有**被冒充跟单利润，原始截断/空响应没有被冒充没有成交。逐条输出发现的问题（severity、路径/行号、原链上交易或来源证据、复现、解决建议），最后给出 `APPROVE`、`REQUEST_CHANGES` 或 `BLOCKED_INSUFFICIENT_EVIDENCE`。审查过程只读，**不得**合并、部署、改变资金、发警报或交易。不得把审核通过当作生产授权。

**交付约束**：每当实际门禁需要其他 AI 复核，在用户可见回复中先明确「需要其他 AI 独立复核」，紧接完整**当轮真实 SHA**提示词（可作为整体复制的 Markdown 引用块/代码块）。同步把固定 SHA、审核请求、审核结果/缺陷和修复再审 SHA 留在 Mission Git；如果尚未能得到其他 AI 的实际回复，状态永远是 `PENDING_OTHER_AI_REVIEW`，不得代替其他 AI 给自己批准。

## 数据、测试和结束判据

- 经济结论分为 `CONFIRMED`、`INFERRED`、`UNRESOLVED`、`SPECULATIVE`；`SIGNED_NATIVE_BLOCK_SCOPE` 不能因为正值就升级成已审计盈利；完整经济闭合必须有本人签名、真实成交、库存、实际报价资产和 gas/税费结算；无实际回款不得认定已卖。
- 一次冻结 **3–5 个跨钱包正负对照样本**，记录入选理由、钱包、exact CA、交易哈希/区块、现存来源 Git SHA、预计分母；批量查询、批量验收，严禁看到结果后挑盈利样本；失败/不可读必须计入分母。
- CI 必须包含来源确定性复算、已冻结验证、缺页/截断、签名不符、报价口径篡改、重复钱包区块、正向误升级、生产 `NO_GO`、样本未改变。报告写明确的 `DONE / PARTIAL / BLOCKED` 和可量化比例。
- 接口免费层不支持 trace/内部回款时标 `UNRESOLVED` 并寻可证实等价免费证据，不能付费、绕过权限或无限重试。单一来源负结果必须明确窗口、分页和范围。
- 先完成已经冻结的 ADFF 龙虾、2ADF 牛来、A83B 牛来经济候选退出核查；如果仍不可闭合，将 blocker 和复现证据固定并转向另一批**已存在 P2 正负对照**，而不是反复耗在同一异常。
- G6 以前所有 `NO_GO / NO_MERGE / NO_DEPLOY` 不变；独立其他 AI Review 和 Mac 只读部署还需各自单独的明确准许与证据。

## 当前状态（2026-10-15）

研究 Draft PR #40；原 23×19=437 单元，7 个近期活跃钱包；P4-C 已确认 8E6B 两个不同 CA 的 BNB/WBNB 净正向回合，以及 DDAC 龙虾净负向回合；剩余 434 钱包×CA 未按同口径完全审计，跟单 U / P5 仍不具备放行证据。**尚无独立其他 AI 复核结论**。本开发规则的 Git 提交不代表审核已执行。
