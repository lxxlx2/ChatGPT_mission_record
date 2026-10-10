# Monster V4 Stage6 — independent other-AI review request (NOT YET REVIEWED)

Status: REVIEW_REQUEST_PREPARED. Do not infer independent AI review success merely from this artifact, a CI pass, or implementer self-audit. Attach reviewer name/model, exact reviewed commit SHA, observed findings, severity, fixes, re-review evidence, and tool provenance when an actual independent reviewer completes the audit.

## Review scope (do not modify unrelated Frank modules)

Current PR: https://github.com/lxxlx2/ChatGPT_mission_record/pull/30

Core changed files:
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_shadow.py`
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_d2.py`
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_d2_evidence.py`
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_mac_service.py`
- `crypto-300-profit-mission/local-agent/tests/test_monster_v4_shadow.py`
- `crypto-300-profit-mission/local-agent/tests/test_monster_v4_d2.py`
- `crypto-300-profit-mission/local-agent/tests/test_monster_v4_mac_service.py`
- `crypto-300-profit-mission/monster/MONSTER_STAGE6_D2_SPOT_EXECUTION_AND_MAC_SHADOW_20261011.md`
- `crypto-300-profit-mission/monster/evidence/monster_stage6_spot_orderbook_3symbol_20261011.json`
- `crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md`

## Priority questions (must answer with exact code lines / repro, not general compliments)

1. Can a full-market or partial-market Binance snapshot create phantom WATCH alerts because timestamps are nonmonotonic, rows cross venues, exchangeInfo is incomplete, or rolling 24h quoteVolume was confused with 3m volume? Are there legitimate gradual-rise cases missed by the 3m/15m/60m windows? Check 75m snapshot history TTL and first-snapshot baseline.
2. Do the WATCH dedup/cooldown, invalidation/rearm, stale queue, retry and D1 closed 5m checks preserve causality and avoid silent drops or duplicate notification events after crash/restart?
3. Is D1 `SETUP_ACTIVE` truly connected to persistent `d2_reviews` with correct spot vs futures classification, stale cutoff, constrained request rate and failure recovery? Could an invalid or delayed D2 quote still produce a false executable recommendation?
4. Is the D2 30 USDT buy→immediate sell depth sweep mathematically sound with Binance `MARKET_LOT_SIZE`, `LOT_SIZE`, `NOTIONAL`, tick size, 100 levels, quantity rounding and buying/selling fees? Is it clearly distinguished from real fills/profit forecasts? Verify actual frozen TST/BROCCOLI714/BTC sample output and extremes.
5. Does the Mac LaunchAgent installer isolate Frank and preserve rollback data, including existing Label collisions, symlinks, root paths, restart behavior, Python binary path, release hashes, existing deployed version upgrades and launchctl failure? Could service run without being recognized as unhealthy when both venues fail?
6. Does the runtime actually deliver WATCH early enough for a profitable workflow, or is the threshold false-positive density still unknown? Check all claims in docs versus CI result: no live mail, no local machine proof, no automatically authorized trading.

## Review acceptance criteria

- Produce severity-ranked findings with exact file/line references and concrete minimal reproductions or fixture tests.
- Identify at least one empirical missing-evidence risk and at least one engineering failure scenario, even if code has no blocking bug.
- Explicitly distinguish `BLOCKER` / `MAJOR` / `MINOR` / `TEST_OR_EVIDENCE_GAP`.
- Run available offline tests or cite accurate CI SHA; cannot fabricate a test run.
- Submit independent actual review comment or separate evidence artifact with reviewer identity and timestamp. Only then change `NOT_YET_REVIEWED` to reviewed; implement and test remediation before Mac production alert activation.

## Current context

Latest reviewed baseline before Stage6 was `bb124b605a925b76bccbcdc47abb6fb3b0c5fcbe`. All post-baseline Stage6 commits remain on PR #30, not merged. CI passes synthetic + frozen historical tests, not a forward live trading study. Public Binance live snapshot is a frozen, non-atomic three-symbol book sample. `PRODUCTION_TRADING=NO_GO`, mail `DRY_RUN_ONLY`, Mac run unverified.
