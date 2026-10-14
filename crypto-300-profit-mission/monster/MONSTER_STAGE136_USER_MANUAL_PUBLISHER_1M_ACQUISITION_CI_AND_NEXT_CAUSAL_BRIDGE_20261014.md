# Monster Stage136: reusable manual publisher source acquisition client, actual two-platform CI, next real causal-runner gap

2026-10-14 Asia/Bangkok; existing [Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30), same research branch. This delivery is a genuine Stage135 source-acquisition capability, not a new trading strategy or new market T0. **No real user-triggered Stage133 T0 or Stage136 live Binance download occurred in this development pass**.

## 1. Prior frozen agreement and deliverables

Frozen **before implementing** at commit `1c5143b5dd2afe142fda4bad7d057266cc8bbb1f`: [Stage136 manual source protocol](MONSTER_STAGE136_FROZEN_MANUAL_PUBLISHER_ARCHIVE_ACQUISITION_PROTOCOL_20261014.md).

- [Stage136 Python archive client](../local-agent/scripts/monster_v4_stage136_manual_publisher_archive_acquisition.py), commit `cf64fb23860ef5080e62bbaa243ed075ad049486`. It first revalidates the complete Stage133 original three-receipt packet and Stage134 population, then plans exactly each Stage135-required symbol/date 1m daily Binance Data Vision ZIP and original `.CHECKSUM`. In the offline default `--t0 --archive-root --out`, no network request or archive write is made.
- Official historical ZIP acquisition requires `--fetch-manual --capture-request`, with the explicit user one-shot authorization schema and true flags; caller must additionally have a real authorizing user chat instruction. The code rejects acquisition before the exact frozen forward seven-day end + a conservative 48-hour readiness margin (not a claimed Binance archive publication SLA). No recurrence, cron, launchd, workflow schedule, Gmail or order entry is installed.
- For each frozen symbol/day, existing ZIP+CHECKSUM data are revalidated by Stage135 and reused. Missing pairs can be fetched using unchanged Stage130 official URL and parser, original publisher checksum SHA256, actual one-minute CSV validity; successful bytes are staged and saved to Stage135's `<archive-root>/<symbol>/<YYYY-MM-DD>.zip[.CHECKSUM]`. A configured per-run budget plus re-run reuse permits resume. A 404/transport-unavailable item stays `SOURCE_UNAVAILABLE`, does not become no-WATCH/negative; corrupt existing/invalid checksum raises an error with evidence retained.
- Exports **complete source plan and outcome** including all original T0 symbols and unverified in-window admission candidates, expected symbol-day count, SHA receipts, reused, newly fetched, unavailable and pending sources. It **never** labels 7-day complete market, issuer identity, point-in-time liquidity, G1 forecast accuracy or profit as PASS. No user notional is assumed.
- [Eight offline unit/integration tests](../local-agent/scripts/test_monster_v4_stage136_manual_publisher_archive_acquisition.py) commit `d586e0fbe6dfda9a51bcba6563b3505dd5f9acbc`; [isolated push/PR/manual-dispatch CI](../../.github/workflows/monster-stage136-manual-publisher-acquisition-offline.yml), commit `414dbb119e0ccd7dd3f3df6a9e436583ea5e76cf`. CI is **synthetic** with locally generated ZIP/CHECKSUM and injected GET, no live Binance official data acquisition.

## 2. Independent GitHub machine tests, factual

[Stage136 GitHub Actions #38596558021](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38596558021), fixed code SHA `414dbb119e0ccd7dd3f3df6a9e436583ea5e76cf`, push trigger, `completed/success`.

- macOS job `115964677414`: **8/8 PASS**, Python compile PASS, default unauthorized live-GET reject and no scheduler source path PASS.
- Ubuntu job `115964679209`: **8/8 PASS**, same checks PASS.
- Tests include all synthetic three T0 venue symbol * nine publisher day **27 source attempts** without winner filtering, UTF-8 URL, offline no side effects, double manual authorization and time gate, official ZIP+CHECKSUM exact saved byte re-read, resuming valid files, rejecting malformed existing source and checksum mismatch without committing bad archives, 404 remaining unavailable, and offline CLI acceptance. These numbers describe **test fixtures only**. They do not describe real Binance market or current crypto opportunities.

## 3. Important discovered remaining mainline incompatibility

The archived original Stage91/Stage38 replay contract is bound to **three original frozen Stage105 dates** and Stage38 `dayT06:00:00Z`, while genuine Stage133 future T0 is a new dynamically derived 5-minute UTC boundary after its actual capture. Consequently a Stage133 06:20 style T0 cannot simply be passed to original Stage91/Stage116 as an approved causal replay. **Do not rewrite the original Stage116 dates or bypass its failed first window**. A separate contract/code path must replay exactly the unchanged archived D0/D1 core on **dynamic newly frozen starts**, retaining every full-market candidate, verified minute source/censor, timing, time labels and out-of-scope issuer flags. Also the archived `monster_v4_shadow.observe_snapshot` checks ASCII-only market symbol IDs while Stage133 original Binance ExchangeInfo and Stage131 population explicitly retain valid Unicode symbols; these may be censored/unsupported for old runner and cannot silently disappear from the new denominator or be reported as successfully scanned.

This is the **next highest-priority functional work**, before more trading signals or historical parameter tweaks: implement and test the dynamic-clock full-market causal D0/D1 replay adapter, with explicit old-core-compatible versus unsupported population and no falsely claimed 1m real alert delivery. Then actual future post-window original verified one-minute data may be processed through Stage135 + this causal adapter and frozen G0-G3 metrics, with true crypto identity still requiring source proof.

## 4. Original gates and user authority unchanged

New Stage133 genuine T0: `NOT_DONE`; genuine unseen fully covered three nonoverlapping forward windows, >=20 independent verified crypto 2x opportunities: `NOT_AVAILABLE`. Stage118/127 remain REJECTED and Stage132 new-listing first-momentum immediate BUY historical fixed exits remain NEGATIVE. Old Oct14 06:00 UTC Stage116 immutable source `SOURCE_FAILED_NO_BACKFILL`. Independent other AI review NOT_DONE, no Mac installed, no real user-facing Monster Gmail, no live trading, no changes to Frank.

`STAGE136_CODE_COMMITTED=DONE`; `STAGE136_MACOS_UBUNTU_CI=PASS`; `STAGE136_REAL_OFFICIAL_ARCHIVE_FETCH=NOT_DONE`; `G0=PARTIAL`; `G1=NOT_SCORABLE`; `G2_G3=NOT_PASSED`; `G4=UNKNOWN`; `G5=NOT_DONE`; `G6=NO_GO`; `FRANK=UNCHANGED`; `GMAIL=OFF`; `NO_NEW_SCHEDULE`.
