# F0 D1 — D3 candidate budgets enforced in the single OS child (OFFLINE)

Parent frozen approved PR #196 SHA `b0b7b1dfda7dd537bcfc1b3ed2e1a8405ec37f72`, Mac verdict `APPROVE_OFFLINE_CODE — D1_PRECONSTRUCTOR_RECEIPT_BOUND_REHEARSAL_ONLY`, 515 full / 154 D1 / 3 new / 7 constructor / 7 protected Mac / 10 D2-D3 contract, all PASS without skips. [Archived reviewer report](https://github.com/lxxlx2/ChatGPT_mission_record/pull/196#issuecomment-6394440515). This child needs **separate** independent review.

## Defect in the integrated chain

PR196 validates a D3 one-shot **candidate** before spending an offline marker, but the existing sole child runs the same hard-coded `6 requests, 3 blocks, 1 HEAD refresh, 250-ms global POST interval, 4000-ms HEAD TTL, 5000-ms request timeout and 5000-ms dispatch`, regardless of a *narrower* D3 candidate. This means the bound candidate described limits that were NOT yet actually applied to dispatch. No live source can safely be admitted until its command/cap data is propagated and enforced in the same coordinator.

## Repair

- `rehearse_supervised_mac_entry_offline` now converts its **already validated against the actual Mac preflight** D3 raw candidate to a strict **offline-only** effective scope before spending the one disposable test grant. The source SHA, permit bytes and actual manifest are still immutable; no new permission is created.
- Effective cap is the **minimum** of the preexisting synthetic fixture limits and D3 narrower per-metric budgets: total attempts min(6, D3 max, effective block+HEAD+2), blocks min(3,D3), head refresh min(1,D3), slots exactly 3, pacing equal D3 gap (never faster than validated D2), HEAD TTL min(4000,D3), timeout min(5000,D3) and dispatch min(5000ms, parent hard-stop, D3).
- `run_bounded_offline_once` validates the exact eight-key scope with strict numeric checks, slots=3, limits and coherence **before O_EXCL + fsync**. It passes the validated scope in a fixed encoded child-only CLI argument, where the child **revalidates** prior to invoking the sole unchanged `run_fake_concurrent`; no alternative source or scheduler. Old no-candidate calls preserve the exact original 9-argv/no-explicit-scope behavior including the original 2-second hard-stop scenario.
- Returned `effective_offline_scope` allows comparing actual `reserved`, `block_attempts`, `head_refreshes`, request timeout, global start spacing and dispatch with D3, without claiming network measurement. The candidate and the scope cannot bypass the mocked constructor or unconditionally denied `send_live()`.
- If candidate dispatch is too short to express a valid mock window, or scope exceeds parent whole-operation hard cap, **fail before test grant marker**. Bad flags, booleans-as-int and widened fixture limits also fail before any marker.

## Tests / release

`tests/test_f0_l2_d1_candidate_budget_wiring.py` checks actual **2-attempt** cap rather than just diagnostic, a narrower block budget and slower D3 POST gap in the same child, multiple malformed/widened test scope cases rejected before marker, and hard-stop window mismatch rejected before marker. Full existing F0 suite includes old parent SIGKILL/replay proof and original HTTPS RID-first test.

**Still blocked:** this is OFFLINE mocked HTTPS. No real source is reachable, actual D2 signer trust roots and D3 separately authorized run are not enrolled. Production OS user-fixed grant registry has never been consumed, and no prior private journal should be read. Physical TLS, provider throughput and real on-wire start spacing are unverified. Do not merge/deploy/monitor/trade. No new RPC/WS.

Independent Mac review: pin child PR HEAD detached, inspect changed blobs/source imports and `cryptography==46.0.4`; run F0 full, D1 only and **four new budget tests alone**, existing parent lifetime / bound-wire and preconstructor tests alone; independently replay a stricter D3 scope then read back the actual journal, markers and start-record gap, and test failure/unknown, no real socket.

**Target verdict:** `APPROVE_OFFLINE_CODE — D1_CANDIDATE_BUDGET_ENFORCEMENT_TEST_ONLY` or `REQUEST_CHANGES`, never a real sender release. `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`.
