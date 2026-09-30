# TRIA 代币基本面与妖币挤压结构联合分析

Updated: 2026-09-30
Status: ACTIVE_RESEARCH

## 对象与身份

- Project: Tria / tria.so
- Token: TRIA
- Canonical Ethereum ERC-20: `0x228bEC415adE4b61D7CaF0adf8C91EAc587BA369`
- Max supply: 10,000,000,000 TRIA
- 当前研究目的：同时应用 `token_trading_principles.md` 与 `meme_trading_principles.md`，判断低市值、低价、Binance Alpha、浅现货流动性、高衍生品杠杆和事件催化是否形成可重复的 squeeze / repricing setup。

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

2026-09-30 TRIA 约 $0.00442，意味着价格仍显著低于两个 Legion FDV 锚。Legion 投资者不受 2028 insider lock 延长影响，因此反弹至 $0.01-$0.02 区间时应重点观察历史筹码卖压。

## 4. 基本面

CONFIRMED / FIRST-PARTY：Tria 已有真实消费与交易产品，包括 self-custodial neobank、Visa card、BestPath routing、Earn、spot/perps 等。官方 whitepaper 披露 70+ protocol integrations、$70M+ BestPath volume；项目新闻稿在 2026-09 披露 600k+ unique accounts、$8.5M+ revenue、运营第八个月盈利，以及日本和韩国贡献接近三分之二收入。

上述经营数字主要来自项目方 / Chainwire 新闻稿，尚未看到审计财务证明，因此只作为 first-party business metrics，不升级为独立审计事实。

CONFIRMED：TRIA 官方 utility 包括 BestPath settlement、PathFinder staking / routing access、gas/fee subsidy、governance 和 membership benefits。

UNRESOLVED：真实产品使用增长是否会强制形成持续公开市场 TRIA buy demand。当前 utility 说明了代币的功能，但还不足以证明收入或 BestPath volume 与二级市场净买盘存在稳定比例关系。

## 5. 市场结构快照 2026-09-30

CoinMarketCap snapshot：

- price: ~$0.00442
- market cap: ~$12.62M
- FDV: ~$44.23M
- 24h volume: ~$3.78M
- 24h: +4.1%
- 7d: +3.7%
- 30d: -13.3%
- 90d: -77.3%

历史 ATH 约 $0.05。因此从当前价格回到旧 ATH 本身约为 11x 级别，数学上 10x 并不需要创造全新历史高点，但对应的流通市值与供应结构已不同，不能直接把旧 ATH 当目标。

近期 Coinglass snapshot 曾显示：

- futures volume ~$11.65M-$15.3M / 24h
- spot volume ~$0.72M-$1.23M / 24h
- open interest ~$15.3M-$16.3M

这意味着衍生品规模接近或超过当时 spot market cap，且 futures volume 远高于 spot volume。该结构具有很强的双向 liquidation / squeeze 弹性。

UNRESOLVED：当前 funding rate、exchange-level long/short concentration 和大户方向尚未取得可靠实时值，因此现在只能确认“具备 squeeze 燃料”，不能确认“向上 squeeze 已经形成”。

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
- Binance Alpha 已存在，尚未 Binance CEX spot listing，保留潜在 listing narrative。
- Bitget / MEXC 等已有 spot，Gate 等已有 perpetual，交易入口充足。
- derivatives OI / spot market cap 比例异常高，具备挤压燃料。
- 主 DEX liquidity 较浅，真实 spot inflow 对价格影响大。
- 项目有真实产品与融资背景，叙事承载能力强于普通壳币。
- 2026-09-29 至 10-01 KBW Seoul，Tria 为 Diamond Sponsor，当前存在亚洲线下曝光和 KOL 扩散催化。
- token contract 本身没有额外 mint / freeze / variable tax 风险。

反向条件：

- 2026-09-30 正好是 233,513,260 TRIA Community release 日，10-30 还有同规模一笔。
- Legion round 历史成本约对应 $0.01 / $0.02，反弹途中存在明显成本锚和潜在供应。
- 大量 reward / community token 的实际卖压尚未完成地址级验证。
- OI 很高但 funding / short crowding 尚未确认，高杠杆同时支持 long squeeze 和 short squeeze。
- DEX liquidity 浅，提高上涨弹性的同时也放大撤退风险。
- 产品收入到 TRIA open-market demand 的价值捕获链条仍不完整。
- 当前 KOL 扩散属于催化线索，不能独立作为入场依据。

## 8. 当前状态

Classification: WATCH -> SETUP CANDIDATE

当前已经满足“低市值 + 深度回撤 + Binance Alpha + CEX/Perp infrastructure + 浅 spot depth + 高 OI + 真实项目叙事 + KBW/KOL catalyst”这一组典型爆拉前置条件。

还缺三个确认项才能升级：

1. funding / long-short / liquidation map 证明杠杆真正偏向可被向上挤压的一侧；
2. 9/30 community release 后，主要 vesting / claim / CEX deposit 地址没有形成持续现货卖压；
3. 价格突破近期 `$0.00477-$0.00515` 区间并进一步越过约 `$0.00575` swing high，同时 spot volume、quote liquidity 和独立买家同步增长。

如果只有 perp volume 上升而 spot 不跟，继续维持 WATCH。

当前失效参考：跌回约 `$0.00417` 以下且 spot / CEX 净流出扩大；更强失效区在约 `$0.00374`，接近近期结构下沿。

## 9. 下一步链上工作

- 重建 Ethereum + BSC/OFT supply bridge accounting。
- 标记 MerkleVester、foundation、ecosystem、CEX、LP、bridge 地址。
- 计算去除特殊地址后的 Top10 / Top20 free-float concentration。
- 追踪 2026-09-30 233.513M release 的实际 recipient、claim、CEX deposit 与卖出路径。
- 拉取 Gate/Bitget 等 TRIA perpetual 的 funding、OI、long-short 与 liquidation concentration。
- 用 spot CEX volume + DEX quote reserve 判断突破是否由真实现货资金驱动。

## Primary / high-quality sources

- https://www.tria.so/legal/whitepaper
- https://blogs.tria.so/en/tria-tokenomics
- https://blogs.tria.so/en/tria-tokenomics-update-august-2026
- https://help.legion.cc/en/articles/12728894-tria-sale-details
- https://www.bitget.com/news/detail/12560605180036
- https://www.mexc.com/announcements/article/first-in-market-17827791533451
- https://www.binance.com/en-IA/how-to-buy/tria
- Ethereum token: https://etherscan.io/token/0x228bEC415adE4b61D7CaF0adf8C91EAc587BA369
