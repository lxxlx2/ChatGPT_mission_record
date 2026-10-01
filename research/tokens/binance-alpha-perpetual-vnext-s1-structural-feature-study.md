# Binance Alpha + 永续 VNext S1 结构变量研究

Updated: 2026-10-01
Status: ACTIVE_RESEARCH

## 目标

Phase B 盲测已经证明：

- price probe
- funding regime
- premium / basis stress cluster
- repeated cluster
- higher trailing price base

能够抓到高波动重估，但仍无法稳定区分约 2x repricing 与用户真正关心的 10x extreme monster。

因此本文件停止继续堆 price / premium 阈值，转向 S1 底层结构：

1. executable free float
2. holder concentration
3. LP / CEX / bridge / staking / vesting inventory
4. underlying index / spot venue fragility
5. futures turnover 相对于真实可交易筹码的大小

本文件只属于 research 层，不修改 Monster V2.1 / Frank / Codex runtime。

TRIA 继续保持完全 out-of-sample。

## 1. Futures turnover / headline FDV 单独无效

使用固定 max supply × 当时 signal price 构造简单 FDV proxy，并以 Phase B 信号窗口的 futures quote turnover 做 sanity check。

### IN

- max supply: 1,000,000,000 IN
- Phase B SignalPrice: 约 0.11854
- FDV proxy: 约 $118.54M
- second-cluster 两根 4h futures quote turnover 合计约 $109.15M
- `8h futures turnover / FDV ≈ 0.92x`

Outcome: 90d Capture 约 2.52x，针对 10x monster 为 false positive。

### NAORIS

- total / max supply market-data reference: 4,000,000,000
- Phase B SignalPrice: 约 0.07645
- FDV proxy: 约 $305.8M
- second-cluster 两根 4h futures quote turnover 合计约 $226.9M
- `8h futures turnover / FDV ≈ 0.74x`

Outcome: 90d Capture 约 2.09x，针对 10x monster 为 false positive。

### 结论

高 futures turnover 相对于 headline FDV 并非 extreme-monster-specific 特征。

原因很直接：FDV 把未来锁仓、长期激励、团队、投资者和不可交易库存全部放入分母，无法描述当前真正能够吸收买卖盘的筹码。

因此 VNext 不应使用 `futures turnover / FDV` 作为核心 S1 判别器。

## 2. 低 TGE headline float 也无法单独区分

### XPIN：强正样本

XPIN 官方 tokenomics：

- total supply: 100B
- Public Sale: 2%，TGE unlock 2%
- Liquidity: 2%，TGE unlock 2%
- Marketing & Airdrop: 12%，6 个月线性
- Strategic Partners & Backers: 16%，6 个月 cliff 后 15 个月线性
- Team & Advisors: 20%，6 个月 cliff 后 24 个月线性
- Foundation: 8%，12 个月 cliff 后 48 个月线性
- Ecosystem Incentives: 40%，120 个月长期释放 / yearly halving

这意味着 XPIN 在 TGE 附近具有明显受限的可即时释放供应结构。

### IN：Phase B false positive

INFINIT 官方 tokenomics：

- max supply: 1B
- Initial Airdrop: 5%，TGE unlock
- Core Contributors: 20%，锁 15 个月，随后季度释放 36 个月
- Investors: 25.5%，锁 9 个月，随后 12 个月日线性释放
- Community & Ecosystem: 49.5%，4 年释放

IN 同样具备低初始释放 + 大比例长期 vesting，但 Phase B 信号后 90d 最高只有约 2.52x。

### NAORIS：Phase B false positive

NaoX / Naoris 官方 MiCA whitepaper 记录：

- public offer: 24,000,000 NAORIS at $0.125
- private backers entered at $0.04 / $0.08
- private-sale tokens locked 4-6 months
- public buyers could claim at launch

NAORIS 同样存在受限的早期可售结构，但 Phase B 信号后 90d 最高只有约 2.09x。

### 结论

`低 TGE unlock %` 只能提高 thin-float 的先验概率，无法单独区分 2x 与 10x。

