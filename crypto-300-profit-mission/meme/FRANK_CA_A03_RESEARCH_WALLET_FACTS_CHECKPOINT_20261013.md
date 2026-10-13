# Frank / CA A03 person-scoped research wallet facts interface checkpoint

Date: 2026-10-13 Asia/Bangkok

Status: `A03_PARTIAL_CODE / CI_PENDING / EXTERNAL_REVIEW_REQUIRED / RESEARCH_ONLY / NOT_DEPLOYED`

## Dependency and authority

- Stacked source: PR #42 at `22f7b8f760fea62f1f713d5aaccb9391cae1a26a` (A02 research registry remediation, still Draft and awaiting a second independent review).
- Parent live main at audit: `449edcf1623836fc41baaf31abdc1b39260ebd7d`.
- `MISSION_SPEC.md`, `FRANK_CA_MULTI_PERSON_TECHNICAL_DESIGN_20261013.md` and 41-task TODO remain controlling.
- Frank V1 production `FrankReader`, mission service, `signals/registry.py`, `meme/registry.py`, writer, `forward.sqlite`, Gmail, frozen policy, Dashboard and Mac run scripts are **unchanged**.

## Implemented part of A03

- `research_wallet_facts.py` provides `WalletFactsProvider` injection and `PersonResearchReader` read-only research selection.
- Same exact mint may be queried separately for two people, or across two wallets belonging to one person. Historical registry slot scope is mandatory. Disabled or unknown people fail before querying a provider.
- Each snapshot is tied to exact chain/wallet/mint/slot/finality/account evidence; values outside the binding interval or identity mismatches are rejected. Missing source returns `NOT_CAPTURED` and `balance=null`, never zero.
- A returned archive balance is explicitly marked `DATED_SOURCE_ASSERTION_NOT_WALLET_COMPLETENESS`; even present source rows have `current_balance_verified=false`, `chain_complete=false`, and `person_balance/person_pnl_usd=null`. Research binding approval/reference fields do not elevate historical facts to person beneficial ownership or live authorization.
- No default source provider loads arbitrary on-disk or remote wallets. A04/A05 must supply an independently verified read-only sidecar provider; A06 handles internal transfers/cost/PnL. No new background scanner or signal privilege.

## Next product-critical gates

1. Independent review on exact A02 SHA; resolve blockers without merging if review fails.
2. A03 still requires a reviewed concrete read-only sidecar adapter, production-hardcode coupling inventory and final backward compatibility review. **Do not mark A03 DONE.**
3. A04 normalized finalized transaction legs + sidecar, A05 complete ATA owner inventory, A06 verified per-person portfolio. Real Mac source/evidence inspection must be separate and privacy-safe.
4. Parallel, isolated F01 current-actionable follow list and C01/C02/C07/C08 CA UI/data work based on latest main. No change to historical immutable email/outbox or frozen V1 policy.
5. Dedicated A03 CI focused and full tests (including real-Git replay). Record actual final SHA/run conclusion once complete.

This file records only submitted engineering work. No on-chain live balance, real user identity control, resolved cost basis or functional Dashboard integration is asserted.
