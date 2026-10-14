# Frank F02-R2 — standalone same-origin localhost research browser

Date: 2026-10-15 Asia/Bangkok.
Code: isolated F02-R2 child of externally approved [PR #63](https://github.com/lxxlx2/ChatGPT_mission_record/pull/63) immutable `f4007f64dc92c87854e752562ea9e24bbfd78c23`.
Current status: `CODE_SUBMITTED / CI_AND_EXTERNAL_REVIEW_REQUIRED / BROWSER_MAC_PENDING / NO_MERGE / NO_DEPLOY`.

## Actual completed prerequisite

User explicitly approved creating one isolated research Sidecar and locally executed exact #63 SHA preflight/import/probe. Mac stdout:
```text
SOURCE_REPLAY=PASS
ISOLATED_SIDECAR_IMPORT=PASS
{"F02_MAC_PROBE": "PASS", "readiness": "STALE_ARCHIVED_SOURCE", "state_counts": {"SOURCE_UNAVAILABLE": 32}, "capture_age_seconds": 7397, "slot_min": 456895319, "slot_max": 456895320}
```
Archive capture SHA `a91fed6fae63f51557ab88fb9ae892247cc32deccd26c631d765ff27aff03261`, frozen historical 32 roster blob `c6f43e4a63ea9daa1c9b820b8faed8ccefcdb2d1`, at archived 2026-10-14 22:54 BKK 9 nonzero/23 observed zero (does NOT establish sell or live holdings). The now 7397-second-old archive exceeds the F02 300-second TTL, so the actual Mac API correctly hid all 32 quantities. This evidence is a user-executed Mac result, not a claim that GitHub can read the private Sidecar.

## Changed child scope

- `scripts/frank_f02_readonly_positions_api.py`: only a static same-origin route table on an already separate **manually started** research-only `127.0.0.1` HTTP listener. `GET /research/positions` returns HTML, `/research/positions.js` and `/research/positions.css` serve fixed local assets; source data remains `GET /api/research/positions`. Static route lookup uses a fixed literal mapping, no filesystem path from requests. No prod `mission_control/server.py` editing. Response headers: `Cache-Control: no-store`, strict self-only CSP, `nosniff`, no framing, no referrer. API still has no CORS and no write endpoint.
- Browser renders **frozen 32 exact Mint research objects**, identity/wallet, source capture UTC, elapsed age/TTL, two finalized non-atomic slots, full verified wire SHA copy and latest actual attempted source metadata, with explicit reason for failure, stale or unverified data. Per-Mint exact CA, status, quantity only if source verified fresh, Token Account count, CA copy and Solscan navigation. Mint search, status filter and manually re-read **local archive** control. Respects zero vs no-open-account/null vs stale unknown; no fake USD / PnL, no BUY/NO_BUY misclassified as actionable, and no automatic RPC refresh.
- **Independent equal-UTC metadata P3 presentation guard:** even if API says `FRESH_VERIFIED_ARCHIVED_OBSERVATION`, browser refuses quantity unless `archive_observation_usable`, `capture_fresh`, latest selected SHA equals original replayed SHA, latest attempted source SHA matches and both latest actual attempted/selected source statuses are `BOTH_PROGRAMS_OBSERVED_NON_ATOMIC`. If inconsistent, browser shows `来源信息不一致` and all observed quantities masked; this guard is view-only, avoiding an unbounded change to previously approved source logic. Original API P3 extra tests 6 passed/2 failed remain recorded and not silently called green.
- Client uses DOM `textContent` and `document.createElement` (no dynamic innerHTML); fixed Solscan links only for validated Base58-looking Mint strings, new-tab `noopener noreferrer`; clipboard only on manual click; no external script, no data storage, no automatic background refresh.
- Unit + actual local socket integration test `tests/test_frank_f02_r2_isolated_browser.py` exercises real HTML/CSS/JS requests, API stale masking, Host gate, CSP, read-only Sidecar byte immutability. Node `tests/frank_f02_r2_render.cjs` validates DOM rendering of fresh/zero/unknown, 32 stale masks, same-UTC conflicted metadata, search/filter and clipboard interaction. CI runs module focused/full and disposable main+F02-R2+frozen C02+F01 combined focused/full.
- This stage does **not** claim a fully usable current live holdings view on Mac: archived source remains stale. A new fresh owner source can only come from separately user-triggered complete original RPC capture and explicit source-matched research-only Sidecar import, never by widening TTL or faking values.

## Follow-through and business acceptance

1. Check exact GitHub commit/CI, fix real functional issues within this PR, freeze immutable head, solicit another-AI independent review `APPROVE/REQUEST_CHANGES`; do not merge.
2. With separate manual authorization, run isolated Mac listener from approved exact branch and **already created isolated research Sidecar**:
   ```zsh
   cd "$HOME/.local/share/frank-f02-r2-review/crypto-300-profit-mission/local-agent"
   python3 -m scripts.frank_f02_readonly_positions_api --person-id frank --bundle "$HOME/.local/share/frank-owner-full-rpc-evidence/owner-f537013b8a094e608cf9657622b627d6" --sidecar "$HOME/.local/share/frank-f02-research/owner-456895319-456895320.sqlite" --max-age-seconds 300 --serve --port 18765
   ```
   In browser navigate to `http://127.0.0.1:18765/research/positions`; archived source page must display stale / 32 null quantities, correct name/address/SHA/slots/source time, 32 entries and working search/filter/CA copy. Manual process stop and verify existing prod listener unchanged. Do not run it now as an assumed macOS command; the Mac is private.
3. F02-R3 isolated Mac page acceptance with actual source, browser/screenshot evidence and source age + true RPC round-trip if user authorizes a fresh capture; standalone cross-module full independent review and separate final whole-system review. No production deploy until explicit approval.

`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADES / NO_PRODUCTION_SQLITE_WRITE / NO_NEW_RPC_AUTO / NO_AUTOMATION`.