真正需要验证的是：

`actual executable float at signal time`

而非文档中的 allocation 百分比。

## 3. VNext 需要的 executable-float 定义

建议将 supply 拆为链上可审计分类：

`Total Supply`

减去：

- vesting / timelock contracts
- treasury / foundation wallets
- team / investor wallets，在仍受链上锁定时排除
- bridge escrow / canonical bridge inventory
- staking / deposit contracts，按真实退出条件分类
- burn / dead addresses
- LP inventory 中不可直接作为自由卖压的一侧，单独记录

再把剩余地址按类型拆分：

- CEX hot / omnibus wallets
- DEX LP / pool inventory
- market-maker / known liquidity wallets
- top holders
- long-tail holders

最终至少生成两个量：

### Effective Circulating Supply

已经解锁、可以正常转移的链上供应。

### Executable Float

在当前主要现货 venue 上，短时间内真正可能参与价格发现的供应。

Executable Float 比 Effective Circulating Supply 更严格。

例如大量币虽然已经解锁，但长期停在从未卖出的独立地址，对几小时级现货深度的作用与 CEX hot wallet / active LP inventory 不同。

## 4. 候选 concentration 指标

第一版建议只研究可解释指标，不训练黑箱分数：

- `Top10_FreeFloat_Share`
- `Top20_FreeFloat_Share`
- `CEX_and_LP_Float_Share`
- `Active_7d_Float / Effective_Circulating`
- `Active_30d_Float / Effective_Circulating`
- `Net_CEX_Inflow_24h / Executable_Float`
- `Net_CEX_Inflow_7d / Executable_Float`
- `Futures_24h_Turnover / Executable_Float_USD`
- `Futures_8h_Turnover / Executable_Float_USD`

这些指标必须基于 signal time 当时可见的链上状态，禁止用今天的 holder distribution 回填历史。

## 5. Index constituents：有当前数据，缺历史 constituents

Binance 官方 USDⓈ-M index constituent endpoint 当前可以返回：

- constituent exchange
- constituent symbol
- price
- weight
- snapshot time

2026-09-30 当前例子：

### MYX

5 个 constituents：Gate, MEXC, Bitget, PancakeSwap V3, Binance Futures。

Binance Futures 当前 weight 约 36.84%。

### LAB

4 个 constituents：Gate, KuCoin, Binance Futures, Binance Alpha，各约 25%。

### RIVER

4 个 constituents：MEXC, Bitget, Binance Futures, Binance Alpha。

### BTW

4 个 constituents：Gate, MEXC, Binance Futures, Binance Alpha。

### IN

5 个 constituents：Gate, KuCoin, MEXC, Bitget, Binance Alpha。

### NAORIS

4 个 constituents：Gate, MEXC, Bitget, Binance Futures。

### XAN

6 个 constituents：Coinbase, Gate, KuCoin, MEXC, Bybit, Binance Alpha。

当前 constituent 数量 / Binance-self weight 没有显示一个足够简单的 strong-vs-false-positive 分界。

更重要的数据限制：当前 official constituent endpoint 返回的是当前快照，不提供历史 constituent composition 参数。

因此禁止用 2026-09-30 的 constituents 解释 2025 / 2026 signal-time index composition。

## 6. Historical depth / Alpha order book 数据边界

Binance 当前公开接口可以获取：

- 当前 Spot order book
- 当前 Futures order book
- 历史 Futures / index / premium klines

本轮没有找到 Binance 官方公开的 Alpha 历史 order-book / depth archive。

因此无法严谨重建 2025 年某个 signal 时刻的 `±1% / ±2% Alpha executable depth`。

若未来获得一手 archive 或项目仓库此前保存过快照，可补入；当前不能通过今天的 order book 倒推历史深度。

## 7. Historical holder snapshot：第一轮真实链上重建

