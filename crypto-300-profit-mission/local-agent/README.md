# PHASE 1 synthetic local E2E

Status: synthetic-only implementation. No market/RPC collector, HTTP/GitHub runtime adapter, real GPT, real Gmail, automation management or launchd installation exists in this package. The default future runtime repo name is configuration only, never contacted.

Python >=3.11. Create the development environment inside this directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r dev-requirements.txt
.venv/bin/python -m pytest -q
```

Modules run directly from this directory; no global installation required. `pyproject.toml` also supports packaging with pinned setuptools. pytest is development-only; runtime uses Python standard library.

```sh
.venv/bin/python -m mission_agent.cli --runtime-root /tmp/mission-synthetic-demo synthetic-event \
  --event-type TEST_ACTION_CANDIDATE --asset SYNTH \
  --observed-time 2026-09-30T00:00:00Z --priority 1 --seed example \
  --payload '{"fixture_decision":"ACTIONABLE_OPPORTUNITY"}'
.venv/bin/python -m mission_agent.cli --runtime-root /tmp/mission-synthetic-demo cycle
.venv/bin/python -m mission_agent.cli --runtime-root /tmp/mission-synthetic-demo health
```

Omitting `--runtime-root` uses `~/Library/Application Support/CryptoMission/phase1-synthetic`, outside the code repository. Each cycle processes outstanding immutable batches, then one new batch when none outstanding, and retries only Sent reconciliation for uncertain deliveries. Repeat cycles to drain backlog. An expired batch without receipt requeues; a receipt created during its valid period can reconcile after TTL. The CLI must not be run against a real runtime DB.

Full repeatable workload (fresh runtime directory required):

```sh
.venv/bin/python -m mission_agent.cli --runtime-root /tmp/mission-e2e-new synthetic-e2e --events 60 --seed 1729
```

All four fixture labels are explicit test inputs, not locally inferred investment conclusions. `synthetic:v1:<hash>` identities cover canonical observation and seed. Eight delivery states are persisted. Mock Gmail stores provider acceptance independently of failed client receipts. Two local consumers use transactional SQLite lease/fencing; remote CAS is not implemented.

Total 5GB budget includes local files/DB/WAL/provider/transport; conservative admission checks reserve space and stop new ingestion/batches/transport near95%, preserving existing queues. This is a soft budget, not an OS quota. Health samples retain latest1,000; seq never resets. `cleanup` verifies and gzip-compresses acknowledged batch/receipt archives older than7days, retaining pending archives and DB event records. Repeated cleanup is idempotent; compressed artifacts remain readable. DB events are not evicted; admission stop prevents unlimited new event growth. Production retention/resource scheduling remains future scope.

Unknown source/clock/sleep/restart metrics are literal `UNKNOWN`. A synthetic E2E success never makes collectors HEALTHY. External TTL overrides a previous HEALTHY with UNHEALTHY_STALE_HOST.

Policy default is `at_least_once`; `at_most_once` is accepted by the state machine too. Both perform cooldown/Sent-only reconciliation after uncertainty. No automatic uncertainty resend horizon is approved/implemented: a timeout-before-acceptance can remain uncertain and requires reviewed recovery in a later phase. This is not a production AT_LEAST_ONCE guarantee or strict exactly-once delivery.

Runtime data, .venv, caches, DBs and .env are gitignored. Use disposable temporary directories for tests; retain diagnostic outputs outside Git. Real provider capabilities and final production gates remain unverified.

## Phase 2A private GitHub transport

GitHubTransport is test-namespace-only and pins lxxlx2/crypto-monitor-runtime, verified PRIVATE, with logical mac/gpt branch isolation. It obtains existing gh credentials in memory; no credentials are stored in runtime payloads. Existing CLI remains synthetic LOCAL_FILE. Explicit opt-in remote runner: `PYTHONPATH=. .venv/bin/python scripts/phase2a_remote.py --root <private-outside-git-directory> --run-id <unique-test-id> --stage matrix|full|faults`. Full stage deliberately SIGKILLs two worker processes to test SQLite/remote recovery. No real Gmail API or market source is called. Never point evidence/runtime roots inside a Git checkout.

Selected remote batch ceiling (`Config.for_remote`): **75,000 bytes**, based on exact connector readback through 99,000 bytes (24.24% margin). Phase 1 LOCAL_FILE Config keeps its established 100,000-byte fixture default; 100,000 remains the absolute protocol/test ceiling; raising the selected production limit requires separate path-specific verification. Remote publication uses `publish_remote`, persists readback provenance in SQLite meta, and marks REMOTE_CONFIRMED only after exact readback. Explicit previous SHA is required to replace current files; archives are always immutable even through the generic writer. See GPT_CONSUMER_SPEC.md and PHASE2A_INTEGRATION_REPORT.md. Production remains NO_GO; no automation activated.
