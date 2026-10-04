# FRANK HFT STICKY vs ROLLING HISTORICAL_REPLAY — 2026-10-04

结论：**NEED_MORE_DATA**。sticky 60 秒 HFT 确实挡住 4 个本可满足 V1 其余条件的 observed episode，涉及 3 个 mint，其中 PAID 占 2 个。新增样本中 3 个在后续出现 inventory unresolved，另 1 个具有明显的混合 BUY/SELL turnover；当前无法证明 rolling 不扩大噪声。这个结论不否认机械漏报，而是区分信号差异与经济质量。

所有实验在全新 private historical SQLite 中进行。生产规则保持 sticky；没有重启、网络查询、通知、Gmail send、live DB 写入或 automation。PRODUCTION_TRADING = NO_GO。

## Authority 与冻结研究口径

Starting HEAD: `e38221ddedbfa467dded151f8215589e8128c5bb`; branch: `codex/frank-only-local-signals`; starting worktree clean。开始执行了 git fetch，未 reset、未 merge main。生产 daemon 仍加载 `46c989c3ef35d63fc02808c519f73aa3e6ea1513`。

CURRENT 复用原 Engine，ROLLING subclass 仅在原 `_evaluate` 执行前改变 `hft`。原 ACTIVE_TRADE/每小时 :29 时钟、episode reset、T0、accumulation、inventory、distribution、freshness、金额与其他 gates 不变。HFT 改变后原 `watch_eligible` 的结果也会随之改变，这是同一 HFT 变量的因果后果，不能冻结旧 WATCH 来阻断它。所有 variants 的 events、库存点、current/peak、state、T0、accumulation flag 一致；ACCUMULATION identity/time 集合一致。

R0：在 evaluation 时点的闭区间 `[at−60, at]` 中 count ≥3 才失败；计整数秒，窗口最后失败秒为 end，end+1 首次 PASS。R5/R15：从 end+1 起连续 300/900 秒无新 HFT 后恢复，出现新窗口则延后。只在原生产时钟 evaluation，不增加恢复 tick，因此 gate 恢复时间不等于信号发出时间。三个版本在看到 replay 结果前固定，无阈值调优。

完整快速 round trip 保持原逻辑：episode 内已证明 current inventory 恰好归零且距首 BUY ≤1200 秒，则该独立标志一直保留到 episode reset。没有改成部分退出或改变约 20 分钟 reference。后续 SELL 即使追加到 CLOSED episode，也不清除这个原始 veto。

USDC quote 直接数值比较；其他 quote 无可信历史换算时金额 gate UNDETERMINED，没有新增 SOL/USD 换算。

## 最小 isolated regression

6 笔 BUY 时间依次为 100000、100020、100060、100200、102800、103000，每笔 13000 USDC、100 raw token。前三笔恰好在 60 秒内，后续跨度 3000 秒，库存保留、无 SELL/distribution。CURRENT 最后 hft=True，MULTIPLE hft gate FAIL，其余 MULTIPLE gates 全 PASS；没有 MULTIPLE。R0/R5/R15 均恢复并生成隔离 shadow MULTIPLE。`HFT_STICKY_BEHAVIOR_CONFIRMED = YES`。

CURRENT subclass 与原 Engine 最小 regression 的 state、signals、完整 evaluation rows 逐项相同。全历史 CURRENT 与此前 verified V1 的 31 signal rows、1095 evaluation rows、153 final mint states 也逐项完全相同。

## 历史数据与边界

使用现有 verified durable `history-shadow-ledger-verified.sqlite`，对全部 raw 重新验证 SHA-256、raw signature binding、classifier classification/trade/clock/signer 一致性。可见的更新历史 ledger 未超过此覆盖；没有拼接 forward live 数据。

