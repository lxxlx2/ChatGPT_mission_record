# Frank FM2 manual forward shadow

This is an explicitly invoked shadow collector. It uses only `https://api.mainnet.solana.com` and the existing immutable official raw cache. It does not install a scheduler, send email or produce an investment decision.

## Bound validation

The constructor accepts paths to the manual records, original raw500 and final processing directory. It rechecks the original fixed Primary50 packet and its exact copied bytes, all500 raw compressed hashes against the earlier independent arithmetic audit, all500 normalized evidence against the current parser, and the aggregate evidence hash. It verifies the50 identities and completed explorer captures, binds recorded signer/fee-payer and available canonical token/authority records, and requires the four-axis thresholds and the separately reviewed original Active13. Caller-declared counts cannot authorize forward collection.

Unknown program decoders stay UNKNOWN. FAILED follows official `meta.err`. Opposing flows are aggregated by mint, including separately decoded transient owned WSOL transfers; repeated create/initialize descriptions identify one account. Native SOL balance changes alone never establish an exchange. Program-bound swap instruction evidence and wallet signature or concrete execution authority are required. There is no lifetime-entry, PnL or wallet-wide full-exit assertion.

Run processing with `--fixed-packet` pointing to the original v4 packet. Retain each processing directory. FM2 never regenerates or resamples its Primary50.

## Durable forward behavior

Default polling is30seconds. The collector paginates from the durable signature boundary and processes the missing signatures in reverse RPC list order. A missing boundary or unavailable transaction stops cursor advancement. Raw cache files are exclusively published after fsync. SQLite commits normalized evidence, first detection/normalization timestamps, generated candidates, and signature/slot/block_time cursor together. Candidate hash/size admission failure rolls the transaction back. Restart reuses the exact cache; identical candidates dedupe by event ID and content hash.

The seed consists of the validated recent500 evidence and an explicit initial cursor. Seed records are not new forward detections. A startup cursor is not an assertion that the intervening history has been processed. Candidate context remains available observed history with `lifetime_entry_proven=false`. Durable broader backfill uses a separate versioned SQLite database and the fixed18,203-signature snapshot; it reuses raw caches, records every result and summarizes each100 records. It does not delay Monster work.

A parser revision uses a new shadow database and preserves the earlier database. `frank_forward_migrate` checks the new500/manual gate, replays archived transactions, verifies unchanged live classifications/canonical axes, copies actual observation timestamps and preserves the latest cursor. The migration emits no new candidates. Its current conservative path refuses migration when the earlier database has live candidates; those require separately reviewed archive migration. No old observation time is synthesized.

## Metrics and acceptance evidence

Wall clock duration and active observation duration are reported separately from forced collector downtime. Real source activity determines status. A quiet source is `FRANK_FORWARD_SOURCE_IDLE`; synthetic signatures are unit fixtures only. At least one new real signature must traverse the RPC/parser/storage path when source activity exists. Non-ACTIVE transactions deliberately produce no active candidate. Historical private transport is reported separately from actual forward candidate transport.

First detection latency is the first official signature-list observation minus chain block_time. Normalized latency is the persisted normalized timestamp minus block_time. Forced recovery samples are reported separately from steady polling. A minimum20 real latency samples is required before presenting p50/p95 as acceptance metrics; smaller samples are reported as insufficient, with sample count and individual observations retained privately. UTC clocks are real wall clocks, never accelerated.

Actual SIGTERM, SIGKILL and at least300seconds of collector stoppage are checked using preserved cursor, SQLite integrity, cache bytes, independent official signature sequence and recovered normalized evidence. Initial empty-cache checks do not demonstrate populated-cache durability; a subsequent real hard-kill with cache files supplies that evidence.

Private test transport accepts only sealed source-bound mechanical candidates, item<=2KB and batch<=75KB. A rebuilt client reads the exact batch back and verifies canonical bytes/hash. Republishing identical bytes causes no commit. Advancing a private current pointer uses the last actually observed blob SHA; failed CAS preserves the existing built batch and retries it with verified expected state. No Gmail, app investment alert, automation or production runtime is authorized.

## Explicit commands

Use the project virtual environment from the local-agent directory. These environment variables are private evidence locations, not credentials:

```sh
.venv/bin/python -m scripts.frank_process500 --root "$FM1_EVIDENCE_ROOT/frank" --output "$FM2_EVIDENCE_ROOT/frank/processing-final" --fixed-packet "$FM1_EVIDENCE_ROOT/frank/processing-v4/review50-packet.json"
.venv/bin/python -m scripts.frank_manual_gate --manual "$FM2_EVIDENCE_ROOT/manual" --raw "$FM1_EVIDENCE_ROOT/frank/raw500" --processed "$FM2_EVIDENCE_ROOT/frank/processing-final" --output "$FM2_EVIDENCE_ROOT/frank/manual-gate-final.json"
.venv/bin/python -m scripts.frank_forward_shadow --root "$FM2_EVIDENCE_ROOT/frank/forward-final" --manual "$FM2_EVIDENCE_ROOT/manual" --raw "$FM1_EVIDENCE_ROOT/frank/raw500" --processed "$FM2_EVIDENCE_ROOT/frank/processing-final" --seconds 7500
.venv/bin/python -m scripts.frank_backfill --snapshot "$FM1_EVIDENCE_ROOT/frank" --root "$FM2_EVIDENCE_ROOT/frank/backfill" --seconds 7500
```

The report records actual processing/parser versions, run paths and verification outcomes. These commands are reproducible entry points, not proof that a run occurred.
