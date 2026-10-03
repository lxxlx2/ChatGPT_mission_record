# Offline PERSON_PATTERN historical validation

Research only. All candidates remain `OBSERVE_ONLY`; production trading remains `NO_GO`. This package has no scheduler, Gmail sender, wallet signer, production registry writer, or production enablement path. Source artifacts in `../validation/` are read-only inputs, not qualification episodes.

## Run and resume

Requires Python 3.11+; standard library only. Run from this directory:

```bash
python3 -m unittest discover -s tests -v
python3 -m meme_person_validation validate-all --page-size 100 --max-pages 1
python3 -m meme_person_validation validate --person ethermonk --max-pages 100
python3 -m meme_person_validation validate --person point-farm --max-pages 100
python3 -m meme_person_validation validate --person thesolstice --max-pages 100
```

Resume is automatic. SQLite transaction payloads and wallet/signature associations persist separately from the page cursor. A partially downloaded page is retried using cached payloads; the cursor advances only when every raw transaction is durable. Empty pages record pagination completion; this does **not** establish archival or token-account coverage. Repeated cursors fail closed. Public RPC defaults to `https://api.mainnet-beta.solana.com`. Prefer a dedicated archive-capable endpoint via `SOLANA_RPC_URL`, `ALCHEMY_API_KEY`, or `HELIUS_API_KEY`. Set these locally in the environment; no values or authenticated endpoints are written to artifacts. Retry/backoff is bounded; HTTP 429 is a data-source blocker rather than a fabricated empty result.

`--cache-only` performs normalization and fixture validation without network access. `--output` selects an isolated run directory. `--persons` and `--policy` select research configs; adding a person requires seed/evidence data, not code branches.

## Responsibilities

| Module | Responsibility |
|---|---|
| `wallet_graph.py` | Separate accepted research ownership, relationships, infrastructure, unresolved identities and validity intervals |
| `solana_export.py` | Finalized signature pagination, raw payload cache, resume; RPC/Alchemy/Helius/indexer/fixture interfaces |
| `event_classifier.py` | Parse token deltas/owners/accounts, SPL transfers, ATA and fees; route dedupe; unproved swaps stay UNKNOWN |
| `reconciliation.py` | Check lossless indexer rows against cached finalized raw transaction identity/accounts; inventory assertions |
| `episode_builder.py` | Person + mint position episodes, weighted-average costs, partial realization, dust exit and censoring |
| `segmentation.py` | TRAIN-only inter-event gap distribution candidates, never an arbitrary inactivity split |
| `feature_builder.py` | Causal window flows, growth, velocity, pre-add profitability and available market observations |
| `signal_discovery.py` | TRAIN-distribution candidate thresholds for five pattern families, observable first trigger |
| `replay.py` | Exact historical executable delayed quotes, fee-aware returns, path MFE/MAE/drawdown, censored source exit |
| `robustness.py` | Closed realized economics, dynamic winner exclusions, mint and validated theme exclusions |
| `split.py` | Chronological splits, boundary-straddling purge, immutable freeze, forward interface without scheduling |
| `negative_controls.py` | Research controls reject accumulation-only families; control snapshots never become replay truth |
| `base_rate.py` | Matched universe false-positive denominator and preregistered performance checks |
| `evaluation.py` | Evaluate frozen pattern triggers and delayed executable samples per chronological stage |
| `qualification.py` | Required evidence gates and >=30 episodes; no automatic production promotion |
| `report.py`, `__main__.py` | CLI orchestration, availability, source hashes, research and audit artifacts |

## Data contracts and fail-closed limitations

Raw RPC decoder deliberately does not call balance changes BUY/SELL. A DEX program mention alone also does not prove user swap intent. Route-specific swap normalization must be supplied by a **lossless verified indexer adapter**. The generic import option is:

```bash
python3 -m meme_person_validation validate --person point-farm --cache-only \
  --events /absolute/local/lossless-events.json \
  --market /absolute/local/point-in-time-market.json \
  --quotes /absolute/local/historical-executable-quotes.json
```

