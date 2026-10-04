# Frank email template upgrade: reliability, presentation and telemetry

## Starting state

BASE HEAD / STARTING HEAD: fd1bd37301263f4407104e980507d58695b7e668.
Branch: codex/frank-only-local-signals.
No clone, reset, clean, checkout discard or live runtime migration was performed.

WORKTREE BEFORE, captured with status/diff/stat/HEAD/branch commands:

```text
 M crypto-300-profit-mission/local-agent/mission_agent/signals/email.py
 M crypto-300-profit-mission/local-agent/tests/test_frank_gmail_delivery.py
?? crypto-300-profit-mission/local-agent/tests/test_frank_email_presentation.py
?? crypto-300-profit-mission/meme/FRANK_MULTIPLE_EMAIL_PRESENTATION.md
```

The initial tracked diff was 2 files, 82 insertions, 9 deletions, plus the two
untracked presentation/test documents. All that work was retained and incorporated.
The original related baseline was 70 passed. The user then explicitly authorized
P0 frozen-content recovery, header compatibility and local health observability.

## New reliability fixes

email_content = IMMUTABLE_RENDERED_PRESENTATION for newly emitted MULTIPLE.
Existing gmail_delivery remains delivery authority; sync never re-renders or
mutates it in any of its seven statuses. If no delivery exists, sync uses the
stored subject/body/content_hash from email_content and validates that hash.
There is no presentation version in the model identity and no hash bypass.

Normal new emission creates signal/outbox/email_content atomically. The previous
constructor migration could nonetheless repaint a preexisting signal using the
current renderer after losing email_content. It now copies an existing trusted
frozen gmail_delivery, or marks MISSING_FROZEN_EMAIL_CONTENT / INVALID_FROZEN_EMAIL_CONTENT.
No old body is guessed; malformed historical content cannot block later valid
new rows. Dry-run rows remain forbidden. No new database table is added.

Only outer whitespace of the three X-Frank identity/hash/mode headers is stripped.
Exact equality remains required; internal whitespace, wrong case/value, full-body
or subject mismatch is not accepted. Sent search, wire markers, ambiguous-send
protection and asynchronous delivery remain unchanged.

## Presentation preserved and refined

Overview now includes complete CA, explicit Asia/Bangkok first/latest buy times,
observed buy/sell counts, latest classified BUY and cumulative quote, inventory
scope, and actual mapped reasons. 多倍信号 is expressly a model-stage name and
not a claim that price will multiply. Path A and B are distinct, freshness does
not invent recent buying, unknown codes display 未识别规则 and remain in audit.
No arbitrary field/environment serialization or price/PnL/symbol lookup exists.

Complete, same-input BEFORE/AFTER fixture emails and hashes are included in
FRANK_MULTIPLE_EMAIL_PRESENTATION.md. They use synthetic fixture_multiple data,
not STONK/live history. Symbol and reliable USD estimate remain unavailable;
lifetime position remains unknown. No real recipient or credential is included.

## Narrow telemetry commit

The service reads the same local summary via read-only summary_from_db.
Unlike a delivery constructor, this reader creates no table or schema. It exposes:
gmail_pending, gmail_sent_verified, gmail_sent_unverified, gmail_blocked and gmail_failed.
Priority: FAILED > SENT_UNVERIFIED > BLOCKED > PENDING > LIVE.
Pending includes PENDING, SENDING and RETRYABLE_ERROR. Missing frozen LIVE content
is also reported as failed even though no sendable delivery row was invented.
Historical/dry rows are excluded from live failures.

LIVE in this telemetry means no outbox risk/pending condition; an empty queue
alone is not OAuth capability or real-send proof. This function never reads a
credential, contacts Gmail or waits for a network worker. No polling/cadence or
scanner/model/delivery gate is modified. These changes are not deployed.

## Validation

