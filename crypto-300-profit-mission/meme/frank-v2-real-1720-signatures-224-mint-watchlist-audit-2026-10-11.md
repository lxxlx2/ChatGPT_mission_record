# Frank V2 — 2026-10-11 14:24 Bangkok real transfer-evidence acceptance and watchlist correction

Source: user Mac packet `frank-v2-transfer-evidence-20261011-142445.zip`
Packet SHA256: `552474f2899225e2376945b1e017ba97f40dd341bf59878c7b0a0c2c6eb4615b`
Mac report `as_of_utc=2026-10-11T07:24:45+00:00`
Release: `RESEARCH_BRANCH_ONLY / MAC_NEW_UI_NOT_DEPLOYED / INDEPENDENT_AI_REVIEW_NOT_DONE`

## Actual source integrity, independent Git readback

ZIP has **42 entries, CRC PASS**, with a Frank transfer-history manifest and **12** part JSON files. All 12 part byte sizes and SHA256 hashes match their manifest, and concatenating their base64 chunks yields SHA256 **`1cda7a289db31582f24d327c7dedd911c14475912346e1c4ff6e731a4f56a96a`**. The user packet says `git_sync=SYNC_OK`, `transfer_git_sync=SYNC_OK`, `transfer_pending=0`.

**Independently verified remote Git:** branch `evidence/frank-ca-local` at `b9fb6e6df9032a0e6f49c1274bb4ba61c9e4c2da` contains **all 13/13 exact corresponding transfer archive Git blob SHA1 values**, as re-computed locally from original ZIP member bytes. The upload is actually present; there is no need for a repeat upload of these bytes. The archive source paths are under `crypto-300-profit-mission/meme/local-evidence/frank-transfer-history/1cda7a289db31582f24d327c7dedd911c14475912346e1c4ff6e731a4f56a96a.json` and corresponding `<snapshot_id>/part-0000.json` … `part-0011.json`. This verifies Git *archive storage*, **not** full-chain wallet history.

## Critical data accuracy findings

Reconstructing the source yielded **1,720 normalized Frank signature records**. Local classifications: `PASSIVE_TRANSFER=1,393`, `ACTIVE_TRADE=78`, `ATA_CREATE=81`, `FAILED_TX=98`, `UNKNOWN_NEEDS_REVIEW=70`.

1. **224 distinct token mints** occur in the wallet-owned `token_balance_deltas`, yet the previous trader/model-only watchlist contained **33 mints**. Of the **191** new mint observations, **104** have positive *passive-receipt-classified wallet token deltas*; the remaining **87** have other account activity or zero-only deltas. These extra mints are **not** 191 verified current holdings, priced assets, or actionable BUY candidates. Some may be dust/unsolicited transfers.
2. **Zero of 1,720** normalized signatures contain a nonempty `wallet_token_transfer_flows` list. Nonetheless **1,454** signature records include wallet-owned token-account delta rows, **1,370** have nonzero token-account delta, and **1,259 of 1,393** classified passive transfers show a nonzero owned-token delta. The instruction-level sender/destination information is **not present in this normalized archive**. No algorithm should invent counterparties or economic acquisition costs from token amounts alone. The parser has a code path to extract parsed token instructions; whether earlier RPC responses lacked those instructions, or mapping/coverage failed, remains **not confirmed**. This is a real parser/provider coverage gap, not proof that no transfers happened.
3. **J7 case:** local normalized signature evidence includes `3opgLQn1…`, passive received **2,846,838.050235** J7, plus `Tk5zC6cZ…` signed SALE of **12,508,217.470763** J7. Two other previously independently verified finalized inbound transfers (10/9 UTC 00:31:43 and 00:32:14) totaling **9,661,379.420528 J7** are **not in the 1,720-row local archive**. This is direct proof that the locally exported signature universe is historically incomplete even for a *known, in-window token*. Original three-transfer on-chain proof is `meme/evidence/frank-v2-j7-onchain-three-transfer-origin-2026-10-11.json` in Draft PR #31. All three transfers were signed by the external sender; this still does not establish the sender's acquisition cost or Frank's realized PnL.
4. **BPxx case:** all four locally recognized Frank-signed market sales are present and show token balance decreases; the previously independently verified earlier million-token holding is **not reproduced as an original acquisition record**. Therefore the huge nominal USDC sale receipts cannot become a PnL number.

### Product correction implemented on isolated PR #31

- `local-agent/mission_agent/mission_control/wallet_watch.py`: now joins all locally normalized **wallet-owned token-account balance deltas** into the trader/model observed universe. Each mint retains original trade/model semantics when applicable, and stores last signature, receipt/send/zero-event counts and source provenance. Raw token quantities are only historical indexed observations, **not current live wallet balances**.
- Default UI `Frank 持续观察池` shows the original trade/model research candidates; additional filters expose `PASSIVE_RECEIPT_ONLY`, `OTHER_ACCOUNT_ACTIVITY` and `ALL` with independent source labels. This prevents unsolicited dust from drowning actionable research while allowing the complete locally observed universe to be audited.
- `local-agent/mission_agent/mission_control/evidence_sync.py` now whitelists the activity/source fields in existing Git Frank poll archives, keeping all 224 current observed rows (within the explicit 300-row evidence cap). Sync truncation status remains explicit for larger future universes.
- `local-agent/mission_agent/mission_control/wallet_transfers.py`: every signature now explicitly states whether parsed counterparties exist. The real user's source requires `BALANCE_DELTA_ONLY_COUNTERPARTY_UNRESOLVED` for relevant passive transactions; no fake sender owner claim. Export records source attribution coverage and does not claim complete source proof.
- New code/tests do **not** modify original Frank Writer, parser, frozen trade signals, Gmail, wallet signing, background scheduler, or live Mac services. Existing opt-in evidence uploader remains disabled in production; PR #31 remains Draft.

Validated with actual ZIP offline arithmetic plus CI synthetic regression fixtures for **224 total / 33 original / 104 passive-only / 87 other activity**, negative source and missing two J7 transfer legs, and complete 224-row Git FakeGit readback. These CI tests do not constitute a real Mac new-version replay.

### Acceptance and next blockers

- Real uploaded archive and Git readback: **VERIFIED**.
- New code research CI: see latest run on PR #31 and check its exact HEAD before claiming a new total.
- Source counterparty attribution coverage: **0/1,720** parsed flow arrays in this archive; **UNRESOLVED**.
- J7 two locally absent incoming transfers: **CONFIRMED MISSING FROM LOCAL INDEX**, original cost still unknown.
- 224 indexed source mints `!=` live holdings or investible BUY pool.
- Independent external AI review, actual Mac UI acceptance, on-demand raw-transaction backfill, cost basis/PnL and production opt-in activation: **NOT DONE**.
- User's <$1 exclusion rule applies to their own investment assets, **not** to deleting Frank research evidence of unpriced transfer-only tokens.

Detailed machine-checkable derived audit on research PR: `meme/evidence/frank-v2-1720-signature-transfer-completeness-audit-2026-10-11.json`. Original full transfer signature payload remains in the content-addressed Git evidence branch.
