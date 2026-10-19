# BSC forward wallet-follow module — single ongoing handoff

Updated: 2026-10-20 Asia/Bangkok. **Do not trust this file without independently checking current PR heads, review comments and source blobs.** This module must not take over old PR #40 or PR #97.

## One objective

Prospectively capture BSC Meme-wallet signed buys and sells, measure when a third party can act with actual quote cost at `+60/+300/+900s`, compare conservative PAPER net outcomes to a pre-registered real ordinary Router random-control cohort. Distinguish L1 capture, L2 executability, L3 as-of features, L4 comparative performance. No retrospective profits or synthetic exercises can prove actual followability.

## Fixed approvals (read only, no auto-merge)

- PR #113 `9134fcd41df49ef836b81c8a040974ad89c1fde1`: architecture **APPROVE**; separate unmerged Draft branch.
- PR #116 `cf88cd9f6568502f5c052ae3befc9cc16cbab98b`: trial cohort & F0 prep **APPROVE**; deterministic preselected 20 primary/10 backup only, replacement proof rules, no outcome fields.
- PR #118 `78e4d26ff7cd1074b7c8de44109b4356e5d0409d`: pure synthetic state machine **APPROVE** (36 original tests, separately 103 adversarial).
- PR #120 `c0a6dca08a57316f70ca7b7e1358c89e262918f4`: saved JSON-RPC parser **APPROVE** (18 tests, separately 60 adversarial). Its HEAD was independently verified before this development; it remains Draft, not merged.
- New stacked bridge Draft PR: fixed SHA and URL must be read from its actual GitHub PR head; this file was prepared **before** its independent review, status `PENDING_INDEPENDENT_REVIEW`.

## Real implementation state

Fully offline Python stdlib work from existing PR #120, with no modifications to its approved parser or the earlier state machine. `f0_rpc_bridge.py` connects a saved full BSC block response to UNKNOWN detection, saved receipt to progressive BUY/SELL hint at injected receipt observation time, a synthetic seeded random-control selection path and three virtual entry/exit quote deadlines. Successful receipts remain **provisional** because Router causality and F1 finality have not been certified. Saved archive `eth_call` quotes remain sidecars, never live or synthetic timed quote successes. Invalid receipts and reorg cancel/reject synthetic quote state.

Bridge integration: 26 additional tests; all 80 tests (36 + 18 + 26) passed locally with saved fabricated data. Fixed report `fixture_bridge_report.json` has no real RPC/E3/QUOTED/PnL evidence. Do not call this an online collector.

## Next action & review

1. Reviewer must check the new stacked PR fixed SHA, compare to PR #120 approved SHA, rerun full 80 test suite and bridge CLI, verify saved evidence SHA256 and independently challenge archive-quote promotion, same-identity UNKNOWN-to-BUY flow, failure/reorg, timestamp attribution, side hints and control selection.
2. Fix only actual P0/P1 functional blockers on the same PR branch and get new fixed SHA review. Avoid endless boundary additions and historical forensic detours.
3. Once bridge APPROVE, prioritize source/provider feasibility (free BSC service, full-block enumeration cost, wallet first-observed timings, normal ordinary Router control stream, independent chain denominator, live timed quotes). Any real request/run still needs the user's separate **written authorization** including provider, quotas, call ceilings, storage, duration, allowed local environment; no automatic service setup.

## Hard stop / authority

`NO_TRADE / NO_RPC_WITHOUT_PERMISSION / NO_PAID_GMGN / NO_WALLET_SIGN / NO_EMAIL / NO_NOTIFICATIONS / NO_BACKGROUND_MAC_SERVICE / NO_NEW_AUTOMATION / NO_PRODUCTION_DEPLOY / NO_MERGE`.

F1 strategy and finality-policy freeze is not complete; F3 6–8wk prospective observation and blinded L4 evaluation have not begun. All real denominators, on-chain causal BUY/E2, E3, actual Router requests and actual profitability remain `NOT_MEASURED/UNRESOLVED`. All stages require independent review; approved SHA is immutable by definition.
