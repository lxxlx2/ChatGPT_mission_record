# Crypto Daily Unified Pipeline Specification

Last updated: 2026-09-22
Status: canonical
Timezone: Asia/Bangkok

## 1. Purpose

This directory is the canonical operating record for one unified Crypto intelligence automation.

The unified automation has two execution modes inside the same hourly task:

1. Hourly research mode: collect incremental market intelligence and save it internally.
2. 09:00 formal report mode: perform one final refresh, read the prior 24 hours of research, build the formal daily report, send one Gmail message, and archive the exact same report body in GitHub.

There must not be a separate hourly collector automation and a separate daily report automation after this migration.

## 2. Scheduling and idempotency

The single automation runs every hour on the hour in Asia/Bangkok.

On every run:
- determine the current Asia/Bangkok local date and hour;
- perform the hourly research scan;
- write exactly one research file for that run;
- write exactly one run-audit file for that run;
- remain silent to the user unless the formal 09:00 report or a permitted correction is actually sent.

At 09:00 Asia/Bangkok:
- first finish the 09:00 hourly research refresh;
- read all research files covering at least the previous 24 hours, including both the current and previous local date where needed;
- re-verify all material facts using fresh sources;
- generate the formal daily report;
- send exactly one normal daily report by Gmail;
- archive the same final body in GitHub;
- read back both Gmail and GitHub and verify them before marking success.

Idempotency rule:
- before sending, check whether the current date already has an official report with a Gmail message ID;
- if an official report already exists, do not send another normal daily report;
- a correction is allowed only for a material factual error or a missed highest-priority event;
- internal scan improvements, formatting preferences, or ordinary new information after the cutoff do not justify a second normal report.

## 3. Storage layout

Hourly research:
`crypto-daily/research/YYYY-MM-DD/HHMMSS.md`

Hourly execution audit:
`crypto-daily/runs/YYYY-MM-DD/HHMMSS.md`

Formal daily report:
`crypto-daily/reports/daily/YYYY/YYYY-MM/YYYY-MM-DD.md`

Formal monthly report:
`crypto-daily/reports/monthly/YYYY/YYYY-MM.md`

Incident and migration records:
`crypto-daily/incidents/`

Every hourly run must produce a run-audit file, including runs with `no_material_update`. The research file may be very short when there is no material update.

## 4. Source policy

Do not use Chinese-language websites as evidence.

Prioritize:
- official project, protocol, exchange, foundation, regulator, central-bank and company sources;
- official chain explorers and verifiable on-chain data;
- primary market data;
- Reuters, Bloomberg, WSJ, FT, The Block, Blockworks and other high-quality English sources when primary evidence is unavailable or needs context;
- English X/Twitter and Reddit as mandatory discovery and sentiment inputs.

Community and KOL content is evidence of discussion, sentiment or a lead. Material factual claims must be independently verified when possible.

Prediction-market data may be used as a market signal. Keep it separate from official confirmation.

## 5. Hourly research mode

Each hourly run scans for incremental information with potential decision value. Do not generate a second user-facing report.

Mandatory scan categories:
- mature crypto market moves and persistent trends;
- spot, derivatives, OI, funding, basis, liquidations and volume when available;
- major whale, exchange inflow/outflow and smart-money changes;
- cross-platform and cross-chain price differences;
- major protocol, governance, roadmap and ecosystem changes;
- airdrop, points, TGE, ICO/public sale, unlock and claim events;
- security incidents, malicious apps, wallet risks and exploit developments;
- Polymarket and other relevant prediction markets;
- IPO, pre-IPO, SPV, tokenized private-equity and RWA structures;
- NFT, digital-art, open-edition, mint, claim and X-native distribution events;
- global macro and geopolitical developments that materially affect crypto.

### 5.1 X/Twitter

Every run must scan English X/Twitter.

At minimum cover:
- official project, chain and exchange accounts;
- foundations and core developers;
- on-chain analysts such as Lookonchain, Onchain Lens, Arkham and Nansen when accessible;
- security teams such as SlowMist, PeckShield, CertiK and SEAL;
- high-signal researchers, market participants and KOLs.

### 5.2 Reddit

Every run must scan Reddit.

At minimum check:
- r/CryptoCurrency;
- r/CryptoMarkets;
- relevant project or chain subreddits for current material candidates.

Use Reddit for early narratives, user experience, arbitrage reports, security anomalies, sentiment and disagreement. Do not treat it as primary factual proof.

### 5.3 NFT and digital-art social heat

Every run must explicitly scan NFT, digital art, open editions, mints, claims and drops on X.

Seed creators and ecosystems include Jack Butcher / Visualize Value, 6529, Beeple, DeeZe, OSF, Art Blocks, OpenSea, Foundation, Manifold and Zora. Expand through quote, repost and reply networks when useful.

