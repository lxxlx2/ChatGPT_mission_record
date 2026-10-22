# BSC F0 — three-slot offline discrete-event coordinator

**Stage:** `THREE_SLOT_OFFLINE_IMPLEMENTATION / NO_REAL_SENDER / PENDING_INDEPENDENT_SHA_REVIEW`.

## Proven input and decision

[Independent PR159 saved30 review](https://github.com/lxxlx2/ChatGPT_mission_record/pull/159#issuecomment-6335034540) approved offline exact `111059087257e792a76516fdd684a127cda52772`, 312/312 PASS and verified actual private Mac Journal SHA256 `e069b7cd38c2ad3c8a3af3a1b1c220efab1714fe4de0bb7a9e2b814a2302d61a`. Measured single-HTTP trial 22 blocks/21.046s, 1.045 blocks/s versus 2.178 blocks/s source HEAD increase. Three hypothetical inflight lanes yielded 2.753–2.976 blocks/s under optimistic reused sequential timings, not real parallel provider evidence. Two lanes have inadequate margin.

## Implementation

`f0_l1_three_slot_offline.py` is an **offline-only deterministic event simulator**. It consumes only the prior SHA-checked private Journal timing distributions via `replay_timings` and never opens a socket or accepts an injected post callback. Its CLI does not accept a permit or `--execute-live`. It creates a new 0600 append-only local JSONL fixture ledger, with globally serialized fsync of every `RESERVE_UNKNOWN` **before** scheduling its fake completion event. A crash fixture leaves durable UNKNOWN; non-crash stop drains remaining virtual in-flight responses.

Exactly one coordinator enforces <=3 total in-flight slots **including HEAD**, >=250ms **global request start** separation, initial chainId then initial HEAD completion before any block dispatch, and source-confirmed HEAD height bounds. Default limits: <=32 attempted total calls including identity, <=24 blocks, <=6 refreshed HEAD, <=60 seconds of *virtual dispatch*, no retries. HEAD checkpoint every four dispatched blocks or as needed for source freshness or height eligibility; stale/regressed source HEAD stops. The simulated clock is not connected to wall clock or provider network.

Out-of-order responses enter a bounded-by-budget reorder buffer; received block responses count separately from **contiguously committed, internally parent-linked** blocks. Missing/failed/timeout/ID-mismatched responses consume budget and leave explicit gaps. Duplicate fake responses are ignored. A bad parent prevents committing the mismatched height and anything beyond it. The first committed height has no independently observed parent anchor. End-of-run reports separately count attempted failures and known unattempted heights under the last synthetic HEAD.

**Only synthetic SHA256 hashes appear in the ledger.** No wallet/transaction identifiers, no real source response bodies, no permit or nonce. Output marks `actual_network_requests: 0`, `real_provider_capacity_claim: UNVERIFIED`, `F0_NOT_PASSED` by contract.

## Mac replay (OFFLINE ONLY)

Use a checkout pinned to this PR's exact new SHA. The actual local source path has a required `archive/` subdirectory. The command below reads private bytes locally, verifies known SHA and emits *six simulated variants* under a new private output directory. It does NOT send any RPC/WS. Use zsh from repository root:

```zsh
umask 077
mkdir -m 700 "$HOME/Library/Application Support/MissionEvidence/20261022-f0-three-slot-offline"
python3 crypto-300-profit-mission/bsc-forward-follow-model/f0/f0_l1_three_slot_offline.py --journal "$HOME/Library/Application Support/MissionEvidence/20261021-adaptive-sampled-head/archive/journal.json" --expected-sha256 e069b7cd38c2ad3c8a3af3a1b1c220efab1714fe4de0bb7a9e2b814a2302d61a --output-dir "$HOME/Library/Application Support/MissionEvidence/20261022-f0-three-slot-offline"
```

The exact saved Journal SHA256 above matches the independently reviewed PR159 value. The simulator refuses mismatches and does not alter source bytes.

### Safety and acceptance gates

- Independent reviewer checks exact SHA; reproduce full suite and targeted tests; validate no actual transport import/callback; verify durable serialized reserve-before-virtual-send and no overwriting old ledger.
- Exercise 3-slot total cap, global 250ms spacing, initial identity and HEAD preflight, source height eligibility, HEAD freshness, budget competition, virtual timeout, slowdown, outage, duplicate, wrong ID, bad parent, parent links only after contiguous release, and simulated abrupt crash UNKNOWN durability.
- Run read-only saved Journal replay on the actual Mac only; raw evidence stays private. Report realistic scenario outputs as `SIMULATION`, including virtual response throughput vs contiguous commit throughput, backlog and buffer, and no future provider capacity claim.
- Any P0/P1 => `REQUEST_CHANGES`; missing real Mac data => `BLOCKED_INSUFFICIENT_EVIDENCE`, never substitute generated historical evidence for actual private saved bytes.
- **No new RPC/WS, no runtime sender, no permit, no trade/sign/quote, no paid services, no merge or deployment.** The previously authorized 30-call permit is consumed. `F0_NOT_PASSED / PRODUCTION_NO_GO`.

## Next practical decision after independent offline approval

If the synthetic coordinator remains bounded and correctly reports missing/ordered coverage, propose a **separate future review of concrete real concurrency transport + globally fsynced reservation/permit**. Then ask user for fresh narrow source-rate and total-attempt authorization before any real three-slot test. The ideal scenario margins alone are not a production launch gate.
