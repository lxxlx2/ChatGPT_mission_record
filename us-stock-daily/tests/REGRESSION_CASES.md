# US Stock Daily Regression Cases

Updated: 2026-09-29

| ID | Fixture | Expected |
|---|---|---|
| STK-01 | Normal active market day with all primary sources reachable | complete 12-section report |
| STK-02 | One secondary source unavailable | full report still produced; missing fact replaced or omitted conservatively |
| STK-03 | 07:00 prebuild exists but is below quality-collapse threshold | QA_FAIL; rebuild missing coverage before send |
| STK-04 | 08:00 Gmail send succeeds, GitHub archive fails | delivered; later archive-only recovery; no duplicate email |
| STK-05 | 08:00 Gmail send fails, complete pending body exists | retain same body; 09:00 recovery sends full report |
| STK-06 | Recovery body is a 9-item summary instead of 12 sections | QA_FAIL; cannot become official |
| STK-07 | Same-day full official Gmail already exists | no duplicate normal send |
| STK-08 | Company/market claim has only weak attribution | do not state causal conclusion as confirmed fact |
| STK-09 | Weekend/holiday with no new US cash session | still use latest completed session + current macro/news; low-event exception must be documented |
| STK-10 | Active private-market deal has no user-rights change | generic company news may be research, not user-rights action |
| STK-11 | Gmail final body and GitHub body differ | not fully delivered; repair GitHub body only |
| STK-12 | Body length or numbered-item count <70% trailing-5 median without genuine low-event reason | QA_FAIL |

Pass requirement: 12/12.
