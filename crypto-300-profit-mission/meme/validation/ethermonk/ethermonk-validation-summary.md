# Ethermonk PERSON_PATTERN Historical Validation

**Mission:** `$300 → $3000 Mission`  
**Candidate:** Ethermonk (`@ether_monk`)  
**Research date:** 2026-10-03 (Asia/Bangkok)  
**Production trading:** `NO_GO`  
**Current candidate state:** `PERSON_PATTERN = OBSERVE_ONLY`  
**Research conclusion:** **KEEP `OBSERVE_ONLY`**

## Executive conclusion

Ethermonk does **not** currently pass PERSON_PATTERN qualification.

The blocker is evidence quality and replay validity, not the size of third-party reported PnL.

1. Public Ethermonk ↔ Solana holding wallet `2xUbYAVq1oJGj45d6JjnaYHAke3NQecUcqWvvVbwmYw8` is **high confidence but not first-party confirmed**.
2. Address continuity is **not proven**. Third-party profile history reaches back to 2026-02-14, but that cannot be substituted for raw person-level wallet history.
3. Multi-wallet execution is **confirmed to exist**. A second wallet, `58c8h7YHd4DW25RBroRHC3D9wyLq8xKuaC7q4K5PNbSr`, has repeated bidirectional cross-token interaction with `2xUb`.
4. Because of that wallet relationship, a balance increase/decrease on `2xUb` cannot safely be treated as a BUY/SELL.
5. Six-month wallet-graph-complete history was not recovered in this research pass.
6. Chain-complete realized PnL, Ex-Top1/Ex-Top3 robustness and delayed replay were not completed.
7. No PERSON_PATTERN is validated. A possible accumulation/conviction pattern remains only a research hypothesis.

Final research state:

```text
Ethermonk
PERSON_PATTERN = OBSERVE_ONLY
validated patterns = 0
qualification = NOT PASSED
production changes = NONE
```

## Repository rule baseline

Canonical file reviewed:

- `crypto-300-profit-mission/meme/MEME_GPT_MONITOR_SPEC.md`
- updated 2026-10-03

Applied requirements:

- new candidates default to `OBSERVE_ONLY` for PERSON_PATTERN;
- PERSON_PATTERN requires accepted historical/replay validation;
- use user-followable delayed entry, not tracked-wallet theoretical entry;
- canonical replay horizons: T+5m, T+15m, T+1h, T+6h, T+24h;
- MFE/MAE and executable liquidity are required;
- TRAIN / VALIDATION / HOLDOUT / real FORWARD separation is required;
- production trading remains `NO_GO`.

This research additionally uses T+1m and T+2m as high-resolution research horizons. They do not replace canonical qualification horizons.

## Identity / wallet map

| Item | Value | Evidence grade | Notes |
|---|---|---|---|
| Public profile | `@ether_monk` | confirmed public profile | no wallet signature attestation found |
| Primary Solana holding wallet | `2xUbYAVq1oJGj45d6JjnaYHAke3NQecUcqWvvVbwmYw8` | high confidence, not first-party confirmed | multiple public mappings + matching on-chain positions |
| Related execution/source candidate | `58c8h7YHd4DW25RBroRHC3D9wyLq8xKuaC7q4K5PNbSr` | high relationship confidence, ownership unresolved | bidirectional cross-token flows |
| FOMO co-signer / fee payer | `AgmLJBMDCqWynYnQiPCuj9ewsNNsBJXyzoUhD9LJzN51` | platform infrastructure | must not be clustered as Ethermonk merely because it signs/pays gas |
| Alternative profile-level address | `Gt6MM3…pRqd` | unresolved | full address / role not resolved |
| EVM/Robinhood-chain wallet | `0x2408ce75d217e3a70d6ca370c78c1b34d706f5a0` | high confidence third-party mapping | outside this Solana validation scope |
| Previous Solana wallets | unknown | unresolved | migration chain not established |
| Original funding source | unknown | unresolved | fee sponsorship prevents naive fee-payer inference |

## Critical wallet-graph evidence

### CATE transfer into `2xUb`

- tx: `a8LVK2BKdwwa9US2Q3Sd4Jsq2NkHUZpMaXYzX1v4oo88dCwWWXbNjicjoUGK3q8UdLZkf2tQG1Ld3Yb2v8qMPS1`
- time: 2026-08-11 16:21:58 UTC
- signer/source: `58c8...PNbSr`
- destination owner: `2xUb...mYw8`
- amount: `2,840,053.288293 CATE`
- classification: related/internal transfer candidate; **not a verified `2xUb` market buy**.

### FONE transfer into `2xUb`

- tx: `5TikrUgW9orCCMvwFWZ1bLtvfpr7RfWqV4Y3MzZ4htmq4DUqvcM7uhkVH7WYwPKYoMH33RVWWeG4MQBrDMzzmdz`
- time: 2026-09-02 04:24:15 UTC
- signer/source: `58c8...PNbSr`
- destination owner: `2xUb...mYw8`
- amount: `9,824,921.440752 FONE`
- classification: related/internal transfer candidate; **not a verified `2xUb` market buy**.

### STONK transfer out of `2xUb`

- tx: `59Wdr1ZAMkdEFFJKvzUw8TrYRQkK38iRfqgNFhqhnJRWCVW4R5hb23zNkhQ2giCjpKDxGHXYnrXWX96yVqJ4YVin`
- time: 2026-09-05 05:27:37 UTC
- signer: `2xUb...mYw8`
- destination owner: `58c8...PNbSr`
- amount: `15,452,352.182300252 STONK`
- direct SPL transfer, not a DEX sale;
- downstream DEX use by `58c8` was observed.

