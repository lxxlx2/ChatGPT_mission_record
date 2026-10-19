# BSC forward wallet-follow research — authoritative handoff

Updated: 2026-10-20 (Asia/Bangkok). **Scope is this module only.** Read this alongside the real GitHub PR HEADs; never assume these SHA values are the latest without checking.

## Business goal

Assess, using *forward-observed* buys of historically early-acting BSC meme wallets, whether a third party can follow after measured delay at configured size and realize conservative **paper** returns better than a pre-selected ordinary-Router-wallet control. Separate L1 discovery reliability, L2 paper executability, L3/L4 increment above controls. No historical cherry-picking, no trading advice, no real-execution assertion.

## Current stage / fixed approvals

- PR #113: architecture `APPROVE`, SHA `9134fcd41df49ef836b81c8a040974ad89c1fde1`, lives on distinct unmerged Draft branch.
- PR #116: F0 preparation `APPROVE`, SHA `cf88cd9f6568502f5c052ae3befc9cc16cbab98b`.
- PR #118: offline state-machine `APPROVE`, SHA `78e4d26ff7cd1074b7c8de44109b4356e5d0409d`: 36/36 original offline tests plus independently reported 103/103 targeted checks. No real E3, QUOTED or paper-profit evidence.
- Current work: **[Draft PR #120](https://github.com/lxxlx2/ChatGPT_mission_record/pull/120)**, stacked on PR #118's fixed SHA; BSC RPC *response parsing without network*. Check its current HEAD before relying on any reported SHA; **independent review is PENDING**, and approval does not inherit from PR #118.
- Independent PR #40 (23 BSC research wallets) and PR #97 (449 EVM wallet history analysis) remain separate, no changes or cancellation. F0 preselected 20+10 public wallet IDs pinned at PR #116.

## Functionality and truthful evidence

Previous: synthetic BUY/SELL/UNKNOWN progressive state machine, virtual entry/exit quotes, E1 failure/reorg/backfill barriers, symmetric random-group behavior, audit statuses; **only synthetic**.

Current: saved full-block, receipt/ERC20 Transfer and ABI Router quote *offline* normalization. In a single isolated tree, **54/54 local `unittest` PASS** (36 original fixed PR #118 tests + 18 new adapter tests); all three original source blobs match PR #118 approved Git. Saved-fixture CLI reports 0 actual RPC / 0 E3 / 0 real quoted / 0 paper-profit labels. Decoded Transfer combinations are provisional hints, not proven actual swaps or realtime signals.

## The next useful step

1. Independent reviewer inspect new fixed SHA, independently rerun all 54 tests, replay fixture, test falsely upgraded E2/E3/QUOTED, malformed RPC and error paths. If P0/P1, fix only blockers then re-review fixed SHA.
2. After this adapter's independent APPROVE: implement **local-only** bridge from parsed RPC candidate/receipt into existing offline event engine with recorded UTC and per-source original blob hashes, still no network. Prioritize actual functional interface over ornamental guards.
3. Only after required authorization: bounded F0 real free-provider feasibility (watchlist and ordinary control detection, true 60/300/900s timed quote requests, independent denominator, request costs) with explicit maximum RPC budgets, provider, storage and stop conditions.

## Hard prohibitions / stop rules

No real RPC without explicit user permission; no tokens, private keys, wallet signing, trading, paid GMGN, email, notifications, new automations, background Mac launchd, production deploy, PR merge. F0 failures like no live control stream, incomplete denominator, missing free source are reportable `BLOCKED/INSUFFICIENT` — do not silently replace with simulated performance. F3 will be blinded and requires final strategy freeze before first sample. For each next task specify its L1/L2/L3/L4/V contribution, baseline SHA, tests, raw evidence, exact remaining blocker and Git report; do not restart PR40/97 forensics or redesign approved architecture.
