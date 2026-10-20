# First real short L1 capture — completed, permit consumed

The user authorized one Mac-local, free official BSC HTTP sample capped at 60 future full-block requests plus chainId and head (62 attempts). This result records actual local execution, not a fixture or global first-seen claim.

## Code and independent gates

Original PR #148 SHA: `a2da7b6af7c5db30f99bf17d2bb876065375292b`. Fresh independent Codex processes found three P1s: missing directory fsync for durable entries; discarded HTTP-error response bodies; deadline checked before potentially slow journal persistence. Three fix commits precede this evidence. Executed code SHA: `e2b70967484e6a4226314977cb2cca28033cfbc5`. Full tests: 257 PASS, zero skips. A fresh Codex process independently returned APPROVE_CODE at that exact SHA; a different fresh read-only process returned APPROVE_PERMIT bound to the actual private file SHA256. Both gates passed before execution. Private approval transcripts and exact permit are retained on the Mac; only hashes and verdicts are published.

## Observed sample

- UTC: 2026-10-20T08:44:44.341Z through 2026-10-20T08:45:45.989Z (Asia/Bangkok 15:44:44.341–15:45:45.989 on 2026-10-20).
- Exit code: 0; stop: `CAPTURE_WINDOW_COMPLETED`.
- Attempts: 62 = 1 chainId + 1 blockNumber + 60 getBlockByNumber, no retries.
- Observed initial head: 128716366; requested future heights 128716367–128716426.
- Received: 60/60 planned blocks (100% this bounded sample). Failed requests/invalid block responses: 0; result-null block unavailable: 0; unattempted heights: 0; gaps in requested interval: 0.
- Independently recomputed 5940 full-block transactions; watched PRIMARY sender candidates: 0; ordinary Router destination candidates: 40; frozen-seed offline random preselected candidates: 20.
- Block local elapsed time: median 766.309 ms; mean 786.871 ms; p95 887.668 ms; max 950.686 ms. The recorded interval includes presend journal persistence and HTTP/parsing overhead; it is not pure wire RTT or first-actionable latency. P95 is the sorted value at zero-based floor(0.95*n).

## Reconciliation and limits

All 62 raw response file SHA256 values match their journal rows. An independent raw replay checked JSON-RPC IDs, request methods, exact future heights, transaction block identities, parent links, PRIMARY sender counts and normalized Router destinations. `summary.json` records private report/journal hashes. Report and journal remain separate. No raw response, wallet transaction list, nonce, permit or approval file is committed.

The 60-height interval is the complete denominator of this requested sample, not an independent whole-chain completeness audit. With pacing 1000ms per future height, local acquisition took about 61.648 seconds; this does not establish public first-seen or sustained real-time head tracking. Zero watched-sender candidates means INSUFFICIENT_LIVE_EVENTS for evaluating watched trades; the 40 Router destination matches and 20 preselected candidates are not EOA/BUY/swap-causality-attested or valid independent controls. E1/finality/E2/E3, quotes and paper returns remain unmeasured. Provider billing is UNVERIFIED.

## Authority now

This nonce and one-shot 62-attempt authorization are consumed. NO_RUN for further requests. No retry, 120-second collection, WS, quotes, signing, trading, deployment, notification or merge was performed or authorized by this result. Next work can inspect the saved sample offline; any new live acquisition requires a new explicit authorization and independently reviewed permit.
