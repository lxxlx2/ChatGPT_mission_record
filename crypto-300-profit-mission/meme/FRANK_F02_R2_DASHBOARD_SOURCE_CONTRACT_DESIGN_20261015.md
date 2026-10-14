# Frank F02-R2 Dashboard isolated research positions UI design and acceptance contract

Date: 2026-10-15 Asia/Bangkok
Status: \`CONTRACT_FROZEN_FOR_NEXT_STAGE / AWAIT_ACTUAL_MAC_F02_R1_PROBE / NO_UI_CODE_DEPLOY / NO_MERGE\`

## Background and non-negotiable mainline

The user goal is a **usable accurate locally hosted dashboard** for real observed Frank current holdings and actionable follow opportunities, with evidence/freshness and clear categories. Unfollowable, rejected or historical objects must not occupy actionable candidate positions; unknown current holdings must be pursued through valid research source collection and never fabricated to make the UI look full.

The implementation dependency remains:
\`A05-R1 verified full source (actual Mac) → A05-R2 frozen 32 target/account reconciliation (real archive) → F02-R1 approved source-anchored read-only API + real isolated Mac probe → F02-R2 isolated browser positions UI → F02-R3 full Mac acceptance → independent F01/C02/A05/F02 integration → final overall independent review\`.

- A05-R1/R2 have prior independent code approvals; full real October14 source externally reviewed by **one** independent other-AI reviewer, frozen 32 target observation **9 nonzero, 23 zero**, no sales/PnL claim.
- F02-R1 new API child [PR #63](https://github.com/lxxlx2/ChatGPT_mission_record/pull/63), exact \`f4007f64dc92c87854e752562ea9e24bbfd78c23\`, independent other-AI \`APPROVE\` (2026-10-15), real socket low/high Slot stale-positive P2 closed, SQLite fixed HTTP 503 P3 closed. Original [PR #62](https://github.com/lxxlx2/ChatGPT_mission_record/pull/62) remains \`REQUEST_CHANGES\`. Accepted **CODE** does not mean user Mac new Sidecar exists; default user Mac capture \`research_sidecar_imported=null\`. See [Mac isolated acceptance runbook](FRANK_F02_MAC_ISOLATED_SOURCE_ACCEPTANCE_RUNBOOK_20261015.md).
- Identical UTC synthetic tie \`latest_attempt=PARTIAL_SOURCE\` vs \`readiness=FRESH_VERIFIED_ARCHIVED_OBSERVATION\` reported as nonblocking P3 with **2 independently failing extra tests**. Do not hide P3; avoid broad code refactor for theoretical timestamp tie, but treat inconsistent readiness/attempt meta as **not promotable to actionable** at UI boundary. This is a proposed display guard; no current UI implementation claim.

## UI information architecture, actionability and provider constraints

For first isolated F02-R2 implementation:
1. Make a **separate researcher-only browser page** served by the exact same isolated loopback listener or otherwise same-origin localhost endpoint; **not** a direct edit or deployment of production \`mission_control/server.py\`. Cross-origin \`fetch\` from current production Dashboard to isolated localhost F02 API is not supported by current CORS policy and must not be hacked by enabling blanket CORS. A same-origin private static page or read-only localhost proxy only after code review is the safe path.
2. Show a compact **primary identity/source strip**: person display name/registered wallet (clickable copy exact Solana address), \`person_beneficial_ownership_verified=false\` explained as registration != controller proof, frozen target scope 32, capture SHA prefix with copy of full source ID, \`slot_min/slot_max\`, \`capture_observed_at_utc\`, \`capture_age_seconds\`, 2 non-atomic RPC queries, whether latest actual attempt succeeded, and last query time.
3. Main positions list is a **research wallet-account observation**, not an authorized trade signal. Only rows with all gates true (latest full source verified, freshness policy met, source attempt consistent, positive exact raw balance) can show an observed quantity. **Never convert this fact to BUY/FOLLOW without independent frozen Frank opportunity decision eligibility.**
4. Rows \`OPEN_ACCOUNT_NONZERO\`: show Mint exact CA, exact decimal quantity, number of open token accounts, Token/Token2022 Program and each account explorer link; \`OPEN_ACCOUNT_ZERO\`: explicit **observed zero account** (not 'sold'); \`NO_OPEN_ACCOUNT_OBSERVED\`: "no open account seen in complete two-program owner scan" with **unknown current/historical amount**, never 0/SELL; \`SOURCE_UNAVAILABLE\`: no amount display, clear reason (\`STALE_ARCHIVED_SOURCE\`, \`LATEST_CAPTURE_ATTEMPT_FAILED\`, \`LATEST_SOURCE_NOT_WIRE_VERIFIED\`, \`INCOMPLETE_OR_NO_LATEST_CAPTURE\`, backend 503).
5. Dedicated history/observation and candidate sections; do not put \`NO_BUY\`, rejected follow candidates, or stale/unknown holdings into primary "Current actionable" tiles. Since F02-R1 does not authorize trades and has no price/PnL, **F02 alone never places a token in the actionable list**. Native existing F01 eligibility must remain authoritative, only after later bounded integration review.
6. Explicit \`value_usd=null\`, \`cost_basis_usd=null\`, \`realized_pnl_usd=null\` must render \`未核实\`, **not** \`$0\` or \`0%\`. USD totals suppressed, no investment amount instruction or inferred profit. Historical 10 vs 9 positive observations **not** evidence of sell.
7. Expose a visible **"manual full-source capture required"** text/action instruction, not an automatic background scan or hidden RPC automation. Manual capture/process is a separate approved workflow; no write endpoint, no key/secret display. Offer convenient accurate copied CA and wallet links.
8. Multi-person/multi-wallet support is a first-class UI data contract (\`person_id\`, \`wallet_id\`, \`wallet\`, stable exact CA); the first roster is historically **Frank-wallet-locked**, so do not present an arbitrary person as if validated against these 32 targets.
9. Source freshness is not determined by browser page reload alone: it must reflect actual observed-at and selected SHA. On 5min+ old archived source, page must show stale and **all 32 quantities hidden**, even if A05-R2 still correctly reports an archived 9 positive / 23 zero historical result. The page must not offer a button that blindly marks old data refreshed.
10. Required error/empty UX: missing research Sidecar -> source configuration/503; wrong wallet -> no cross-person leakage; later lower/higher slot partial -> stale old positive masked and source failed; latest source complete but different SHA -> masked; P3 equal timestamp conflict -> do not promote quantity as actionable unless source attempts & readiness align; no local proxy to production private SQLite.

## Product acceptance matrix

| Test case | Mandatory visible result | Business gate |
| --- | --- | --- |
| Real archived 2026-10-14 at observation time, complete 32 target rows | 9 observed positive /23 observed zero, 0 absent; provenance SHA/slots/non-atomic | Archived research view **only** |
| Same archived source after F02 300-second TTL | \`STALE_ARCHIVED_SOURCE\`, 32 \`SOURCE_UNAVAILABLE\`, null quantities | No "current" balance claim |
| New valid source with 32 targets | Only observed positive/zero/absent status under approved TTL, accurate token account collection | Still not an actionable follow decision |
| Later partial lower residual Slot vs previous full | \`LATEST_CAPTURE_ATTEMPT_FAILED\`, no old positive, attempt SHA/time and selected old source differentiated | Must pass real localhost HTTP |
| Later partial higher residual Slot | Same fail-closed result | Must pass real localhost HTTP |
| Later unverified complete source | \`LATEST_SOURCE_NOT_WIRE_VERIFIED\`; no old positive | Do not bypass source hash |
| Same-Mint multiple Token Accounts | Exact full integer/decimal sum and details, Token2022 + state | No canonical ATA only assumption |
| No open account vs observed zero | Null/unknown vs explicitly observed \`0\` | Neither implies sale |
| Missing/invalid research Sidecar | Generic source error (503) and no retry-to-prod | No production data write |
| Synthetic exactly equal UTC contradictory attempt/readiness | Mark source status inconsistent/non-actionable (no false "latest good" promotion) | Nonblocking P3 tracked; UI must not present false trade recommendation |
| F01 NO_BUY/negative determination | Exclude from actionable, retain only research/history when needed | Frozen F01 decisions unchanged |
| Browser direct Mac isolated test | Same-origin private localhost API, no CORS bypass, timestamp visible and CA copy works | F02-R3 separate evidence |
| Long-running service and restart | Manual process close, no automatic LaunchAgent installed | Only separately approved deployment later |

## Implementation preparation and review flow

- First complete F02-R1 Mac **read-only preflight** against existing full bundle; obtain explicit user approval before creating new isolated research Sidecar; execute corresponding real \`--probe-once\` and store **privacy-limited** evidence before claiming F02-R1 business pass.
- Then branch from reviewed PR #63 code and build minimal **isolated browser renderer** and strong source/identity UI contract; do not retrofit production Dashboard routes until authorized final integrated release plan. Unit/browser/real localhost HTTP tests + full GitHub CI + one independent other-AI \`APPROVE\` against exact SHA.
- Conduct F02-R3 Mac browser verification with actual source, stale and recovery, screenshots and interaction proof, separate full F01/C02/A05/F02 integration and final independent whole-system review. No automatic merge/deploy.
