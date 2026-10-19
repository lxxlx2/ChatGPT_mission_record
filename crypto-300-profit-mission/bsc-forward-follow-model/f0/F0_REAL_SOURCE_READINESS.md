# BSC F0 — Real Free-Source Feasibility: Authorization-Free Readiness (R0)

**Date:** 2026-10-20 (Asia/Bangkok)  
**Status:** `PREFLIGHT_DESIGN_AND_OFFLINE_BUDGET_ONLY / NO_RUN / PENDING_INDEPENDENT_REVIEW`.  
**Fixed authority:** architecture PR #113 `9134fcd41df49ef836b81c8a040974ad89c1fde1`; F0 plan PR #116 `cf88cd9f6568502f5c052ae3befc9cc16cbab98b`; approved offline state/adapter/bridge PR #118 `78e4d26ff7cd1074b7c8de44109b4356e5d0409d`, PR #120 `c0a6dca08a57316f70ca7b7e1358c89e262918f4`, PR #121 `bf9fbb0a6bbff3a9375c6a937cea52d016104733`. No authorized live run and no baseline source is changed in this preparation PR.

## Why this is the next decision, not another historical wallet audit

The existing saved-RPC bridge can replay events, but **we do not yet know whether any free provider can deliver the watchlist + randomized ordinary-Router control + timed 60/300/900-second quote requests with independent completeness auditing**.

BNB Chain's post-Fermi official introduction states BSC mainnet block interval **0.45s** (2026 upgrade). A full block enumeration at one request per block requires **192,000 block fetches in 24h** and **384,000 in 48h**, excluding receipt/quote/audit requests, retries and gaps. This is a major difference from an old three-second assumption. `newHeads` alone is just a header notice; it is not the complete transaction stream and does not independently enumerate wallet signers or ordinary-Router buys.

Official source: https://docs.bnbchain.org/bnb-smart-chain/introduction/  
Fermi release: https://docs.bnbchain.org/announce/fermi-bsc/

## F0 candidate sourcing and honest current status

| Path | Confirmed by current public documentation | Still UNVERIFIED / no live requests performed |
|---|---|---|
| BNB Chain public HTTP RPC | Official page lists public RPC endpoints with an advertised 10K requests / 5 minutes and explicitly says **`eth_getLogs` disabled on listed mainnet endpoints** | Exact method responsiveness, actual quotas, full-block transaction delivery, initial lag, independent provider quality, and sustained control discovery. Never treat a stated shared rate limit as a personal free allowance |
| Alchemy BSC WebSocket + HTTP | Official BNB Smart Chain `eth_subscribe` page documents `wss://` requirement; `newHeads` exists. Alchemy pricing/throughput docs list 30M CU/month and **300 CU/s account-wide** as the conservative planning reference; another Alchemy support article states 500 CUP/s/app (conflicting documentation). Actual account limit remains **UNVERIFIED** | The user's actual account/app, available monthly remainder, whether every needed BSC method works on user's endpoint, WS event size and cost, retry/reconnect, latency, or rate limit on a real day |
| Independent check path | In principle compare a separately enumerated block/receipt set to first-observed capture | Unverified different-method/provider access, per-wallet signed BUY denominator, coverage of indirect aggregators; two APIs at one upstream are not proof of independent provider |

Official BNB HTTP docs: https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/  
Alchemy BSC WS: https://www.alchemy.com/docs/chains/bnb-smart-chain/bnb-smart-chain-api-endpoints/eth-subscribe  
Alchemy published pricing (300 CU/s): https://www.alchemy.com/docs/reference/pricing-plans ; current account-wide throughput: https://www.alchemy.com/docs/reference/throughput ; conflicting support FAQ (500 CUP/s/app): https://support.alchemy.com/articles/5827006872-what-is-included-in-the-free-tier  
Alchemy method CU schedule: https://www.alchemy.com/docs/reference/compute-unit-costs

Current published Alchemy cost model, **illustrative only**, is `eth_getBlockByNumber=20 CU`, `eth_getTransactionReceipt=20 CU`, `eth_call=26 CU`, `eth_getCode=20 CU`; generic subscription traffic uses `0.04 CU/byte`. The official plan is account-wide. This is **not** a claim that 30M CU can be freely devoted to this module, or that WS messages are 1000 bytes.

Example with **zero additional calls and zero WS transfer**: 24h full block 192,000 requests / 3.84M CU; 48h 384,000 / 7.68M CU. For illustration **only**, 1000 bytes/head delivered for 24h at 0.04CU/byte adds 7.68M CU, bringing total to 11.52M CU before any receipts, retries, quotations, controls beyond block scans or other account activity. For 48h the same hypothetical scenario is 23.04M CU before extras. Actual per-event payloads must be measured and fixed in evidence, not assumed.

## Preferred least-cost investigation sequence (not a permission to execute)