用户已明确选择 Alchemy app `ChatGPT Crypto Monitor All Chains`。该 app 覆盖 BNB Mainnet 与 Ethereum Mainnet。本轮只做 read-only historical RPC、ERC-20 `Transfer` replay 与 historical `eth_call`，没有签名、广播或交易操作。

### 7.1 Signal-time historical block anchors

全部锚点使用当时已经冻结的 VNext signal 定义，并以真实 block timestamp 收敛：

- MYX BNB block `55,492,839`，timestamp `2025-07-27 12:00:00.500 UTC`。
- XPIN BNB block `63,305,500`，timestamp `2025-10-03 08:00:00 UTC`。该时点是 21d seasoning 后第一组 basis `2-of-3` cluster，比此前记录的 2025-10-13 obvious price probe 提前约 10 天。
- IN BNB block `63,459,084`，timestamp `2025-10-04 16:00:01.500 UTC`；Ethereum block `23,505,462`，timestamp `2025-10-04 15:59:59 UTC`。
- NAORIS BNB block `60,772,022`，timestamp `2025-09-11 08:00:00 UTC`；Ethereum block `23,338,486`，timestamp `2025-09-11 07:59:59 UTC`。

### 7.2 Historical total-supply and cross-chain normalization

Historical `totalSupply()` at the frozen blocks:

- MYX BNB: `1,000,000,000`。
- XPIN BNB: `100,000,000,000`。
- IN BNB: `68,452,431.298171`。
- IN Ethereum: `931,547,568.7018291`。
- IN BNB + Ethereum 精确约等于 `1,000,000,000`，说明 signal-time economic supply 在两链之间拆分；单链 Top10 会受到桥接 / 跨链供应分布影响。
- NAORIS BNB: `120,000,000`。
- NAORIS Ethereum: `4,000,000,000`。
- NAORIS 两链直接相加得到 4.12B，超过 canonical 4B，因此 BNB 120M 不能直接加到 Ethereum total supply；需要按 bridge representation / escrow 机制归一化。

结论：任何 `Top10 >= X%` 策略在 multi-chain token 上都必须先完成 bridge normalization。直接读单链 holder leaderboard 可能把桥 escrow 或镜像供应当成真实控盘。

### 7.3 MYX：强正样本的 historical concentration

MYX genesis mint 为 1B，随后一笔初始分配交易把完整 1B 精确拆到 14 个 allocation 地址。

初始大桶包括：

- 200M
- 175M
- 167.184M
- 116.64M
- 80M
- 79.44M
- 64.241M
- 40M
- 20M
- 19.813M
- 17.964M
- 13.147M
- 3.776M
- 2.795M

在 2025-07-27 signal block 逐地址 `balanceOf()` 后：

- 14 个原始 allocation 地址仍合计持有约 `862.944M`，占 total supply `86.29%`。
- 仅这 14 个地址中余额最大的 10 个合计约 `856.530M`，占 total supply `85.65%`。
- 200M 与 175M 两个最大初始钱包在 signal 时余额完全未变。
- 167.184M 地址仍持有约 163.296M。
- 116.64M 地址仍持有完整 116.64M。

`85.65%` 是已知初始 allocation 地址子集形成的 raw Top10 lower bound，不是全链精确 Top10。后来接收大额转账的新地址尚未全部并入，因此真实全链 Top10 只能等于或高于该子集下界。

### 7.4 XPIN：强正样本的 historical concentration

XPIN genesis mint 为 100B。最初发行地址随后形成五个主要分配桶：

- 40B
- 20B
- 16B
- 16B
- 8B

这五项精确合计 100B。

官方 tokenomics 同期类别为：Ecosystem 40%、Team 20%、Strategic 16%、Foundation 8%、Marketing & Airdrop 12% + Public 2% + Liquidity 2%。金额结构与链上五桶高度吻合，但具体 wallet-to-category 映射在没有一手地址标签前仍记为 `INFERRED`。

2025-10-03 basis-only watch block 的 historical balance：

