# X revenue workflow

This vertical slice converts current public market data and official regulator feeds into an X-ready candidate while keeping publication locked behind human approval.

Pipeline branches:

- `Nasdaq US equity-index session + Kraken live ticker -> cross-asset analysis -> market candidate`
- `Federal Reserve RSS + SEC RSS -> title deduplication -> recency/keyword trend scoring -> approval context`
- `candidate + context -> quality and integrity checks -> human approval queue`

Run it from the repository root:

```sh
python3 x-revenue/pipeline.py run
```

The command creates one immutable timestamped directory under `x-revenue/artifacts/`. Review `candidate.txt`, `approval-packet.md`, `quality-check.json`, and the source receipts before making a decision.

Verify that all required files and immutable hashes still match before approval:

```sh
python3 x-revenue/pipeline.py verify \
  --artifact x-revenue/artifacts/<run-id>
```

Record a local human decision without publishing:

```sh
python3 x-revenue/pipeline.py approve \
  --artifact x-revenue/artifacts/<run-id> \
  --decision approve \
  --actor owner
```

Check whether the external publish boundary is open:

```sh
python3 x-revenue/pipeline.py publish-check \
  --artifact x-revenue/artifacts/<run-id>
```

The publish check currently fails closed. It never sends a network request. A real X publisher requires an approved account, an `X_BEARER_TOKEN`, an approved candidate whose digest still matches, and separate explicit authorization to publish.

## Source and failure behavior

- Only HTTPS requests to the fixed Nasdaq, Kraken, Federal Reserve, and SEC hosts are allowed.
- Responses are size-limited and their SHA-256 digests are stored in the artifact.
- The Nasdaq Composite, Nasdaq-100, and PHLX Semiconductor index quotes must all resolve to one recent US trading session; a mixed or stale basket fails closed.
- Regulator-feed items older than seven days are excluded from trend scoring.
- Each run is written to a staging directory and renamed only after every required file exists.
- Existing run directories are never overwritten.
- Candidate deduplication excludes the display timestamp, so an unchanged substantive post is not queued again a minute later.
- A process lock serializes runs; the deduplication state uses a unique temporary file and atomic replace only after artifact verification.
- If post-rename validation or state persistence fails, the new run directory is removed and the prior state remains in place.
- A source error, schema change, stale receipt, duplicate candidate, or quality failure stops the run before approval.

No model, credential, Telegram message, X post, payment, or analytics mutation is invoked by this slice.

## Current boundary

This milestone is a runnable source-to-approval vertical slice. It does not yet schedule itself, deliver approval requests to Telegram, call the X API, or collect post analytics. Those stages remain explicit follow-up work; the included publish check stays closed even if a credential happens to be present.