- UTC start: 2026-09-03T16:32:58+00:00
- UTC end: 2026-09-30T09:39:20+00:00
- usable signatures: 6874; ACTIVE_TRADE: 634; active tokens: 203; reconstructed episodes: 180
- raw missing: 0；642 UNKNOWN_NEEDS_REVIEW、900 FAILED_TX、4433 PASSIVE_TRANSFER、265 ATA_CREATE 不当作 ACTIVE_TRADE。
- 203 active tokens 中只有 153 个最终 state、180 个已知 BUY 起点 episode；没有可见起点的 SELL 不制造 episode。
- 原拟议 30D window 的更早范围未在该可用子集中，未知交易也未被补猜。raw missing=0 仅指已纳入的 6874 条，不代表完整 30D、更不代表 wallet lifetime。
- HFT 每个已分类 signature 至多一个 user-level active trade，不计 DEX CPI hop。wallet/signature duplicate=0，ACTIVE_TRADE raw-hash duplicate=0。未发现这一口径的重复输入；无法仅从 distinct signatures 判断人物意图。
- Chronology SHA256: `7dd4cb90f0dc3bcd3d527421742fa45b55ac1807967deb4f81f7ee30b20f6ed3`

## 总量与分类

| 指标 | 数值 |
|---|---:|
| episodes_total | 180 |
| episodes_hft_ever（含独立 rapid roundtrip） | 31 |
| 60 秒 burst sticky episodes | 9 |
| 60 秒 sticky ratio | 5.00% |
| rapid roundtrip episodes（与 burst 有重叠） | 23 |
| MULTIPLE CURRENT | 10 |
| MULTIPLE R0 | 14 |
| new MULTIPLE | 4 |
| new / all episodes | 2.22% |
| new / current MULTIPLE | 40.00% |
| current MULTIPLE lost under rolling | 0 |
| ACCUMULATION A / B | 21 / 21 |

31 个 ever-HFT = 9 burst + 23 rapid −1 overlap。研究的唯一变量是其中 9 个 burst 的 sticky 状态，不将全部 31 个都称为 rolling 60 秒误伤。

分类按首次实际 emission：新增 R0 MULTIPLE 优先归 B；A/B 都无 MULTIPLE、且存在其他核心 gates 全 PASS 的 HFT-only blocked evaluation 才归 C；其余首次结果/时间相同归 A，否则 D。这避免把因金额/库存等原因双边不通过的 episode 全归咎于 HFT。

| Category | Episodes |
|---|---:|
| SAME_RESULT | 176 |
| STICKY_BLOCKED_ROLLING_MULTIPLE | 4 |
| BOTH_HFT_BLOCKED | 0 |
| OTHER_DIFFERENCE | 0 |

## Recovery sensitivity

| Variant | Total MULTIPLE | New MULTIPLE | Lost current | 新增首次触发相对 R0 |
|---|---:|---:|---:|---|
| R0 | 14 | 4 | 0 | 四个均 0 秒 |
| R5 | 14 | 4 | 0 | 四个均 0 秒 |
| R15 | 14 | 4 | 0 | 四个均 0 秒 |

四个首次触发距最近 HFT 窗口失效分别已超过 15 分钟。当前样本无法区分 R0/R5/R15，也不能据此认定即刻恢复总是安全。

## Sticky burst 后续行为（分母 9 episodes）

| 行为 | Episodes |
|---|---:|
| 首次 HFT 后 (0,60m] 有 BUY | 6 |
| 首次 HFT 后 >60m 有 BUY | 4 |
| 首次 HFT 后 >45m 有 BUY | 4 |
| HFT 后某个可判定点 inventory ≥当时 causal peak 的50% | 6 |
| 最终 inventory ≥episode peak 的50% | 0 |
| HFT 后曾出现 >35% observed peak drop | 7 |
| HFT 后 evaluation 曾触发原 rolling unrecovered distribution veto | 7 |
| 最终 CLOSED | 4 |
| 最终 inventory unresolved | 5 |

“曾保留库存”与“最终库存”分开；distribution peak drop 与原 60m 未恢复 veto 分开。终态 5 个 unresolved 不当作归零，也不当作长期持仓。

## 四个新增 MULTIPLE 逐一审计

按后续 BUY 数、buy span、USDC 的降序 lexicographic 行为顺序展示；机器结果另外保存每个维度的独立排名。原始 quote 的金额不声明独立核验美元价值。

### 1. 98kfF7rmsg1QDUEoCqNE7g7M1FdrTt92TEp2CLzypump

episode_id: `e8023ff4c14194e30ad8757c0a0b96ae376c17d8bdf4978c7acd5511604e55b3`

