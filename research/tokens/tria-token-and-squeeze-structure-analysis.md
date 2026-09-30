# TRIA 代币基本面与妖币挤压结构联合分析

Updated: 2026-09-30
Status: ACTIVE_RESEARCH

## 对象与身份

- Project: Tria / tria.so
- Token: TRIA
- Canonical Ethereum ERC-20: `0x228bEC415adE4b61D7CaF0adf8C91EAc587BA369`
- Max supply: 10,000,000,000 TRIA
- 当前研究目的：同时应用 `token_trading_principles.md` 与 `meme_trading_principles.md`，判断低市值、低价、Binance Alpha、Binance Futures、浅现货流动性、高衍生品杠杆和事件催化是否形成可重复的 squeeze / repricing setup。

## Evidence labels

- CONFIRMED：官方、链上或交易所一级资料直接验证。
- INFERRED：多个独立证据一致但仍缺最终链上归因。
- SPECULATIVE：叙事、传播和价格路径判断。

## 1. 代币合约

CONFIRMED：Ethereum 主合约已验证，`TriaToken` 为普通 ERC-20 + ERC20Permit + Ownable。构造函数一次性向 treasury mint `10,000,000,000 * 1e18`，源码没有额外公开 mint function，没有 proxy，也没有 freeze / blacklist / pause / transfer-tax 逻辑。

这对妖币模型属于明显正项：后续增发、可变交易税和管理员冻结这几个常见风险在 canonical Ethereum token 上没有发现。

链上数据同时显示 BNB Chain 存在 TRIA OFT 表示层，因此 holder / liquidity / circulating 分析必须区分 canonical Ethereum supply、跨链 OFT 与 CEX 托管地址，不能把不同链余额机械相加。

## 2. Tokenomics 与释放

CONFIRMED：官方 tokenomics：

- Community 41.04%
- Foundation 18.00%
- Ecosystem & Liquidity 15.00%
- Investors 13.96%
- Core Contributors 12.00%
- 固定 10B supply，无持续通胀。

2026-08-28 官方更新：团队和普通投资人 cliff 延长到 2028-02，随后至 2030-02 完成 vesting；该修改明确不适用于 Legion round investors。

官方把 336,924,781 TRIA 的 Community allocation 从 2027/2028 提前到 2026 H2。计划释放：

- 2026-08-30: 313,513,260 TRIA
- 2026-09-30: 233,513,260 TRIA
- 2026-10-30: 233,513,260 TRIA

因此 2026-09-30 当天存在明确新增可流通供应事件。该项是当前 squeeze thesis 的主要反向变量。

CoinMarketCap 在 2026-09-30 10:02 UTC 给出的 circulating supply 为约 2.85426B，而项目较早披露的 genesis circulation 为约 2.1577B。数据源当前正在反映累积释放，但具体 free-float 必须继续用 vesting contract、CEX custody 和跨链余额重建，不能只采用聚合器 circulating 数字。

## 3. 早期成本与上方套牢盘

CONFIRMED：Legion sale 存在两种结构：

- $100M FDV：30% TGE，70% 在包含 2 个月 cliff 的 6 个月窗口内线性释放。
- $200M FDV：60% TGE，40% 在包含 2 个月 cliff 的 6 个月窗口内线性释放。

在 10B 总供应下，对应约 $0.01 / $0.02 每枚的估值锚。

2026-09-30 TRIA 约 $0.00443，意味着价格仍显著低于两个 Legion FDV 锚。Legion 投资者不受 2028 insider lock 延长影响，因此反弹至 $0.01-$0.02 区间时应重点观察历史筹码卖压。

## 4. 基本面

CONFIRMED / FIRST-PARTY：Tria 已有真实消费与交易产品，包括 self-custodial neobank、Visa card、BestPath routing、Earn、spot/perps 等。官方 whitepaper 披露 70+ protocol integrations、$70M+ BestPath volume；项目新闻稿在 2026-09 披露 600k+ unique accounts、$8.5M+ revenue、运营第八个月盈利，以及日本和韩国贡献接近三分之二收入。

上述经营数字主要来自项目方 / Chainwire 新闻稿，尚未看到审计财务证明，因此只作为 first-party business metrics，不升级为独立审计事实。

