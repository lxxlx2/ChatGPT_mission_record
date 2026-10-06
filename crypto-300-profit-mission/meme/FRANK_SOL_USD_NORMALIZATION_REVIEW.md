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

For a Frank trade at epoch `T`, normalization uses the close of the immediately previous fully closed UTC 1-minute SOLUSDC candle. The pair was verified through Binance market data to have current and recent historical 1-minute candles.

A durable candle reference contains only candle/source evidence:

- source, symbol, interval and selection rule;
- `reference_epoch`;
- candle open/close timestamps;
- OHLC;
- selected SOL/USDC close;
- evidence SHA256.

It deliberately does **not** contain a Frank transaction `block_time`. Each normalized trade wraps the shared candle reference with its own `trade_block_time`, so two Frank trades in the same minute may share one evidence hash without inheriting each other's transaction timestamp.

### Cache and retry policy

Only these results are durable-cacheable:

- `VERIFIED` exact candle;
- deterministic `BINANCE_KLINE_NOT_FOUND`.

Transient failures such as HTTP 429, 5xx, timeout, network failure or malformed/transient response are retried with bounded backoff and are **not persisted** in `sol_usdc_references`.

Therefore a temporary failure on the first trade in a minute cannot permanently mark all later trades in that minute unresolved. Replay reports unresolved references grouped by failure reason.

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

The synthetic representation exists only so the already-frozen V1 evaluator can consume the verified equivalent without code changes. Dashboard/API must label the original SOL payment separately and must never imply Frank actually paid USDC.

## Strict replay regression gate

`scripts/frank_sol_usd_shadow_replay.py` reads source `forward.sqlite` with `mode=ro + query_only` and writes a separate target DB.

The regression comparison is deliberately strict. It does **not** exclude a mint merely because that mint also contains SOL transactions.

Signal identity for the hard gate includes:

- person;
- mint;
- episode;
- signal type;
- stage;
- triggering signature.

Required gate:

```text
missing_source_signals == []
source_signal_regression_pass == true
usdc_regression_pass == true   # compatibility alias for the same strict gate
```

A shadow signal may be added for newly resolved SOL evidence, but no previously emitted source signal may disappear silently. A change in triggering signature is exposed for manual review rather than hidden by a looser mint-level comparison.

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

`transient_wait_grace_seconds = 60`.

Only an existing `BUY / SMALL_BUY -> transient WAIT` is delayed. During grace:

- `candidate_latest` updates immediately;
- no immutable WAIT event is created;
- no Gmail/local invalidation notification is sent.

Recovery before 60 seconds clears the pending transition silently.

If there is an observation/service gap longer than the grace interval, the debounce clock is reset. Downtime therefore cannot count as continuous evidence and cannot cause an immediate WAIT notification on restart.

Non-transient `NO_BUY`, SELL/EXIT and structural invalidations remain immediate.

## Forward threshold evidence

Review mode records at most one `follow_observations` row per candidate per 60-second bucket and keeps 14 days by default.

`scripts/mission_meme_threshold_replay.py` explores the fixed candidate grid only; it never writes policy and never selects an automatic winner.

Default minimum sample count is now **30**, not 10. The report explicitly warns about multiple-testing/overfitting risk.

Return basis is:

`BUY_SIDE_EXECUTABLE_QUOTE_MARK_TO_MARK_EXCLUDES_SELL_SLIPPAGE_AND_FEES`

Therefore it is not realized PnL.

At 15m/60m, missing executable prices are not dropped. Reports include:

- observed outcome count;
- censored outcome count;
- no-route count;
- price-unavailable count;
- no-observation count;
- observed return statistics;
- pessimistic lower-bound statistics treating every censored outcome as `-100%`.

Historical Jupiter executable impact does not exist in the old durable DB and must not be invented. Historical reconstruction and new forward OOS evidence remain separate.

## Real Jupiter fixtures

`scripts/capture_jupiter_quote_fixtures.py` performs read-only `/swap/v1/quote` GET requests only.

Before any network request it preflights every requested output path and the manifest, so an immutable existing fixture cannot be discovered only after partial capture.

USDC request amounts use `Decimal`, not float, and reject precision beyond six USDC decimals.

Before approval capture at least:

1. liquid token;
2. thin-liquidity token;
3. no-route mint.

Verify `priceImpactPct`, route/no-route behavior and current real error shape against immutable fixtures.

Metis `/swap/v1` is deprecated by Jupiter. It remains only as a quote-only compatibility source in this review candidate because current Swap V2 order/build paths require a taker wallet. Deprecation is not authorization to add signing or wallet execution.

## Dashboard quote semantics

Dashboard candidate data exposes both:

- the effective/model quote fields;
- `latest_buy_original_quote_asset` / `latest_buy_original_quote_quantity`;
- whether normalization occurred;
- historical USDC equivalent.

The UI column is explicitly labeled `Frank 原始支付`. For a normalized SOL trade it displays, for example:

`2.5 SOL ≈ 250 USDC（历史换算）`

It must not display `250 USDC` alone as if that were Frank's actual payment.

## Tests added

Coverage includes:

- exact previous-closed SOLUSDC candle selection;
- candle evidence contains no transaction block time;
- same candle reused by two trades retains separate transaction times;
- HTTP 429 classified retryable;
- transient failure is not cached and a later same-minute call can recover;
- deterministic missing K line is cacheable;
- strict regression does not exclude mixed SOL/USDC mints;
- frozen Frank V1 can recover ACCUMULATION/MULTIPLE from verified shadow input;
- unresolved SOL remains `UNDETERMINED`;
- Mission Control only uses verified event-time equivalent;
- transient WAIT debounce/recovery;
- long service gap resets debounce;
- bounded forward observations;
- threshold censoring and pessimistic -100% lower bound;
- exact Decimal Jupiter fixture amount conversion.

## Remaining approval gates

Do not change `FOLLOW_POLICY_V1_REVIEW_CANDIDATE` to `FROZEN_APPROVED` until all are complete:

1. external review of the new branch HEAD;
2. full existing + new local-agent test suite passes;
3. shadow replay on the real local `forward.sqlite`;
4. `missing_source_signals == []` and strict regression PASS;
5. manual review of every newly recovered SOL signal;
6. real Jupiter liquid / thin / no-route fixtures captured and parser verified;
7. enough forward observations for threshold review, otherwise remain `INSUFFICIENT_SAMPLE`;
8. Gmail/local live delivery remains review-disabled until separately approved;
9. `PRODUCTION_TRADING = NO_GO` remains unchanged.

No result from this branch may automatically modify production configuration, restart the Frank daemon, enable a scheduler, send a live notification, or place a trade.