- 首 BUY / 最后 trade UTC：2026-09-26T19:46:39+00:00 / 2026-09-26T23:16:44+00:00
- 首次 HFT：2026-09-26T19:49:10+00:00，当时闭区间 60 秒内 3 个 active signatures，构成 {"BUY": 3}。前三笔实际 span 10 秒。
- 首窗口首次 PASS：2026-09-26T19:50:04+00:00；其后首次低频 BUY：2026-09-26T20:08:51+00:00，距该 expiry 1127 秒。这是首个不处于 burst 窗口的 BUY，不声称永久无后续 burst。
- 整个 episode：BUY 15 / SELL 4；BUY span 5082 秒；known USDC 403839.428676。
- 首 HFT 后完整可见后续：BUY 11；首后续 BUY 到末 BUY span 4928 秒；首 HFT 到末 BUY elapsed 4931 秒。
- 截至首次 shadow signal：BUY 14 / SELL 0；首 HFT 后 BUY 10；累计 USDC 377159.576006；HFT 后 BUY USDC 247159.576007。
- signal 时库存 raw 8952033850447，causal peak 8952033850447，retention 1；distribution gate PASS。只使用触发前库存，完整 lifetime UNKNOWN。
- 后续 distribution veto evaluations 2；曾 >35% peak drop True；最终 INVENTORY_UNDETERMINED，inventory raw None，最终 retention None。后续信息不影响信号。
- rolling 首触发 UTC：2026-09-26T21:11:15+00:00；kind ACTIVE_TRADE；距最近 burst expiry 4871 秒。
- triggering signature：`3oehA7BeKEnapTG4BLwD87zd4wvhvZ8xW3fqKP8ZcZygjBFnRX9oTB1Bx4Vdntt6DG3dBHsNcysoxHEQh7ADxBU4`。hourly 触发时该 signature 是 Engine 记录的最新 ACTIVE_TRADE，不把它伪装为该小时新交易。
- CURRENT MULTIPLE = 无；R0/R5/R15 = 有、首次时间一致。CURRENT HFT-only blocked evaluations: 4。
- 行为判断：A_SPLIT_ACCUMULATION_LIKE。Behavioral resemblance only; user intent and actual arbitrage profitability unproven. Separate signed transactions 不支持把 Jupiter CPI hops 算作多笔；B 路由意图或 C 真正套利未获可判定证据。
- PnL：PNL_UNAVAILABLE。

首 HFT prefix：

| UTC | Signature | Direction | Original quote quantity |
|---|---|---|---|
| 2026-09-26T19:49:00+00:00 | `5kGhFA17fVH4xDqrrFuJkphxLynPRFvRNrYidoEuW1GT11v2BQsDLPkHgUEWq8EMi3ebfQ2qcQgDE2edhC41YjS4` | BUY | 35000 USDC |
| 2026-09-26T19:49:03+00:00 | `3GuqjHtrbfRCooDBWRYoXtFw4Tx2rZqqxNpRFgpjr1raVQejzZQrXx75xE5hxDY7L7UqD5tDCXXFmNM43SctWqsM` | BUY | 35000 USDC |
| 2026-09-26T19:49:10+00:00 | `3ehiwTepivtTbFPMywu1tuBBzCf2dxmstkVaSriRjxKYXcqgBriN8dyDfM3MMBwNqBVgKYcaJk6e1eoNa8VKqCYV` | BUY | 35000 USDC |

rolling fail windows（UTC，end 为最后失败秒）：

- 2026-09-26T19:49:10+00:00 → 2026-09-26T19:50:03+00:00; first PASS 2026-09-26T19:50:04+00:00
- 2026-09-26T23:16:36+00:00 → 2026-09-26T23:17:32+00:00; first PASS 2026-09-26T23:17:33+00:00

首次 MULTIPLE reason codes：

- `ACCUMULATION_BEHAVIOR_STAGE_ESTABLISHED`
- `MEANINGFUL_ACCUMULATION_T0_ESTABLISHED`
- `EPISODE_USDC_QUOTE_GE_10000`
- `PERSISTENCE_PATH_B_GE_3_BUYS_SPAN_GE_45M`
- `OBSERVED_INVENTORY_RETAINED_OR_RESUMED_NET_BUYING`
- `NO_UNRECOVERED_35PCT_ROLLING_DISTRIBUTION`
- `NO_CONFIRMED_HFT_EXECUTION`
- `FRESHNESS_BEHAVIOR_PASSED`
- `NON_BEHAVIOR_VETO_GATES_REMOVED_BY_USER_REQUIREMENT`

