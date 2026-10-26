# Issue #207 / D2–D3 — PROPOSED production identity and single-run signing contract

Status: **DESIGN + DETERMINISTIC MESSAGE BYTES ONLY / NOT ENROLLED / NOT AUTHORIZED**.

Parent source: PR216 independent ARM64 Mac `APPROVE_OFFLINE_CODE — D2_SINGLE_FD_HELD_ONCE_TEST_MARKER_ONLY` at fixed `8aa21a04fead8e6a6db326ed8dfa244f9f76192c`. [Attributable reviewer audit](https://github.com/lxxlx2/ChatGPT_mission_record/pull/216#issuecomment-6417376330): F0 588/588, D1 171/171, FD-held once 10/10, OS read-only 10/10, staged source 9/9, patched HTTPS 16/16, D2-A/B/C 10/10/7. This parent permits ONLY disposable TEST marker consumption, not production.

**Why this contract is next:** The only existing three-role Ed25519 checker `f0_l2_d2b_signed_execution_offline.py` accepts **caller-supplied test keys**, uses a `TEST-ONLY` signing domain and outputs a `PRODUCTION_NO_GO` diagnostic. The production registries in `f0_l2_d1_grant.PINNED_LIVE_TRUST_ROOTS` and D2-B `PRODUCTION_D2_D3_TRUST_ROOTS` remain empty. The D1 one-use writer is only rehearsed with OS temporary directories. Additional mock-signature/marker layers will not authenticate a person or permission. This is a specification for the missing REAL trust ceremony and safe execution gate, with **NO real public keys included**.

## 1. Three separately accountable signing authorities

| Role | Exact power in a future reviewed implementation | Required independent provenance |
|---|---|---|
| D2 `user` | Approves a fixed, read-only BSC permit's exact original bytes, code SHA and manifest | Actual user's explicit decision, out-of-band confirmation of public-key fingerprint, fresh challenge signed on a user-controlled device |
| D2 `reviewer` | Independently reviews code SHA and the same permit/manifest; signs a distinctly domain/role-separated D2 statement | Separately accountable human (or formally delegated reviewer), independent key ownership proof and documented review verdict at the fixed SHA |
| D3 `operator` | Approves **one** bounded foreground execution intention bound to both D2 grant and the final code/manifest | Separate enrolled key and actual last-mile human approval; operator proof cannot be inferred from user's D2 signature or a successful test |

All three key IDs, actual canonical Ed25519 raw public bytes and ownership/accountability records must differ. Three labels alone are insufficient; use canonical raw key fingerprints, not PEM-string hashes. **No signer can independently enroll their own key or rotate any role without separate review.** Never place any private key, seed, API token or signing response on GitHub, in this chat, or in CI. Fingerprint alone is NOT proof that the claimed person controls the private key.

### Enrollment ceremony — NOT YET PERFORMED

1. Freeze and independently review the **final future code SHA and complete tracked-source manifest** after the trusted root changes, including Python dependency inventory. Pending/unsigned artifacts cannot grant production release.
2. Each named participant provides only their **public** Ed25519 key and a verified identity channel; an independent reviewer checks identity, role ownership and one fresh challenge signature on domain-specific bytes **without copying a private key**. Record key ID and canonical raw-public SHA256 fingerprint, who checked it, when, and method/evidence location with access controls. Avoid identifying personal details in public repository.
3. Record independently approved trust-root enrollment as a new pinned code change. Root enrollment **must NOT** turn `send_live` on. An authority module may only consume internally enrolled immutable keys (not keys, callbacks or paths supplied with a grant).
4. Only after that code's exact SHA/native tests pass may the user/reviewer prepare a **new** D2 permit for that final SHA; D3 operator signs a **separate** one-shot intent for the same SHA and digest. The code SHA changes whenever enrollment/release code changes, invalidating old signatures; **never rewrite a previously signed SHA** or treat root-enrollment review as an execution authorization.
5. Document suspension, revocation and rotation: changing any key or withdrawal must invalidate pending launches; no automatic old-key fallback, no cross-domain acceptance, no ambiguous overlap windows. Fail closed if proof precedes a later revocation or machine trust changes. Private signing should remain offline, hardware-protected if feasible.

**Human decisions still missing:** participant selection and independent reviewer, accountable operator, machine/OS account, where private proof evidence is kept, and the maximum one-run budgets. Nothing in this PR chooses those people on the user's behalf.

## 2. Proposed role-specific signed messages

Source of truth for exact proposed message byte encoding: `f0_l2_d2_production_signature_spec.py`. This module **DOES NOT sign, verify, enroll or authorize** anything. It is a cross-platform proposal to be reviewed with real signer owners before it becomes normative. It currently accepts explicit caller-provided digest strings ONLY to compute messages, not as attested facts.

- D2 domain: `bsc-f0-d2-production-permit-PROPOSAL-v1`. There are **two different bytestrings**, one with `role=user`, one with `role=reviewer`. Fields, exactly in order: `role`, `grant_id`, `permit_raw_sha256`, `reviewed_git_sha`, `source_manifest_sha256`, `chain_id`, `endpoint`, `methods`.
- D3 domain: `bsc-f0-d3-production-once-PROPOSAL-v1`; `role=operator`. Fields, exactly in order: `role`, `grant_id`, `run_id`, `intent_raw_sha256`, `permit_raw_sha256`, `reviewed_git_sha`, `source_manifest_sha256`, `chain_id`, `endpoint`, `methods`.
- Encoding: a four-byte unsigned **big-endian** byte count of the domain followed by the domain bytes; a four-byte field count; then for each field **4-byte big-endian length + ASCII name + 4-byte big-endian length + ASCII value**. No canonical JSON re-serialization, newline ambiguity, implicit type conversion, float, user-selected domain or optional field. The D2 permit and D3 intent are signed by SHA256 of their **original complete raw bytes**, so semantically identical alternate serialization invalidates reused signatures.
- The proposal fixes chain ID 56, `https://bsc-dataseed.bnbchain.org`, and precisely `eth_chainId,eth_blockNumber,eth_getBlockByNumber`, no additional RPC methods, fallback provider or signing transaction. All digest formats are lowercase fixed-length hex. The grant/run IDs must match the existing 12–80 ASCII `[A-Za-z0-9_-]` convention and differ. Test/rehearsal domains in D1/D2-B can never be interpreted as D2/D3 production messages.
- The exact production Ed25519 proof schema, provenance record, versioning and root deployment must be finalized in a separate reviewed decision. Do not begin gathering real signatures based solely on this `PROPOSAL` domain. **A proposed message is not a signed grant.**

### Signed scope and freshness

The existing strict permit/intent **candidate** parser (`f0_l2_d1_real_sender_contract.py`) requires exact field sets, an immutable reviewed commit, source manifest in D3, grant/run IDs, UTC bounds, caps, shared max-inflight 3, minimum POST gap >=250 ms, three read-only RPC methods, no proxy/WS/redirect/retry, no background and free-only execution. A production evaluator must authenticate all proofs using enrolled keys, compare original D2+D3 bytes and stored physical manifest, then enforce each candidate cap in the **actual** coordinator, not just in a preflight printout. It must reject a promised cap the implementation cannot enforce (for example RAW limit below the fixed existing 2,000,000-byte reader).

Clock validity must be checked at admission AND **again at the actual physical HTTP POST boundary after shared spacing**, using an independently reviewed real UTC source. The current `OfflinePostUTCWindow` and patched ctor timestamps are TEST-ONLY. A Python `request()` invocation time is not a verified on-wire timestamp. Expired, stale HEAD, incomplete RAW, timeout, truncated HTTP, signer revocation, lost child or unverified runtime -> **STOP/UNKNOWN/FAILED, no automatic retry**.

## 3. Production one-time OS grant and directory attack surface

PR213 approves read-only OS-account registry inspection, **not** FD retention. PR216 approves retaining a test directory FD across **the SAME original O_EXCL + marker fsync + directory fsync** in a disposable /tmp root. Neither proves a real account's production lease, cross-session tamper resistance or authority.

A future production design must independently specify:
- Which exact OS account, protected home/root, launch code and filesystem policy hold the irrevocable one-shot marker; the registry's owner cannot trivially reset the nonce by replacing/removing the entire directory. If this threat model cannot be met, production release stays NO_GO.
- Secure FD opening and inode identity from reviewed OS source, holding fixed ancestor/registry FD through marker creation. No caller-provided path, temp override, symlink-following, alternate directory, delete-on-failure or new marker-writing implementation.
- The one grant ID and D3 run ID are consumed/recorded in the **existing** durable writer. A failed fsync or lost parent is `CONSUMED_OR_UNKNOWN`; no reuse, no cleanup, no retry, no alternate recipient.
- A real foreground supervised child under the already reviewed single 3-slot coordinator. The parent kill/hang path must leave no orphan live POST process; all network requests obey original maximum total attempts / global shared spacing, and all RAW/SETTLE records and UTC decisions are durable.
- No actual production directory read, marker creation or expiration attempt is authorized by this document.

## 4. Required release artifact / independent assurance

A future independently reviewed release bundle must bind **exact Git commit**, 212+ tracked F0 files as the tree evolves, SHA256 of every file and loaded module origin, reviewed 11 critical modules plus newly introduced transport/auth/registry files, installed cryptography `46.0.4`, Python binary and dependency bytes. Mere local hashes are observations, **not** remote attestation against a malicious machine owner. Code review must recheck supply-chain and runtime integrity separately from proof-of-key-possession.

Separate evidence:
1. Source review approval for the final code SHA, NOT an old Draft PR's approved ancestor.
2. Three individual identity/ownership confirmation records from independent channels, separate trust-root enrollment code review and revocation state.
3. Exact raw D2 user+reviewer permit signatures, exact raw D3 operator run-intent signature, final source manifest, nonexpired UTC and immutable one-run budgets.
4. A later **new explicit user instruction** authorizing exactly one fixed-scope, foreground, read-only BSC pilot, after all three previous gates PASS.
5. Only then may a production runner be designed/reviewed to consume exactly one OS-fixed grant before a live socket; any trial must have no background daemon, no wallet key, no trades, no WS, no extra providers.

**Until then: no separate scheduler, no actual physical network request, no production key or marker, no live release.**

## 5. What is approved by THIS new PR?

Only proposed deterministic role/domain-separated **message byte layout** and the design for future verified key ownership, rotation, non-ambiguous authorization and runtime isolation. Unit tests should prove counted parsing, role separation, strict hash and ID format, mutation binding, existing TEST domain incompatibility, no socket/open/marker and unconditionally rejecting `send_live`.

This PR must be a Draft child of approved PR216 exact `8aa21a04fead8e6a6db326ed8dfa244f9f76192c`. Run full offline F0 (expected **598** tests = 588 + 10), isolated new test 10, old D1 171, OS readonly 10, FD-held 10, staged source 9, HTTPS ctor 16, D2-A/B/C 10/10/7, UTC 4, budgets 4, hard-stop 5 and child lifetime 2. Compare independent full SHA and actual imported modules on Mac ARM64, or mark Mac UNVERIFIED. Do **not** claim this creates real cryptographic proofs: there is no production trust key, signature verification or authenticated owner in this increment.

Possible exact-SHA review verdict only: `APPROVE_OFFLINE_CODE — D2_PRODUCTION_SIGNATURE_PROTOCOL_PROPOSAL_ONLY` or `REQUEST_CHANGES`. **Even APPROVE never means real production signing is authorized.**

**Hard state: `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`**; NO_DEPLOY, NO_RESTART, NO_RPC, NO_TRADES, NO_BACKGROUND.
