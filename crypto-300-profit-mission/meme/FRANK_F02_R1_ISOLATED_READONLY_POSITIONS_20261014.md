# Frank F02-R1: source-pinned isolated read-only positions API

Date: 2026-10-14 Asia/Bangkok.
Status: \`CHILD_CODE_SUBMITTED / EXACT_CI_AND_OTHER_AI_REVIEW_REQUIRED / NOT_PROD / NO_MERGE\`.

## Factual input and independently reviewed upstream

- Approved A05-R1 parent PR #60 code SHA \`e4529ba7069e5499d12323a7160ceac08c481fae\`; A05-R2 parent PR #61 SHA \`076f9cabb58cac2d0890fa15cf9906cafe37423b\`, both user-forwarded external GPT-6.1 Sol and Gemini 3.8 \`APPROVE\`; no GitHub-native formal review claim. R2 new original 32 roster Git blob \`c6f43e4a63ea9daa1c9b820b8faed8ccefcdb2d1\` remains immutable.
- GPT-6.1 Sol reviewer reported independently accessing user Mac's two private original raw replies: at 2026-10-14 22:54:15.873 BKK, 1785 SPL Token accounts/945282 bytes/slot 456895319, 1448 Token-2022/848980 bytes/slot 456895320, 3233 open accounts, capture SHA \`a91fed6fae63f51557ab88fb9ae892247cc32deccd26c631d765ff27aff03261\`. Real original target 32 = 9 nonzero/23 zero/0 absent/32 target open accounts; independently reaggregated 32 rows match the R2 tool per that review. Gemini independently approved code but did not claim full private raw inspection. This is an *archived* observation, not a continuously verified current balance, executable trade idea, person control, or PnL.
- Research Sidecar import was intentionally NOT performed by original Mac capture (\`research_sidecar_imported=null\`). **F02 cannot serve this archival source until an explicit separate research-only import** with provenance match. No implicit migration, no production forward.sqlite access.

## Contract, scope and operational safety

New code lives only in \`local-agent/scripts/frank_f02_readonly_positions_api.py\` with dedicated tests and CI; original \`mission_control/server.py\` and its production routes are **unchanged**. \`--serve\` is an explicitly manual, local \`127.0.0.1\` listener exposing \`GET /api/research/positions\`; no scheduler, public bind, CORS access, network RPC, transaction, Gmail, new SQLite writer, background service or trading path. Default invocation is \`PLAN_ONLY\` without reads/writes/network; \`--probe-once\` reads actual private archive and prints source-bounded research JSON without starting HTTP listener.

- Registry selects one exact research \`person_id\` and \`wallet\` binding; no Frank address hardcoded in API. Selection of a multiwallet person must be explicit. Frozen 32 Mint R2 roster is wallet-pinned, so other peoples' research cannot silently borrow Frank's list. Future generic roster interfaces may be approved separately.
- Requires **both** an original complete dual-program bundle satisfying approved \`replay_owner_full_receipts\` and an explicitly designated **separate** \`WalletEvidenceStore(read_only=True)\` \`ACCOUNT_CAPTURE\` research Sidecar. It independently validates original-wire provenance on service start and pins \`verified_full_wire_capture_sha256\`. No raw RPC bundle contents are sent over HTTP.
- At request time \`latest_inventory\` reads **all** immutable \`ACCOUNT_CAPTURE\` candidates and selects the latest by chain slot/timestamp with a newer slotless-failure override. The only circumstance permitting actual raw quantities is: latest slot source valid for both token programs, age <= configured \`--max-age-seconds\`, and latest Sidecar capture SHA exactly equals the independently verified original-wire bundle SHA. An old successful snapshot is never allowed to reappear after a later failed attempt, an unverified new capture, or stale source.
- Response has per Mint \`OPEN_ACCOUNT_NONZERO\`, \`OPEN_ACCOUNT_ZERO\`, \`NO_OPEN_ACCOUNT_OBSERVED\` (unknown amount and not a historical sale) or \`SOURCE_UNAVAILABLE\`. All source-failed/expired/unverified current values are \`null\`, not zero. Full 32 rows only, preservation of all target Mint token accounts and exact raw decimal-string quantity. Response includes \`person_id\`, \`wallet_id\`, wallet binding role/evidence status, source UTC/slot range/hashes/freshness, non-atomicity, roster blob and state-count summary. No USD value, costs or PnL, no actionable signal, no person-control proof. HTTP responds with \`Cache-Control: no-store\`.
- Missing research Sidecar or mismatched original owner/source fails before serving; sidecar is opened only with SQLite \`mode=ro\`. No implicit Sidecar creation, source import or migration. Current review must not be mistaken for final API Mac/browser/production acceptance.

## Current gates and next path

1. Finalize exact SHA tests, actual GitHub module full CI and disposable F01/C02/A05/F02 full CI.
2. Obtain independent another-AI review **of final F02-R1 code SHA** for freshness and complete-wire pin, no stale resurrection, sidecar-only read mode, Flask-free localhost endpoint isolation, explicit person/wallet, quantity precision and no CORS; insist on actual HTTP test not just pure functions.
3. After approval and **separate user-authorized research-only Sidecar import from already validated bundle**, run Mac \`--probe-once\` against same archived source and verify accurate but time-stale result. Fresh "current" numbers require *another* manual approved full-wire capture and matching research Sidecar import; do not silently relabel October 14 22:54 as current.
4. F02-R2 isolated Dashboard browser and F02-R3 Mac QA, then independent cross-module and final system review; no merge/deploy until explicit authorization.

No production file or service changes. \`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADES / NO_PRODUCTION_SQLITE / NO_AUTOMATION\`.
