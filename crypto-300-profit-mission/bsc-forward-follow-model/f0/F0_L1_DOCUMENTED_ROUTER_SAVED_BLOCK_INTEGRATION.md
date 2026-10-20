# F0 L1 — frozen PR116 signer + documented Router candidate detection from one saved full-block stream

**Status: OFFLINE_IMPLEMENTED / PENDING_INDEPENDENT_REVIEW / NO_RUN.** This branch starts from approved PR #136 fixed SHA `cd30f8b69301b53380473a33ebb428351d4c1bce`, not from unreviewed PR #141. No HTTP/WS client, automation, quote, trade or live permit was added.

## Business objective

Before funding the first short prospective L1 sample, establish **one shared block stream** from which the approved 20-primary signer cohort and ordinary third-party Router-address candidates can be counted using the SAME observed block coverage and clock provenance. This is not a separate wallet analysis project, nor a backtest of old PR #40/#97 profits.

Previously `f0_l1_window.py` only matched `synthetic_routers` and `router_allowlist_kind=SYNTHETIC_ONLY`. It could replay mock Router controls, not real registry-bound addresses. The new saved-envelope **candidate-only** path accepts:
- exactly the byte-for-byte PR #116 cohort manifest (Git blob `fcd0029314353313867e565190cd4f2882089f11`), retaining 20 PRIMARY and 10 BACKUP with no promotion of BACKUP;
- exactly the approved registry `F0_ROUTER_SOURCE_CANDIDATES.json` (Git blob `dc425f85a3f89dd0eb2f73ee6583ad88549a00f2`), independently validated by the existing `official_router_addresses()` reader;
- explicit `router_allowlist_kind=OFFICIAL_DOCUMENTED_ADDRESS_ONLY_NOT_CAUSAL_CONTROL`, forbidding any `synthetic_routers` override;
- the existing **saved, injected** JSON-RPC full-block records and their synthetic UTC/monotonic metadata (not real observed clocks).

Both sides are derived from `block_candidates()` in exactly the same received block; `from` matching a frozen PRIMARY is **WATCHLIST_PRESELECTED** signer candidate, and outside-wallet `to` matching the two documented Routers is **CONTROL_CANDIDATE** (address destination match only). FNV random preselection uses only the PR116 `selection_seed`, never a user-chosen alternative seed. Both candidates emit `control_eligible=false`, `e2_attested=false`, `actual_e3=false`, no quote or profitability labels. **Preselection does not establish causal swap, receipt success, cost, independency, EOA key control or a genuine control denominator.**

PR #140 user/operator-reported real 24-read BSC code check at block `128636823` found 19/20 PRIMARY with no runtime code, 1 with runtime code (`0x7b3d8e939ee08b52d06ab5e6f85791a6007e8d61`), and both Router contracts code-present. This input is historic **single-height user-reported code state**; no raw chain responses were independently replayed here. Do not silently remove/replace the contract-code PRIMARY: preserve the 20-wallet cohort and report it separately pending predeclared sample eligibility policy. The router registry remains intentionally tagged documentary-only even after that reported code-at-height evidence.

## Regression tests and honest execution status

New `tests/test_f0_l1_documented_router.py` has six cases: pinned registry Git blob; real PR116 cohort plus documented Router addresses correctly split through injected saved blocks; raw registry mutation fails; fake cohort cannot masquerade as real Router mode; unchanged synthetic fixture remains valid; and updated `fixture_l1_report.json` matches exact synthetic offline replay after ignoring CLI-added input-file digests. Two positive cases depend on the real PR116 file present in a complete Git checkout.

This authoring environment verified the remote code and test file updates, but **has NOT run the complete Git checkout test suite**. Approved parent #136 previously had 213/213 PASS zero skip. With 6 additional tests the **expected count is 219**, NOT an observed 219/219 PASS. An independent reviewer must run `unittest discover` in a full Git checkout (expect **219/219 PASS, zero SKIP**), verify no regressions or source substitution, and compare the fixture replay. Do not merge before approval.

## Next REAL L1 data capture (requires NEW user authorization)

This is the necessary source-interface step, **not** a live collector. At officially documented 0.45s/block, a **two-minute** BSC window is about **267 nominal blocks**, implying approximately 267 full-block response reads plus separate chain/head reads and any failed/missing/recovery/audit reads. Real network throughput, public first-seen latency, head delay, completeness, 10K/5min shared public endpoint limit, and independent control denomination are **not established**. `eth_getLogs` is documented as disabled on official BSC public HTTP endpoints, so it is not a permitted fallback. Sources: https://docs.bnbchain.org/bnb-smart-chain/introduction/ and https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/ .

Before any L1 live run: independently review the exact bounded network sender, per-request pre-send journal and single-use permit; receive **fresh, separately explicit user authorization** for its endpoint, methods, max total/discovery requests, UTC window, request rate, failure/coverage ceiling, storage/privacy and free-only cost policy. The old four-request smoke AND completed 24-read qualification grants have both been spent. The previously observed 49 transactions were ONE historical block, not a block average. Do not assume 267 reads will succeed or deliver 100% coverage.

If blocks are not covered or actual comparable watch/control events are absent, report `DENOMINATOR_UNRESOLVED`, `INSUFFICIENT_LIVE_EVENTS`, or `BLOCKED_REALTIME_CONTROL` rather than paper profitability. No E1/E2/E3 or +60/+300/+900s quote currently proved.
