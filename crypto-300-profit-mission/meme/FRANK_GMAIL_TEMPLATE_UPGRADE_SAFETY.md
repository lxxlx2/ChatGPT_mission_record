# Frank Gmail template upgrade safety

Base HEAD: fd1bd37301263f4407104e980507d58695b7e668.
The previously uncommitted presentation changes are retained separately.
This reliability change is not deployed; all providers and ledgers in tests are fake/temporary.

## Authority

email_content = IMMUTABLE_RENDERED_PRESENTATION.
Engine._emit renders a genuinely new MULTIPLE once and freezes its subject/body/content_hash.
GmailOutbox.sync reads that frozen row instead of calling the current renderer.
Once gmail_delivery exists it is the delivery authority for every status: sync
skips it before any content lookup, render, enqueue or mutation. Signal identity,
content hash definition, wire identity and send/ambiguous-recovery gates are unchanged.

## Missing historical content

Normal V1 emission creates signal, outbox and email_content in the existing atomic
transaction. A missing content row is not a normal partial V1 commit. Existing
legacy/manual/migration states can nevertheless lack the row or table.

The old Engine initialization re-rendered such signals with the current template.
That is unsafe across template upgrades. Initialization now restores presentation
only from an existing gmail_delivery row with a matching subject/body content hash.
This copies trusted persisted bytes, never the current template. An existing delivery
row remains untouched. If both frozen sources are absent, the outbox records
MISSING_FROZEN_EMAIL_CONTENT; inconsistent frozen hashes record INVALID_FROZEN_EMAIL_CONTENT.
Historical DRY_RUN_AUDIT status stays forbidden. No invented email is enqueued.
Later valid frozen/new signals continue through sync independently.

No new table or model-state schema is introduced. Engine's model computations,
policy thresholds, stage/episode/signal identity and classification remain unchanged.
Only its presentation compatibility recovery is edited.

## Header compatibility

Only surrounding whitespace of X-Frank-Signal-ID, X-Frank-Content-Hash and
X-Frank-Delivery-Mode is stripped after parsing. Values still require exact equality.
No lowercase, substring or internal-whitespace normalization is allowed. Folded
LIVE, TEST and HISTORICAL_TEST headers pass round-trip tests; internal hash spaces fail.
Subject and complete body verification, SENT labels and wire markers are retained.

## Focused regression evidence

112 passed, 0 failed, 0 skipped for the new template-upgrade suite plus the five
requested delivery/API/V1/historical/local-signal suites at the P0 gate.
Tests cover all seven existing delivery statuses; OLD sent/pending/uncertain rows;
recovery without extra sends; a genuinely new Engine-produced MULTIPLE using NEW;
old live/historical rows not blocking new signals; absent content/table; safe
restart restoration; corrupt frozen hash fail-closed; folded header round-trip.

Known deferred items: HFT_STICKY_EPISODE_VETO and non-USDC coverage. No HFT,
SOL/USDT, quote conversion, classifier or evaluator change is made here.

NO LIVE GMAIL SEND. NO REAL HISTORICAL TEST SEND. NO REAL macOS notification.
NO DEPLOYMENT. PRODUCTION_TRADING = NO_GO.

An additional fake background-worker regression processes OLD and NEW signals
together through the actual asynchronous kick path. Latest combined results
and commit boundaries are recorded in FRANK_EMAIL_TEMPLATE_UPGRADE_REPORT.md.
