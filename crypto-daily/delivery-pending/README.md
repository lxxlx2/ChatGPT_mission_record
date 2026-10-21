# Single approved report manifest for cloud validation (no local scanner)

The existing Crypto ChatGPT task produces a structured JSON manifest **only for the one report date it is about to send**; e.g. `2026-10-22.json`. The file is stored in this folder on Git main. It is not a new recurring monitor or a separate mail service.

## Mandatory fields

- `report_date`: YYYY-MM-DD, matches filename.
- `body`: the COMPLETE 13-heading text/plain candidate the user would receive.
- `items`: EVERY numbered body line in exact printed order: `section` (1..13), `item_number` (restart at 1 in every section), `event_key`, `role` (highlight/detail), `text` (byte-for-byte match to line excluding numbering).
- `events`: every item event_key with `material_version`, `kind` from `EDITORIAL_RULESET.json`, `published_at`, `source_url`, meaningful `actual_delta`, `impact`, `status`; Top5 additionally `impact_breadth` (market-wide/multi-venue/sector-wide), explicit `top5_basis` (at least 40 chars), `top5_evidence_url`, reliable `source_confirmed:true` and must not be `user_only`. `priority:'HIGH'` events not in body need `excluded_reason`.
- `source_receipts`: exactly one per required lane in the active JSON rule; `checked_at`, `query_or_url`, `status:'checked'` with real `result_urls`, or `status:'source_gap'` with real `error`. Never invent source checks.
- `market_core`: actual time-stamped BTC/ETH/SOL quote, positive `price`, `source_url`, `observed_at`. Their prices must ALSO be printed in Chapter Two.
- `empty_section_reasons`: any chapter 2-13 without numbered evidence gets a researched INTERNAL `reason` and `checked_lanes` linking to actual checked source receipts.
- `previous_events`: event key/version from real last 7 days delivered Sent/Git and TGE known ledger. Use a NEW txid/official policy version as a different fact. No historical stale replays.

## GitHub hosted CI (on push, NO CRON)

The file `.github/workflows/crypto-daily-editorial-qa.yml` is triggered by a push changing a dated `delivery-pending/*.json` (or the editor source/tests), NOT on a timer. It runs Node 22 with the checked-in `editorial_gate.mjs`/offline regression suite on a GitHub-hosted machine. On a passing report, `ci_editorial_receipt.mjs` writes `crypto-daily/delivery-qa/YYYY-MM-DD.json` with a `manifest_blob_sha`, `rules_blob_sha`, `editorial_gate_blob_sha`, `validated_at`, and `status: EDITORIAL_QA_PASS`.

The existing ChatGPT publisher should fetch the new QA receipt and compare ALL THREE Git file blob hashes with the actual files it is about to send. If no matching receipt, stale receipt, CI failed or Git write rejected, do not say CI passed. Carry out any permitted independently audited DEGRADED provider fallback according to `PIPELINE_CONTRACT.md` with exact evidence. Sending Gmail still requires Gmail tool success; GitHub CI does NOT send Gmail and has no mailbox credential or user wallet access.

`crypto-daily/delivery-qa/_ci-selftest.json` is a cloud offline-tests health artifact, NOT an approved daily email or proof of external source completeness.

Full report must not be reduced to an unresearched short note just because old event replays were removed. Preserve 13 headings, market and risk breadth, true original source timestamps and decision-relevant depth. The test does not independently retrieve/exhaust the news universe, and passing it does not prove zero omissions.
