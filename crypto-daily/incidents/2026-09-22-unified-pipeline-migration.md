# Crypto unified pipeline migration audit

Date: 2026-09-22
Timezone: Asia/Bangkok
Status: completed

## Scope

The previous Crypto workflow used two active automations:

- formal daily report automation: `6a8600b9d12481919bc43ebc800c9916`
- rolling research automation: `6ab0b7a02d448191a469742b8dea7229`

The workflow has now been consolidated into the formal daily report automation ID, which runs hourly and contains both the research stage and the 09:00 formal-report stage. The former rolling research automation has been disabled.

## Problems found during migration review

1. The pre-migration rolling research task wrote `crypto-daily/research/` files but did not create a matching `crypto-daily/runs/` audit file for every research execution. For example, research files already existed on 2026-09-22 before migration while `crypto-daily/runs/2026-09-22/` did not yet exist.

2. Recent historical formal reports from 2026-09-15 through 2026-09-21 used the earlier section layout. Several also contained internal QA/process text such as classification checks, numbering checks, CA/link QA and zero-selection process notes.

3. The current product requirements now use a different fixed 13-section structure, combine Early/Meme/NFT/new-ecosystem coverage, add a dedicated persistent-trend watchlist section, and keep internal QA out of the user-visible report.

## Repair

The canonical file `crypto-daily/REPORT_SPEC.md` was replaced with a unified pipeline specification effective 2026-09-22.

From the first post-migration hourly run onward:

- one automation performs all hourly research and 09:00 report work;
- every hourly run writes one research file and one run-audit file;
- non-09:00 runs remain silent and do not send Gmail;
- the 09:00 run first completes its fresh scan, then reads at least the previous 24 hours of research;
- the formal report uses the current fixed 13-section structure;
- internal QA/process text remains in run audits;
- the formal Gmail body and GitHub report body must match;
- Gmail and GitHub are both read back before the 09:00 run is marked successful;
- duplicate daily sends are blocked by checking the existing official report and Gmail message ID.

## Historical data policy

Historical Gmail-backed reports are preserved as historical records. They are not rewritten solely to conform to the new 2026-09-22 structure, because rewriting them would break the record of what was actually sent.

The structure and process defects above are recorded here so later audits can distinguish legacy output from post-migration output.
