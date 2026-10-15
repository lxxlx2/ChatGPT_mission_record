# Independent read-only F02 manual refresh review

Verdict: APPROVE for the bounded code change. No reportable P2 or higher issue found. This is a separate agent review, not an external product review, live chain observation, or independent Mac browser business acceptance.

Reviewed checkout `/Users/jerson/Documents/ChatGPT/mission-f02-refresh-20261015`, fixed HEAD `a20a9f972589e34d2eae435c2ee4696eb53bb1d7`, comparison base `a59e423304cb2081aef359c0649245c7e1d05b48`. HEAD checked before and after and clean `git status --short` confirmed. Six changed files reviewed including formal development rules, source refresh workflow, manual CLI, UI labels, workflow and tests. No repository source modifications.

## Actual independent execution

Python `/tmp/frank-pr59-review-venv/bin/python`; cwd `crypto-300-profit-mission/local-agent`.

- CI-equivalent focused suite: manual refresh, F02 R1/R2, frozen32, complete RPC receipts, latest inventory: **85 passed in 7.00s**.
- Additional suite with chain capture normalization in place of complete receipts: **89 passed in 4.35s**.
- `node tests/frank_f02_r2_render.cjs`: PASS for loaded-source TTL expiry, background visibility, filters/copy, fresh/stale/metadata conflict. This is real JS execution with DOM test harness, not a native browser claim.
- Actual default module invocation returned `PLAN_ONLY`, `network_invoked=false`, `sidecar_created=false`, `source_ttl_seconds=300`. Its focused test guards network invocation and verifies no session directory is created.
- Independent additional probe `/tmp/frank_f02_independent_probe.py`, using synthetic complete owner responses and real wire replay/SQLite/loopback socket: PASS. Reconstructed a second `ResearchPositions` object from the new session files and read valid quantity. All files/directories inside new session had zero group/world permission bits. Real HTTP returned page/API 200; `/wire/manifest.json` and `/positions.sqlite` 404; hostile Host 403; mismatched wallet query 400. Second synthetic partial attempt made exactly two calls, returned no service, and preserved prior SQLite bytes. At source time +301s, all 32 rows became SOURCE_UNAVAILABLE. Appending one byte to source file caused new service startup to fail with OWNER_RAW_RPC_BYTES_SHA_MISMATCH.

Probe initially needed `PYTHONPATH=.` because it was placed outside repository; its tempfile root needed `.resolve()` because macOS `/var` is a symlink and evidence intentionally rejects symlink ancestors. Both harness corrections were made only in /tmp. Initial pytest invocation also emitted unrelated cleanup warnings from older pytest temporary trees; subsequent separate basetemp runs completed without those warnings.

## Static conclusions

CLI reserves loopback port before acquisition or SQLite writes. Fixed session root plus UUID session names prevents this CLI from selecting existing research or production DB destinations. Complete dual-program manifest and replay are required before new SQLite capture; incomplete source immediately returns no service. Source/roster reconciliation is applied before serving. ResearchPositions replays original bytes and gates matching capture hash and 300s age. Shared collector performs bounded finalized owner queries, enforcing second-program minContextSlot, HTTPS-only transport, no redirects, response-size/framing validation and redacted transport errors. HTTP has fixed literal resource mapping and does not expose private wire or SQLite files. Source/UI diff leaves the approved TTL JS unchanged; page labels now clearly distinguish local filtering from acquiring a new observation and arbitrary CA analysis.

Code review approval does not satisfy real RPC authorization, new-source native Mac interaction, whole F02-R3 completion or joint final product acceptance. No live RPC, production access, deployment, merge, automation, Gmail or trades were performed. The synthetic acquisition proves workflow behavior only and cannot establish current Frank holdings. Keep Draft/NO_MERGE/NO_DEPLOY gates until separately satisfied.
