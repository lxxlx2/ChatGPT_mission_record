# F0 D2-A — closed physical-source admission, same coordinator, OFFLINE ONLY

**Fixed approved base:** PR #201 PLAN_ONLY SHA `b3e8fb1e6f6811b7599d86cb26c4d81a0c5bde12` (docs-only, GitHub full F0 526/526), stacked on independently Mac-approved PR199 `15ac0ed4dbb839d785546d71b3accd5b232df942`; [attributed independent verdict](https://github.com/lxxlx2/ChatGPT_mission_record/pull/199#issuecomment-6397222150). **The new D2-A runtime code has not been independently approved.** See `F0_D2_REAL_SOURCE_ONE_COORDINATOR_DESIGN.md`.

## Code changes

1. Add `f0_l2_d2a_physical_admission.py`, a frozen slots-only `UnreleasedPhysicalHTTPSProposal`. Its metadata are exact reviewed-source commit SHA, manifest digest, D2 candidate raw digest, D3 candidate raw digest, fixed endpoint, chain 56, exact three read-only RPC methods, and three slots. The proposal is not callable, has no `reply`, factory, transport, network primitive, key, callback, nonce or attached actual grant. Any caller can construct matching bytes: **shape is not signature verification**. `to_diagnostic` always identifies D2/D3 as untrusted, zero network, production NO_GO. `send_live` always refuses.

2. Add `request_physical_source_admission` to the **existing** `f0_l2_d1_coordinator.py`. It is the future physical-source admission seam, **unconditionally DENIED** even for an exact plausible proposal; before creating `ExclusiveEvidence`, reserving an RID, consuming any one-use marker or constructing HTTPS. It does not accept a registry, transport, arbitrary factory, authorization callback, time-injection or writable output location. Later D2/D3 cannot be implemented simply by changing a flag. `run_fake_concurrent` recognizes an exact proposal and calls this closed gate before any time or output action, rather than accidentally accepting it as a fake source. All other nonfake values remain denied by its existing precise allowlist.

3. Harden the **same existing** `GlobalStartGate.run` lower-level path: before using the old duck-typed `source.reply` fallback, exact-class-check all four reviewed memory-only fake source classes; reject subclassed classes and per-instance replacements of `reply` or `reply_over_memory_https`. This closes a previously exposed alternate low-level fake dispatch method without creating another coordinator or touching its RID journal, global pacing lock, 3-slot worker pool or response/RAW/SETTLE handling.

4. New `tests/test_f0_l2_d2a_physical_admission.py` with eight tests: fixed immutable non-executable candidate; altered type/host/methods/slots/digests rejected; exact plausible candidate rejected before evidence, HTTPS constructor and socket; direct single coordinator admission always denied; direct lower-level gate refusal with no starts; FakeSource subclasses and per-instance method injection denied before journal; direct lower-level duck-typed and mutated fake refusal; and all reviewed `send_live`/release methods still deny even with plausible untrusted D3 JSON.

## Why no real HTTPS today

D2 signer trust roots remain empty. D3 candidate is not independently authenticated human consent. No actual OS-user-fixed production once-marker has been consumed. `UnreleasedPhysicalHTTPSProposal` is NOT a sender object and contains no physical HTTPS factory. Real HTTPS `http.client.HTTPSConnection` in the older reviewed D1 primitive remains accessible only under explicit test patch in its current officially exercised codepath; direct use is **not a security boundary** and must never be claimed to be impossible solely because methods are private. This D2-A stage introduces **no additional** real-network invocation. No change to the previously approved synthetic timing tests or virtual UTC.

## Independent review gate

