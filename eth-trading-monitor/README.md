# ETH Trading Monitor

This directory stores the automated ETH trading-signal monitoring records used by the ChatGPT mission workflow.

## Repository policy

- Repository: `lxxlx2/ChatGPT_mission_record`
- Timezone: `Asia/Bangkok`
- Every scheduled check must write a lightweight result into the repository, even when there is no actionable trade.
- `NO_ACTION` runs must not send email or user notification.
- Actionable signals must create a durable signal report and may trigger the configured user notification/email workflow.
- Monitoring evidence should include, when available: ETHUSDT price, funding, open interest, top-trader long/short structure, Hyperliquid/main perpetual-market context, Polymarket probabilities, material macro events, and the decision rationale.

## Paths

- `state/latest.md`: most recent monitor result, overwritten each run.
- `reports/daily/YYYY/YYYY-MM/YYYY-MM-DD.md`: chronological daily run log. Append one timestamped section per scheduled check.
- `signals/YYYY/YYYY-MM/YYYY-MM-DDTHHMM-<signal>.md`: immutable report for an actionable OPEN_LONG, OPEN_SHORT, TAKE_PROFIT, STOP_LOSS, MOVE_STOP, CANCEL_SETUP, REDUCE, or PAUSE signal.

## Decision outputs

Each run must end with exactly one primary status:

- `NO_ACTION`
- `OPEN_LONG`
- `OPEN_SHORT`
- `TAKE_PROFIT`
- `STOP_LOSS`
- `MOVE_STOP`
- `CANCEL_SETUP`
- `REDUCE`
- `PAUSE`

Actionable reports must state the exact action, price/trigger, intended notional or fraction, leverage if applicable, stop, take-profit plan, and concise rationale. Never fabricate unavailable market data; mark unavailable fields explicitly.
