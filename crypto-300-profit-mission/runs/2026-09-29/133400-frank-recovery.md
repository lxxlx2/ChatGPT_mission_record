# Frank recovery audit — 2026-09-29 13:34 Asia/Bangkok

source_selected: Alchemy Solana mainnet / app mkhr4iorbgonin56
wallet: 498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ
cursor_before_signature: 35s2Y8jayg4XjASEWmNmFTAYBqbFE1G2XAc3CmVQG5zxiCZWBRcQFDmyAtvDkQn9deNJhSaxofS6NU34mDtWYtQS
cursor_before_slot: 451436899
cursor_before_time: 2026-09-29 04:15:07 Asia/Bangkok
cursor_after_signature: 5TCVznw1fF2d7Be5LMBjn1J7C8zdY2ByZNLMn3Y38Y5zKGixScuq5JXHwS2crP4zvYh6FmSYntHFadz4WXjV1Ehc
cursor_after_slot: 451550987
cursor_after_time: 2026-09-29 12:44:13 Asia/Bangkok
signatures_seen: 30
active_swaps_verified: 0
passive_or_reward_filtered: 29
failed_transactions_filtered: 1
unresolved_tx_count: 0
cursor_advanced: true
stage_result: NO_ACTION
stage_events_persisted: 0
gmail_delivery_state: none_required

## Recovery classification

All finalized signatures newer than the recovery baseline through slot 451550987 were manually replayed with Alchemy transaction inspection.

Observed non-alert activity:
- repeated third-party ATA/account creation and passive transfers where Frank was not signer;
- holder/creator fee distribution;
- repeated Frank-signed DepositToken operations, treated as fund-management/deposit actions rather than token BUY/SELL;
- one failed CreateTokenAccount transaction (MissingAccount);
- create-token-account-only transactions with no verified Frank active swap;
- tx 3bUrntKXT3dLPVaqxWB2zbYGoTwXd6thepgEjYW1U24jVgBErgd7dFMReNr6vaaZmi9wkuCLa3zZ6zW2LqgFtj2p contained a Buy instruction and credited a small token amount to a Frank-owned account, but the visible payer/authority path was third-party and there was no verified Frank quote-asset debit. It is classified as third-party/passive receipt, not a Frank active BUY.

No transaction in the recovery window met the active-swap proof requirements for PRECONFIRM or SUSPECTED_CONVICTION.

## Health conclusion

The 13:32 scheduled run correctly reported partial_failure because its own Frank audit did not persist. This manual recovery closes the historical cursor gap and establishes a current durable cursor. Future :29 runs still require their own complete Frank audit; this recovery does not waive the mandatory per-cycle health gate.