- 40B 初始地址仍约 39.6B。
- 20B 初始地址仍完整 20B。
- 一个 16B 初始地址仍完整 16B。
- 8B 初始地址仍完整 8B。
- 另一个 16B 初始地址已降到约 0.435B，并存在至少两个可追踪下游地址约 0.932B 与 0.298B。

这些已知地址在 signal 时合计至少约 `85.265B / 100B = 85.27%`。

这同样是 lower bound，尚未覆盖所有 downstream holders。

### 7.5 IN：false positive 的分配结构明显更分散

IN Ethereum genesis mint 为 1B。早期发行地址随后将几乎完整供应拆到二十多个不同地址，常见单桶为 50M，另外还有 71.667M、55M、30M、25M、20M、15M、12.5M 等。

按初始分配金额排序，最大的 10 个 allocation 地址合计约 `531.667M / 1B = 53.17%`。

进一步追踪确认：

- 71.667M 初始地址随后把完整余额转入独立合约 `0xbe83...`，signal block 该合约仍持有完整 71.667M。
- 两个独立 55M 初始地址分别转入不同目标合约 `0xaa2d...` 与 `0x6e64...`，signal block 两个目标各自仍持有完整 55M。

因此至少前三个较大 allocation 并没有在 signal 前合并到同一 holder；IN 的供应组织方式与 MYX / XPIN 少数超大桶明显不同。

当前尚未完成 IN 全链 signal-time 精确 Top10 replay，因此 `53.17%` 只能描述 genesis allocation Top10，不能当作最终 historical Top10。

### 7.6 NAORIS：Top10 90% 规则出现强 false-positive evidence

NAORIS Ethereum genesis 将完整 4B mint 到单一发行地址。

到 2025-09-11 Phase B false-positive signal：

- 原发行地址仍持有约 `1,918,042,162.2222223`，占 canonical 4B 的约 `47.95%`。
- 地址 `0xaa2a...` signal 时持有约 `1,440,934,373.335583`。
- 一条 `0x7108... -> 0xbc88... -> 0x1fe2...` 的链上迁移最终使 `0x1fe2...` 在 signal 时持有约 `422,000,005`。

仅这三个地址合计：

`3,780,976,540.557805 NAORIS`

占 canonical Ethereum 4B supply：

`94.52%`

因此 NAORIS 在 Phase B signal 时仅 Top3 已超过 `90%` concentration。

该样本的 forward 90d MFE 只有约 `2.09x`，所以 `raw Top10 > 90%` 无法单独作为 10x monster 判别器。

额外核对：

- 当前 Binance Spot `NAORISUSDT` 返回 `Invalid symbol`，截至本轮查询仍没有 Binance 主板现货交易对。
- NAORIS 属于预先固定的 Alpha + Futures cohort。
- Binance official historical OI statistics 对 2025-09-11 的旧 `startTime` 请求返回 invalid parameter，signal-time `OI > $5M` 暂记 `DATA_UNAVAILABLE`，禁止用当前 OI 回填历史。

因此目前可以确认 NAORIS 同时满足 `Alpha + Futures`、`无当前 Binance 主板 Spot`、`signal-time raw Top3 > 90%`，但历史 OI 门槛无法由 Binance 官方现有历史接口复原。

### 7.7 对“Alpha + Futures + 高控盘”筛选法的当前判断

截图中的候选规则提供了一个有用的 universe filter，但链上回测说明 `Top10 > 90%` 本身过于粗糙：

- MYX / XPIN 强正样本确实具有高度集中的大额 allocation / long-term inventory。
- NAORIS false positive 在 signal 时 Top3 已达到 94.52%，集中度甚至更极端。
- IN false positive 的初始 distribution 明显更分散，说明 concentration 可能仍有信息量，但不能用单一 90% threshold 表达。

下一步应把 raw concentration 拆为：

- `Locked_or_Programmatic_Supply_Share`
- `Top10_Executable_Float_Share`
- `Top10_Unlocked_NonBridge_Share`
- `Bridge_Escrow_Share`
- `CEX_LP_MM_Inventory_Share`

