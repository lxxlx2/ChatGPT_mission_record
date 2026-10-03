# Meme PERSON_PATTERN Validation Status

Updated: 2026-10-03
Timezone: Asia/Bangkok

This directory stores research artifacts for candidate-person historical/replay validation before any PERSON_PATTERN production enablement.

Canonical monitor rules remain in `../MEME_GPT_MONITOR_SPEC.md`.

## Current candidates

| Candidate | Research state | PERSON_PATTERN | Validated patterns | Production change |
|---|---|---|---:|---|
| Frank | Existing accepted project source | project-established | existing project state | no change here |
| Ethermonk | Research pass imported | OBSERVE_ONLY | 0 | none |
| Point Farm | Separate research in progress; artifacts not yet imported | OBSERVE_ONLY | unknown | none |
| TheSolstice | Separate research in progress; artifacts not yet imported | OBSERVE_ONLY | unknown | none |

## Ethermonk current result

Directory: `ethermonk/`

Imported artifacts:

- `ethermonk-validation-summary.md`
- `ethermonk-episodes.csv`
- `ethermonk-patterns.json`
- `ethermonk-codex-handoff.md`

Research conclusion: KEEP `OBSERVE_ONLY`.

The main architectural finding is that PERSON_PATTERN validation cannot assume `person == one wallet`. Ethermonk research found a high-confidence holding wallet (`2xUb...`) and a materially related execution/source candidate (`58c8...`) with bidirectional cross-token flows. Direct SPL transfers between related wallets must not be silently classified as market BUY/SELL events.

Three important regression fixtures are preserved in the Ethermonk handoff:

1. CATE `58c8 -> 2xUb` must not become a `2xUb BUY`.
2. FONE `58c8 -> 2xUb` must not become a `2xUb BUY`.
3. STONK `2xUb -> 58c8` must not become a market `SELL`.

The current Ethermonk episode CSV is a targeted key-token reconstruction, not a completed six-month person-level episode ledger. Qualification remains blocked pending wallet-graph resolution, chain-complete history, delayed replay, robustness, TRAIN/VALIDATION/HOLDOUT and real FORWARD validation.

## Replay horizons

Canonical repo horizons remain:

- T+5m
- T+15m
- T+1h
- T+6h
- T+24h

Candidate research may additionally use T+1m and T+2m for higher-resolution followability analysis. These extra horizons do not replace canonical qualification requirements.

## Safety / production state

- production trading: `NO_GO`
- no new automation/task is authorized by these research artifacts
- no candidate is promoted by merely importing research files
- no wallet is added to a production registry by this import
- third-party PnL is non-canonical until independently reconstructed/replayed

## Import authorization note

The original Ethermonk research handoff states `git_commit_authorized: false` because that research conversation itself was told not to write Git. On 2026-10-03, the user explicitly authorized this separate conversation to sync the progress and required files into `lxxlx2/ChatGPT_mission_record`. This import does not grant standing authorization for future production/config/task changes.