### 2. CbcyNo7m1amFWqEQm2m4PLv1UNvpcL3C1Ujm6AkzpKoU

episode_id: `2a3367bd6f19bc12537367583b170847f736887ca80c4e3b8467477b1c2dd192`

- 首 BUY / 最后 trade UTC：2026-09-26T19:46:52+00:00 / 2026-09-26T23:14:29+00:00
- 首次 HFT：2026-09-26T19:46:58+00:00，当时闭区间 60 秒内 3 个 active signatures，构成 {"BUY": 3}。前三笔实际 span 6 秒。
- 首窗口首次 PASS：2026-09-26T19:47:53+00:00；其后首次低频 BUY：2026-09-26T19:57:16+00:00，距该 expiry 563 秒。这是首个不处于 burst 窗口的 BUY，不声称永久无后续 burst。
- 整个 episode：BUY 12 / SELL 3；BUY span 5088 秒；known USDC 179748.597338。
- 首 HFT 后完整可见后续：BUY 9；首后续 BUY 到末 BUY span 4464 秒；首 HFT 到末 BUY elapsed 5082 秒。
- 截至首次 shadow signal：BUY 11 / SELL 0；首 HFT 后 BUY 8；累计 USDC 171744.578847；HFT 后 BUY USDC 96744.578847。
- signal 时库存 raw 9395895868811，causal peak 9395895868811，retention 1；distribution gate PASS。只使用触发前库存，完整 lifetime UNKNOWN。
- 后续 distribution veto evaluations 1；曾 >35% peak drop True；最终 INVENTORY_UNDETERMINED，inventory raw None，最终 retention None。后续信息不影响信号。
- rolling 首触发 UTC：2026-09-26T20:36:34+00:00；kind ACTIVE_TRADE；距最近 burst expiry 2921 秒。
- triggering signature：`2j2ykhDVKXx8aJkP92Ez98VZJn44HB7GsagdzGGrWFZvNkVeu7W1g7bTtkCCTj7vESnBoHgXENZ2H94tCiHg4b3V`。hourly 触发时该 signature 是 Engine 记录的最新 ACTIVE_TRADE，不把它伪装为该小时新交易。
- CURRENT MULTIPLE = 无；R0/R5/R15 = 有、首次时间一致。CURRENT HFT-only blocked evaluations: 4。
- 行为判断：A_SPLIT_ACCUMULATION_LIKE。Behavioral resemblance only; user intent and actual arbitrage profitability unproven. Separate signed transactions 不支持把 Jupiter CPI hops 算作多笔；B 路由意图或 C 真正套利未获可判定证据。
- PnL：PNL_UNAVAILABLE。

首 HFT prefix：

| UTC | Signature | Direction | Original quote quantity |
|---|---|---|---|
| 2026-09-26T19:46:52+00:00 | `44uowgKU1ZVDfUGu243Pc1PtV1uiF8awgRomSFGGWY6x7oHD1Z67V98qGYvdQJRn6M4r97fZdnqmNbXZtzp4wnXf` | BUY | 25000 USDC |
| 2026-09-26T19:46:55+00:00 | `5xbyj3A2Gfgvk4DhJgRAWoxmUrrneySFn2sAGtEfY3MMnuvF6MKcGBn4oFqyV7yikjhiYFU6Z9BPYryQert24dft` | BUY | 25000 USDC |
| 2026-09-26T19:46:58+00:00 | `4KodHwjh6fT9BM3uSiG3gz9jLzWiQHnrMBNv1HHGEJ5gASQShdKhQD4Zxe6SyiN5ouroUrF8gWrtSvyB9w5QYmGi` | BUY | 25000 USDC |

rolling fail windows（UTC，end 为最后失败秒）：

- 2026-09-26T19:46:58+00:00 → 2026-09-26T19:47:52+00:00; first PASS 2026-09-26T19:47:53+00:00
- 2026-09-26T23:14:29+00:00 → 2026-09-26T23:15:16+00:00; first PASS 2026-09-26T23:15:17+00:00

