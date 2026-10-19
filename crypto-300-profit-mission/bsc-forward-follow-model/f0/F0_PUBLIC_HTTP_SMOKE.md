# BSC F0 — One-time public HTTP smoke prototype (offline-reviewed, NOT RUN)

**Status:** `OFFLINE_SMOKE_PROTOTYPE / PENDING_INDEPENDENT_REVIEW / NO_LIVE_PERMISSION / NO_RUN`.

**Authoritative baselines:** architecture PR #113 `9134fcd41df49ef836b81c8a040974ad89c1fde1`; F0 preparation PR #116 `cf88cd9f6568502f5c052ae3befc9cc16cbab98b`; approved code PR #118 `78e4d26ff7cd1074b7c8de44109b4356e5d0409d`, PR #120 `c0a6dca08a57316f70ca7b7e1358c89e262918f4`, PR #121 `bf9fbb0a6bbff3a9375c6a937cea52d016104733`, source-readiness PR #122 `1656710a6e0f7bc134956bd23e5338f09ab9f34e`. All are separate unmerged Draft PRs. This implementation does not modify previously approved source files.

## Scope and business purpose

The next mainline bottleneck is not historical wallet research: it is whether genuine BSC public data can be obtained within a precisely bounded free request budget. This PR prepares exactly one **read-only public HTTP transport smoke**. There is no F0 24–48h collector, no WS/`eth_subscribe`, no quote request, no independent denominator, no actual wallet monitoring and no trading.

The prototype `f0_bounded_smoke.py` has two intentionally disjoint modes:

1. `--fixture fixtures/bounded_smoke.json`: a **fully offline** replay. It is the only mode exercised or authorized in this PR. The CLI outputs `actual_rpc_calls=0`, E1 unresolved, E2 false, E3/real QUOTED/PAPER zero. Synthetic responses are not factual blockchain evidence.
2. `--execute-live --permit <user-approved-local-json> --report <path>`: a **future gated path which has NOT been exercised**. It fails without a local authorization file that explicitly lists scope, exact approved provider, methods, nonzero absolute caps, narrow UTC window, user Mac environment, free-only policy, no WS/retry, and `/tmp/` storage/retention. Publishing the code is NOT user permission. No authorized permit file is included in Git, and no API keys are accepted.

For future review and explicit authorization, the sole coded provider is the public endpoint `https://bsc-dataseed.bnbchain.org` from BNB Chain's official endpoint list: https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/ . It is not verified accessible, free for this user, performant, or guaranteed to serve fully decoded block transactions. No fallback to paid/third-party endpoints.

## Fixed 4-call ceiling and scope

At most one call each in this order:

| Method | Scope / expected observation |
|---|---|
| `eth_chainId` | Must equal 56 / `0x38` |
| `eth_blockNumber` | Observe a head number, no timestamp claim |
| `eth_getBlockByNumber` | Request exactly that height with `full=true`, one full-block control-discovery cost unit |
| `eth_getTransactionReceipt` | First transaction hash from that block, only when a full transaction object exists; receipt must match tx hash and block identity |

No loops, retries, automatic polling, WebSocket, subscriptions, `eth_getLogs`, `eth_call`, wallet signing, transaction submission, or background execution. Empty blocks use only three RPC calls. Each attempt increments its cap **before** sending, even if an HTTP transport failure happens. Any `eth_getBlockByNumber` call automatically counts toward the one discovery-call cap, regardless of the caller-provided flag. The public URL is exact-match allowlisted. Redirects and inherited network proxies are disabled. The maximum response body size is 2 MB; timeout 4 seconds/request; status must be HTTP 200. Only aggregate counts and SHA256 of response envelopes are kept in the report, never raw payloads. These limits intentionally make this a tiny probe, **not** a coverage assessment.

