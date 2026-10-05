# Meme Module — Mandatory Reading Order

Updated: 2026-10-06

This directory is the entry point for Meme research/validation.

Before analyzing a new Meme CA, read and apply the following in order:

1. `../meme_trading_principles.md`
   - canonical Meme/token research principles;
   - token identity, authorities, supply, LP, holder normalization, dev/funder history, trading quality, entry/invalidation.

2. `WALLET_CLUSTER_ANALYSIS_SPEC.md` — **MANDATORY**
   - wallet-cluster reconstruction is part of the standard holder analysis, not an optional deep dive;
   - raw Top10/Top20 concentration is insufficient;
   - do not call holder structure clean/distributed/healthy before cluster adjustment;
   - public infrastructure/CEX false links must be excluded;
   - unresolved material clustering must be reported as `WALLET_CLUSTER_UNRESOLVED`.

3. `MEME_GPT_MONITOR_SPEC.md`
   - person/wallet signal pipeline, PERSON_PATTERN qualification, replay/followability and production boundaries.

## Required CA-analysis sequence

For every serious Meme/new-token CA review:

`canonical token identity`
→ `authority / Token-2022 risk`
→ `supply / burn`
→ `main pool / executable liquidity`
→ `Top20 token-account owner resolution`
→ `special-address normalization`
→ **`wallet cluster reconstruction`**
→ `cluster-adjusted concentration`
→ `dev / creator / funder history`
→ `real trade quality`
→ `narrative / product / KOL propagation`
→ `entry / invalidation / risk state`.

The wallet-cluster step must include, when data is available:

- direct token/quote transfers;
- common non-public funder;
- batch funding;
- common signer/control account;
- synchronized buys/sells;
- identical distinctive order size;
- common consolidation address;
- public router/fee-payer/CEX exclusions;
- confirmed-relation vs probable-control vs probable-execution separation.

## Required concentration output

At minimum report:

- `RAW_TOP10_PCT`;
- `EX_LP_TOP10_PCT`;
- `EX_SPECIAL_TOP10_PCT`;
- `LARGEST_CONFIRMED_RELATION_GROUP_PCT`;
- `LARGEST_PROBABLE_CONTROL_CLUSTER_PCT`;
- `LARGEST_PROBABLE_EXECUTION_CLUSTER_PCT`;
- `DEV_LINKED_CLUSTER_PCT`;
- `CLUSTER_ADJUSTED_TOP10_PCT`;
- `UNRESOLVED_MATERIAL_HOLDER_PCT`.

Use `UNAVAILABLE` / `UNRESOLVED` rather than filling missing values with estimates.

## Hard wording rule

Before wallet-cluster reconstruction is complete, do **not** conclude:

- holder structure is clean;
- holder distribution is healthy;
- Top10 is low therefore insider risk is low.

Use instead:

`raw holder concentration appears low, but wallet-cluster ownership/control remains unresolved`.

## Production boundary

These files govern analysis/research. They do not authorize new automations, production trading, live validation, or configuration changes.
