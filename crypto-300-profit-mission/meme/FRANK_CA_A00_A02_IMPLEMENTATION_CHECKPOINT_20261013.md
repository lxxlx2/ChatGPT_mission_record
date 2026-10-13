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
