# Oct 15 three-monitor incident: both daily deliveries + Surf, StandX rights
Report timezone: Asia/Bangkok
Task changes: three existing enabled tasks; only TGE task prompt updated in place; names/hours/recipient/scope unchanged.
Current status: 4 MANUAL USER-REQUESTED EMAILS VERIFIED DELIVERED; scheduled Gmail write reliability UNRESOLVED.

## Evidence of initial absence and automation failure
- Gmail Sent search after Oct14 before recovery: no Oct15 formal US Stock or Crypto Daily and no recent Surf/StandX action alert.
- Crypto Oct15 08:19 prebuild had in-memory content and pending; Oct15 10:18 final-retry and 11:18 final-retry confirmed full 13-section attempts but Gmail blocked by OpenAI tool safety checks, zero official email id. Hourly 03:20 and 06:20 attempts missing finals; 12:16 attempt has no final in checked run directory. Task still ENABLED with 09:20 primary/10:20,11:20 recovery schedule.
- US Stock Oct15 Git pending /us-stock-daily/delivery-pending/2026-10-15.md existed and STK QA-PASS, but initial 06:40 update blocked and 08:40 only an attempt without terminal final; no Gmail Sent until user-requested manual recovery. Task ENABLED with normal 07:40 primary / 08:40 recovery schedule.
- TGE 2026-10-15 04:00 shard0 checked StandX site with no new announcement yet; do not pretend it could have known an afternoon post. 09:13 shard1 classified Surf eligibility as SOURCE_GAP; inability to parse JS app was treated as absence of authoritative actionable content, while official issuer's dated English blog provided a complete eligibility/claim-open source once published. Later StandX headline was missed across non-shard hours, and 12:00 actual run has no observed final as of audit. App push reported by user, but provenance is unavailable and notification settings for existing task disabled; no Gmail and no proven actionable event in scheduler records.
- StandX official X URL observed but full first-party text inaccessible; precise withdrawal/airdrop milestone hours based on second-hand English translation require Tier A re-verification. Cannot claim personal holding or allocation checked.

## Actually delivered manual email proof (exact Gmail Sent+readback+identical Git)
| Kind | Gmail ID | Canonical |
|---|---|---|
| SurfBoard member claim opened 10:00 BKK Oct15 (annual membership eligibility; Nov13 deadline) | 1a13e676f3e4e04d | airdrop-tge-monitor/reports/events/2026/2026-10/2026-10-15/1409-surf-surfboard-member-claim.md |
| StandX shutdown / DUSD community airdrop risk, official link full text SOURCE_GAP | 1a13e6930e07d0ae | airdrop-tge-monitor/reports/events/2026/2026-10/2026-10-15/1410-standx-winddown-dusd-airdrop.md |
| US Stock formal 12 sections, 63 items, latest Oct14 US session | 1a13e6a5b42b17ac | us-stock-daily/reports/daily/2026/2026-10/2026-10-15.md |
| Crypto formal 13 sections, 57 items, Binance Spot Oct15 14:15 BKK + Surf and StandX | 1a13e6c2913e845b | crypto-daily/reports/daily/2026/2026-10/2026-10-15.md |

Every item checked via Gmail read_email, SENT label, recipient, and Git readback exact body equality; no same-day duplicate reported.

## Durable corrections
- State and dedupe updated `airdrop-tge-monitor/state/known-events.md` commit c77ba19b651acb2104b04c2795740b22f613ec6a, separate from old Surf September referral.
- TGE state updated latest observed scheduled terminal at 09:13 partial, with manual deliveries clearly separate; commit f959e920e4ec5517fd3c2e84cd3fca51a44f8c2d.
- Runtime 7393bfe424cdab0e7e7169fb438635cdf7632f89 / spec 56e4dc71207f07a551bd0eaaa3e98838c16b227d: first-party blog/FAQ fallback for dynamic JS app, bounded lifecycle cross-shard headline discovery for projects already in Registry, emergency venue closure, explicit Gmail-only authority.
- Existing hourly TGE task prompt updated IN PLACE without schedule changes. Regression specification: `airdrop-tge-monitor/tests/2026-10-15-surf-standx-regression.md`, commit c18f3c1340b260c588d6aab9d6ecbc3a0f73e2dd.
- Safety-check blocking actual causes opaque and are NOT fixed by manual email success. Future scheduled runs must demonstrate independent source receipts and Gmail Sent/readback+Git equality; avoid workaround or unapproved extra tasks.

## Operational action
- No more same-event Surf/StandX alerts. Only verified new material changes: StandX official eligibility open Oct26, claim open Nov1, changed exit schedule, or Surf membership deadline/claim route changes, after primary verification and Sent dedupe.
- For StandX held DUSD/LP/Vault/perps, protect real capital first, re-verify official closeout steps and deadlines. Never treat cancellation of original token as TGE success; no claims about user allocation.
- Normal Crypto/USStock future reports still face scheduled Gmail safety check risk. Manual recovery success doesn't prove fixed. No reminders created, no app push substituted for Gmail.
