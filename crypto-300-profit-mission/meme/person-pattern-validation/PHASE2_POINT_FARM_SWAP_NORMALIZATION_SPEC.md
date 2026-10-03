# Phase 2 — Point Farm swap normalization / episode reconstruction

Date: 2026-10-03
Scope: Meme / PERSON_PATTERN offline research only
Primary subject: Point Farm Capital (`point-farm`)
Production trading: `NO_GO`
PERSON_PATTERN: `OBSERVE_ONLY`

## Goal

Move the first-run pipeline from `raw finalized transactions -> UNKNOWN` to an auditable Point Farm path:

`raw finalized chain history -> decoded user-intent swap -> reconciled person inventory -> structural episode -> economic enrichment -> executable replay`

Do not tune or qualify a trading pattern in this phase. The immediate gate is trustworthy swap / episode reconstruction.

## Why Phase 2 is necessary

The first-run implementation correctly fails closed: raw token balance deltas are not classified as market trades unless a lossless adapter supplies `verified_swap`, route evidence, quote/token deltas and account evidence. As a result, the first run collected real chain data but produced 0 valid episodes and 0 executable replay samples.

Simply downloading more ordinary RPC transactions is not sufficient. Without route / swap semantics, a larger cache mainly creates more `UNKNOWN` events.

There is also an implementation distinction that must be made explicit:

- **structural certainty**: whether BUY/SELL direction, token quantity, person attribution and episode boundaries are known;
- **economic certainty**: whether historical USD notional, cost basis, executable price, fees, liquidity and slippage are known.

Missing USD economics must not silently convert a structurally verified swap back into an unknown transfer. Conversely, a structurally reconstructed episode must not become qualification-grade until economic reconciliation is also complete.

## Preferred decoded-history provider

Preferred Phase 2 semantic source: **Helius Parsed Events API**, while finalized raw chain data remains the audit source of truth.

As of 2026-09, Helius documents Parsed Events as the successor to Enhanced Transactions. It can decode address history / transaction signatures using an IDL catalog covering thousands of Solana programs and preserves token/SOL transfers plus raw fallback for unsupported programs.

The adapter must require `HELIUS_API_KEY` from the environment. Never commit a key or authenticated URL.

Provider roles:

1. raw finalized RPC / archive RPC: canonical transaction identity, signature, slot, block time, raw accounts, balances;
2. Helius Parsed Events: decoded instruction/account roles and swap semantics;
3. optional historical market/quote provider: USD economics and executable replay;
4. existing research fixtures: regression controls only, never canonical chain truth.

If Helius Parsed Events is unavailable, return an explicit credential/data blocker. Do not relabel raw balance deltas as swaps to keep the pipeline moving.

## Reconciliation rules

A parsed provider event can become a verified market swap only when it reconciles to cached finalized raw chain evidence.

At minimum verify:

- same signature;
- same slot when provider supplies slot;
- same block time when provider supplies timestamp;
- accepted Point Farm wallet is the user / transfer authority for the decoded swap;
- canonical input/output mints are present;
- input/output quantities are present;
- referenced token accounts / named accounts are consistent with raw transaction accounts when the provider exposes them;
- transaction did not fail;
- route/program evidence is retained;
- duplicate CPI/pool legs do not create duplicate user-intent trades.

If any material reconciliation fails, keep `UNKNOWN` or `UNRESOLVED`; never downgrade evidence requirements.

## Swap verification vs economic verification

Introduce separate state rather than using one `known` flag for both inventory and USD accounting.

Recommended event fields:

```text
swap_verified: bool
economics_verified: bool
quote_mint
quote_delta
quote_amount
usd_notional
usd_price_evidence
route_id
route_evidence
semantic_provider
semantic_provider_version
raw_signature_reconciled
```

A swap may be structurally verified while `economics_verified=false`.

Example: Point Farm swaps SOL for token X and the decoded input/output quantities and authority are fully verified, but exact historical SOL/USD execution value has not yet been sourced. That event may contribute to token quantity / buy-count / timing episode structure, but must not contribute a fabricated USD cost basis.

## Episode reconstruction states

Separate at least:

```text
PARTIAL_HISTORY
STRUCTURALLY_RECONSTRUCTED
ECONOMICS_INCOMPLETE
FULLY_RECONSTRUCTED
QUALIFICATION_BLOCKED
```

`STRUCTURALLY_RECONSTRUCTED` means the relevant market BUY/SELL sequence and token inventory path can be reconstructed from complete accepted scope without unresolved external flows.

`FULLY_RECONSTRUCTED` additionally requires historical economics sufficient for realized/remaining cost accounting and the existing inventory reconciliation gate.

Only `FULLY_RECONSTRUCTED` episodes count toward PERSON_PATTERN qualification and the canonical >=30 episode minimum.

