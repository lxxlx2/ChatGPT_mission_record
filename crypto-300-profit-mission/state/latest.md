# Crypto Mission Latest State

Checked: 2026-09-24 20:30 Asia/Bangkok

Main status: RAPID_DRAWDOWN_ALERT

## PONS
- Binance live mark 0.62327697, index 0.62230057, funding +0.007852%.
- OI latest 65.328M PONS, up modestly from 64.952M in prior hourly sample. Top-trader 1h position L/S 2.2059, slightly below 2.2316 prior sample. ADL risk HIGH.
- Existing 0.625 fill is near flat. 0.585/0.545 bids and 0.498 hard stop remain valid. No PONS action trigger.

## ETH
- Binance live mark 2665.82, funding +0.007513%, OI ~2.2795M ETH, top-trader 1h position L/S 1.5758.
- Sep 25 quarterly expiry remains ahead. Strategy prohibits forced pre-expiry entry. NO_ACTION.

## JUMP / Legion
- No newly verified official final FDV, price, allocation, TGE unlock, vesting or initial circulation found this interval. Keep reserve; no sizing action.

## SHARTCOIN / kids.fun
- Authoritative recorded wallet balance remains 44,982.98 SHART unless user execution after the 18:55 signal supersedes it.
- Fresh contract-matched Pump.fun and Metaplex pages for UpBB...kids show about USD 0.00209-0.00210 and market cap about USD 2.02M-2.10M. Metaplex reports liquidity ~USD 734K, 24h volume ~USD 4.76M, mint authority disabled and freeze authority disabled.
- Prior Mission snapshot at 18:55 was USD 0.003986. Current ~USD 0.00209 implies an approximate 47.6% drawdown from that snapshot in about 1.6 hours, well beyond the >=20%/1h rapid-drawdown risk threshold in spirit and >=30%/4h threshold explicitly.
- A conflicting GMGN index currently displays USD 0.00479, so exact execution price must be checked in the user's trading venue before submitting. Pump.fun and Metaplex agree closely near USD 0.00209, giving two independent contract-matched sources for the downside event.
- ACTION: do not add. If the earlier 10,000-token 15x take-profit was NOT executed and executable venue price is near USD 0.0021, cancel the stale 15x sell instruction and protect profit: sell about 15,000 SHART now / on a weak reclaim failure, retaining the rest as runner subject to the existing 5x/3x downside rules. If the 10,000-token 15x tranche was already executed, do not duplicate it; reduce only if the remaining runner still matches the position file's failed-momentum condition.

## UNICRED / CRED
- Official public unicred.fun page is currently rendering stale/empty 0 / 4,444 data to the crawler, so it cannot be used as a reliable live state source this interval.
- Last directly verified Mission chain state remains 1,631 / 4,444 minted, 760 staked, totalWeight 2,709, #230 claimable 0.000425543372573347 ETH, known claimed + claimable 0.00129554 ETH. Exact current wallet-specific claimable rent: unavailable this interval.
- No rent-breakeven or sold-out event can be confirmed this interval. Continue hourly direct-chain attempt; do not estimate an exact new rent value without a reliable read.
- Fresh CRED price/liquidity could not be reliably re-verified from an execution-grade source in this interval; no CRED alert is asserted.

## Launch radar
- No new famous/established-brand launch candidate passed identity and quality gates this interval.

## Decision
RAPID_DRAWDOWN_ALERT on SHARTCOIN. Confirm executable UpBB...kids price in venue; if near USD 0.0021 and the earlier 15x tranche was not executed, protect profit with the position-file downside tranche rather than waiting for the stale 15x target. No new PONS, ETH, JUMP or UNICRED action confirmed.