Lossless event bundle: `events[]` plus `inventory_assertions[]`. Every swap needs event_id/signature/slot/block_time/wallet/mint/quote_mint/token_delta/quote_delta/source_token_account/destination_token_account/route_id/route_evidence/usd_notional/usd_price_evidence/verified_swap. Cached raw transaction signature, slot, time and source/destination account membership must match. `verified_swap` is an adapter conclusion requiring auditable route evidence, not permission to relabel unproved balances. Unsupported routes remain UNKNOWN. DEX-specific instruction ABI decoding, native SOL fee/rent reconciliation, historical closed ATA enumeration, and archive-provider coverage attestations are **not implemented in this initial release**. Consequently wallet-only RPC pagination is never labeled chain-complete qualification coverage.

Inventory assertions require canonical mint, initial_quantity `"0"`, final_quantity, evidence_id, and complete_owner_inventory. Unknown external flows block reconciliation. Reconstruction without complete balances remains partial. Open episodes retain separate realized and unrealized fields; missing historical marks stay null. Dust quantity defaults to exact zero, a conservative engineering assumption, configurable before freeze. Dormant-gap candidates are reported from TRAIN only; this release does not split open episodes on a gap because a validated position/thesis reset definition is unavailable.

Market observations require mint, timestamp and available_at (defaults to timestamp). At signal time only observations known by then are read. Missing liquidity, holder or market-cap history remains null. Signal builders never read terminal episode economics.

Executable quotes require exact timestamp = T_signal + delay, exact configured notional, mint, side, price, quantity, route, liquidity, slippage, price_impact, fees, executable and historical_pool_evidence. Exit quotes additionally require matching acquired quantity and net proceeds_usd. There is no interpolation, candle substitution, or tracked-wallet entry fallback. Historical path observations require the same acquired quantity, executable proceeds and pool evidence; MFE/MAE only populate when path_coverage_complete is supplied. Missing path prevents COMPLETE replay. The default USD 25 notional is an explicit research assumption, not a trading recommendation. No permanent slippage or profitability threshold is invented. `HISTORICAL_QUOTES_FILE` can replace `--quotes`.

Canonical delay/horizon seconds are 300/900/3600/21600/86400; high-resolution 60/120; auxiliary 0/1800/7200. Fixed horizon returns are measured from delayed user entry. Open source episodes do not fabricate source-full-exit returns.

## Qualification and remaining engineering gates

Engineering tests passing does not validate a strategy. The initial CLI intentionally cannot pass research qualification while complete token-account coverage, verified route economics, historical executable prices, validated theme labels, relevant base-universe false positives, and preregistered profitability evaluation are unavailable. Matched base-universe comparison and preregistered numeric policy checks are available in `base_rate.py`; CLI automatic policy acceptance remains blocked until such auditable datasets and policy are supplied. Missing metrics remain null and gates false. No source CSV is used for threshold optimization. Negative controls only reject a known unsafe model family; stronger families remain untested until causal histories and executable replay exist.

Frozen configurations include code hash, seeds, thresholds, TRAIN episode IDs and segmentation candidate. Changing them in an already frozen output directory raises `FROZEN_CONFIG_CHANGED_NEW_HOLDOUT_REQUIRED`; create a new predeclared data split/output for a new experiment. Early no-data runs do not freeze or consume HOLDOUT. `ForwardInterface` is an inert future contract and cannot start live observation.

## Artifacts

Outputs stay under ignored `output/<person>/`. Raw data is lossless SQLite (`transactions`, `wallet_signatures`, `checkpoints`); normalized events and episodes have CSV plus JSON outputs; features/signals/replay/robustness/stage reports/qualification/source manifests/negative controls have JSON outputs. This standard-library release uses SQLite/CSV/JSON instead of pretending to produce Parquet. No large raw data enters Git. Sanitized compact execution summaries may be committed under `reports/`.

## Authority and conflicts

Baseline: origin/main `973c1ff7`. Read monitor spec, validation README, all three summaries/CSV/pattern JSON/handoffs, global Mission/scope/framework/principles, and Frank replay/checkpoint references. Current canonical rules keep all three OBSERVE_ONLY with zero validated patterns. Existing Frank Python runtime is not present in this repository snapshot. Historical research handoffs prohibit committing their originating research; the current explicit request authorizes new pipeline/code/tests. Source research files remain unchanged. No new profitability cutoff is authorized; qualification stays blocked until preregistration and evidence exist. Repo canonical horizons take priority over handoff extra horizons.
