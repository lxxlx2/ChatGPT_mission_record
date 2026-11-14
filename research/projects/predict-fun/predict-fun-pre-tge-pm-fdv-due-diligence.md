# Predict.fun — pre-TGE PP, Polymarket FDV odds, Aspecta, cash-flow and participation constraints


## 2026-11-15 ~02:32 Bangkok: revised Binance Alpha TGE, live premarket and PM mismatch, opening spot trade NO_GO now

**Status:** `TGE_SCHEDULED_2026-11-18_16:00_BKK / BINANCE_ALPHA_CONFIRMED / BINANCE_MAIN_SPOT_RESCHEDULE_UNVERIFIED / PREMARKET_PERP_LIVE / POST_LAUNCH_FLOAT_UNVERIFIED / WATCH_NO_TRADE`. Research only; no orders, wallets, alerts or automations created. This newer update supersedes the 2026-10-28 statement that there was no known revised TGE date; the Oct 30 delay and Oct 27 security incident remain relevant.

### Primary launch and premarket evidence

- **Binance Wallet official, English:** https://www.binance.com/en-AE/square/profile/binancewallet (verified issuer account; mirrored in https://www.binance.com/en/square/post/11-12-2026-predict-token-generation-event-to-resume-november-18-387389618874833 ) states PREDICT TGE will resume on **2026-11-18 09:00 UTC = Wednesday Nov 18 16:00 Asia/Bangkok**. Prime Sale Key users can check token balance and **trade on Binance Alpha** at launch if event executes. This is a *scheduled official exchange announcement*; it does not confirm that a separate Binance main-board PREDICTUSDT spot pair has resumed. Binance's English Oct30 spot listing postponement remained the most concrete listing-change record observed: https://www.binance.com/en-PH/support/announcement/detail/eb1fb9e5f41f43b682332aff0b7b89ce . On 2026-11-15, direct Binance spot price API `PREDICTUSDT` returned **invalid symbol (-1121)**, independent of Alpha's planned listing. Issuer's canonical onchain token CA, audited vesting, actual initial transfers/LP/liquid float still **not confirmed in this research**.
- **Binance original Futures pre-market announcement** https://www.binance.com/en/support/announcement/detail/5ef55cf8358e4a48b2512a156e89c8e5 confirms USDⓈ-M `PREDICTUSDT` 5x max pre-market perp since Oct25, official total planned supply 1,000,000,000, **mark price method driven by recent perp prints**, no live spot anchor before TGE. Binance direct API snapshot **2026-11-14 19:30 UTC / Nov 15 ~02:30 Bangkok**: last prices `1.0598–1.0644 USDT`, best bid `1.0584`, ask `~1.0604–1.0605` with small best-level quantities (18 tokens on bid, 6 token on earliest ask), aggregated deeper orders not static execution certainty. 24h open `0.9982`, last `1.0644`, change **+6.632%**, high `1.0788`, low `0.9275`; rolling 24h volume `$2,959,467.24 USDT`, 103,919 reported trades. Open interest **5,521,638 PREDICT** roughly `$5.88M` at $1.064, hourlies rose ~5.1M -> ~5.5M units during past day; new speculative positions are accumulating but direction of actual net taker aggressor cannot be inferred from OI alone. Funding history `0.00005 = +0.005%` each four-hour interval; under this special pre-market rate cap, do not infer robust long demand.
- **Primary Aspecta premarket UI** https://trade.aspecta.ai/ displayed `Predict (V3 Pool)` **~$1.01B FDV**, about **$738.6K** pool notional in listing; a separate displayed row `Predict.fun` **$346.15M FDV with 0% movement**. These are two distinct market products/possibly stale pools; **do not average, conflate or present as a single price**. No authoritative 1:1 token or full redeemable spot parity was established. The Binance official derivative and V3 pool broadly align near $1B, but do not prove opening spot price.

### Required project-specific PM, direct Polymarket first party

- https://polymarket.com/event/predictfun-fdv-above-one-day-after-launch, indexed market snapshot fetched on **Nov 15**: cumulative event volume **~$9.45M**, threshold YES **>$500M 89%, >$600M 85%, >$800M 69%, >$1B 43%, >$1.5B 21%, >$2B 10%**. Bid/ask cards for key thresholds `>$1B Buy Yes 43.9¢ / Buy No 57.2¢`, `>$800M Buy Yes 70¢ / Buy No 32¢`; these are indicative taker prices, not necessarily full-size depth. Market rule: token must actually be publicly transferable/tradable; **FDV is measured at 4pm ET on the calendar day AFTER launch**, using the most liquid price source, not an opening 1-minute top tick; if never launched by Dec31 2027 market resolves NO. Probabilities may also include launch/delay risk and manipulation/market microstructure risk. These live odds are sharply less optimistic than the **Oct28 source snapshot >$1B 84%**. Direct archived opening returned an older three-month crawl with contradictory levels; use the freshest dated search-indexed snapshot rather than that stale archival response.
- Mandatory scan outcomes: project-specific Polymarket market FOUND, no more confidence imported from same-ticker unrelated pools. Kalshi, Limitless and Predict.fun native direct counterpart not newly verified in this pass; keep as no independent confirmed venue rather than invent odds.

