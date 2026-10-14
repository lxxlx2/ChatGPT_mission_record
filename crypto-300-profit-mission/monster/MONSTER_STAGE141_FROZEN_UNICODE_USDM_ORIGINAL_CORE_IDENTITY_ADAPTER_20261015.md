# Monster Stage141 — frozen Unicode symbol coverage without changing original V4 D0 or Stage80 D1

Date: 2026-10-15 Asia/Bangkok. Same existing Draft PR #30. Frozen BEFORE implementation or tests. This directly resolves real-market observed source-to-model coverage, not new signal thresholds or historical optimization.

## Actual observed population gap

The original 2026-10-14T17:52:47.096Z Stage140 recorded 525 TRADING USD-M USDT perpetual instruments. Exactly FIVE original venue names contain Unicode characters: 哈基米USDT, 币安人生USDT, 我踏马来了USDT, 牛来USDT, 龙虾USDT. The original V4 D0 production shadow code rejects non-ASCII symbols at observe_snapshot; Stage137 previously labelled complete-source Unicode as MODEL_SYMBOL_UNSUPPORTED_NOT_A_NO_WATCH. These five are in original G0 attempts, not supposed to vanish.

## Frozen implementation

1. For ISOLATED OFFLINE original V4 D0 SQLite only, map exact UTF8 original market IDs to deterministic uppercase 32-hex SHA256 ASCII proxy with fixed prefix/suffix USDT, with collision checks over FULL original population and with real ASCII originals. ASCII stays unchanged. Original production source Git blob bc958b3d90a8a52afa51515cb53f7e5fafaffaaa and Stage80 D1 contract SHALL NOT CHANGE, nor numeric prices, candles, quote volumes, original UTC tick timing, WATCH limits, gross HIGH labels or full population denominator.
2. Only original V4 D0 observe_snapshot/process_queue isolated SQLite sees proxy identity. Original Binance source filenames/download names remain exact UTF8; Stage80 D1 and outward results always retain original exact venue symbol; no alias ever sent to Binance REST, official publisher, order books, notifications or trades. Explicit status ORIGINAL_V4_NUMERIC_CORE_WITH_UNICODE_IDENTITY_ADAPTER_CAUSAL_OFFLINE, source_core_unicode_adapter_used true; do not falsely label as unchanged original symbol identity. Original full source incomplete => CENSORED, in-window issuer-unverified new listing => unsupported still, not a negative case.
3. Stage138 must accept the new isolated adapted status as source-compatible while retaining historical stage137 status values and old report snapshots intact. Add actual Stage140 saved 525 original venue list to collision and count test, synthetic Unicode 11520-minute true old D0 WATCH and Stage80 D1 replay equivalence compared against unchanged ASCII using identical time-series and exact label times; keep original core blob pin, SHA source and default NO_GO.
4. Actual integrated macOS and Ubuntu tests; formal report and development cadence update. No new background source collection or market fetch. This is an engineering coverage fix, not crypto issuer proof, G1 forecast validation, net executable PnL, other AI review or deployment permission.

Freeze status: STAGE141_CODE=NOT_DONE, REAL_STAGE140_UNICODE_POPULATION=FIVE_CONFIRMED, ORIGINAL_V4_CORE_BLOB=FROZEN_UNCHANGED, G0=PARTIAL, G1=NOT_SCORABLE, G2_G3=NOT_PASSED, G4=UNKNOWN, G5=NOT_DONE, G6=NO_GO, FRANK=UNCHANGED, GMAIL=OFF, NO_NEW_SCHEDULE. Original Stage116 failed initial source, Stage118/127 REJECTED and Stage132 negative BUY economics remain unchanged.
