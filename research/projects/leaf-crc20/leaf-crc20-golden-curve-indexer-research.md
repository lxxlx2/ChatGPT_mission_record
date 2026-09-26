# Bitcoin L1 CRC-20 LEAF Golden Curve、Indexer 与解锁供应研究

Updated: 2026-09-26
Status: ACTIVE_RESEARCH

## 研究目标

重建 CRC Garden 的 Golden Curve allocation 与 indexer 逻辑，最终得到可用于卖压分析的真实 CRC-20 LEAF unlock supply schedule。

需要回答：

1. Golden Curve 如何把 BTC / ORDI / ICO-20 输入转换成 CRC-20 LEAF allocation。
2. quote 是否来自公开 API、前端本地公式或 indexer endpoint。
3. 每个未 spend 的 2100 / 6767 vault 实际对应多少 CRC-20 LEAF。
4. 当前已经真正解除时间锁并发生首次 transfer 的 CRC-20 LEAF 数量。
5. 未来各成熟高度的精确 CRC-20 LEAF 释放量。

## 官方规则已确认

CRC Garden Terms 明确写明：

- interface、indexer、quote logic 和 transaction templates 属于 experimental software。
- expected LEAF amount 由 Golden Curve 与 current indexed state 计算。
- 最终 allocation 取决于交易有效性、排序、确认、indexer 接受的 Bitcoin chain、protocol rules、available supply 与 chain reorganization。
- indexer 对 confirmed Bitcoin data 的 deterministic interpretation 决定 interface display。

Primary source:
https://crc.garden/legal/terms?lang=en

这意味着界面 quote 不能直接当作永久保留的 allocation，区块排序和 indexer state 会影响最终结果。

## 当前链上锁仓结构

最新本地扫描快照高度：968662。

- 144 blocks: 233 mint，233 matured，170 spent。
- 1000 blocks: 157 mint，118 matured，69 spent。
- 2100 blocks: 179 mint，0 matured。
- 6767 blocks: 289 mint，0 matured。
- unknown: 0。

四档均可通过已确认 Taproot template 重建。

TapScript 结构：

```text
PUSH32 <fixed commitment>
OP_DROP
PUSH <relative block lock>
OP_CHECKSEQUENCEVERIFY
OP_DROP
PUSH32 <owner x-only pubkey>
OP_CHECKSIG
```

已验证 lock ScriptNum：

- 144: `02 9000 b2`
- 1000: `02 e803 b2`
- 2100: `02 3408 b2`
- 6767: `02 6f1a b2`

Internal key 使用已确认 NUMS point：

`50929b74c1a04954b78b4b6035e97a5e078a5a0f28ec96d547bfee9ace803ac0`

## 已实际解除时间锁的 CRC-20 LEAF

239 个已 spend vault 均包含 CRC-20 LEAF transfer。

- 144: 170 笔，首次 transfer 合计约 90,599,002.38095246 LEAF。
- 1000: 69 笔，首次 transfer 合计约 88,963,224.76190474 LEAF。
- 合计约 179,562,227.1428572 LEAF。

该数值代表从已识别时间锁 vault 发生的首次 CRC-20 transfer，总量口径不能直接等同当前自由流通、交易所可卖余额或市场卖出量。

## 已观察到的 ICO-20 迁移换算

在已 spend 且能同时观察 old ICO-20 input 与 CRC-20 transfer 的样本中：

- 144 档 `CRC / old ICO` 比例高度稳定，约 0.77049。
- 1000 档比例高度稳定，约 0.952381。

1000 的经验比例接近 `20/21`，144 的经验比例接近 `47/61`。

当前只把它们记录为 empirical mapping。尚未获得协议源码或 indexer 公式前，不把近似分数写成正式协议公式。

2100 也不能直接套用上述比例。官方 Activity 在 block 967930 展示过：

- old ICO-20 paid: 1,630,000 LEAF
- allocation: 1,456,588.57 CRC-20 LEAF
- lock: 2,100 blocks

对应比例约 0.89361，表明 allocation 还受到 Golden Curve / state 的影响。

Primary source:
https://crc.garden/activity

## 前端 / indexer endpoint 调查状态

已执行公开网页与公开 GitHub 检索：

- crc.garden 官网、Activity、Terms 可以被搜索引擎读取。
- Terms 明确存在 quote/indexer logic。
- 当前公开 GitHub 搜索未定位到 crc.garden 前端源码或可直接引用的 Golden Curve 实现。
- 搜索缓存没有暴露足够的 API route / JS bundle 内容，无法在当前远端环境安全地完成 endpoint 枚举。

因此使用本机只读 probe 完成最后一段：

`leaf_crc20_golden_curve_probe.py`

该 probe 只执行：
- GET crc.garden public pages；
- 下载 same-origin JS bundles；
- 搜索 quote / allocation / indexer / Golden Curve / API 字符串；
- 可选调用本机 Chrome headless 记录被动网络请求；
- 只对安全的 same-origin GET candidate 做探测。

不会连接钱包、签名、POST、广播交易或执行任何写操作。

预期输出：
- `leaf_crc20_golden_curve_probe_report.json`
- `leaf_crc20_golden_curve_relevant_snippets.txt`

## 完成条件

当 endpoint / 前端实现获得后：

1. 确认 Golden Curve 公式和 input asset handling。
2. 用历史已 spend 样本回放，要求重建 allocation 与链上 transfer 一致。
3. 计算 2100 和 6767 每个未 spend vault 的 CRC-20 LEAF allocation。
4. 生成按 block height 聚合的精确 unlock supply。
5. 结合成熟后 spend 延迟，建立潜在短期流通增量区间。

在上述回放通过前，old ICO-20 input 只作为筹码规模 proxy。