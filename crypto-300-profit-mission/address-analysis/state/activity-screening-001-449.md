# 449 钱包活跃度初筛最终进度

更新：2026-10-19（Asia/Bangkok）
状态：`ACTIVITY_SCREEN_COMPLETE / PNL_REVIEW_NEXT / RESEARCH_ONLY`

已按原来源顺序完成 **449/449** 个 EVM 地址的历史签名活跃度首轮筛选。前120地址完整核查 BSC、Ethereum、Base 起终 nonce，后329地址 BSC 优先、无签名时查 Ethereum，再查 Base，首次命中早停。

| 项目 | 数量 |
|---|---:|
| 固定来源钱包 | 449 |
| **已初筛** | **449（100%）** |
| **至少一条已查链有签名活动（下一阶段优先）** | **237** |
| **BSC/ETH/Base 均无签名增长（暂缓）** | **212** |
| 待筛 | 0 |
| 完整钱包近30天/长期PnL已审计完成 | 0 |

## 最后四批实际结果

| 批次 | 来源行 | 有签名活动 | 三链无签名 | 原始nonce文件 |
|---|---|---:|---:|---|
| 020 | 381–400 | 10 | 10 | [JSON](../evidence/batch-020-first-hit-bsc-eth-base-nonce.json) |
| 021 | 401–420 | 11 | 9 | [JSON](../evidence/batch-021-first-hit-bsc-eth-base-nonce.json) |
| 022 | 421–440 | 11 | 9 | [JSON](../evidence/batch-022-first-hit-bsc-eth-base-nonce.json) |
| 023 | 441–449 | 1 | 8 | [JSON](../evidence/batch-023-first-hit-bsc-eth-base-nonce.json) |
| **新增合计** | **69个** | **33** | **36** | |

- [449 地址逐行状态、来源行号与全部候选集合](../evidence/activity-candidates-001-449.json) 是当前权威记录；历史前380/220等快照保留，不再代表最新进度。
- [237 个待查盈亏的活跃候选 CSV](../evidence/active-wallets-237.csv) 按原始地址顺序排列，可直接逐批加载。
- 最后一批仅 **#444** 命中 BSC 签名增长，其余8条三链未见签名增长；没有遗留未确认RPC错误或缺查链。

## 下一阶段：先做真实钱包盈利筛选

**盈利研究只对237个活跃候选优先执行，仍按原始来源行号每批20个，不再增加无关开发工具。** 第一批活跃行号：
`1, 2, 3, 4, 5, 6, 7, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 25, 27`。

逐钱包报告：近30天/长期交易与盈亏可核实部分、盈利币种、亏损币种、手续费及未实现持仓；无法取得历史成本或跨链来源时标 `UNRESOLVED`，不阻塞下一钱包。仅看过交易签名不等于发生代币买卖，不把已保存的3组正收益单币轮次推广成3个盈利钱包，不根据钱包接收token自动判定0成本。

**本轮仅BSC/Ethereum/Base三条链、冻结2026-09-17至2026-10-17 UTC的签名nonce变化。** 无签名并不意味着Polygon、Arbitrum及所有其它EVM网络不活跃，也不排除被动接收ERC20/NFT。筛查结果不表示2026-10-19当前实时活跃，不能把237当作所有EVM活跃钱包真实总数。

`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE / NO_NEW_AUTOMATION`。PR #97 继续 Draft。
