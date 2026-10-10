# Frank / CA local evidence synchronization

Status: **storage branch initialized, user Mac uploader NOT YET DEPLOYED**.
Updated: 2026-10-11 Asia/Bangkok

This **separate evidence branch** stores sanitized, read-only, locally captured results. Its content does **not** change Mission production rules or the `main` branch.

When the reviewed uploader is explicitly installed and enabled on the Mac:
- `ca/<mint>/<job-uuid>.json`: one per completed manual CA query, with source timestamps, holder/funding/transaction evidence where available, explicit truncation/completeness flags and local report SHA256.
- `frank/YYYY-MM-DD/HHMM.json`: every observed completed Frank poll written as a small record in a **15-minute UTC bucket**, uploaded when that bucket closes. Material scans also carry sampled classified trades, coverage and signal candidate evidence.
- A finished result is only considered **GIT_CONFIRMED** after authenticated upload and byte-identical Git readback.
- Failed/unavailable GitHub uploads remain in a 0700/0600 protected **local pending spool**, retried on the next existing trigger or explicitly by the CLI. Git success must not be inferred from local `QUEUED_LOCALLY` status.

No source repo-wide Git checkout, monitor thresholds, scanner, Gmail or wallet is modified to publish records. The app uses its **existing** Mission Control / CA execution points (no new LaunchAgent) and is **disabled** until `MISSION_EVIDENCE_EXPORT_ENABLED=1` is explicitly configured in a reviewed deployed version.

Security: reject credential-bearing fields, JSON exception bodies, local paths, email/Gmail metadata, private keys and RPC/auth URLs. The branch is not a place for raw wallet DB dumps, original config files or screenshots containing identifiers. The full private local raw reports remain at their existing location and are referenced with SHA256; some Git summaries may be explicitly incomplete to stay inside bounded upload limits.

Authority: `crypto-300-profit-mission/meme/frank-ca-git-evidence-sync-design-2026-10-11.md` on `main` after governance synchronization; implementation candidate in [PR #31](https://github.com/lxxlx2/ChatGPT_mission_record/pull/31).

No scheduled task, email or user-uploaded evidence has been added by initializing this branch.
