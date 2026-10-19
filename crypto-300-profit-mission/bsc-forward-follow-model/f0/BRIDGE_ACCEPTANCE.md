# BSC F0 — offline saved-RPC-to-state-machine bridge

Status: `OFFLINE_BRIDGE_IMPLEMENTED / ALL_SYNTHETIC / NO_NETWORK / PENDING_INDEPENDENT_REVIEW / NO_GO`

Authority: architecture PR #113 fixed `9134fcd41df49ef836b81c8a040974ad89c1fde1`, F0 preparation PR #116 fixed `cf88cd9f6568502f5c052ae3befc9cc16cbab98b`, state-machine PR #118 fixed `78e4d26ff7cd1074b7c8de44109b4356e5d0409d`, adapter PR #120 independently APPROVE fixed `c0a6dca08a57316f70ca7b7e1358c89e262918f4`.

## Concrete incremental functionality (L1/L2 bridge)

The module `f0_rpc_bridge.py` connects existing *saved* JSON-RPC response normalization to the approved offline clock-injected event state machine without modifying either approved code module:

1. Read a user-provided JSON **offline fixture only** (`mode=OFFLINE_BRIDGE_FIXTURE_ONLY`, `trial=true`, `chain_id=56`). No endpoint, credential, clock, subscription, daemon, buy or sell call exists in this bridge.
2. A saved `eth_getBlockByNumber` result yields WATCHLIST or ordinary-Router `CONTROL_CANDIDATE` transaction IDs. Map the latter to the state machine `CONTROL_RANDOM` candidate path, with actual simulated seeded selection still performed by the *existing* state machine. No real random market sampling or coverage claim.
3. On the injected **block-observed** time, create one immutable UNKNOWN detection per `(chain,wallet,tx_hash)`; preserve the same `event_id`, `first_received_ms`, and original blob hash. Never invent an actionable BUY at block time if the Token and direction are unknown.
4. On separately injected **receipt-observed** time, validate identity, decode ERC20 Transfer records, and obtain BUY_CANDIDATE/SELL_CANDIDATE *hint* only. Update the existing UNKNOWN event's side/CA at this **later observation time**. No lookahead timestamp overwrite and no duplicate event. The resulting virtual ENTRY/EXIT requests use the approved +60/300/900s synthetic scheduler.
5. Even if the receipt is marked successful and a synthetic tip height is provided, the bridge **does not send a successful synthetic E1/causal-flow attestation to the state machine**. Until finality and causal Router/swap policies are frozen and independently proven, these stay `E0_SEEN_SYNTHETIC` and `UNVERIFIED_SWAP_ROUTE`. Failed receipt rejects its event; synthetic reorg explicitly invalidates events and cancels/rejects outstanding virtual quote outcomes.
6. Saved `eth_call` ABI quotes use adapter `SIMULATED_ARCHIVE_QUOTE/NO_QUOTE` and go to an **archive-only sidecar**. They are never injected as timed `QUOTED` or `SYNTHETIC_REPLAY_QUOTE` into state-machine execution. A **separate explicit** `virtual_quotes` field permits synthetic response replay only when `synthetic_response=true`; this exercises quote-processing edge cases with no claim about live request time.
7. Preserve original full-block, receipt and archive-quote source SHA256; include every injected-time assumption and differentiated sample denominators. No E2 actual, E3 actual, actual RPC, live QUOTED or paper-profit labels are produced.

## Executed tests

```zsh
python3 -m unittest discover -s crypto-300-profit-mission/bsc-forward-follow-model/f0/tests -v
python3 crypto-300-profit-mission/bsc-forward-follow-model/f0/f0_rpc_bridge.py --fixture crypto-300-profit-mission/bsc-forward-follow-model/f0/fixtures/rpc_bridge_replay.json --report /tmp/bsc-f0-rpc-bridge-report.json
```

The full suite includes **36 approved state-machine cases + 18 approved RPC-format cases + 26 new bridge cases = 80/80 PASS** in the local isolated source copy. Tests cover both groups, BUY/SELL, failure receipt, provisional UNKNOWN evolution, origin time, archive/live quote separation, late response, missing/invalid quote value, BACKFILL, reorg before/after virtual quotes, same event identity, invalid RPC block/receipt identity, malformed ABI, source provenance and prohibition on live inputs. The stored synthetic CLI report is deterministic and must be independently regenerated against the frozen source SHA.

The example saved-RPC fixture has 3 detected transactions (WATCHLIST 2, ordinary Router candidate 1), three receipts (BUY hint, SELL hint, one failed), an archive-only quote, and two explicit virtual quote responses (one synthetic success, one synthetic error). Group selection is synthetic and fixed with `control_modulo=1` in the fixture. It does not demonstrate real free-provider access, actual control discovery, E2 causal swaps, quote latency or completed F0.

## Explicit remaining F0/F1 blockers and stop conditions

- **NO F0 LIVE PERMISSION:** No RPC or WebSocket, no real source is contacted. True 24–48-hour read-only trial still needs explicit user authorization including allowed provider/app, free quota, `MAX_TOTAL_RPC_CALLS`, `MAX_CONTROL_DISCOVERY_CALLS`, allowed Mac environment, storage/retention and time window. User refusal or missing scope = `NO_RUN`.
- Real observation clock must come from independently measured ingress; injected fixture `observed_ms` is not any true first public availability evidence.
- Actual initial control Router coverage vs. cost/quotas remains `NOT_MEASURED`; group membership alone is not a valid matched baseline.
- Chain finality/confirmation and causal swap Router decoding are intentionally `UNRESOLVED_F1_POLICY`; saved Transfer flow hints cannot become actual E2/E3. In particular, a receipt itself does not prove a path is sellable.
- Valid archive quotation does not prove simultaneous live `QUOTED`; user authority is required for any experiment issuing real quote requests.
- Independent expected signed BUY denominator, provider correlation failures and completeness remain `NOT_MEASURED`; no 95% PASS assertion.
- No actual profit/trading implication and no funds allocation, transaction signing, alerts, emails, new automations, Git merge or production launch.

Next mainline step after independent **APPROVE of this fixed bridge SHA**: a bounded source-method assessment and user-approved F0 live pilot, not more historical PnL forensics or a new speculative L3/L4 strategy.
