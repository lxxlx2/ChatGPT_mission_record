# daos.world 历史发射项目参与价、峰值与达峰时间

Updated: 2026-10-05 Asia/Bangkok
Purpose: short-term launch / whitelist EV research for PaperDAO and future daos.world raises
Scope: participation price -> historical peak -> time to peak. Long-term fundamentals are intentionally secondary.

## Method

Evidence priority:
1. Historical fundraising contracts and token mints read directly from Base / HyperEVM.
2. daos.world official project/leaderboard pages and official docs.
3. Historical price aggregators where the canonical contract can be matched.

Important limitations:
- USD participation prices are approximate conversions using native-asset USD prices around the launch/raise date. The native-token cost is the stronger datum.
- Some V2 raises had tiers / adjusted contribution accounting. A weighted-average presale cost is not necessarily every wallet's exact tier price.
- Historical microcap pools are often no longer indexed. An unavailable ATH is left UNRESOLVED rather than reconstructed from unreliable current dead pools.
- ATH is not the same as opening price. Several major winners peaked days after launch.

## Quantified historical sample

| Project | Chain | Canonical token | Raise / participant supply evidence | Participation cost | Approx USD entry | Best verified historical peak | Peak multiple vs entry | Peak date / time-to-peak | Confidence |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| FDREAM | Base | `0x0521AaA7C96E25afeE79FDd4f1Bb48F008aE4eac` | 50 ETH / 1.0B contributor tokens | 0.00000005 ETH | ~$0.0001664 | ~$0.02532-$0.02538 | ~152x | 2024-12-31; Coinboom gives 15:34, ~3d13h after token launch | HIGH |
| AiSTR (old daos.world token) | Base | `0x20ef84969f6d81ff74ae4591c331858b20AD82CD` | 40 ETH / 1.0B contributor tokens | 0.00000004 ETH | ~$0.0001311 | $0.017152 | ~131x | 2024-12-31, ~8d after launch | MEDIUM-HIGH |
| ALCH | Base | `0x2b0772BEa2757624287ffc7feB92D03aeAE6F12D` | 50 ETH / 1.0B contributor tokens | 0.00000005 ETH | ~$0.0001710 | $0.003457 | ~20.2x | 2025-01-04, ~10-11d after launch | MEDIUM-HIGH |
| HSTR | HyperEVM | `0x3FA145caD2C8108A68cfc803A8e1aE246C36dF3e` | Tier-1 example reconstructed: 22 HYPE -> 4,766.66 HSTR | ~0.00461539 HYPE | ~$0.2015 using ~$43.66 HYPE | $2.48 | ~12.3x | 2025-07-26, about 1 day after presale distribution | HIGH for observed Tier-1 wallet / ATH |
| AR | Base | `0x3e43cB385A6925986e7ea0f0dcdAEc06673d4e10` | 20 ETH / 1.0B contributor tokens | 0.00000002 ETH | ~$0.00006830 | >= ~$0.0007794 observed 2025-01-14 | >= ~11.4x | reached by 2025-01-14, ~25d after launch; true ATH unresolved | MEDIUM for lower bound |
| HARD | Base | `0x3de67b963766076a3e77e4bec067460523574694` | 100 ETH / 1.0B contributor tokens | 0.00000010 ETH | ~$0.0003341 | $0.001985 | ~5.94x | 2025-01-31, ~6d after launch | MEDIUM; CoinPaprika has a lower conflicting peak |
| YT | Base | `0x387627b2bceb9ba5b476f6597727a7acf47f5b6c` | 55 ETH adjusted contributions / 900M contributor tokens | ~0.000000061111 ETH | ~$0.0001626 | $0.000398 | ~2.45x | 2025-03-05, ~15d after token mint | MEDIUM-HIGH |
| RWOK | Base | `0x06e3685982b381ab7ecb760c8fbd7d92ac368a27` | 100 ETH raw goal; 96.52723825 ETH adjusted / 800M contributor tokens | weighted avg ~0.000000120659 ETH | ~$0.0003162 weighted | UNRESOLVED | UNRESOLVED | historical ATH not reliably indexed | LOW for ATH |
| PVP | HyperEVM | `0x3Ca34A690a9622c3D191327E70e6C312b247986A` | 1,000 HYPE / 800M contributor tokens | avg 0.00000125 HYPE | approx ~$0.0000687 around launch HYPE price | UNRESOLVED | UNRESOLVED | historical ATH not reliably indexed | MEDIUM for entry / LOW for ATH |

## Chain-confirmed launch timestamps

- AR token mint: 2024-12-20 05:01:55 UTC.
- AiSTR old token mint: 2024-12-23 03:00:01 UTC.
- ALCH token mint: 2024-12-24 13:08:33 UTC.
- FDREAM token mint: 2024-12-28 02:27:13 UTC.
- HARD token mint: 2025-01-24 23:51:37 UTC.
- RWOK token mint: 2025-02-08 05:53:43 UTC.
- YT token mint: 2025-02-17 21:18:11 UTC.
- HSTR presale distribution observed: 2025-07-25 00:45:14 UTC.

## What a 0.1 ETH allocation would have looked like at the historical peak

