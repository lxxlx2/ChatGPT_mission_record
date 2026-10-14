# Monster Stage122 — first real Stage99 one-shot failed at Stage105 ASCII market-symbol contract, fixed and two-OS tested

Date: 2026-10-14 Asia/Bangkok; original [Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30). Scope: root cause / data-source model mainline only, NOT a strategy threshold or scheduled job change.

## 1. Actual Mac observed failure from user, not guessed local access

The user actually ran the **original** Stage99 `status` and displayed stdout/stderr log tails. First fixed frozen snapshot time `2026-10-14T06:00:00Z`, launch planned `2026-10-14T05:48:00Z` (Oct14 12:48 Bangkok); local report:

```json
{
  "window": "2026-10-14T06:00:00Z",
  "written_utc": "2026-10-14T05:48:29.963309+00:00",
  "status": "SOURCE_FAILED_NO_BACKFILL",
  "reason": "ValueError:STAGE91_MARKET_SYMBOL_DUPLICATE_OR_INVALID",
  "launchd_plist_exists": true,
  "research_only": true,
  "actual_trades": "NONE",
  "monster": "NO_GO",
  "frank": "UNCHANGED",
  "gmail": "OFF"
}
```

The separately shown .err.log and .out.log files were empty. Mac DID run at the expected time; the program recorded a concrete source validation error. Original two remaining fixed windows `2026-10-28T06:00:00Z`, `2026-11-11T06:00:00Z` still show `SCHEDULE_INSTALLED` and `launchd_plist_exists=true`. **A plist file is not proof of process loaded/running/unloaded**; Oct14 plist true despite SOURCE_FAILED deserves separate authorized local read-only `launchctl print` evidence. No Mac state was changed by this research.

Initial Stage105 code `re.fullmatch("[A-Z0-9]+(?:_[A-Z0-9]+)*",symbol)` returned the ambiguous combined duplicate-or-invalid error. Binance's independently acquired **CURRENT** native USD-M `exchangeInfo` at `2026-10-14T09:08:34.198Z` had five symbols violating that ASCII rule: `币安人生USDT`, `我踏马来了USDT`, `龙虾USDT`, `牛来USDT`, `哈基米USDT`. It contained 927 all exchange entries, 525 active USDT perpetual, so dropping invalid-looking exchange rows is forbidden: it would destroy full market denominator. **We cannot prove which of those five was present in the original 05:48 original HTTPS response**, because no successful source JSON/SHA was saved; the observed failure type and present market prove the code compatibility defect and strongly explain the incident, but not the exact original offending row.

## 2. Frozen approach, code commits, actual patches