首次 MULTIPLE reason codes：

- `ACCUMULATION_BEHAVIOR_STAGE_ESTABLISHED`
- `MEANINGFUL_ACCUMULATION_T0_ESTABLISHED`
- `EPISODE_USDC_QUOTE_GE_10000`
- `PERSISTENCE_PATH_B_GE_3_BUYS_SPAN_GE_45M`
- `OBSERVED_INVENTORY_RETAINED_OR_RESUMED_NET_BUYING`
- `NO_UNRECOVERED_35PCT_ROLLING_DISTRIBUTION`
- `NO_CONFIRMED_HFT_EXECUTION`
- `FRESHNESS_BEHAVIOR_PASSED`
- `NON_BEHAVIOR_VETO_GATES_REMOVED_BY_USER_REQUIREMENT`

### 3. 98kfF7rmsg1QDUEoCqNE7g7M1FdrTt92TEp2CLzypump

episode_id: `0fc2c485fe94776708fe3fa98597d675874a0e09f781031bed58d50f9f6e9098`

- 首 BUY / 最后 trade UTC：2026-09-26T00:04:03+00:00 / 2026-09-26T19:29:39+00:00
- 首次 HFT：2026-09-26T00:04:15+00:00，当时闭区间 60 秒内 3 个 active signatures，构成 {"BUY": 3}。前三笔实际 span 12 秒。
- 首窗口首次 PASS：2026-09-26T00:05:04+00:00；其后首次低频 BUY：2026-09-26T00:11:17+00:00，距该 expiry 373 秒。这是首个不处于 burst 窗口的 BUY，不声称永久无后续 burst。
- 整个 episode：BUY 9 / SELL 5；BUY span 11893 秒；known USDC 223995.584839。
- 首 HFT 后完整可见后续：BUY 6；首后续 BUY 到末 BUY span 11459 秒；首 HFT 到末 BUY elapsed 11881 秒。
- 截至首次 shadow signal：BUY 7 / SELL 0；首 HFT 后 BUY 4；累计 USDC 173995.584840；HFT 后 BUY USDC 98995.584840。
- signal 时库存 raw 10257336381862，causal peak 10257336381862，retention 1；distribution gate PASS。只使用触发前库存，完整 lifetime UNKNOWN。
- 后续 distribution veto evaluations 4；曾 >35% peak drop True；最终 INVENTORY_UNDETERMINED，inventory raw None，最终 retention None。后续信息不影响信号。
- rolling 首触发 UTC：2026-09-26T01:29:00+00:00；kind HOURLY_29；距最近 burst expiry 5036 秒。
- triggering signature：`5zgcxbH2MAWXrr5Kf4dHce6R8J95bqwFPKBH3pgALFhZPoZi7frZdsLuaRFoNgDdVCKQmLN2P43uSH2BV2p5NARi`。hourly 触发时该 signature 是 Engine 记录的最新 ACTIVE_TRADE，不把它伪装为该小时新交易。
- CURRENT MULTIPLE = 无；R0/R5/R15 = 有、首次时间一致。CURRENT HFT-only blocked evaluations: 4。
- 行为判断：A_SPLIT_ACCUMULATION_LIKE。Behavioral resemblance only; user intent and actual arbitrage profitability unproven. Separate signed transactions 不支持把 Jupiter CPI hops 算作多笔；B 路由意图或 C 真正套利未获可判定证据。
- PnL：PNL_UNAVAILABLE。

首 HFT prefix：

| UTC | Signature | Direction | Original quote quantity |
|---|---|---|---|
| 2026-09-26T00:04:03+00:00 | `62jaXrKGvbc2s3Hsmc4WWEVzQhyr62btaaPxHVMHUuT5ew9q6NZRQcwPhsrzBVbzXaTQDW5ZQRuDWsdoquzYAD79` | BUY | 25000 USDC |
| 2026-09-26T00:04:07+00:00 | `3jwqwNe1fmyZ8zb3Gm3jwPSptPEk8Z8mHq1wQmAMJjwYCeSCwYvnwLC6jqQMY3gxDoRwWuKJNxJGCannnVeKbkyx` | BUY | 25000 USDC |
| 2026-09-26T00:04:15+00:00 | `3fNZXQ73hqyy9JVAC9U5Jd7kpzzAnzQn8ktwUsYYbgAtRg1J8JVL5WTzPaa6wvgmNRe6ANw7iqRE4gBpbLj48LmV` | BUY | 25000 USDC |

