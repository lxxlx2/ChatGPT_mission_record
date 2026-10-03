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
| TheSolstice | Research pass imported | OBSERVE_ONLY | 0 | none |

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

## TheSolstice current result

Directory: `thesolstice/`

Imported artifacts:

- `thesolstice-validation-summary.md`
- `thesolstice-episodes.csv`
- `thesolstice-patterns.json`
- `thesolstice-codex-handoff.md`

Research conclusion: KEEP `OBSERVE_ONLY`.

High-confidence Solana wallet candidate:

`4ugDhHJ8XDXAeABmrNmGffFaLbJb9BkPyiFGVSV9ocwo`

Identity remains high confidence rather than cryptographically first-party confirmed.

Key research result:

- STONK is an exceptional positive accumulation case, but the current Pump platform display attributes about 97.14% of displayed profit to STONK. This percentage is research context only, not canonical chain-recomputed PnL.
- MARKET is the decisive false-positive regression case: Fomp shows 22 tracked buys and 0 sells in the observed window, yet the later Pump snapshot marks the position around -95.1%.
- Therefore repeated adds, position growth and no major sell cannot by themselves qualify a PERSON_PATTERN.
- EYE (3 buys / 4 sells) and PUMPRPG (1 buy / 1 sell) do not reproduce the STONK pyramid structure.
- The public detailed trade feed is capped/incomplete, so exact executable delayed replay has not been completed.

Required regression fixture:

`market_repeated_adds_must_not_auto_pass`

A model using only repeated buys / position growth / no-major-sell must fail this fixture.

The TheSolstice CSV currently contains a small research-grade set of key episodes and controls, not a complete six-month raw episode ledger. `thesolstice-patterns.json` remains `NO_VALIDATED_PATTERN`.

## Cross-candidate architectural requirements discovered so far

Codex should treat these as shared validation-pipeline requirements rather than person-specific exceptions:

1. `person_id` may map to multiple wallets; build a wallet graph before person-level PnL or episode reconstruction.
2. Direct token transfers and platform fee-payer/co-signer activity must not be silently classified as market BUY/SELL.
3. Symbol is display-only; mint/CA is canonical token identity.
4. Missing historical price, liquidity or ownership evidence must fail closed rather than be silently imputed.
5. Open episodes must keep realized and unrealized PnL separate.
6. Threshold discovery must not use visible winners and then claim validation; preserve TRAIN / VALIDATION / HOLDOUT separation.
7. Robustness must include dynamic Ex-Top1 / Ex-Top3 and material-token/theme exclusions where data permits.
8. Person-specific accumulation heuristics require explicit negative controls; TheSolstice MARKET is one such regression fixture.

## Replay horizons

Canonical repo horizons remain:

- T+5m
- T+15m
- T+1h
- T+6h
- T+24h

Candidate research may additionally use T+1m and T+2m for higher-resolution followability analysis. These extra horizons do not replace canonical qualification requirements.

The TheSolstice source research handoff focuses on +1m/+2m/+5m/+15m because that was the candidate-specific research request. When Codex implements the shared pipeline, the canonical 1h/6h/24h horizons must still be supported under the current Meme spec.

## Safety / production state

- production trading: `NO_GO`
- no new automation/task is authorized by these research artifacts
- no candidate is promoted by merely importing research files
- no wallet is added to a production registry by this import
- third-party PnL is non-canonical until independently reconstructed/replayed
- importing research artifacts is not authorization to enable live validation or send trade alerts

## Import authorization note

The original Ethermonk and TheSolstice research handoffs state `git_commit_authorized: false` / `commit_or_push_this_research: false` because those research conversations themselves were told not to write Git. On 2026-10-03, the user explicitly authorized this separate conversation to sync research progress and required files into `lxxlx2/ChatGPT_mission_record` so Codex can consume them later.

This import authorization is limited to research/status artifacts. It does not grant standing authorization for future production/config/task/monitor changes.
