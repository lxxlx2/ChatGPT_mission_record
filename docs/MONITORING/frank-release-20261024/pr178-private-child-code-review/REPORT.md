# Frank D2 private-child candidate — REQUEST_CHANGES (one P2), offline tests PASS; read-only port inventory

## Fixed identity and scope

Candidate branch `research/frank-d2-private-child-port-stable-20261024`; exact head `06cb3597c70a68ee8b3ba91b74fcfa98cc08a828`; base original PR178 `ea9a7715beb4d2a55ae956bf993828cbddcb50e5`. Independent clean detached checkout, candidate remote ref checked again unchanged; original PR178 HEAD also unchanged. Main workspace has unrelated existing edits and was neither switched nor modified.

Exactly four changed files inspected: `wallet_d2_ingress.py`, `test_frank_d2_ingress.py`, `test_frank_d2_http_route.py`, and `PR178_PRIVATE_CHILD_PORT_STABILITY_CODE_ONLY.md`. Exact binary diff SHA256 `4e93e18010ce4fb5abf271f41c208a377de3abe1bf2a2ca0f1821a69af2af072`.

## Independent code verdict

**REQUEST_CHANGES; P0=0, P1=0, P2=1.** No production fault or data loss demonstrated.

### P2-1 — new read/write Git-boundary guarantee contradicts actual reader

[New design line13](https://github.com/lxxlx2/ChatGPT_mission_record/blob/06cb3597c70a68ee8b3ba91b74fcfa98cc08a828/docs/MONITORING/frank-release-20261024/PR178_PRIVATE_CHILD_PORT_STABILITY_CODE_ONLY.md#L13) says “读写均拒绝 Git/worktree”. But [read_d2_source lines208–250](https://github.com/lxxlx2/ChatGPT_mission_record/blob/06cb3597c70a68ee8b3ba91b74fcfa98cc08a828/crypto-300-profit-mission/local-agent/mission_agent/mission_control/wallet_d2_ingress.py#L208) checks owner/modes/types/file identity without testing Git membership.

Actual zero-network filesystem repro: create a separate synthetic directory; initialize it with real Git; place synthetic valid JSON at `control/frank-d2-private/frank-d2-owner-at-slot.json` with0755/0700/0600. Original `query_d2(control,page=0)` returns `BALANCE_AT_OBSERVED_FINALIZED_SLOTS_NOT_LIVE`, not rejection. `probes.json` records this. The original writer really does reject Git, and that guard remains unchanged.

Minimal change: if exporter-only Git exclusion is intended, correct the new document to explicitly distinguish writer enforcement from reader permissions/identity checks and operator preflight. If read-side exclusion is intended, implement it and add actual Git/linked-worktree reader tests. Do not claim an unimplemented read-side guarantee. This is a **new documentation/acceptance-contract inconsistency**, not a newly introduced Git-reader runtime vulnerability; the base reader also lacked Git discovery.

A second characterization probe shows a symlink in an ancestor (`alias/control`, final root itself ordinary) is accepted. Final-root, direct-child and source-file symlinks are rejected. This inherited limitation is disclosed, **not raised as another new P2** or used to expand scope.

## Successful boundaries and tests

- Private child path only; no fallback to legacy root filename. Missing child is UNKNOWN, never zero.
- Legitimate shared0755 / child0700 / source0600 accepted; shared root mode stays0755.
- Final-component symlink/unsafe mode tests pass. Independent selective stat mocks for wrong owner at root/child/source all reject. These owner tests are **mocked**, not actual chown/cross-user Mac proof.
- Original schema/provenance/self-check remains unchanged; checksum is not authentication. Multi-account integers, exact Mint lookup, page boundaries, zero-vs-absent and dated non-atomic states retain coverage.
- Exporter blob is unchanged at base/head: `7709dec5a749a10d75596b46b8afa818970e0f2b`. No production data transformed/imported.
- Handler remains same-origin explicit GET on the existing Dashboard. No new bind/server/job/port/POST/RPC or production writer in this four-file patch.

Actual Darwin arm64 Python3.14.7:
```
python3 -B [isolated runner, unittest modules]
test_frank_d2_ingress
test_frank_d2_http_route
test_frank_d2_private_output
test_frank_d2_owner_at_slot
55 run / 0 failures / 0 errors / 0 skipped
```
Actual Node24.18.0:
```
node --test tests/test_frank_d2_ingress_ui.mjs
6 pass / 0 fail / 0 skipped
```
**61 named tests pass**. Parent/children macOS sandbox denied network; Python socket bind/connect disabled; empty environment and isolated HOME/TMPDIR; writes restricted to disposable test storage/checkout. No dependency installation. Private output suite used real synthetic Git repositories/linked worktree. The system git shim emitted an xcrun-cache write-denial warning, but tests all passed. Independent probe runner initially referenced a nonexistent Homebrew git binary; corrected only that disposable runner to the already installed CommandLineTools Git, then probe completed. No product/test assertions changed.

Independent read-only reviewer (PUBLIC source-only material; no private listener argv or local data sent) returned NEEDS_CHANGES for the same P2 documentation issue. Review JSON preserved.

Patch-risk recommendation `revise`, workflow `revise`; moderate impact/likelihood, partial protection, managed future recovery, high confidence. Structured assessment schema validator exit0. A passing offline suite cannot repair a contradicted contract or authorize merge/import/deployment. No subject edits made.

## Actual LISTEN snapshot (read-only)

Observed UTC2026-10-23T23:45:39.734426+00:00 / Bangkok2026-10-24T06:45:39.734426+07:00. `lsof -nP -iTCP -sTCP:LISTEN` returned15 IPv4/IPv6 socket rows, **12 distinct TCP port numbers / 8 processes**; no warning. Mapped current process metadata and user launchd PID ownership without HTTP probes.

|Port(s)|Actual process / role|Decision|
|---|---|---|
|127.0.0.1:8766|Frank Dashboard; exact dashboard launchd label matches|Required; keep. Future D2 must reuse this same service|
|127.0.0.1:8765|python3.13, `dashboard_server.py`; ancestors Python→uv→launchd|Actually listening, separate Dashboard; necessity unresolved, keep|
|127.0.0.1:48721|python3.13|Purpose unresolved, keep|
|*:5000, *:7000|ControlCenter|System application; specific function not probed, keep|
|*:58720|rapportd|macOS system role, keep|
|127.0.0.1:20017|NeteaseMusic|User application, keep|
|127.0.0.1:53998/53999/54027|Antigravity|Development application, keep|
|127.0.0.1:54000/54001|language_server|Development tooling, keep|

**Confirmed redundant listeners:0.** A purpose not yet established does not prove redundancy. Historical Frank178 fixture64103/64738 were absent from this actual snapshot. 8765 is now actual OS evidence, not an inference from a parser default. No service was killed/migrated/merged or reconfigured. Other modules' independent responsibilities were preserved.

## Safety and stopping point

`NO_NEW_LISTENER / KEEP_8766 / PROD_WRITES=0 / EXPORTER=0 / NEW_RPC=0 / PROD_HTTP_GET=0 / RESTARTS=0 / DEPLOYS=0 / MERGES=0 / NOTIFICATIONS=0 / TRADES=0`.

Only synthetic offline data used. No production SQLite, private raw/receipts/balance/source import, directory chmod or service writes. Product candidate and original PR178 remain unchanged. Temporary review checkout removed clean at closeout. Evidence branch only, no new PR.

Stop after this scoped review. Resolve the one documented P2 before code approval. Production child creation, real import and Dashboard-only deployment each remain separately authorized later steps.