rolling fail windows（UTC，end 为最后失败秒）：

- 2026-09-26T00:04:15+00:00 → 2026-09-26T00:05:03+00:00; first PASS 2026-09-26T00:05:04+00:00
- 2026-09-26T19:28:35+00:00 → 2026-09-26T19:29:21+00:00; first PASS 2026-09-26T19:29:22+00:00
- 2026-09-26T19:29:26+00:00 → 2026-09-26T19:29:28+00:00; first PASS 2026-09-26T19:29:29+00:00

首次 MULTIPLE reason codes：

- `ACCUMULATION_BEHAVIOR_STAGE_ESTABLISHED`
- `MEANINGFUL_ACCUMULATION_T0_ESTABLISHED`
- `EPISODE_USDC_QUOTE_GE_10000`
- `PERSISTENCE_PATH_A_PRIOR_HOURLY_WATCH`
- `OBSERVED_INVENTORY_RETAINED_OR_RESUMED_NET_BUYING`
- `NO_UNRECOVERED_35PCT_ROLLING_DISTRIBUTION`
- `NO_CONFIRMED_HFT_EXECUTION`
- `FRESHNESS_BEHAVIOR_PASSED`
- `NON_BEHAVIOR_VETO_GATES_REMOVED_BY_USER_REQUIREMENT`

### 4. UpBBfyC75u3kxDGWmmmW2yauk9YY3CqZhdt1KUDkids

episode_id: `3a666709f0f1edca33435d4e4c1e483473866332c01a779e849de4d3508014a8`

- 首 BUY / 最后 trade UTC：2026-09-24T02:10:11+00:00 / 2026-09-26T23:22:05+00:00
- 首次 HFT：2026-09-24T02:10:52+00:00，当时闭区间 60 秒内 3 个 active signatures，构成 {"BUY": 1, "SELL": 2}。前三笔实际 span 41 秒。
- 首窗口首次 PASS：2026-09-24T02:11:59+00:00；其后首次低频 BUY：2026-09-24T02:27:40+00:00，距该 expiry 941 秒。这是首个不处于 burst 窗口的 BUY，不声称永久无后续 burst。
- 整个 episode：BUY 3 / SELL 50；BUY span 5826 秒；known USDC 50000。
- 首 HFT 后完整可见后续：BUY 2；首后续 BUY 到末 BUY span 4777 秒；首 HFT 到末 BUY elapsed 5785 秒。
- 截至首次 shadow signal：BUY 3 / SELL 9；首 HFT 后 BUY 2；累计 USDC 50000；HFT 后 BUY USDC 30000。
- signal 时库存 raw 17622741379433，causal peak 17622741379433，retention 1；distribution gate PASS。只使用触发前库存，完整 lifetime UNKNOWN。
- 后续 distribution veto evaluations 5；曾 >35% peak drop True；最终 CLOSED，inventory raw 0，最终 retention 0。后续信息不影响信号。
- rolling 首触发 UTC：2026-09-24T03:47:17+00:00；kind ACTIVE_TRADE；距最近 burst expiry 5718 秒。
- triggering signature：`28yaTKozi1gfKNMFYEa7NQrgcZxuVwiaQTEjamaRZbvn3reZSwx1xYj1NE9nLAqjy4rdCA1yvjYCmnhjhHXfg5FE`。hourly 触发时该 signature 是 Engine 记录的最新 ACTIVE_TRADE，不把它伪装为该小时新交易。
- CURRENT MULTIPLE = 无；R0/R5/R15 = 有、首次时间一致。CURRENT HFT-only blocked evaluations: 2。
- 行为判断：D_UNDETERMINED_MIXED_HIGH_TURNOVER。Behavioral resemblance only; user intent and actual arbitrage profitability unproven. Separate signed transactions 不支持把 Jupiter CPI hops 算作多笔；B 路由意图或 C 真正套利未获可判定证据。
- PnL：PNL_UNAVAILABLE。

首 HFT prefix：

