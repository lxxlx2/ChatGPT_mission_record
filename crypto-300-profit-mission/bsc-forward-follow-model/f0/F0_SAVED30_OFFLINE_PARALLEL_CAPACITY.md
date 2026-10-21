# F0: 2026-10-21 sampled-HEAD result and offline parallel capacity gate

**Source:** [Actual user/operator Mac one-use report on PR #158](https://github.com/lxxlx2/ChatGPT_mission_record/pull/158#issuecomment-6318282277), at fixed independently approved source SHA `3a826d3eec1433d536c6fed1789997e225f6a8a0`. Live evidence private Mac only; report/journal digests are public proof-of-claim metadata but do not substitute independently re-reading local bytes. No new RPC authority.

**Observed:** 30 requests = chain 1, HEAD 1+6, full block 22; 22/22 successful, 0 attempted missing and 0 errors. 21.046 sec elapsed; `HEAD_POLL_BUDGET_EXHAUSTED` exit 0. Initial sampled source HEAD 128952119; final *sampled* head 128952156, received contiguous 128952120–141. After the final refresh 15 known heights 142–156 unattempted (not failed). Refresh backlog 2/4/8/12/15/19 blocks. Sample source HEAD increased 37/16.991s = 2.178 blocks/sec; overall delivery 22/21.046s = 1.045 blocks/sec. Mean local per-full-block request ~771.538ms, median ~750.038ms; source HEAD request median ~426.062ms. These measurements are NOT pure network RTT, globally independent chain head or an ETH/E2/E3 trading signal.

**Conclusion:** existing sequential official public HTTP source does not keep pace in this finite sample. The observed per-block mean alone implies a theoretical serial block-only ceiling of ~1.296 blocks/s, before HEAD requests and other overhead; this is below sample source HEAD growth 2.178. Increasing HEAD budget or run duration alone cannot resolve that throughput deficit. This does NOT prove every free provider, full concurrent source or WebSocket is infeasible.

## What this PR actually implements

- `f0_l1_offline_capacity.py` ONLY reads exact locally saved `journal.json` bytes, verifies caller-supplied SHA256 and the Journal request index/method/state/duration ledger, and extracts **aggregate latencies only**. It makes **ZERO** HTTP/WS calls, cannot execute a permit, cannot sign/trade, and does not need wallet addresses or raw RPC response bodies.
- For each 1/2/3 hypothetical inflight slot count and HEAD checkpoint after every 4 or 8 full blocks, it replays the captured *sequential* request durations as a deterministic work-conserving worker-slot capacity projection. It enforces one global 250ms minimum simulated request **start** spacing and 32-attempt total budget with 24 full blocks and HEAD checks counted. It reports projected rate and margin versus the actual observed 2.178 bps sampled source growth.
- All scenarios are `HYPOTHETICAL_ONLY_NO_PROVIDER_CONCURRENCY_VERIFIED`: provider may rate-limit or slow under parallel connections; shared journal fsync and ordering contention are **not** included; a real collector must gate heights on the latest separately verified HEAD and retire out-of-order arrivals by exact height and parent hash before treating them as contiguous. The output deliberately does **not** claim completeness, future rate, E1/E2/E3 or F0 PASS.

## Real Mac-only saved-evidence replay invocation (NO NETWORK)

Run from the existing local Git checkout of **this PR's offline-only code SHA**, not from the old real source entrypoint. The input remains private and read-only. The user/operator reported `journal.json` SHA256 exactly:

`e069b7cd38c2ad3c8a3af3a1b1c220efab1714fe4de0bb7a9e2b814a2302d61a`

```zsh
python3 crypto-300-profit-mission/bsc-forward-follow-model/f0/f0_l1_offline_capacity.py --journal "$HOME/Library/Application Support/MissionEvidence/20261021-adaptive-sampled-head/journal.json" --expected-sha256 e069b7cd38c2ad3c8a3af3a1b1c220efab1714fe4de0bb7a9e2b814a2302d61a
```

If the path differs, use the actual private evidence path; do not invent or reconstruct the private bytes. Do not post wallet/tx hashes, JSON response bodies, permit, nonce or the 30 raw response files. Sanitized aggregate projections only may be recorded in the follow-up PR, explicitly marked as simulations. If journal hash or row accounting mismatch, fail closed and report it; do not overwrite the saved evidence.

**Next practical decision:** independent offline code review, actual Mac journal SHA verification and six scenario projections. If ideal 2 inflight barely exceeds sample growth, prefer a 3-slot bounded offline planner (with rate limiting, durable pre-send reservation, request-specific response identities, heights sealed only when contiguous, and bounded HEAD freshness) *before* proposing another limited live permit. Do not add live concurrency before independent review. A provider's true parallel capacity, sustained control discovery, timed quotes, independent denominator, F0 PASS and production readiness remain **UNVERIFIED**. All previous 4/24/62/30-call real permits are **CONSUMED**.
