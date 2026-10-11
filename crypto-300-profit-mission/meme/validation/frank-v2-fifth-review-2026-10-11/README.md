# Frank V2 PR #31 fifth-round review scripts (2026-10-11)

Synthetic fixtures and committed evidence only. No RPC, no credentials, no production database.

1. Reverse regression (F1, F2 exception family, F6 sanitizer). Run with PYTHONPATH at a local-agent tree:

       PYTHONPATH=. python ../meme/validation/frank-v2-fifth-review-2026-10-11/r5_reverse.py

2. Sanitizer output comparison over committed evidence strings (base vs pinned vs fixed trees):

       python r5_sanitizer_compare.py <path-to>/crypto-300-profit-mission/meme/evidence

The script loads three evidence_sync.py files by path; edit the three paths at the top of
`r5_sanitizer_compare.py` to the local base, pinned and fixed worktrees before running.
