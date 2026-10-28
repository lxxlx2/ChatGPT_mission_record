# Frank STATUS（唯一状态来源）

> 本文件是 Frank 模块唯一的“当前决策状态”来源。它不是证据来源：原始数据、实验回执、GitHub artifact、审核评论和 `meme/*.md` 研究报告保留各自权威性，本文件只引用它们。冲突时以原始证据为准。
> 任何 AI 开始任务前必须读本文件，结束后必须更新本文件。行数超限 = 漂移信号。
> 规则见 `docs/frank-operating-model/FRANK_OPERATING_MODEL_V1.md`。

更新时间：2026-10-28 20:00 Asia/Bangkok
更新者：Codex（首版，待 GPT 接管）

## 北极星答案（1 行）

投入：待 P1 到期决定 ｜ 实盘：`TRADE_NO_GO` ｜ 证据状态：`NEED_MORE_DATA`（P1 未启动）—— 依据：六币研究 3 盈 3 亏、盈利集中于 PerPs（[2026-10-10 报告](../../crypto-300-profit-mission/meme/FRANK_MULTIMINT_ACTUAL_ONCHAIN_AND_FOLLOWABILITY_2026-10-10.md)）；G4 严格因果有效价格行 0/30，事后敏感性 15 行（[PR #239](https://github.com/lxxlx2/ChatGPT_mission_record/pull/239) @ `990188c9`）。**不是 edge 不存在的证明。**

## 当前阶段与预算（最多 5 行）

阶段：P0 冻结噪音（待用户批准启动，与 P1 并行）
预算：已用 0 / 上限 2 天、0 外部请求、0 新功能
止损线：2 天后 STATUS.md 未上线或仍有新 Frank Draft PR 产生 → 停止并汇报（PR 清理数量不是止损条件）

## 本周唯一目标（1 行）

STATUS.md 上线、101 个 Frank Draft PR 完成打标（不关闭）、Claude 完成 P1 数据盘点 → 投入决策不变，但 P1 可以启动。

## 正在进行（最多 3 项）

- [B→P1] PR #239 G4 退出因果修复 —— Codex 已独立复核 APPROVE @ `990188c9`（仅研究代码正确性）—— 等用户决定是否作为 P1 数据基础
- [C·冻结] PR #232 F01 Dashboard @ `0b16f0ea` —— 代码与隔离验收已过 —— P1 结论前不推进；生产 8766 替换需单独授权
- [C·冻结] Issue #165 V1 pyc 来源验证 —— 对北极星贡献为零 —— 建议 DROPPED（注意：这是来源考古，不是 S 类安全检查；S 类门禁不受影响）

## 等用户授权（最多 3 项）

1. 是否批准本运营模型 V1（R2）并启动 P0 冻结噪音 + P1 并行？
2. 是否同意 GPT 角色从"开发+管理"改为"仅守目标与预算，不写代码"？
3. 是否同意 Issue #165 及全部 F1–F3 发布管控**文档**工作标记 DROPPED？（S 类安全门禁本身不受影响）

## 本周已关闭（最多 5 行）

- （P0 启动后填写）

## 已知但故意不做（C 类清单）

- Dashboard 503 降级美化、浏览器 OS 沙箱、Chrome for Testing 隔离 —— 均与北极星无关
- V1 143 个 .pyc 可复现性、6 个 pytest 缓存边界 —— 与北极星无关（属来源考古，不是 S 类）
- 多钱包扩展 —— 单钱包北极星未回答前不做

## S 类（永远生效，不在 C 类清单内）

`NO_DEPLOY / NO_RESTART / NO_REAL_RPC / NO_CA_POST / NO_TRADES / NO_MERGE / NO_PRODUCTION_WRITE`；固定 SHA 审核；隔离边界证明。见 `docs/DEVELOPMENT_RULES.md` 第 4 节。
