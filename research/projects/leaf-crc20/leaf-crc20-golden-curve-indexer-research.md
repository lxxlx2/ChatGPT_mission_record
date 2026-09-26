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

## Golden Curve 前端与 API 探测结果

2026-09-26 本机 probe 已完成 19 个 same-origin asset 抓取，并从静态 bundle 中确认以下规则。

### CONFIRMED：公开描述的 Golden Curve

英文前端文案直接给出：

- marginal price: `P = m × S^1.618`
- single allocation 的 exact cost 为该 tranche 上的积分
- total supply: `1,000,000,000 LEAF`
- mint window: 从 deployment block 起 `9,666` blocks，结束后剩余 supply burn
- asset equivalence: `1 BTC = 7,000 points`，`1 ORDI = 1 point`
- 因此官方示例 `0.01 BTC = 70 ORDI`，两者在同一 indexed state 下得到相同 expected LEAF allocation

由公开边际价格公式可直接数学推导，若 allocation 从 supply `S0` 到 `S1`，则 points cost 为：

```text
C = ∫[S0,S1] m * S^1.618 dS
  = m / 2.618 * (S1^2.618 - S0^2.618)
```

该积分表达式属于 DERIVED，不把 `m` 的数值或 `S` 的内部单位当作已确认。

### CONFIRMED：production mint config

公开 `GET /api/mint/config` 返回：

- `backend_mode = production`
- `network = mainnet`
- `protocol = crc-20`
- `ticker = LEAF`
- `builder_assets = [BTC, ORDI, LEAF]`
- `lock_options = [144, 1000, 2100, 6767]`
- `lock_allocation_bps = 10000`
- `tusm_fee_sats = 10000`
- treasury / TUSM treasury:
  `bc1phuuulh7fs5zrm48ethfyqvt860fxsaxuq643telqn06yz4u3c70spyleaf`

`builder_assets` 明确包含 `LEAF`。Activity 前端把 `payment_asset == LEAF` 显示为 `legacy LEAF`，因此 old LEAF 确实属于 mint input 类型之一。

当前证据没有给出 legacy LEAF 到 Golden Curve points 的精确换算规则。

### CONFIRMED：quote 与 state endpoint

前端 bundle 暴露：

- `GET /api/mint/state`
- `GET /api/mint/state?address=<address>`
- `GET /api/mint/wallet-assets?paymentAddress=...&ordinalAddress=...`
- `POST /api/mint/quote-budget`

`quoteMintBudget` 明确把请求对象 JSON serialize 后 POST 到 `/api/mint/quote-budget`。

早期 probe 对 quote-budget 使用 GET，所以得到 404。这个 404 不能解释为 endpoint 不存在。

### CONFIRMED：Activity 数据模型

Activity 前端对每个 mint event 读取：

- `mint.payment_asset`
- `mint.payment_amount_atoms`
- `mint.csv_blocks`
- event `amount_atoms` 作为 CRC-20 LEAF allocation

其中：
- BTC / LEAF payment amount 以 1e8 为显示 divisor
- ORDI payment amount 以 1e18 为显示 divisor
- `payment_asset == LEAF` 显示为 `legacy LEAF`

因此只要取得完整 812 个 mint event 的顺序数据，就具备重建 `input asset -> payment -> indexed supply -> allocation -> lock` 历史序列的字段基础。

### Probe 限制

Chrome headless passive network 两次均在 45 秒 timeout，因此本轮没有从 Chrome netlog 得到额外 URL。

该限制没有影响静态 bundle 结论。19 个网页 asset 已成功下载，公开 config、oracle 与 bundle 中的 API wrapper 均已获取。

### 当前仍然 UNRESOLVED

1. Golden Curve coefficient `m` 的精确数值。
2. supply `S` 在后端公式中的原子单位 / normalization。
3. `POST /api/mint/quote-budget` 的完整 request schema 与 response schema。
4. legacy LEAF 对 Golden Curve points 的换算规则。
5. 144 / 1000 / 2100 / 6767 是否只影响 unlock timing，还是会进入 allocation pricing；`lock_allocation_bps=10000` 本身不足以证明存在 lock multiplier。
6. 107,813,367.5647406 old ICO-20 LEAF migration 最终对应多少 CRC-20 LEAF。
7. 全部 2100 / 6767 vault 的精确未来 unlock allocation。

下一步优先读取 `/api/mint/state` 及 address-scoped state，并从本机 raw JS bundle 恢复 quote request object 的字段构造，再用 quote endpoint 的只读报价行为和历史 mint events 回放 Golden Curve。

## 完成条件

当 endpoint / 前端实现获得后：

1. 确认 Golden Curve 公式和 input asset handling。
2. 用历史已 spend 样本回放，要求重建 allocation 与链上 transfer 一致。
3. 计算 2100 和 6767 每个未 spend vault 的 CRC-20 LEAF allocation。
4. 生成按 block height 聚合的精确 unlock supply。
5. 结合成熟后 spend 延迟，建立潜在短期流通增量区间。

在上述回放通过前，old ICO-20 input 只作为筹码规模 proxy。