# BSC F0 — 真实 EOA 资格检查前的失败请求分母（离线版）

**状态：PENDING_INDEPENDENT_REVIEW / NO_RUN / NO_LIVE_AUTHORITY**。继承 PR #131 `33f14bbfa0173d067d01a71dec740aaa40a8e50e` 已获独立批准的离线预检。只修复一次真实只读 `eth_getCode` 资格检查前，失败尝试无法留在报告里的 P2，**不**新增真实网络发送器或新的许可。

## 为什么必须修

原 `f0_l1_preflight.py` 用 `envelope()` 读取保存的 RPC 响应，遇到 JSON-RPC `error` 就抛出 `RPC_ERROR`，导致整个审计没有输出。原来的 `NOT_CHECKED` 表示没有保存观察；它不能与「尝试后 RPC 错误」「已尝试但网络超时」混为一谈，否则未覆盖数量和费用上限会失真。

## 新的最小成功/失败证据合同

所有观察首先必须绑定已冻结 PRIMARY 钱包的 **地址**、本轮共同冻结的 **区块高度**、`chain_id=56`、`eth_getCode`、原始请求参数 `[wallet, hex(height)]` 和本地整数请求 ID。非 PRIMARY、重复钱包、超出 20 个观察、错误请求字段 **直接拒绝**。有响应的 JSON-RPC envelope 还要匹配 `jsonrpc=2.0` 与相同 ID；ID 错误拒绝，不准计成指定钱包的正常错误。

三种已保存尝试：
- 合法成功响应：`NO_CODE_AT_SAMPLED_BLOCK` 或 `HAS_RUNTIME_CODE_AT_SAMPLED_BLOCK`。仅说明固定高度返回代码状态，不升级到实际 EOA、BUY、E1/E2/E3 或可用 Router。
- 合法 JSON-RPC `error` 对象（整数 `code`；无非空 `result`）：`RPC_ERROR_AT_SAMPLED_BLOCK`。记录服务商**整数错误码**和响应 envelope SHA256，永不输出原始错误消息，绝不升级为代码状态。非法 / 互相矛盾的 envelope **拒绝**。
- 已保存的发送尝试没有响应：观察显式标记 `attempted=true`、`rpc=null`，其 `transport_error_code` 严格限定为 `NETWORK_TIMEOUT / NETWORK_ERROR / HTTP_ERROR / RESPONSE_TOO_LARGE`，分类 `TRANSPORT_FAILED_AT_SAMPLED_BLOCK`。无原始响应哈希，也不伪造 HTTP 证据或计费事实。

没有观察的冻结钱包仍为 `NOT_CHECKED`。汇总必须始终满足：

`NOT_CHECKED + NO_CODE + HAS_RUNTIME_CODE + RPC_ERROR + TRANSPORT_FAILED = 20`

并独立给出 `saved_getcode_attempts = saved_getcode_success_responses + saved_getcode_rpc_errors + saved_getcode_transport_failures`。**这些数只是对已保存观察的计数**；`actual_rpc_calls=0` 是本离线处理器自己的网络调用，`saved_attempts_provider_billed=UNVERIFIED`。将来真正的发送器必须在发包前持久计数；不能把漏写的一次发送偷偷标成 `NOT_CHECKED`。

Router 文档地址仍只属于来源候选：`router_onchain_code_verified=false`、`live_control_enabled=false`。真实 Router `eth_getCode`、真实 PRIMARY 资格、确定代码部署高度、EOA 资格、实时观察、对照候选与 +60/+300/+900s 报价全部未验证。

## 复核命令和边界

在完整 Git checkout 中执行（没有网络调用）：

```zsh
python3 -m unittest discover -s crypto-300-profit-mission/bsc-forward-follow-model/f0/tests -p 'test_*.py'
```

PR #131 的完整 checkout 复审确认 `178/178 OK, ZERO skipped`。本轮拆分旧的一个复合错误测试为两个，并新增八项定向回归，**期望 187 项，无 skipped**，以审核者真实执行结果为准；不能把期望写为实测。重点包括：RPC error message 不泄露、三类状态分母、无响应超时显式计费、错误 request/response identity 拒绝、非法错误 envelope 拒绝、未知传输错误码拒绝、模拟成功路径不回归。此前获批代码及旧版证据文件原样保留，不能修改 PR #131 的批准 SHA。

## 接下来的业务步骤（仍全部 NO_RUN）

通过独立复审后，才准备**最多 24 次**的独立受控只读资格检查：20 PRIMARY `eth_getCode`，2 Router `eth_getCode`，1 `eth_chainId`，1 `eth_blockNumber`；这是**未授权的提案**，需要固定新执行代码 SHA、错误预算含失败发送、UTC 窗口、并发/速率、唯一 nonce、原始证据和具体许可独立审核，再由用户单独批准。不能复用已经用完的四次 RPC 许可。任何 RPC/WS/交易/签名/通知/部署/合并均不属于此修复授权。
