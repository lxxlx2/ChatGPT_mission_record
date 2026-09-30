# Binance Alpha + 永续 VNext S1 结构变量研究

Updated: 2026-09-30
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

## 7. Historical holder snapshot 的可行路径

MYX / LAB / XPIN 位于 BNB Chain；RIVER / IN / NAORIS 等存在 Ethereum / multi-chain ERC-20 合约。

要重建 signal-time holder state，最可靠的方法是：

1. 将 signal timestamp 映射到各链 historical block。
2. 从 token genesis 到该 block 重放 ERC-20 `Transfer` logs。
3. 计算每个地址在该 block 的 token balance。
4. 标记 vesting / treasury / bridge / LP / CEX / staking 等已知地址。
5. 生成 Effective Circulating 与 Executable Float 快照。
6. 对每个历史 signal 只使用该 signal block 之前的数据。

该方法成本较高，但符合项目“链上事实优先”的证据原则。

当前已连接的 Alchemy 账号存在 3 个 app；连接器规则要求多 app 时由用户指定 app 后才能进行 RPC / logs 查询。本轮未擅自选择，也未因此用估算数据填空。

Blockscout 当前连接的可用 chain registry 未直接返回 BNB Smart Chain，因此不能假设它可替代 BSC historical RPC。

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

INFERRED：

- 真正可能增加 10x-specific discrimination 的变量是 signal-time executable float、holder concentration、active inventory 和 futures notional 相对于 executable float 的比例。
- 文档 tokenomics 适合提供地址分类线索，但最终 supply / holder 结论应以 signal-time 链上重建为准。

UNRESOLVED：

- MYX / XPIN / LAB / RIVER / IN / NAORIS 在 signal block 的 Top10/Top20 executable-float concentration。
- signal-time LP / CEX / staking / vesting inventory。
- `futures turnover / executable-float USD` 是否真正区分 2x 与 10x。
- 哪个链上 concentration / active-float 指标最稳定。
- 新 Phase C holdout 的结果。

## Sources

- XPIN official tokenomics: https://docs.xpin.network/tokenomics
- INFINIT official IN tokenomics: https://docs.infinit.tech/tokenomics/in-token
- MYX official tokenomics: https://myxfinance.gitbook.io/myx/protocol/tokenomics
- NaoX official MiCA whitepaper: https://www.naox.org/mica-compliance-white-paper
- Binance official USDⓈ-M index constituent API documentation.
- Binance public Futures and Premium Index market data, queried 2026-09-30.
- CoinMarketCap latest token supply metadata used only for current max/total-supply sanity checks; not treated as historical holder truth.