| UTC | Signature | Direction | Original quote quantity |
|---|---|---|---|
| 2026-09-24T02:10:11+00:00 | `2NFJgJDWVf3EdiMUqXdBEc3YSoKHUQcCoT51bxdiANsbSRZRwmrtYzEgzkhagvoU3habjQ9XfP9avhWPYZP5B7Eq` | BUY | 20000 USDC |
| 2026-09-24T02:10:48+00:00 | `2b1s5Sias2tyuLDncBWcybeUAPYr8sjv2rLLeMcYKWy6a1qgkmz5uMffobGA39a1eVR14V4XNobEgrousNHmHvPT` | SELL | 4.599695 USDC |
| 2026-09-24T02:10:52+00:00 | `4jwbE83Hnmu9kTVtKw2f5qD6ijzkCtvF7pFmxZW3r9YqxVBZ12tgCRHkpAJAWX33yNCYTBNu8xQYKZmi7rAMCgfN` | SELL | 4.708729 USDC |

rolling fail windows（UTC，end 为最后失败秒）：

- 2026-09-24T02:10:52+00:00 → 2026-09-24T02:11:58+00:00; first PASS 2026-09-24T02:11:59+00:00

首次 MULTIPLE reason codes：

- `ACCUMULATION_BEHAVIOR_STAGE_ESTABLISHED`
- `MEANINGFUL_ACCUMULATION_T0_ESTABLISHED`
- `EPISODE_USDC_QUOTE_GE_10000`
- `PERSISTENCE_PATH_B_GE_3_BUYS_SPAN_GE_45M`
- `OBSERVED_INVENTORY_RETAINED_OR_RESUMED_NET_BUYING`
- `NO_UNRECOVERED_35PCT_ROLLING_DISTRIBUTION`
- `NO_CONFIRMED_HFT_EXECUTION`
- `FRESHNESS_BEHAVIOR_PASSED`
- `NON_BEHAVIOR_VETO_GATES_REMOVED_BY_USER_REQUIREMENT`

## 已知 winner sanity checks

| Name | 绑定/历史 | 60s HFT episodes | Current MULTIPLE | Rolling MULTIPLE | Sticky blocked 新增 |
|---|---|---:|---:|---:|---:|
| STONK | PRESENT; 2 episodes | 1 | 1 | 1 | 0 |
| PAID | PRESENT; 5 episodes | 4 | 1 | 3 | 2 |
| Pistacio | UNRESOLVED_NAME_TO_MINT | UNDETERMINED | UNDETERMINED | UNDETERMINED | UNDETERMINED |
| PERPSPAD | UNRESOLVED_NAME_TO_MINT | UNDETERMINED | UNDETERMINED | UNDETERMINED | UNDETERMINED |
| fone | UNRESOLVED_NAME_TO_MINT | UNDETERMINED | UNDETERMINED | UNDETERMINED | UNDETERMINED |
| Pumpcat | UNRESOLVED_NAME_TO_MINT | UNDETERMINED | UNDETERMINED | UNDETERMINED | UNDETERMINED |
| CATE | UNRESOLVED_NAME_TO_MINT | UNDETERMINED | UNDETERMINED | UNDETERMINED | UNDETERMINED |

STONK 有两个 observed episodes：正式 MULTIPLE episode 在 2026-09-06T04:18:35+00:00 已触发，直到 2026-09-09T21:24:55+00:00 的后段 SELL burst 才出现 HFT。它确实曾 HFT=true，但没有阻止此前 MULTIPLE；A/R0 首次 signal 完全相同。不能把“ever HFT”误当作“被 sticky 漏报”。

PAID exact mint 的 5 个 episode 中 4 个出现 60 秒 HFT，CURRENT 有 1 个 MULTIPLE，R0 有 3 个（新增两个详见上文）。其他三个 episode 的结果保持不变。PAID 与 STONK mint 使用仓库既有 `research/frank-30d-replay-state.md` 锚点，再确认存在于 raw-verified ACTIVE_TRADE dataset。

Pistacio / PERPSPAD / fone / Pumpcat / CATE 在既有报告中只有名称/聚合描述，当前 bounded 本地来源未找到可核验 name→mint 绑定；不宣称它们不在 dataset，不猜 mint、不制造交易。这里是 winner attribution 数据缺口。

## 行为强度与事后经济重要性

