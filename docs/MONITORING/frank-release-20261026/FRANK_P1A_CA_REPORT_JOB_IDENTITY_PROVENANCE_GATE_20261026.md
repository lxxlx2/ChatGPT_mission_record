# Frank P1-A — CA 已完成任务与报告关联的真实产品修复（代码候选）

日期：2026-10-26（Asia/Bangkok）

## 真实阻断与代码证据

[Issue #165 Oct23 D0 Mac 只读诊断](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6347259929) 已定位旧前端 `GET /api/cluster-analysis?job_id=...` 遇到一次连接拒绝就永久停止轮询。后来发布的旧 Dashboard 源码 `914e9e47fed2e60bc24690fcb083413a64d4e681` 有有限 GET 重试/缓存恢复，不能把旧前端错误继续当成未修复的原因。[Oct25 C0 一次性生产只读 GET](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6400369303) 已真实 HTTP200 读回同 Mint 的历史 Deep 报告，但**原任务 job_id 不可恢复，历史报告无 job_id，不能证明该缓存与失败的任务同一**。这项不确定性在用户界面中可见。

本次直接修复**实际 CA 产品的任务—报告关联证据**，不是新增 F1x 合成发布器层：

- 以独立审核过的 PR205 C1 总 RPC wire/time budget 产品代码 SHA `4fdf2238a4db2347975689913e49142b760dc091` 为唯一固定比较基线建立独立 Draft PR。原有 C1 budget、RPC fallback/retry、错误 fail-stop 及旧 G1/G2 组件不改动。
- `mission_agent/mission_control/server.py`：在真实 CA worker `WalletClusterAnalyzer.analyze()` **和 `rpc.assert_can_publish()` 成功**之后、报告序列化/写入之前，向当次已创建的 dict 报告加入 `ca_job_id = job_id`。仅向未来的成功报告添加 ID；不会修改旧历史文件，也不会把 RPC 失败转成 DONE。
- `mission_agent/mission_control/static/app.js`：`GET /api/cluster-latest?mint=...` 的报告在显示为已完成任务的结果前，若报告含有明确但**不匹配**的 `ca_job_id`，立即拒绝渲染，保留现有 pending identity 和**仅 GET 重试**入口，不重复 POST。明确匹配的新报告允许显示“任务 ID 相同”，**不宣称资金归一化、报告完整、当前链上状态或可交易**。无 `ca_job_id` 的旧历史缓存仍然可读，但保留“本次任务关联未核实”，不伪造关联。主动选择历史缓存仍以“历史”标注。
- 测试运行真实 `ClusterJobManager._run` 持久化到隔离临时目录（分析器/RPC 使用无网络替身），核对时间戳文件与 `latest.json` 包含真实 job ID。真实 app.js 测试核对同任务匹配、同 Mint 不同任务拒绝及旧格式的未核实状态，原 C1 budget、原 GET-only 恢复/身份竞争回归一并运行。

## 严格边界

这是**产品代码候选，不是实际生产验收**。不存在新 Mac 授权；不能修改本机运行源码、Runner/plist，或补发历史报告中的未知任务编号；旧 `bootstrap` 失败原因依旧 `ROOT_CAUSE_UNRESOLVED`。即使任务 ID 能匹配，也只证明由该 ID 的 worker 保存了这份报告；**不能单独证明 RPC 全覆盖、链上查询新鲜度、用户钱包现在的持仓或报告内容正确性**。现在 `latest.json` 仍然由 Mint 索引，若同 Mint 后续任务覆盖，它只能安全拒绝冒认，不保证原任务的报告可再获取；可单独评估是否需要持久的 ID 索引，但本次不擅自扩大。

**本轮禁止：** 新 CA POST、真实 Solana RPC、额外生产 GET、Dashboard 部署/重启、Loop/V1/D2 变动、监控通知、邮件、交易、合并 Draft PR。若要真实验收该修复，须先另行批准可靠的 Dashboard-only 发布器和一次性 Mac 操作，再另行批准有界真实 CA Query。

**门禁：`CA_JOB_REPORT_CODE_CANDIDATE / BASE_C1_APPROVED_OFFLINE / INDEPENDENT_REVIEW_PENDING / C2A_ROLLED_BACK / C2B_NOT_AUTHORIZED`**。
