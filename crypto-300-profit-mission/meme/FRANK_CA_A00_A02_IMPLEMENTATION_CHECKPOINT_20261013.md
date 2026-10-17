# Frank / CA development checkpoint — A00 / A01 / A02

Date: 2026-10-13 Asia/Bangkok

**Branch:** `dev/frank-ca-registry-a00-a02-20261013`, created from immutable main `17a71c863b44c67f7a1a47639fd482958e56ee4b`.

**Scope:** data/source inventory, freeze 12 screenshot cases, first research-only person/multi-wallet registry + tests. **No main merge, no Mac deployment, no production SQLite mutation, no Gmail, no new tracked live persons, no changes to Frank production signal behavior.**

## Verified deliveries

- **A00 — baseline manifest RECORDED**: `meme/FRANK_CA_A00_CURRENT_MAIN_BASELINE_20261013.md`. Captures exact main, PR states, existing TWO registry formats, original hardcoded coupling and research/live boundary.
- **A01 — screenshot baseline RECORDED, red functional tests NOT_YET_RUN**: `meme/evidence/frank-ca-a01-screenshot-regression-fixtures-20261013.json`. Holds twelve problem IDs and responsible later TODO stages. All screenshot CA/price/cluster/holder figures are **user-visible historical reports only**, not new independent chain truth; old screenshot mint transcription needs original input/live mint validation.
- **A02 — research-only module IMPLEMENTED, INDEPENDENT_REVIEW_PENDING**: `local-agent/mission_agent/mission_control/person_registry.py`. Reads existing `config/frank_local_registry.json` schema v1 **without editing it**, accepts explicit future research bindings schema v2, one-person-many-wallets, two separate persons, optional non-overlapping historical wallet bindings by half-open slots, registry allowlist for research users. This module explicitly grants **no** signal/delivery/trading authority, even for Frank; frozen V1 controls its own authorized behavior separately.
- `tests/test_person_registry_research_v2.py`: 13 real regression tests, including v1 legacy file exact equality, multiple wallet scopes, disabled second person, no auto live rights, overlapping ownership assignment rejection, slot-bound lookup, unsupported chain rejection, no mutation to registry input.
- Workflow `.github/workflows/frank-ca-registry-a00-a02-20261013.yml` runs Python compileall, pyflakes, Node check and actual Git replay suite. **GitHub Actions run [38391776145](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38391776145)** at exact code+evidence commit `8b1b4d0682029b77a9c4114d03ba5afbb790e78c`: **SUCCESS**, **13 registry tests passed**, **1,440 complete local-agent tests passed**. Later report-only commit does not alter tested code.

## Boundaries and known gaps

1. **Not a live multi-person feature yet**: no runtime or route imports this new registry, `service.FrankReader(self.production_root)` and `wallet_watch.PERSON` remain unchanged. A03 must integrate the research-only interfaces without changing live Frank signal scope, after other-AI review.
2. **Wallet registration is not on-chain beneficial ownership proof**. `REGISTERED_UNVERIFIED` must not be shown as `CURRENT_CHAIN_BALANCE_VERIFIED`. A04/A05 still require historical signature and exact slot/ATA source evidence; no PnL.
3. **A01 is not completed acceptance testing**; existing main has the listed business bugs, but F/C red/green tests and real chain validation belong in implementation stages, not falsely marked done by copying screenshots.
4. No old Gmail safety research fix or new CA site/query/quote has been deployed. Prior PR31/32/33/35/39/41 merged; #28/#37/#38 remain unmerged as of A00 observation.
5. Any eventual second person is research-only unless a new user-approved production signal policy passes independent validation. Accepting a person wallet in a JSON registry does not authorize a new subscription/scan/LaunchAgent.
6. If main changes after this recorded baseline, rebase/compare in a fresh CI and re-review actual integration SHA. Do not use frozen A02 CI as release authority.

**Next engineering gate:** independent AI review at the exact draft PR head (including security and true time-range ownership). Then A03 read-only consumption and A04 economic event/data coverage, following design/TODO. Production trading remains NO_GO and release unauthorized.


## 2026-10-13 Claude independent review and remediation continuation

