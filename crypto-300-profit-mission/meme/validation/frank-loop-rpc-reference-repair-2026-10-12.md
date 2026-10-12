# Frank Mission Loop RPC_FILE configuration repair — user-reported result (2026-10-12)

## Scope

Source: user-pasted local Mac terminal output after explicitly executing an RPC_FILE reference repair. The source is **not** independent remote Mac inspection, authenticated Solana RPC network proof, or confirmation that future LaunchAgent restart will succeed.

## Before

The prior sanitized preflight identified:
- `POLICY_JSON_PRESENT=PASS`, `APPROVED_SHA256_FILE_PRESENT=PASS`;
- `SOLANA_RPC_FILE_PRESENT=FAIL` in the existing Loop runner, which blocked further policy, DB clone and delivery anti-replay checks;
- the separate secret-free path diagnostic showed the Loop and Dashboard pointed to the **same missing path**, whereas the canonical application-support RPC file existed and was owner-only.

## Repair reported by Mac terminal

```text
RPC_FILE_REWRITE=PASS
MISSION_LOOP_RPC_FILE_REFERENCE=CANONICAL_APP_SUPPORT_RPC_FILE
DASHBOARD_RPC_FILE_REFERENCE=CANONICAL_APP_SUPPORT_RPC_FILE
CANONICAL_RPC_FILE=EXISTS
CANONICAL_RPC_FILE_MODE=0600
CANONICAL_RPC_FILE_SIZE_BYTES=67
```

Only the `RPC_FILE=` variable in the two runner shell scripts was changed by the user's command, and the command did **not** invoke `launchctl kickstart`, Gmail, database mutation, or Solana RPC. The active Mac process PIDs and actual contents of the credentials were not independently rechecked. Canonical file presence/permissions are not proof of valid credentials or a successful restart.

## Next gate

Rerun the existing **strictly read-only** Loop upgrade preflight (Git blob `d63ce182b6f74e71d28afccfcc67f85db11b46b3`) against live files, to verify:
- policy identity and approval match;
- live health freshness, OAuth credentials ownership;
- cloned SQLite migration/schema integrity;
- no legacy Gmail/local rows that would be eligible for unexpected new notifications;
- unchanged live Loop/Dashboard PIDs.

`LOOP_DEPLOYMENT=NOT_STARTED`. Do **not** restart Mission Loop until this follow-up preflight and reversible upgrade plan are independently validated.

Dashboard layout redesign is tracked separately as **Draft PR #35**; it must not change the operational release gates or trade/Gmail policy.