Structural episodes may be used to test parser/segmentation behavior and to measure buy/add timing, but not to claim profitable alpha.

## Point Farm scope

Primary accepted research wallet:

`Beqv6dzTcjV2eodo8RRXCiCcnSYrS1vkQKhfqwHXqeit`

Unresolved attribution:

`6cerGp…615t`

Do not merge the unresolved address.

Start with Point Farm only until one real end-to-end path works. Do not spend API quota backfilling Ethermonk and TheSolstice before Point Farm has produced audited structural episodes.

## History completeness

For Point Farm, wallet-reference pagination alone is not enough to assert chain-complete history.

Implement / use an address-history method that includes the wallet's token-account activity where supported. Helius documents `getTransactionsForAddress` with token-account coverage and Parsed Events address history for decoded history. Provider-specific semantics must be tested rather than assumed.

Track separately:

```text
wallet_address_history_complete
token_account_history_complete
semantic_decode_complete
inventory_reconciliation_complete
economic_history_complete
```

Do not collapse these into one `history_complete` boolean in reporting.

## First Phase 2 acceptance target

Do not require 30 episodes just to declare Phase 2 engineering success.

Phase 2 engineering PASS requires all of the following on real Point Farm history:

1. at least one decoded Point Farm market swap reconciled against finalized raw chain transaction evidence;
2. BUY/SELL direction derived from decoded user intent / input-output assets, not a raw balance sign heuristic;
3. no internal/external token transfer regression is misclassified as a swap;
4. at least one real multi-trade token sequence groups into a structural episode;
5. source signatures and route evidence are preserved;
6. economics missingness stays explicit instead of fabricated;
7. restart/checkpoint is idempotent;
8. existing negative fixtures remain passing;
9. no production/live mutation.

After this passes, continue Point Farm history until >=30 `FULLY_RECONSTRUCTED` episodes or a documented data/economic blocker is reached.

## Mandatory regressions

Retain all first-run tests and add at least:

```text
parsed_swap_requires_raw_signature_match
parsed_swap_requires_accepted_user_authority
parsed_swap_input_output_direction
parsed_swap_duplicate_inner_legs_one_user_trade
parsed_transfer_never_becomes_swap
structural_episode_can_exist_without_usd_economics
structural_episode_not_qualification_grade
usd_missing_does_not_corrupt_token_inventory
pointfarm_purr_accumulation_failure
pointfarm_ubi_accumulation_failure
pointfarm_toerogan_no_sell_failure
```

The existing Ethermonk internal-transfer fixtures and TheSolstice MARKET false-positive fixture must continue to pass.

## Helius migration / beta safety

Parsed Events is a beta API and its response schema may evolve.

Therefore:

- isolate provider-specific parsing in its own adapter;
- save a sanitized schema/version manifest with research output;
- never spread Helius field names through core episode logic;
- fixture-test representative decoded Jupiter / Pump / Raydium-style swaps before trusting them;
- unsupported / changed payloads fail closed;
- do not fall back from a parsing error to balance-delta BUY/SELL inference.

Enhanced Transactions may be used only as an explicitly documented fallback if Parsed Events cannot support a required historical case; do not mix provider interpretations silently.

## Economic enrichment is a separate gate

Phase 2 swap semantics do not authorize approximate replay.

Historical USD / execution layer must later provide auditable evidence for:

- quote asset historical price where needed;
- pool / route executable quote at T_signal + delay;
- fees;
- price impact;
- slippage;
- liquidity;
- MFE / MAE path coverage.

Stablecoin quote assets can only be treated as USD-equivalent under a declared/preregistered policy with depeg handling. Native SOL quote amounts require historical SOL/USD evidence.

No candle-close substitution for executable replay.

## Reporting

Add a Phase 2 Point Farm report containing at least:

```text
raw_transactions
parsed_transactions
verified_market_swaps
unknown_transactions
reconciliation_failures
unique_mints
structural_episodes
fully_reconstructed_episodes
history coverage dimensions
semantic provider
provider schema/version
credential/data blockers
```

Show several inspectable real swap rows with signature, timestamp, input mint/amount, output mint/amount, route/program and reconciliation state.

## Branch / safety

Continue on `codex/offline-person-validation` unless a new research branch is explicitly needed.

Allowed:

- offline research code;
- tests;
- provider adapters;
- ignored local caches;
- compact sanitized reports/fixtures.

Forbidden:

- production PERSON_PATTERN enablement;
- automation/task creation;
- live validation;
- Gmail changes;
- production wallet registry edits;
- trading/wallet mutation;
- secrets in Git.

Final states remain:

```text
Point Farm PERSON_PATTERN = OBSERVE_ONLY
validated_pattern_count = 0
production trading = NO_GO
```

until later gates independently pass.
