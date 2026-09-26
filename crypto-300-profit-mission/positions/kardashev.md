# KARDASHEV position

Updated: 2026-09-26 16:13+ Asia/Bangkok

## Identity

- Name: Kardashev Research
- Symbol: KARDASHEV
- Solana Token-2022 mint: `5wW9mhbwq1HTFh341iimpmrqBB4mfxdXiYhdYBL7hUnp`
- Primary wallet: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`

## Current chain state

DIRECT_CHAIN snapshot:
- current supply: **984,707,322.903859**
- mint authority: revoked
- freeze authority: revoked
- metadata update authority: revoked
- wallet KARDASHEV balance: **4,103.186501**
- wallet USDC: **266.559188**
- wallet native SOL: **0.129098090**

PumpSwap pool owner:
`3QaH1ifhQgUXHQdX3DHi9oMrWzTQfKLcomoCyeRRLMh6`

Latest observed PumpSwap reserves:
- KARDASHEV: **37,037,133.881128**
- SOL: **583.816843184**

Using SOL ~120.84 USD only as a contemporaneous market reference:
- implied KARDASHEV price: **~0.0019048 USD**
- implied market cap: **~1.876M USD**
- remaining wallet position value: **~7.82 USD**

These price/MC values are snapshots and must be refreshed before any future trade decision.

## User trade reconstruction

### Entry

Transaction:
`3X9RBfcz3MuxwEh7HmrZv38ZmjLU2e2GRnoqZoMBZWcRuyas5xKYbXz3mG411q4a3XsFzo8bv4yaMoAyxbMvS1Fd`

Time:
2026-09-26 15:38:19 Asia/Bangkok

Observed route:
- **19.9 USDC** swap input
- **0.1 USDC** route/platform fee
- total USDC capital used: **20.0 USDC**
- initial KARDASHEV acquired, reconstructed from later sales + current balance: **18,794.553778**
- approximate USDC-only average entry: **0.00106414 USD**
- Solana network fee: **0.000855001 SOL**

### Profit taking

1. 2026-09-26 15:51:03
   - tx: `42pzPRuPFDw8kTPgxiHjr3MeQsDZKGHD8kMnArmwgtED6SmNvZ38ZuMmnDg8KbEf9pkRQoiwTG9yx5vJ8toDEDW5`
   - sold: **11,500 KARDASHEV**
   - gross routed SOL output observed: **0.172433804 SOL**
   - network fee: **0.000203051 SOL**

2. 2026-09-26 15:58:31
   - tx: `276yqa4hESC9xRWiSSkizMPSMa5cRXaZ3ti3emkcrwBE9K6ta1TWQqr5qgG8PL6tTfmwqNb5iNZrw9wnRJmxgJZP`
   - sold: **1,823.638444 KARDASHEV**
   - gross routed SOL output observed across the route: **~0.034140742 SOL**
   - network fee: **0.000210204 SOL**

3. 2026-09-26 16:13:15
   - tx: `3B1UjRXfPeWYMxiL2eD6MYejZq85fDJLpHupEP9X6B1pntV2uYv1PEkyeDiQjUS1YYm5ZTRBJTnyNafoiwpzR8Qj`
   - sold: **1,367.728833 KARDASHEV**
   - gross routed SOL output observed: **0.038477213 SOL**
   - network fee: **0.000049851 SOL**

Totals:
- sold: **14,691.367277 KARDASHEV**
- remaining: **4,103.186501 KARDASHEV**
- sold fraction of initial position: **~78.17%**
- gross routed proceeds observed: **~0.245051759 SOL**
- total network fees across entry + three exits: **~0.001318107 SOL**

At SOL ~120.84 USD:
- gross realized proceeds reference: **~29.61 USD**
- original USDC capital: **20.00 USD**
- principal has already been recovered
- gross cash recovered above original capital: **~9.61 USD**
- proportional realized trading PnL before network fees: **~+13.98 USD**
- remaining position reference value: **~7.82 USD**
- total position PnL reference after the listed network fees: **~+17.27 USD**, about **+86%** on the original 20 USD

PnL uses a contemporaneous SOL/USD reference and is therefore an estimate. The chain quantities and transaction signatures are authoritative; future accounting should refresh SOL/USD or use actual conversion transactions when available.

## Risk / thesis notes

### Confirmed positives
- Token-2022 mint/freeze/metadata authorities are revoked.
- Current PumpSwap quote reserve has grown versus the earlier research snapshot, showing real SOL demand during the move.
- Initial 20 USDC principal has already been recovered; the remaining 4,103.186501 tokens can be treated as a profit-position from a capital-at-risk perspective.

### Confirmed red flag
Creator:
`CALQ1EwjARtaW6FW6KQDZj4jhye9Vt4NvTzFwmg4JHqC`

The creator-controlled KARDASHEV token account was observed selling two lots of **67,882,099.177197 KARDASHEV** shortly after launch, about **135.764M / 13.58% of initial supply** in total. Current creator KARDASHEV balance is 0.

This materially lowers trust in the project and means the remaining position should be managed as a high-volatility narrative/momentum trade, not a high-conviction long-term fundamental position.

### Narrative
Primary narrative is the recent Kardashev / K2 civilization theme, including renewed attention after Elon Musk discussed K2-scale civilization. No verified corporate, research-institute, Musk, SpaceX or other official affiliation has been established.

## Position handling

Current status: **PRINCIPAL_RECOVERED / PROFIT_POSITION**

Do not add size automatically.

Future decision priority:
1. refresh PumpSwap SOL reserve and KARDASHEV reserve;
2. inspect top external holders for coordinated transfers into pools;
3. watch whether creator/related addresses reacquire and distribute;
4. only then use price/MC levels.

A sharp rise in KARDASHEV reserve together with a large drop in SOL reserve is a direct exit-risk signal.
