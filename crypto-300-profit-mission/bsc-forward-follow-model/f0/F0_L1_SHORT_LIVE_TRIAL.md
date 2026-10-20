# BSC F0 — 本机 HTTPS 短窗口、最多 60 个未来高度的连续区块试验

**状态：`LIVE_RUNNER_CODE_UNREVIEWED / USER_CONSENT_SCOPE_RECORDED / CONCRETE_PERMIT_PENDING / NO_RUN`。**

用户本轮在 ChatGPT 回复“可以，授权，你开始做采集器吧”。结合前一轮建议的“30–60 个区块、先做短样本”，将此授权**保守限定为一次不超过 60 个完整区块请求 + 1 个 `eth_chainId` + 1 个 `eth_blockNumber` = 最多 62 次只读 HTTP 请求**，在用户自己的 Mac 上，官方免费 BSC 端点。旧 4 次及 24 次单独权限均耗尽。授权是**范围许可**，不能代替新代码 SHA 与**执行前具体 permit 的独立审核**；未审核以前绝对不得发包。

## 固定执行范围

| 项目 | 单次上限/约束 |
| --- | --- |
| HTTP 端点 | `https://bsc-dataseed.bnbchain.org`，Chain ID = 56 |
| 允许方法 | 一次 `eth_chainId`、一次 `eth_blockNumber`，最多 **60** 次 `eth_getBlockByNumber([hex(height), true])` |
| 高度范围 | 官方端点返回的 HEAD+1 至 HEAD+N（N 最多 60），**禁止把旧块倒查冒充前瞻发现** |
| 发包速率 | 串行，两次发包至少 250ms；未来高度计划每块间隔 500–2000ms，不能保证节点实时可用 |
| 总预算 | 最多 62 次尝试，失败、超时、结果 null、中断后状态未知都消费预算，不重试 |
| 窗口 | 不超过 10 分钟的固定 UTC 许可窗口；每次发送前验证仍有效 |
| 大小、延时 | 每个响应不超过 2MB，单请求超时 1–8 秒；遇到连续 3 次无有效区块提前退出 |
| 网络实现 | TLS 主机证书验证、禁用代理和 HTTP redirect，不支持 WS、eth_getLogs、交易、签名、付费服务 |
| 审计 | **统一** `journal.json` 预发送 fsync，源链+head+全部取块都记录；不同的 `report.json`；每个实际返回 HTTP response 原始字节只保存到本机 `raw_responses/*.response.json`（600 权限，**不得上传 Git**） |
| 许可 | 固定新运行器 Git SHA、脚本 SHA256、依赖文件原始字节、一次性随机 nonce，独立审核者批准**具体 permit 文件 SHA256**后才可运行 |
| 输出 | 分类、覆盖与漏块分母、钱包签名 / Router 地址候选，**control_eligible=false**、E2/E3/PnL 未证明 |

该试验统计的是**用户 Mac 收到单个官方 HTTP 节点响应的时间**，不是全网首次广播、块最终性、全球最低延迟或交易可跟单性。针对未来高度的请求可能早于节点发布，`result:null` 只能记为缺块/失败，此次**不得重试以填平窗口**。链头 RPC 如滞后于实际 BSC，全局首次时间不能从该试验判断。

## 本轮代码

- `f0_l1_live_short.py`：真实 HTTPS 传输 + 统一预算与逐请求 fsync 日志；调用 #147 的 HTTP 编解码和 #145/#143 的同源全块解析；固定结束状态与错误分母；本地保存原始来源字节以允许事后复算。
- `tests/test_f0_l1_live_short.py`：**10 项完全 fake HTTP 测试**，包括 60+2 预算、未来一个块成功、`result:null`、错误 Chain ID、超时、KeyboardInterrupt 保留 UNKNOWN、已存在输出拒绝、改动 manifest 拒绝、时间窗过期、禁止 redirect。
- `.github/workflows/bsc-f0-offline-unittest.yml`：只运行不带任何真实网络许可的 F0 unittest，`contents:read`，5 分钟超时。
- #147 的纯 HTTP wire、#145 的 bounded injected collector、#144 的 #141/#143 组合不进行源文件重写。

此前已批准的 #145 完整 suite **230/230 零 SKIP**，#147 的 11 项新增测试本地**11/11 PASS**、但 #147 完整 suite 尚未独立复审。本分支新增 10 项，预计 **251 项完整测试**（230+11+10），只以 CI/完整 Git checkout 的**实际运行**为准。不能把预期 251 宣称通过。

## 执行门禁（在用户 Mac，不要在 GitHub Actions 运行 `--execute-live`）

1. 审核该 PR 的固定 SHA、代码差异与完整测试（要求 251 项 ZERO SKIP），且确认**没有新增 P0/P1**。若需修改，重新固定 SHA。
2. 使用干净、独立的 Git checkout，HEAD 必须等于此运行器获批的 SHA；运行脚本和 10 份依赖/manifest/Router registry 必须与 Git HEAD 完全一致。原 PR #136/#145/#147 的过期许可**绝不可复用**。
3. 在本机私有 `/tmp` 单独目录生成新 permit，字段与 `validate_permit()` 严格一致：`scope=bsc-f0-l1-short-http-single-use-v1`、`user_authorized=true`、`independent_review_required=true`、`endpoint`、`chain_id=56`、三种 `methods`、`max_block_reads=60`、`max_total_attempts=62`、`min_interval_ms>=250`、`future_block_pace_ms=500..2000`、`max_response_bytes<=2MB`、`timeout_ms<=8000`、`fail_streak_limit=3`、10 分钟内的 UTC 窗口、一次性 64 小写 hex nonce、`approved_commit_sha`、`approved_script_sha256`、私有 `storage_root`、`archive_raw_public_rpc=true`、`free_only/read_only/no_retries/no_ws/no_proxy/no_redirects=true` 和 `background=false`。
4. 使用新的隔离只读 Codex/Claude 审核进程对**实际 permit 文件和其 SHA256**、Git 完整依赖、目录权限、UTC、预算、预算消耗策略、nonce、单次运行入口独立复核，输出 `APPROVE_PERMIT <permit-实际文件-SHA256>`。不得由执行 Agent 自己签字。将审核结论按原样保存本地为独立 `approval.txt`，但**不要提交 permit/nonce/approval 文件到 Git**。
5. 仅在审核后的窗口有效时，在用户 Mac 明确执行：
   `python3 crypto-300-profit-mission/bsc-forward-follow-model/f0/f0_l1_live_short.py --execute-live --permit <private-permit.json> --review-approval <private-approval.txt>`
6. 真实调用前用原子方式占用唯一 nonce。任意 RPC 已开始，不得再次运行来凑满 62 次。结束后本地核查 `journal.json` 中请求编号、UTC+monotonic、状态和 raw-response 哈希与 `raw_responses/` 字节一致；再核对 `report.json` 完成/漏块/失败及 Router / watch 候选。报告仅可提交脱敏汇总、哈希、来源分级的证据 Draft PR。

## 后续业务判断

- 如果公共端点 60 个未来块中缺失/失败过多，先如实证明“公共 HTTP 不满足当前延迟/完整性要求”，再讨论免费替代或 WS；不得用假块填充，也不得把 `NO_CODE` 标为永久 EOA。
- 若区块覆盖率和候选量足够，再向用户另行申请真实连续 120 秒 L1 的更大请求预算。+60/+300/+900s 实时报价与独立纸面收益是**后续单独阶段**，不在本次试验范围。
- **不得**开启常驻服务、交易执行、通知、付费节点或主仓库合并。

官方 BNB Chain 文档：https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/
