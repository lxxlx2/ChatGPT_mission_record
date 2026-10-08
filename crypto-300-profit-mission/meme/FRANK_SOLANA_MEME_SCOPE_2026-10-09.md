# Frank — SOLANA TOKEN ONLY / FOMO transaction evidence correction

Status: research scope decision, 2026-10-09 Asia/Bangkok.
Priority: Meme/Frank inside $300 → $3000 Mission.
Production status: NO_GO; no new background task, monitor, mail or trading config.

## User's hard boundary

**Only actual SOLANA-ISSUED meme token (exact Solana Mint) BUY/SELL, holdings and followability matter.**
Source chain of quote USDC / SOL is not a token identity classifier.
Do not extend this mission to reconstructing the acquisition history of
Robinhood Chain or other EVM tokens. Do not require RH RPC coverage as a
prerequisite for validating a Solana-mint trading candidate.

A trade must be included because the asset bought/sold is a Solana SPL mint,
NOT because a Solana wallet paid USDC or because a DEX named a familiar ticker.

## Rechecked technical documentation

Chainstack's experimental FOMO listener/reference:
- https://github.com/chainstacklabs/fomo-solana-rh-listeners/blob/main/docs/01-how-it-works.md
- https://github.com/chainstacklabs/fomo-solana-rh-listeners/blob/main/docs/02-trade-lifecycle.md
- https://github.com/chainstacklabs/fomo-solana-rh-listeners/blob/main/scripts/shared/solana.py

Rules supported by those sources:
- FOMO in-app cash is normally Solana USDC. Issued tokens stay on their
  issuance chain. **Solana USDC → Solana SPL token** is a same-chain swap
  via Solana aggregators/venues; **no Relay order is necessary**.
- A Solana Relay PAY is a deposit which contains amount+order ID but no target
  mint. It does not prove a Solana-mint purchase and must not be counted as one.
  Cross-chain settlements may describe RH/EVM token delivery or withdrawal.
  Those directions are OUT OF SCOPE until a specific SOL token delivery is
  independently observed.
- FOMO co-signer `AgmLJBMDCqWynYnQiPCuj9ewsNNsBJXyzoUhD9LJzN51`.
  Candidate same-chain programs: DFlow, Jupiter, other actual DEX programs,
  not a single fixed program family.
- Buy/sell evidence comes from wallet-owned SPL/Token-2022 balance deltas,
  SOL/USDC/WSOL counterflow, fill structure, and exact mint; multi-hop
  routes must be collapsed to **one transaction-level economic fill**.
- An incoming SPL transfer *without* established matched purchase counterflow
  is a receipt/airdrop/gift/unknown, never confirmed BUY.
- If the SOL token is delivered via a solver from a different funding chain,
  record SOL arrival as an unmatched receipt, not a verified buy or a guessed
  entry price. Cross-chain funding is not required for SOL token discovery.

Independent references:
- https://docs.bitquery.io/docs/blockchain/Solana/fomo-api/
  (FOMO signer, DFlow ProtocolName, `Trade.Buy.Account.Owner`,
  one-wallet Solana trade filter, limitations of raw signer fields).
- https://hoodwatch.dev/blog/fomo-family-on-solana
  (relayed Solana swaps, token-account delta reconstruction, external
  profile-vs-execution-wallet attribution caveat).
- https://solana.com/docs/rpc/http/getsignaturesforaddress
  (only transactions with requested account in `accountKeys`).
- https://solana.com/docs/rpc/http/gettokenaccountsbyowner
  (find wallet-owned SPL accounts).
- https://solana.com/docs/payments/accept-payments/verification-tools
  (read signatures on token accounts and pre/post balances).

## What actual Mac evidence establishes (not more)

Fixed window `1791386454..1791472854`:
- 173/173 **Solana root-wallet** signatures matched RPC, then 173/173
  individual transactions hydrated, including 93 reused cache records.
