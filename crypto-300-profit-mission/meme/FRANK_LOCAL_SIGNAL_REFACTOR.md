# Frank-only local signal refactor — 2026-10-03

Authorized target: `FRANK_ONLY`, `LOCAL_DETERMINISTIC_SIGNAL`.
Operational status: **SHADOW_ONLY / NOT_DEPLOYED**. The existing launchd scanner remains active and unchanged. This document does not certify the target as live.

- Only Frank is enabled in `local-agent/config/frank_local_registry.json`; multiple wallets per person remain structurally supported.
- Other persons = DEFERRED. TOKEN_CONSENSUS = DEFERRED.
- GPT investment judgment and SEND/NO_SEND are removed from the target Frank critical path. The existing GPT handoff design is superseded for this requested target; its history is preserved. The old live service still uses that handoff pending cutover.
- Production trading = NO_GO. No wallet signing, trading or mutation; no new automation.

## Model identity is unresolved

The canonical historical definition is `state/frank-wallet-watch.md`, particularly the 2026-09-29 two-stage override: PRECONFIRM -> SUSPECTED_CONVICTION.

PRECONFIRM Path C: single active BUY >=15,000 USD equivalent, or >=2 active buys totaling >=25,000 USD in 60 minutes. The older meaningful-accumulation clock is >=2 buys totaling >=3,000 USD in 60 minutes, or >=5,000 USD followed by another buy in 60 minutes. These describe distinct stages and must not be interchanged without an explicit mapping.

SUSPECTED_CONVICTION includes persistence and >=10,000 USD cumulative buys, plus price, liquidity and token-control gates. The present request excludes social research, executable price/followability and GPT investment judgment. No independent frozen local multiple-model configuration was found in the audited active code. Deciding which historical stage and remaining gates define the two new signals is **BLOCKED_CANONICAL_STAGE_MAPPING_REQUIRED**. No SOL threshold or USD estimate has been invented. No deterministic-model completion is claimed.

## Implemented in the isolated branch

`mission_agent.signals` provides conservative classification, SQLite signature/trade/position records, supplied-stage signal identity and outbox infrastructure, finalized catch-up, and audit CLI. It imports no GPT or Git transport. Its scanner is explicitly shadow-only and does not evaluate a model or deliver signals.

The classifier requires a successful signed exchange, recognized invoked swap instruction, and opposing owned token/quote flows. Third-party ATA creation and proven inbound transfers never enter trade state. Unsupported exchange shapes and incomplete metadata remain UNKNOWN_NEEDS_REVIEW. Native SOL amounts are never inferred from rent-inclusive wallet deltas; decoded transient WSOL transfer evidence is retained.

Positions describe the observed active-trade ledger. Existing history is incomplete. Confirmed sells without a reconstructable earlier position are preserved as ACTIVE_TRADE / SELL_POSITION_UNRESOLVED; no EXIT is invented. Zero active-trade inventory closes the observed episode in tests. A canonical wallet-wide dust/close policy and complete bootstrap inventory remain unresolved, so this is not certified as full live position accounting.

All replay outbox entries are DRY_RUN_AUDIT and cannot be delivered. Supplied-stage tests exercise ledger mechanics; they do not validate a strategy model. Local notifier execution success means OS command acceptance, not proof a user saw a notification. A process crash during osascript dispatch leaves IN_FLIGHT evidence; exactly-once OS delivery recovery remains NOT_IMPLEMENTED. The environment had no terminal-notifier executable. No live test notification was sent.

No reliable local Gmail sender/credential integration was found in the audited runtime; existing Gmail code is mock or an external connected-capability canary. Gmail outbox delivery records CREDENTIAL_BLOCKED, never a fake message id. Automatic Gmail sender/reconciliation remains NOT_IMPLEMENTED.

## CLI

Run from the isolated branch's `crypto-300-profit-mission/local-agent` with the existing Python environment:

```bash
python -m mission_agent.signals --db /absolute/path/to/shadow-ledger.sqlite audit-frank --last 50
python -m mission_agent.signals --db /absolute/path/to/shadow-ledger.sqlite inspect-tx SIGNATURE
python -m mission_agent.signals --db /absolute/path/to/new-shadow-ledger.sqlite replay --source-db /absolute/path/to/old.sqlite --raw /absolute/path/to/raw --registry config/frank_local_registry.json --since UNIX_TIMESTAMP
```

Query commands open SQLite read-only. Replay writes only the explicitly selected independent ledger. Raw historical envelopes are signature-bound and unwrapped before classification.

## Cutover prerequisites

Resolve model mapping and USD evidence policy, complete model tests and historical signal replay, establish inventory/dust policy, complete crash-safe delivery recovery, then checkpoint and perform one controlled cutover with chain/local reconciliation. No cutover or legacy restart was performed during this audit.
