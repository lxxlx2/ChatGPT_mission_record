# ChatGPT Mission Control — GitHub Projects setup

This repository uses GitHub Issues as the source of truth for remediation and quality work. The connected GitHub tool can create/update Issues and repository files, but it does not currently expose GitHub Projects v2 creation or field-management actions, so the Project board must be created once in the GitHub UI.

## Recommended project

Name: `ChatGPT Mission Control`

Preferred view: Board + Table

## Recommended custom fields

| Field | Type | Suggested values |
|---|---|---|
| Status | Single select | Backlog, In progress, Monitoring, Blocked, Done |
| System | Single select | Airdrop/TGE, Crypto Daily, US Stock Daily, Archive/Infra |
| Work type | Single select | Report quality, Data source, Backfill, Automation, Audit |
| Priority | Single select | P0, P1, P2, P3 |
| Health | Single select | Green, Yellow, Red |
| Last verified | Date | latest manual/automated verification |
| Owner | Assignee | GitHub assignee |

## Initial issues to add

- #1 Backfill historical formal reports and alert archives
- #2 Upgrade Crypto Early/Meme Alpha coverage
- #3 Make monthly stock and crypto recommendations actionable

## Recommended Board columns

1. Backlog
2. In progress
3. Monitoring
4. Blocked
5. Done

## Recommended Table views

### Monitoring systems
Filter: `Work type = Automation OR Audit`
Group by: `System`
Show: Status, Health, Last verified, Priority

### Report quality
Filter: `Work type = Report quality OR Data source`
Group by: `System`
Sort: Priority ascending

### Archive completeness
Filter: `Work type = Backfill`
Show: Status, Last verified

## UI setup

1. Open the repository and click **Projects**.
2. If GitHub shows **New project**, create a new project named `ChatGPT Mission Control`. If the repository tab only offers linking, open your GitHub profile → **Projects** → **New project**, then create it there and link it back to this repository.
3. Choose the **Board** template. Add a second **Table** view after creation.
4. Add the three issues above by searching `repo:lxxlx2/ChatGPT_mission_record` inside the project’s Add item control.
5. Create the custom fields listed above from the project field menu.
6. Set initial issue mapping:
   - #1: System=Archive/Infra, Work type=Backfill, Priority=P0, Status=In progress
   - #2: System=Crypto Daily, Work type=Report quality, Priority=P0, Status=In progress
   - #3: System=Crypto Daily + US Stock Daily (or leave System blank and use Work type), Priority=P1, Status=In progress
7. In Project settings, link repository `lxxlx2/ChatGPT_mission_record` if it is not already linked.

The board should track quality/remediation work. Raw hourly run records and report files should stay in the repository rather than being turned into one Project item per run, otherwise the board becomes unusable.
