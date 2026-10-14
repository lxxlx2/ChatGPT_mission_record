# Stage122 — Independent other-AI review request (Claude/Codex CHAT, not self-review)

Scope: original Mission Monster PR #30 research branch, exact code under initial tested commit `437f38871743bd74d7bd87d214be807267c2ca87`. Original one-shot Stage99 reviewed code remains installed and unchanged. Do NOT install/activate/change any Mac LaunchAgents as part of review.

## Evidence for reviewer

User actual Mac Stage99 Oct14 05:48:29Z state: `SOURCE_FAILED_NO_BACKFILL`, `ValueError:STAGE91_MARKET_SYMBOL_DUPLICATE_OR_INVALID`; `launchd_plist_exists=true`; no Git evidence snapshot for Oct14. The existing Stage105 input validator accepted only `[A-Z0-9]+(?:_[A-Z0-9]+)*`. A separate Binance CURRENT 2026-10-14 09:08:34 UTC USD-M `exchangeInfo` response contains **five** Unicode symbols: `币安人生USDT`, `我踏马来了USDT`, `龙虾USDT`, `牛来USDT`, `哈基米USDT`. Because no original Oct14 05:48 raw exchangeInfo was archived, the *exact* offending symbol in the old Mac response is not independently proven; do not invent it. Need evaluate root cause with this evidence distinction and scrutinize no post-window backfill rule.

### Exact files to review by their tested git blob IDs

- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage105_capture_universe_core.py` blob `79472cee0d5b29ed9649b18e25b734a79b0e6935`: new `valid_exact_venue_symbol`, raw population completeness, duplicate and invalid split, excludes path/control chars, preserves Unicode exact identifiers.
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage38_usdm_original_v4_1m_pilot.py` blob `cf12a3bc9453777b22aa40fcd1a7c6be0e26af4d`: urlencode exact UTF-8 name only for Binance publisher 1m ZIP archive URL; ensure reader keeps original ZIP CSV member, all SHA receipts, never substitutes missing data.
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage116_one_shot_forward_replay.py` blob `c2dde243f493290e73ffe1e609447296f24e0ce8`: deterministic 24-shard hash now UTF-8, source completeness and no double count.
- `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage122_unicode_market_source.py` blob `c02023daec0a73540797c47cb3a12ed413c56e0f`: 7 synthetic fixture scenarios using 5 real current venue names, under 3 fixed windows; preserved original body SHA, independent Binance-time, no historical recapture, negative name tests.
- `.github/workflows/monster-stage122-unicode-binance-capture-recovery-ci.yml` blob `d0bf3ef3505cc204276aca1fb1e58e0c99ce4436`.
- Original installed launchd orchestration remains unchanged: `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py` blob `2543c2547366867bcb3aa002479fd46c7f83f683`.
- Original Stage97 independent time capture remains unchanged: `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage97_one_shot_usdm_capture.py` Git blob `1d4fb2dffed821850b94b9780a9bf83be13904ae`.
- Original Stage102 installed-review binding still cryptographically checks Stage105 **original** blob and user authorization; a new changed Stage105 breaks prior review by design.

## Actual tests to inspect

- Initial new [Stage122 CI #38543025133](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38543025133) `FAILURE`: two **synthetic test-fixture** errors (source fixture Chinese symbols listed after synthetic capture time, byte-tamper test attempted to replace raw UTF8 visible characters while Python JSON fixture was escaped Unicode). NO production strategy or source code relaxed to pass these; fixture corrected `437f388...`.
- Final [Stage122 CI #38543106703](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38543106703) `SUCCESS`: macOS and Ubuntu genuine code execution of seven focused tests, Stage97 publisher/clock verifier, original Stage38 and Stage116 regressions, Stage99 core and original independent chat-review permission gate tests, Stage99 standalone local Git worktree and import isolation. **No real external Binance 05:48 raw file was verified** by this offline suite.

## Review questions requiring genuine criticism

1. Can the old Stage105 regex fail on the above real Unicode symbols despite the exact Mac logs not preserving offending raw bytes? Is the proposed Unicode Letters/Numbers + ASCII-uppercase policy too permissive/restrictive for real Binance USD-M full universe? Any tricky Unicode normalization collisions, unsafe ZIP member, path traversal, empty _ or control chars?
2. Does Stage38 `urllib.parse.quote(symbol,safe="")` match the official data.binance.vision ZIP object hierarchy and checksum URL retrieval for Unicode symbol names? If not independently verified live against publisher, mark `SOURCE_AVAILABILITY_UNKNOWN`, never claim it works just from a fixture. Does the current code treat 404 as censored without fabricating negative symbol outcomes?
3. Does UTF-8 shard hash preserve deterministic total population, exact once-only model evaluation and causal 1m admissions? Check compatibility with originally fixed sharding/previously archived date data.
4. Does the Stage97 verified raw response still require original authenticated Binance /fapi/v1/time before and after; does Stage105 accept only the full exact source and preserve crypto/TradFi/multiplier UNKNOWN instead of silently treating a name as crypto?
5. Is it correct that first Oct14 window is permanently source-censored in absence of a locally saved SHA? Are there signs of still-present old Oct14 LaunchAgent plist requiring *separate* local read-only `launchctl` verification / eventual user consent to cleanup?
6. **Approval and deployment boundary:** The old Stage102 review fingerprint pins original Stage105 file, so newly developed Git code is NOT covered by the prior user install consent. Check whether any script or workflow accidentally bypasses source and review gate, starts a new scheduled task or does an unauthorized Mac install. Future Oct28/Nov11 user-installed jobs remain old unless a fresh independent reviewed and separately approved local replacement.
7. Most importantly, explain whether this is a genuine mainline data capture blocker fix rather than repeated low-value edge-case work; do not claim new model economic success.

Please provide actual reviewer model/identity; exact source reviewed Git SHA+file blobs; verdict PASS/REQUEST_CHANGES; concrete findings with file/function/line or repro; proposed fixes; and independent test instructions or independent test output. This prompt itself is **NOT** a completed other-AI review, and all real deployment gates remain NO_GO.

`REQUEST_PREPARED`, `REVIEW_OUTPUT_NOT_RECEIVED`, `NO_MAC_CHANGE_AUTHORIZED`, `OCT14_SOURCE_CENSORED`, `FUTURE_WINDOW_MAC_OLD_SOURCE_RISK`, `MONSTER_DEPLOY_NO_GO`.
