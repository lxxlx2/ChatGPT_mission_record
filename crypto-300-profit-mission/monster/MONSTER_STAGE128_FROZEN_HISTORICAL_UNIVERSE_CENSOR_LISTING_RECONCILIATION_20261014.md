# Monster Stage128: predeclared historical-market censor and listing-boundary reconciliation

Research-only; existing Draft PR #30. Date: 2026-10-14 Asia/Bangkok. This contract is frozen before the new Stage128 code/CI and final machine evidence.

## Purpose, provenance and hard separation

Original Stage93 already reported 5,400 USD-M venue-symbol/date attempts (6 original 7-day anchors × 900 archived symbol names), 3,283 full official 1m causal results, 2,117 source-censored, 51 source-complete 2x, and 48 early5 original D0. Its 48/51 is only *exposed source-complete* gross futures HIGH discovery, not G1 full market crypto, and not actual executable net. Do not re-tune old D0/failed Stage118/127 priority, and do not change any old outcome.

Stage37 historical SOURCE is publisher-SHA-validated *monthly hourly* census of the 900 ex-post symbol roster, file `evidence/monster_stage37_sixdate_all5400_usdm_source_and_GT.csv`, Git blob `4b02019195a7a48ef6d33606db9b57d6a3429f4b`. This is NOT a point-in-time venue-eligibility list. Stage123 archived **2026-10-14 09:48:24.840Z** USD-M exchangeInfo includes `onboardDate`, but is a **later metadata snapshot**; it is not 2025/2026 official exchangeInfo captured at the historical anchors. Stage123 files + manifest are archived in `monster/evidence`, validated by the existing Stage124 full-source loader.

## Frozen deterministic audit

For every one of Stage37's exact 5,400 `(date,symbol)` rows, compare with Stage123 archived exact `symbol`, no spelling, prefix or underlying-unit normalization. Verify exactly six specified 7-day UTC06 windows × 900 distinct symbols, 927 current exchangeInfo items, Stage37 3,333 hour-complete vs 2,067 hour-incomplete, and Stage93 3,283 1m-complete / 2,117 censored / 51 2x / 48 early5, where hourly complete minus minute complete equals 50 = 47 hourly-vs-minute publisher price conflicts and 3 official 1m gaps.

Segment **hourly-incomplete** 2,067 symbol/dates based solely on later snapshot (NEVER auto-exclude):
- `LATER_METADATA_ONBOARD_AFTER_7DAY_END`,
- `LATER_METADATA_ONBOARD_INSIDE_7DAY_WINDOW`,
- `LATER_METADATA_ONBOARD_AT_OR_BEFORE_ANCHOR`,
- `ABSENT_FROM_LATER_METADATA`.
Separately enumerate hourly-complete symbol/dates with `LATER_METADATA_ONBOARD_AFTER_ANCHOR_CONTRADICTION` or `ABSENT_FROM_LATER_METADATA`. Every cohort must be retained, with all per-day and total counts, and listing-window examples with exact event dates.

The timestamp bins use UTC anchors at `06:00Z` and end exclusive at anchor+7 days, comparing integer milliseconds. A valid later `onboardDate` must be a positive nonbool integer; if absent/invalid return `LATER_ONBOARD_UNKNOWN`, not "never listed". The later source's `serverTime` is not capture authenticity; the full Stage123 manifest source is the only reference. Never infer precise historical exchange eligibility, crypto issuer, active per-minute venue status, completed trades, no-opportunities, or confirmed delistings from current onboarding, and do not silently move missing cases into negative returns.

Reports preserve all Stage93 verified winner misses unchanged: CETUS late, PENGU no WATCH, F same minute. No modification to Stage77 G0–G6 numeric targets; G0 and G1 remain incomplete. Treat Stage37 missing source as distinct from **actual tradability**. In-window future onboarding from a later snapshot is a *research lead*, not independent source proof of a new listing.

## Acceptance

Code parses complete source archive offline, validates exact census/source classifications, reconciles each 900/date with Stage93, produces summary + actionable listing-research exception list and excludes no symbols from the old population. Synthetic source corruption, altered Unicode symbol, missing metadata and contradiction tests + a real 5,400 source-read in Ubuntu/macOS Actions, with no network, no schedule, no emails or orders. Archive machine findings and report failing assertions without modifying frozen sample/threshold.

`MODEL_STAGE118=REJECTED`; `MODEL_STAGE127=REJECTED`; `G0=PARTIAL`; `G1_NEW_OOS=NOT_SCORABLE`; `G4=UNKNOWN`; `OTHER_AI_REVIEW=NOT_DONE`; `MONSTER_DEPLOY=NO_GO`; `FRANK=UNCHANGED`.