Even a successful live smoke would prove only this endpoint returned structurally consistent read-only RPC objects at one time. It would NOT prove genuine first-seen latency, ordinary-Router random-control sampling, E1 finality, E2 swap causality, E3, live quotes, public sellability, independent denominator or strategy profitability. A failed smoke may return before four calls. On a runtime failure **after a validated permit**, the CLI catches the transport/HTTP/response/RPC/validation exception, writes a local JSON report with `mode=AUTHORIZED_PUBLIC_HTTP_SMOKE_FAILED_CLOSED`, `attempted_rpc_calls`, `attempted_control_discovery_calls`, `actual_rpc_calls` (attempted sends, **not proven delivered/billed by provider**), a sanitized `error_code` and `stop_state=BLOCKED_SOURCE`, then exits nonzero; no auto-resume. The raw response, URL query, permit body, and exception text are never included. Reporter I/O failure or sudden process termination could still prevent report persistence; independent quota checking remains necessary before any real authorization.

## Test and execution provenance

```zsh
python3 -m unittest discover -s crypto-300-profit-mission/bsc-forward-follow-model/f0/tests -p 'test_*.py'
python3 crypto-300-profit-mission/bsc-forward-follow-model/f0/f0_bounded_smoke.py --fixture crypto-300-profit-mission/bsc-forward-follow-model/f0/fixtures/bounded_smoke.json
```

This branch initially added 19 direct tests (chain and receipt identity, response shape, calls, error paths, source URL, immutable method allowlist, disabled redirects, time window, and permit-fail-closed). The original 19 tests remain, and the current review fix adds **8 targeted tests**: third-request timeout, network failure, overlarge response and RPC error (all persist 3 attempts + 1 discovery attempt), early wrong-chain failure (1 attempt), successful mocked live CLI, full-block discovery cap bypass, and error-message privacy. The currently checked local combined suite is **119/119 PASS** (prior 92 + new 27). Real network I/O was mocked and explicitly forbidden for the tests; fixture CLI output remains byte-identical. The independent reviewer must rerun the full suite at the new fixed SHA.

## Required future permission, not given

A real smoke requires a **new user decision after independent code review**, including the exact official endpoint, method list (four reads), `MAX_TOTAL_RPC_CALLS=4`, `MAX_CONTROL_DISCOVERY_CALLS=1`, `max_response_bytes<=2_000_000`, `no_retries=true`, `no_ws=true`, permitted user Mac environment, duration <=10 minutes in UTC, retention <=24h and `/tmp/` report storage. No wallet address/private key and no payment authorization are necessary.

The permit parser requires `user_authorized=true` in a local approval file; that flag is a **procedural gate**, not cryptographic proof of user consent. **Unresolved P2 before any future live authorization:** bind an approved permit to the reviewed code SHA and single-use nonce, and record the permit digest, with a separate fixed-SHA review before running. The operator must have independently obtained user's explicit written approval in this conversation and must never create an approval file by assumption or check one into Git. At present **NO_RUN**.

## PR #124 independent review corrections

- Review at `d481cdd9d010c207fa537b5fafe4f80969e3e63a` was `REQUEST_CHANGES` solely for failed-request accounting. This branch now persists an audit report on any injected runtime failure after valid permit with the attempted request/discovery counters intact and `BLOCKED_SOURCE` stop state.
- Adjacent P2-2: automatic discovery accounting for all full-block RPC reads; cannot bypass by passing `discovery=False`.
- Evidence P2-3: no absent local `test_run.log` hash is claimed as a committed artifact; reproducible repository-root test command is authoritative.
- Authorization P2-1 is not closed by this repair; no real live smoke may be considered approved.

## Next development / acceptance

- Independent reviewer evaluates the gate and negative tests before allowing any real smoke.
- Only after separate explicit authorization may the exact limited public HTTP test be executed on the user's permitted Mac environment. If it cannot access a full block under limits: report `BLOCKED_SOURCE` with request count. Do not swap providers or bypass with archive evidence.
- A passed smoke is **not** a 24–48h F0 trial authorization. F0 feasibility still requires sustained source budget, WS/control discovery, independently auditable denominator, true first-seen clocks, finality/E2 causal rules, and real three-delay quote timing.
