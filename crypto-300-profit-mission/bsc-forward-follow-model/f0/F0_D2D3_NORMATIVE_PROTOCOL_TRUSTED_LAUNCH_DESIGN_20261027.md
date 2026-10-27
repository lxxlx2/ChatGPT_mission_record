# BSC 前向跟单 F0 D2/D3：正式授权协议与可信前台启动候选设计

Date: 2026-10-27 Asia/Bangkok
Status: `DESIGN_CANDIDATE / A4_A5_NOT_DECIDED / NO_REAL_SIGNERS / NO_GO`
Scope: BSC wallet/address L1 acquisition and subsequent L2/L3/L4 feasibility research. No Monster, Frank, monitoring, alerts or trading.

## 0. Authority, intent and what is actually frozen

- Architecture source: Draft PR #113 at `9134fcd41df49ef836b81c8a040974ad89c1fde1`; F0 preparation: Draft PR #116 at `cf88cd9f6568502f5c052ae3befc9cc16cbab98b`. Do not redesign these.
- Last independently approved **code**: PR #217 at `8362b4048d45b0bd13be4a6e4b6be35ad737819b`. It only implements an offline `PROPOSAL-v1` signing byte **encoder**. Its production roots remain empty.
- Production security decision framework: PR #219 `1b35156710a860ae579c0e2ff1fd47d8f1052ad5`, DOCS_ONLY-approved.
- Human A6 limited decision: PR #221 `9c847bb684681b93dc16c206df917d07cb26ef85`, independently reported `APPROVE_DOCS_ONLY — A6_TRUSTED_ACCOUNT_THREAT_MODEL_DECISION_SCOPE`. The user accepts **trusted operator Mac account, no adversarial same-UID process**, for one future **bounded, free-only, read-only, foreground** F0 pilot; malicious same-UID registry reset and Python/clock/source tamper remain outside protection.
- This document designs an **A4 normative candidate and A5 launch contract for independent review**, without selecting actual identities, public keys, registries, runtime machine or budget. The protocol is **not** normative until independently accepted and committed in a separate explicitly approved change. It is not a user signature, network grant or tested implementation.

**Objective:** make a future real foreground read-only F0 event/Router-control source possible under the already chosen safety model, with one reviewed code SHA, the **existing unique three-slot coordinator**, exactly one globally paced request ledger, durable RAW/UNKNOWN and no auto-retry. Avoid repeating disposable signer/marker wrappers that do not close this human trust boundary.

## 1. A4 candidate: immutable bytes and roles

### Three distinct accountable principals

1. `D2_USER`: the actual user authorizes exactly the original raw D2 *permit* bytes. Evidence must establish their own public-key control and affirmative scope consent.
2. `D2_REVIEWER`: a separately accountable human/organization independently reviews exact candidate code SHA, manifest and D2 permit; control of a distinct independently verified public key is required. A model's written APPROVE alone is not a cryptographic identity.
3. `D3_OPERATOR`: a separately accountable operator signs exactly one *run intent* after the final source/permit freeze and before the only foreground attempt. An operator's key, ownership and intent must be distinct from the two D2 roles. If operated on behalf of the user, delegation still needs explicit user consent and independent provenance.

Role labels, differing PEM encodings or fingerprints alone **do not prove different owners**. Verify canonical raw Ed25519 public bytes, distinct key ownership and the human mapping. A1/A2/A3 remain `UNDECIDED`. No key collection, ownership check, challenge issuance or enrollment is authorized here.

### Candidate production domain separation

A future independently adopted implementation may use **new production** domains, for example:
- D2: `bsc-f0-d2-production-permit-v1`
- D3: `bsc-f0-d3-production-once-v1`

The literal strings above are **review candidates, not live-accepted domains**. PR217's `bsc-f0-d2-production-permit-PROPOSAL-v1`, `bsc-f0-d3-production-once-PROPOSAL-v1` and D1/D2-B TEST domains must always be refused by a future live verifier. Do not simply delete `PROPOSAL` from the old module or reuse TEST key injection as a production trust store.

For byte encoding, retain PR217's reviewed shape unless an independent protocol decision requires revision: 4-byte unsigned big-endian domain length, domain bytes, 4-byte big-endian ordered field count, then for each field 4-byte big-endian name length/name ASCII and 4-byte big-endian value length/value ASCII. No whitespace/JSON reserialization of signed messages. Accept exact lower-case 40-hex SHA1 and 64-hex SHA256 with fixed lengths; reject duplicate fields, unknown fields, malformed count, role alias, repeated public key, alternate domain and non-ASCII.

Proposed D2 field order retained exactly from PR217: `role,grant_id,permit_raw_sha256,reviewed_git_sha,source_manifest_sha256,chain_id,endpoint,methods`; D3: `role,grant_id,run_id,intent_raw_sha256,permit_raw_sha256,reviewed_git_sha,source_manifest_sha256,chain_id,endpoint,methods`. D2 `role` must be `user` or `reviewer`, D3 must be `operator`. The raw SHA256 values cover the **original full raw permit/intent bytes**. Role-specific Ed25519 signatures are made over the final domain-separated encoded messages; the verifier must not accept caller-provided public roots or arbitrary encoding.

