# Frank Wallet Live Cursor

Updated: 2026-09-29 12:45 Asia/Bangkok
Target: `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`

- state: RECOVERY_REQUIRED
- source_primary: Alchemy Solana mainnet
- app_id: `mkhr4iorbgonin56`
- baseline_signature: `35s2Y8jayg4XjASEWmNmFTAYBqbFE1G2XAc3CmVQG5zxiCZWBRcQFDmyAtvDkQn9deNJhSaxofS6NU34mDtWYtQS`
- baseline_slot: 451436899
- baseline_block_time: 2026-09-29 04:15:07 Asia/Bangkok
- last_successfully_processed_signature: none
- last_successfully_processed_slot: none
- cursor_advanced: false
- reason: two-stage live rules activated around 04:20; first successful recovery run must replay all finalized signatures newer than the baseline before advancing.

Latest manual source health check:
- finalized signature retrieval: PASS
- latest observed signature at check: `5TCVznw1fF2d7Be5LMBjn1J7C8zdY2ByZNLMn3Y38Y5zKGixScuq5JXHwS2crP4zvYh6FmSYntHFadz4WXjV1Ehc`
- latest observed slot: 451550987
- latest observed block time: 2026-09-29 12:44:13 Asia/Bangkok
- recent signatures include passive third-party ATA creation, confirming the need for active-swap filtering.

Cursor rule: any UNRESOLVED_TX/error gap blocks cursor advancement past that point.