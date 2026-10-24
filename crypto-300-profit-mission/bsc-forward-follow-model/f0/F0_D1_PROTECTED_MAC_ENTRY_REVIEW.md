# F0 D1 protected Mac entrypoint — implementation review, not a live run

**Frozen approved parent:** PR186 SHA `08adde4ef8be33d846645d9bd50b479e19f7a3b0`, independent Mac `APPROVE_OFFLINE_CODE — D1_CONCRETE_SINGLE_COORDINATOR_SCOPE_ONLY`, **473/473 full, 112/112 D1, 9/9 newly added**, zero SKIP. Actual Mac reviewed 170 F0 Git-tracked files, 11 loaded modules, real Python and cryptography 46.0.4 local hashes (73 RECORD hash gaps). No real sockets tested or approved.

## Mainline increment

`f0_l2_d1_protected_mac_entry.py` is the **single explicit Mac supervised entrypoint, in REVIEW-ONLY mode**. Unlike caller-supplied ephemeral signer roots, it prepares for the approved F0 user+Codex model:

1. Mac-only, direct one-shot `--verify-only` CLI. No `--run`, background/daemon, signer/nonce issuer, hidden override, writable result file or environment flag to activate network. `send_live()` **always raises** `D1_MAC_PROTECTED_SEND_DISABLED_D2_D3_REQUIRED`.
2. Read strict candidate raw JSON (max 8192 bytes) through the already reviewed exact-key parser. It must identify this **exact expected reviewed Git SHA** and satisfy already reviewed free BSC endpoint/chain 56, only `eth_chainId`, `eth_blockNumber`, `eth_getBlockByNumber`, max 32 total/24 block/6 head, 3 slots, >=250ms gap, <=60s dispatch, <=5s *socket* timeout, no retries/proxy/WS/redirect/paid/background, explicit short UTC window and 2MB RAW archive limit. In this PR, these are **candidate** scope checks and do NOT create actual D2 approval.
3. From the actual Mac process, import a fixed list of critical F0 modules and invoke reviewed `review_loaded_runtime_offline()`: exact clean checkout SHA, ALL tracked F0 file bytes, actual loaded `__file__` / `__spec__.origin` for each critical module, Python executable digest and cryptography wheel RECORD/gaps; Codex must separately compare released bytes and source. Local readback is **not** OS-vs-malicious-admin remote attestation.
4. Read the **fixed Mac registry path** from the reviewed `PRIVATE_FIXED_REGISTRY` implementation. Require it to match the **OS-account home directory**, not an injected `HOME` or a permit/evidence path; reject symlink components, non-private target modes and overlap with evidence root. Missing registry is clearly **not ready**. This operation **only inspects**, never creates/removes/consumes markers.
5. `datetime.now(timezone.utc)` verifies candidate signed interval but is only a local wall clock, not independently trusted UTC. No real connect and no physical wire timestamp.
6. Return a small JSON assessment to stdout: exact candidate permit raw digest, reviewed SHA, runtime provenance, fixed registry existence, blocked authority, D2 and D3 false, sender-to-coordinator not yet bound, zero network. This diagnostic itself **cannot** become an approved permit by setting fields.

## What this PR does NOT complete

The existing PR186 sealed-memory concrete HTTP code and one-coordinator three-slot / durable RAW evidence remain intact and frozen. **This PR does NOT yet connect the true `http.client.HTTPSConnection` constructor to that coordinator or a permanently protected live grant.** Merely checking a candidate manifest is not user approval. The real D1 launch is still default DENY. The fixed registrar exists in reviewed source, but this entrypoint does NOT call `consume()` until an executable, independently Codex-reviewed real pathway can guarantee consumption+fsync and per-request `RESERVE_UNKNOWN` **before TLS connect**, RAW fsync before SETTLE, actual shared POST-attempt timing and no unknown replay.

Absolute whole-operation deadlines remain separate from the current 5s socket *inactivity* timeout. `request()` call boundary is not proven physical HTTPS first-byte emission. Real socket exception/OS SIGKILL UNKNOWN, provider 3-slot capacity and same-window HEAD-to-commit throughput **remain unmeasured**. No valid D2 exact permit has been requested, and user has not authorized a D3 real run. Old 30-call permit is consumed. **Do not enable a live sender just because this PR's review-only preflight passes.**

## Independent Mac/Codex acceptance

- Confirm fixed PR HEAD/diff SHA vs approved PR186, only expected files, exact Git blobs/SHA256 and clean isolated detached checkout.
- Run full test discovery and focused D1 discovery in existing vetted `cryptography==46.0.4` environment. Verify new tests prohibit all `http.client.HTTPSConnection`, have NO grant consumption, and cover candidate scope/sha invalid, non-Mac, nonprivate roots, symlink/OS-home registry mismatch, expired local UTC, missing registration and denied `--run` or `send_live()`.
- On Mac only, run the command using a **review-only TEST candidate** with an active UTC interval if desired; this is **not** D2/D3 issuance. Do not touch old Mac BSC journal or existing grant. Do not run production launch. Checking module path imports in a detached checkout must not mutate frozen parent. Avoid local long-lived tasks.

**Verdict only:** `APPROVE_OFFLINE_CODE — D1_MAC_PROTECTED_PREFLIGHT_SCOPE_ONLY` or `REQUEST_CHANGES`. This does **not** mean D1 gate completion or real TLS/registry integration. Next concrete task must finish one protected real coordinator+registrar+HTTPS sender gate at a *separate new SHA*, then D2 exact user approval and D3 explicit single-shot execution. No repeat of the old third-human PKI barrier.

**State:** `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`. NO_NEW_RPC / NO_WS / NO_REAL_PERMIT / NO_TRADE / NO_MERGE / NO_DEPLOY / NO_BACKGROUND.
