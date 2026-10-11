# Frank V2 PR #31 independent BLOCK response, 2026-10-11 Bangkok

## Independent review origin and evidence distinction

A user-provided independent Claude Haiku 5.5 review evaluated code SHA `87a0611bacbd46fc044aec79a941dbf9ec3c88e8` and returned **BLOCK**. The reviewer reports an unpushed local amended commit `16e4ef6f` replacing `89ccf783`; the reported patch and reproduction scripts are **not verified as pushed or present in this repository**. The reviewer's independent Solana PDA cross-check and test claims are attributed to their supplied report; their environment could not access live Solana RPC. Its primary-signature-binding logic was code-reviewed and covered by existing tests, **not independently compared by that reviewer**. This response document is the implementer's tracking record, not a new independent review or a reproduction of that full unpublished patch.

## Finding-by-finding research remediation

| Review ID | Severity | Actual research changes | Remaining release gate |
| --- | --- | --- | --- |
| H1 | HIGH | `ata_backfill.py` explicitly marks `PAGE_LIMIT_REACHED`, partial pagination and CLI exit 3; dedicated full-page test | Mac real read-only pagination replay and other-AI re-review |
| H2 | HIGH | Any successful signature without valid ATA balance proof becomes `PARTIAL_TX_UNVERIFIED`, with an explicit unverified signature list; [] of confirmed-missing no longer implies absence of gaps | Real raw source breadth and review |
| H3 | HIGH if opt-in | `service.loop` export exceptions including SQLite are isolated from decisions/Gmail; error type exposed in health, background `Future` exception observed with bounded retries; opt-in remains OFF | Mac dry shadow/export failure drill and reviewer verification |
| M1 | MEDIUM | Isolated ATA read-only adapter handles `JSONDecodeError` (ValueError) and malformed-root AttributeError, retains prior evidence and outputs partial local artifact. Frozen V1 `mission_agent/frank/rpc.py` deliberately UNMODIFIED | Real provider malformed-envelope test pending; no V1 collector change |
| M2 | MEDIUM | Dated, separate J7/BPxx ATA owner-index gap evidence, overlay in `wallet_watch` and row-level Dashboard visibility. Local 1-count passive transfers retained with source label; two extra J7 receipts separate. Real Git replay now asserts historical gap | Mac rendering/visibility test pending, broader mint gap not yet indexed |
| M3 | MEDIUM | Two selected J7 `getTransaction(jsonParsed)` full result strings saved along with independently computed UTF-8 SHA256 and primary signature checks. Explicitly sourced to connected Alchemy tool; frozen Frank V1 uses public Solana RPC | Other transactions and exact production endpoint replay not archived; **PARTIAL** |
| M4 | MEDIUM | Immutable content-addressed CA/history/ATA files reject conflicting remote Git content; only 15-minute Frank poll buckets remain intentionally mutable. FakeGit regression tested | External Git concurrent-write adversarial review pending |
| M5 | MEDIUM | Versioned loaded-address suffix supported where provable; unresolvable token balance account index fails closed and successful missing proof becomes explicit partial | Live ALT provider behavior **UNVERIFIED** |
| L1 | LOW | Sanitizer raises on excessive arrays and redacts absolute user home paths, including embedded strings | Extra sanitization review |
| L2 | LOW | CLI outputs `git_sync` and `scan_status` separately; exit code 2 still prioritizes failed Git sync over partial scan exit 3 | Exit precedence remains unchanged; caller must parse both fields |
| L3 | LOW | Mission Control worker future failures observed in health; dashboard CA export `evidence_executor.submit` path has no independent future-result repair | **OPEN** |
| L4 | LOW | CLI `--since-time=0` help still ambiguous | **OPEN** |

## Cross-source actual evidence kept separate

- BPxx canonical ATA seven bounded pages: 70 finalized signature-list records; 4/70 found in the independently reconstructed original 1,720-row local owner index; 66 missing owner-index signatures (63 before index start, 3 during), but only **one** of the in-window successful misses has an independently verified +0.771543330 BPxx balance delta. Source costs and total BPxx profit UNKNOWN.
- Two J7 Token-2022 ATA incoming receipts independently re-read from real finalized `getTransaction`; the raw result strings and their SHA256 are archived as `evidence/frank-v2-j7-raw-rpc-responses-sha256-2026-10-11.json`. Economic acquisition costs unknown.
- Read-only `owner_index_gap_status=CONFIRMED_HISTORICAL_GAP` conveys a *dated* observation and does not change the original Frank model's BUY/SELL, alerts, quote, Gmail, signing, or production Writer.

## Gates and authority

All research changes stay on Draft PR #31. **Do not merge or deploy** until the exact new HEAD has a green GitHub CI, a separate independent re-review of original H/M blockers, and a bounded real-Mac read-only acceptance; complete-chain attribution, user-wallet economic cost and CA accuracy remain unresolved. `MISSION_EVIDENCE_EXPORT_ENABLED` OFF in production, `PRODUCTION_TRADING=NO_GO`. No new automation, daemon, email, or live trading is authorized. Original independent reviewer commit `16e4ef6f` is not represented as pushed; this is a separate implementation response.
