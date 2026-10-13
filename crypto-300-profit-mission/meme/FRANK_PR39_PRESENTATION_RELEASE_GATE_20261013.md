# Frank PR #39 presentation: release readiness and Mac deployment gate

Date: 2026-10-13 (Asia/Bangkok). **STATUS: PREDEPLOY_PREPARATION_ONLY.**

This is a deployment **plan**, not an observed deployment or a claim that Mac
production has been changed.

## Audited product and authority

- Reviewed product head: `bda7ef0dfd89e6c1b11f9020163bf754bed5ae74`.
- Reviewer result for that exact source: **APPROVE for code merge only**.
- [GitHub Actions run 38289617455](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38289617455): exact same SHA, **SUCCESS**, targeted **50 passed**, all local-agent **1,277 passed**, including historical Git replay.
- Production policy is still **PRODUCTION_TRADING = NO_GO**. No auto-trading.
- Previous PR #35 Dashboard opportunity-first release has been reported deployed.
  This PR does not reorder the existing DOM or change its CA research controls.
- Product files are immutable after reviewer approval. Operations-only evidence
  scripts/tests/docs added after that review must NOT be counted as a new product
  review. Compare HEAD to the audited SHA under `mission_agent`, `config`,
  and `scripts/mission_meme_v1.py`; changes mean **STOP / re-review**.

## Why Dashboard-only deployment is insufficient for this PR

PR #39 changes the Dashboard, future email rendering, and Mission Control
local notification freezing. The last two run in the **Mission Control loop**.
A Dashboard-only source switch would leave the old email/local notification
semantics active. Eventually deployment must deliberately verify and update
**both** Dashboard and Mission Control loop source/release pins. The separate
Frank-only chain scanner and model are out of scope.

Do not restart any service solely because this document exists.

## Current independent-review closure

- H1 composite/routed last-buy amounts: unknown complete cost shown as unknown,
  observed leg kept as evidence, verified direct USDC and authorized SOL conversion preserved.
- M1 desktop pending presentation: new rows have frozen title/summary in separate
  `local_delivery_presentation` table; legacy rows can use hash-verified
  frozen Gmail subject/body, otherwise they enter MANUAL_REVIEW (no dispatch).
- L1/L2 blank and missing amounts now use consistent unknown presentation.
- L4 real JS currency formatter coverage exists.
- New email title prioritizes decision + latest recognized action + inventory;
  historical pattern is in body, long signature at end of audit section.
- L3 render-level BUY+SELL is nonblocking and unreachable under frozen policy;
  do not change frozen decision predicates as part of rollout.

## Release gates, in order

1. Freeze approved **product** blob against `bda7ef0d` and verify exact
   GitHub CI. Main may have advanced independently; recheck merge-tree before
   merge. Do not assert PR #39 already merged.
2. Run the **read-only** preflight below on the actual Mac against its actual
   Mission Control and Frank production SQLite files. The script makes no
   SQLite changes, sends nothing and never calls `launchctl`.
3. N1: record current latest-BUY `amount_predicate` coverage, including old
   direct-USDC-like rows missing it. Those stay labeled "未确认" (safe);
   **do not rewrite history** just to make displayed amounts look complete.
   If the script returns `REVIEW_REQUIRED_LEGACY_BUY_PREDICATES`, investigate
   evidence and decide whether to accept conservative unknown labels.
4. N3: verify `PRAGMA quick_check` and `foreign_key_check`, schema
   compatibility, live Gmail outbox states, and local notification queue.
   **Historical LIVE SENT_VERIFIED count is not required to be zero.**
   Require **LIVE in-flight = 0** and unresolved local queue = 0 immediately
   before the controlled switch, or stop and inspect. No silent deletion.
5. Before any restart: take a consistent private SQLite backup using the
   SQLite backup API; check backup integrity and foreign keys. Record
   immutable Gmail identities, attempt counts, statuses, subjects, body
   hashes, message IDs and receipts **privately**, not in public Git or
   this chat. Record source hashes for Frank policy, evaluator, classifier,
   scanner, store, parser, RPC, registry, approved follow policy and runtime
   runner pointers. Validate available disk space.
6. Verify the approved policy bytes/pin, LaunchAgent user and source pointers,
   existing loop/dashboard PIDs and current heartbeat/last successful poll.
   Ensure the replacement directory uses the intended approved source,
   existing virtual environment/configuration and no partial/mixed files.
7. Only after separate explicit deployment authorization and deployment
   script review: controlled release of both Mission Control loop and
   Dashboard; no Frank-only scanner restart, no test Gmail and no synthetic
   decision. The additive `CREATE TABLE IF NOT EXISTS`
   `local_delivery_presentation` will be created when ControlDB opens.
