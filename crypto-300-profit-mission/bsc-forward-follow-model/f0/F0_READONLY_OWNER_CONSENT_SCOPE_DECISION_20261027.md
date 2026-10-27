# BSC 前向地址跟单 F0：取消三方签名，改用用户单次许可和有界只读执行

Date: 2026-10-27 Asia/Bangkok
Decision: `USER_ACCEPTED_SIMPLIFICATION / POLICY_RECORD_ONLY / IMPLEMENTATION_NOT_APPROVED / NO_RPC`
Owner: user instruction in conversation after explicit explanation of D2/D3 overengineering.
Applicability: BSC forward-follow **public-chain read-only research** only; no wallets, signing transactions, orders, swaps, automated trading, production monitoring, unattended service or paid RPC.

## 1. Superseding decision

The user has explicitly agreed to remove the requirement for three separate human signing authorities, three Ed25519 keypairs, public-key enrollment ceremony, revocation infrastructure and signed D2/D3 release proofs for this **bounded, local, foreground, read-only** address-following research.

The historical Draft PRs #217 (`8362b4048d45b0bd13be4a6e4b6be35ad737819b`), #219 (`1b35156710a860ae579c0e2ff1fd47d8f1052ad5`), #221 (`9c847bb684681b93dc16c206df917d07cb26ef85`) and #223 (`fff69d569a3a20e908768cccda359bb6439ac051`) remain immutable records of explored but now **NOT REQUIRED** production-signature governance for this bounded public-data research. Their earlier docs-only approvals are not security proofs, and they do not create live RPC permission.

For this narrow use case, A1/A2/A3 separate cryptographic principals, A4 full production signature protocol and A5 three-signature enrollment workflow are **SUPERSEDED AS MANDATORY LAUNCH GATES**. A6's explicitly accepted honest macOS-account threat model remains in force: same-UID actively malicious tampering is outside the guaranteed defense boundary, not magically solved. A7's substantive guarantees (fixed reviewed code/runtime, true resource caps) and A8's fresh, explicit user consent for actual network activity **remain mandatory as engineering and human gates**, without requiring a cryptographic signing ceremony. This decision does not weaken STOP/UNKNOWN accounting.

This policy is authoritative for the next **research design choice** only, after a fixed-SHA code review. It does **not retroactively switch on** `send_live()` in existing code, relax old sentinels, mint permits, or authorize any old or future single-use request.

## 2. The minimum sufficient one-operator process

1. **Code freeze and independent technical review:** pin the exact Git commit, all actually loaded source/dependency bytes, sole launcher, fixed BSC provider, three permitted read-only JSON-RPC methods, safe budgets and single-coordinator behavior. Independent review may be by Codex/Claude as *code audit*, with exact SHA; no second or third human signing authority is required. Tests must not be mistaken for real chain evidence.
2. **A newly scoped user instruction, each real run:** user explicitly approves exactly **one** foreground read-only experiment with stated **exact SHA**, named machine/account or designated trusted execution environment, permitted method/source, request/response-byte/time/rate upper limits and an agreed private evidence location. Generic '继续'/'接受简化方案' is **not** permission to call RPC. All previous 4-, 24-, 30- and 62-attempt grants are spent and cannot be reused.
3. **Cheap one-use local guard:** on the trusted macOS account bind a fresh unpredictable run ID to one fixed owner-private local receipt/nonce journal; reject a duplicate/active run, mismatch, stale SHA, expired UTC or path alias. Use existing atomic O_EXCL/fsync and RID-before-POST writers where appropriate; do not invent a second coordinator or parallel signing registry. After crash/uncertainty, classify the run consumed/unknown, never auto-rerun. This is accidental/concurrent reuse protection, **not** cross-session anti-tamper against malicious same UID.
4. **Physical execution:** only one reviewed foreground launcher; preserve the original single global **three-slot** coordinator and global start pacing. Verify real wall UTC and budget at each last physical POST decision; actual request cap includes timeouts, nulls and failed attempts. Fixed TLS endpoint and chain 56, no proxy, paid fallback, redirect, WS, additional RPC methods, transactions, trades or background watcher under this F0 grant.
5. **Durable evidence and evaluation:** exclusive presend `RESERVE_UNKNOWN`/RID before any socket/POST, bounded original RAW bytes/SHA256 before SETTLE, block parent-hash/height/finality/gap classifications, measured local ingress time distinct from block header time, no fabricated success after partial response, no implicit retry. Publish a redacted, source-cited evidence aggregate, never raw private journal or a fake PnL.
6. **Scope change:** if task later expands to signing transactions, unattended live monitoring, higher privileges or non-public data, a **new** risk evaluation and new user approval are required. No approval inheritance from this decision.

