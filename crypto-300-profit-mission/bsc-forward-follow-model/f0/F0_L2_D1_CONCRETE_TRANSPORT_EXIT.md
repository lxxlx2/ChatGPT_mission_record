# F0 D1 — concrete HTTPS sender source, code-only audit and D1 exit gates

**Frozen approved parent:** PR181 `35e1cba6cc4b4e841ff6f096bf6ed0af22b2ac8d`, independently reviewed on Mac as `APPROVE_OFFLINE_CODE — D1_TLS_PHASE_MOCK_SCOPE_ONLY`; 449/449 full and **88/88 D1 focused** PASS, 7/7 new. Parent SHA unchanged.

## Business goal and stop decision

The authoritative `ARCHITECTURE.md` (PR113 SHA `9134fcd41df49ef836b81c8a040974ad89c1fde1`) requires F0 to validate affordable forward identification of wallet-signed BSC BUY/SELL, a **real-time ordinary Router control group**, scheduled +60/+300/+900s quote availability, and an independently reconstructable missed-event denominator, before F1/F2 and eventual blind paper-alpha evaluation. Full 24–48h actual F0 has NOT been authorized or run. The old serial sampled-source observation showed only **1.045 committed full blocks/s versus observed sampled HEAD growth of 2.178 blocks/s**; three-slot fake with historical serial timings was about **1.740 committed blocks/s** on the 2.178-bps synthetic scenario. Neither proves actual provider concurrency nor sustainable capture. No further standalone mock-only micro-stage should substitute for a bounded actual source feasibility verdict.

## Concrete engineering increment in this PR

`f0_l2_d1_concrete_https.py` adds a **specific fixed-host** `http.client.HTTPSConnection` code path for the future D1 code audit, rather than a caller-provided arbitrary factory:

- `HOST=bsc-dataseed.bnbchain.org`, port 443, `ssl.create_default_context(SERVER_AUTH)`, `CERT_REQUIRED` and hostname checking. Standard library directly selects host rather than honoring proxy environment or following redirects. Request method `POST /` only, `eth_chainId`, `eth_blockNumber`, `eth_getBlockByNumber` through approved `json_body` strict payload parser, request body max 2000 bytes.
- Single connection attempt; final post guard **AFTER TLS connection**; single POST attempt; one response read capped at `max_bytes + 1` up to 2,000,000 bytes; raw status+headers+body available for downstream journal. Preserve raw HTTP503 without misclassifying it as parsed success. Reject redirects, compressed frames, duplicate headers and oversize evidence; close in `finally`, no redirects, retries or paid fallback.
- Explicit `connect_attempted_at` and `post_attempted_at` timestamps. The latter is a **Python call-to-request timestamp, not the physical socket first-byte timestamp**; an attempted connection may already send TLS packets even if final gate refuses the POST. POST write/read failure is uncertain, never `NOT_SENT`, never retried.
- The **public** `send_live` unconditionally raises `D1_CONCRETE_HTTPS_LIVE_DISABLED_REQUIRES_D2`. The private review primitive also requires an internal **test-only token** before constructing HTTPS. This token is **not authentication** (privileged Python code can import/reuse it); real credentials, trusted review root, UTC, fixed registry and final coordinator integration are absent. It is a guard against accidental imports and an explicit sign that this is not a usable D2 sender. **NEVER call it against actual network before D2/D3 authorization.**

**No test or code invoked the genuine constructor with a real network**: `tests/test_f0_l2_d1_concrete_https.py` patches `http.client.HTTPSConnection` across EVERY private primitive call, verifies fixed endpoint/TLS settings, correct body, guard after connect/no POST on denial, connect timeout, POST write/read timeout, 503 raw retention, redirect/gzip/duplicate response header/oversize refusal, context certificate verification, denied public entry and absent test token. Zero RPC/WS, no actual private Mac BSC journal.

## Whole D1 gate, status versus original matrix

| Gate | Verified/offline functionality | **Still blocking real D1 completion** |
|---|---|---|
| G-01 | Public `send_live` intentionally disabled | Production trusted entry absent |
| G-02 | Checked Git F0 files, local wheel/RECORD and Python byte hashes; offline caller-supplied pins | **No independently published and authenticated full interpreter/stdlib/dynamic wheel closure**; local missing RECORD hashes. Cannot self-attest production provenance |
| G-03/G-04 | Offline two-role Ed25519 with `cryptography==46.0.4`; correct role binding, signed fake permit, fake UTC at POST | **No enrolled real user/reviewer identities, trusted clock or separate D2 exact permit approval** |
| G-05/G-06 | `OfflineGrantRegistry` O_EXCL/fsync and isolated fake-run uniqueness | **Production fixed registry integration to actual real send entry + independent release binding absent** |
| J-01..J-05, J-07..J-09 | Sealed memory 3-slot coordinator, 250ms fake start, HEAD TTL and ordered durable blocks with original request IDs | Same constraints not yet applied to actual concrete HTTPS sender |
| J-06 | This PR has **specific HTTPS code** and patched-socket offline response tests | **Actual socket/TLS peer, physical POST emission gap, absolute timeout and sender-to-durable-ledger contract not verified** |
| J-10 | 3 real Mac OS SIGKILL tests of fake process and UNKNOWN/drain, no grant reuse | Actual POST-write unknown and process interruption, physical power failure not tested |
| M-01..M-03 | Historical finite serial samples + hypothetical concurrent scheduling, provenance separated | No real 3-slot concurrency same-window head growth/commit measurements, no sustained catch-up claim |

### Decision gates / next mainline work — consolidate, do not proliferate mock PRs

**D1 exit:** one future bounded integration must connect a *real* trusted program bootstrap (reviewed exact full runtime bytes + independently verified signer identity), fixed production one-use grant registration, single coordinator and concrete HTTPS sender, with durable pre-network `RESERVE_UNKNOWN` and raw-before-`SETTLE`. It must be independently Mac-reviewed at one fixed SHA and remain **default DENY**. If true bootstrap / identity cannot be established, explicitly record `D1_BLOCKED_AUTHORITY` and stop rather than invent more ephemeral pins.

**D2:** user gives a NEW explicitly scoped permit (allowed free provider/account, methods, total attempt/HEAD/BLOCK limits, UTC and quota, evidence root); independent reviewer authenticates signer and exact SHA/permit bytes. Neither D1 code APPROVE nor self-signed offline fixture is user permission.

**D3:** only after separate explicit request to run ONE bounded real three-slot sample on Mac, evaluate its actual network and same-window source-head vs continuous-commit rates. If still slower, report `BLOCKED_SOURCE`/F0_NOT_PASSED and re-evaluate truly free alternate WS/HTTP data paths; do not keep extending the runtime automatically. D4 further decision only after legitimate evidence. The complete F0 24–48-hour source, random real-time controls, matched quotes, independent denominator are subsequent distinct explicit trials—not implied by a 32-attempt smoke test.

No merge, production deployment, subscriptions, trading, wallet signing, news/email monitoring or paid API. Earlier 30-call real grant consumed. This PR only enables **source-code review of a concrete sender**, NOT an executable sender.

**State:** `D1_PARTIAL / F0_NOT_PASSED / PRODUCTION_NO_GO`.
