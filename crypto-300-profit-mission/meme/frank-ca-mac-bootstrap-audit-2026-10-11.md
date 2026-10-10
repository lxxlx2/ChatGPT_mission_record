# Frank / CA Mac 首次证据同步验收：真实数据与远端逐字节核对

Date: 2026-10-11 Asia/Bangkok
Status: `REAL_MAC_BOOTSTRAP_DATA_INSPECTED / EVIDENCE_REMOTE_GIT_CONFIRMED / CONTINUOUS_AUTO_EXPORT_NOT_ENABLED / PRODUCTION_UNCHANGED`
Source: user-provided local evidence ZIP `frank-ca-evidence-20261011-053908.zip`, uploaded to the Mission conversation; independent GitHub evidence branch readback, and direct Alchemy finalized `getSignatureStatuses` for three original screenshot trades. The source ZIP is **not** published in Git by this audit; its already sanitized individual evidence files were uploaded through the Mac CLI to the dedicated evidence branch.

## 1. Actual local source window (NOT a wallet-complete claim)

Read-only D0 audit extracted from the ZIP:
- as_of_utc: `2026-10-10T22:39:08+00:00`; 24h lower bound: `2026-10-09T22:39:08+00:00`.
- Lifetime `LOCAL_INDEX_ONLY` distinct signatures: **1,660**.
- Last 24h locally indexed signatures: **199**:
  - `ACTIVE_TRADE`: **1**, locally recognized `SELL`: **1**, recognized `BUY`: **0**.
  - `PASSIVE_TRANSFER`: **153**.
  - `FAILED_TX`: **39**.
  - `ATA_CREATE`: **6**.
- Historical trade/state union in the local audit produces **32** `watch_seed` mint rows: `OPEN=5`, `CLOSED=13`, `INVENTORY_UNDETERMINED=2`, `UNKNOWN=12`. These are **local model labels**, not independently verified current token ownership, executable value, complete token universe or prospective BUY endorsements. Of these observed mints, 20 have at least one locally recognized BUY and 27 at least one locally recognized SELL across available history.
- Current latest captured Frank writer event `poll_count=20707`, recorded around `2026-10-10T22:38:54Z`; `last_successful_poll=2026-10-10T22:38:57Z`, `last_processed_slot=455422471`, `new_signatures=0`, `raw_pending=0`, `model_unprocessed=0`. This is a **dated observation**, not a guarantee of continuing health.

### Full historical identities of screenshot trades, now recovered from REAL Mac index

| Bangkok 2026-10-09 time | Local side | CA | Local USDC quote | Full signature |
| --- | --- | --- | ---: | --- |
| 08:26:47 | EXIT | `HzYCHqAN2uoHGRnL9v2ChCfFQX3bvJuJd5zu2Hd5MZQy` | `7031.556770` | `5wqKv5YuurRKUaJAK5fZtFrNg6GocVZuTTiAPWYrYDaswyUArwAZurpbZFU6WBjHp5z5Bt5bPCkLNKVQHfS6yigx` |
| 08:26:53 | SELL_POSITION_UNRESOLVED | `J7bhFegCHZAeRzdYDwmbSp1CJ1bDJkutSg26B4SXpump` | `2232.343956` | `Tk5zC6cZNLC4Jsbypi7gQkqD1FdA2YUvqRcaRx7ETGDyUsdyKHnooYqmcC5Lq5VrSSccQZiQUUCogUsxgpu3jDq` |
| 08:27:21 | BUY | `CWKbSd7jwMXXexP3pbwLAWMzr4HXAXTvt4R9pk2Vyyyc` | `3300.000000` | `23PV54NFD7R1NXJ7r3UZMM6Xo38z9u7KJ3D7Rn2my25pVhegZAbtJCTnEVmQ8JB7aVjeDhcMSMvmifWmgHRp5hiJ` |

Independent direct finalized status query at Solana context slot **455423504**: **all three signatures exist, are finalized and have err=null**; slots **454718132**, **454718154**, **454718257**, respectively. Their **exact USDC quote amounts are not independently reconstructed in this pass**: `getTransaction(version=1)` for two complex swaps returned truncated ~8098-byte payloads. The amounts above are Mac **local index observations**, the first TWEETCRAFT 7031.556770 also has earlier separate chain-flow evidence already filed in `FRANK_TWEETCRAFT_ROOT_SWAP_EVIDENCE_20261009.md`. The second has explicit `SELL_POSITION_UNRESOLVED`: do not re-label its proceeds as fully reconciled PnL.

