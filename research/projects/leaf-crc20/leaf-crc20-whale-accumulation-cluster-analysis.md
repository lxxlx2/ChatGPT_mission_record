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

## 社交媒体统计的当前证据状态

待全量复算 claim：

- 149 acquisition transactions: UNRESOLVED
- 120 seller addresses: UNRESOLVED
- 0.605 BTC cost: UNRESOLVED，且需要先明确 cost 口径
- 107,813,367.5647406 old ICO-20 LEAF accumulated/migrated: migration amount CONFIRMED

0.605 BTC 至少存在三种可能口径：
- seller net BTC receipts
- whale net BTC outflow
- seller receipts + protocol/service cost + network fee

因此全量脚本会同时输出这些口径，不强行让结果匹配帖子数字。

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

Final classification 在这些文件回传后更新为：

- independent whale accumulation
- mixed organic sellers + linked cluster
- concentrated organized distribution
- UNRESOLVED

只有共同资金源或其他强链上证据足够时，才会写入项目方关联判断。