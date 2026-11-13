# Mission Frank D1 — wallet signed-activity source view (parallel GPT lane)

Date: 2026-10-19 (Bangkok); code branch: `feat/frank-v2-d1-activity-ledger-gpt-20261019`; exact main parent: `ee4baaf5ffd9719094c91d3cd96eaf54bf22cb4a`.
Status: **RESEARCH_READ_ONLY_LEDGER / NO_CHAIN_COMPLETENESS / REAL_MAC_EVIDENCE_PENDING / DRAFT**.

## User-facing capability and why it matters

Existing Frank Dashboard exposes only separate feeds of model candidates, market trades and review candidates. D1 original V2 design requires a wallet-level complete **local facts** chronology for all indexed signatures, with active-trade, passive, account creation, failure and unknown classified **independently of BUY strategy**. This small step provides a private, local searchable HTML based on existing `forward.sqlite` with exact wallet+signature link to recognized trades, immutable source classification and direct public transaction URLs. It does not claim to be a complete chain ledger.

A source `ACTIVE_TRADE` with no `trades` leg is shown as `ACTIVE_WITHOUT_TRADE_LEG` and an otherwise passive/failed/unknown source with a recognized trade leg is shown as `CLASS_TRADE_MISMATCH`; both are **review flags**, not proof of a failed parser or automatic signal. All unknowns remain unknown. Does not show or reconstruct USD PnL or current balance.

## Existing historical ATA scope used correctly

A verified correction artifact already lives at `meme/evidence/frank-v2-ata-index-scope-correction-2026-10-11.json`. We **do not** rely on superseded `frank-v2-known-ata-gap-summary-2026-10-11.json` unqualified. Bounded dated facts:

| Mint prefix | ATA-only signatures absent from main-account-key index | Before Oct02 index start | During known window | Failed in-window | Successful but not yet verified | independently verified passive receipts |
|---|---:|---:|---:|---:|---:|---:|
| J7bh... | 2 | 0 | 2 | 0 | 0 | 2 |
| BPxx... | 66 | 63 | 3 | 1 | 1 | 1 |

Main-wallet account key absence from ATA-only transfers is a **source coverage limitation**, not automatically a bug and definitely not a market BUY. Signature list counts are **not** token transfers. These dated counts MUST NOT be mixed into 2026-10-19 live activity totals.

## Boundaries / validation

- Only existing local Frank SQLite via URI `mode=ro`, `PRAGMA query_only=ON` and typed source queries, default **1 day** and explicitly optional 7 days, max 5000 signatures; overlimit is a failure, not truncated evidence.
- Only reads already-in-repository corrected Oct11 ATA JSON; no RPC, no SQLite writer, no browser process server, no Gmail, no trade, no production root edit. HTML private in `~/Downloads`; hyperlink to public Solscan **only if clicked**.
- Tests run real temporary SQLite: exact wallet+signature join, no enrichment from other wallet, positive active trade, passive/unresolved/failed/ATA types, old source not joined, cross-class/ledger discrepancies, no DB bytes change, safe output HTML, historical 2+66 corrected scope, row-limit fail closed. Do not claim synthetic SQLite is real Mac proof.
- Actual Mac one-time delivery **after independent code review**; no repeated C02/503 or review-loop scaffolding. Stop when the 24h event feed's genuine counts can be verified against already observed `273 signatures / 2 BUY`, and move on to targeted D1 missing categories if there is a real mismatch.
- Claude is working separately on D2 fourteen-priority-token wallet inventory. This D1 PR is strictly independent and must not touch `mission_agent/`, PR #109/#110, the same D2 files or control database.

**No merge/deploy/new RPC/transaction/notification/production SQLite write without approval.**