CONFIRMED：TRIA 官方 utility 包括 BestPath settlement、PathFinder staking / routing access、gas/fee subsidy、governance 和 membership benefits。

UNRESOLVED：真实产品使用增长是否会强制形成持续公开市场 TRIA buy demand。当前 utility 说明了代币的功能，但还不足以证明收入或 BestPath volume 与二级市场净买盘存在稳定比例关系。

## 5. 市场结构快照 2026-09-30

CoinMarketCap snapshot：

- price: ~$0.00442-$0.00443
- market cap: ~$12.62M
- FDV: ~$44.23M
- 24h volume: ~$3.78M
- 24h: +4.1%
- 7d: +3.7%
- 30d: -13.3%
- 90d: -77.3%

历史 ATH 约 $0.05。因此从当前价格回到旧 ATH 本身约为 11x 级别，数学上 10x 并不需要创造全新历史高点，但对应的流通市值与供应结构已不同，不能直接把旧 ATH 当目标。

### Binance 交易入口修正

CONFIRMED：TRIA 同时已经存在 Binance Alpha 和 Binance USDⓈ-M Futures `TRIAUSDT` 永续。此前将“尚未 Binance CEX spot listing”简化表达成“未上 Binance”会误导，正确状态是：

- Binance Alpha：已存在。
- Binance Futures `TRIAUSDT` perpetual：已存在并活跃交易。
- Binance 主板现货 spot：本研究当前仍未确认正式 listing。

2026-09-30 约 17:10 Asia/Bangkok 的 Binance Futures 实时快照：

- last price: ~$0.004432
- mark price: ~$0.004429
- index price: ~$0.004411
- 24h futures quote volume: ~$6.44M
- 24h futures base volume: ~1.426B TRIA
- 24h high / low: $0.004698 / $0.004252
- Binance open interest: ~994.8M TRIA，按 mark price 约 $4.41M
- funding rate: +0.005% / 当前 funding interval

Binance 单交易所 OI 已约等于当前流通市值的三分之一，仍然属于高杠杆结构，但低于此前引用的跨交易所 Coinglass $15M-$16M OI 快照。跨交易所 OI 与 Binance 单交易所 OI 必须分开记录。

### Binance 多空结构

CONFIRMED：Binance 最近一小时级数据没有显示空头拥挤，反而显示多头账户明显占优。

最新 overall account long/short：

- long accounts: ~71.2%
- short accounts: ~28.8%
- long/short ratio: ~2.47

最新 top-trader position ratio：

- long: ~60.94%
- short: ~39.06%
- long/short ratio: ~1.56

过去 24 小时 top-trader position long ratio 从约 59.5% 逐步升到约 60.9%。Funding 同时保持正值，因此当前证据不支持“空头已经高度拥挤、马上可被向上 squeeze”的说法。

最近一小时 taker buy/sell ratio 一度升到约 1.53，说明短周期主动买入增强；但过去 24 小时多个小时该比值低于 1，因此只能记为近期买盘改善，不能把单小时数据当作持续现货主导趋势。

当前衍生品结构更准确的表述是：高 OI 提供双向清算燃料，但账户与大户仓位当前偏多，若价格失守关键支撑，long liquidation 风险同样明显。

## 6. Spot liquidity 与 holder 结构

Ethereum Uniswap V3 TRIA/USDT 主可见池近期约有 ~$140K 双边 liquidity，链上 DEX volume 远低于 CEX / derivatives volume。BSC 可见 V4 pool 更浅。

这对价格弹性是双刃剑：少量真实 spot inflow 可以快速抬价，同时一旦 CEX / vesting recipients 转为净卖出，回撤也会非常快。

公开 holder 聚合器显示 Top10 高度集中，但该原始数字不能直接解释为鲸鱼控制。最大的 Ethereum 地址之一已被链上 explorer 识别为 `MerkleVester` vesting contract，曾持有数十亿 TRIA。因此必须先剔除 vesting、bridge/OFT、CEX、LP、foundation/treasury，再计算真实自由钱包 Top10 / Top20。

Holder concentration 当前状态：ACTIVE_RESEARCH。

## 7. 妖币模型映射

正向条件：

