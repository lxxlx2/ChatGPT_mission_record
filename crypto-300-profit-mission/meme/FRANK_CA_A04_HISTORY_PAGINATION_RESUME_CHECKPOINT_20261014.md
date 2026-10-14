# Frank / CA A04 historical RPC backfill and source cursor — 2026-10-14

Status: `CODE_SUBMITTED / FINAL_SHA_CI_PENDING / EXTERNAL_REVIEW_REQUIRED / RESEARCH_ONLY / NO_MERGE / NO_DEPLOY`

## Mission authority and dependencies

- Parent [Draft PR #45](https://github.com/lxxlx2/ChatGPT_mission_record/pull/45) HEAD pinned at project start: `92fbacbc411fb29a628c32d42bc5b6889603b7f6`. That PR is itself stacked on #43 and #42, all Draft and unmerged.
- Latest independently checked `main` at start: `656098f5bc845a234557b4cf6d14c57023f3b79b`, which is *not* the branch source; do not assert integrated-main CI or Mac readiness.
- Global authority: `crypto-300-profit-mission/MISSION_SPEC.md`, `FRANK_CA_MULTI_PERSON_IMPLEMENTATION_TODO_20261013.md`, and the frozen multi-person design.
- User separately assigned C02 to Codex; **no C02 files or PR #46 modified**.

## A04 actual software delivered

- `local-agent/mission_agent/mission_control/wallet_history_replay.py` introduces a finalized-only, injectible Solana read-only source collector and a journal in the already isolated `research-wallet-evidence.sqlite` Sidecar.
- `getSignaturesForAddress` supports **exclusive `before` pagination** (1–1,000 signatures/page) from latest available into older pages. Do not silently stop at 100/1,000 or assume a shorter page means end: only a subsequent explicit empty page records `pagination_end_observed`.
- The journal saves page fingerprint, all signature+slot rows, and next `before` in **one SQLite transaction**. A crash after the page leaves durable `PENDING` records and is resumed before any older page. A raw `getTransaction` evidence record and a wallet-scoped normalized view plus signature `CAPTURED` transition are **one transaction**, so cursor motion or a partial write cannot silently declare a complete economic record.
- Global `RAW_TX` identity is signature+Slot, independent of wallet; `WALLET_TX_VIEW` is wallet+signature+Slot, allowing two separately registered research wallets to share one chain event without doubling global transactions. Conflicting raw transaction hashes fail closed and leave the second wallet pending; no automatic trade/fee/PnL attribution.
- Source failures are durable gaps (`RPC_RATE_LIMIT_429`, `RPC_DENIED_403`, `RPC_TIMEOUT`, `TRANSACTION_NOT_AVAILABLE`, `TRANSACTION_NORMALIZATION_INCOMPLETE`, immutable conflicts). No private URL, key or provider text is persisted or printed.
- `scripts/frank_research_history_readonly.py`: explicit research-person allowlist and one wallet, defaults to `PLAN_ONLY` (no RPC and no Sidecar creation). `--execute` only manually reads finalized RPC and writes a private research Sidecar, capped per run by `--max-pages`, `--page-size`, and `--tx-budget`; no scheduler, signal, Gmail or trading permissions.
- Output separates `pending`, `captured`, `observed_signature_count`, observed Slot range, `missing_detail_counts`, last source error and continuation cursor. `history_complete=false` **always**: a provider's empty last page is `AVAILABLE_SOURCE_END_NOT_GENESIS_PROVEN`, not certified genesis/whole-chain/ATA completeness.
- Scope is a **manual historical owner-address backfill**. It does **not** yet refresh an old HEAD for newer incoming signatures, independently backfill all ATA accounts, prove the original economic funder, determine cross-owner beneficial control, classify every DEX route, or compute cost lots/PNL. Those are subsequent A04/A05/F02 tasks and must remain unchecked.

## Real external Solana checks, not from a production Mac

Connected Alchemy Solana finalized RPC on 2026-10-14 read the canonical *Frank-research* wallet as registered in source (not the user's personal Mission Solana wallet):
- First `getSignaturesForAddress(limit=4)` returned four finalized signatures at Slots **456664602, 456661829, 456659250, 456656354**.
- A second call with `before` the first page's final signature returned four finalized, nonoverlapping signatures at Slots **456653739, 456650996, 456648277, 456645392**.
- The first `getTransaction(jsonParsed,finalized,maxSupportedTransactionVersion=0)` returned the **same Signature and Slot 456664602**; accountKeys 8, pre/post Token balance entries 2 each, meta fee present.
- This independently supports the official RPC pagination and receipt contract: https://solana.com/docs/rpc/http/getsignaturesforaddress and https://solana.com/docs/rpc/http/gettransaction.
- These are **8 sampled recent signatures and 1 receipt**, not 8 fully journaled local transactions; no Mac Sidecar, full wallet/ATA coverage or historical PnL proven. No private RPC credentials or full raw personal wallet history committed to public Git.

## Development/test and release gates

- Baseline PR #45 has normalized token changes but no persistent signature cursor and no manual history CLI. New tests cover **1,005 signatures** across 400/400/205/explicit empty pages, actual SQLite close/reopen, missing tx, 429 and retry, wallet-level dedup/conflict, bad finalized/Slot/order, plan-only and account authorization.
- `.github/workflows/frank-ca-a04-history-replay-20261014.yml` runs compileall/pyflakes/Node, targeted A04+earlier A04/A05, and whole local-agent real Git replay.
- Only final exact-SHA passing CI can be cited. No second independent AI review yet. Production/Mac browser/SQLite/LaunchAgent/Gmail/frozen policy left unchanged. Do not merge into #45 or main before parent independent review and user's separate deployment authorization.

## Priority next work

1. Independently review exact SHA and transaction atomicity, checkpoint rollback and source-error coverage; resolve actual blockers.
2. Integrate **historical ATA/token-account address enumeration + checkpoint per address** using A05's explicit token owner proof. Keep non-atomic balance captures separate.
3. Real Mac local opt-in history capture and repeated re-run with read-only evidence report; validate archived 32 Mint/J7/BPxx samples and gaps. **Requires actual Mac inputs and separate authorization for production deployment**, never treat current synthetic tests as proof.
4. Classify market swaps/routing/fees/cost only with transaction-level evidence, then enable F02 truthful inventory and later A06/F03 PnL.
