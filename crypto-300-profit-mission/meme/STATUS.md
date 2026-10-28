# Frank STATUS（唯一当前决策状态入口）
更新时间：2026-10-28 20:47 Asia/Bangkok
更新者：GPT（用户已授权启动 P0/P1；运营模型 PR #241 仍为 Draft）

## 北极星答案（1 行）
投入：`INVEST_GO`（仅本轮已批准的 P0/P1 离线工作，**到期重新裁决**）｜实盘：`TRADE_NO_GO`｜证据：`NEED_MORE_DATA`（仅阶段进行中）——历史 6,874 签名、M3 315 BUY/188 episode（[G0-A #117](https://github.com/lxxlx2/ChatGPT_mission_record/pull/117)）；G4 原预注册 0/30 合格价格、跟单可执行报价 0（[G4 #239](https://github.com/lxxlx2/ChatGPT_mission_record/pull/239) @ `990188c9`）。不能据此证明不存在 edge。

## 当前阶段与预算（最多 5 行）
阶段：P0 冻结噪音与 P1 历史回答**并行启动**；只读已有 GitHub/归档资料，不做生产 Mac 操作。
P0：2026-10-28 20:47 → **2026-10-30 20:47 曼谷**（2 天），0 新外部行情/RPC 请求，0 新功能；本清单只打标，不关闭 PR。
P1：2026-10-28 20:47 → **2026-11-04 20:47 曼谷**（7 天），新 P1 研究 PR 最多 3，**已授权新外部行情/RPC 请求 0 次**。
实测待办：全仓 199 个 Open PR，Frank 标题/分支候选 103 个，继续 10/冻结 85/待清理候选 8；详见 [P0 冻结清单](../../docs/frank-operating-model/FRANK_P0_OPEN_PR_TRIAGE_20261028.md)。
预算到期：**强制 `INVEST_GO / INVEST_NO_GO`**，标注置信度及最大盲点；禁止以 `NEED_MORE_DATA` 或自动申请新预算收尾。阶段启动许可不等于合并/部署/交易许可。

## 本周唯一目标（1 行）
**在 P1 截止前**用 6,874 已核验签名与已有价格/成交证据交付可复核的“继续投入还是停止”决定（含覆盖分母、缺失和最大赢家剔除）；没有可执行证据也必须 `INVEST_GO / INVEST_NO_GO`，不得延长阶段。

## 正在进行（最多 3 项）
- [A] P1 历史证据盘点：以 [PR #117 G0-A](https://github.com/lxxlx2/ChatGPT_mission_record/pull/117) 的 315 BUY / 188 episode 为分母，核对已有价格、成本和可执行报价，**只读且不做新采集**；开发/研究实现按模型由 Claude 承担。
- [B→A] P0 打标清单：103 条 Open Frank 候选在 [P0 清单](../../docs/frank-operating-model/FRANK_P0_OPEN_PR_TRIAGE_20261028.md) 内做一次性分类；只冻结噪音，不关闭任何栈式依赖。
- [A] G4 既有修复证据：[PR #239](https://github.com/lxxlx2/ChatGPT_mission_record/pull/239) 已获固定 SHA 研究审核，原预注册严格有效价格 0/30，另 15/30 事后敏感性不能算真实跟单利润。

## 等用户授权（最多 3 项）
- 当前无新的授权请求：P0/P1 **无外部请求**的启动已批准；未来合并至 main、生产 Mac 访问、Jupiter/RPC、通知、PR 关闭或实盘均须分别明确授权。

## 本周已关闭（最多 5 行）
- 运营模型 [PR #241](https://github.com/lxxlx2/ChatGPT_mission_record/pull/241) 已获用户批准，R2 两处歧义已修订；**仍 Draft 未合并，不能声称 main 已采用**。

## 已知但故意不做（C 类清单）
- F1–F3 新发布流程、无关 UI 打磨、pyc 考古和额外辅助门禁；不将真正的 S 类生产/资金安全检查列为 C。
- 不新增报价采集、定时任务、外部 RPC、Mac/8766 发布、钱包签名、交易或未经审核的 PR 清理。

## S 类（不可豁免）
`NO_DEPLOY / NO_RESTART / NO_REAL_RPC / NO_CA_POST / NO_TRADES / NO_MERGE / NO_PRODUCTION_WRITE` 默认生效；固定 SHA、只读隔离和明确独立授权始终是必要前提。参考 [DEVELOPMENT_RULES](../../docs/DEVELOPMENT_RULES.md) 第 4 节。