Record an NFT or digital-art event as a material candidate when any one of the following is true:
- a verified or established creator launches a new open edition, mint, claim or drop;
- within roughly six hours the post reaches about 100k views, 500 likes, 100 reposts or 100 replies;
- at least five independent high-signal NFT/Crypto accounts discuss or repost it within a short window;
- the event uses a new distribution or payment rail such as X Money, Farcaster, Base, Robinhood, wallets or payment systems;
- it has a short and explicit participation deadline;
- an established project or creator launches a new series closely related to a historically important work.

A missing collection contract is not a reason to ignore a rapidly spreading event. Contract, collection, mint safety and official-domain checks become mandatory before giving any actionable mint or trading link.

### 5.4 Mature-market trend discovery

Do not depend on a manually named watchlist.

Scan major CEX assets, high-liquidity CoinGecko/CoinMarketCap assets, and major perpetual markets such as Hyperliquid. Check available 24h, 3d/5d, 7d and 30d windows.

Escalate an asset into the persistent-trend candidate pool when any of these is true:
- roughly plus or minus 5% in 24h;
- roughly plus or minus 15% to 20% in 7d;
- roughly plus or minus 30% in 30d;
- clear relative strength or weakness versus BTC/ETH for at least three days;
- a new 30d, 90d, all-time high or all-time low;
- material volume expansion;
- unusual OI, funding, basis or liquidation behavior;
- persistent ETF, institutional or on-chain flows;
- a material protocol, regulatory, listing or upgrade catalyst.

Candidates such as ZEC, HYPE or UNI must be discovered by the scan when they qualify. They must not depend on the user naming them first.

### 5.5 Cause research

Do not stop after writing that no credible explanation was found.

For every significant mature-asset move inspect:
1. official X, blog, governance and docs;
2. exchange listing, delisting or campaign announcements;
3. spot volume and cross-exchange pricing;
4. perpetual OI, funding, basis and liquidations;
5. on-chain transfers, exchange flows and whale positions;
6. Polymarket and other relevant real-money prediction markets;
7. English X from teams, researchers, KOLs, market makers and on-chain analysts;
8. Reddit project communities plus r/CryptoCurrency and r/CryptoMarkets;
9. high-quality English media.

If no single cause is confirmed, record confirmed factors, on-chain clues, X/Reddit hypotheses, counterarguments and evidence strength.

### 5.6 Cross-platform and cross-chain scan

Scan the same asset across major CEX, DEX and chains, including Ethereum, Arbitrum, Base, BNB Chain, Solana, Robinhood Chain, Hyperliquid, X Layer/OKX, Avalanche, Sui, Optimism and other relevant transparent ecosystems.

If an executable spread is around 2% or more, or carry/LP/bridge economics are abnormal, calculate when possible:
- buy price;
- sell price;
- executable depth;
- gas;
- slippage;
- bridge fees;
- withdrawal restrictions;
- bridge or challenge time;
- fast-bridge liquidity;
- capital lock time;
- net return;
- annualized return;
- convergence risk;
- practical capacity.

### 5.7 Chain ecosystem scan

At minimum scan Ethereum, Solana, BNB Chain, Base, Robinhood Chain, Hyperliquid, X Layer/OKX, Arbitrum, Optimism, Avalanche, Sui and Zcash.

Look for launchpads, tokenized stocks/RWA, DEX and bridge changes, incentives, official partnerships, NFT or inscription standards, and roadmap changes.

### 5.8 Whale and security scan

Escalate large public whale or smart-money events when:
- a position or transfer is roughly $5M or more;
- PnL is roughly $5M or more;
- the holding is systemically large;
- the structure can affect liquidation or market positioning.

Separate on-chain confirmed facts from wallet attribution and self-reported claims.

Security scanning must cover:
- protocol exploits;
- malicious mobile or desktop apps;
- browser extensions;
- supply-chain attacks;
- iOS, Android and macOS vulnerabilities;
- seed phrase or Keychain theft;
- App Store or Play Store poisoning;
- exchange and wallet security advisories.

## 6. Hourly research file format

Each material candidate should include, when applicable:
- discovery time;
- topic or asset;
- why it may matter;
- confirmed facts;
- current market, on-chain and derivatives data;
- official sources;
- X source or signal;
- Reddit source or signal;
- prediction-market signal;
- counterevidence;
- unresolved verification items;
- suggested formal-report chapter.

If nothing material changed, write a short `no_material_update` research file.

Do not send Gmail from hourly research mode.

## 7. Formal daily report

Only one normal report is sent each day at 09:00 Asia/Bangkok.

The report must be decision-oriented. It should prioritize:
- what is newly important today;
- which persistent trends strengthened or weakened;
- which opportunities or risks are verifiable;
- what should be watched next.

Do not write a chronological news dump.

### 7.1 Fixed 13-section structure

The exact first-level section names and order are:

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

Do not rename, merge, remove or reorder these sections.

Chapter items use full-width numbering `（1）（2）（3）`. Deeper levels use `①②③` or bullet points.

### 7.2 Persistent-trend chapter

Chapter 3 explains major mature-market moves and the research behind them.

Chapter 12 converts persistent trends into a decision-oriented watchlist.

