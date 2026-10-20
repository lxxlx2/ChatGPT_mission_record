# F0 — 自适应 HEAD 调度与预发送账本集成：完全假响应回放

**状态：OFFLINE_ONLY / NEW STACK UNREVIEWED / NO_LIVE_RPC / NO_MERGE。**

基线：PR #153 SHA `501d729993d390f9001c6c0c02f6d9a184bd1115` 经当前会话**直接审核**为 APPROVE（离线），并且完整 273/273 PASS ZERO SKIP。**不是隔离 Codex 独立审核**，记录见 PR #153 评论。PR #152 SHA `f3ae8041b0077b6f12d181b52f1ff6e3fded9fb9` 有隔离独立离线 APPROVE，263/263 PASS。所有 4/24/62 真实调用授权已经耗尽，不能重用。

## 交付的最小实际功能

- `f0_l1_adaptive_head_plan.py` 中**仅针对 head 不前进**添加指数退避：连续 N 次不变，下一次轮询等待 `min(base_interval × 2^N, explicit_cap)`。退避是时间等待，不会增加“免费”的调用额度；每次尝试仍占用 head 预算。head 增长时重置计数。
- `f0_l1_adaptive_journal_replay.py` 是**离线集成执行器**，不接受回调/端点参数，只能消费传入的预声明假响应 `frames`。它实际复用曾经审核过的 `f0_l1_live_short.Journal` 的发送前原子持久写入、独立的 `journal.json`、`raw_responses/` 和 `report.json`，请求体复用 `f0_l1_http_wire` 的白名单/ID/全块校验。**虽然 Journal 来自含真实 HTTPS 函数的既有模块，但此处只传入封闭的内存假发送函数，绝不调用 live_https_post**。
- 前两次尝试是 `eth_chainId=56` 与初始 `eth_blockNumber`；以后每次 `READ_HEAD` 都是新的 `eth_blockNumber`，`READ_BLOCK` 是 `eth_getBlockByNumber([hex(height),true])`，四类调用**合并计入一个实际已记录假调用总上限**。计划不超过最近一次脚本响应验证的 head 高度；读取失败只记录那个确切高度而不重试。
- 使用冻结的 PR116 manifest、两份文档 Router registry 原始字节绑定及现有 `block_candidates` 进行离线分类。非 PRIMARY 的 Router `to` 地址命中不是 swap 成功或独立有效对照；不升级 `control_eligible` / E2/E3 / 报价。
- 额外保留**合成 HEAD 快照**和 `sampled_head_minus_processed_height`，但这些来自假响应，不能称为真实链头滞后。报告包含 `actual_rpc_calls=0`、`source_provenance=IN_MEMORY_SCRIPTED_RPC_ONLY_NOT_CHAIN`；假发送器没有网络出口，脚本不能申请或消费真实许可。
- 按预算/缺失结果/停滞退避/HEAD 回退/失败/超时模拟上限停止，并且所有请求在内存响应被消费前都先落到独立账本。若模拟失败，报告不会用未调用高度补零、不会用脚本剩余响应伪造真实样本。

## 单一总预算和实际业务方向

真实实验中的总调用数必须计算 `1 chainId + 1 initial HEAD + N subsequent HEAD + M full-block attempts`，每一个 HEAD refresh 都是收费的 **请求次数**，不是免费的“观察”。例如假试验 `N=3、M=1` 恰好尝试 **6** 次。当前代码只执行**假传输**并持久记账，不创建生产许可、更不请求扩大真实 RPC 范围。

用户 Mac 上历史样本报告的 26 秒 header 时间跨度、58.979 秒本机接收跨度、约 766ms 单区块处理时长已经说明固定每个高度约 1 秒会在这组数据中落后。新的 head 自适应避免请求不存在的未来高度，也能有界退避，却**无法仅凭单路串行轮询就保证追上约 441ms 的出块间隔**。后续可行性仍取决于实测完整块读取速度与免费的节点响应能力，不能把本离线结果说成已具备实时跟单。

## 审核与测试

本分支新增 10 项 fake-only 端到端测试，覆盖：chain/head+后续 HEAD+区块总账；3 次 head 原地不变后按 1s、2s 退避再读块；总预算截断；错误链和失败 head 禁止额外调用；空结果保留缺块高度；回退停止；字节改动拒绝；虚拟时窗内 head 不变提前停止；现有 output root 不能再跑。测试将 mock patch `f0_l1_live_short.live_https_post` 为直接报错，避免伪装“真实 HTTP 成功”。

上一个基线完整测试 273/273 PASS；本分支**预计 283**（+10），在新固定 SHA 全量 CI 真正运行并独立审核前，不得称为 283/283 PASS。

下一步按既定主线：独立审核通过后确定第一次**新的** HEAD 刷新真实短窗口所需的预算/固定 SHA/证据目录和供应商免费配额，重新向用户申请具体范围授权，再单独审核私有 permit。原 PR149 的真实执行和 PR151 的离线结果不能被替换或重新赋权。

**本 PR 严禁：** 实际 BSC RPC、WS、付费 API、交易、签名、后台运行、邮件、合并或部署。
