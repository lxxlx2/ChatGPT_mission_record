# Frank SOL/USDC normalization + Mission Meme follow review

Status: `CODE_ONLY / REVIEW_ONLY / NOT_AUTHORIZED_LIVE`

Branch: `codex/frank-sol-usd-normalization-review`

Production trading: `NO_GO`

## Why this exists

Frank V1 records SOL/WSOL active trades and inventory chronology, but its frozen amount predicates are numeric only for direct USDC quotes. A SOL quote therefore remains `UNDETERMINED` for the existing USD-equivalent gates even when the trade itself is valid.

This review candidate normalizes SOL to an auditable event-time **SOL/USDC** reference and replays the original frozen Frank V1 model unchanged.

## Safety architecture

Production `classifier.py`, `evaluator.py`, `engine.py`, `scanner.py`, frozen policy and delivery authority remain unchanged.

```text
source forward.sqlite [READ ONLY]
  -> existing ACTIVE_TRADE classification
  -> SOL/WSOL quote only:
       Binance official public SOLUSDC 1m history
       immediately previous fully closed candle close
       durable candle evidence
  -> attach transaction-specific block time to the use of that candle
  -> shadow-only synthetic USDC-equivalent quote
       preserve original SOL raw quote in original_quote
  -> original frozen Frank V1 Engine/evaluator, dry_run=True
  -> separate replay DB + report
```

No current SOL price is substituted for a historical Frank trade.

## Historical reference evidence

Default source: `BINANCE_OFFICIAL_SPOT_SOLUSDC`.

Selection rule: `PREVIOUS_CLOSED_1M_CLOSE`.

For a Frank trade at epoch `T`, normalization uses the close of the immediately previous fully closed UTC 1-minute SOLUSDC candle.

A durable candle reference contains only candle/source evidence:

- source, symbol, interval and selection rule;
- `reference_epoch`;
- candle open/close timestamps;
- OHLC;
- selected SOL/USDC close;
- evidence SHA256.

It deliberately does **not** contain a Frank transaction `block_time`. Each normalized trade wraps the shared candle reference with its own `trade_block_time`, so two Frank trades in the same minute may share one evidence hash without inheriting each other's transaction timestamp.

### Cache, retry and access-block policy

Only these results are durable-cacheable:

- `VERIFIED` exact candle;
- deterministic `BINANCE_KLINE_NOT_FOUND`.

Transient failures such as HTTP 429, 5xx, timeout, network failure or malformed/transient response are retried with bounded backoff and are **not persisted** in `sol_usdc_references`.

Non-retryable access-denial responses `403 / 418 / 451` are treated as a likely environment/region access problem. Three consecutive SOL-reference failures with one of these reasons abort the replay instead of continuing to request every Frank trade.

The replay target always stores every durable reference it actually uses. An optional separate `--reference-cache` SQLite file can be reused across fresh replay targets so verified minute candles do not have to be downloaded again.

Input/normalization failures are reported separately from reference failures. Examples:

- `QUOTE_DECIMALS_MISSING`;
- `QUOTE_AMOUNT_MISSING`;
- `NORMALIZATION_FAILED_WITH_VERIFIED_REFERENCE`.

These must not be mislabeled as Binance reference failures.

## Shadow conversion

Example:

```text
Frank actually paid:
  2.5 SOL

shared historical evidence:
  SOL/USDC = 100

shadow evaluator representation:
  quote_asset = USDC
  quote_quantity = 250
  quote_normalization = SOL_TO_USDC_SHADOW_EQUIVALENT

preserved audit field:
  original_quote = 2.5 SOL
```

The synthetic representation exists only so the already-frozen V1 evaluator can consume the verified equivalent without code changes.

## Strict replay acceptance gate

`scripts/frank_sol_usd_shadow_replay.py` reads source `forward.sqlite` with `mode=ro + query_only` and writes a separate target DB.

The signal regression comparison is deliberately strict. It does **not** exclude a mint merely because that mint also contains SOL transactions.

Signal identity includes:

- person;
- mint;
- episode;
- signal type;
- stage;
- triggering signature.

A replay is **not** considered validated merely because no old source signal disappeared. SOL normalization must actually have been exercised and resolved.

Hard code-level replay gate:

```text
source_signal_regression_pass == true
missing_source_signals == []
sol_trades > 0
sol_unresolved == 0
sol_resolution_gate_pass == true
shadow_replay_gate_pass == true
```

This prevents the empty-pass failure mode where Binance is inaccessible, every SOL trade remains unresolved, the shadow output equals source output, and regression comparison alone would incorrectly look green.

`BINANCE_KLINE_NOT_FOUND`, missing block time, missing quote decimals/amount, HTTP access denial, timeout or any other unresolved SOL trade keeps `shadow_replay_gate_pass = false` until explicitly resolved or separately redesigned and re-reviewed.

Every added SOL signal must be manually traceable:

```text
transaction
-> original SOL quote
-> transaction block_time
-> shared Binance SOLUSDC candle
-> USDC equivalent
-> frozen V1 predicates
-> recovered signal
```

