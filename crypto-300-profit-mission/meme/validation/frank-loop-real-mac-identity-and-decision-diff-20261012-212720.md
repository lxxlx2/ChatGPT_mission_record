# Frank Loop real Mac identity and source delta — 2026-10-12 21:27 ICT

## Evidence/provenance

User-uploaded `frank-loop-identity-readonly-20261012-212720.zip`; ZIP SHA256 `bf5b485a14ce7280027b35b7c9afc00be67f6848917ca040e1b8f841f1c68edf`. One sanitized `identity.json`; generated 2026-10-12T14:27:20.377688+00:00. This is a Mac user-run result, not direct access by the model.

The report has **20/20 PASS**, no FAIL, `error_type=null`. Both LaunchAgents running, PIDs and runner file hashes unchanged during read-only audit. Actual Loop executable process arguments and cwd match the runner's checkout. It explicitly does **not** attest already-loaded Python module bytes in memory.

**Live old Loop checkout at report time** `b358688a3b819ce59162bc2b0949e25541f3f8ef`.
**Pinned target already-installed Dashboard checkout** `6a5b7e8a533f99c871e31f9674329fcb4f929cc2` (PR #34 merge).

Machine environments: Python **3.14**, websockets **15.0.1**, shared venv path equality. This is only metadata; CI runs on Linux Python 3.12 and does not exercise actual Mac launchd/Gmail/RPC latency.

## Exactly what differs

Mac's source digest report: **11 modified/added Python module paths**, 116 old and 124 new Python files scanned. GitHub repository comparison for the **actual old SHA** vs pinned SHA confirms the same 11 paths: **2 modified** (`service.py`, `server.py`) and **9 added** (auxiliary history/evidence/watchlist modules).

| Relative to mission_control | Git status | Role |
|---|---|---|
| `service.py` | modified | Mission Loop's orchestration and optional evidence export |
| `server.py` | modified | Local dashboard/API |
| `ata_backfill.py` | added | Read-only ATA research |
| `delivery_review.py` | added | Historic notice review/presentation |
| `evidence_sync.py` | added | Opt-in evidence spool/upload |
| `transfer_archive.py` | added | Optional archive of public transfer research |
| `wallet_history.py` | added | Read-only trade-history reconciliation |
| `wallet_inventory.py` | added | Read-only balance evidence reconciliation |
| `wallet_reconciliation.py` | added | Quantity-gap review |
| `wallet_transfers.py` | added | Read-only transfer history |
| `wallet_watch.py` | added | Independent observed token watchlist |

No differences were reported for `mission_agent/mission_control/delivery.py`, `policy.py`, `signals/store.py`, `signals/engine.py`, `signals/classifier.py`, `signals/evaluator.py`, or the actual `scripts/mission_meme_v1.py` entrypoint.

Independently fetched both `service.py` versions from the exact old/new Git SHAs. The source text of the following entire method regions is **byte-identical**:
- `_quote()` (quote-skipping/quote construction)
- `_stable_quote_inputs()` through `_notification_intent()` (decision and notification intent helpers)
- **`cycle()`** (entire state/decision/outbox and Gmail-drain path, including 600-second initial notification age guard)

The original `__init__` adds `self.evidence_export_last_error_type = None`; `_write_health` adds the corresponding diagnostic field. `loop()` adds an **opt-in** asynchronous evidence export subsystem gated by environment value `MISSION_EVIDENCE_EXPORT_ENABLED == "1"`, and retains the same `self.cycle()` main invocation. The reviewed Loop-only runner script expressly inserts `export MISSION_EVIDENCE_EXPORT_ENABLED=0` before launching the new process. Import-time integration, Python 3.14 behavior and first-cycle latency remain subject to actual controlled deployment.

## Rollback and historical notifications

The Mac report confirms `legacy_delivery_identical=true`: `delivery.py` is byte-identical, so the **source-equivalence prerequisite** of PR #36's automatic rollback path is satisfied for this actual Mac checkout. This is materially different from earlier reviewer examples based on another assumed old commit. Automatic rollback is still **conditional**: only if no unsafe old/stale-sendable records, no overlapping Loop workers, correct runner/LaunchAgent process identity, and the rollback health check succeeds. Never claim rollback guaranteed under all failures or restore an old SQLite snapshot over new events.

The prior sixth Mac preflight (31/31 PASS; before this newest report) established cloned SQLite consistency and absence of queued stale notifications **then**, not immutable future status. Run a fresh preflight immediately before any separately authorized apply.

## Outstanding production release gates

1. **Explicit user approval** of the observed 11-module source delta, and acknowledgment that `service.py` and import/loop behavior changed even though the complete decision cycle, policy and delivery implementation did not.
2. No CLI switch or `--approve-signal-code-change` flag is authorized by this analysis or code-merge approval alone.
3. Refresh exact 31-check Mac read-only clone/Gmail preflight close to any proposed cutover; inspect new/sending/uncertain mail state separately.
4. Verify first-cycle time and post-old-PID-exit health under actual Mac launchd; CI synthetic timings are not a guarantee.
5. Require the user's separate, explicit live-Mission-Loop-restart authorization. Keep Dashboard code rollout (PR #35's follow opportunities first) independent.

**CURRENT: PR #36 code MERGED, MAC LOOP still OLD, DEPLOY BLOCKED.** No Mac process was restarted by this uploaded identity script; no Gmail sent or production database written.
