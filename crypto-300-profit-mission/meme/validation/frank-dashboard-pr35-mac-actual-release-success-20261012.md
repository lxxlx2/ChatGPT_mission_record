# Frank PR #35 Mac Dashboard-only production acceptance — 2026-10-12

## Operator receipt and screenshot
The user provided a direct pasted macOS Terminal log and browser screenshot from the local Frank Dashboard. This report records **operator-supplied** evidence, not direct SSH/container access to the Mac.

- Release exact SHA: `62697bf98606c19c5709c27006a6a40d9408db97` (previously reviewed/merged PR #35).
- Integrity check on the exact operations helper: `SCRIPT_INTEGRITY=PASS`.
- Existing Dashboard PR #34 source verification: `CURRENT_DASHBOARD_EXPECTED_PR34=PASS`.
- New version source verified: `REMOTE_PINNED_SHA=PASS`, `RELEASE_PR35_LAYOUT_ORDER=PASS`, `RELEASE_FOLLOW_OPPORTUNITY_ID=PASS`.
- Private backup receipt **identifier only**: `20261012T153535Z-25790`. Never upload private sqlite snapshots, OAuth credentials, or backup contents to the public repository.
- Both production SQLite snapshots integrity: two `SQLITE_BACKUP_INTEGRITY=PASS`. Detached server launched, old Dashboard recognized by listener/PID plus root HTML, exact J7/BPXX read-only window assertions passed.
- `LIVE_PR35_OPPORTUNITY_FIRST=PASS` checked on both detached candidate server **and live production HTTP response**.
- `DASHBOARD_PID_REPLACED=PASS`, `DASHBOARD_STILL_LIVE=PASS`.
- `MISSION_LOOP_PID_UNCHANGED=PASS`, `MISSION_LOOP_FILE_UNCHANGED=PASS`.
- `DASHBOARD_PR35_LAYOUT=SUCCESS`, `DASHBOARD_RELEASE=SUCCESS`, `DASHBOARD_RESTART=YES MISSION_LOOP_RESTART=NO`.
- `NO_GMAIL_SEND_INITIATED=YES LOOP_EXPORT_CONFIGURATION_UNCHANGED=YES`.

### Visual confirmation
Uploaded Safari screenshot of the local `127.0.0.1` Dashboard shows, from top:
1. current follow opportunity card (NO_BUY, latest SELL, inventory uncertain);
2. Frank status tiles;
3. Frank recent buys and sells;
4. lower sections remain below scroll fold.

Example opportunity: `2j5SaS7…nW2ZM`, in the UI **NO_BUY** with 7 local buys and 2 local sells. Quote, deviation and impact explicitly show **not requested because Frank exited**. Historical accumulation is displayed but not a fresh buy signal. Bottom recent-transactions feed shows SELL and `卖出待确认` separately; that classification is not independent evidence of complete trade reconciliation.

Screenshot at the point of observation showed a healthy 13-second-ish loop heartbeat and functioning UI. The screenshot does **not** prove the previous approval path sent any live emails or that all underlying chain-derived balances are correct. It confirms presentation/routing and that the already-running Loop was not kicked by this Dashboard helper according to the user-provided terminal receipt.

## Actual release status
**PR35 Dashboard Mac deployment: SUCCESS and visually accepted.**

Do not rerun the PR35 installer merely for this result. Do not restart/upgrade the production Mission Loop as a side effect of UI changes.

## Follow-up work remaining, deliberately segregated
- **Draft PR #37**: future Gmail copy semantic fix (NO_BUY with latest SELL and unknown position before historical MULTIPLE; last BUY payment labeled historical). Exact CI [38271418409](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38271418409) **SUCCESS**, 35 focused, 1266 full tests. Still requires independent AI review of frozen mail identity/no replay. Template deployment would require an independent live Loop upgrade and is **not part of this Dashboard-only release**.
- **Draft PR #38**: compact collapsed watch pool with focus/total count. Exact CI [38272215542](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38272215542) **SUCCESS**, 7 focused, 1263 full tests. Still requires separate layout review, merge and separately approved Dashboard-only rollout.
- The previously prepared PR36 **Mission Loop live cutover remains NOT_STARTED and requires separate explicit authorization**. Existing source release and backup safety should not be changed in this UI task.

`CURRENT_PHASE=PR35_MAC_LIVE_SUCCESS__PR37_38_INDEPENDENT_REVIEW_PENDING`