These three transactions must become regression fixtures for the eventual person-level validation pipeline.

## Historical coverage achieved

Targeted raw token-account coverage was reconstructed for five key positions:

| Token | CA | First confirmed observed `2xUb` activity | Current/observed state | Main finding |
|---|---|---|---|---|
| STONK | `6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx` | 2026-08-12 | residual balance | 15.452M later transferred to `58c8` |
| CATE | `Ai66LHZG9MCzg1WKdawwqduVAXpNDUuV8M3uyq5ppump` | 2026-08-11 | current `2xUb` ATA = 0 | first observed balance came from `58c8` transfer |
| FONE | `CTPoyCwkjMvoJwU4xvZZqoD8tiYk6yDchySiN5gGpump` | 2026-09-02 | still held in observed state | first observed balance came from `58c8` transfer |
| MINI | `Ax5dAamJPeuaLpFUzs9FdcpoUhHDcxyjPzxCJQidjups` | 2026-09-06 | still held in observed state | first observed route used `2xUb`-authority USDC input |
| CTO | `8K5X85PAJHAAVSvYaAzgVPPAPsqqHmvx16ZyBiscYF8L` | 2026-09-04 | current `2xUb` ATA = 0 | first observed route used `2xUb`-authority USDC input |

The accompanying `ethermonk-episodes.csv` is therefore a **targeted key-token reconstruction**, not a completed six-month person-level episode ledger.

Observed ATA signature counts must not be interpreted as trade counts.

## Robustness / PnL status

Formal Mission robustness is currently unavailable because a wallet-graph-complete, chain-reconciled episode ledger does not yet exist.

Do **not** use third-party PnL as canonical performance.

One third-party page showed internally inconsistent 30-day totals, but both versions suggested very high concentration in STONK. That is only a sensitivity warning explaining why Ex-Top1 / Ex-Top3 / Ex-STONK testing is mandatory; it is not qualification data.

Formal required robustness once the ledger exists:

- All episodes
- Ex-Top1
- Ex-Top3
- Ex-largest token/theme
- Ex-STONK if material

## PERSON_PATTERN status

Validated patterns:

```json
{
  "status": "NO_VALIDATED_PATTERN",
  "patterns": []
}
```

Research-only hypothesis:

`EM_ACCUMULATION_CONVICTION_TRANSITION_V0`

Possible structure:

```text
first market exposure
→ repeated exposure increase
→ position expansion
→ conviction transition
→ observable signal candidate
```

This is **not validated** because:

- wallet graph is unresolved;
- transfers into the holding wallet can masquerade as buys;
- chain-complete cost basis and exits are missing;
- causal T0 cannot be defined consistently for all episodes;
- delayed replay is incomplete;
- TRAIN/VALIDATION/HOLDOUT/forward proof is missing;
- extreme-winner concentration may be material.

No numeric trigger threshold should be selected from visible winners.

## Codex requirements derived from this research

Codex should implement the following order:

```text
wallet graph
↓
platform address exclusion
↓
DEX swap / internal-transfer classification
↓
person-level episode reconstruction
↓
causal observable T0
↓
delayed replay
↓
robustness exclusions
↓
TRAIN
↓
VALIDATION
↓
HOLDOUT
↓
real FORWARD
↓
qualification decision
```

Required replay horizons for the combined research pipeline:

- 1m
- 2m
- 5m
- 15m
- 1h
- 6h
- 24h

The 5m/15m/1h/6h/24h horizons are canonical repo requirements; 1m/2m are additional research resolution.

## Production restrictions

This research does not authorize:

- `SIGNAL_ENABLED`;
- task/automation creation;
- `$300-3000` task modification;
- production Gmail alerts for Ethermonk;
- production registry wallet addition;
- wallet/trading actions;
- silent merging of `58c8` and `2xUb`;
- use of profile lifetime stats as current-wallet lifetime history;
- use of third-party PnL as canonical truth.

## Import note

The research conversation was originally instructed not to commit/push Git. The user later explicitly authorized a separate conversation on 2026-10-03 to sync this progress and required artifacts into the Mission repository. This import is documentation/data synchronization only and does not authorize production changes.

## Evidence transaction IDs

- CATE source transfer: `a8LVK2BKdwwa9US2Q3Sd4Jsq2NkHUZpMaXYzX1v4oo88dCwWWXbNjicjoUGK3q8UdLZkf2tQG1Ld3Yb2v8qMPS1`
- FONE source transfer: `5TikrUgW9orCCMvwFWZ1bLtvfpr7RfWqV4Y3MzZ4htmq4DUqvcM7uhkVH7WYwPKYoMH33RVWWeG4MQBrDMzzmdz`
- STONK transfer-out: `59Wdr1ZAMkdEFFJKvzUw8TrYRQkK38iRfqgNFhqhnJRWCVW4R5hb23zNkhQ2giCjpKDxGHXYnrXWX96yVqJ4YVin`
- downstream STONK DEX sample on `58c8`: `5n7rZaua69XMYp8NaNYvTL4B768izT2fxF6uLTwSqLViy9NWcMoep9bKDCnCAJ4bvHztVeBVssczrK47gfdiJyBg`
- MINI route sample: `MvgBJvSkiqofTGrXu4npg2hgkFTFPNsNApKdAsEpNwrzn1LTAHxR8iPe3PJ1XqeJatVoo8XrWf9iVK9cZZEDYR7`
- CTO route sample: `4C5uG3RArWgQDXxR6CGETKardTbwmierr2EFRLak2yBTZxJmsMRyCgYiDGBDg9FXnjDEc1NPX5jokmxNn6haGiM`
