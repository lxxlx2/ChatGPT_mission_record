# Frank / CA C01-C08 unified research entry and no implicit execution quote checkpoint

Date: 2026-10-13 Asia/Bangkok
Status: `C01_USER_ENTRY_CODE / C08_AUTO_QUOTE_REMOVED / CI_AND_OTHER_AI_REVIEW_PENDING / NOT_DEPLOYED`

## Mainline and exclusions

Independent branch from main `4ac0b1612e8d238ab9189de066ea16a6f6e66455`. Existing Frank V1 frozen follow decision, `follow_policy_v1.approved.json`, `MissionMemeService._quote()`, local/Gmail notification and immutable outbox **untouched**. Zero new automation, wallet signing or trading.

This addresses two user screenshot issues about general CA research UX:
- C01: user enters one Solana CA in a single visible mode. The browser no longer offers quick/standard/deep, and always supplies the currently tested `standard` preset to the existing backend for backwards compatibility. **Important limitation**: C05 still has bounded historical owner/funding samples; current backend `standard` must not be described as a completed full-chain history or final C01 acceptance.
- C08: generic CA no longer automatically requests a Jupiter $30 quote either at BASE_READY or at report-finalizing. The generic market preview and report show dated DexScreener references only, not a phantom $30 executable price. An old saved report's legacy quote is retained as `ARCHIVED_NOT_LIVE` (not new or current). The separate *user-specified amount* opt-in quote path is **not implemented in this PR** and remains C08 follow-up.

## Code

- `mission_control/server.py`: removed the two default Jupiter quote requests for general CA. Kept legacy persisted quote annotation but always archival. Manager's reporting and partial RPC states remain independent of Jupiter availability.
- `mission_control/static/index.html`: one mint form, honest coverage/missing-history description, reference market snapshot only.
- `mission_control/static/app.js`: fixed single browser preset `standard` and removed implicit $30 cards, expiry timer, stale quote interaction, and obsolete picker; full research progress and explicit missing source information remain.
- `meme/cluster.py::markdown`: new general CA reports say no automatic execution quote requested; historical legacy quote is labeled archival without a real-time claim.
- `tests/test_frank_ca_c01_c08_no_default_quote.py`: failing-before-fix contract captures no quote calls during BASE_READY/final, single-mode UI, old-report archival, no $30 display. Existing dashboard expectations revised to the new user-approved UI semantics; other suites remain.

## Acceptance and next tasks

This is a **Draft-only code checkpoint**. Exact-head CI and independent other-AI review are separate required gates; no Mac deployment or changed main. Full C01/C08 acceptance requires C05 historical completeness and optional explicit-amount quote API, with real browser/chain tests after reviewed merge and operator authorization. C02 token name/mint cross-check and C07 narrative remain parallel outstanding business tasks.