四个新增的逐维度独立排序保存在 JSON `behavior_rankings`，使用后续 BUY 数、整个 BUY span、已知 USDC 和最终 retention；最终 unresolved 值在排名末尾，明确保留 missing，不转换为真实零库存。若末值相同，原 chronological order 稳定排序。

经济排名：**PNL_UNAVAILABLE**。已有文档中的公共聚合 PnL、不同窗口或 token 总盈亏，不能可靠分配到本次 observed episode。没有完整 cost basis、剩余库存经济估值、历史转换与每个 episode 的已核验收益证据，所以不编造 per-episode PnL、不按后来价格排序。所有 signal 都先依原 chronology 生成，之后才附加行为/赢家描述。

## 判断与下一步所需证据

保留 NEED_MORE_DATA：3 个 BUY burst 后继续建仓的新增 episode 具有明确持续建仓行为（两 PAID + 一个未命名 mint），但第四个混合 turnover episode 同样被放行。R5/R15 没有过滤该混合样本；样本数小，不能证明延迟恢复解决噪声。3/4 新增最终 unresolved、缺可靠逐 episode PnL，使 “没有明显扩大垃圾信号” 尚未成立。

若研究继续，需要补齐 observed inventory 的不可判定 SELL/raw-routing 缺口、完整窗口覆盖、winner mint provenance，以及与 episode 可审计关联的事后经济结果。此轮没有补抓、没有修 parser、没有为结果改阈值；也没有提出可直接上线的 V2。

## 交付、验证与生产隔离

研究 helper：`local-agent/scripts/frank_hft_sticky_rolling_historical_replay.py`。post-replay audit/report helper：`local-agent/scripts/frank_hft_historical_replay_report.py`。isolated regression：`local-agent/tests/research/test_frank_hft_sticky_rolling_historical_replay.py`。逐 episode 全 chronology/窗口/信号/reason codes/排名：`meme/evidence/frank-hft-sticky-vs-rolling-2026-10-04.json`。SQLite 与 runtime isolation snapshot 只保留 private evidence。

CURRENT/ROLLING helper 只能创建新 historical workspace，拒绝已有 workspace、live 命名和 forward.sqlite source。所有 generated outbox 为 DRY_RUN_AUDIT，未调用 delivery adapter。

生产源码/config SHA-256 均与研究前相同；daemon PID/restart_count 不变、loaded source commit 不变、source_drift=false。仅只读现有 health 文件证明隔离，没有进行 live validation。最终 Git commit/push 仅包括 research helpers、historical regression、report、evidence；不 merge main。

PRODUCTION FILES CHANGED = NO; POLICY CHANGED = NO; LIVE SERVICE RESTARTED = NO; LIVE/HISTORICAL SIGNAL SENT BY RESEARCH = NO; PRODUCTION_TRADING = NO_GO.

## 实际验证与复现

研究 regression：10 passed、0 failed、0 skipped。完整 local-agent suite：557 passed、0 failed、3 skipped（numpy 缺失的无关 Monster 测试）。历史完整 CURRENT parity：31 signals / 1095 evaluations / 153 mint states，全字段相同。四个 variants 均通过隔离 outbox DRY_RUN_AUDIT 与 SQLite integrity 检查。

运行命令来自 Frank-only local-agent cwd：

```sh
python -m pytest -q
python -m pytest -q tests/research/test_frank_hft_sticky_rolling_historical_replay.py
python -m scripts.frank_hft_sticky_rolling_historical_replay \
  --source "$PRIVATE_EVIDENCE/history-shadow-ledger-verified.sqlite" \
  --work "$PRIVATE_EVIDENCE/frank-hft-sticky-rolling-historical-replay-NEW-UNIQUE-RUN" \
  --policy config/frank_local_signal_v1.json \
  --output ../meme/evidence/frank-hft-sticky-vs-rolling-2026-10-04.json
```

其中 python 为原已存在的 local-agent venv，PRIVATE_EVIDENCE 为本地已有 Frank-only private evidence 根目录。work 必须全新。post-replay report helper 的 `--help` 显示所需 artifact、variant-work、原 baseline、研究前只读 boundary snapshot、现有 runtime health 文件与 report 参数。既有结果已完成，无需触及 live DB 复现。