Protocol constraints fixed for this candidate only: BSC chain 56, `https://bsc-dataseed.bnbchain.org`, and exactly `eth_chainId`, `eth_blockNumber`, `eth_getBlockByNumber`; no `eth_getLogs`, `eth_call`, WS, wallet signing, transaction send, fallback, paid source or alternate host. `grant_id` and `run_id` must be distinct, unique, 12–80 characters from `[A-Za-z0-9_-]`. Actual request and time ceilings shall come from a future separately reviewed literal permit; **no number is authorized by this spec**.

### Original raw permit and D3 intent validation

- Use strict, pinned parse schemas already documented in `f0_l2_d1_real_sender_contract.py`; enforce exact keys/types and no duplicate JSON keys or JSON NaN/Infinity. Hash original bytes **before** decoding. Re-encoding to normalized JSON must never change signature verification.
- D2 and D3 must agree on the same final SHA, manifest hash, grant ID and permit hash; D3 additionally carries the distinct run ID, one-shot scope and bounded UTC. D2 user/reviewer each independently sign the same original permit digest under their respective roles. No role can self-approve on the others' behalf.
- Source-manifest binding: fix and review the complete code/dependency set first; compute a deterministic, sorted inventory of the **actual** fixed Git tree objects, loaded Python source bytes, Python executable and installed dependency wheel/version hashes, then hash the **external derived manifest**. Keep this derived manifest out of its own file-hash input to avoid recursive hashing. A manifest is observational evidence under trusted account, not a remote attestation.
- **SHA circularity avoidance:** enroll and independently review eventual trusted public roots in a separate commit **without enabling live source**. Freeze the **final released source SHA** and external manifest after all implementation/review changes. Only then request new D2 signatures for that fixed SHA followed by D3 intent. Any later source edit, dependency change, new root/revocation state, or launcher modification invalidates the signatures and requires a fresh code review and fresh consent. A moving PR HEAD can never be the signature target.

## 2. A1/A2/A3 real identity provenance and revocation proposal

This is a *process for future independently authorized enrollment*, not an invitation to send signatures or keys now.

- Independent reviewer verifies each proposed principal's accountability using a separately agreed channel; record only role, consent authority, key identifier, **canonical raw public-key SHA256 fingerprint**, verification method, reviewer and sealed evidence reference. Public keys alone and a model response cannot establish human ownership.
- Future possession challenge must include nonce, purpose, role, explicit domain, expiry and frozen source reference, and must be verified out-of-band; no reusable challenge proof grants source release or network access.
- Maintain a small externally reviewable trust-root / revocation manifest in the code review bundle with `role,public_key_fingerprint,version,valid_from,valid_until,revoked_at` (future actual schema to be approved). Reject absent, duplicated, expired, revoked, self-verified, swapped or mixed-version roots.
- Revocation before attempted execution aborts with `AUTHORITY_REVOKED`; any root/identity change after freeze invalidates grant and intent. Fail closed if the revocation source cannot be verified. No stale-key fallback or blanket "approved once, valid forever".
- Private key material, seed phrases, signing devices and challenge responses must never be committed, pasted into chat, uploaded to CI or written to public logs. Enrollment of actual keys and verification of real people need a separate explicit authorization and independent review; **none occurs in this PR**.

## 3. A5 candidate: source-pinned trusted foreground launch

A5 is still `UNDECIDED`: do not infer real UID, home, machine or private evidence path from former temp tests.

The later launcher must be the **only** reviewed entry to production mode. It shall verify these in the stated order, failing without network or marker on any unmet precondition:

1. Confirm approved fixed OS account identity from the real system passwd entry and a user-approved fixed launcher/executable location. Refuse env overrides (`HOME`, custom URL, `PYTHONPATH`, dependency root, arbitrary output root, proxy), symlink/path/UID mismatch, unexpected privilege boundary, dirty code and unexpected module origin. This verification does not protect against an intentionally compromised same UID, per A6.
2. Reconstruct the exact independently audited immutable Git HEAD/tree and full source/dependency manifest. Verify time-bound real D2 and D3 role signatures using **pinned reviewed roots**, their ownership/revocation data, the **original raw** D2/D3 bytes, frozen source SHA, fixed BSC chain/host/methods and the exact caller-independent budget.
3. Check real UTC against signed interval at preflight, detect backward wall-clock discontinuity against monotonic timestamps during the run, and abort if clock validity cannot be justified. Store all intended deadlines and measured actual times separately; no wall-clock rewrite of first-seen activity or post-hoc quote timestamps.
4. Bind the single genuine `grant_id` and `run_id` to the single OS-account-fixed protected registry. Hold reviewed directory FD and use the **existing O_EXCL + file/dir fsync writer**. Do not change marker format by silently adding another registry. Under trusted account, this prevents honest concurrent reuse and preserves a durable record if the directory remains intact; it **does not defend malicious same-UID cross-session deletion**. If marker is present or consumption uncertain, stop without retries.
5. Within the **one original three-slot coordinator** persist exclusive RID/`RESERVE_UNKNOWN` to stable private storage **before any real HTTPSConnection constructor**. No separate scheduler, sender, queue or receipt writer. Verify shared global >=250 ms pacing and final fresh real UTC/budget/HEAD at the last POST boundary; use fixed TLS verified origin, no redirects, proxies, alternate transport or arbitrary factory.
6. Persist bounded raw responses and SHA256 before settlement. Preserve `UNKNOWN` or `FAILED` for network/partial body/reorg/clock/parent loss, no invented full RAW, no automatic retry or alternate output directory, no silent missing block. Confirm contiguous parent hash only from actual verified data, preserve known unattempted and sampled-vs-committed denominators. Never imply E2/E3/actual QUOTED from transport success.
7. End after the one predefined bounded foreground attempt. No daemon, restart, scheduled task, wallet signature, trade or notification. On process kill/hang, orphan child must be bounded and irreversible grant remains spent/UNKNOWN. No automatic recovery run.

