# Authorized local Frank shadow — FM3

Exactly one LaunchAgent: `com.jerson.crypto-monitor-frank-shadow`. Its plist is local in `~/Library/LaunchAgents`; implementation generates this exact identifier and refuses to overwrite a different existing configuration. It runs the repository Python as a module, retains private logs/raw/SQLite/health outside Git and stays active after the interactive work ends.

Only official Solana finalized signatures/getTransaction jsonParsed are polled. A fresh root seeds normalized500 without candidates, records a current finalized cursor boundary without creating a forward observation, then observes later signatures. Cursor pagination must find the durable boundary before processing. Evidence, real observation, candidates and signature/slot/blockTime cursor commit atomically in SQLite.

30-second cadence, health replacement fsynced and atomic, one-process lock. Health exposes actual observation counts, polling/request/retry/errors/429/timeouts, cursor and latest candidate, successful poll time, restart and transport status. Missing ACTIVE remains WAITING_REAL_EVENT. No historical transaction is promoted to a forward sample.

A separate transport thread uses only `runtime-v2-test/frank-forward-shadow/<run_id>/` on the private runtime repository. Real observations are required for every transported item. Immutable batch readback, canonical exact equality, hash validation and identical-publish zero-write check are recorded. Published but unverified batches are retried after restart; receipts are keyed by batch ID.

Historical backfill is a bounded300-second child with an exclusive history lock and lower priority than forward. New historical network requests start only in the first8 seconds after a successful completed poll, leaving at least22 seconds before the next nominal poll. Existing historical raw/SQLite progress resumes. The main forward thread never waits for historical network calls or transport. A pending request may finish in its own worker; it cannot occupy the forward execution thread. Shutdown terminates the child; the history lock also prevents duplicate workers across an abrupt parent restart.

No Gmail, app alert, GPT call, ChatGPT automation, portfolio write, wallet operation or production transport exists in this service. Exactly one Frank LaunchAgent is authorized; Monster history/replay remains manually invoked.
