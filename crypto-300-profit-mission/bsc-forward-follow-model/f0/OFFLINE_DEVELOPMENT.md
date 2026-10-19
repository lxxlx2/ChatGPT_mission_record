# BSC Forward Follow F0 — Offline Collector Development and Acceptance

Status: `OFFLINE_IMPLEMENTATION_REVIEW_FIX / SYNTHETIC_ONLY / NO_RPC / PENDING_INDEPENDENT_REVIEW / NO_GO`

Architecture: [PR #113](https://github.com/lxxlx2/ChatGPT_mission_record/pull/113) fixed commit `9134fcd41df49ef836b81c8a040974ad89c1fde1`.
Preparation: [PR #116](https://github.com/lxxlx2/ChatGPT_mission_record/pull/116) APPROVE fixed commit `cf88cd9f6568502f5c052ae3befc9cc16cbab98b`.
This branch is based on PR #116's reviewed commit, and must be reviewed separately. The original PR #116 and PR #113 remain unchanged.

## What actually works offline

A pure Python standard-library **synthetic event replay**, with no socket, RPC, API keys, timed background jobs, signing or transactions. It is **not** a live collector. The CLI accepts ONLY `mode=SYNTHETIC_ONLY` and trial events, and sets `e3_actual_count=0`, `quoted_actual_count=0`, and `paper_profit_labels=0` even if fixtures exercise E1/E2-like shapes or virtual quote scheduling.

## PR #118 independent review fixes (three P1; compare fixed SHA db8c0781...)

1. `quote` fixture rows now require explicit `response_status: SUCCESS` and a **positive decimal string** `synthetic_amount_out_raw`, with no `error`. Any error, missing/null/zero/invalid amount or absent success status becomes `NO_QUOTE` with `quote_unavailable.reason` and a digest of the source row. This applies identically to WATCHLIST / CONTROL_RANDOM and ENTRY / EXIT. Timely virtual scheduling alone is not a quote success.
2. A new append-only `direction_update` input identifies an existing UNKNOWN E0 record as BUY or SELL **under the same event ID**, without changing `first_received_ms` or replacing actionable discovery with block time. Exactly the first real-time update `at_ms` becomes `actionable_ms`. An E1 receipt received while the direction was UNKNOWN is retained and causality-checked after identification; rejected/reorged events cannot be resurrected. Only one 3-delay schedule is created. Duplicate wallet+tx IDs are rejected in this bounded single-CA synthetic prototype.
3. SELL has a **separate** EXIT virtual quote scheduler, `purpose: EXIT`, an independent `exit_quote_state`, and `exit_quote_request_scheduled` / `exit_quote_replay` trace. The 60/300/900s virtual delays for EXIT are interface-test scenarios, **not** a frozen production sell policy. SELL never appears as a BUY quote. Failed E1 and reorg invalidate SELL quotes with the same semantics as BUY; controls use the same state machine.

The existing six-event fixture remains six events, still pure synthetic, and now annotates all five synthetic quote responses with explicit `response_status: SUCCESS`. New negative tests separately cover absent value, upstream error, null/invalid value for main/control, UNKNOWN before/after receipt upgrade without duplicate count or backdating, and SELL quote success/failure/reorg/control. This review repair does not add a network/production collector.

Functions exercised end-to-end:
- Preserve two distinct clocks: observed transaction hash vs first BUY/SELL+CA actionable identification; reject backdated/future actionable times.
- Identify BUY/SELL/UNKNOWN, allow explicit UNKNOWN→BUY/SELL direction update in the same event, retain BACKFILL without scheduling L2; synthetic E1 owner/receipt/confirmation checks and E2 path/Router evidence gates.
- Select random ordinary Router controls with deterministic pre-registered FNV32 `(seed|wallet|tx_hash)` and identical +60/+300/+900 second virtual quote scheduling as the watchlist.
- Record virtual ENTRY/EXIT quote deadlines and synthetic response source/timestamp; real success needs a valid explicit response status and positive raw amount; missing, upstream-error, late and E1-failed stages stay distinct and never turn into REAL QUOTED.
- Receipt failure or simulated reorg INVALIDATED: reject pending and prior quote outcomes in final eligibility status, preserve append-only trace of observed synthetic events and previously seen quotes; no control redraw.
- Idempotent input-row hashes, reject conflicting event IDs, track group/state/quote denominators. Output is a deterministic JSON report with original fixture SHA256 and explicit synthetic labels.
- No F1 L2 paper profit/fee model yet; no real Router quote, official BSC finality or independence-of-RPC check (all deliberately reserved for separately authorized F0 live trial and F1 freeze).

## How to test locally (zsh, commands contain no inline comments)

```zsh
python3 -m unittest discover -s crypto-300-profit-mission/bsc-forward-follow-model/f0/tests -v
python3 crypto-300-profit-mission/bsc-forward-follow-model/f0/f0_offline_collector.py --fixture crypto-300-profit-mission/bsc-forward-follow-model/f0/fixtures/offline_replay.json --report /tmp/bsc-f0-offline-replay.json
```

Both commands use local fixtures only and do not depend on the main Mission's local agent runtime, external networks or private keys. The report is written ONLY when `--report` is supplied. `--fixture` is mandatory; `--report` omission prints the report.

## Boundaries, not evidence of live feasibility

- The fixture contains fake public 0x-shaped wallets/tokens/receipts and virtual quote responses. `flow.swap_route_connected` and `confirmations` are **fixture assertions**, not independently validated on-chain observations. No confidence can be gained about actual BSC Router log decoding from this trial alone.
- E2-like labels carry `SYNTHETIC`. No E3 and no realized profit can ever be issued by this CLI. Valid synthetic responses are labelled `SYNTHETIC_REPLAY_QUOTE`; quote errors or missing responses become `NO_QUOTE`; neither is real-time `QUOTED`.
- A real F0 would need separately authorized endpoints, bounded call budgets, actual trial wallet eligibility checks, encrypted/private quote storage policies, provider/clock measurements, independent gap reconstruction, E1 finality policy, an authenticated control stream and actual multi-delay Router quoting. Missing one of these should not be represented as a successful production feature.
- Current code is a prototype for **state-machine interface tests** only. It is not approved to run on a schedule and contains no network connector. No Git merge, deployment, notification, wallet signature or trade permission is implied.

## Required review gate

Other AI must inspect the fixed Git SHA, execute the committed test suite, run the CLI, review each adversarial case (lookahead, late quote, mismatched signer, wrong Router, failed E1 in controls, unknown, backfill, reorg, causality), and confirm no network/trade code. Status remains `PENDING_OTHER_AI_REVIEW` until independent approval at the exact corrected code SHA. Do not open additional stage work for superficial boundary cases; identify true integration blockers in one review report.
