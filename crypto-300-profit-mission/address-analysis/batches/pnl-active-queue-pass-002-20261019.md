# 地址分析 / 活跃候选第 2 组交易与盈亏初查（2026-10-19）

对应 [Mission PR #97](https://github.com/lxxlx2/ChatGPT_mission_record/pull/97)，**活跃队列序位 21–40**，原源行 `29,30,31,32,34,37,38,39,43,44,45,50,51,60,63,64,65,66,67,68`。与 PR #40 完全隔离；原 449 个钱包的活跃度初筛不再重复。

**进度：** `40/237 ACTIVE_CANDIDATES_FIRST_OUTBOUND_DISCOVERY`，其中本轮 20 个钱包均取得所选链出账第一页，15 个存在未处理的下一页，5 个该类别分页已结束。仍是地址盈利分析的**前置交易发现**，本轮新增已实现盈利/亏损闭环为 **0**，全钱包 30 日/长期 PnL 仍 0/449 审核完成。

## 本组 20 个钱包的可追溯源行记录

查询范围使用冻结 2026-09-17 至 10-17 各链历史区块，单链 `getAssetTransfers(fromAddress, erc20+external, asc, limit 5)`，六个低频或关键钱包 (#034/#044/#045/#050/#051/#060) 额外检查对应入账。结果只是交易方向与代币合约的**来源线索**。

| 源行 | 所查网络 | 出账首批记录 | 还有后续页 |
|---|---|---:|---|
| #029 | bnb-mainnet | 5 | 有 |
| #030 | bnb-mainnet | 5 | 有 |
| #031 | bnb-mainnet | 5 | 有 |
| #032 | bnb-mainnet | 5 | 有 |
| #034 | bnb-mainnet | 6 | 有 |
| #037 | bnb-mainnet | 5 | 有 |
| #038 | bnb-mainnet | 5 | 有 |
| #039 | bnb-mainnet | 5 | 有 |
| #043 | bnb-mainnet | 5 | 有 |
| #044 | bnb-mainnet | 2 | 无 |
| #045 | base-mainnet | 6 | 有 |
| #050 | eth-mainnet | 1 | 无 |
| #051 | base-mainnet | 4 | 无 |
| #060 | bnb-mainnet | 4 | 无 |
| #063 | bnb-mainnet | 5 | 有 |
| #064 | bnb-mainnet | 5 | 有 |
| #065 | bnb-mainnet | 5 | 有 |
| #066 | bnb-mainnet | 5 | 无 |
| #067 | bnb-mainnet | 5 | 有 |
| #068 | bnb-mainnet | 5 | 有 |

## 重要分类和风险

- **#034：** BSC 30 日只有 5 次本人签名 nonce 增长，但 ERC20 事件出账仍有后续分页，部分 token 字符模仿 USDC。这证明 `Transfer.from=wallet` 不能直接当作本人签名的出售，必须检验各 tx 原始 `from` 与成功回执。
- **#044：** 同时出现 canonical WBNB `0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c` 和视觉相近但 CA 不同的 `WB឵N឵B`，金额 raw 可完全相同，不能以符号聚合为同种资产。
- **#045：** Base 真实 USDC `0x833589fcd6edb6e08f4c7c32d4f71b54bda02913` 与多种外观类似 USDC 的其它 CA 混杂；不能将非 canonical CA 转出直接视为 USDC 资金流或盈利兑现。
- **#050：** ETH 链仅检到 1 笔 `external` 支出，指定窗口内相同 API 类别未见入账；这不是负收益证明，期初本金/其它来源未完成。
- **#051：** Base USDC 与 aBasUSDC 存取以及 AERO 转移，与仓库先前 Aave 核查方向相符，不能把借贷存取误算为亏损 Swap。
- **#060：** BSC 同笔 `short` 代币交易对应多条转出日志，不能按多次卖出累计虚构利润。
- **#027/#029/#022：** 已观察到 GENIUSCZ 同一 exact CA 与跨源名单钱包转账关系，仍没有共同控制人和经济利润证据。
- **#065/#066/#067** 可能带有来源文件的“高盈利地址”标签，全部维持 `UNVERIFIED_SOURCE_LABEL`，不因备注就进入钱包盈利排行榜。

真实哈希首项、来源行号、抽样范围、分页状态和 6 个双向样本详见 [机器证据](../evidence/pnl-active-queue-pass-002-20261019.json)。完整原始 provider JSON 尚未归档；信息分类由当前只读来源汇总，后续对盈利指标仍需收据、历史成本、Gas、完整分页及跨链重建。

## 按主线推进

累计已对 **40/237** 个优先活跃候选完成第一轮逐地址可核查的交易发现；**未完成盈利全量审计：0/449**。下一批活跃队列序位 41–60（源行 `69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,86,91,94,101,102`）。优先证明完整买卖及亏损币，复杂高频页和伪装代币入 Deferred，继续处理后续钱包。任何没有原始付费成本或成交回款的余额变化不可产生 ROI。

`OPEN/DRAFT / RESEARCH_ONLY / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE / NO_NEW_AUTOMATION`。
