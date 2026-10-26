# BSC F0 — D2/D3 production-release threat model and authority decision record

**State: DECISIONS_PENDING / DOCS_ONLY / NO_LIVE_AUTHORITY.** No production code change, signed grant, signer enrollment, OS marker, real HTTPS RPC, deploy, trade or daemon. This document is a release decision boundary for [Issue #207](https://github.com/lxxlx2/ChatGPT_mission_record/issues/207), **not** a new source or sender.

## Evidence / frozen source baseline

Independent ARM64 Mac reviewer approved PR #217 **only** for deterministic PROPOSED signature-message bytes, fixed SHA `8362b4048d45b0bd13be4a6e4b6be35ad737819b`, base PR #216 `8aa21a04fead8e6a6db326ed8dfa244f9f76192c`. [Attributed audit record](https://github.com/lxxlx2/ChatGPT_mission_record/pull/217#issuecomment-6418113738). Mac F0 598/598 PASS, D1 171/171, spec 10/10, 0 skips. These approvals do **not** authorize collecting real signatures or a physical-source execution. The PR chain remains Draft/unmerged.

Source-backed inventory at PR #217:
- `f0_l2_d1_grant.py`: `PINNED_LIVE_TRUST_ROOTS = {}`; offline user/reviewer Ed25519 validation accepts *caller-provided TEST trust roots*. `validate_live_trust_roots_not_enrolled()` ultimately denies; `_consume_once_using_open_dirfd` implements atomic O_EXCL + marker/file/dir fsync but does **not** authenticate signer identity or authorize network.
- `f0_l2_d2b_signed_execution_offline.py`: `PRODUCTION_D2_D3_TRUST_ROOTS = {}`; separate *test* D3 operator domain and ephemeral caller public roots. It cannot be repurposed as production verification by passing real key material.
- `f0_l2_d2_production_signature_spec.py`: `PROPOSAL-v1` D2 user/reviewer message with 8 fields and D3 operator with 10 fields. **No production signature issuer, verifier, key pinning, revocation, enrollment, or live release.** The explicit `PROPOSAL` domain is **not yet a normative production protocol**.
- `f0_l2_d2_os_registry_readonly.py`: read-only `pwd.getpwuid(os.getuid())` owner/no-symlink/private-mode and opened-directory inode check; closes FD. A `filesystem_ready=True` diagnostic is **not a lease**.
- `f0_l2_d2_fd_held_one_use_offline.py`: holds a directory FD during single atomic marker consumption only under disposable `/tmp/bsc-f0-once-test-...`. Owns neither a protected cross-run production root nor real nonce.
- `f0_l2_d2_physical_source_offline.py` and `f0_l2_d1_coordinator.py`: distinct staged source reuses the one three-slot global coordinator **only with test-substituted HTTPSConnection**; actual stdlib constructor is blocked; original fake entry and `send_live` deny. Test receipt protects fixture execution order only, not arbitrary Python modifications or production identity.

## 1. Concrete adversaries and guarantees we can/cannot offer

| Threat / failure | Existing evidence | Required production control | Decision |
|---|---|---|---|
| User injects fake public root as a trusted signer | Offline D1/D2-B roots are caller-injectable | Immutable, independently reviewed enrolled production roots; exact real-role public-key fingerprints from independently verified humans | **BLOCKED** |
| User replays old grant/D3 signature under changed code or manifest | PROPOSAL message binds SHA and raw digests, but no verifier/enrolled roots | Final reviewed runtime SHA+manifest attested by a separately protected launch path; strict raw-byte and exact 3-role checks | **BLOCKED** |
| One signer claims multiple role labels / PEM aliases | Offline test compares canonical Ed25519 raw public bytes | Canonical key fingerprints *and independent ownership/governance*, not only distinct IDs | **BLOCKED** |
| Expired/revoked signer or wall-clock rollback | Existing UTC check uses fake clock, production revocation undefined | Authoritative time/expiry policy and revocation version, evaluated before marker and at real POST; rollback -> STOP | **BLOCKED** |
| Same grant spent twice *concurrently* in same stable private dir | O_EXCL/fsync shared helper, tested on temp FD | Exact OS-account fixed directory protected through process lifetime; marker immutable and never reset | **PARTIALLY TESTED** |
| Registry-owning same-UID process deletes marker or renames entire registry *between runs* | Held-FD only protects one critical section; read-only inspector releases FD | Independently administered replay anchor **outside the attacker's write authority**, or explicitly narrower trusted-user threat model accepted by accountable owner | **BLOCKED** |
| Malicious same-UID process monkeypatches Python/source/client/clock | Constructor identity and private test seals are Python objects | Trusted code/process boundary and audited launch artifact; cannot claim in-process Python tokens protect against compromised same UID | **BLOCKED** |
| Unexpected child exit / TLS timeout / partial HTTP response | Offline hard-stop, UNKNOWN, no retry, bounded RAW/FAILED tests | Re-run independently on final production source, same one coordinator and one-shot release, no alternate provider, retry or daemon | **OFFLINE ONLY** |
| Source substitution, proxies, WS or transaction methods | Hard-coded HTTPS host + strict method list under mocked constructor | Fixed production TLS/pinned endpoint and DNS/proxy behavior, no caller-selected factory, secrets, WS or transactions | **BLOCKED** |

**Essential decision:** If a process running as the SAME OS UID may actively tamper with the registry directory or Python runtime, owner-private `0700` and a held directory FD are **insufficient** to guarantee durable replay prevention or trusted signatures. Mac filesystem permissions alone cannot elevate that same-UID process to a cryptographically independent authority. Do not claim this threat is solved by another disposable marker test. If no credible separate authority is available, **production remains NO_GO**. If the owner explicitly elects a narrower threat model (honest user account, no same-UID adversary), document the residual risk and obtain independent safety review *before* implementing a production grant. Do not silently downgrade this assumption.

Root/admin compromise, hardware compromise, malicious upstream TLS endpoint and OS kernel faults are not demonstrably prevented by existing Python-only tests; they remain outside the current proven boundary and require explicit treatment.

## 2. Decisions required from humans before a production-key enrollment PR

All statuses are **UNDECIDED**. Do not prefill with fake identifiers, guessed personal names, keys or test roots.

| ID | Required binding / outcome | Owner and independent review evidence | Current |
|---|---|---|---|
| A1 | Actual D2 user signing authority and custody method | User's separately expressed assent + out-of-band public-key challenge proof; **no private key shared** | UNDECIDED |
| A2 | Actual *independent* D2 reviewer | Independently accountable reviewer, reviewed exact source SHA, separately controlled Ed25519 public key, verified ownership | UNDECIDED |
| A3 | Actual D3 single-run operator | Distinct accountable operator, separate key/consent for one future run; user approval to delegate if operator differs | UNDECIDED |
| A4 | Normative D2/D3 signing protocol version/domain and key revocation | Independent spec decision after PR217 PROPOSAL audit; no real signatures before finalization | UNDECIDED |
| A5 | Real Mac / OS UID / trusted launcher, protected filesystem threat model | Operator and independent reviewer attest fixed OS-account, execution trust boundary, same-UID tamper threat/residual risk | UNDECIDED |
| A6 | External or otherwise protected once-only anti-replay anchor, or formally accepted narrowed threat model | Independent security review with inode/rename/delete and reboot evidence; no user-writable marker reset if adversarial same UID in scope | UNDECIDED |
| A7 | Final code SHA/manifest, dependency inventory, fixed provider/3-method budgets, hard-stop/UTC/RAW | Future independently audited code release, not ancestor approvals or local text assertions | UNDECIDED |
| A8 | Explicit consent to *one* foreground bounded read-only physical BSC pilot | New user instruction **after** A1–A7 and final code review, not this issue/PR | **NOT AUTHORIZED** |

The same person must not silently self-certify all three roles; separate public key labels without independent owners are not sufficient. Roles are accountable human or organizational authorities, not models, generated API keys or an automated fixture.

## 3. Proposed order of gates — all fail-closed and no RPC during design

1. **Approve this threat model and select human owners / OS boundary** (A1–A6). This is a governance decision, not code activation.
2. Freeze and independently review a final normative signing schema and enrollment ceremony; prove real human possession and role distinction in an access-controlled process. Only actual public keys/fingerprints and attestations (no private keys/signatures in repo) may be considered for a **separate** trust-root enrollment change. Enrollment itself must keep the network disabled.
3. Build a release candidate with immutable reviewed code/source manifest/runtime, fixed trusted launcher, strict real D2/D3 verifier, real UTC and same existing coordinator/transport, OS-owned replay anchor and supervised one-shot child. Audit actual source changes at new fixed SHA under no-network mocks.
4. Independently review signer revocation, time rollback, forged diagnostics, mismatched raw D2/D3 payload, duplicate signers, namespace changes, lost parent, pre/post-marker faults and safe real constructor isolation. Failure or uncertainty -> permanent stop for that grant; **no retry, no alternate output, no delete-on-failure**.
5. **Only after A1–A7** may the user decide whether to authorize A8, specifying final SHA, intended OS machine/account, grant/run IDs, one fixed BSC provider, three read-only methods, exact maximum requests/bytes/duration, evidence location, and no production transactions/WS/background work.
6. The actual authorized one-shot run must perform authenticated preflight before consuming marker, consume through one reviewed atomic writer, persist pre-POST RID, enforce final UTC and shared pace at every physical POST, keep failed/UNKNOWN states durable. No extra trial runs or auto-restarts. Any code/authority/OS change invalidates earlier approval.

**Circular SHA avoidance:** First review and freeze *all code and enrolled trust-root data*. Then sign exact final SHA/source manifest/raw D2 and D3 under the separately approved normative domain. Any post-signing source edit invalidates signatures and requires new source review/consent; do not obtain signatures against a moving PR HEAD.

## 4. Explicit rejected shortcuts

- **NO** using PR217 `PROPOSAL` bytes as production signatures.
- **NO** inserting real PEM keys into existing injected TEST `trust_roots`.
- **NO** changing `send_live` or constructor identity check based on a green CI or accepted test receipt.
- **NO** treating `filesystem_ready`, `CONSUMED_OR_UNKNOWN`, temporary marker or Python in-process seal as user consent.
- **NO** a second scheduler, RPC queue or alternate RID/RAW writer.
- **NO** reading actual registry, consuming production marker/nonce, touching old private journals, signing, network RPC/WS, deployment, merge, trading or local background daemon under this documentation-only review.
- **NO** claiming real on-wire pacing, provider block coverage or F0_PASSED based solely on synthetic fixtures.

## 5. Acceptance for this DOCS-ONLY PR

- Compare this document and `HANDOFF.md` only against fixed approved PR217 SHA; PR remains Draft/unmerged.
- Reviewer verifies each **existing-code factual claim** at the exact base SHA, especially empty roots, fake HTTPS constraint, read-only OS registry, shared disposable marker and the proposed signing domain.
- Threat matrix must state which properties are *demonstrated in tests* vs *unverified production controls*. Same-UID directory swap must not be misclassified as solved.
- A1–A8 must remain UNDECIDED/NOT AUTHORIZED without named humans, PEM keys, operational credentials or executable instructions.
- Existing F0 Linux CI may run; no source behavior or test count is changed. A green CI does not resolve threat model or grant authority.
- Possible scoped verdict: `APPROVE_DOCS_ONLY — D2D3_PRODUCTION_RELEASE_THREAT_MODEL_DECISION_GATE` or `REQUEST_CHANGES`. It cannot be an `APPROVE_OFFLINE_CODE` that authorizes real signatures.

**Immutable operational state: `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO` — NO_DEPLOY / NO_RESTART / NO_RPC / NO_TRADES / NO_BACKGROUND.**