真正需要验证的候选机制是：少量真正可交易 float 是否被少数活跃地址 / venue 控制，同时 futures notional 足以远大于该 executable float。

## 8. 新的 Phase C 门槛

Phase C 暂时不建立 holdout，也不查看 TRIA。

必须先完成至少一个真正的 S1 structural feature，使它能够在 development evidence 上解释：

- 为什么 MYX / XPIN 等 extreme sample 的 executable structure 更容易形成持续反身性；
- 为什么 IN / NAORIS / COMMON / RECALL 只能形成约 2x 或一次性 spike；
- 为什么该指标在 signal time 可计算；
- 为什么没有使用未来数据；
- 为什么数据源可以稳定复现。

只有满足上述条件后，才固定 Phase C rule 并选择全新的 untouched holdout。

## 9. 当前证据等级

CONFIRMED：

- Phase B 的 repeated-basis + higher-base 规则无法区分 2x 与 10x。
- IN / NAORIS 在 false-positive signal 窗口的 futures turnover / headline FDV 已经很高，说明该比值缺乏 monster-specific discrimination。
- XPIN、IN、NAORIS 都具有受限早期供应 / 锁仓结构；低 headline initial float 本身无法区分强正样本和 false positive。
- Binance index constituents endpoint 只给当前 snapshot；当前 constituent count / weight 没有形成简单分界。
- 本轮没有找到 Binance 官方 Alpha historical depth archive。
- MYX / XPIN signal-time 链上历史状态均显示极高的大额 allocation concentration；已知地址 lower bound 分别约 85.65% 与 85.27%。
- IN genesis allocation Top10 约 53.17%，且已核验的 71.667M、55M、55M 大桶在 signal 前保持分立。
- NAORIS signal-time Top3 占 canonical Ethereum supply 约 94.52%，但其 Phase B signal 后 90d MFE 仅约 2.09x。
- IN 与 NAORIS 的 multi-chain supply accounting 机制不同；单链 Top10 / 简单跨链求和都可能失真。

INFERRED：

- raw holder concentration 仍可能包含有效结构信息，但必须先剥离 vesting、treasury、bridge、staking、LP / CEX / MM inventory。
- 真正可能增加 10x-specific discrimination 的变量是 signal-time executable float、active inventory 和 futures notional 相对于 executable float 的比例。
- XPIN 五个初始大桶与官方 tokenomics 类别在金额上高度吻合，但 wallet-to-category 的具体映射仍需一手标签或合约语义确认。

UNRESOLVED：

- MYX / XPIN 全链精确 raw Top10 / Top20，以及剥离长期 allocation 后的 executable-float concentration。
- IN signal-time 全链精确 Top10 / Top20 与 BNB bridge-normalized holder state。
- NAORIS `0xaa2a...`、`0x1fe2...`、发行地址等大户的 treasury / vesting / custodian 语义。
- signal-time LP / CEX / staking / vesting inventory。
- `futures turnover / executable-float USD` 是否真正区分 2x 与 10x。
- 历史 OI 超出 Binance public retention 时的可靠一手恢复方案。
- 新 Phase C holdout 的结果。

## Sources

- XPIN official tokenomics: https://docs.xpin.network/tokenomics
- INFINIT official IN tokenomics: https://docs.infinit.tech/tokenomics/in-token
- MYX official tokenomics / official MYX distribution materials.
- NaoX official MiCA whitepaper: https://www.naox.org/mica-compliance-white-paper
- Binance official USDⓈ-M index constituent API documentation.
- Binance public Futures, Premium Index, Spot exchange-info and OI market-data endpoints, queried 2026-09-30 / 2026-10-01.
- Alchemy read-only BNB Mainnet and Ethereum Mainnet historical RPC through user-selected `ChatGPT Crypto Monitor All Chains` app, queried 2026-10-01.
- Historical ERC-20 `totalSupply()`, `balanceOf()` and Transfer history at the frozen signal blocks are treated as primary chain evidence.
- CoinMarketCap latest token supply metadata used only for current max/total-supply sanity checks; not treated as historical holder truth.
