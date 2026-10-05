# Frank email template deployment

FRANK_EMAIL_TEMPLATE_UPGRADE_LIVE = PASS

Deployed source commit: `46c989c3ef35d63fc02808c519f73aa3e6ea1513`. Source SHA-256: `599f2f05f197725a25fd85a82501504a772f253866c0556183bbfd82da00a0ce`.

Deployment started 2026-10-04T05:42:17.199943+00:00 and verified 2026-10-04T05:42:56.976746+00:00 (UTC). The branch and remote matched the exact approved commit and the worktree was clean before deployment. LaunchAgent `com.jerson.crypto-monitor-frank-local` runs the Frank-only local-agent worktree with its existing Python environment and unchanged configuration.

One controlled `launchctl kickstart -k` changed PID 57287 to 85524 and restart_count 2 to 3. Stop was requested at 2026-10-04T05:42:27.200109+00:00; this is the command timestamp, not an instrumented kernel exit timestamp. The new daemon started at 2026-10-04T05:42:28.207997+00:00 and completed its first successful poll at 2026-10-04T05:42:30.315284+00:00.

Scanner status RUNNING, consecutive_errors 0, source_drift false. Cursor slot before/after: 453162654 / 453162654. Finalized chain and durable local signatures in the inclusive restart window each contain 1 baseline anchor, with 0 new transactions, missing 0 and extra 0. Raw pending and model unprocessed are both 0.

A consistent SQLite backup was created using the backup API in the private evidence directory. integrity_check = ok; foreign_key_check = empty. Full local-agent tests: 547 passed, 0 failed, 3 skipped; skips are unrelated Monster tests requiring unavailable numpy.

LIVE Gmail delivery rows and Gmail master outbox rows were both 0 before and after deployment. LIVE_GMAIL_IN_FLIGHT = 0. The original Gmail TEST and historical TEST remain in their separate private ledgers; full existing row comparisons confirmed unchanged identities, attempts, message IDs, subjects, bodies and hashes. Duplicate sends caused by deployment = 0; Gmail sends caused by deployment tests = 0. No historical replay, synthetic signal, test notification or test email was performed.

New telemetry reports email_delivery_status LIVE; gmail_pending 0, gmail_sent_verified 0, gmail_sent_unverified 0, gmail_blocked 0, gmail_failed 0. LIVE describes local queue health only and does not guarantee OAuth or provider availability.

Old signals retain their frozen presentation. Future real MULTIPLE signals use the new Chinese presentation; real Gmail validation of that presentation awaits the next natural signal. No signal was created for deployment validation. ACCUMULATION remains local notification only; MULTIPLE remains local notification plus Gmail.

Deployment changed no source or configuration bytes. Protected policy, evaluator, classifier, scanner, store, parser, RPC, registry and V1 policy files match their pre-deployment SHA-256 values. HFT, thresholds, wallet, OAuth and delivery authority remain unchanged. No automation was created and main was not merged. PRODUCTION_TRADING = NO_GO.

Detailed health snapshots, consistent backup, protected hashes, cursor/signature reconciliation and immutable-delivery comparisons are retained privately in `frank-email-template-upgrade-deployment.json`. This report commit is documentation only; the running daemon continues to report the deployed source commit above, and no second restart is required.