At PR final exact SHA:
- Compare precisely the new proposal module, existing coordinator changes, eight negative tests, this review doc and HANDOFF against the frozen PR201 baseline. Verify original D1 coordinator/HTTPS/registry are unchanged except the two deliberate early source type guards/admission function.
- Run full F0 and isolated eight D2-A tests, existing D1 165, 4 UTC, 10 ctor, 4 budgets, 5 hard-stop, 2 child-lifetime cases. Record real exit codes/skips/test IDs. Linux CI is necessary, not a substitute for independent code review; if an ARM64 Mac is unavailable, mark native Mac outcome **UNVERIFIED** rather than approve a Mac execution.
- Independently forge exact candidate metadata, subclass FakeSource or overwrite instance reply, and call both `run_fake_concurrent` and low-level `GlobalStartGate.run`: reject before evidence/RID/HTTPS and no gate start. Verify existing four exact sealed test sources keep working. Mock socket constructors only, never call RPC/WS.
- Reproduce stop behavior on incompatible callback/trust/digest with no production registry access. No D2/D3 activation and no new process or background task.
- Review target: `APPROVE_OFFLINE_CODE — D2A_CLOSED_REAL_SOURCE_ADMISSION_ONLY` or `REQUEST_CHANGES`; report the exact SHA/environment and evidence. Neither verdict is permission to send real RPC.

**Status:** `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`. Never merge, deploy, trade or consume production nonce under this review.


## 2026-10-25 exact-SHA independent Mac REQUEST_CHANGES and P1 repair

**Superseded fixed reviewed SHA `72b3d2b3967725473f767e76899ad837b8b09b68`: `REQUEST_CHANGES`**, archived with external reviewer attribution at [PR202 comment 6397603374](https://github.com/lxxlx2/ChatGPT_mission_record/pull/202#issuecomment-6397603374). The Mac reviewer independently ran F0 534 unique tests, D1 165, D2-A eight, UTC four, physical ctor ten, budgets four, hard-stop five, child-lifetime two, all PASS/zero skips; discovered a separately reproduced **P1 not covered by original 8 tests**.

The precise missing guard was an instance-level override of `PatchedConstructorOfflineSource.reply_transport_evidence_offline` (the **actual** transport method used in `GlobalStartGate.run`). Both `run_fake_concurrent` and lower-level `GlobalStartGate.run` rejected instances overriding `reply` and `reply_over_memory_https`, but failed to reject the real called name. In the reviewer’s network-free sentinel-only reproduction, the high-level entry invoked the injected method twice and wrote 2 RIDs + attempts.jsonl/RAW; direct lower gate invoked it once and recorded `FRAME`. The overriding method skips the original test constructor safeguards. This is P1 in the offline exact-source admission contract, **not evidence of a real BSC network send**.

**Narrow repair only (same Draft PR202 branch):**
- Source commit `f96d2c4b9230c3e318d3883cae8c5420d0ed3169` adds the **third, actually invoked instance method name** to both checks, before evidence/RID/HTTPS on the high-level path and before callback/start record on the lower-level gate. Does not change scheduler, owner, transport, grant or authorization logic.
- Regression commit `50c205a87e7c8fa6b264dd1a75ec1b2eba27a5f6` adds **two** network-free tests using a patched exact-class `PatchedConstructorOfflineSource` with a local-sentinel callback returning a forged but never-executed RAW-shaped frame. High-level expects `D1_SCOPE_INVALID`, uncalled writer/HTTPS/socket, empty evidence and empty sentinels; direct gate expects `D2A_GATE_NON_FAKE_SOURCE_REFUSED`, zero starts and no callback/constructor. D2-A isolated count increases from **8 to 10**, full F0 from **534 to 536** if no regressions. These counts are expectations until the new SHA’s actual CI logs confirm.

**New approval MUST** pin the revised final 40-character Git commit and compare against approved PLAN_ONLY PR201 `b3e8fb1e6f6811b7599d86cb26c4d81a0c5bde12`. Preserve the old `REQUEST_CHANGES`, validate both synthetic injections independently, re-run full F0/D1/new D2-A and four valid source controls on real Mac ARM64 or state Mac not verified; check other established mock hard-stop/UTC invariants. Github Linux CI success alone cannot retroactively approve old code. **`D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`**.