### Project business and fundamentals update

- DefiLlama original https://defillama.com/protocol/predict-fun recent indexed snapshot **Nov 14**: TVL around **$11.2M** (time-dependent subpages show ~$10.75m daily / ~$11.2m live), 30-day **gross fees ~$7.9M**, **retained protocol revenue ~$2.08M**, DEX volume **~$393.4M**, notional DEX volume **~$775.8M** (different measures, do not add). 30d retained-revenue run-rate `$2.08M*12 ~= $24.96M/year` **IF sustained**. At Binance pre-market `$1.06B FDV`, `FDV / current annualized run-rate ~= 42.5×`. This is NOT token-holder revenue, audited profit or proven future growth; fee refunds/rebates remain large. 2026-10-28 research had net retained ~$1.99M, so growth by current 30d window is modest relative to large $1B valuation.
- Persistent security red flag: Oct27 approx **$400K** users' unauthorized transfers as recorded in first-party/independent October research and DeFiLlama incident registry. **Completed refunds or independently audited root-cause postmortem still unverified** as of this pass. Do not omit this in investment analysis.
- Planned supply **1B**, issuer stated **16%=160M nominal TGE unlocked** (initial-circulation mechanics not onchain verified), Season1 first tranche **7%=70M** with options reported **35% immediate or 100% linear 12 months**, early supporters 26.05%, team 10% locked 24-month cliff +36-month vest per issuer statements; original metadata allocation discrepancy (Ecosystem 50.95% vs 51.95%, liquidity 5% vs 4%) still requires first-party primary doc proof. 160M at $1.06 ~**$169.6M** nominal initial float valuation if fully traded, potentially material relative to <$3M/day premarket derivatives volume. **Not all nominal unlocked tokens equal immediately sellable tokens**. Do not equate TGE unlock with actual selling.
- Macro observed same-time direct Binance spot: **BTC ~$65,576 -4.977%/24h**, **ETH ~$1,830 -6.084%**, **BNB ~$589.46 -7.527%**; CMC composite **crypto marketcap -5.22%/24h, -13.3%/7d, Fear & Greed 15, total derivatives OI -8.93%/24h**. PREDICT perp **+6.63%/24h** is a contrary speculative/divergence signal (possible hype/positioning; no attribution proved). AP Nov13 Fri US indexes **S&P 500 -0.4%, Nasdaq -0.9%**; crypto selloff worsened over weekend. Coinbase institutional Nov13 report attributes macro weakness to hotter inflation/jobs, perceived Fed hawkishness and stablecoin contraction `$11.5B/30d` (analyst estimate, not independent central bank data). https://www.coinbase.com/institutional/research-insights/research/weekly-market-commentary/weekly-2026-11-13

### Decision / conditional spot opening trade (not executed)

- **WATCH, NO BUY before TGE; opening market order at ~$1.06 equivalent FDV is not supported**. The binding spot venue is Alpha 2026-11-18 16:00 Bangkok if schedule holds; current futures mark cannot guarantee spot/opening executable prices or a scalp. PM prices only 43% for `>$1B` **at the next-day close**, incompatible with unqualified expectation of a clean uptrend when starting near $1.06B; 21% for `>$1.5B`.
- **Scenario arithmetic** from an illustrative $1.06 entry, before fees/slippage: sell at $1.20 = +13.21%, $1.25 = +17.92%; loss at $0.90 = -15.09%, $0.80 = -24.53%. At +13.2 upside / -15.1 downside, realized success rate must exceed ~53.4% before fees/price gap to have positive payoff even if exits always fill. No evidence that this scalp has such a win rate; taking a high-price opening market order is adverse selection in thin launch order books.
- **Conditional observation setup, NOT predicted safe buy level:** if opening spot price is **$0.80–0.90 or lower** after a sharp first selloff, re-evaluate only with live exact CA, 5–15 minute stabilized higher lows, actual buy-side 0.5%-2% depth, realistic $100/$300/$1000 order impact, filled spot volume and major-wallet net transfers. If immediate price is at or above ~$1.00 and the tape is extended, prefer skip. These are heuristic zones anchored to ~$800–900M FDV and Polymarket threshold probabilities, **not backtested signals or promised profits**.
- Entry invalidation if program permissions/vesting/CA unresolved, CEX/Alpha trading suspended again, thin/wide order book, high sell impact, top-wallet unlock transfers, BTC/BNB new lows or breaks of local stabilized base. Do not send transactions, create new monitoring, place orders or deploy any production strategy. Any future actual buy/sell requires user-specific explicit trade authorization and real-time quote.
- User position UNKNOWN/NOT CONFIRMED; no PREDICT holdings assumed. Current mission `PRODUCTION_TRADING=NO_GO`.

