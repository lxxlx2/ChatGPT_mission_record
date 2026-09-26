# Bitcoin L1 CRC-20 LEAF 鲸鱼吸筹、迁移与卖方地址集群分析

Updated: 2026-09-26
Status: ACTIVE_RESEARCH

## 目标地址

`bc1pa8vrkzs2wrrh6nsu862vj50vgmsajtju5yv52atlm6xdf0nmaesqrffjrs`

研究目标：

1. 全量复算 ICO-20 LEAF 买入笔数。
2. 精确计算买入 LEAF 总量。
3. 精确计算 unique seller 地址数。
4. 分别计算 seller net BTC receipts 与 whale net BTC outflow。
5. 判断社交媒体所称 149 笔、120 地址、0.605 BTC、107.813M LEAF 是否成立。
6. 追踪卖方用于出售的 UTXO immediate parent transactions。
7. 检查卖方是否存在共同上游资金地址、共同 parent tx 或明显项目基础设施关联。

## 已确认迁移交易

Migration TX:

`0300a053f5a1172e67465fe9c7e68eb5cd3c8b9c5932138cdc7f2023de493f56`

Confirmed block: 967541

链上 OP_RETURN：

```json
{"p":"ico-20","op":"transfer","tick":"LEAF","amt":"107813367.5647406"}
```

同一交易执行：

```json
{"p":"crc-20","op":"mint","tick":"LEAF"}
```

并创建 330 sat Taproot vault：

`bc1pkrns7ra9mwp3t4mq7ukwygkk5jptadtggftal9l5tt3r8j2ertjs5dv976`

该 vault 已通过 Taproot commitment 重建分类为 6767 block lock。

Maturity height:

`967541 + 6767 = 974308`

Mempool:
https://mempool.space/tx/0300a053f5a1172e67465fe9c7e68eb5cd3c8b9c5932138cdc7f2023de493f56

因此 107,813,367.5647406 old ICO-20 LEAF 的迁移提交量属于 CONFIRMED。

最终 CRC-20 allocation 仍需 Golden Curve/indexer 结果，不能把 old input 自动按 1:1 记成 CRC-20 LEAF。

## 更早的 6767 锁

同一个 whale 在 block 967495 已经执行过直接 CRC-20 mint：

`7ced516f66705e6c6a4558b1fb0ff49a8eb972e8f921c6c5e1510d719b5a1772`

该交易同样创建：

`bc1pkrns7ra9mwp3t4mq7ukwygkk5jptadtggftal9l5tt3r8j2ertjs5dv976`

并向固定 pyleaf 地址支付 100,000 sats。

该 mint 同样匹配 6767 block lock。

首笔成熟高度：

`967495 + 6767 = 974262`

所以 whale 的观察窗口至少有两个：

- 974262: 早期直接 CRC mint 可进入 spend 条件。
- 974308: 107.813M old ICO migration 对应 vault 进入 spend 条件。

## 已确认买入交易样本

公开链上已确认多个相同结构样本：

- `edbd7fff9fb46e7f0215dca24b752e38681c359e353f72626f181d2755805fdb`
  - ICO-20 LEAF: 1,290,036.29767881
  - whale 提供 BTC
  - seller 输入 dust UTXO 并收到 BTC
  - whale 收回 change

- `45f640dc0a5b9a243b8936b5df5b7c2bd2514ad25d8b3c3549d2937cfae33bae`
  - ICO-20 LEAF: 680,639.54958551

- `fe56142d63c7837a9af252f475520ee2ff4fe77f97665ea8f5dcd203df903de5`
  - ICO-20 LEAF: 1,410,421

- `94133c63da63c6b8b88bb542e5c604ffd814a57a1ebd619dd178169fe16351d0`
  - ICO-20 LEAF: 348,337

- `5907ed42ae82abec5d9f7f79842da277b2f85c7efbf9076d1fabd815db17f4d3`
  - ICO-20 LEAF: 500,000

这些样本确认存在持续的 BTC 对价 ICO-20 LEAF 归集行为。

## 社交媒体统计的全量复算结果

2026-09-26 本机全量脚本完成 153 笔地址历史扫描，并识别 149 笔 acquisition transaction。

CONFIRMED：

- 149 acquisition transactions。
- 120 unique inferred seller addresses。
- 107,813,367.5647406 old ICO-20 LEAF acquisition sum。
- recurring trade infrastructure address `bc1q54cxdsctws0uxy6lx6uar5agzm07z3a7wu0zt2` 出现在全部 149 笔 acquisition。

BTC 对价按不同口径为：

- seller net BTC receipts: 0.5475904 BTC。
- whale net BTC outflow: 0.57376186 BTC。
- Bitcoin network fee: 0.00173357 BTC。
- whale net outflow - seller receipts - network fee = 0.02443789 BTC，目前只记为 other transaction value flow，尚未完成逐输出归因。

因此社交媒体所称 0.605 BTC 暂时无法按当前三种可复算口径重现，维持 UNRESOLVED。0.605 BTC 比当前复算的 whale net outflow 高 0.03123814 BTC，后续只有在逐笔输出归因能够解释差额时才升级为 CONFIRMED。

## 卖方集群方法

使用 `leaf_crc20_whale_audit.py` 全量读取 whale 地址历史。

Acquisition 定义：

- whale 是交易 input；
- OP_RETURN 包含 ICO-20 LEAF transfer；
- 同一交易存在 non-whale input；
- 排除高频 recurring protocol/coordinator input 后，识别 seller input/output。

对每个 seller 继续读取其出售时使用 UTXO 的 immediate parent tx。

Strong linkage evidence:

1. 多个 seller UTXO 来自同一个 parent transaction。
2. 多个 seller 的 immediate parent tx 由同一个 upstream address 提供 input。
3. 多个 seller 在同一非协议模板交易中共同作为 inputs。

Recurring trade-template address 单独分类。协议模板重复只能证明共同交易基础设施，不能直接证明共同 beneficial owner。

## 本机全量审计输出

脚本：

`leaf_crc20_whale_audit.py`

输出：

- `leaf_crc20_whale_audit_report.json`
- `leaf_crc20_whale_acquisitions.csv`
- `leaf_crc20_whale_sellers.csv`
- `leaf_crc20_whale_clusters.json`

## 全量审计后的集群结论

当前一跳 UTXO funding graph 结果：

- multi-seller clusters: 0。
- strong linkage edges: 0。
- common parent transactions: 0。
- common upstream addresses: 0。
- sellers with direct recurring protocol upstream: 0。

因此当前分类更新为：

**INFERRED: independent whale accumulation**

含义仅限当前可见的一跳链上证据：149 笔买入确实由同一 whale 持续提供 BTC，对手方被识别为 120 个 seller 地址，同时没有发现多个 seller 共用 immediate parent、共同 upstream funder 或直接由 recurring protocol infrastructure funding 的证据。

这不能证明 120 个地址对应 120 个独立实际控制人。当前脚本只做 immediate parent / one-hop upstream linkage，若需要排除更深层地址集群，下一阶段应做 2-3 hop ancestry、地址复用、共同时间窗口和项目方已知地址标签交叉检查。

只有共同资金源或其他强链上证据足够时，才会写入项目方关联判断。

## 已归档机器结果

- `data/whale-audit-2026-09-26-report.json`
- `data/whale-audit-2026-09-26-clusters.json`

详细 acquisitions / sellers CSV 由本机脚本生成，用于本轮统计复核；仓库当前保留汇总和集群机器结果以及可复跑脚本。