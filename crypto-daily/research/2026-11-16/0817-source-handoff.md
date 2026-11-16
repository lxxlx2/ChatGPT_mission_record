# 2026-11-16 08:17 Asia/Bangkok source handoff (INCOMPLETE, NOT APPROVED FOR EMAIL)
status: PARTIAL_SOURCE_GAPS
code_gate: CODE_NOT_EXECUTED
ci: CI_NOT_PROVEN
gmail_delivery: NOT_ATTEMPTED_PREBUILD
rules_sha: PIPELINE_CONTRACT=29ffbc1d32ca87a744d2990e8d55639ebb84a6f9; EDITORIAL_RULESET=2ed51528d230508ae4e0015762b1d60c9d72e299; SECURITY_SOURCE_POLICY=7266f425982aebb695c2ad4b718bf8d3d0b363bf
gmail_sent_check: 2026-11-16 date-prefix no matching formal report in search; authoritative 2026-11-15 Gmail ID 1a1dd09a9eee770f; canonical Git blob 0c93cbf68752c8dd68e42fc35c8022689d58fc9c

## §2 verified core market source
Binance official spot 24h ticker, closeTime 1794791863000 (~2026-11-16 08:17 ICT), URL https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT
BTCUSDT 64878.01, +3.257%, high 66132.01, low 62006.00, quote volume 1793849013.07 USDT.
ETHUSDT 1812.11, +4.688%, high 1845.18, low 1711.08, quote volume 740223756.61 USDT.
SOLUSDT 71.51, +3.443%, high 73.28, low 67.41, quote volume 317201422.59 USDT.
BNBUSDT 593.29, +3.631%, high 599.72, low 566.00.
HYPEUSDT 66.68, +4.728%, high 69.05, low 62.42.
Source: official Binance connector single-symbol ticker, corresponding https://api.binance.com/api/v3/ticker/24hr?symbol=ETHUSDT etc. These are rolling 24h and MUST be refreshed at 09:20.

## §5 ETF official aggregator
Farside checked 2026-11-16 ~08:17 ICT, latest complete US session 2026-11-13:
BTC ETF total -185.4 USD million; IBIT -143.5m; FBTC -41.9m. https://farside.co.uk/btc/
ETH ETF +2.3m; FETH +11.6m and Grayscale ETH -9.3m. https://farside.co.uk/eth/
SOL ETF -3.1m, FSOL -3.1m. https://farside.co.uk/sol/
These values already appeared in Nov15 delivered email. ROUTINE_NO_NEW_MARKET_DAY; may include as last completed session in §5, not a novel Top5 story.

## §9 policy/security candidate requiring prior-family comparison
Binance issuer 2026-11-12 16:54 announcement confirms completed coverage of affected assets, 2026-11-12 PoR snapshot for 198 tokens and phased withdrawal reopening; https://www.binance.com/en/support/announcement/detail/0729ad59cde74700b4eaa96c33441e71 . This predates 11-15 report and is NOT novel. Reuters 2026-11-14 reported expected restoration of remaining withdrawals by end of following week: https://www.reuters.com/legal/government/binance-targets-full-reopening-withdrawals-by-next-week-2026-11-14/ ; likely already reported in 11-15 canonical. Exclude without a verified new issuer status and previous/new field evidence.

## Outstanding before publication
Not yet verified this round: futures funding/OI, Arkham/Lookonchain original transaction IDs, issuer TGE/Early/NFT, macro official releases, six independent security source families, client message renderer security, official X, Anthropic venue access. Mark SOURCE_GAP; never claim no events. Need read latest report acceptance CR-37/38 and seven-day actual Gmail bodies for full family dedupe. No pending manifest built in this run yet; this file is a partial handoff, not an approved 13-section report.
