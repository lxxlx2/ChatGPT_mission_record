# BSC forward wallet-follow module — single ongoing handoff

Updated: 2026-10-20 Asia/Bangkok. **Do not trust this file without independently checking current PR heads, review comments and source blobs.** This module must not take over old PR #40 or PR #97.

## One objective

Prospectively capture BSC Meme-wallet signed buys and sells, measure when a third party can act with actual quote cost at `+60/+300/+900s`, compare conservative PAPER net outcomes to a pre-registered real ordinary Router random-control cohort. Distinguish L1 capture, L2 executability, L3 as-of features, L4 comparative performance. No retrospective profits or synthetic exercises can prove actual followability.

## Fixed approvals (read only, no auto-merge)

- PR #113 `9134fcd41df49ef836b81c8a040974ad89c1fde1`: architecture **APPROVE**; separate unmerged Draft branch.
- PR #116 `cf88cd9f6568502f5c052ae3befc9cc16cbab98b`: trial cohort & F0 prep **APPROVE**; deterministic preselected 20 primary/10 backup only, replacement proof rules, no outcome fields.
- PR #118 `78e4d26ff7cd1074b7c8de44109b4356e5d0409d`: pure synthetic state machine **APPROVE** (36 original tests, separately 103 adversarial).
- PR #120 `c0a6dca08a57316f70ca7b7e1358c89e262918f4`: saved JSON-RPC parser **APPROVE** (18 tests, separately 60 adversarial). Its HEAD was independently verified before this development; it remains Draft, not merged.
- PR #121 `bf9fbb0a6bbff3a9375c6a937cea52d016104733`: offline bridge **APPROVE**. Independent reviewer ran 80/80 tests plus adversarial probes. No actual RPC or E3. PR remains unmerged Draft; corrected F0 test invocation is `python3 -m unittest discover -s crypto-300-profit-mission/bsc-forward-follow-model/f0/tests -p "test_*.py"`.
- Current next-stage [Draft PR #122](https://github.com/lxxlx2/ChatGPT_mission_record/pull/122), branch `research/bsc-forward-f0-live-source-readiness-20261020`: real-free-source **readiness only**, `f0/F0_REAL_SOURCE_READINESS.md`, offline budget CLI and 12 tests, `f0/F0_SOURCE_PREFLIGHT_TEST_EVIDENCE.json`. Locally executed 92/92 combined tests against blob-matched PR #121 baseline + new code; source quotas/performance still UNVERIFIED. **Latest PR #122 head must be re-read from Git; independent review PENDING; no runtime permission.**

## Real implementation state

Fully offline Python stdlib work from existing PR #120, with no modifications to its approved parser or the earlier state machine. `f0_rpc_bridge.py` connects a saved full BSC block response to UNKNOWN detection, saved receipt to progressive BUY/SELL hint at injected receipt observation time, a synthetic seeded random-control selection path and three virtual entry/exit quote deadlines. Successful receipts remain **provisional** because Router causality and F1 finality have not been certified. Saved archive `eth_call` quotes remain sidecars, never live or synthetic timed quote successes. Invalid receipts and reorg cancel/reject synthetic quote state.

Bridge integration: 26 additional tests; all 80 tests (36 + 18 + 26) passed locally with saved fabricated data and independently rechecked at PR #121 approved SHA. Fixed report `fixture_bridge_report.json` has no real RPC/E3/QUOTED/PnL evidence. Do not call this an online collector.

## Next action & review

1. `f0/F0_REAL_SOURCE_READINESS.md` and pure arithmetic `f0/f0_source_budget.py` document **the next feasibility decision**. Mainnet block time is now ~0.45s: 192,000 full-block lookups per day in naive one-per-block enumeration. BNB public RPC disables `eth_getLogs` on listed mainnet endpoints; BSC `eth_subscribe` through Alchemy is documented but **not validated against this user's free account**. All sample CU/bandwidth costs are assumptions, not measured usage.
2. Reviewer should inspect this new preparation-only PR, rerun offline budget unit tests and check provider-method citations, no-network design and accurate no-run state. Fix only mainline blockers.
3. **PR #121 reviewer P2:** the bridge passes `min_confirmations` but never positively enforces E1; label `UNRESOLVED_F1_POLICY` until F1 policy freeze and tests. False BUY hints caused by third-party payer/airdrop-like Transfer combinations remain `UNVERIFIED_SWAP_ROUTE`; no real E2/E3 promotion. The previous `discover -s tests -t .` command is incorrect; use the repository-root test invocation above.
4. When independently approved, the only permitted automatic work is **offline preflight and planning**. Real smoke check or 24–48h F0 run requires separate written authorization for provider/app, exact approved read methods, account free quota, maximum total/control/WS calls and bytes, duration, retries, local environment, retention and stop policy. Until then `MAX_TOTAL_RPC_CALLS=0`, `MAX_CONTROL_DISCOVERY_CALLS=0`, `NO_RUN`.

## Hard stop / authority

`NO_TRADE / NO_RPC_WITHOUT_PERMISSION / NO_PAID_GMGN / NO_WALLET_SIGN / NO_EMAIL / NO_NOTIFICATIONS / NO_BACKGROUND_MAC_SERVICE / NO_NEW_AUTOMATION / NO_PRODUCTION_DEPLOY / NO_MERGE`.

Current F0 readiness is offline budget planning only; free-source feasibility, real source cost and first-observed latency are `UNTESTED`. F1 strategy and finality-policy freeze is not complete; F3 6–8wk prospective observation and blinded L4 evaluation have not begun. All real denominators, on-chain causal BUY/E2, E3, actual Router requests and actual profitability remain `NOT_MEASURED/UNRESOLVED`. All stages require independent review; approved SHA is immutable by definition.