- Preregistered development contract at `196e4b83052520be4a41df4cd20d25eb75628750`: `MONSTER_STAGE122_STAGE99_UNICODE_MARKET_SYMBOL_ROOT_CAUSE_FIX_PROTOCOL_20261014.md`. This explicitly marks Oct14 as source-censored, prohibits later refetch and future unreviewed Mac redeploy.
- Stage105 `monster_v4_stage105_capture_universe_core.py` `afb577a85a857f3905e5820f378d0711106ce592`, final tested blob `79472cee0d5b29ed9649b18e25b734a79b0e6935`: accepts exact uppercase ASCII + Unicode Letters/Numbers and legal underscore-separated delivery symbols, rejects spaces/punctuation/format controls/duplicate/paths. Preserves every original USD-M exchangeInfo symbol, SHA256 bytes, original /time proof, fixed time-window, crypto/contract multiplier unknown. Explicit `STAGE91_MARKET_SYMBOL_INVALID` vs `STAGE91_MARKET_SYMBOL_DUPLICATE`.
- Stage38 `monster_v4_stage38_usdm_original_v4_1m_pilot.py` `a7fc5253224b7e7ea32d4101c133fa0a21fa6eb1`, final blob `cf12a3bc9453777b22aa40fcd1a7c6be0e26af4d`: preserves Binance exact Unicode symbol, URL-escapes its UTF-8 name for historical Binance data. Publisher `.CHECKSUM`, SHA256, strict ZIP/CSV member and daily 1440 minute bars remain mandatory. Whether the actual publisher ZIP exists for a specific fresh Unicode name is separately `UNVERIFIED` until official source retrieval, missing=source-censored not a negative opportunity.
- Stage116 `monster_v4_stage116_one_shot_forward_replay.py` `eb535fde5e14a2b19c4fa957e958a627282f5b2e`, final blob `c2dde243f493290e73ffe1e609447296f24e0ce8`: consistent UTF-8 deterministic 24-way hash shard, no name rewriting; original V4/D0 and D1 rule parameters unchanged.
- Test script `test_monster_v4_stage122_unicode_market_source.py`, final blob `c02023daec0a73540797c47cb3a12ed413c56e0f`: literal five current real Chinese names, five source contract/integrity/clock/ZIP/path safety cases, all eight synthetic mixed exchangeInfo symbols preserved, count6 active, separate collision and forged SHA; original Oct14 after-deadline attempted recapture is blocked even with a callable fixture; three fixed future dates stable.
- Offline test workflow `.github/workflows/monster-stage122-unicode-binance-capture-recovery-ci.yml`, blob `d0bf3ef3505cc204276aca1fb1e58e0c99ce4436`: NO schedule, NO live Binance GET, NO Git archive upload, NO launchctl install, no Frank/Monster/Gmail/trading.
- Genuine initial [CI #38543025133](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38543025133) failed TWO synthetic fixture assertions (fixtures listed newly onboarded symbols AFTER synthetic capture minute, and escaped Python JSON raw byte tamper test tried to replace absent literal Chinese string). Fixed **only fixture setup**, source parser and frozen business policy unchanged, at `437f38871743bd74d7bd87d214be807267c2ca87`.
- Reexecuted [CI #38543106703](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38543106703) PASS **both** macOS/Ubuntu. Includes seven focused independent fixtures, Stage97 source and independent Binance time proof, Stage38 publisher ZIP selftest, Stage116 source replay/shard selftest, original Stage99 local Git/launchd no-network isolation tests, Stage102 reviewed-byte consent gate tests. Compiled and ran actual code. This does NOT validate a real future Binance capture or create a new independent other-AI review.

## 3. IMPORTANT: remaining two installed jobs have not been repaired

The prior independent Stage99 review and user installation authorization pinned **eight immutable runtime Git blobs** including the original Stage105 version and original Stage99 launcher. Stage105 is now corrected **in Git on original PR**, but the user's isolated `$HOME/.local/share/monster-stage99-source-capture/repo` retains the old approved executable bytes. The Git fix DOES NOT mutate those local bytes, and running a new clone source with the old Stage102 review receipt MUST fail closed. No new independent other-AI response or new explicit permission to replace existing Oct28/Nov11 macOS launchd jobs has been obtained.

A precise [external independent review request](MONSTER_STAGE122_EXTERNAL_AI_REVIEW_REQUEST_UNICODE_SOURCE_FIX_20261014.md) binds the completed exact tested code and original Stage99 security constraints. Until actual other-AI review returns PASS (with findings addressed) and user expressly authorizes local source+job switch, future installed jobs remain `OLD_CODE_AT_RISK`. In particular: **do NOT call the old `retry-push` for Oct14**: its local state `SOURCE_FAILED_NO_BACKFILL` has no recorded `source_sha256`; an undocumented capture file, if later found, would require genuine original raw receipt verification but not a new Binance GET.

Stage99's `launchd_plist_exists=true` on Oct14 after the scheduled event is noteworthy; simply looking at the file doesn't prove it is still registered. Read-only direct user Mac `launchctl print` and state logs (already provided) are needed to establish actual state before any approved fix/replacement.

## 4. Follow-up handoff / gates

`STAGE122_CODE_FIX=DONE`;
`STAGE122_TWO_OS_OFFLINE_CI=PASS`;
`STAGE122_EXACT_ROOT_SYMBOL_AT_05_48=UNKNOWN_BUT_CODE_DEFECT_VERIFIED`;
`OCT14_REAL_WINDOW_SOURCE=SOURCE_FAILED_NO_BACKFILL`;
`STAGE99_OCT14_AUTO_UNLOAD=NOT_VERIFIED_PLIST_STILL_PRESENT`;
`STAGE99_OCT28_NOV11_EXISTING_INSTALL=OLD_CODE_AT_RISK`;
`STAGE122_NEW_INDEPENDENT_OTHER_AI_REVIEW=NOT_DONE`;
`STAGE122_NEW_LOCAL_CHANGE_PERMISSION=NOT_GIVEN`;
`STAGE122_MAC_FUTURE_RUNTIME_REPLACED=NO`;
`ORIGINAL_519_STAGE118_FAST_MODEL=REJECTED`;
`G0_TRUE_CRYPTO=PARTIAL`; `G4_REAL_EXECUTABLE_NET=UNKNOWN`;
`MONSTER_DEPLOY=NO_GO`; `FRANK_UNCHANGED`; `GMAIL_AND_AUTOTRADE=OFF`.

Next highest-value step: real independent reviewer of the exact tested source; fix its findings and re-test; prepare a narrowly scoped, fully auditable local user-consented replacement of **only** the remaining two Stage99 one-shot jobs while avoiding touching Frank and respecting original review binding. The 2026-10-14 source window remains explicitly censored; continue independent Monster market mainline without pretending its missed source is OOS loss.
