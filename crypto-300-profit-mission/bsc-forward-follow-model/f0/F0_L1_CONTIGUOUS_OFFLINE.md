# BSC F0 — 连续区块 L1 钱包与 Router 随机对照发现的离线验收

**2026-10-20, Asia/Bangkok.** `OFFLINE_L1_PROTOTYPE / NO_NETWORK / NO_RUN / PENDING_INDEPENDENT_REVIEW`。本阶段独立于旧 PR #40（BSC 钱包研究）与 PR #97（449 钱包活动筛查）；继承 **PR #125 固定 SHA `fa3dae9b0f221747cb64bb1be21497979985e596`** 的获批离线代码，PR #127 `91eca250939f17fd0430f2b657e704434f0421eb` 的历史 smoke 归档已获独立 APPROVE，仅限文档证据。任何 PR 的合并及 Mac 部署不在本次范围内。

## 主线目标

首次真实公共 HTTP smoke 的用户本地报告确认 BSC `chain_id=56`，一个高度为 `128614660` 的完整区块有 49 笔交易、4 次调用及 1 次区块发现读、receipt 身份匹配。**原始 HTTP payload 未上传，不能在本 PR 中重放；49 笔是单块，不是平均。** 当前代码阶段要先建成可复现的“连续完整区块发现→缺口与预算记录→名单钱包 vs 普通 Router 对照候选”数据接口。再次触链及真实两分钟连续读取尚未授权。

## 已实现接口 `f0_l1_window.py`

输入：`--fixture`（只能 `mode=SYNTHETIC_SAVED_RPC_ONLY`、`trial=true`、BSC 56，注入 UTC + 单调毫秒钟）；`--cohort`（PR #116 固定预选清单格式，恰 20 PRIMARY + 10 BACKUP，PR40/PR97 各 10 个 PRIMARY + 5 个 BACKUP，排除已知事后收益字段，不得自动启用 watch）；`--report`（可选本地 JSON）。只接受已保存的 `eth_getBlockByNumber(full=true)` 格式信封，无 HTTP、WS、付费 API、后台服务、实际报价、签名或通知。遗留适配器 `block_candidates()` 与抽样 `_hash32(seed|wallet|tx_hash)` 函数直接复用，**不修改已审核模块**。

逐高度建立 4 种事实：`RECEIVED`、`FAILED`（请求已尝试，保存原因）、`MISSING_NOT_ATTEMPTED` 与成功读取但 `ingest_path=BACKFILL`。保留区块哈希、parentHash 连续关系、响应哈希、请求/响应/首次记录 UTC 与单调时钟，检查高度与 full-tx 身份。**允许不同区块请求在时间上重叠**（只要求请求开始时间有序及各自的请求→响应→首次入库顺序），不把未来真实 0.45 秒出块误认为只能串行采集。跨缺失区块不宣称已核实连续父哈希。任何验证时钟仍是**合成注入**，不代表 BSC 实际首次对外可见时间。

WATCHLIST 用交易对象 `from` 是否命中 PRIMARY 判断，含普通签名交易，**不是 BUY 成交**；普通 Router 候选要求非名单发起地址 `from` 且 `to` 精确在**合成** Router 允许列表。控制组按照现有固定 FNV 函数预选，输出 `control_selected_offline=true/false`，但不假装已经建立真实对照组。`BACKFILL` 不会成为真实 E3。**PR #129 审核 P1 修复：** 真实 cohort 路径必须验证 PR #116 manifest 原始字节的 Git blob SHA1 = `fcd0029314353313867e565190cd4f2882089f11`，并核对 `selection_seed` 等于冻结架构 SHA `9134fcd41df49ef836b81c8a040974ad89c1fde1`。随机对照只从 cohort 的 `selection_seed` 派生，fixture 不再允许提供 `control_seed` 覆盖。输入明确声明 `cohort_source_kind`：`SYNTHETIC_FIXTURE_ONLY` 仅接受标记为 synthetic 的假名单，`FROZEN_PR116_GIT_BLOB` 只有在提供真实原始字节、其固定 Git blob 完全匹配后才可识别冻结 PRIMARY。报告给出 `VERIFIED_PR116_GIT_BLOB_OFFLINE_ONLY` 或 `SYNTHETIC_FIXTURE_NOT_REAL_COHORT`；所有分支仍完全离线。**名单 blob 合格并不意味着 EOA 技术资格已核实**，真实 Router allowlist 仍未冻结。

