# BSC F0 — 24 次只读钱包 / Router 资格检查器（代码待复审，尚未获实时授权）

**状态：`OFFLINE_IMPLEMENTED / REVIEW_PENDING / NO_RUN`。** 父基线 PR #133 固定 SHA `296aa3f2b8dfb80726f06b3663dede3e2e7c0d5c`，独立审核 `186/186` 无 skip。此次新增真实 HTTP 发送路径的**代码准备**并不授予任何新的 RPC 权限。前次 4 次 BSC HTTP smoke 权限已经耗尽。

## 本轮交付了什么

`f0_l1_code_probe.py` 复用已审核的 `f0_bounded_smoke.https_sender`、Git SHA / 源脚本自检和一次性 nonce，并严格把执行许可分成另一种不可与四次 smoke 混用的 scope。对真实 PR #116 原始 manifest 必须通过固定 Git blob `fcd0029314353313867e565190cd4f2882089f11`；20 个 PRIMARY 来自这份 manifest，2 个 Router 仅来自 `F0_ROUTER_SOURCE_CANDIDATES.json` 的官方文档登记（链上仍未证明）。无额外地址替换、无自动 BACKUP、无收益字段。

每次运行最多按固定顺序请求：

1. `eth_chainId` 一次，必须为 56；错误则立即停机。
2. `eth_blockNumber` 一次，在本次运行中冻结唯一高度；错误则立即停机。
3. 20 个 PRIMARY `eth_getCode`，全部使用该高度、固定顺序；RPC 错误和网络失败都记录，每一钱包最多一试。
4. 2 个候选 Router `eth_getCode`，仍只是代码在所采样高度的状态，**不是 Router 方法或 swap 因果批准**。

总量上限 **24**，分组上限 **20+2**，单响应最多 **2 MB**，默认串行、无重试、无 WS、无交易/签名/通知、无后台服务或付费。真实模式的 `min_interval_ms` 许可约束 **100–1000 ms**，最长 **10 分钟 UTC** 时间窗；每次请求发出前重新核对窗口（超时则不再发送）。连续三次来源失败提前停止，其余未查钱包保留 `NOT_CHECKED`。由于公共节点和代码高度关联，成功也只代表 `CODE_AT_SAMPLED_BLOCK`，不等于 EOA/控私钥/真实买卖/可跟单。

### 强制失败记账

`AttemptJournal.begin()` **在调用 HTTP sender 前** 将序号、方法、类别、固定区块、钱包、`requested_utc`、`requested_monotonic_ns` 和 `ATTEMPTED_OUTCOME_UNKNOWN` fsync + 原子写入 `journal.json`。无异常返回后才改写为 RPC_RESPONSE / TRANSPORT_FAILED / INVALID_RESPONSE。因突然断电造成的 `ATTEMPTED_OUTCOME_UNKNOWN` **必须计作可能发送、可能计费**，严禁自动重试。正式报告同时保留 saved getCode 的成功、RPC 错误、传输失败、NOT_CHECKED 五种分母；无法合法归类的错误保存到 journal 并在报告留 `unreconciled_attempts`，`BLOCKED_SOURCE`，不把它们算作“未发送”。

RPC error 原始 `message/data` 不写入报告，只保留 JSON-RPC 数字错误码和规范化 envelope 的 SHA256；不保留全部原始响应体。不能把 SHA256 视为已独立复算的链上证据。请求尝试数不等于服务商确认收到或计费。`actual_rpc_calls` 在真实运行指发送函数被尝试调用的次数，在 fixture 模式始终为 0；本次没有任何真实请求。

### 完整 Git 绑定及许可

真实模式必须依次校验：新 `scope` / 经独立批准的固定 Git HEAD 与**执行脚本 SHA256**、被 import 的四份 Python 源文件与两份 manifest/Router registry 的实际工作树字节都等于 Git HEAD、最多 24 次与两组限额、官方 endpoint、本地 `/tmp` 输出路径、响应 cap、10 分钟窗口、一次性随机 nonce。`consume_nonce` 在第一请求前持久登记且不可重复运行。**一个含 `user_authorized: true` 的文件并不能证明用户同意，也不能代替具体 permit 的独立审核。** 本 PR 不提供可用于实际运行的 permit 文件；运行前必须先取得用户另行书面授权及另一 AI 对具体文件逐项复核。

特别注意：重新运行程序不会补全失败的上一次尝试；一个 nonce 即使在第一请求前崩溃也已消耗。

## 离线可复现（仅使用合成钱包，不发送 HTTP）

从仓库根目录：

```zsh
python3 -m unittest discover -s crypto-300-profit-mission/bsc-forward-follow-model/f0/tests -p 'test_*.py'
python3 crypto-300-profit-mission/bsc-forward-follow-model/f0/f0_l1_code_probe.py --fixture crypto-300-profit-mission/bsc-forward-follow-model/f0/fixtures/l1_code_probe_24_mock.json --manifest crypto-300-profit-mission/bsc-forward-follow-model/f0/fixtures/l1_fake_cohort.json --router-registry crypto-300-profit-mission/bsc-forward-follow-model/f0/F0_ROUTER_SOURCE_CANDIDATES.json
```

合成回放固定 **24 次尝试（2 来源身份、20 钱包、2 Router）**，`actual_rpc_calls=0`，本地 CLI 结果与 `fixture_l1_code_probe_24_report.json` 一致。

**本地隔离测试：`Ran 209 tests, OK (skipped=2)`：207 PASS、2 SKIP。** 跳过的两项是继承的真实 PR116 原始 manifest 正例，因为此隔离目录缺少它。**独立审核必须在含真实 manifest 的完整 Git checkout 重新执行并证明 `209/209 PASS、零 SKIP`**。新 23 项定向测试均已执行且通过。不能把这一期的 2 SKIP 声称通过，也不能把审核通过自动升级为真实 API 许可。

### 下一阶段真实业务目标（仍待授权）

完成真实技术资格检查后，基于实际 20 个 PRIMARY 的代码状态、Router 代码和失败率决定是否可进入短窗口完整区块 L1 连续扫描及普通 Router 控制候选预注册。**真正 F0 的连续块覆盖率、首见时延、Router 交易因果、E1/E2/E3、+60/300/900s 报价和对照组分母仍未测量。** 本次资格检查不是 24–48 小时 F0 授权，必须独立审批。