**Status: A02_REMEDIATION_IMPLEMENTED / EXACT_HEAD_CI_RECHECK_REQUIRED / SECOND_REVIEW_REQUIRED / NO_MERGE / NO_DEPLOY.** The earlier checkpoint above is historical evidence of the first implementation, not the latest acceptance result.

### Reviewer scope and independently reproduced findings

- Original A02 review target: PR #42 head `37db294926565069f506e7d61c2bcd0a2c879954`; review outcome `BLOCK`. Reviewer reported actual red tests and a separate **NOT_PUSHED** candidate patch; the reviewer patch commit IDs are not GitHub-verified and have not been represented as remote work.
- Independent source inspection reconfirmed width-only base58 validation, silent v2 start-at-zero assignment, non-binding-scoped IDs, permissive schema version typing, and disabled zero-wallet divergence. These affect account identity and ledger attribution.
- Source check corrected the review's CI-trigger claim: the **actual** PR workflow at `37db2949` triggers `push` on `dev/frank-ca-registry-a00-a02-20261013`; [run #38392055340](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38392055340) was itself a successful `push` event for that head. The asserted wrong branch trigger was not observed in the remote workflow.
- The three readers have different purposes and semantics. `signals/registry.py` is production gating, `meme/registry.py` is existing approved history/runtime mapping, and the new `PersonRegistry` is strictly research-only. One overlapping Frank address in these sources is **not** proof of on-chain beneficial control.

### Remediation made on the existing Draft PR branch

- Product fix `c7c54690c01e8d1e81055ef47a0d4715342ddbb2`: require base58-decoded 32-byte Solana pubkey; reject invalid v2 missing `valid_from_slot`; use binding-specific `wallet_id` for v2 while retaining v1 key; strict integer-only schema; permit genuinely disabled wallet-empty placeholder persons; add source/approval/funding/controller **reference metadata only**, which cannot grant delivery, signal, trade or ownership verification.
- Test fixture `38af418d9e913314ab957cd35466ae7f3a444fc1` explicitly supplies v2 `valid_from_slot`; old v1 data is still read unchanged.
- New independent regression test file at `2c5c6ea29f30623a42b5bfa52dbedca4bb8a144d`: invalid pubkey widths, exact schema types, historical reassignments, disabled placeholders, reference metadata guard, and **cross-loader identity-only** consistency on the existing Frank registry. Comparison intentionally does not equate production `verified` with research `REGISTERED_UNVERIFIED`.
- Workflow change `4d68fdb8c5cf8748c8d4ae16a580ef680d636250`: focused CI explicitly includes both the original A02 suite and review regressions on push. Exact final reviewed/CI SHA must be taken from GitHub after this documentation commit; earlier successes cannot be reused as final gate evidence.

### Residual gates and next product-critical execution

1. **A02 / E01 / E02:** Independent second review of the actual new SHA and exact-head CI. Still `NO_MERGE` until review closes all blocking identity-contract issues. Metadata references alone do not approve a wallet or validate balances.
2. **A03 then A04/A05:** Keep the present Frank V1 registry/Reader/Loop unchanged while exposing `PersonRegistry + WalletFactsProvider` to isolated read-only research endpoints; maintain source-slot binding references and raw ATA/mint/owner/finality evidence in a sidecar. An optional binding source is never an inventory/PnL proof. R-1 canonical ownership-authority and R-2 real approval/evidence validation remain open for A03/A05; do not solve by replacing the live loader with the research loader.
3. **F01/F02:** Once the research fact wiring is designed, deliver a truly filtered current follow-opportunity list and separately verified chain holdings with slot/source. The current main NO_BUY cards and unknown holdings remain unfixed by A02.
4. **C01/C02/C07/C08 in parallel:** Single-mode CA query progress; verified mint identity; sourced project narrative; removal of **general CA-only** default $30 quote, without touching Frank V1 policy or delivery. Other holder-depth work follows the existing C03–C10 gates.
5. **S01 separately:** Review historical PR33 residual delivery failure paths against the latest main and resolve only real defects in a separate safe PR.

This remains an **engineering checkpoint**, not real Mac ownership verification, operational deployment or user approval. Production SQLite, personal wallet balances, Gmail, LaunchAgents and frozen Frank V1 strategy were not changed by this PR.
