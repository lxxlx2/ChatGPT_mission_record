# F0 D2/D3 actual HTTPS source: one-coordinator design and stop gates

Status: PLAN_ONLY / NO_NETWORK / NO_MERGE / NO_DEPLOY.

This plan neither implements nor authorizes real BSC requests. Do not infer cryptographic approval or live permission from Mac D1 acceptance or GitHub CI.

## Pinned prior approval and purpose

Inherited scope: PR199 at 15ac0ed4dbb839d785546d71b3accd5b232df942, parent PR198 ee8528fb7de98efd40de3ac5035dc29a56cf644b. Independent reviewer reported APPROVE_OFFLINE_CODE — D1_CHILD_FINAL_FAKE_POST_UTC_ONLY; 526/526 F0 and 165/165 D1 on Darwin ARM64; 4 UTC, 10 physical ctor, 4 budgets, 5 hard-stop and 2 child-lifetime tests passed. Report archived: https://github.com/lxxlx2/ChatGPT_mission_record/pull/199#issuecomment-6397222150. Local evidence is on reviewer Mac, not accessible here. An old PR199 SHA 6859a497... remains REQUEST_CHANGES and is not approved.

This remains the BSC F0 forward-follow discovery lane, not Frank, Monster or wallet-modeling. No trading or autonomous local scanner is in scope.

## Current code and its non-equivalence to real permission

- f0_l2_d1_coordinator.py owns the ONE 3-slot scheduling lock, RID allocation, RESERVE_UNKNOWN fsync BEFORE transport, RAW fsync BEFORE SETTLE, and contiguous block commits. Its run_fake_concurrent exact whitelist is fake-only and must NOT be quietly relaxed.
- f0_l2_d1_concrete_https.py has the fixed verified TLS constructor call, one HTTP POST, bounded RAW, and rejected-RAW classifications. In D1 the constructor is patched or memory backed, and send_live always denies. The review-only private primitive is not a security authority.
- f0_l2_d1_protected_mac_entry.py and f0_l2_d1_real_sender_contract.py bind D2/D3 candidate shape to approved code/manifest and the virtual TEST UTC. The JSON D3 candidate is UNSIGNED and is not human consent.
- f0_l2_d1_grant.py has two-role Ed25519 TEST verification, but PINNED_LIVE_TRUST_ROOTS is empty. OfflineGrantRegistry accepts caller paths and MUST NOT be promoted as a production issuer.
- f0_l2_d1_hard_stop_once.py supervises ONE patched HTTPS fake child, permanently consumes a disposable TEST marker and preserves UNKNOWN on parent loss or timeout. It is NOT a live child.

## Ordered implementation milestones in separately reviewed Draft PRs

### D2-A — fail-closed real physical source admission seam, offline only

Design an exact future physical source type and explicit admission hook in the SAME coordinator. Admission must be rejected BEFORE any evidence directory creation, RID reservation, test or production marker, or HTTPS constructor until independently reviewed production authority exists. No new pool, scheduler or writer. The fake-only entry remains fake-only. Never add a generic transport callback or arbitrary factory that can turn a test grant into a live sender. A candidate diagnostic must never unlock dispatch.

Tests: source-class masquerade, direct physical-source invocation, test-capability injection, forged approval diagnostics, real constructor patched to throw, zero new journal/markers/network after denial, old mock regression all PASS.

### D2-B — independent production authorization, still no live release

Require separately reviewed pinned PUBLIC Ed25519 roots and demonstrably distinct enrolled user/reviewer identities, exact permit raw bytes, code SHA, actual loaded module/source manifest and role-specific signatures. D3 must be separately authenticated one-shot human execution approval, not just a matching candidate JSON. Fix destination, chain 56, methods eth_chainId/eth_blockNumber/eth_getBlockByNumber, free-only HTTPS, no proxy, no redirects, no WS, maximum three slots, budgets/bytes/timeout/UTC and grant/run identities. A real clock's UTC rollback/expiry must STOP. Do not save or synthesize private signing keys, authorizations or signatures in repo/chat/CI. Keep send_live closed until D3 and a separate actual run authorization.

### D2-C — one supervised physical HTTPS source inside the existing coordinator

No alternate run_real_concurrent thread pool. Adapt the ONE existing RID owner/global pacing lock/three slot scheduler to supervise an exact approved physical source without weakening the fake entry. Atomic production OS-user-fixed grant consumption (O_EXCL, marker file fsync, directory fsync) must precede even an HTTPSConnection constructor. For each RID, durable RESERVE_UNKNOWN BEFORE constructor, then final trusted UTC/candidate validity and shared global spacing immediately BEFORE each POST call. Report Python call boundary, not assumed on-wire timestamp. No retry after connect, POST, read, timeout, signal or parent loss; preserve UNKNOWN uncertainty and irreversibly consumed marker.

Existing bounded RAW HTTP evidence semantics must carry over: valid complete responses may be RPC-parsed only after archive; complete 302, gzip or otherwise rejected RAW is saved with FAILED; incomplete or oversized response never invents full RAW; fsync failure never produces success or performance claim. Hard-stop and parent-loss watchdog remain tied to ONE child, no background daemon, restart or replay.

Strict TLS: fixed bsc-dataseed.bnbchain.org:443; normal CA and hostname verification; no redirects, gzip, proxy, alternate host or WS. Bound request body, total response bytes and headers, and reject content inconsistencies. Do not treat a test-patched HTTPSConnection as proof of physical network throughput.

### D3 — first real, bounded, foreground read-only pilot requires new consent

ONLY after independently reviewed physical source code, trusted D2 two-role signatures, separately authenticated D3 explicit human one-shot approval, inspected fixed OS-user production registry and new exact-SHA Mac verification can a separately user-authorized read-only first live call be considered. An offline D1 APPROVE or this plan is NEVER sufficient. Any mismatch -> STOP with zero network. No trades or background service.

## Required negative and positive offline tests

1. Non-authorized or fake source cannot access production dispatch. All direct/replaced source classes, callbacks/factories, valid-looking unsigned D3 JSON, missing keys, mismatched manifest/code hash and replayed grant stop before transport.
2. Same coordinator is the only scheduler: each RID has durable RESERVE before TLS construction, 3 slots maximum, one globally shared POST pacing lock. Candidate gaps and TTL/dispatch/UTC expiry checked AFTER waiting; stale work denied before POST.
3. Clock checks are real-wall-UTC in future physical code, not D1 virtual test clock. Record actual Python POST boundary; do not claim actual physical packet time or provider capacity from offline injection.
4. Persistence: one-use production registry cannot be renamed away or switched output; RAW fsync before SETTLE; 503, 302, gzip, malformed ID/JSON, overlong/partial payload, wrong chain/height/parent, failed fsync and broken transport cannot be success or COMMIT.
5. Parent SIGKILL and blocked TLS must reap child without restart; UNKNOWN remains UNKNOWN. The marker stays consumed even when write durability is uncertain. Mac symlink aliases and root ownership validated.
6. Each code increment: full Linux CI and independent real ARM64 Mac detached exact SHA, zero skipped/duplicate IDs, verified actual module paths and cryptography==46.0.4. Independently sourced evidence and source-level P0/P1 gate. An accepted D1 test is not D2 production approval.

## Mandatory stop state

D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO.

This is DOCUMENTATION ONLY, no executable runtime changes. No real RPC/WS, production nonce, old private BSC journal, synthesized signing, merge, deployment, background scans or trades. No scheduling of any local task. Stop on any discovered P0/P1 and repair current PR before stacking real sender implementation.