8. After switch, verify schema, foreign keys, decision policy hash, read-only
   Frank adapter, dashboard HTTP/DOM, Mission Control heartbeat, new
   notification eligibility only on **future real transitions**, Gmail
   SENT readback and queue counts. Preserve all old rows and their identity.
9. If checks fail: restore prior application source/runner pointers and
   perform a controlled service reload. Leave the **additive** table in
   the SQLite database; the old application simply ignores it. Never roll
   back by overwriting SQLite with an old backup while newer real decisions
   or receipts may exist. Stop and reconcile before any database restore.
10. Save timestamped, redacted evidence to the Mission repository only
    after protecting secrets and any personal email/wallet data. Do not
    declare LIVE success without actual Mac-side post-switch evidence.

## One-shot read-only Mac command

The Mac terminal may start in the home directory, which is **not** a Git
repository. Do **not** use `git rev-parse --show-toplevel` from `~`.
Prepare a new, isolated sparse clone from any directory. Keep the production
Dashboard and Mission Loop worktrees untouched. Pin the preparation commit
and verify its exact SHA before running the read-only audit.

```zsh
(
  set -e
  AUDIT_ROOT="$HOME/.cache/frank-pr39-independent-audit"
  mkdir -p "$HOME/.cache" "$HOME/Downloads"
  git clone --depth 40 --filter=blob:none --sparse --single-branch --branch fix/frank-presentation-history-semantics-20261012 https://github.com/lxxlx2/ChatGPT_mission_record.git "$AUDIT_ROOT"
  git -C "$AUDIT_ROOT" sparse-checkout set crypto-300-profit-mission/local-agent
  git -C "$AUDIT_ROOT" checkout --detach 3e7b4da6e6bf52eaf29aaac82279238830b54464
  python3 "$AUDIT_ROOT/crypto-300-profit-mission/local-agent/scripts/frank_pr39_predeploy_readonly.py" --source-root "$AUDIT_ROOT/crypto-300-profit-mission/local-agent" > "$HOME/Downloads/frank-pr39-preflight-20261013.json" || true
  cat "$HOME/Downloads/frank-pr39-preflight-20261013.json"
  open -R "$HOME/Downloads/frank-pr39-preflight-20261013.json"
)
```

A `REVIEW_REQUIRED_LEGACY_BUY_PREDICATES` or
`BLOCKED_ACTIVE_DELIVERY_QUEUE` result remains meaningful **NO_GO** evidence,
not permission to proceed. Do not hide a failed gate or merge/restart based
on the existence of this file.


From the `crypto-300-profit-mission/local-agent` directory of a clean
**PR #39 preparation worktree** containing the audited product SHA:

```zsh
python3 scripts/frank_pr39_predeploy_readonly.py
```

The control database is resolved from `~/.frank_meme_control_root`.
The expected Frank production database location defaults to the documented
`~/Documents/ChatGPT/crypto-monitor-frank-only-evidence-20261003/live-v1/forward.sqlite`.
If either actual location differs, use explicit existing paths:

```zsh
python3 scripts/frank_pr39_predeploy_readonly.py --control-db "/absolute/path/to/mission-control.sqlite" --frank-db "/absolute/path/to/forward.sqlite"
```

The script reports **aggregate counts only**, omitting mint, signature,
wallet, Gmail subjects/bodies, credentials and actual file paths. Exit codes:
`0` read-only preflight passed; `3` active/in-flight delivery blocked;
`4` legacy BUY amount-predicate coverage requires manual review;
`5` unavailable/unverifiable source or database. **Exit 0 does not
authorize deployment.**

## Specific N4 observation and replay constraint

Adding two metadata fields to `inputs` changes new `input_hash` values and
can change a **future** transition's snapshot identity. The service currently
calls `record()` only after evaluating a candidate; unchanged decision states
reuse the existing decision event (`changed=False`), and notification intent
is separately gated on transitions and last enqueued decision. Existing
`decision_events` / `gmail_delivery` rows must remain immutable. Compare
pre/post event and delivery counts and hashes before asserting zero duplicate
messages. Do not erase records or force old events through the new renderer.

## Explicit non-claims

- No live Mac preflight evidence has been uploaded yet.
- No actual current Frank `v1_states` predicate coverage has been verified.
- No merge, production reload, migration, real Gmail or synthetic signal was
  performed by creating this plan and audit script.
- No decision to trade or enable an automated order is implied.
