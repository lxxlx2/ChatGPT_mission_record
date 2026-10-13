# Independent PR41 forward recovery review — 2026-10-13

Reviewed input: c4fe6a62c455a79b792ee743f13d342e15bc8aee.
Product release remains pinned to 52d43d18ee5a6d87408bc68d4832869fce8817a9.

Original input disposition: REQUEST_CHANGES. Three operational correctness findings:

1. High: recovery calls legacy_scanner_snapshot, which deliberately strips dynamic state. A pinned PID and unchanged source can coexist with a stale/error polling heartbeat. No recovery cursor baseline or monotonic checks existed. Fix: scanner_guard verifies poll freshness, status, PID, loaded digest, policy, source_drift, NO_GO, protected config files and cursors; rechecks before migration, before Loop and before success.
2. High: exception cleanup called launch() before bootout and skipped unloading on RuntimeError/CalledProcessError. A loaded KeepAlive job with no current PID raises LAUNCH_PID; an orphan may survive successful bootout. Fix: disable both roles, always attempt bootout, independently verify service absence, wait for scoped workers, and persist/report residual_worker_pids (null means inventory unavailable), with cleanup errors. This is fail-closed reporting, not an OS-level guarantee of termination after failed disable/bootout.
3. High: success never revalidated the Dashboard after Loop startup or verified a unique final worker set. Extra scoped Loop or a failed/restarted Dashboard could coexist with success. Fix: prove Loop absence and Dashboard-only worker set before Loop start; prove exact two-worker set and unchanged runtime identities before success.

Tests add stale/future/error/drift/policy heartbeats, regressed/replaced/deleted cursors, no-PID bootstrap failure, orphan after unload, duplicate Loop, and real child SIGKILL at INIT, every R checkpoint and every mutation/start intent. Git/SQLite/backups/migration/journals are real temporary resources; launchd, worker table and HTTP remain simulated. No production action is performed by these tests.

SQLite inspection: running databases use mode=ro and sqlite3 backup (including WAL); backups use O_EXCL and integrity checks. Only sealed incident backups use immutable=1, avoiding sidecars on historical backups; it must not be applied to the live scanner DB. Migration is additive DDL inside BEGIN IMMEDIATE with schema/FK/integrity checks. Historical rows are compared byte-for-value before start and retained after start. No backup restore, historical resend or old runner restore is performed.

Interruption contract: persisted journal prevents automatic repeated recovery; an existing directory also makes mkdir fail if killed before initial journal. Each mutation/start has a persisted intent. SIGKILL cannot execute cleanup: after enable/bootstrap, new services may remain enabled/running. Operators must inspect journal, disabled registry, loaded jobs and residual workers before separate manual remediation; never delete the attempt directory to retry. A checkpoint test proves repeated execution is blocked, not that killed processes perform cleanup.

macOS compatibility: the review host's launchctl(1) documents enable/disable service-target, bootstrap domain-target plist, and bootout service-target, exactly as Mac.start/hold/stop use them. No production launchctl mutation was executed. Actual service bootstrap behavior on the affected Mac remains unverified until separately authorized recovery; a prior read-only plan cannot prove startup.

Runtime boundaries: scanner PID 52300/source digest and incident identity are intentionally specific to this outage. Scanner restart blocks recovery. Terminal historical Gmail/manual-review rows remain intact; future notifications can occur only during authorized Loop startup, so tests do not claim no future sends. Recovery never starts the old Loop or touches scanner launchd lifecycle. Failure may leave orphan workers, which are now explicit blockers rather than silent success.

Release decision: original SHA is rejected. The patched candidate requires exact-head full CI success and a fresh affected-Mac read-only --plan using its new tool SHA. Code review approval does not authorize deployment. This review session forbids production recovery, Mac service restart, Gmail, production SQLite writes and trading.

Exact patched commit and CI results are recorded in the final chat report; workflows run on this commit through the existing PR41 branch triggers.
