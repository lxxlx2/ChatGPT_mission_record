# F0 D1 integrated offline exit gate — single audit, explicit authority block

Parent independent Mac approval: PR #182 **`980121f75626df53508155b09d0776841b2c4f67`**, `APPROVE_OFFLINE_CODE — D1_CONCRETE_HTTPS_CODE_SCOPE_ONLY`; **459/459 full, 98/98 D1, 10/10 new**, no new P0/P1. The approved code is frozen. This child is **one integration checkpoint**, not a new real-network permission.

## Mainline business question

F0 exists to learn whether the FREE BSC source can support continuous, audited wallet-signed BUY/SELL capture, a simultaneous ordinary Router wallet control group, real-time +60/+300/+900-second quotes and an independently checkable denominator for missed events. Those full F0 objectives still require their original separate 24–48h authorized trial. Current evidence cannot assert the source keeps up: a historical real serial sample measured **1.045 committed blocks/s vs sampled source growth 2.178 blocks/s**, and an offline 3-slot simulation under that synthetic growth produced roughly **1.740 blocks/s**. The real provider's sustained three-socket capacity is **unmeasured**.

## Code implemented here

`f0_l2_d1_integrated_exit.py` exposes:

- `run_offline_integrated_fake_with_pins(...)`: Only the exact class `SealedMemoryHTTPSSource` is accepted, without any network-capable sender callback, factory, CLI, real registry or trusted realtime input. An **externally provided TEST reference** pins exact commit SHA, permit bytes, inventory bytes and separate user/reviewer public-key fingerprints and is rechecked against actual installed Git, cryptography and Python bytes **before the TEST registry is touched**. The pre-existing strict bundle repeats test signer, UTC scope, checkout and budget checks; `OfflineGrantRegistry` creates a single 0600 O_EXCL/fsynced consumed marker in a disposable private root; `run_fake_concurrent` then executes three shared *memory-only* HTTP slots and persists original request IDs, `RESERVE_UNKNOWN`, RAW and SETTLE; `reconcile_saved_attempts` independently audits the generated fake ledger. Failed post-time UTC or invalid source cannot silently become a successful block. Changing output paths does not refund an already consumed test grant.
- `production_d1_exit_verdict()`: returns **`D1_BLOCKED_AUTHORITY`** and a fixed list of material G/J/M blockers. It has **no caller-supplied `trusted`, `approved` or `allow_live` argument**, and signed fixture/temporary pins never set its release status. Production roots are currently empty, complete runtime provenance remains false.
- `send_live()`: unconditionally raises `D1_BLOCKED_AUTHORITY_NO_NETWORK_OR_PERMIT` *before any real HTTPS constructor or grant access*, even when a caller passes `execute_live=True` or test keys.

This PR **does not connect** the concrete `http.client.HTTPSConnection` from PR182 to the coordinator; doing that safely requires *both* an independently authenticated production bootstrap and a separately reviewed one-use permit and physical-start accounting. Connecting arbitrary caller-injected factories under an ephemeral test signature would be an authorization bypass, not progress.

## One D1 exit matrix; no scattered mock milestones

| Original gate | Already independently Mac reviewed | Still required to exit D1 |
|---|---|---|
| G-01 | All public live entrypoints deny; integrated live entry denies even when supplied test data | Independently reviewed protected production startup |
| G-02 | Local full F0 Git tracked inventory, wheel RECORD and Python executable digest, TEST reviewer pins | **Trusted source-independent full runtime+stdlib+native dependency closure** and independently published approved reference. No self-signed production pins |
| G-03 / G-04 | Offline Ed25519 two-role test signatures and POST-time fake UTC bound to signed permit | Real user/reviewer identity enrollment, authenticated signers, trusted UTC; new exact D2 scope approval |
| G-05 / G-06 | Shared test O_EXCL/fsync marker, no grant reuse across output roots and SIGKILL fake regressions | Real fixed registry bound to same immutable protected startup and sender; no user-input root |
| J-01–J-05, J-07–J-09 | Full sealed-memory three-slot coordinated scheduling, per-method budgets, >=250ms fake POST-call gap, HEAD TTL, RAW-before-SETTLE, first-commit and bad-parent accounting | Actual concrete sender must be connected **under the identical single coordinator and durable pre-network journal**, proving start gap at the physical socket boundary |
| J-06 | PR182 actual HTTPS code inspected with every constructor replaced by memory substitute | Real TLS peer and full request absolute timeout; exact fixed transport behind authenticated permit; no real network authorized |
| J-10 | Three OS SIGKILL fake process boundaries with accurate UNKNOWN state | Actual socket crash/partial POST uncertain and real disk-loss proof |
| M-01–M-03 | Limited historical serial source samples + offline simulations only | A separately approved one-shot D3: same-window actual HEAD growth, completed block throughput, gaps, response count and cost. No sustainable tracking claim based on 32 attempts |

**Ready for D2? NO.** `D1_BLOCKED_AUTHORITY`. Trust root, external source provenance and production sender are **not implemented**; cannot be made true with a caller-editable JSON field. If trustworthy enrollment cannot be established, STOP at this status. Avoid reopening already-closed small fake boundary cases and do not pretend D1 completion.

## Acceptance and next decision

Independent Mac reviewer must check one fixed SHA and diff to approved PR182, verify new module/tests/docs and complete regression. Demonstrate valid test-signed and pinned memory-only session has correctly spent test grant and `OFFLINE_ACCOUNTED_NOT_LIVE`, while wrong pins/altered permit/source fail **before any registry/evidence**; expired fake POST keeps marker spent, no source fake POST; repeated same grant fails after moving output root; production `send_live()` always denies. Mac tests use isolated `cryptography==46.0.4`; **all HTTPS connection constructors are forbidden**.

Outcome may be `APPROVE_OFFLINE_CODE — D1_INTEGRATED_FAKE_EXIT_BLOCKED_SCOPE_ONLY` or `REQUEST_CHANGES`; neither is D1 full completion, D2 permit approval, D3 physical network authority, merger or deployment. A separate future D1 implementation would require an independently reviewed authentic human signer/public key enrollment source and trusted complete runtime bootstrap; if none can be established, record `D1_BLOCKED_AUTHORITY` and terminate this track's release preparation.

**No real RPC/WS**, no production/user grants/keys/nonce, no new paid source, trade, merge, deployment, background jobs or new Mac resident load. Old 30-call approval was spent. `F0_NOT_PASSED / PRODUCTION_NO_GO`.
