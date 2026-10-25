# Frank P1-B — 2026-10-25 双程序 owner 实际来源：离线核对与 32 Mint 验收门禁

**状态：PLAN_ONLY。** 本文件不是 Mac 私有目录读取、RPC、生产导入或 Dashboard 发布授权。单次官方公共 RPC 请求已经完成，授权已经消耗，禁止重试。Issue #165 原业务 P1 未关闭。

## 1. 最新已核实的 GitHub 证据

- [Mac 唯一真实采集执行记录 #6394698928](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6394698928)，显示 `FRESH_OWNER_CAPTURE_PASS / FULL_DUAL_PROGRAM_SOURCE_REPLAY_VERIFIED`。记录由执行器生成；协调器只从 GitHub 独立读回，**没有再次读取 Mac 私有原始回执**。
- 固定被审核采集代码 SHA：`79ae1b91081f9a7fe659eda9cea59fb80eea16e1`（PR #195 Draft/未合并），原基线 PR #60 `e4529ba7069e5499d12323a7160ceac08c481fae`（Draft）。[独立 Mac 代码审核 #6394432036](https://github.com/lxxlx2/ChatGPT_mission_record/pull/195#issuecomment-6394432036) 已批准代码/离线行为。
- 官方公共端点 `api.mainnet.solana.com`，实际两次只读方法 `getTokenAccountsByOwner`，每程序一次，HTTP200，零重试、零备用端点。执行时间 `2026-10-25T07:06:02–07:06:03Z`（曼谷14:06），Finalized SPL Token slot **461166205**，Token-2022 slot **461166207**，**不同 slot、非原子**。第一条归档/fsync 完成后才发起第二条。
- SPL：**1876** Token Accounts / **994698** bytes / SHA256 `40f61bf0e85c61adbb50c140ee67173e3a92bcfbab99798dee6b51dc76d3cb78`。Token-2022：**2429** Token Accounts / **1417112** bytes / SHA256 `308fec08408a18d566e3aa9b742d756280a4c799e1dfde29ced9219df7277574`。
- 执行报告宣称合计 **4305 unique Token Accounts、4305 unique observed Mints**；完整 manifest `complete=true` 且 missing 空，离线 replay 成功；标准化 capture SHA256 `7b07a0298cb2209a244cb2103883bff54e3c7a8487985321fdfb29d7a1eb2f5e`。实际非零 Mint 数量、目标32核实情况 **尚未给出**；4305 不得作为投资持仓数量。
- 真实旧 D2 仅为 **2026-10-23T14:46:32Z** 的另外两条 finalized slot 历史数据，**4148 observed Mints / 3275 nonzero Mints**，目前仍是正式8766唯一已安装的该历史观察来源。新总数与旧总数相减 **+157**，只是集合基数的净差；**不能推断新增157个 Mint，也不能推断157笔买入**，必须私下计算集合的 added/removed/intersection。
- 当前正式 Dashboard 产品 SHA `914e9e47fed2e60bc24690fcb083413a64d4e681`，旧 PR168 rollback 保留。未发生本轮部署、生产私有 JSON 替换、SQLite 导入、Loop/V1重启、通知、交易。

## 2. 下一次仅离线核对的最低范围（需要新的单独授权，当前未执行）

仅在用户重新批准 **Mac 私有目录有限只读访问＋可选新临时目录内派生报告**后，在 Mac 上使用固定 SHA 的原始 replay 源处理本次**已经归档的完整原始证据**，不得重新请求链上：

1. **先固定原始来源**：仅从已知 Git-external owner-only evidence bundle 路径读取原始两个 wire（0600），校验 SHA256/字节长度/文件身份/0700父目录；回放前核对原始 manifest 完整两程序/owner/slot、capture digest。不要扩大为递归全用户目录搜索，不遍历生产 SQLite，不读取浏览器登录凭据。读取/校验失败即 `OFFLINE_REPLAY_SOURCE_BLOCKED`，不能从旧快照补齐。**禁止任何网络调用**。
2. **单份标准化 replay**：使用 [PR195固定源码](https://github.com/lxxlx2/ChatGPT_mission_record/blob/79ae1b91081f9a7fe659eda9cea59fb80eea16e1/crypto-300-profit-mission/local-agent/mission_agent/mission_control/wallet_full_rpc_evidence.py) 的 `replay_owner_full_receipts`，验证 source digest、4305 unique accounts、Mint 唯一性、两程序实际 finalized slot。若原账户有多个 TokenAccount 对应同 Mint，归一化汇总必须依据源文件去重，不能简单按账户数计算币种数；若 replay 与报告 count 不同，记录冲突，停止并保持数据原样。
3. **D2 纯离线派生**：已经部署的 [`wallet_owner_at_slot.py`](https://github.com/lxxlx2/ChatGPT_mission_record/blob/914e9e47fed2e60bc24690fcb083413a64d4e681/crypto-300-profit-mission/local-agent/mission_agent/mission_control/wallet_owner_at_slot.py) 提供 `project_replayed_owner`；[`wallet_d2_ingress.py`](https://github.com/lxxlx2/ChatGPT_mission_record/blob/914e9e47fed2e60bc24690fcb083413a64d4e681/crypto-300-profit-mission/local-agent/mission_agent/mission_control/wallet_d2_ingress.py) 提供 `build_d2_document_from_verified_pr60_replay` 和 `validate_d2_document`。优先复用这些**现有且已审过的函数**，不新造投研余额汇总规则。新文件仅在 **Git外新的 owner-only 临时目录**进行本机 dry-run，核对全部数量/decimal/zero/unobserved分类、返回来源哈希、source schema 和文件大小不超过现有 D2 **4,000,000 bytes**限制；不写回旧 `frank-d2-private`，不动 8766。
4. **32 个目标 Mint：必须先有可信固定 roster**，核实其版本/来源、每个 Mint key 的正确性、是否与同一已注册 owner 相符，逐一离线映射至 normalized replay，逐个标记 `NONZERO_AT_SLOT` / `ZERO_AT_SLOT` / `NO_ACTIVE_OWNER_TOKEN_ACCOUNT_OBSERVED_AT_SLOTS`；缺少 roster 即 `TARGET_32_ROSTER_NOT_VERIFIED`，不能默认用页面 watchlist 或 PR60 的全量 Mint 集合代替。未观察到账户**不是被链上证实的余额0**。
5. **旧新两日期集合比较**：如果用户另批读取**特定旧 D2 私有 JSON**，只按其已校验的日期、slot、owner 和 Mint 分类来做交集、旧独有、新独有与数量变化；计算 `old_only`、`new_only`、`shared`，其关系须满足 `old_only + shared = 4148`、`new_only + shared = 4305`；然后在共同 Mint 中再分类数量升/降/不变。**不得**称数量变化为买/卖或真实 PnL（可能为转账、空投、销毁或 TokenAccount状态变化）。旧来源读取是额外受限的私有访问，不默认涵盖在单纯新 bundle replay 的许可中。
6. **只输出脱敏小结**：Git Issue 允许提交总数、非零数、32目标的状态计数、旧新集合统计、slot/time/source digest、兼容验证与失败原因；不发布 owner 地址、Mint名单、Token Account pubkey、具体余额、私有完整原始响应、真实本机文件路径、RPC/API 密钥。逐项账户核对表只能在本机0700/0600私有环境内保存（若用户批准）。
7. **验收等级**：`OFFLINE_NEW_SOURCE_REPLAY_PASS`；`TARGET_32_AT_SLOT_VERIFIED`仅在32个目标均经可信 roster 对照；`OLD_NEW_RECONCILIATION_PASS`仅在旧源可信且集合恒等式成立；`DRY_RUN_D2_DOCUMENT_VALID`仅在严格schema/大小/哈希验证通过。各状态独立，不互相推导；禁止通过中间任一项直接宣布生产已更新。

## 3. 不可越界的下一步决策

在完成上述**新的、单独授权的 Mac 离线核对**前，P1-B状态只能认定 **“更新的两程序 finalized 来源确已取得”**，不是永久实时持仓、原生 SOL 资产、全钱包估值、盈亏、32目标通过、活跃主动买单或实际发版验收。

是否把 10月25日派生的 D2 文档导入/替换当前 10月23日私有来源，须等待此阶段校验与独立固定SHA审核结束，再由用户**另外授权一次生产私有数据切换/回滚**；不能把本次 Solana RPC 权限延伸为 Dashboard release 权限，也不能自动写 SQLite、开启定时更新、发邮件、通知、交易。持仓 P1 的业务验收应记录采集 slot 和已知过期性质。

CA Quick/Standard/Deep 真实新扫描正确性是**另一个仍 OPEN**的 P1，历史缓存单次 GET 的 PASS 不能替代。

**Current coordination**: `FRESH_OWNER_CAPTURE_PASS_GITHUB_RECORDED / OFFLINE_NEW_BUNDLE_RECONCILIATION_NOT_YET_AUTHORIZED / TARGET32_NOT_VERIFIED / HISTORICAL_D2_OCT23_UNCHANGED / NO_IMPORT_OR_RELEASE / ISSUE165_OPEN`.
