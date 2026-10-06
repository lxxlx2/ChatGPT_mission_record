# Frank SOL/USDC normalization + Mission Meme follow review

Status: `CODE_ONLY / REVIEW_ONLY / NOT_AUTHORIZED_LIVE`

Branch: `codex/frank-sol-usd-normalization-review`

Production trading: `NO_GO`

## Why this exists

Frank V1 currently records SOL/WSOL active trades and inventory chronology, but its frozen amount predicates are numeric only for direct USDC quotes. A SOL quote therefore remains `UNDETERMINED` for the existing USD-equivalent gates even when the trade itself is valid.

The original source policy is stated in USD-equivalent terms, while the frozen implementation uses direct USDC as the numeric representation. This review candidate therefore normalizes SOL to an auditable event-time **SOL/USDC** reference, rather than silently treating USDT as USD, and does not change the live production model.

## Safety architecture

Production `classifier.py`, `evaluator.py`, `engine.py`, `scanner.py`, frozen policy and delivery authority remain unchanged.

The candidate path is:

```text
source forward.sqlite [READ ONLY]
  -> existing ACTIVE_TRADE classification
  -> if quote is SOL/WSOL:
       Binance official public SOLUSDC 1m history
       previous fully closed candle close only
       persist source candle + evidence hash
  -> shadow-only synthetic USDC-equivalent quote
       preserve original SOL raw quote in original_quote
  -> original frozen Frank V1 Engine / evaluator, dry_run=True
  -> separate replay DB + report
```

No current SOL price is substituted for a historical Frank trade.

## Historical price source

Default candidate source:

`BINANCE_OFFICIAL_SPOT_SOLUSDC`

Endpoint class: Binance official public Spot market-data, no account credential required.

Selection rule:

`PREVIOUS_CLOSED_1M_CLOSE`

For a Frank trade at epoch `T`, normalization uses the close of the immediately previous fully closed UTC 1-minute SOLUSDC candle. This intentionally gives up some precision to avoid using any price information that completed after the trade.

The pair was verified through Binance market data to have current 1-minute candles and historical 1-minute data for 2026-09-01, covering the relevant recent Frank research window.

Each persisted reference contains:

- source and symbol;
- interval and selection rule;
- Frank block time;
- candle open/close timestamps;
- OHLC;
- selected SOL/USDC close;
- evidence SHA256.

If the exact candle is unavailable or invalid, normalization stays `UNDETERMINED`.

Pyth Benchmarks is not the default because its historical API currently requires an API key. It can be added later as an optional cross-check, not an implicit fallback.

## Shadow conversion

A verified example:

```text
original_quote:
  asset = SOL
  quantity = 2.5 SOL

event-time reference:
  SOL/USDC = 100

shadow model quote:
  quote_asset = USDC
  quote_quantity = 250
  quote_normalization = SOL_TO_USDC_SHADOW_EQUIVALENT
```

The synthetic USDC representation exists only so the already-frozen V1 evaluator can consume the amount without any evaluator code change. The original SOL quote and normalization evidence remain attached to the trade.

This must never be described as Frank actually paying USDC.

## Replay report

`scripts/frank_sol_usd_shadow_replay.py` must run against a read-only source DB and a new target DB.

Required report fields include:

- total signatures / ACTIVE_TRADE count;
- SOL trade count;
- SOL resolved / unresolved count;
- source signal count;
- shadow signal count;
- SOL-added ACCUMULATION / MULTIPLE signals;
- missing source signals;
- `usdc_regression_pass`;
- source-only and shadow-only USDC signals.

Hard acceptance gate before any production migration design:

```text
usdc_regression_pass = true
missing previously valid USDC source signals = 0
all added SOL signals manually inspectable back to:
  transaction -> original SOL quote -> Binance SOLUSDC candle -> USDC equivalent -> V1 predicates
```

A recovered SOL signal is evidence for review, not automatic production authorization.

## Mission Control transient failure debounce

Review policy now uses:

`transient_wait_grace_seconds = 60`

Only an existing `BUY / SMALL_BUY -> transient WAIT` is delayed.

During the grace window:

- `candidate_latest` updates immediately so the dashboard shows the problem;
- no immutable WAIT event is created;
- no Gmail/local invalidation notification is sent.

If service/data recovers before 60 seconds, the pending transition is deleted and no WAIT -> recovery notification pair is emitted.

If the fault persists past the grace period, one normal WAIT transition is created and can notify through the existing delivery rules.

Non-transient `NO_BUY`, SELL/EXIT or other structural invalidation remains immediate.

## Forward follow-policy evidence

Review mode records at most one `follow_observations` row per candidate per 60-second bucket and keeps 14 days by default.

Recorded fields include:

- pattern and runtime state;
- executable Jupiter price;
- Frank latest-buy reference price;
- price deviation;
- Jupiter price impact;
- route existence;
- provisional Decision.

This is calibration evidence only. It does not send a trade and does not automatically change thresholds.

`scripts/mission_meme_threshold_replay.py` evaluates candidate threshold grids using durable 15m / 60m forward executable-price observations. Fewer than the requested minimum samples is explicitly `INSUFFICIENT_SAMPLE`.

Historical executable Jupiter impact does not exist in the old durable DB and must not be invented. Historical reconstruction and new forward OOS evidence must remain labeled separately.

## Real Jupiter fixtures

`scripts/capture_jupiter_quote_fixtures.py` captures official read-only `/swap/v1/quote` responses and hashes them. It performs no wallet operation, transaction build, signing or send.

Before approval capture at least:

1. liquid token quote;
2. thin-liquidity token quote;
3. no-route mint response.

Verify parsing of `priceImpactPct`, route/no-route behavior and current real error response shape against these immutable fixtures.

Metis `/swap/v1` is currently deprecated by Jupiter. The current candidate keeps it only as a quote-only compatibility source because Swap V2 order/build requires a taker wallet. V2 migration should be evaluated separately; deprecation alone is not permission to add a wallet/signing path to Mission Control.

## Tests added

New code-level coverage includes:

- exact previous-closed-minute SOLUSDC candle selection;
- future/wrong candle fails closed;
- SOL quote normalization preserves original quote;
- missing SOL/USDC reference stays unresolved;
- original frozen Frank V1 evaluator can recover ACCUMULATION/MULTIPLE from verified normalized SOL input;
- unresolved SOL still stays `UNDETERMINED`;
- Mission Control only uses verified event-time SOL/USDC for Frank entry price;
- transient WAIT debounce and recovery;
- zero-grace compatibility for older fixtures;
- bounded forward observation upsert/pruning.

## Remaining approval gates

Do not change `FOLLOW_POLICY_V1_REVIEW_CANDIDATE` to `FROZEN_APPROVED` until all are complete:

1. external review of this branch;
2. full existing + new local-agent test suite passes;
3. SOL shadow replay on the real local `forward.sqlite`;
4. zero USDC regression;
5. manual review of every newly recovered SOL signal;
6. real Jupiter liquid / thin / no-route fixtures captured and parser verified;
7. enough forward observations to evaluate provisional 8% / 20% deviation and 1.5% / 3% impact thresholds, otherwise retain `INSUFFICIENT_SAMPLE`;
8. Gmail/local delivery remains review-disabled until separately approved;
9. `PRODUCTION_TRADING = NO_GO` remains unchanged.

No result from this review branch may automatically modify production configuration, restart the Frank daemon, enable a scheduler, send a live notification, or place a trade.