- Previous classifier: 152 `PASSIVE_TRANSFER/FRANK_NOT_SIGNER`,
  18 `THIRD_PARTY_ATA_CREATE`, 2 `UNKNOWN`, 1 `ACTIVE_TRADE/BUY`.
- Read-only evidence parser identified `SWAP_CANDIDATE=1` and
  `RELAY_PAY=1` in root-wallet-accessible transactions. The Relay payment
  signature is `KTW6qm2yw8PJC1cqUVejnG9yfYo3UQN5Y6dJJrwXeZQfbxL2ZvbtB4aymTPbPYr9BkhJrrhtswMGUytgqF5othS`,
  order ID `0xcb9a15b8ab25ecbbbb657b12fce469a196ef9efb3cea089e8b335aa78b2776ed`.
- **No full Solana SPL-holder account / DFlow user-owner enumeration has been
  performed. The actual token mint and quote amount of SWAP_CANDIDATE are
  NOT in the user-shared terminal summary.** Do not invent them.
- 173/173 therefore proves only coverage **of the queried root pubkey**,
  not complete Solana token buy/sell history and not Frank-person history.
- Candidate Solana wallet `A5SEXYJY4jTEi6sjMLfZs5KAP8SVFvLDPDV67GgSSZSk`
  returned 0 signatures for root-address style RPC enumeration in this
  window. This cannot prove its owned SPL token accounts were inactive.
- Third-party identity references CONFLICT:
  https://provadata.com/traders/frankdegods labels
  `498g…AayQ` as a verified Solana wallet; 
  https://hoodwatch.dev/trader/A5SEXYJY4jTEi6sjMLfZs5KAP8SVFvLDPDV67GgSSZSk
  uses `A5SEXY…SZSk` and currently shows no attributable closed trades.
  Neither association is independently cryptographically established here.
  Keep both as separate candidate identities and test exact onchain holdings
  and real FOMO fill owners before combining.

## Correct scope for next code iteration

1. Build read-only **Solana SPL account universe** for each candidate owner.
   Enumerate Token + Token-2022 via `getTokenAccountsByOwner` and recover
   historical closed ATAs from transaction/event indexes when possible.
   Do not call a current snapshot a full historical wallet inventory.
2. Cover `getSignaturesForAddress` for token accounts, not just root wallet.
   Complement with wallet-filtered indexed DEX fills using FOMO co-signer +
   DFlow `Trade.Buy.Account.Owner`. Do not try to stream *all* FOMO
   co-signer transactions to filter locally without bounded cost.
3. Validate for each exact Solana Mint a transaction-level BUY/SELL
   (opposing wallet-owned token/USDC/SOL deltas, program/route evidence,
   single transaction hash, non-duplicated; wallet/mint/time/value fields).
   Require observable counterflow; unknown stays UNKNOWN.
4. Reconcile exact 24h window against an independently indexed
   user-owner DFlow feed and historical SPL token accounts; provide
   `root-signature coverage`, `token-account coverage`,
   `trade-classification coverage`, `external-index divergence`
   separately. All other figures are not completeness claims.
5. Once Solana-only fills and identity are proved, perform historic replay
   and delayed-followability tests. Production signals must not be changed
   without reviewed, gated rollout and preserved Gmail deduplication.

## RH/EVM component status

`mission_agent/meme/fomo_crosschain.py` and `scripts/audit_frank_fomo_crosschain.py`
are historical research prototypes, **PARKED / OUT OF SCOPE for Frank Solana
Meme signals**. Do not spend further RPC calls, engineering cycles or
automated alerts on RH/EVM unless user explicitly reopens that scope.
No RH data should be required to render, rank or notify about Solana Mint
signals. The user-directed mission scope takes priority over those prototypes.

This scope note does not itself attest any additional live chain transactions,
does not run tests or alter a Mac LaunchAgent, and is not a production gate.
