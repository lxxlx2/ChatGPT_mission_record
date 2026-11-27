# Frank buy USD evidence (local, read-only)

The Dashboard can read a trusted operator's `frank-buy-usd-evidence.json` from its existing control directory. The file is optional. Do not commit it, raw responses, or wallet data. The reader does not call an exchange or affect signal/delivery rules. Keep the existing version 1 `records` for exact trade-bound evidence unchanged.

Version 2 keeps the same `records` and adds `captures`. Each capture contains:

- `asset`: `SOL`, `USDC`, or `USDT`. WSOL is only treated as SOL when the signed trade's quote proof already normalizes it to SOL.
- `block_time`: integer Unix seconds, used to select the exact UTC second of the admitted buy.
- `source_url`: the actual Kraken Spot PostTrade request URL, matching the exact asset/USD and one-second interval returned by `mission_agent.signals.historical_usd_tick.capture_url(asset, block_time)`.
- `raw_base64` and `source_sha256`: standard Base64 and lowercase SHA-256 of the same locally retained unmodified response bytes.

Record only genuine complete responses. The hash checks consistency, not exchange authenticity; the operator remains responsible for provenance. Do not pass private wallet/transaction identifiers to an exchange. One observation can serve signed buys in the same asset and second, but is used only for an admitted buy with attributable payment. Empty, saturated, mismatched, duplicate or disagreeing captures are not priced. Neither nearby ticks nor a stablecoin peg is a fallback. The entire file remains capped at 4 MiB. Use a private file and publish a replacement atomically if updating live staging.

The exact USD fields remain null for market conversions. The UI marks the separate estimate with ≈ and describes it as a same-second payment-asset estimate, not a USD fill. No captures are supplied by default. This path does not demonstrate real source availability or coverage for any historical window.
