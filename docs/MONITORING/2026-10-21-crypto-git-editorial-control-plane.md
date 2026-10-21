# Crypto Daily: Git-controlled editorial pipeline — 2026-10-21

## Scope and actual decision

User rejected short/incomplete corrected reports, BALANCE artificially filling global Top5, repetitive news, and any new local Mac monitoring. Change applies to the EXISTING ChatGPT Crypto daily task, not any Monster/Frank/Mac runtime, and does not create a separate scheduled monitor.

The structural fault: old ChatGPT automation's large changing prompt combined source discovery, importance ranking, thirteen-chapter templating, duplicative filler, editorial checks and Gmail delivery. A structural 13-heading/25-item correction with many undocumented blank sections is NOT a complete adequately researched report. Prompt-only statements do not prove primary-source recall or that actual JS code ran.

## Completed Git main changes (actual tool writes verified by readback)

- `crypto-daily/PIPELINE_CONTRACT.md`: separates collector / event accounting / topic routing / current-news completeness / editorial QA / Git prepared body / Gmail readback / Git final archive.
- `crypto-daily/EDITORIAL_RULESET.json`: machine authority for 13 chapter placement, Top5 evidentiary requirements, source lanes, no-padded headings, standard error conditions and SHA-bound CI receipts. Top5 at most 5, never quota. Every item has one primary home.
- `crypto-daily/scripts/editorial_gate.mjs` + `crypto-daily/tests/test_editorial_gate.mjs`: deterministic structural and metadata check, actual section number, Top5 eligibility, source receipts, match of numbered body lines to events, material versions, negative checks for undispositioned high-risk candidates, known-event repetition, timestamped BTC/ETH/SOL in body and source manifest, and researched reasons for empty chapters.
- `crypto-daily/scripts/ci_editorial_receipt.mjs`: emits approved report receipt with exact blob SHAs for manuscript/rules/editorial code only when machine checks pass.
- `.github/workflows/crypto-daily-editorial-qa.yml`: GitHub-hosted Node 22 job; only `push` to main on eligible code or dated pending manuscript files; NO `schedule`, no cron, no remote login to user's Mac. Read-only validation of market content; only writes Git pass-proof artifacts with GitHub bot, no Gmail/wallet privileges. Manifests described in `crypto-daily/delivery-pending/README.md`.
- `crypto-daily/REPORT_SPEC.md`, `REPORT_ACCEPTANCE.md`, `COLLECTOR_SPEC.md`, `DELIVERY_RUNBOOK.md`: refer to Git control plane and keep original core requirements.
- The original ChatGPT task `6a8600b9d12481919bc43ebc800c9916` remains enabled at exactly the same Asia/Bangkok :20 scheduler slots and has been rewritten as a Git-rule bootstrapper, rather than a repository of prose hard-coded individual events.

## BALANCE regression: user correction adopted

The BALANCE project itself, its early art/token economics, valuation and Jack Butcher design are in **§8 Early/Meme/NFT**. Only a genuinely distinct current CCA bidding/settlement/refund/claim ACTION belongs in **§7 TGE/public sale**. The SAME project launch or auction sentence is not repeated in both. A personal participation is never itself eligibility for **§1 global Top5**. `EDITORIAL_RULESET.json` category examples and the latest `PIPELINE_CONTRACT.md` take precedence over older examples in long historical acceptance prose.

The fifth independently identified 500 BTC Clifton Collins movement is a §5 real institutional/labeled onchain flow; it does NOT automatically merit global Top5 solely due a $41.5m source estimate. A Coinbase Prime-labeled deposit is not an executed market sale.

## Tests and receipts ACTUALLY seen

The latest Git-backed editorial gate code and 16 regression test cases ran in the in-chat JavaScript test environment: **16 PASS / 0 FAIL**. Includes a valid 13-chapter/no-padding case, missing-market-price errors, missing source receipts, old-event replays, more than two repeats of one event, BALANCE personal bid blocked from Top5, project in §8, separately justified CCA in §7, and incorrect-section negative cases.

More importantly, a GitHub-hosted cloud CI **actual Node test self-check** was observed: `crypto-daily/delivery-qa/_ci-selftest.json` exists on Git main and has
- `tested_commit: 9c890bbcf4d9df6ae83df7ecad3391e481e61384`
- `editorial_rules_blob_sha: df26ea064cc6feae99e345f6efaf402485b0482c`
- `gate_blob_sha: da773d88528efe3effa6c0591bfa3e47e8360699`
- `checked_at: 2026-10-21T03:51:54.438Z`
- `state: NODE_TESTS_PASSED_ON_GITHUB_RUNNER_NOT_PRODUCTION_DELIVERY`

This is proof the cloud Node/CI path and Git writeback actually ran, not just a file being committed. It is **NOT** proof that an actual pending report was validated, that news recall was exhaustive, or that Gmail scheduled send will work. The first real prepared manuscript must yield `delivery-qa/YYYY-MM-DD.json` with the exact manifest/rules/code blob SHA matches before a true `GIT_CI_QA_PASS` can be reported. Any new code/rule change requires a new matching cloud receipt.

## Next real end-to-end production acceptance

Next normal day, existing 08:20 collector/prebuild must retrieve current primary English source receipts and create a complete dated `delivery-pending/YYYY-MM-DD.json` (not a thin 25-item correction), with credible empty-section reasons and typed event/item routing. GitHub push CI must validate and write its SHA-matched report receipt. Existing 09:20 task must recheck Sent prefix, validate external source facts and receipt, Gmail-send exactly one full report, then read back actual body/recipient and archive the identical body to Git; 10:20/11:20 are recovery only. Only all these together prove a fully healthy scheduled delivery.

## Explicit residual risks / blockers

- The previous 2026-10-21 user-requested corrected email `1a15c6d25715d6ca` was already sent and archived. Its 25 numbered items and several blank chapters lack a post hoc independently validated full 11-domain source manifest. Do NOT claim that shorter correction meets the new complete-source standard. No THIRD same-date mail was sent as a side effect of this architecture change; a genuine new user-authorized full corrected edition would require a fresh complete review and Sent/Git provenance.
- Today's classification work is not itself an independent 24h source sweep: missing articles and primary X 403 can still cause omissions before classification. Git CI validates declared receipts, not the truth of inaccessible news or an exhaustive chain scan.
- Platform-level scheduled Gmail safety checks can still block a legitimate send; cloud Git rules and CI cannot bypass provider policies. No deceptive delivery-success claim.
- One older paragraph in the historical `REPORT_ACCEPTANCE.md` still phrases BALANCE as §7-focused. A targeted attempt to update that exact paragraph was rejected by provider safety checks. `EDITORIAL_RULESET.json` and `PIPELINE_CONTRACT.md` explicitly have classification precedence and correctly set §8 project/§7 actions; the old prose still needs normal later reconciliation, not circumvention.
- No GitHub scheduled workflow, no Mac launchd, no paid subscription, no trading or signing. The separate original US stock and TGE schedules were not modified in this architecture iteration.