## Mission Control transient failure debounce

Review policy uses:

```text
transient_wait_grace_seconds = 60
transient_wait_reset_gap_seconds = 300
```

Only an existing `BUY / SMALL_BUY -> transient WAIT` is delayed. During grace:

- `candidate_latest` updates immediately;
- no immutable WAIT event is created;
- no Gmail/local invalidation notification is sent.

Recovery before 60 seconds clears the pending transition silently.

The downtime reset threshold is deliberately independent from the grace period. A slow candidate cycle lasting more than 60 seconds must not continuously restart the timer. Only an observation gap longer than 300 seconds restarts debounce evidence.

Non-transient `NO_BUY`, SELL/EXIT and structural invalidations remain immediate.

## Forward threshold evidence

Review mode records at most one `follow_observations` row per candidate per 60-second bucket and keeps 14 days by default.

`scripts/mission_meme_threshold_replay.py` explores the fixed candidate grid only; it never writes policy and never selects an automatic winner.

Default minimum sample count is **30**. The report explicitly warns about multiple-testing/overfitting risk.

Return basis is:

`BUY_SIDE_EXECUTABLE_QUOTE_MARK_TO_MARK_EXCLUDES_SELL_SLIPPAGE_AND_FEES`

Therefore it is not realized PnL.

At 15m/60m missing executable prices are retained and classified. `NO_ROUTE` is the only censored state used for a `-100%` route-failure stress bound. `PRICE_UNAVAILABLE` and `NO_OBSERVATION` remain unknown censoring and are **not** converted into losses, because service downtime is not evidence that the token lost 100%.

Reports include:

- observed outcome count;
- total censored count;
- no-route count;
- price-unavailable count;
- no-observation count;
- unknown-censored count;
- observed return statistics;
- route-failure lower-bound statistics with `NO_ROUTE = -100%` only.

Historical Jupiter executable impact does not exist in the old durable DB and must not be invented. Historical reconstruction and new forward OOS evidence remain separate.

## Real Jupiter fixtures

`scripts/capture_jupiter_quote_fixtures.py` performs read-only `/swap/v1/quote` GET requests only.

Before any network request it preflights every requested output path and the manifest. USDC request amounts use `Decimal`, not float, and reject precision beyond six USDC decimals.

Before approval capture at least:

1. liquid token;
2. thin-liquidity token;
3. no-route mint.

Verify `priceImpactPct`, route/no-route behavior and current real error shape against immutable fixtures.

## Dashboard/API quote semantics

Public/legacy candidate fields now describe Frank's **original payment evidence**:

- `latest_buy_quote_asset`;
- `latest_buy_quote_quantity`;
- `latest_buy_original_quote_asset`;
- `latest_buy_original_quote_quantity`.

If a shadow trade was normalized, synthetic evaluator fields are exposed only under explicit names:

- `latest_buy_model_quote_asset`;
- `latest_buy_model_quote_quantity`;
- `latest_buy_usdc_equivalent`;
- `latest_buy_quote_was_normalized`.

The UI column is labeled `Frank 原始支付`. For a normalized SOL trade it displays, for example:

`2.5 SOL ≈ 250 USDC（历史换算）`

It must never display `250 USDC` alone as if that were Frank's actual payment.

## Tests / audit targets

Coverage includes:

- exact previous-closed SOLUSDC candle selection;
- candle evidence contains no transaction block time;
- same candle reused by two trades retains separate transaction times;
- retryable 429 is not persisted;
- deterministic missing K line is cacheable;
- reusable external reference cache copies evidence into a fresh replay target without a network call;
- strict regression does not exclude mixed SOL/USDC mints;
- missing quote decimals/amount are input failures, not reference failures;
- frozen Frank V1 can recover ACCUMULATION/MULTIPLE from verified shadow input;
- unresolved SOL remains fail-closed;
- transient WAIT debounce/recovery;
- a 90-second slow evaluation cycle does not reset a 60-second grace timer;
- only a >300-second gap resets debounce;
- no-route threshold outcome gets a -100% stress bound;
- no-observation remains unknown and is not converted to -100%;
- exact Decimal Jupiter fixture amount conversion.

## Remaining approval gates

Do not change `FOLLOW_POLICY_V1_REVIEW_CANDIDATE` to `FROZEN_APPROVED` until all are complete:

1. external review of the new branch HEAD;
2. full existing + new local-agent test suite passes;
3. shadow replay on the real local `forward.sqlite`;
4. strict source-signal regression PASS;
5. every SOL trade needed by the replay is resolved and `shadow_replay_gate_pass == true`;
6. manual review of every newly recovered SOL signal;
7. real Jupiter liquid / thin / no-route fixtures captured and parser verified;
8. enough forward observations for threshold review, otherwise remain `INSUFFICIENT_SAMPLE`;
9. Gmail/local live delivery remains review-disabled until separately approved;
10. `PRODUCTION_TRADING = NO_GO` remains unchanged.

No result from this branch may automatically modify production configuration, restart the Frank daemon, enable a scheduler, send a live notification, or place a trade.