The actual `http.client.HTTPSConnection` remains **disabled** at all public entry points until a **separate code PR** is independently audited at a new SHA, real trust-root enrollment is reviewed, and the user later specifically authorizes exactly one A8 pilot. No production mode flag can be enabled by this design alone.

## 4. Explicit release state machine and stop conditions

| State | Meaning | Permitted next action |
| --- | --- | --- |
| `DESIGN_ONLY` | This document, PR217 proposal, and A6 docs review | Read, compare, independently audit docs; no keys/network |
| `PROTOCOL_REVIEWED_NOT_ENROLLED` | A4 candidate independently accepted in a future fixed SHA review | Separate human decisions, future signer/launcher enrollment review; still no RPC |
| `IDENTITIES_AND_RUNTIME_REVIEWED_NO_RUN` | A1–A5/A7 separately evidenced and approved, final source frozen | Request a fresh bounded A8 user decision; still no run |
| `A8_EXPLICIT_ONE_SHOT_GRANTED` | User independently approves one exact SHA/manifest, grant/run IDs, Mac UID, UTC, method/attempt/byte ceilings and private output root | One new independently validated permit and **single supervised foreground read-only attempt only** |
| `CONSUMED_OR_UNKNOWN` | Grant used or any uncertainty/partial failure | Stop, preserve evidence, **no retry and no permit reuse** |
| `F0_REPORT_READY` | Actual accepted/rejected/raw evidence analyzed after permission | Evaluate F0 completeness/latency/quote-control feasibility; never silently infer PASS |

**Perpetual hard stop until independently changed:** production keys missing, source manifest unresolved, unsigned/stale proof, malformed domain, reviewer not independent, same-account governance unresolved, real UID/launcher mismatch, marker cannot be safely consumed, UTC unverified, any attempt over signed cap, or public live entry still denying -> `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`.

## 5. Next code review acceptance, after design is independently reviewed

A *later* isolated code PR may replace the **proposal-only** message validator with a reviewed pure production-domain validation implementation and **default-denied** trusted-launch preflight. It must have:

- An independent golden-byte implementation for D2 user/reviewer and D3 operator; reject PR217 PROPOSAL, D1 TEST and D2-B TEST domains; altered raw permit/intent, swapped roles and duplicate key IDs reject.
- Invalid signature/unspecified human provenance/revoked root/expired UTC/wrong hash/wrong method/cap/budget/foreign UID/symlink/dirty dependency or SHA all reject before any genuine socket or marker.
- A precise check that the future production code derives source identity internally, never from a caller-supplied `approved: true`, test capability, mock object, root map or output path.
- Integration with the **existing** three-slot start lock / exclusive journal only; patch **all real HTTP/socket constructors** in offline tests and verify no alternative sender was added.
- Crash and partial read denial including presend UNKNOWN, RAW-before-SETTLE, no retry, no on-wire timing or profitability claim. Negative tests for forged quote/swap/first-received time remain.
- Fixed new HEAD plus exact diff/source blob checks, full Linux CI and independent actual Mac ARM64 review. A green CI cannot attest real person identity or release privileges.

**Stop after this reviewable design** if actual accountable principals, normative domain approval or OS launcher remain unselected. Do not expand into more purely synthetic key/marker micro-PRs; no fake enrollment and no silent relaxation of A1–A5/A7.

## 6. Decision checklist for independent DOCS-ONLY reviewer

Verify that this is a practical **candidate** using the PR217 encoder and existing code, with no hidden promotion of `PROPOSAL`; role ownership, raw-byte/digest, exact freeze and revocation rules are internally consistent; A6 assumed honest same-UID but explicitly accepts residual malicious-owner risk; same existing RID/RAW and three-slot source is preserved; and final implementation and A8 authorization remain separately gated.

Allowed result: `APPROVE_DOCS_ONLY — D2D3_PROTOCOL_TRUSTED_LAUNCH_DESIGN_SCOPE` or `REQUEST_CHANGES`. It cannot approve A1/A2/A3 actual signer ownership, A4 as installed normative code, A5 as verified Mac, A7 final release or A8 real RPC.

Global operational state: `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`.
No merge, deployment, restart, RPC/WS, production keys/signatures/markers, old private journal access, background service, email, alerts, automations or trading.
