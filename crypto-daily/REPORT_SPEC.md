# Crypto Daily Report Specification

Last updated: 2026-09-21
Status: canonical

## Goal

The daily report is a decision-oriented market intelligence product. It must identify new high-impact events, persistent trends, cross-market/cross-chain opportunities, structural changes, security risks, and invalidation conditions. It must not read like a chronological news dump.

Only one normal report is sent each day at 09:00 Asia/Bangkok. A full correction may be sent only for a material factual error or a missed highest-priority event.

## User-visible content

Internal rules, QA, numbering checks, classification checks, scan logs, missing-data explanations, GitHub status and correction mechanics belong only in run audits.

Do not put phrases such as:
- 分类自检：通过
- 序号自检：通过
- CA与链接QA：通过
- 本节仅收……
- 本期正式入选0个
- lengthy explanations for why a section is empty

If a section has no decision-relevant update, use at most one short line.

## Fixed report structure

一、今日最重要的5件事
二、BTC/ETH/SOL及主要资产
三、二级市场剧烈波动与持续趋势
四、监管与政策
五、机构、VC、基金、交易所、上市公司、做市商、鲸鱼真实资金动作
六、融资、协议、基础设施、稳定币、RWA、预测市场、AI/Crypto、DePIN及公链生态
七、空投、积分、TGE、ICO/公售、解锁和实际可参与机会
八、Early / Meme / NFT / 新生态热点
九、安全、黑客、漏洞、恶意App、脱锚、跑路、清算与重大解锁
十、全球局势与跨市场冲击
十一、未来24至72小时催化
十二、持续趋势与跨市场机会观察清单
十三、今日行动与风险结论

Chapter items use full-width numbering （1）（2）（3）. Deeper levels use ①②③ or •. Gmail is text/plain.

## Persistent-trend discovery

Do not depend on a manually named watchlist. Scan the mature market universe first.

At minimum cover major CEX assets, high-liquidity CoinGecko/CoinMarketCap assets and major perpetual markets such as Hyperliquid. Check available 24h, 3d/5d, 7d and 30d windows.

Escalate a mature asset into the trend candidate pool when any of these is true:
- roughly ±5% in 24h
- roughly ±15% to ±20% in 7d
- roughly ±30% in 30d
- clear relative strength versus BTC/ETH for 3+ days
- new 30d/90d/ATH/ATL
- material volume expansion
- unusual OI/funding/basis/liquidations
- persistent ETF/institution/on-chain flows
- material protocol, regulatory, listing or upgrade catalyst

Chapter 3 explains the move. Chapter 12 converts persistent trends into a watchlist with decision value.

For each Chapter 12 candidate include, when data exists: 24h/7d/30d trend, volume, OI/funding/liquidations, spot vs derivatives, whale/exchange flows, official catalyst, X/KOL views, Reddit views, counterevidence, invalidation conditions, and the next 1–7 day price/on-chain/event checkpoints.

## Cause research

Do not stop at “no credible explanation found”.

For every significant mature-asset move inspect:
1. official X, blog, governance and docs
2. official exchange listings/delistings/campaigns
3. spot volume and cross-exchange price
4. perpetual OI, funding, basis and liquidations
5. on-chain large transfers, exchange flows and whale positions
6. Polymarket and other real-money prediction markets where relevant
7. English X from teams, researchers, KOLs, market makers and on-chain analysts
8. Reddit project communities plus r/CryptoCurrency and r/CryptoMarkets
9. Reuters, The Block, Blockworks and other high-quality English media

If no single cause is confirmed, provide confirmed factors, on-chain clues, X/Reddit hypotheses, counterarguments, and evidence strength.

## Cross-platform and cross-chain opportunity scan

Scan same-asset prices and executable depth across major CEX/DEX/chains, including Ethereum, Arbitrum, Base, BNB Chain, Solana, Robinhood Chain, Hyperliquid, X Layer/OKX, Avalanche, Sui and Optimism.

If an executable spread is around 2%+ or carry/LP/bridge economics are abnormal, calculate buy price, sell price, depth, gas, slippage, bridge fees, withdrawal limits, bridge/challenge time, fast-bridge liquidity, capital lock time, net return, annualized return, convergence risk and capacity.

Do not explain an asset such as UNI using only one venue's 24h ticker when cross-chain pricing may be the key driver.

## X and Reddit

X/Twitter is mandatory daily input. Scan official project/chain/exchange accounts, foundations/core developers, on-chain analysts, security teams and high-signal researchers/KOLs. Label community claims and verify material facts independently.

Reddit is mandatory daily input. Check r/CryptoCurrency, r/CryptoMarkets and relevant project/chain subreddits. Use Reddit for early narratives, user experience, arbitrage reports, security anomalies and disagreement. It is community evidence only.

## Chain ecosystem scan

Daily ecosystem scan includes Ethereum, Solana, BNB Chain, Base, Robinhood Chain, Hyperliquid, X Layer/OKX, Arbitrum, Optimism, Avalanche, Sui and Zcash.

Look for launchpads, tokenized stocks/RWA, DEX/bridges, incentives, official partnerships, NFT/inscription standards and roadmap changes.

A trend can be report-worthy even before any individual token/NFT passes a full trading-safety review. Examples include Zcash inscriptions/NFT standards, BNB Chain Genius.fun/GSTOCK, and X Layer RWA/tokenized-stock expansion.

## Whale and security scan

Escalate large public whale/smart-money events when a position/transfer or PnL is around $5M+, the holding is systemically large, or the structure can affect liquidations/market positioning. Separate on-chain confirmed facts from self-reported claims.

Security scan must include SlowMist, PeckShield, CertiK, SEAL, exchange security teams, Apple/Google security notices and high-quality security media. Cover protocol exploits plus malicious apps/extensions, supply-chain attacks, iOS/Android/macOS exploits, seed/Keychain theft and App Store/Play Store poisoning.

## Polymarket, IPO and tokenized private equity

For Polymarket and similar companies, keep separate:
- official token/TGE evidence
- IPO/equity financing and corporate preparation
- third-party SPV/tokenized private-equity exposure

A third-party Pre-Access/private-company token is not automatically the company's own token or equity. State issuer, rights, Binance Wallet/PancakeSwap/Paimon roles, and whether voting/dividend/direct claim rights exist. Any partnership or allocation inference must be labeled as inference unless directly confirmed.

## Sources

No Chinese websites.

Important items should carry short source tags in the body, such as:
来源：官方X + Binance市场数据 + Lookonchain
来源：SlowMist + Apple App Store
来源：Polymarket官方 + Binance Pre-Access FAQ + KOL X

Full URLs may be collected at the end of the GitHub report.