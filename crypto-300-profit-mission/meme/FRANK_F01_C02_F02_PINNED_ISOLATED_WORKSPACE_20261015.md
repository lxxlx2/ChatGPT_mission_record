# Frank F01 / C02 / F02 fixed-SHA isolated integration — 2026-10-15

Status: PR72_OLD_SHA_REQUEST_CHANGES / P1_IGNORED_DATA_AND_P2_PIN_RECEIPT_CHILD_FIX_DEVELOPMENT / CI_AND_OTHER_AI_REVIEW_PENDING / REAL_MAC_NOT_RUN / NO_MERGE / NO_DEPLOY.

Independent original PR #72 review at f9b0082aca2944ec6430bee173018924a6578721 found a real P1: ignored unsaved research files were deleted by cleanup because default git status suppressed them; a P2: changing the candidate in the marker to its approved ancestor was wrongly accepted. This separate child repair keeps the original rejected SHA unchanged, requires external assembly receipt and full clean/ignored status, and adds both exact reproduction cases.

## Objective

Create one reproducible isolated Git checkout from exact source identities, rather than repeatedly combining a moving main. This is **not** a production deployment, a real Solana RPC scan, a Mac service startup, or proof of currently held Frank positions. User rejected the prior UI redesign; no UI change is included.

Fixed reference commits:

| Source | Exact SHA |
|---|---|
| Reviewed PR #71 parent | d998fb5966fac2eee5dbeedca5f78126d1b51b6d |
| main snapshot | 662ba4aceb9d53cb7a541ad3f251f9e12b8c09ea |
| C02 #49 | 8898134a8a302e1187138f7fb3da87a554567e6d |
| F01 #44 | 516e3335a134c608f477019b79027982f43af32a |
| Child integration development commit | required explicit 40-char SHA, frozen at CI trigger time; must be descended from reviewed #71 |

The parent PR #71 has an external code APPROVE at its exact SHA; the new child still requires independent review. Do not silently use moving origin/main or claim merging these inputs in disposable CI changes remote main.

## Entry point and supported operations

Script: crypto-300-profit-mission/local-agent/scripts/frank_pinned_joint_workspace.py

Default mode (PLAN_ONLY): python3 -B -m scripts.frank_pinned_joint_workspace

Default performs NO Git operations, does not read or modify private SQLite, starts no HTTP listener, and issues no RPC.

After separate code review and user authorization, in an existing repository checkout and with exact approved child SHA:

- Assemble: python3 -B -m scripts.frank_pinned_joint_workspace --assemble --source-repo EXISTING_LOCAL_REPO_ROOT --staging-root EXISTING_TEMP_ROOT --name frank-joint-manual-qa --integration-sha REVIEWED_40_CHAR_SHA
- Capture the returned manifest_sha256 **outside the staged tree**, along with the exact reviewed 40-character candidate SHA; keep that assembly receipt immutable, not copied from the later potentially modified marker.
- Verify: python3 -B -m scripts.frank_pinned_joint_workspace --verify --staging-root EXISTING_TEMP_ROOT --name frank-joint-manual-qa --integration-sha REVIEWED_40_CHAR_SHA --manifest-sha256 ASSEMBLY_RECEIPT_64_CHAR_SHA256
- Cleanup only after separate explicit approval: python3 -B -m scripts.frank_pinned_joint_workspace --cleanup --staging-root EXISTING_TEMP_ROOT --name frank-joint-manual-qa --integration-sha REVIEWED_40_CHAR_SHA --manifest-sha256 ASSEMBLY_RECEIPT_64_CHAR_SHA256

Commands are intended for later separately authorized Mac testing. They are not a request to run now.

The staging name must be an immediate frank-joint-* child of an existing staging root; collisions, symlinks, overlap with source, invalid SHA and wrong reviewed parent are rejected. The implementation copies COMMITTED local Git objects only into a new detached temporary checkout, merges pinned source inputs in order, validates ancestry and clean status, and writes a manifest under the **staged .git directory**, not in main or production. The local source checkout, even if dirty, is not reset, stashed, modified or cleaned.

