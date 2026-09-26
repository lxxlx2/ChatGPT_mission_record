# Technocore Close Call local runner

Authority: `../../positions/flop-close-call.md`.

This helper is intentionally conservative. Version 1 handles the immediate start only:

1. create the fixed 52-key fleet locally;
2. register `BASE-B0` and a unique low-traffic room;
3. register the remaining keys;
4. inspect the live referee;
5. open a scheduled static pair;
6. open bracket round 1.

Bracket rollover automation is deliberately deferred until round-1 live settlement behavior is verified.

## Security

Private Ed25519 seeds are written only to:

`~/.config/technocore-close-call/keys.json`

The script sets mode 0600 and refuses to run if the file becomes group/world-readable.

Never commit that file or paste its seeds into chat.

## Run

From the repository root:

```bash
uv run crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py init
uv run crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py status
uv run crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py bootstrap
```

After bootstrap says the dedicated room is registered and all owner messages have been sent, wait at least one fresh sweep, then:

```bash
uv run crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py status
uv run crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py open-static 1
uv run crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py open-bracket
```

Do not run `open-static 1` twice.

If the script refuses because the reference is older than 120 seconds, wait for a fresh referee sweep. Do not bypass the freshness guard.

## First-live checkpoint

After T01 and bracket round 1 are submitted, inspect `d-close1-flow`, `d-close1-positions` and `d-close1-pnl` before adding rollover code. The next planned bracket rollover is 2026-09-28 09:15 UTC, so there is time to validate actual settlement behavior first.