This is a mechanical illustration assuming the same presale rate and an impossible perfect ATH exit; it is not realized PnL.

- FDREAM: 0.1 ETH -> 2,000,000 FDREAM. At ~$0.02538 ATH: ~$50,760. Launch-day 0.1 ETH was roughly $333. Gross peak multiple ~152x.
- AiSTR old: 0.1 ETH -> 2,500,000 AiSTR. At $0.017152: ~$42,880. Launch-day 0.1 ETH was roughly $328. Gross peak multiple ~131x.
- ALCH: 0.1 ETH -> 2,000,000 ALCH. At $0.003457: ~$6,914. Launch-day 0.1 ETH was roughly $342. Gross peak multiple ~20.2x.
- AR: 0.1 ETH -> 5,000,000 AR. At the independently documented 2025-01-14 price implied by $857.29K / 1.1B supply: ~$3,897. This is a lower-bound historical observation, not verified ATH.
- HARD: 0.1 ETH -> 1,000,000 HARD. At $0.001985: ~$1,985. Launch-day 0.1 ETH was roughly $334. Gross peak multiple ~5.94x.
- YT: using weighted-average raise rate, 0.1 ETH -> ~1,636,364 YT. At $0.000398: ~$651. Launch-date 0.1 ETH was roughly $266. Gross peak multiple ~2.45x.

## HSTR later-cycle example

HSTR is useful because it tests whether the extraordinary first-wave Base returns repeated on HyperEVM.

Direct chain reconstruction:
- HSTR total supply: 1,000,000.
- Official tokenomics allocate 650,000 HSTR to daos.world presale.
- PVP treasury sent 22 native HYPE into the presale and subsequently received 4,766.66 HSTR.
- Observed Tier-1 effective cost = 22 / 4,766.66 = ~0.00461539 HYPE/HSTR.
- HYPE historical price around that entry date was about $43.66, giving ~US$0.2015/HSTR.
- HSTR recorded ATH = $2.48 on 2025-07-26.
- Observed Tier-1 peak multiple = ~12.3x.
- Presale distribution occurred 2025-07-25 00:45 UTC, so the dated ATH was reached roughly one day after distribution.

This is a much more relevant later-cycle analogue than assuming every new daos.world launch repeats FDREAM/AiSTR.

## Interpretation for the claim “previous projects opened 40-50x”

NOT SUPPORTED as a platform-wide historical rule.

The verified record is strongly right-skewed:
- FDREAM and old AiSTR were exceptional ~130-150x peak outcomes.
- ALCH was ~20x.
- HSTR observed Tier-1 was ~12x.
- AR had a documented >=11x level, but exact ATH is unresolved.
- HARD was ~6x using the higher cross-tracker ATH.
- YT was ~2.45x.
- RWOK and PVP do not currently have sufficiently reliable historical ATH data to force into the ranking.

Most importantly, several large multiples were not opening prints:
- FDREAM peak: ~3.5 days after launch.
- AiSTR: ~8 days.
- ALCH: ~10-11 days.
- HARD: ~6 days.
- YT: ~15 days.
- HSTR: ~1 day after presale distribution.

Therefore “40-50x at open” conflates a few first-wave ATHs with opening performance.

## Projects still missing a defensible full entry-to-ATH reconstruction

Official daos.world leaderboard also contains BBL, MONARK, ATLAS, TRIAL, GG and SHINOBI. They are not assigned a made-up ROI here because one or more of the following are missing from reliable historical sources:
- canonical presale tier / accepted amount,
- contributor token amount,
- liquid historical pool data,
- trustworthy historical ATH indexed against the canonical token.

BBL is a particularly bad example for using today's DEX quote: its surviving Raydium pool has only a few dollars of liquidity and produces nonsensical multi-billion-dollar apparent FDV. That cannot be used as historical peak evidence.

## Sources

First-party / chain:
- https://daos.world/leaderboard
- https://daos.world/
- https://docs.daos.world/technical-details-base
- historical Base / HyperEVM fundraising contracts and token mint transactions read directly through RPC/indexed chain data.

Historical price corroboration:
- FDREAM: https://www.coingecko.com/en/coins/fdream and https://coinboom.net/coin/dr3am-fund
- old AiSTR canonical CA: https://blockspot.io/coin/aicrostrategy/
- ALCH: https://coinpaprika.com/coin/alch1-alchemist-accelerate/
- HARD: https://coincheckup.com/coins/hardwaire-dao/about and https://coindataflow.com/en/currency/hardwaire-dao
- YT: https://coinpaprika.com/coin/yt3-yaptrade/
- HSTR: https://www.coingecko.com/en/coins/hyperstrategy
- AR dated market snapshot: https://www.gate.com/learn/articles/ar-revolutionizing-decentralized-finance-with-alameda-research-2-0/6871

## Decision-useful takeaway

For future daos.world whitelists, the historical edge is concentrated in getting the presale allocation before public price discovery. The first Base wave produced two extreme 100x+ peak outliers, but later quantifiable launches have generally compressed into low-double-digit or single-digit peak multiples. Do not use “old projects did 40-50x” as a base-case assumption. For PaperDAO, model several cases rather than one heroic historical multiple.