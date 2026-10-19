# ADR-001 — Monster早期链上研究：免费优先、功效下限、单一治理入口

- 日期：2026-10-19 Asia/Bangkok
- 状态：`PROPOSED_POLICY_BASELINE / USER_SPEND_AUTHORITY_NOT_GRANTED`
- 适用：仅Monster Draft PR #30，不覆盖旧Stage/30例Base现有已冻结具体试验。
- 依赖：[Monster早期研究架构合同](../MONSTER_EARLY_ARCHITECTURE_CONTRACT_V1.md)与[机器schema](../schemas/monster_early_records_v1.schema.json)
- 版本：V1，后续不可原地改ADR决定；必须另建ADR-002显式`supersedes: ADR-001`。

## 决策、理由和不能误认的含义

**D1：研究源总支出默认 $0，不自动开通Plan C。** 免费公共历史BSC RPC且有实测无缺页数据优先；失败再试确实允许完整导出的免费索引。A、B都无法满足范围/来源证明，则`SOURCE_BLOCKED`，只报告若付费需要什么、多少钱与可能改善什么。**这不是用户同意付费的记录**；向用户单独申请且得到明确授权之前绝不付费、不得复用GMGN付费API或偷偷充值。BNB官方公共RPC禁用eth_getLogs；Google官方列表截至2026-10-16未列BSC；Dune有bnb.logs但Free API view-only，这些未证可用之源均不能被记为PASS。

**D2：15个独立的、90天成熟、同一冻结名义金额下经当时双向容量可卖出的10x代币，是进入信号分离力判定的必要非充分条件。** 不到15个记`INSUFFICIENT_POSITIVES`；达到15个仍须保留时段相关、月分块bootstrap可信度、不同月份一致性、倍数标签稀缺性和多重比较，不能仅凭lift>3宣告PASS。任何无法证明买卖、仍未满90天或只有高OHLC插针的币不计入可卖出正例，不作为确认的0输家。该阈值在看到真正的新样本标签计数之前定；原已曝光月份不能算全新OOS。

**D3：ADR取代继续积累Stage决策文档。** 已有的`MONSTER_USER_VALUE_AND_NEXT_VALIDATION_DECISION_20261018.md`保留原文作为历史/索引，不再写大段新路线；新业务门槛、样本、时间分割、研究金额、统计准则更改都进入编号ADR。一个Phase默认最多2次需审批的合同更改；普通实现改动走Git commit + 现有测试；跨真实结果口径或PIT的代码虽自称“修bug”仍需独立审查。每Phase最多一份主JSON和人可读报告，不新增Stage脚本与186个新workflow。用户未批准之前，本ADR是一份推荐治理基线而非自动操作许可。

## 未采纳的替代

- 自动升级到Alchemy/QuickNode/Bitquery收费版：用户过去明确拒绝付费替代，研发成本不可被架构决策偷换。
- 直接接受15个正例或top decile 3x为统计证明：小样本和同月份相关性会导致严重不确定度。
- “实现改动从不需要独立Review”：实质PIT/资金损益/漏失事件问题需要跨代码和证据的门禁，单纯CI不能替代。
- 反复对原decision.md追加Stage N：会再次产生治理膨胀而不带来可买/可卖证据。

## 核验和边界

此ADR只记录拟执行的研究默认值，不包含数据源测试通过、真实回放、外部独立模型审计或Mac本机采集成功。保持`G0 PARTIAL / G4 UNKNOWN / G6 NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。

除用户另行明确同意外，不创建定时任务、不部署服务、不改Frank、不发Gmail、不进行真实交易。
