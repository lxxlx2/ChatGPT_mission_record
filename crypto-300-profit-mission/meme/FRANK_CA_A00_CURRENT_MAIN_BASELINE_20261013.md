# Frank / CA A00 — 2026-10-13 code and authority baseline

Status: BASELINE_RECORDED / MAC_RUNTIME_NOT_NEWLY_READ / SECURITY_FIX_NOT_DEPLOYED_BY_THIS_WORK

## Fixed identity and authority

- Observed public main: `17a71c863b44c67f7a1a47639fd482958e56ee4b`. This is a code snapshot, **not** a live Mac fingerprint.
- Source of constraints: `crypto-300-profit-mission/MISSION_SPEC.md`; `crypto-300-profit-mission/meme/FRANK_CA_MULTI_PERSON_TECHNICAL_DESIGN_20261013.md`; `crypto-300-profit-mission/meme/FRANK_CA_MULTI_PERSON_IMPLEMENTATION_TODO_20261013.md`.
- Approved live scope: **Frank only**, frozen deterministic V1, read-only new research, manual trading only and `PRODUCTION_TRADING=NO_GO`. Existing Loop and Gmail must remain unchanged.
- `config/frank_local_registry.json`: schema 1, one Frank person and one Solana PRIMARY wallet, `enabled:true`. This is a config assertion, **not** independent chain proof of wallet ownership or current balance.
- `config/meme_person_registry.json`: separate historical `mission_agent/meme/registry.py` registry. Do not conflate with `mission_agent/signals/registry.py` or silently migrate approval.
- `mission_agent/signals/registry.py::load` explicitly allows one enabled Frank person; `mission_control/frank.py::FrankReader` accepts a person_id but defaults Frank, `mission_control/service.py` instantiates `FrankReader(self.production_root)`, and `wallet_watch.py` has `PERSON = "frank"`. These are known A03 integration coupling points, **not fixed by the A02 research interface**.

## Relevant PR state confirmed 2026-10-13

| PR | Title/scope | GitHub status | Decision for this work |
| --- | --- | --- | --- |
| #28 | CA 429 and research report | open, unmerged | Compare source semantics; do not blindly cherry-pick |
| #30 | Monster V4 | open, unmerged | **Out of Frank/CA scope** |
| #31 | Frank V2 ATA | merged | Keep its historical evidence and read-only contracts |
| #32 | Gmail OAuth | merged | Not part of this research-only change |
| #33 | review breakdown | merged (old code) | New H-5/H-6/M-8–M-13 research fixes still require main-diff review |
| #35 | follow opportunities first | merged | Layout is implemented; signal-only filtering is not |
| #37 | future Gmail copy | open, unmerged | Compare against latest PR39, no auto-merge |
| #38 | collapse watch pool | open, unmerged | Compare against current watchlist, no auto-merge |
| #39 | historical MULTIPLE payment text | merged | Does not prove live current chain inventory |
| #41 | controlled Mac recovery | merged | Preserve protected Loop/backup/restart gates |

At this snapshot `server.py` CA query presets `CLUSTER_PRESETS` still exist; `meme/cluster.py` bounds deep research to 20 owners/100 history/50 funding signatures; general CA issues an implicit `execution_quote_30_usdc`; `app.js` includes unfinished X/FOMO narrative and displays non-CLOSED `NO_BUY` candidates at first priority.

## Technical research scopes and artifacts for next stages

- A01 source is the user's screenshots, recorded in `meme/evidence/frank-ca-a01-screenshot-regression-fixtures-20261013.json`. That file does not claim exact live wallet balances or verified chain slots.
- A02 implemented in research-only `local-agent/mission_agent/mission_control/person_registry.py`, with `tests/test_person_registry_research_v2.py`. No existing Frank V1 service/controller imports this module yet; until A03, research-only interfaces are **not** production-installed.
- A03 must remove `wallet_watch.PERSON` / `service.FrankReader()` implicit single-person coupling **without enlarging live authority**. Preserve legacy Frank default for existing live entrypoint, and inject registry only into new read-only v2 research interfaces.
- A04/A05 need new slot-pinned Mac evidence and historical event payloads before claiming verified inventory/PnL. No public Git raw copy of production SQLite.
- Existing CA acceptance spec `meme/ca-analysis-unified-accuracy-acceptance.md` is **requirements only**, not evidence that the 12 screenshot issues are fixed.

## Scope and approval checkpoint

This A00/A01/A02 branch must not alter existing config, signal engine, delivery, Gmail, server HTTP, frontend, production SQLite, Mac release scripts or LaunchAgents. Merge/release remains blocked pending independent review of final code and explicit user authorization for Mac operations. The CI result must be recorded with its **exact commit SHA**, not inferred from the existence of a workflow file.