1. **Paper provider qualification:** choose one truly free BSC-capable service; identify account owner approval, plan and remaining quota, exact methods available, whether request ceilings and rate limits can be enforced; ensure no credit card/paid switch/automatic charging.
2. **Small, separately authorized bounded smoke check before 24–48h trial:** prove chain ID `0x38`, known block identity and full transactions, one signed watched-wallet transaction without looking at outcomes, an ordinary allowlisted Router candidate, error/retry semantics, source UTC ingress and monotonic local clock. Every call belongs to an audited counter. No inference from archive timing to genuine first-seen.
3. **Source capability gate:** if WS `newHeads` is supported, measure actual incoming payload size/latency, run bounded concurrent `eth_getBlockByNumber(full=true)` for headers, ensure no missing heights under subsecond block times; verify recovery with a **separate BACKFILL label** that never masquerades as timely E3. Without WS, evaluate fully bounded HTTP polling and document whether the latency/coverage makes the main/control design impossible.
4. **Real controls are essential:** new full-block signed transactions calling allowlisted Routers, sampled by pre-registered seed independent of eventual receipt/ROI, with explicit `rpc_random_control_discovery` cost and lost/unknown coverage. No replayed controls in the main strategy estimator.
5. **Receipt and finality:** check block hash, confirmed receipt status, signer and observed confirmation/finalized-tag semantics. On currently approved bridge, `min_confirmations` is *passed but NOT enforced* on positive receipt events. Do not advertise an E1 PASS. F1 must implement and test a justified frozen finality policy, including receipt-before-confirmation provisional quote and E1-failed/reorg quote rejection in both groups.
6. **E2 causal Router rule:** a `BUY_CANDIDATE` based on ERC20 transfer hints is **not a verified swap**, especially for third-party payers, aggregators, transfer bundles and airdrop-like flows. Before any actual E2/E3 signal, freeze causal linkage and Router permit list in F1. Unknown and nonallowed flows remain unresolved, are counted in L1 denominator, and do not become paper trades.
7. **Time-matched quotation:** actual outbound request and inbound response UTC/monotonic clock for 60/300/900s after first actionable BUY/SELL+CA identification, with exact pool block/path amount, failures/staleness/fees and symmetric policies for main/control. **Saved `eth_call` must remain `SIMULATED_ARCHIVE_QUOTE`**.
8. **Independent denominator:** on bounded fixed blocks, reconstruct signed Router candidate transactions and receipts via a separate retrieval method, preferably different provider, then report both error directions. Missing independent provenance = `DENOMINATOR_UNRESOLVED`, not fabricated 95% completeness.
9. **Budget stop:** keep nonzero explicit total requests, control discovery requests, WS traffic bytes/CU (if metered), per-method quota, retry cap, storage volume/retention, rate and trial window. **Stop on any ceiling or provider cost uncertainty; do not roll to a paid tier**.

## P2 notes from PR #121 independent review (not a new P1)

- **P2-1 finality configuration:** current offline bridge's `min_confirmations` does not gate positive receipt-side BUY/SELL hint. This is acceptable in **PROVISIONAL-only** interface testing; F1 must either remove the parameter or implement a genuinely enforced finality policy with tests. Required F1 result: explicit `UNRESOLVED_F1_POLICY` until independently verified, never E1/E2/E3 PASS by configuration alone.
- **P2-2 payer attribution:** simple transfer association can overcount hints or miss third-party payer swaps. Emit `UNVERIFIED_SWAP_ROUTE` and report false-hint rate when real evidence is authorized. No promotion to trade or matched control solely on these hints.
- **P2-3 test invocation:** run from repository root:
  `python3 -m unittest discover -s crypto-300-profit-mission/bsc-forward-follow-model/f0/tests -p "test_*.py"`.
  Avoid `discover -s tests -t .` from within `f0/`, which the reviewer found produces an import error. This preparation branch supersedes the outdated command in the **handoff**, not the approved old PR #121 file.

## Offline capacity planning tool (safe now)

`f0/f0_source_budget.py` is pure standard-library arithmetic, **no socket, no provider credentials, no subscription, no runner**. It always returns `trial_run_authorized=false`, `actual_rpc_calls=0`, `stop_state=NO_RUN` even if user supplies positive request ceilings and hypothetical CU budget.

```zsh
python3 crypto-300-profit-mission/bsc-forward-follow-model/f0/f0_source_budget.py --hours 24
python3 crypto-300-profit-mission/bsc-forward-follow-model/f0/f0_source_budget.py --hours 48 --ws-bytes-per-block 1000 --cu-budget 30000000
python3 -m unittest discover -s crypto-300-profit-mission/bsc-forward-follow-model/f0/tests -p "test_*.py"
```

The first two commands **calculate only**; the third executes offline tests. Output counts are scenario estimates, not a runtime permission/certificate or vendor SLA.

## Explicit run authorization contract — STILL EMPTY

| Required user-approved field | Current value |
|---|---|
| `PROVIDER_AND_ACCOUNT` / free entitlement / account ownership | **UNRESOLVED** |
| `APPROVED_LOCAL_ENVIRONMENT` and permitted methods | **UNRESOLVED** |
| `MAX_TOTAL_RPC_CALLS` | **0 = NO_RUN** |
| `MAX_CONTROL_DISCOVERY_CALLS` | **0 = NO_RUN** |
| `MAX_WS_BYTES_OR_CU` and network request rate | **0 = NO_RUN** |
| `MAX_RETRIES` / per-method cap / abort criteria | **0 = NO_RUN** |
| `TRIAL_START_END_UTC` (first smoke check must also be separately bounded) | **UNRESOLVED** |
| `STORAGE_ROOT`, retention and raw-response privacy scope | **UNRESOLVED** |
| `COST_POLICY` | **FREE_ONLY / NO_PAYMENT / NO_AUTO_UPGRADE** |
| Wallet/transaction/signature/notification permission | **NONE** |

The table is a **future approval checklist**, not an invitation to infer approval from earlier messages. Do not ask the user for credentials in chat or embed them in Git.

**STOP conditions:** `BLOCKED_SOURCE`, `BLOCKED_REALTIME_CONTROL`, `DENOMINATOR_UNRESOLVED`, `INSUFFICIENT_LIVE_EVENTS`, `QUOTA_EXHAUSTED`, `NONFREE_COST_RISK`; log evidence then stop instead of substituting archived simulations.

**This PR's acceptance scope:** read-only source-method comparison, deterministic no-network capacity planner, corrected handoff, independent audit. **No actual real-data collection, RPC/API, 24–48h trial, connection setup, or change to approved PR #121.**
