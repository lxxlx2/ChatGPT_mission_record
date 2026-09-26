# PONS Position

Updated: 2026-09-26 13:00 Asia/Bangkok

## Authoritative current state

The prior deep resting entries are canceled.

### Binance PONSUSDT perpetual — USER_CONFIRMED

Source: user screenshot at 2026-09-26 12:58 Asia/Bangkok.

- direction: LONG
- mode: isolated 3x
- entry: **0.6250**
- current position notional shown: **41.32 USDT**
- margin shown: **13.20 USDT**
- mark shown: **0.6451307**
- unrealized PnL shown: **+1.31 USDT**
- ROI shown: **+9.58%**
- realized PnL shown: **-0.13 USDT**
- liquidation price shown: **0.4293629**
- hard stop remains: **0.4980 Mark Price**
- take-profit: none shown
- current-orders tab shows 1 order, consistent with the displayed 0.4980 stop

### Canceled orders — USER_CONFIRMED

The old averaging bids are no longer active:
- **0.5850 canceled**
- **0.5450 canceled**

Reason supplied by user: price did not retrace to those levels and the user did not want the remaining capital sitting idle.

Do not reopen, recreate or treat these two orders as pending unless the user explicitly sets them again.

## Robinhood Chain spot sleeve — DIRECT_CHAIN

Fresh Alchemy read at about 2026-09-26 13:00 Asia/Bangkok.

Canonical PONS:
- contract: `0x39dbed3a2bd333467115de45665cc57f813c4571`
- token metadata: name Pons, symbol PONS, 18 decimals
- wallet balance: **54.799953441979625 PONS**
- Alchemy price: **0.6448796581 USD/PONS**
- spot mark value: **~35.34 USD**

Robinhood Chain native gas:
- **0.000826657957256326 ETH**
- ETH reference price: **2684.44 USD**
- gas-wallet mark value: **~2.22 USD**

The user confirms that the capital released by canceling the remaining Binance orders was withdrawn and converted into PONS spot plus gas.

The Robinhood Chain swap leg is now directly reconstructed from transaction logs at 2026-09-26 12:58:38 Asia/Bangkok:
- input: **35.291194 USDG**
- output: **54.799953441979625 PONS**
- reconstructed spot acquisition rate: **~0.64400044 USDG/PONS**

This establishes the PONS spot token cost basis for that swap leg. Any separate withdrawal fee and the native-ETH gas acquisition cost remain outside this PONS-token cost basis unless independently reconstructed.

## PONS sleeve accounting

The original PONS sleeve began as a **50 USDT** budget. It is no longer a "50 USDT futures-margin budget."

Current components:
- Binance futures margin: **13.20 USDT** USER_CONFIRMED
- Robinhood spot PONS mark value: **~35.34 USD** DIRECT_CHAIN + market price
- Robinhood native gas mark value: **~2.22 USD** DIRECT_CHAIN + ETH price

Gross current component value is about **50.76 USD-equivalent**, before exact fee/cost-basis reconciliation.

This figure is not PnL.

## Monitoring rules

Hourly Mission monitoring must now check:

1. Binance public PONS market data against the existing futures position:
   - stored entry 0.6250
   - hard stop 0.4980
   - liquidation reference 0.4293629
   - meaningful rapid-move / leverage / funding / OI changes

2. Robinhood Chain DIRECT_CHAIN:
   - canonical PONS balance
   - PONS price/value
   - native ETH gas balance
   - material unexpected wallet delta

3. Do **not** monitor 0.5850 or 0.5450 as live orders. They are historical canceled orders.

4. Do not create a new averaging order, target, leverage change or capital reallocation automatically.

5. Private Binance futures quantity/PnL/order state remains USER_CONFIRMED until a newer screenshot or connected account source is available.

## Alerts

Send a factual alert when a stored threshold is crossed, a material security/liquidity event occurs, or the direct-chain PONS/gas balance changes unexpectedly.

Unchanged ordinary price movement stays silent.