**Allowed offline work now:** source inspection; reuse existing code and saved evidence; analysis and tests; a single coherent Draft implementation PR with reviewed source + hard-deny live endpoints until the next user authorization. No live calls now.

## 3. What the saved real data actually shows, and the next business milestone

Current read-only evidence from the already saved `F0_SHORT60_LAG_OFFLINE_RESULT_20261020.json` (source Git blob `ce1d9cb9e19e12e291da1b3e3406f57d6958ad54`) and paired report:

| Measure | Observed | Meaning / limitation |
| --- | --- | --- |
| One earlier authorized sample | 60 consecutive future block heights, 62 raw HTTP responses, 62/62 SHA256 verified | Historical consumed permission; no remaining grant |
| Observed raw block transactions | 5,940 | Not necessarily 5,940 validated swaps |
| Frozen watch signer candidates | 0 | Too few live watch events to score F0 followability |
| Router-address + selector candidates | 40 | `router_swap_causality_attested=false`; control eligibility still FALSE |
| Block-header timestamp span | 26 s | Header timestamps have 1-second granularity |
| Local receive span | 58.979 s | About 59 s to collect block set; not true global first-seen |
| Median receive-minus-header | 18.496 s | Clock / timestamp / lag proxy only |
| First-parent link | **UNANCHORED** | Only 59 internal parentHash links verified, not all 60 anchored |
| E2/E3 actual executable quotes | 0 | No 60/300/900 second true quote evidence or profitability |

**Next technical outcome:** prove whether an affordable, user-authorized source can deliver the frozen 20 PRIMARY + randomized contemporaneous ordinary Router controls with acceptable first-observed latency and fully auditable completeness under subsecond BSC blocks. Explicitly measure verified watch BUY/SELL events, receipt/Router causal validity, control sampling denominator, missed heights, latency, and +60/300/900 scheduled **real quote** feasibility. If source falls behind, declare **F0_INSUFFICIENT_SOURCE / L1_NOT_PASSED**, do not stamp PASS or derive ROI. L1/L2/L3/L4 remain separate evidence gates. Do not use historical realized return to select F0 cohort or mark ordinary Router address hits as controls.

Older work including `f0_l1_live_short.py` has a simpler one-shot bounded permit, and the full three-slot/D1 code already has journal and physical mock-test facilities. **Reuse audited components and repair any source limitation at a new exact SHA; do not build another authorization platform.** It is invalid to treat this decision as overriding an existing method's unconditional `send_live` deny.

## 4. Concrete replacement release checklist

Only three operational release questions remain for a later real F0 test:

- `SOURCE_REVIEWED`: fixed Git SHA, independent code test, read-only RPC scope and true request-time/byte budget enforcement PASS, no unapproved network entrypoints.
- `USER_SINGLE_RUN_APPROVED`: new explicit one-shot user instruction for that fixed code, method, machine, budget and expiry PASS.
- `RUN_EVIDENCE`: one foreground run, non-replayable under trusted user account, durable original bytes/attempts and honest gaps; success/failure assessed **after** run. No green test substitutes for live evidence.

Until first two pass: `NO_LIVE_NETWORK / F0_NOT_PASSED`. Immediately after any run: no automatic second run; F0 outcome is established by evidence, not permission.

Historical `D1_BLOCKED_AUTHORITY / PRODUCTION_NO_GO` remains true of **existing unmodified code**. This new simpler decision **supersedes the three-party process as a design prerequisite**; it does not falsely claim that the existing executable gates or code reviews have already been changed.

Global boundary this turn: `NO_DEPLOY / NO_RESTART / NO_RPC / NO_TRADES / NO_BACKGROUND / NO_MERGE / NO_KEYS / NO_NEW_AUTOMATION`.