**Window distinction:** these October 9 morning trades are excluded from the 24h period ending October 11 05:39 BKK. Local 24h `1 sell` refers to a **different later event**, not one of those screenshot rows. Both data periods can coexist without contradiction.

## 2. CA evidence completeness and byte-level archive audit

ZIP locally includes **two** CA reports:
- `7VertkgF9KLhxxJXHX6uaWuoYZTP9LdGj2bWmVXVpump`: sanitized allowlisted normalized report **2,283,271 bytes** reassembled from **20** base64/JSON chunks. All 20 chunk hashes and the full sanitized SHA256 `539d9972fb14e2348ac54d4dfa5170c051bc68300cbe00eac7996d9c0b7ec79c` matched locally. Includes **20** holder rows, **683** trade-evidence rows, **4** funding rows, `rpc_calls=235`, `rpc_endpoint_failures.PRIMARY=13`, `special_normalization_complete=false`, `narrative_status=NOT_AUTOMATICALLY_VERIFIED`, `cluster_status=WALLET_CLUSTER_UNRESOLVED`. Local job `DONE` does **not** prove exhaustive ownership or verified narrative.
- `HzYCHqAN2uoHGRnL9v2ChCfFQX3bvJuJd5zu2Hd5MZQy`: **88,398** sanitized source bytes, local SHA256 `8ff3baa46eecf0dfdc308e04c24d21269e2ae6611edf14ebf1c124f05db248ca` matched. Includes **20** holder rows, **25** trade rows, **1** funding record, deep_holders_scanned=6, `special_normalization_complete=false`.
- Both reports retain bounded/unresolved evidence status. No claim they match GMGN or that all source providers have been independently reconciled.

**Remote Git verification** as of evidence branch commit `66ba44a2f6556a64df63c3a809c79d945958ed5f`:
- Location: `evidence/frank-ca-local/crypto-300-profit-mission/meme/local-evidence/`.
- **23 artifact blobs**: 2 CA manifests + 20 chunks + 1 Frank bucket. Every local Git blob SHA computed directly from ZIP bytes was compared against the live Git tree's `blob.sha`; **23/23 exact matches**. Frank bucket `2026-10-10/2230.json` contains the one captured poll event.
- Therefore **Git evidence upload really succeeded** for this packet, separate from local success messages or an uploader's terminal exit code. No repeat Mac command is needed merely to re-send this exact packet.
- IMPORTANT UI bug: ZIP `summary.json` says `git_sync: NOT_REQUESTED` because the Mac bootstrap generated its ZIP **before** attempting authenticated Git upload, and only wrote final result to adjacent `.status.json`. Thus the ZIP itself held a stale status despite verified remote upload. Fixed on the research branch `scripts/frank_evidence_bootstrap.py::refresh_zip_summary`, with a synthetic ZIP preservation test. This fix was **not** installed on the user's Mac.
- The Mac uploaded ZIP was generated as a one-time bootstrap; this is **not** evidence of ongoing post-bootstrap automatic uploads. `MISSION_EVIDENCE_EXPORT_ENABLED` remains disabled in the code by default, and production deployment/restart was not authorized or done.

## 3. Remaining development and security gates

- Direct source import and existing-unit test safety were previously green. The updated ZIP status fix ran as a new GitHub CI job `38092440343` (actual success verified in GitHub Actions).
- Current full inventory PnL, residual mint owner reconciliations, evidence cross-platform parity, and all-history first-funder reconstruction remain incomplete.
- Secure data portability: user-uploaded ZIP must not be blindly reposted as a raw DB, and its direct on-chain signature values are public but can be large; no credentials, local live database or signer config should be committed to Git.
- PR #31 stays **Draft**. Independent AI/security review, actual Mac runtime install review, source writer/Gmail regression, and explicit user authorization are still required to activate continuous automatic upload.
- Evidence ingestion success and CA **analysis accuracy** are separate gates. This validated export infrastructure, not the claim that the present CA page meets the user's single complete-research standard.

No new scheduler, monitoring task, local LaunchAgent, Gmail, trading execution or production setting was created or changed by this verification.