单独输出完整窗口分母、成功块、失败块、缺失高度、BACKFILL 块、关注钱包签名交易、普通 Router 候选、已预抽样候选、尝试的 HTTP/发现成本（合成）。源端真实成本、真实分母及漏读率一律 `NOT_MEASURED`，`actual_rpc_calls=0`、E2=false、E3/QUOTED/PAPER=0、`NO_RUN`。只有后续用户单独授权且通过审核的真实采集器能使用实测时钟或升级证据。

## 实际离线验收证据

从 repo root 运行：

```zsh
python3 -m unittest discover -s crypto-300-profit-mission/bsc-forward-follow-model/f0/tests -p 'test_*.py'
python3 crypto-300-profit-mission/bsc-forward-follow-model/f0/f0_l1_window.py --fixture crypto-300-profit-mission/bsc-forward-follow-model/f0/fixtures/l1_contiguous_replay.json --cohort crypto-300-profit-mission/bsc-forward-follow-model/f0/fixtures/l1_fake_cohort.json --report /tmp/bsc-f0-l1-synthetic-report.json
```

测试清单 `l1_fake_cohort.json` **全是编造的 EVM 测试地址**，现显式标为 `synthetic_fixture_only=true`，不允许被误标为真实预选名单。新增的 `test_real_pr116_git_blob_and_primary_wallet_positive` 直接读取仓库中的真正 `F0_COHORT_PRESELECTION.json`、校验固定 Git blob、把真实 PRIMARY 钱包地址注入人工 full-block 以验证 WATCHLIST 命中；仍不访问 RPC。独立审核必须在包含真实 manifest 的完整 Git checkout 执行该正例。合成夹具高度 100–104：成功 100、103、104；101 模拟请求失败、102 未读取；103 是 BACKFILL。返回 **窗口 5，高度成功 3、失败 1、未读 1、已尝试发现 4、watch signer 3、Router 候选 3、合成预选 2**。29 项定向测试包括漏块、hash 链、错误区块/重复高度、发起人而非收款人、失败计数、预算、时钟、预选分层及禁止盈利字段、BACKFILL 不可变成 E3。本轮修复在原批准的 156 项上新增 7 项，共发现 **163 项**。当前本地隔离树缺少真实 manifest 文件，结果 **162 PASS + 1 SKIP**；该 SKIP 是真实 blob 正例，不能冒充通过。PR 中原始 Git checkout 包含 manifest，独立复审必须完成 **163/163 PASS、零 SKIP**。本轮变更证据单独存于 `F0_L1_FROZEN_COHORT_EVIDENCE.json`，原 PR #129 固定 SHA 的证据不作回写。

## 下一阶段真正需要什么

1. **修复版定向复审**：在完整 Git checkout 完成 163/163 测试、零 SKIP，特别核实真实 PR #116 Git blob、PRIMARY 钱包正例和抽样 seed 来自真实 manifest。PR #127 已独立批准但只限历史证据。
2. 冻结用于真实捕获的 20 个 PRIMARY 的技术 EOA 合格状态（按 PR #116 只做技术替补）；冻结真实 Router allowlist、FNV 采样参数、独立数据源与分母方案，拒绝历史收益/结果泄漏。
3. 设计完整的**有界实时采集适配**（首次观察 UTC+monotonic、父哈希/缺块与追块、HTTP 请求预算、主/对照共享发现流、receipt 可能缺席）。先用 mock transport 做有界本地演练。
4. 若需要真实 2 分钟 L1 试验，按主网约 0.45 秒每块预估约 267 个新区块、至少相近数量的 full-block 读取；还要额外 head、receipt、失败及审计调用。**此前四次真实 RPC 许可已耗尽**：必须重新由用户批准端点/方法、总请求及控制发现次数、rate、UTC 时间窗口、存储留存和免费费用上限；具体 permit 需独立审查，不能自动重用 PR #125 的 nonce 或扩大预算。
5. 若短窗口内未见真正名单 BUY、实时可比普通对照，报告 `INSUFFICIENT_LIVE_EVENTS` 或 `BLOCKED_REALTIME_CONTROL`，不得用合成结果代替可跟单收益。

**权限边界：** `NO_RPC / NO_WS / NO_TRADE / NO_SIGN / NO_ALERT / NO_BACKGROUND / NO_DEPLOY / NO_MERGE`。本 PR 仅离线代码。不要为了边界问题无限延期核心功能；下一关键验收是有限真实窗口的发现率与对照组成本，而非新的历史选币回测。
