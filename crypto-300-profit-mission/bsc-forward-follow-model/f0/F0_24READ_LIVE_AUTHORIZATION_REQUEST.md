# F0 — 24 次真实 BSC HTTP getCode 资格检查：待用户单独授权的执行申请

**状态：`PERMISSION_NOT_GRANTED / NO_RUN / NO_ACTIVE_PERMIT`。**

## 审核基线与审核边界

- 最后通过独立审核的可执行代码固定 Git SHA：`cd30f8b69301b53380473a33ebb428351d4c1bce`，对应 [PR #136](https://github.com/lxxlx2/ChatGPT_mission_record/pull/136)。完整 Git checkout 独立执行 `213/213 PASS, zero SKIP`，此前 PR #135 的报告覆盖账本 P1 已关闭；此批准 **仅限离线代码**。
- 由 PR #136 修复过的 `f0/f0_l1_code_probe.py` 文件 SHA256：`3a3b399262280760a3c87a161a96536911717671612919bd66770ed842a6fea8`，Git blob `046f50179a4163739d4dc1ed47fac243b196381d`。执行前，具体 permit 必须绑定该 commit SHA 和该 SHA256，且全部依赖文件的原始字节必须与 Git HEAD 相等；**不得**将本说明文件所在的后续文档分支 HEAD 填入 permit，也不能从该分支运行审核过的执行器。
- PR #116 的真实冻结 cohort manifest blob：`fcd0029314353313867e565190cd4f2882089f11`。仅覆盖其中 20 个 PRIMARY 钱包（10+10）；无 BACKUP 替换或收益筛选。
- 两个候选 Router 来自 `F0_ROUTER_SOURCE_CANDIDATES.json`：PancakeSwap v3 Universal Router `0x1A0A18AC4BECDDbd6389559687d1A73d8927E416`、Infinity Universal Router `0xd9C500DfF816a1Da21A48A732d3498Bf09dc9AEB`。文档来源 https://developer.pancakeswap.finance/contracts/universal-router/addresses ；**链上运行代码和 swap 因果尚未验证**。

## 拟请求用户一次性授权的确切范围（非现有授权）

| 权限维度 | 提议 |
| --- | --- |
| 访问地点 | **仅用户自己的 Mac**，在独立 checkout 的固定 `cd30f8b...` 代码上运行一次；没有代操钱包 |
| 官方端点 | `https://bsc-dataseed.bnbchain.org`，无需钱包密钥或付费 API |
| RPC 方法 | `eth_chainId` → `eth_blockNumber` → 20 × `eth_getCode(PRIMARY, frozen_height)` → 2 × `eth_getCode(Router, frozen_height)` |
| 链与高度 | 主网 `chain_id=56`；仅一次读取最新高度，后续 **22 个 getCode 使用同一高度** |
| 请求硬上限 | **最多 24 次尝试**（2 身份/高度 + 20 PRIMARY + 2 Router）；失败调用、已发送但无响应或崩溃中断的调用仍消费预算 |
| 速率与时限 | 串行；许可固定 `min_interval_ms=250`（严格不小于 100 ms）；每次发送前检查 UTC 时间窗；有效窗口 **至多 10 分钟** |
| 响应上限 | **每次不超过 2,000,000 字节**；超限停止/分类，不扩容 |
| 退出策略 | Chain ID 非 56、区块高度不可用、三次连续来源失败、权限/配额/时间窗违规均立即停止；**无重试** |
| 文件与保留 | 许可为 Mac 本地私有文件；唯一目录 `/tmp/bsc-f0-24read-...`，固定 `journal.json`（逐尝试写前 fsync，不能覆盖）、`report.json`（汇总）两文件；`retention_hours=24` 是许可限制，**并没有证明存在自动清理器** |
| 禁止 | WS、`eth_getLogs`、发送交易、签名、交易所访问、自动报价、实时长期监听、后台运行、通知、部署、PR 合并、付费数据源 |

**金额与费用：** 本次拟访问 BNB Chain 免费公共 HTTP 数据端点，不使用付费 Alchemy、GMGN 或商业 API；不会进行资产操作。`provider_billed=UNVERIFIED` 仍保留，以区别请求尝试与服务端实际计费。没有已核实的持续免费配额承诺。

## 获得单独用户授权之后（必须按此顺序完成）

1. **用户在对话中明确同意以上准确的 24 次提议范围。** 先前四次真实 smoke 的许可已用尽；PR 审核者的 `APPROVE` 不是用户授权。
2. 在用户 Mac 的 **独立 Git checkout（HEAD 精确为 `cd30f8b...`）** 生成一份不可执行前置状态的 `permit.json`，随后填入一次性 32–64 小写十六进制随机 nonce、私有 `storage_root`、真实绝对 UTC 起止时刻（最多 10 分钟）、`approved_commit_sha`、`approved_source_sha256`、刚批准的 endpoint/methods/caps 和明确用户同意标记。**本仓库绝不提交具体 permit/nonce**。
3. 由另一审核者**在真实请求之前逐字段复审同一份具体 permit 的完整内容及 SHA256**，并核对单独用户授权、受审 Git HEAD、源码 SHA256、执行入口、请求数、存储目录、独立文件名、时间窗和无重试。该审核可以在本地进行；不得把原始 nonce、私有 permit 或本地路径公开粘贴到 Git。若 permit 过期或改变任何字段，审核视为失效，重新生成并复审。
4. 获准后才在用户 Mac 从审核过的源代码调用 `f0_l1_code_probe.py --execute-live --manifest <approved-repo>/f0/F0_COHORT_PRESELECTION.json --router-registry <approved-repo>/f0/F0_ROUTER_SOURCE_CANDIDATES.json --permit <private-path>/permit.json --report <private-root>/report.json`。运行前仍执行既有许可、Git SHA、依赖、nonce、路径检查；不得自动重试。
5. 结束后仅共享**脱敏**的 `report.json` 汇总与 exit code；逐请求 `journal.json` 在本地保留，审核者可在本地核对。公开报告必须区分用户提供的运行结果 vs 独立验证；响应哈希没有原始包则 **UNVERIFIED**。之后新窗口连续 L1 捕获、普通 Router 对照和报价需要**各自独立批准**。

## 实验通过/失败的业务判定

这次最多可以建立 **20 个 PRIMARY 与 2 个 Router 在一个区块高度的代码状态**、响应错误/超时分母和可用公共 HTTP 读写速率的初步事实；不能证明钱包私钥控制、永久 EOA、Router 方法和 swap 因果、F0 连续覆盖率或盈利。所有钱包现在仍是 `NOT_CHECKED`，两个 Router 现在仍是 `onchain_code_verified=false`。**只有真实结果和日志回来以后**，才能决定后续短窗口实时 L1 实验。

### 关于本文件的性质

本文件是**不可执行的权限申请书**，故意**不包含** `user_authorized: true` 的有效 permit、不含 nonce、不设可直接通过校验的实时 UTC 窗口，也不触发任何网络请求。新提交为说明与交接资料；它不改变受审执行器固定 SHA。