For each Chapter 12 candidate include, when data exists:
- 24h, 7d and 30d trend;
- volume;
- OI, funding and liquidations;
- spot versus derivatives direction;
- whale and exchange flows;
- official catalyst;
- X/KOL view;
- Reddit view;
- counterevidence;
- invalidation conditions;
- next 1 to 7 day price, on-chain or event checkpoints.

### 7.3 User-visible content rules

Internal rules, QA, scan methodology, classification explanations, GitHub status, missing-data process notes and correction mechanics belong only in run audits.

The report body must not contain process text such as:
- 分类自检：通过
- 序号自检：通过
- CA与链接QA：通过
- 本节仅收……
- 本期正式入选0个
- long explanations for why a section is empty

If a section has no decision-relevant update, use at most one short line.

Every user-visible paragraph should answer at least one of:
- what happened;
- why it matters;
- how price or capital reacted;
- what to watch next;
- what actionable opportunity or risk exists.

## 8. Polymarket, IPO and tokenized private equity

For Polymarket and similar companies, keep separate:
- official token or TGE evidence;
- IPO, equity financing and corporate preparation;
- third-party SPV or tokenized private-equity exposure.

A third-party pre-access or private-company token does not automatically represent the company’s own token or direct equity. State issuer, economic rights, voting or dividend rights, redemption or claim mechanics, and platform roles when known.

Any partnership or allocation inference must be labeled as inference unless directly confirmed.

## 9. Source presentation

Important user-visible items should carry concise source tags, for example:
- 来源：官方X + Binance市场数据 + Lookonchain
- 来源：SlowMist + Apple
- 来源：Polymarket官方 + Binance Pre-Access FAQ + KOL X

Do not use Chinese websites.

The Gmail body and the GitHub formal-report body must be identical. Full URL collections that would make the email unreadable should remain in hourly research or run-audit files.

## 10. Gmail and GitHub synchronization

Formal daily Gmail:
- recipient: `lxx.run688@gmail.com`;
- format: text/plain;
- one normal daily email only.

Daily report YAML must include at least:
- report_type;
- report_date;
- timezone;
- email_subject;
- gmail_message_id;
- gmail_sent_at;
- automation_id;
- status.

After Gmail sending:
- read back the actual sent message;
- verify recipient, subject, all 13 section headings and visible numbering.

After GitHub writing:
- read back the formal report;
- verify YAML metadata, all 13 section headings, numbering and body equality with the Gmail final body.

Only after both readbacks pass may the 09:00 run be marked success.

## 11. Run audit

Every hourly run writes `crypto-daily/runs/YYYY-MM-DD/HHMMSS.md`.

At minimum record:
- run_time;
- automation_id;
- run_mode: hourly_research or daily_report;
- run_status;
- sources_scanned;
- x_scanned;
- reddit_scanned;
- market_universe or material candidates;
- trend_candidates;
- cross_chain_spread_scan;
- prediction_markets_scanned;
- chain_ecosystems_scanned;
- security_feeds_scanned;
- whale_scan;
- cause_research;
- research_file_path;
- daily_report_attempted;
- qa_performed;
- qa_issues_found;
- qa_corrections;
- numbering_self_check;
- structure_self_check;
- gmail_attempted;
- gmail_sent;
- gmail_subject;
- gmail_message_id;
- gmail_error;
- github_report_path;
- gmail_readback_verification;
- github_readback_verification;
- superseded_message_id when applicable;
- tool errors.

At non-09:00 hours set `daily_report_attempted: false`, `gmail_attempted: false`, and keep the user-facing run silent.

## 12. Correction policy

A second email is allowed only when the already-sent report contains:
- a material factual error;
- a materially wrong source attribution;
- a major structural failure that changes meaning;
- a missed highest-priority market, security or eligibility event.

A correction must:
- clearly identify itself as a correction;
- supersede the prior Gmail message ID in GitHub metadata;
- preserve an audit trail;
- never hide the previous error by deleting the historical record.

## 13. Monthly report

On the first day of each month, the 09:00 run also prepares the previous calendar month’s long-term investment report.

Archive:
`crypto-daily/reports/monthly/YYYY/YYYY-MM.md`

The monthly report should cover:
- long-term core opportunities;
- growth satellite positions;
- high-risk small-position or event-driven ideas;
- assets or projects waiting for better entry conditions;
- primary-market, ICO or IPO opportunities;
- items to continue watching;
- items to avoid or downgrade.

Include valuation or price context, 1 to 5 year thesis, 6 to 12 month catalysts, key risks, invalidation conditions, preferred entry conditions and position role.

## 14. Migration and historical records

Research and reports created before 2026-09-22 remain historical records and should not be rewritten merely to match newer structure rules.

Known legacy reports may contain older section names or internal QA text. Record such differences in migration or incident audits. Apply this specification prospectively from the unified automation migration.

The current canonical operating rule from 2026-09-22 onward is one hourly unified automation with one 09:00 formal report stage.
