# SHART_TAKE_PROFIT

Time: 2026-09-24 18:55 Asia/Bangkok

Asset: SHARTCOIN, tracked liquid mint `UpBBfyC75u3kxDGWmmmW2yauk9YY3CqZhdt1KUDkids`.

Trigger:
- Mission 15x target: approximately USD 0.003966.
- Fresh contract-matched Bitget Web3 indexed price: approximately USD 0.003986.
- Approx multiple versus fixed participation reference USD 0.00026437: 15.08x.
- 24h high: about USD 0.005138.
- 24h volume: about USD 6.68M.

Action:
- Sell 10,000 SHART if executable price remains around or above USD 0.003966.
- Do not add new capital.
- Recorded pre-action wallet balance is 44,982.98 SHART, so nominal post-tranche balance would be about 34,982.98 before any user-side changes.
- Continue runner management using live liquidity and the position-file trailing/downside rules.

Caveat:
- Direct Solana RPC wallet execution verification remains unavailable in this run. The UpBB mint is supported by current liquid-market indexing and Gate's on-chain listing, while the earlier GKp social-address discrepancy remains tracked.