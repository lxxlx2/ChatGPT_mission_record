# Issue #165 Acceptance B：Mac 既有完整源零网络回放

**EXISTING_FULL_SOURCE_REPLAY_VERIFIED_DATED**

本次结论：找到了完整 SPL Token 与 Token-2022 owner 回执，并在固定 PR60 代码下回放成功；它们只能证明已明确记录日期/各program finalized slot 的历史 token-account 余额，**不能证明 2026-10-23 当前持仓**。Acceptance B 的当前余额证据仍缺失；本轮停止，不采集新源。

## 实际生产与文件核对

- 正式8766唯一监听者 Dashboard PID88897；cwd固定发布SHA `656ed2c96f4210d106d7b1129ec6cf8d7c4586f3`；437个安装文件均与已安装规范清单一致。
- 只GET `/api/frank-observed-watchlist`，数据更新时间 `2026-10-23T10:15:57+00:00` 是本地视图生成时间，不能当链上余额采集时间。
- 实际 `data_source=READ_ONLY_FORWARD_SQLITE`、`scope=LOCAL_INDEX_ONLY_NOT_COMPLETE_CHAIN`、`snapshot_status=SNAPSHOT_NOT_PRESENT`，没有snapshot_origin/date/slot。1355行全部 `current_chain_balance_verified=false`、`current_chain_balance=null`，全链覆盖false。
- 本地状态汇总：model_open3、inventory_needs_review4、historical_exit24、unresolved_history20；这些不是RPC真实当前持仓结论。
- 当前control-root的 `frank-inventory-snapshot.json` **不存在**，lstat无文件且不是坏symlink。其hash/mtime/来源均为N/A，未修改或创建。
- 与此前仓库推断不同：安装包只包含local-agent树，原server解析的同级 `meme/evidence/frank-v2-thirty-two-mint-finalized-2026-10-11.json` 不存在，因此本机并未显示仓库Oct11回退快照；ATA证据也返回EVIDENCE_NOT_PRESENT。只记录实际来源缺口，本轮不修部署/源码、不导入历史数据以冒充当前。

## 私有证据范围与离线方法

只枚举已知 `~/.local/share/frank-owner-full-rpc-evidence` 和 `~/.local/share/frank-f02-research/manual-sessions` 的回执manifest/两份raw文件；没有扫描整个用户目录、读取私钥或数据库。没有打开研究SQLite，包括其WAL/SHM。

独立detached checkout：PR60 `e4529ba7069e5499d12323a7160ceac08c481fae`。直接调用该版本未改动的 `replay_owner_full_receipts(bundle, expected_wallet=...)`；expected owner来自该固定版本Frank registry，且与目标32-Mint来源owner一致，并非只相信manifest自报owner。Python socket connect/create_connection在审计进程内被拒绝函数保护。未执行采集CLI的 --execute/--import-sidecar；没有SQLite import。

3/3回放通过：验证每份原始响应bytes、SHA256、JSON-RPC id、program、owner、每账户pubkey/Mint、raw amount、decimals、账户state、slot、账户去重、capture指纹及两program完整性。原manifest/raw文件回放前后hash不变。不会把局部Mint过滤结果当全owner程序回执。

## 三组历史读取（SPL / Token-2022 分列）

|manifest采集开始时间 UTC|finalized slots|账户数 SPL / 2022|总账户 / Mint|目标32历史余额|
|---|---|---|---|---|
|2026-10-14T15:54:15.873036+00:00|456895319 / 456895320|1785 / 1448|3233 / 3233|9 非零 / 23 零|
|2026-10-15T06:10:01.348696+00:00|457132317 / 457132319|1788 / 1488|3276 / 3276|9 非零 / 23 零|
|2026-10-17T22:19:21.466690+00:00|458199733 / 458199735|1820 / 1728|3548 / 3548|8 非零 / 24 零|

采集时间来自manifest `observed_at_utc`（客户端记录，非区块时间或provider签名证明），文件mtime分别保存在replay-summary.json，不能代替经认证的请求结束时间。最新组曼谷时间为2026-10-18 05:19:21，今天已是2026-10-23，不足以证明当前余额。

每组均 `same_slot_atomic=false`；SPL和Token-2022是两次独立请求，slot相差1或2，不可归并成同一slot。不同日期三组也绝不拼成一个组合余额。回放器保留 `wallet_total_balance_verified=false`；native SOL、其他token program、受益所有权、全历史/估值/PnL不在本证据证明范围。

最新组：全owner 3548个账户、3548个不同Mint，其中2680账户/Mint非零；**不等于2680个主动买入或可交易有价值持仓**，包括可能被动到账/无价token。目标32Mint均各有1个账户（32/32），raw/decimals逐项保留且与Oct11目标roster的decimals一致；不是只查ATA，也没有把不存在账户一律当零。

## 最新组目标32：脱敏逐账户核对

账户与Mint只发布SHA256前12位识别符；完整SHA256、raw、decimals、program、slot、state及时间见派生CSV/target32 JSON。**不发布完整地址或原始RPC回执**。这里每项都有真实账户，raw=0表示该程序slot下该账户实际零余额，并不代表今天已清仓。