- 约 $10M 级低 circulating market cap。
- FDV 约 $40M 级，绝对估值低。
- 旧 ATH 距现价约一个数量级。
- Binance Alpha 已存在。
- Binance `TRIAUSDT` 永续已经上线且交易活跃，说明币安体系已有稳定衍生品价格发现与流量入口。
- Binance 主板现货当前仍未确认，因此未来若正式 spot listing，仍保留额外 listing narrative，但不能把 Alpha + Futures 当成“即将主板现货”的证据。
- 其他 CEX 也已有 spot/perp，交易入口充足。
- Binance 单所 OI 约 $4.4M，约为当前流通市值三分之一，杠杆参与度高。
- 主 DEX liquidity 较浅，真实 spot inflow 对价格影响大。
- 项目有真实产品与融资背景，叙事承载能力强于普通壳币。
- 2026-09-29 至 10-01 KBW Seoul，Tria 为 Diamond Sponsor，当前存在亚洲线下曝光和 KOL 扩散催化。
- token contract 本身没有额外 mint / freeze / variable tax 风险。

反向条件：

- 2026-09-30 正好是 233,513,260 TRIA Community release 日，10-30 还有同规模一笔。
- Legion round 历史成本约对应 $0.01 / $0.02，反弹途中存在明显成本锚和潜在供应。
- 大量 reward / community token 的实际卖压尚未完成地址级验证。
- Binance overall accounts 当前约 71% long，top-trader positions 约 61% long，funding 为正，当前没有确认的 short crowding；高 OI 当前同样构成 long squeeze 风险。
- DEX liquidity 浅，提高上涨弹性的同时也放大撤退风险。
- 产品收入到 TRIA open-market demand 的价值捕获链条仍不完整。
- 当前 KOL 扩散属于催化线索，不能独立作为入场依据。

## 8. 当前状态

Classification: WATCH

当前已经满足“低市值 + 深度回撤 + Binance Alpha + Binance Futures + 浅 spot depth + 高杠杆参与 + 真实项目叙事 + KBW/KOL catalyst”这一组典型高波动前置条件。

但 Binance 实时多空结构对“向上 short squeeze”假设形成直接反证：总体账户与 top traders 均明显偏多，funding 为正。因此不能因为 OI 高就自动推导为上行 squeeze setup。

升级到 SETUP 需要三个确认项：

1. 9/30 community release 后，主要 vesting / claim / CEX deposit 地址没有形成持续现货卖压；
2. 多空结构重新出现可被向上挤压的条件，例如价格上涨同时 funding 不显著变热、short share 增加或 OI 在上涨中由被动空头推动，而非多头进一步堆积；
3. 价格突破近期 `$0.00477-$0.00515` 区间并进一步越过约 `$0.00575` swing high，同时 spot volume、quote liquidity 和独立买家同步增长。

如果只有 perp volume / OI 上升而 spot 不跟，或 long ratio 继续扩大，继续维持 WATCH，并提高多头清算风险权重。

当前失效参考：跌回约 `$0.00417` 以下且 spot / CEX 净流出扩大；更强失效区在约 `$0.00374`，接近近期结构下沿。

## 9. 下一步链上工作

- 重建 Ethereum + BSC/OFT supply bridge accounting。
- 标记 MerkleVester、foundation、ecosystem、CEX、LP、bridge 地址。
- 计算去除特殊地址后的 Top10 / Top20 free-float concentration。
- 追踪 2026-09-30 233.513M release 的实际 recipient、claim、CEX deposit 与卖出路径。
- 持续读取 Binance TRIAUSDT funding、OI、overall long-short、top-trader positions 与 taker flow，和其他交易所交叉验证。
- 用 spot CEX volume + DEX quote reserve 判断突破是否由真实现货资金驱动。

## Primary / high-quality sources

- https://www.tria.so/legal/whitepaper
- https://blogs.tria.so/en/tria-tokenomics
- https://blogs.tria.so/en/tria-tokenomics-update-august-2026
- https://help.legion.cc/en/articles/12728894-tria-sale-details
- Binance USDⓈ-M Futures live market data: `TRIAUSDT`
- Ethereum token: https://etherscan.io/token/0x228bEC415adE4b61D7CaF0adf8C91EAc587BA369