### Sources & method reminders

- [Binance premarket perp rules](https://www.binance.com/en/support/announcement/detail/5ef55cf8358e4a48b2512a156e89c8e5)
- [Binance Wallet issuer launch post](https://www.binance.com/en-AE/square/profile/binancewallet)
- [Binance original paused spot announcement](https://www.binance.com/en-PH/support/announcement/detail/eb1fb9e5f41f43b682332aff0b7b89ce)
- [Polymarket project-specific FDV thresholds](https://polymarket.com/event/predictfun-fdv-above-one-day-after-launch)
- [Aspecta own live premarket table](https://trade.aspecta.ai/)
- [DefiLlama project fee/revenue and exploit history](https://defillama.com/protocol/predict-fun)
- [Binance direct query results described above are read-only app tool observations, not a static stored external API URL or current guaranteed quote]

---

Updated: 2026-10-28 Asia/Bangkok (Oct17 historical snapshot retained below as dated history; new Oct28 tokenomics and incidents override it).
Authority: `crypto-300-profit-mission/PROJECT_ANALYSIS_FRAMEWORK.md`, `token_trading_principles.md`, `PROJECT_ANALYSIS_EVIDENCE_WORKFLOW.md`, `MISSION_SPEC.md`.
Type: `BNB_CHAIN_PREDICTION_MARKET / PREDICT_TOKENOMICS_PUBLISHED / S1_SNAPSHOT_DONE / TOKEN_CONTRACT_AND_TGE_UNVERIFIED / BINANCE_WALLET_PRE_TGE_CONFIRMED`.
Maturity: `LEVEL_4_VERIFIABLE_ONCHAIN_MARKET_VOLUME_REVENUE / BUSINESS_CASH_FLOW_ACCRUES_TO_TOKEN_UNCONFIRMED`.
User status: **NO USER TOKEN OWNERSHIP OR PLATFORM PP BALANCE ESTABLISHED**; do not invent position.
Execution: `RESEARCH_ONLY / NO_TRADE / NO_AUTOMATION / NO_PRODUCTION_DEPLOY`.

## 2026-10-28 $PREDICT issuer tokenomics, Season 1 choice, Binance Prime Sale, incident and live PM

**Review time:** 2026-10-28 Asia/Bangkok afternoon. **This dated update supersedes Oct17 'token unconfirmed' statements below.** Research only: no wallet action, no paid purchase, no automated monitoring. **Issuer original:** https://x.com/predictdotfun/status/2115328311752868024 . Direct `x.com` web reader returns HTTP 403; corroborating issuer/account posts via publicly readable https://www.sotwe.com/predictdotfun and source-linked Oct28 English reports. **CA, final official original infographic/document and token contract source not fetched; do not claim direct original tweet text was audited**.

### Confirmed broadly corroborated newly issued token rules (announced, not yet mainnet-verified)

- `$PREDICT`, **1,000,000,000 hard-supply tokenomics plan**; TGE **16% = 160m nominally unlocked**, but *currently live ERC20 contract, actual deployed initial float, mint authority, circulating supply, onchain proof and spot liquidity unverified*.
- **Season 1 points snapshot completed** on **2026-10-27** per original @predictdotfun post directly mirrored with text at https://www.sotwe.com/predictdotfun ; **Season 2 PP already active**. For S2 liquidity PP, maker points split between resting quoted orders and actually filled orders; low/no fills get zero fill-based PP. This PP mechanic is separate from any specific snapshot/airdrop allocation rate.
- First season user distribution: **7% of supply = 70m PREDICT**, drawn from ecosystem/community tranche; individual S1 PP->PREDICT conversion, final eligible PP denominator, anti-Sybil bonus/penalty, user wallet's allocation and claim contract **NOT YET VERIFIED**. Official claims S1 final PP amounts and **claim date will be announced within 24h of Oct28 announcement**; that is announcement of a future claim date, NOT a proof claims are open now.
- **Beneficiary must select within one month of claim opening** or reported eligibility **forfeited** (per Oct28 CoinNess English https://coinness.com/en/news/77756 ; independently secondhand until exact official terms are read). Two alternatives: **A: take 35% of nominal individual entitlement immediately, forgo rest**; **B: receive 100% of nominal entitlement under 12-month linear vesting**. Exact linear vesting start, cliff/first installment, one-time choice immutability, smart contract code and unclaimed-forfeiture destination not available. Decision formula if fair immediate token price `P0` and weighted actually monetizable next-12m price `P_future`: B beats A before discount/fees when `P_future > 0.35*P0`. Large incentive to choose B in token units, but 12-month price/dilution/default risk; neither universally better. **No personal PP balance proven in repo**, so no user-specific payout claim.
- **Investor+insider supply:** Early supporters **26.05% (260.5m)**, core contributors **10% (100m)**, **TGE 0 for both**, issuer plan **24-month cliff then 36-month monthly vest**; treasury **8% (80m)**. Full release plan ~5 years. Need independent vesting contracts, admin controls and full 16% TGE tranche reconciliation.
- **MATERIAL CONFLICT IN 2 SOURCES:** Lookonchain original-source-linked English feed https://lookonchain.com/feeds/79067 reports **50.95% Ecosystem/Community (509.5m) and 5% Liquidity (50m)**. RootData https://www.rootdata.com/news/805005 and CoinNess https://coinness.com/en/news/77756 report **51.95% Ecosystem/Community (519.5m) and 4% Liquidity (40m)**. Both sum to exactly 100% when combined with common investor 26.05%, team 10%, treasury 8%, **so one full percentage point/10m tokens materially disputed**. NEVER present either as primary verified until original tokenomics illustration / doc is read. 70m Season 1 is consistent on both.
- **No verified public spot token mint/CA, final token standard, audited distributor, contract locked holders or LP**. Platform is on BNB Chain; cannot automatically infer token will deploy BNB on the exact same token contract prior to issuer disclosure. Any `$PREDICT` ticker on an explorer remains impersonation risk until authoritatively linked.

### Binance Wallet Pre-TGE Prime Sale: official launch notice ≠ spot token listing

- Predict issuer's new original account post as directly quoted on public account index https://www.sotwe.com/predictdotfun : `We're excited to announce that $PREDICT will be featured in the Pre-TGE Prime Sale on @BinanceWallet! October 29, 2026, 08:00–10:00 UTC ... Event Portal ... soon.`
- Binance Wallet original issuer account post mirrored on same page: `Join the Pre-TGE Prime Sale Edition ... 08:00–10:00 (UTC) on October 29, 2026 ... Eligible users need Binance Alpha Points ... details and Event Portal will be released soon.`
- **Exact Bangkok: Thursday Oct29 2026 15:00–17:00**. This is a two-hour **SUBSCRIPTION WINDOW**, not immediate TGE or sell liquidity.
- Binance Wallet first-party generic Pre-TGE mechanics https://www.binance.com/en-AE/learn/binance-alpha-events : qualified Alpha Points, contribution token per project, a max-wallet funding amount, oversubscription **pro-rata actual accepted allocation**, remainder contribution refund, token lock until official TGE; **specific PREDICT sale price, USDT/BNB funding currency, Alpha-Point minimum/deduction, cap, accepted raise, per-wallet deposit maximum, oversubscription refund clock and actual unlock = UNPUBLISHED AT REVIEW**. Historical default 3 BNB/10–15 Alpha Points KOL estimates are NOT project terms and must not be used. Binance Futures PREDICTUSDT premarket **perpetual derivatives** announcement Oct25 https://www.binance.com/en/support/announcement/list/0000000000000000000048 is NOT a transferable PREDICT spot listing and does not settle a PM TGE event.

### Measurable operating business updated; distinguish fees from net revenue

- Independent sourced DefiLlama dynamically read on Oct28 2026 https://defillama.com/protocol/predict-fun : **TVL $10.17m**, **30-day gross trading fees $7.98m**, **30-day protocol retained revenue $1.99m** (explicitly after refunds, maker rebates, referral distributions; ~24.9% of gross fees), **7-day revenue $625,668**, **24h revenue $66,556**, **30-day DEX swap volume $401.29m**, **30-day notional volume $797.12m**. Those volume series have distinct definitions and are NOT additive. **30d run-rate $1.99m * 12 = $23.88m / year ONLY if sustained; not audited earnings or guaranteed token cash flows**. TVL is collateral in settled markets, not pure treasury cash. Apr2 investor YZi Labs / Susquehanna as prior documented; invested amount/token price and employee cost still unknown.
- Previous Oct17 dynamic snapshot ~$12.09m TVL, ~$6.73m gross fees and ~$1.56m retained revenue; dates differ. Current shows ~higher last-30d fees/revenue but lower TVL, **not proof of sustained organic paid-customer cohort growth**, maker subsidy reduction or profitability. Need unique active payers/whales/wash-adjusted trades/retention and audited user rebates.

### SECURITY INCIDENT IS MATERIAL AND STILL OPEN

- On **Oct27 2026**, issuer publicly stated **approximately $400,000 USDT** moved without authorization from a small set of user wallets; third-party-hosted API documentation potentially compromised, **preliminary unproven causal attribution**; official promised reimbursement and future postmortem. Direct issuer account text from https://www.sotwe.com/predictdotfun , independent English media https://crypto.news/predict-fun-400000-usdt-theft-refunds/ .
- **Independent forensic trace** https://www.bitquery.io/investigations/predict-fun-hack traced **29 compromised wallets, 397,708 USDT**, two transaction waves Oct22 and Oct27, signed via owner's keys, **no Predict.fun core trading contracts called in 33 drained transfers**. Bitquery says one wallet was drained post-official announcement, and trail includes 166.8 ETH into Tornado Cash. This establishes malicious wallet ownership/key compromise in observed transactions, NOT independently proven leaked-source (docs) root cause. **No evidence actual reimbursements complete.** Production security posture, user key export/approval and whether compromised docs access still dangerous must be evaluated before signing/depositing; no user action initiated.

### Required independent prediction-market read: ACTIVE

- Direct https://polymarket.com/event/predictfun-fdv-above-one-day-after-launch read on **2026-10-28** current web view: parent cumulative volume **$7,871,264**, price threshold YES displayed `>$500m 97%`, `>$800m 91%`, `>$1bn 84%`, `>$1.5bn 51%`, `>$2bn 35%`, `>$2.5bn 18%`, `>$3bn 12%`. These are market displayed percentages, not equal to best executable YES buys; e.g. `>$1bn Buy Yes 86.5c / Buy No 19.5c`; `>$1.5bn Buy Yes 60.8c / Buy No 58.5c` indicative very wide spread/low execution reliability; need actual order book depth per threshold. Market rules are **FDV at 4pm ET on day after token actually publicly launches**, not TGE announcement or Binance Wallet Pre-TGE presale window; unresolved if no launch before Dec31 2027. Price/FDV thresholds imply token unit prices with 1bn supply: `$500m FDV -> $0.50; $1bn->$1.00; $1.5bn->$1.50; $2bn->$2.00`, not live cash token quote.
- Direct https://polymarket.com/event/will-predictfun-launch-a-token-by read Oct28: `by 2026-10-31 85% YES` (`Buy Yes 87c`, cumulative market event volume ~$969,978); `by 2026-11-30 99%`. Announcement, Pre-TGE derivative or locked sale tokens do not count until a transferable token trades per market resolution.
- Polymarket Oct17 repo old odds `>$1bn 43%, >$2bn 21%` are **STALE and superseded**, not a reason to claim current 43%. Difference at Oct28 `84%,35%` is sharp repricing, BUT do not assert it was caused exclusively by today’s issuer tokenomics without an order-book historical timeline. Kalshi, Limitless and Predict.fun native indexed project-specific counterpart not verified. Polymarket is the directly verified project-specific PM.

### Decision & unknown gates

- **Status:** `TOKENOMICS_PUBLISHED / S1_AIRDROP_70M_CONFIRMED_BY_MULTIPLE / S1_SNAPSHOT_CLOSED / CLAIM_DATE_PENDING / PREDICT_ALPHA_PRESALE_OCT29_TIME_CONFIRMED / TGE_AND_SPOT_CA_UNVERIFIED / SECURITY_INCIDENT_OPEN / WATCH_NO_TRADE`.
- Research prioritization: (1) resolve issuer primary allocation infographic conflict and full 16% TGE liquid float; (2) check first official S1 final PP and individual eligibility/amount (user unknown) + date and true one-month selection deadline; (3) obtain issuer / Binance Wallet sale portal and **PREDICT-specific** subscription contract, price and accept cap; (4) verify actual audited BNB token, mint control, vesting, locked sale and LP; (5) track security postmortem and real reimbursements before any wallet action; (6) read PM updated bid/ask depth at user decision time.
- This update is **not** an instruction to bypass source-specific transaction restrictions or buy any asset. No wallet-signature, payment, Gmail, automated monitor, token movement or claim executed.

---

## 1. The KOL thesis

User uploaded @MysticXBT post quoting @0xzhaozhao on 2026-10-17 and @predictdotfun, says:
- 5亿人民币? **NO**: Chinese crypto FDV shorthand `5亿 FDV` generally denotes **$500M USD FDV** in this context; currency is NOT printed explicitly in user screenshot, so treat the assumed USD as **contextual inference**, not verbatim fiat unit.
- $500M FDV 'sell house and all-in'; $1B 'heavy buying'; $2B 'high odds to double'; $4B 'wait'.
- Another comment touts NeoSoul (unrelated), and Predict.fun as a token participation idea. KOL owns unspecified inventory and has not published trackable executed positions or probabilities; hypotheses, not approval or authority.
- Four thresholds: **500 million / 1 billion / 2 billion / 4 billion USD FDV**; distinguish circulating MC vs FDV vs share/equity valuation.

## 2. Canonical identity and team, legal

- **Official application** https://predict.fun and X https://x.com/predictdotfun; chain **BNB Chain**, prior small Blast deployment from predecessor/historical protocols in DefiLlama; execution is hybrid off-chain order book and on-chain settlement.
- **Operator first-party Terms** https://docs.predict.fun/terms-of-service: **PDF Labs Limited**. Founder called **Ding** in investment firm's first-party statement, commonly `dingaling` / @dingalingts. Earlier employer/creator bios found on secondary sources only; do NOT claim independently confirmed specific prior Binance job/title or founder role at PancakeSwap without matching first-party corporate evidence.
- Official developer documentation https://docs.predict.fun/developers/technical-overview: signed EIP712 off-chain CLOB with on-chain `CTFExchange`/ERC1155 conditional tokens, wrapped USDT, optional Venus yield, UMA/Chainlink resolution infrastructure.
- **REAL GEO BLOCKER**: original service terms updated 2025-11-18 https://docs.predict.fun/terms-of-service prohibit trading for people residing in / physically located in **Thailand** (among other listed jurisdictions), including via VPN. Applies to USER CURRENT BANGKOK CONTEXT. Prohibited/close-only risk. This is a **first-party contractual eligibility exclusion**, and independent local law question remains separate. Do not recommend account trading, Binance-linked Predict event market trading, farming PP, or VPN workaround while restriction applies. Binance portal integration does not automatically exempt Thailand.
- No official token contract, canonical ticker/CA, chain, token total supply, team allocation, airdrop PP conversion ratio, TGE date, unlock/claim schedule, eligible geography or vesting verified as of research. Avoid identifying speculative premarket `V3_Predict` derivative as spot token.

## 3. Funding and partnerships

**Investor first-party statement** YZi Labs 2026-04-02: https://www.yzilabs.com/blog/yzi-labs-doubles-down-on-predict-fun-with-susquehanna-crypto-following-easy-residency-season-2. Confirmed:
- incubated at YZi Labs EASY Residency Season 2;
- strategic follow-on round backed by **YZi Labs and Susquehanna Crypto**. Amount, token vs equity split, investment valuation, investor liquid token cost, side letters, vesting **not disclosed**. Never project investment discount off funding logo.
- Susquehanna strategic market-making/liquidity support, with direct proof of 2026-07-07 launched negotiated block trading for 100,000+ shares: https://predict.fun/pt/news/predict-fun-delivers-streamlined-on-chain-block-trading-platform-for-prediction-markets
- Platform's 2026-03-04 **acquisition of Probable**, per first-party https://predict.fun/ru/news/predict-fun-completes-strategic-acquisition-of-probable ; independent post-acquisition integrated users/volume retention unverified.
- Official Binance Wallet integration 2026-04-09 https://predict.fun/pt/news/powered-by-predict-bringing-prediction-markets-to-binance-wallet and 2026-06-02 first-party Predict Points in Binance Wallet https://predict.fun/id/news/earn-predict-points-directly-via-the-binance-and-binance-wallet-apps.
- Integration != Binance invested equity or Binance token listing; do not infer either.

## 4. Product and business metrics (DefiLlama public methodology, snapshot fetched 2026-10-17, dynamic)

Source: https://defillama.com/protocol/predict-fun and https://investors.defillama.com/protocol/predict-fun?events=false&revenue=true&tvl=false
- **TVL ~$12.09M**, BSC $12.05M + Blast ~$36k; DefiLlama latest displayed TVL series for Oct 17 ~$11.37M, conflicting within the same dynamic page. Preserve time/aggregation discrepancy, do not silently take as single exact same-time fact.
- **Last-30d DEX swap volume ~$338.84M**, **notional trade volume ~$673.79M**, different DefiLlama definitions and not additive.
- **Last-30d gross trading fees ~$6.73M**, **net protocol revenue after refunds, maker rebates and referral ~$1.56M**. Difference ~$5.17M and net retention **~23.2%**. Net protocol revenue is NOT token-holder distributions, audited profit or cash that holders may claim.
- Daily 24h gross fees ~$273,967; retained ~$69,683 at read. Metric volatility and wash/incentive risks significant.
- **Monthly gross ~6.73M vs net ~1.56M** implies currently substantial cost/rebate burden; if incentives fade, volume may fall. Retain rates after growth unknown.
- Naive current net annualization **$18.72M (1.56×12)**. Illustrative FDV/net-revenue multiples at $500M/$1B/$2B/$4B = **26.7× / 53.4× / 106.8× / 213.7×**. This is **NOT P/E nor equity claim nor future-token yield**. DeFiLlama separately shows trailing-year annualized from lower past volume (~$9.47M); do not conflate 30d run-rate vs trailing-year.
- 2026-04-02 issuer claimed 130k+ users, 4m orders and $1.8B cumulative matched volume; independently verified unique human users, wash-adjusted share, maker IDs and cohorts not established. More recent DeFiLlama cumulative ~$7.19B notional/$3.46B DEX swap volume have different scopes; not contradictory if distinct methodologies/times.
- Product edges: off-chain book with on-chain settlement, sponsored gas, USDT collateral earning yield via Venus, UMA oracle conditional outcomes; Chainlink price markets, bulk/off-chain negotiated trades. Predict's yield https://docs.predict.fun/the-basics/yields has **10% management fee** on yield and dependence on Venus liquidity/utilization.
- Smart-contract audits index https://docs.predict.fun/developers/audits includes Cyfrin Chainlink PDF and reports on UMA/Venus; no independent full finding-to-current-deployment reconciliation; audits not a universal clean bill.
- Mainnet product at **L4**. Some observed retained trading revenue supports commercial activity but not a verified standalone net profit or direct token value capture.

## 5. Competitors and sector regime

- **Opinion (OPN)** has actual traded token already, as of 2026-10-17 DefiLlama https://investors.defillama.com/protocol/opinion: ~$3.06M TVL, ~$42,942 last-30d fees, displayed spot OPN ~$0.053 and **~$52.83M FDV** with ~182.72M circulating, 1B total. Early speculative ATH ~$0.46 Mar 5 and presently ~88.6% lower. Comparing OPN token FDV to Predict eventual FDV requires controlling **huge revenue gap, tokenomics, cycle, token value rights, post-listing selloff**; counterexample for airdrop/post-listing sustainability, not reliable one-to-one multiple.
- **Kalshi and Polymarket** operate with much larger recognized ecosystems/volume and different regulatory distribution, on/offchain product models; public private-equity valuations (e.g. >$10B) ARE NOT directly comparable to Predict token FDV (different legal claims, cash rights, float).
- Strong reputational/regulatory risk: 2026-10-12 Reuters poll public skepticism on event contract betting; 2026-10-16 WIRED flags possible circular volume/activity farming on third-party prediction markets. These sources do **not** prove Predict.fun wash trades, only demonstrate why volume should be adjusted and why regulatory limits matter.

## 6. Official Predict Points (PP) / TGE uncertainty

First-party docs: https://docs.predict.fun/the-basics/how-to-earn-points and fee docs https://docs.predict.fun/the-basics/predict-fees-and-limits
- PP issued weekly, majority to bona fide liquidity providers with real bid/ask orders close to mid, satisfying minimum order, spread, live order-book snapshots; some to normal trades/positions.
- Anti-abuse: spoofing, cancel abuse, balance manipulation may result in **all points reset to zero**.
- 2026-06 official Binance integration gave **3,299,336.61 PP retroactively** to eligible users. These are reward points, **not USD, not a confirmed airdrop**.
- As of Oct 17 docs no formal PP/token exchange ratio, snapshot date, allocation pool, TGE, claim or guaranteed token rights; public 2026-10-06 `Soon` with possible P token is a teaser not enough to establish specifics (independent reports).
- official maker fee 0; taker fee up to 2% depending on share pricing (e.g. 100 contracts at 50c costs $50 + $1 fee). Platform risk of market PnL and collateral lock, more significant than gas.
- **Bangkok restriction makes PP trading inadvisable/ineligible under Terms, independent of profitability.** Research-only exploration okay.

## 7. Prediction market (Polymarket) FIRST-PARTY odds and event settlement

Direct public event (snapshot taken 2026-10-17): https://polymarket.com/event/predictfun-fdv-above-one-day-after-launch .
- Parent nested FDV threshold event, cumulative displayed volume **~$7.045M** across event at source read. Separate strikes have total cumulative volume ~$0.30M–$1.2M; do NOT interpret event cumulative volume as depth or available exit size.
- Threshold $400M YES **85%** (~86c ask), $500M **79%**, $600M **70%**, $800M **54%**, $1B **43%**, $1.5B **26%**, $2B **21%**. Quotes are independent and can have bid/ask mismatch; exact expected FDV distribution not recoverable without normalized current order books.
- `>500M` implies 79% Yes by PM participants (with no-token-by-deadline risk embedded); `>1B` 43%; `>2B` 21%. Under monotonic/cross-market consistency assumptions, rough implied bins: <=500M 21%, 500M–1B 36%, 1B–2B 22%, >2B 21%. This is **not an objective forecast or arbitrage-free probability PDF**; avoid using thin-tail 4B chance invented. $4B event not listed, so **P(>4B) <= P(>2B) ~21%**, with no direct actionable quote for >4B.
- Definition: Predict.fun **governance token**, publicly transferable/tradable; measured **4pm ET on calendar day following token launch** using the most liquid market, **not token ICO pricing, not opening minute peak, not a 30-day average**. If no token launched by **Dec 31, 2027 at 11:59pm ET** => NO. Supports time-based outcome uncertainty.
- There are secondary cached odds variations as low as <500M threshold near 45% to as high 83% across earlier read dates; true rapidly changing sentiment, do not silently blend snapshots.
- Not separately verified a Predict.fun-native PM market for its own token listing FDV with sufficient independent depth; major data from Polymarket is external.

## 8. Aspecta premarket pricing / risks

Market: https://trade.aspecta.ai/projects/usdt/V3_Predict shows a recent fetch snapshot **synthetic $8.4073 per key / $840.73M headline implied FDV**, ~-5.32% 24h, cumulative V3 volume ~$220,999. Price not guaranteed current at user execution time. The `$840.73M` comes from premarket synthetic convention and **cannot be used to derive official token supply, CA or upcoming circulating MC**.
- At $840.73M synthetic entry reference, $500M realized FDV ratio -> **-40.53%**; $1B -> **+18.94%**; $2B -> **+137.89%**; $4B -> **+375.77%** (a simplified same-supply price comparison ignoring collateral, fees, loss of basis, actual settlement/coin delivery).
- Crucial primary terms https://docs.aspecta.ai/premarket-v3/asset-settlement : long users may receive **native tokens or USDT compensation**, depending on shorts delivering; **full token delivery not guaranteed**, plus collateral allocation and funding/settlement fees. https://docs.aspecta.ai/premarket-v3/trade documents V3 stages and ADL. https://docs.aspecta.ai/premarket-v3/fees-and-benefits : maker ~1%, taker ~1.25%, potential additional long-settlement ~2%, varying per instrument. Verify exact Predict project rules before any hypothetical trade; do NOT call it spot or tradable official token.
- The market is thin relative to a $840M headline FDV; even modest order book size may strongly move quote. *Real tradable value* contingent on premarket keys, actual settlement. No position purchased.
- Aspecta's own legal/geographic terms need separate review and in no way override Predict's Thai restriction.

## 9. Fundamental valuation and why KOL's 500M/1B/2B/4B is not actionable

Using net 30d run rate $1.56M x 12 = **$18.72M** (optimistic persistence, not trailing audited income):
| Hypothetical token FDV | FDV / 30d-net-revenue-run-rate | relative to Aspecta $840.73M key-based pricing | Perspective |
| $500M | 26.7× | −40.5% | research watchlist only; still needs token shareholder rights and dilute supply |
| $1B | 53.4× | +18.9% | short-term TGE upside vs quoted synthetic premkt insufficient for 'all-in' |
| $2B | 106.8× | +137.9% | high-growth/sentiment condition needed |
| $4B | 213.7× | +375.8% | extreme token valuation, unsupported by present holder cashflows |

Scenarios are price ratios only; true return depends on **acquisition cost, float, unlocked share, trading fees, pool depth, market maker inventories, vesting, airdrop sell pressure and actual rights**.
- At hypothetical **10% initial circulating**, $500M/$1B/$2B/$4B FDV imply $50M/$100M/$200M/$400M circulating MC. At 25%, $125M/$250M/$500M/$1B. Neither 10% nor 25% is announced! Do not present as real initial float.
- Hypothetical upside for an actual future airdrop must be written in terms of the official token allocation (q) and total token supply (S): `value = q/S × FDV` before fees/unlock, with `q,S` **UNKNOWN**. No user PP wallet evidence, no dollar prediction.
- Outcome threshold betting implied probability is **market odds**, not guarantees and no independent distribution of the author's own $1B/$2B trade return.
- The main issue is not whether project is real; it clearly has active business. **Issue is whether token holders get economics** and how much immediately free-float supply / FDV valuation there is. Funding investors may hold equity/warrants with rights different from token holders.

## 10. Decision and go/no-go

**Current research gate: WATCH / NO_GO for platform PP farming or transaction from Thailand; NO_GO to aggressive Aspecta premarket token-equivalent pricing.**
Reasons ranked:
1. Explicit Thailand ban in official ToS. User physically based in Bangkok; this is decisive for platform trading today.
2. No official tokenomics/TGE/CA/claim/PP rights despite teaser; no confirmed token unit price or unlock.
3. Synthetic premarket $840.73M and PM >$1B around 43%, >$2B around 21%, with high delivery/counterparty risk.
4. Net revenue retaining ~$1.56M/month but costs/refunds ~$5.17M/month; profitability and sustainability with weaker incentive volumes uncertain.
5. First-party strategic investors/real integrations make project worth retaining in pre-TGE research queue, not evidence of safe token ROI.
6. Early holder class, token investor effective cost, liquidity/lockups unresolved.
7. Competing distribution/challenging regulation.

Retain information on upcoming issuer token allocation/claim and actual change only. **Do not create or modify tasks, alerts, automations, Gmail, launchd, trades, wallet actions, existing production rules or user conversation title.**

## 11. Evidence gaps / next manual diligence

- Official first-party token total supply, distribution/vesting, token contract identity and audit, allocation rights, claims, TGE date, chain/venue.
- Historical organic volume/unique active humans, bot/wash-adjusted 7/30d, weekly TVL net inflows, true market maker concentration, user retention and fee/rebate sources.
- Corporate capital raise amount, formal round valuation, token SAFT vs equity and price, founders verified legal identity.
- Verify issuer official GitHub linkage to live deployed contracts; docs mention runtime but no Git repo + contract deploy admin ownership independently tied in this research. Audit-to-deployed-bytecode review pending.
- Fresh Polymarket threshold bids/asks/market depth, turnover; fresh Aspecta key/USDT liquidity and share delivery ratio when TGE known.
- Thailand lawful ability to trade permitted exchanges/instruments distinct from restricted Predict.fun platform eligibility; first-party rules must be checked at any future participation request.