|Mint哈希前缀|Token Account哈希前缀|原始数量raw|decimals|finalized slot|
|---|---|---:|---:|---:|
|`5e83acc43c03`|`7282e8dc51a7`|0|6|458199733|
|`f3e91760ad21`|`72f42e55b880`|0|9|458199733|
|`2980a1f1bcd7`|`b63bf2eda95d`|0|6|458199733|
|`42370c25ac86`|`08ae713d3ebc`|0|6|458199735|
|`c70d3f501219`|`2cb07c1a7ed6`|7263953506555|6|458199735|
|`3767258429ec`|`d3bdc219def4`|0|6|458199735|
|`d527f0555369`|`da3ebe6e56d6`|0|6|458199733|
|`f12b8928ba72`|`0701ba736a16`|0|6|458199735|
|`eab478af01ca`|`df0314316e97`|22246999|6|458199735|
|`8e68a07f56a3`|`997c217dc495`|29551841|6|458199735|
|`cdf80fe14d81`|`00eaa5bd855f`|0|6|458199735|
|`a422964cc1ea`|`aef142801e43`|0|6|458199735|
|`1bf7ae1570ed`|`7ebe684daccc`|0|6|458199735|
|`6c61a8e69f81`|`c1394f0693d9`|12043213758361|6|458199735|
|`627ac0f2a75c`|`6aba56f422f4`|0|6|458199735|
|`7175dcb95b38`|`efb1c3ec6a28`|0|6|458199735|
|`039455d3cdd1`|`c28359792006`|0|9|458199733|
|`9e040ad5ed06`|`8fc8b593ebb3`|52736752|6|458199735|
|`dfd42fb00c17`|`b943d2ae9d78`|0|6|458199735|
|`88fad0dfe522`|`d5c575023736`|0|6|458199735|
|`7e834b723ba7`|`a0c7361fe119`|0|6|458199735|
|`b893d3daa499`|`5931f1ba5384`|9090666|6|458199735|
|`1032be2a4eb8`|`2d1f5f31b67c`|0|6|458199735|
|`e225a43e974d`|`a135d5ce6574`|50017498|6|458199735|
|`c80ba527afdb`|`cf74106f1354`|0|6|458199735|
|`36aa002a6fdf`|`78447e6dd8b6`|0|6|458199735|
|`0b877749a3f8`|`0fa19000d5e0`|3411999978741|6|458199735|
|`2b2a4c3dafcf`|`2f28e67bf142`|0|6|458199735|
|`9bdd899388ae`|`6dc952b79348`|0|6|458199735|
|`432c049d3cd0`|`55abb3522647`|0|6|458199735|
|`142e500c3320`|`bdc99f3ad8a4`|0|6|458199733|
|`06a4ac1b17c1`|`4d8c5a1b2fe9`|0|6|458199733|

所有程序返回账户的逐项脱敏对照分别保存在三份 `*-accounts.csv`，覆盖3233/3276/3548行；不只发布32条。三份 `*-target32.json` 是各日期目标账户分项对照；replay-summary.json含program官方ID、原响应byte/hash、manifest/capture指纹。哈希仅证明此次字节一致性与可重复执行，不是独立provider attestation。

## 缺失证据与下一次待授权方案（本次不执行）

缺口：没有今天的两program finalized owner完整回执、精确请求开始/结束时间与当前slot、没有当前导入快照；旧manifest不保留历史provider身份，不能从raw JSON反推当时提供商。现有证据不支持“当前余额完整”或CA/钱包全部业务验收通过。

下一轮最多 **2条** `getTokenAccountsByOwner`，分别官方 SPL Token / Token-2022 programId，owner为同一已注册Frank钱包，`encoding=jsonParsed, commitment=finalized`；不按Mint过滤、不分页/自动重试/切换备用源。第二条可用第一条slot作为minContextSlot，但仍非原子快照。为避免现有采集器首条失败后仍继续第二条，执行方案必须由外层明确门禁：第一条失败即停止，第二条不发。

- 实际可用提供商：本机既有配置的 **Alchemy Solana Mainnet，host `solana-mainnet.g.alchemy.com`**。只读取并记录hostname，没有公开URL路径/key，也没有探测端点。
- 用量：最多2次JSON-RPC请求，成功时2份完整响应；不调用getBalance/getSlot/报价/交易/扫描。留存请求起止UTC、program、slot、HTTP/JSON错误、raw byte/hash与manifest。
- 费用：**本轮新增RPC费用为0（未请求）**。该账户套餐、方法CU费率及边际收费尚未核实，不能承诺免费或编造美元上限。下一次授权前须明确“现有已付/免费剩余额度、禁止超额计费”的可核验预算；无法确认额度/费用上限则不发请求，不购买额度/新key。
- 响应上限：PR60原实现 **每条12,000,000 bytes**，两条至多24,000,000 bytes；已有最大单条约1.01MB仅是历史观测，不保证未来大小。25秒HTTP timeout；不安装常驻任务。
- 停止条件：未获新授权、费用/配额不明、非HTTPS/重定向、HTTP非200/429/5xx、声明长度不一致/截断、超上限、JSON-RPC错误/id不符、owner/program/账户归属不符、slot缺失/低于minContextSlot、重复账户/decimals矛盾，任何一项出现立即停止；保留partial原回执但不导入、不声称完整，不重试或补更多调用。

本报告仅提交方案，不执行以上任何调用。**NO_NEW_RPC / NO_DB_IMPORT / NO_PRODUCTION_CHANGE / NO_NOTIFY / NO_TRADE**。完成有界审计后停止；不重复D1、CA页面测试或另开功能PR。