```text
P0 TEMPLATE MIGRATION = PASS
OLD SENT SIGNAL + NEW TEMPLATE = PASS
OLD PENDING SIGNAL + NEW TEMPLATE = PASS
OLD SENDING / SENT_UNVERIFIED + NEW TEMPLATE = PASS
NEW SIGNAL USES NEW TEMPLATE = PASS
OLD SIGNAL CONTENT MUTATED = NO
DUPLICATE SEND = 0 (extra resends in fake tests)
EMAIL PRESENTATION = PASS
REASON CODE MAPPING = PASS
HEADER ROUNDTRIP = PASS
HEALTH TELEMETRY = PASS
MODEL_SEMANTICS_UNCHANGED = PASS
CLASSIFIER CHANGED = NO
SCANNER SEMANTICS CHANGED = NO
POLICY CHANGED = NO
HFT CHANGED = NO
PRODUCTION DEPLOYED = NO
REAL GMAIL SENT = NO
REAL macOS NOTIFICATION = NO
PRODUCTION_TRADING = NO_GO
```

File-level disclosure: engine.py was edited ONLY in __init__ presentation recovery.
All its other methods (_emit, _evaluate, process, tick, drain, state/summary helpers)
were compared against the base and are byte-identical. Saying the entire engine.py
file is unchanged would be inaccurate. policy/evaluator/classifier/scanner/store,
parser/RPC and registry files were byte-compared and are unchanged. Service edits
are telemetry; scanner/cadence/network call AST sequences match the base exactly.

Actual commands/results:

- Initial related baseline: 70 passed.
- P0 focused gate: 112 passed; later actual async worker regression also passed.
- Final requested five suites + template upgrade/header + presentation + health:
  140 passed, 0 failed, 0 skipped in 0.72s.
- Full local-agent suite: 547 passed, 0 failed, 3 skipped.
- The 3 skips are unchanged numpy-dependent Monster tests.
- py_compile for all changed Python implementation/tests: PASS.
- Renderer AST checks: no clock-now / network / getenv call: PASS.
- Model file/method bytes and service scanner-call AST checks: PASS.
- Secret scan and forbidden credential/database/env/cache staging check: PASS.
- git diff --check: PASS.

All Gmail providers and notification dispatch in tests are fake/mock/stub, with
temporary fixture ledgers. No live validation, OAuth, runtime SQLite write,
LaunchAgent restart, deployment, real historical send or automation action occurred.

## Commit separation

A: fix: freeze gmail presentation across template upgrades
- gmail.py frozen-content sync + outer-header whitespace normalization.
- engine.py presentation recovery only.
- upgrade/recovery tests, safe migration test setup and safety document.

B: feat: improve Frank multiple email presentation
- email.py local deterministic presentation.
- presentation tests, display-only assertion update and complete BEFORE/AFTER fixtures.

C: fix: report real Frank gmail delivery health
- local summary error visibility, pure health mapping and service telemetry reads.
- telemetry tests and this final report.

Final commit SHA, local/remote equality, clean status and complete base-to-ending
stat are verified in the final handoff. No merge to main is performed.

## Deferred, recorded only

KNOWN_MODEL_REVIEW_ITEM: HFT_STICKY_EPISODE_VETO.
No change to the episode-sticky HFT veto; rolling versus permanent behavior needs
its own authorized replay/review.

KNOWN_COVERAGE_GAP: USDC direct numeric amount gates; non-USDC (including SOL)
amount gates may be UNDETERMINED without reliable conversion; current USDT quote
coverage and complex multi-asset UNKNOWN/AMBIGUOUS routes remain separate review.
No threshold, quote classifier or conversion rule is changed here.

EMAIL_TEMPLATE_UPGRADE_SAFE = PASS
EMAIL_CONTENT_CHANGE_ONLY = PASS (presentation layer; separate authorized reliability/telemetry)
MODEL_SEMANTICS_UNCHANGED = PASS
PRODUCTION_NO_GO
