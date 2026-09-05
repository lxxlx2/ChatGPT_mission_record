# X revenue workflow

This workflow converts real public market data and official regulator feeds into X-ready candidates while keeping publication locked behind human owner approval via Telegram or local CLI.

Pipeline flow:

- `Real market feeds (Nasdaq, Kraken, Fed/SEC RSS) -> Deterministic triggers`
- `If market quiet / unchanged -> NO_ACTION (no candidate, no Telegram notification)`
- `If triggered -> Deterministic cross-asset analysis -> Candidate (<= 280 chars)`
- `Quality and integrity checks -> Persisted artifact directory`
- `Telegram Owner approval request with cryptographically bound callback query buttons`
- `Owner decision (Approved / Rejected / Expired) persisted atomically`
- `External publish gate: LOCKED (external_publish_allowed=false, external_publish_performed=false)`

## Commands

Run the workflow once against live sources:

```sh
python3 x-revenue/pipeline.py run
```

Poll Telegram for pending approval callbacks:

```sh
python3 x-revenue/pipeline.py poll-callbacks
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

## Telegram Approval Configuration

To enable Telegram approval notifications:

1. Store the Telegram bot token safely in macOS Keychain (never committed to Git):
   ```sh
   security add-generic-password -a x-revenue -s x-revenue.telegram-bot -w "<YOUR_BOT_TOKEN>" -U
   ```
2. Set your Telegram Chat ID in `x-revenue/config.json` (or via `TELEGRAM_CHAT_ID` environment variable):
   ```json
   {
     "telegram_chat_id": "YOUR_CHAT_ID",
     "telegram_allowed_user_ids": ["YOUR_USER_ID"]
   }
   ```

If credentials are not yet configured, runs continue cleanly and record `delivery_state: CREDENTIALS_MISSING` in `approval.json`.

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
