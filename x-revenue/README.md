# X revenue workflow

This workflow converts real public market data and official regulator feeds into X-ready candidates while keeping publication locked behind human Owner approval.

## Current pipeline

- `Nasdaq + Kraken + Fed/SEC RSS -> deterministic trigger/detection`
- quiet or unchanged market -> `NO_ACTION` with no candidate and no Telegram noise
- triggered event -> deterministic cross-asset analysis -> deterministic candidate <= 280 chars
- quality/integrity checks -> persisted immutable artifact set
- existing `@Jersonliu_bot` discovers pending approval artifacts
- Owner approves/rejects exact candidate SHA256
- approved text is copied manually into X by the Owner
- external X publishing remains locked: `external_publish_allowed=false`, `external_publish_performed=false`

The X repository does not own a second Telegram polling client. Telegram delivery/callback ownership is unified in `lxxlx2/local-ai-platform` and was merged there through PR #42.

## Local model policy

Local Qwen is currently **not approved for X/Twitter copy generation** on the 48 GB workstation under representative office workload.

### Qwen3.6

On 2026-09-06 two representative production memory preflights denied admission before model start. The second measured about 22.45 GiB reclaimable memory versus the current 23.8 GiB admission threshold for the 28 GiB model profile.

Result: `X_COPY = RESOURCE_BLOCKED / DO_NOT_USE_FOR_X_COPY`.

This is an availability/resource decision, not a writing-quality verdict. The model never started for the X-writing test.

### Qwen3.8

Qwen3.8 has a higher expected memory envelope and prior representative cold-load evidence hit the relative swap-growth safety limit.

Result: `X_COPY = RESOURCE_BLOCKED / DO_NOT_USE_FOR_X_COPY`.

### Promotion rule

A local text model may replace deterministic candidate generation only after a dedicated `X_COPY` qualification passes under representative workload, including:

- safe admission/coexistence;
- 10 real saved market artifacts;
- zero unsupported numbers, events, causes or invented facts;
- zero posts above 280 characters;
- no direct buy/sell instructions or promised returns;
- at least 7/10 outputs judged materially more useful than the deterministic baseline;
- bounded latency compatible with the scheduled workflow;
- cleanup/resource gates pass;
- human Telegram approval remains mandatory.

Until that happens, deterministic candidate generation is canonical.

## Commands

Run the workflow once against live sources:

```sh
python3 x-revenue/pipeline.py run
```

Verify an artifact's integrity and immutable SHA-256 hashes:

```sh
python3 x-revenue/pipeline.py verify \
  --artifact x-revenue/artifacts/<run-id>
```

Record a local human decision without Telegram:

```sh
python3 x-revenue/pipeline.py approve \
  --artifact x-revenue/artifacts/<run-id> \
  --decision approve \
  --actor owner
```

Verify that the external publish gate remains locked:

```sh
python3 x-revenue/pipeline.py publish-check \
  --artifact x-revenue/artifacts/<run-id>
```

Run the workflow verification test suite:

```sh
python3 -m unittest discover -s x-revenue/tests -p "test_*.py" -v
```

## Unified Telegram approval

The existing `@Jersonliu_bot` in `lxxlx2/local-ai-platform` owns Telegram networking and approval callbacks.

The X workflow only persists/enqueues approval artifacts. It must not reintroduce:

- a second `getUpdates` consumer;
- direct X-workflow Telegram token ownership;
- duplicate callback handling;
- external publishing.

Approval states remain persisted as `PENDING`, `APPROVED`, `REJECTED` or `EXPIRED`, bound to the exact candidate SHA256.

## Scheduler & launchd

A 15-minute runner is provided in `x-revenue/scheduler.py` with bounded logging and single-instance locking.

To activate the persistent user launchd agent:

```sh
cp x-revenue/com.jerson.x-revenue.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.jerson.x-revenue.plist
```

To deactivate:

```sh
launchctl bootout gui/$(id -u)/com.jerson.x-revenue
```

The scheduler performs detection/candidate preparation only. It does not publish externally.
