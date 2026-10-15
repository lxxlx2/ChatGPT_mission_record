# Oct 15 TGE discovery + notification regression — Surf / StandX
Status: SPEC_AND_TRACE_VERIFIED; FUTURE_UNATTENDED_RUN_PENDING
Timezone: Asia/Bangkok
Scope: existing hourly HH:00 rights monitor, existing Registry only
No tasks/schedules/names or extra notification channels added.

## Actual historical evidence
- 2026-10-15 04:00:28 `runs/2026-10-15/040028-final.md`: shard0 did check StandX home and concluded no newly dated ACTION; this was BEFORE the Oct15 shutdown announcement broke in the afternoon. This particular scan is not itself an omission of a future publication.
- 2026-10-15 09:13:25 `runs/2026-10-15/091325-final-retry.md`: urgent and shard1 scanned Surf but classified SOURCE_GAP due to inaccessible claim JavaScript and without finding issuer primary blog; 0 ACTION/no email. The official issuer blog `https://asksurf.ai/blog/en/surfboard-nft-launch` (published Oct15) establishes claim starts 03:00 UTC (10:00 BKK), eligible annual Pro/Max purchased before Sept16, 30-day claim ending Nov13. No proof that the blog was online at 09:13; correct failure is absence of verifiable pre-open eligibility/deadline lead and immediate post-open fresh discovery/delivery, not an invented 09:13 missed accessible final blog.
- There is no TGE actual final after 09:13 in the inspected Oct15 directory as of this manual correction. No proof that a 12:00 shard0 check ran or saw the new StandX shutdown statement, so do not call it a verified later successful scan.
- StandX official X new posts linked `https://x.com/StandX_Official/status/2110613283967230232`, `https://x.com/StandX_Official/status/2110613379270185114`. Search indexes and an English translated news story describe staged venue shutdown, native-token cancellation, DUSD giveaway and phased withdrawal/redemption deadlines, but actual first-party X full text was inaccessible in manual verification. Exact UTC deadline milestones remain a SOURCE_GAP until first-party direct text or an official English blog can be read.
- User reported Surf App alert after launch, no Gmail. In configuration TGE App notifications are OFF; all inspected TGE Oct15 finals have zero ACTION and zero Gmail attempted. We cannot recover the provenance of a displayed App push from Git or the automations settings alone; no proof the specific push originated from the same task. App is NOT authoritative delivery.
- Manual user-requested recovery (separate from scheduled success): Surf Gmail Sent `1a13e676f3e4e04d`, exact archived `reports/events/2026/2026-10/2026-10-15/1409-surf-surfboard-member-claim.md`; StandX Gmail Sent `1a13e6930e07d0ae`, exact archived `reports/events/2026/2026-10/2026-10-15/1410-standx-winddown-dusd-airdrop.md`. Unchanged messages permanently deduped in `state/known-events.md`.

## Root causes and corrected behavior
1. FIRST-PARTY FALLBACK: Do not mistake JS claim-app read failures for unavailable issuer first-party content; search issuer English dated blog/FAQs and source index; `asksurf.ai/blog/en/surfboard-nft-launch` is a qualifying Tier A.
2. CROSS-SHARD EMERGENCY: Every existing hourly pass does a bounded first-party/English lifecycle HEADLINE sweep for EXISTING Registry projects (halt, refund, closeout, reduce-only, deposits, withdrawals, claim and eligibility launches), independent of single deep-shard rotation. A material StandX shutdown can be discovered without waiting 4h for its next Shard0. This is one bounded batch of discovery, not a second full deep shard.
3. ACTION STATE DIFFERENCE: New SurfBoard NFT member claim is a separate stable key from September Surf referral claim. Existing user relevant annual membership population warrants a claim eligibility check reminder, but user's personal qualified NFT count is unverified. StandX one-time DUSD airdrop must not be represented as approved native token TGE.
4. NOTIFICATION DELIVERY: Only actual Gmail Sent/readback + Git archive counts as a delivered rights action. App prompt/visible output cannot substitute, regardless of whether app platform displayed Surf in some separate UI; task settings remain disabled. NO_ACTION silence.
5. TIMELINE: Never claim an earlier scan should have seen a document published later, nor a blog existed at 09:13 when its exact issuance time is unknown. Keep first_seen and source published times separate. A partial final is not complete coverage.
6. SOURCE TIERS: Missing direct StandX X text is retained as SOURCE_GAP; the risk email disclosed this gap, did not invent user's individual allocation or guarantee DUSD convertibility. Further exact dates must be first-party checked.

## Acceptance scenarios
| ID | Input | Expected behavior | Current result |
|---|---|---|---|
| TGE-20261015-1 | Surf JS app unreachable, official issuer dated article accessible | Read blog, identify open claim, eligibility and deadline, create material ACTION | Spec repaired; needs live verification |
| TGE-20261015-2 | Surf referral already mailed Sept12; new SurfBoard member Claim opens Oct15 | Distinct stable event key, no erroneous suppression | Confirmed manual email + dedupe |
| TGE-20261015-3 | StandX material venue shutdown posted AFTER 04:00 shard0 while other shard scheduled | Bounded cross-shard discovery surfaces it urgently, protected fund withdrawal advice | Spec repaired; needs live verification |
| TGE-20261015-4 | DUSD giveaway, no official platform native token | Distinguish DUSD from a StandX native TGE | Correct in recovered email |
| TGE-20261015-5 | Direct X first-party body unreadable | Keep milestone source gap; clearly classify secondary text | Correct in recovered email |
| TGE-20261015-6 | User sees an App notice but Gmail Sent absent | Classify not delivered; attempt Gmail once with complete action evidence | Confirmed manual email |
| TGE-20261015-7 | Existing stable key already delivered | Suppress unchanged reminders, only re-alert on new official material delta | Keys saved, live test pending |
| TGE-20261015-8 | Historical attempt-only run | Never invent or count as verified full coverage | Spec retained |

Next actual hourly TGE run must be checked for: source_receipts, bounded cross-shard material lifecycle discovery, correctly differentiated Surf/StandX stable keys, Gmail dedupe, honest partial status, and no App-generated ACTION proxy. Production PASS requires future actual evidence; Git writes/prompt updates alone are not proof.