The historical replay branch refs/remotes/origin/evidence/frank-ca-local is copied directly from the existing local Git source, its exact commit SHA is stored in the manifest, and verification requires that ref to remain unchanged in the isolated checkout. If that ref has not been fetched into the source checkout, assembly fails closed. **Do not skip the 1,720-signature historical Git replay tests or silently fetch their input from a mutable remote**. GitHub CI explicitly fetches current remote branch objects into its own local source checkout before assembly, then independently freezes the local evidence ref SHA for that run.

The independent assembly stdout receipt (exact integration SHA plus SHA-256 digest of the whole original manifest bytes) is **required** for both verify and cleanup. The CLI rejects missing receipt values and does not trust the candidate SHA copied from its own marker; changing that candidate to a valid approved ancestor still fails. Neither candidate nor manifest digest is re-derived from the later staged marker for an acceptance decision.

Verify fails on manifest digest mutation, candidate mismatch, historical evidence ref drift, HEAD drift, tracked changes, ordinary untracked files **and ignored** temporary research files. Cleanup repeats the checks and refuses anything in ignored paths such as runtime-local/, *.sqlite*, *.db or .env. Ignored entries are **never** an authorization to delete. Only a strictly clean, verified staged checkout can be removed. This forbids automatic deletion of user-created evidence even if Git's default status would hide it. A staged tree used for live research or tests may accumulate ignored caches; manual cleanup remains blocked until those files are separately preserved and removed by their owner, outside this tool. Neither assemble nor verify/cleanup launches services, so no processes require stop. Later source service startup and shutdown require their own audited manual-only protocol.

## Real integration evidence in CI

Existing Frank CI workflow is extended, NOT a new schedule/LaunchAgent. The disposable joint job now assembles an independently cloned pinned Git checkout using the current reviewed child commit as the fifth input and frozen main; it verifies the SHA manifest before running any tests. Dependencies and native source HTTP integration tests run in the staged checkout, not the source worktree. Tests exercise actual Mission Control F01/C02 HTTP handlers, exact CA identity, F02 native HTTP/32-Mint TTL using **synthetic** dual-program RPC and temporary research-only SQLite, plus all historical regression tests. Separate synthetic Git fixture tests ensure default no-op, correct pinned merge, no source mutation, duplicate destination failure, cleanup safety and git-manifest tamper rejection.

The user Mac private earlier capture has archived 9 nonzero /23 observed-zero out of 32 frozen targets, and observed 3276 token accounts /3276 unique Mints in the same snapshot; that source is older than 300-second TTL. Such archived source cannot prove today's live full-wallet positions, latest sales, PnL, or all-wallet user-facing accuracy. C02's saved report also does not prove full narrative, holders, LP/Dev/funders or market activity research has completed.

## Required subsequent gates

1. Green pinned exact-SHA CI and independent other-AI code review.
2. User-approved Mac read-only preflight: source SHA, isolated test root, existing private full-wire + sidecar, provenance, three unused ports, and zero overlap with production SQLite, Frank V1, Loop and Gmail.
3. Separate manually started isolated native services and true localhost GET acceptance (no production restart or new real RPC). A stale F02 response MUST remain SOURCE_UNAVAILABLE, never an old quantity.
4. Complete the one-mode arbitrary Solana CA research requirements C01/C03-C10 (official exact-CA narrative, holder LP/vault, Dev/funder/first acquisition, risks and evidence) and A05/A06/F02 present-tense complete wallet.
5. Actual user browser product acceptance, independent cross-module/final reviews, explicit production release authorization.

NO_MERGE / NO_DEPLOY / NO_NEW_REAL_RPC / NO_TRADES / NO_GMAIL / NO_PRODUCTION_SQLITE_WRITE / NO_NEW_AUTOMATION.
