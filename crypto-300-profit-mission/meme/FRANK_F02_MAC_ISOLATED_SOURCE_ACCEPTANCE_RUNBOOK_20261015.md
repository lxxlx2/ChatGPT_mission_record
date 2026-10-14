# Frank F02-R1 Mac isolated actual-source acceptance runbook

Date: 2026-10-15, Asia/Bangkok.
State: \`RUNBOOK_READY / USER_ISOLATED_RESEARCH_IMPORT_AUTHORIZATION_REQUIRED / NO_PROD\`.
**This is a plan, not a claim that any 2026-10-15 Mac command has run.**

## Frozen reviewed identity and source

- External independent source review [Draft PR #63](https://github.com/lxxlx2/ChatGPT_mission_record/pull/63) at exact immutable Git commit \`f4007f64dc92c87854e752562ea9e24bbfd78c23\`: \`APPROVE\` after rerunning the original real HTTP stale-positive regression and SQLite 503. [Review checkpoint in PR #63](https://github.com/lxxlx2/ChatGPT_mission_record/pull/63#issuecomment-6174214955).
- The original [PR #62](https://github.com/lxxlx2/ChatGPT_mission_record/pull/62) \`c24119989b7e752ee925e38c777ceb376ac97f81\` remains externally \`REQUEST_CHANGES\` forever. Do NOT run that old SHA.
- A05-R1 user Mac source bundle (local-only): \`$HOME/.local/share/frank-owner-full-rpc-evidence/owner-f537013b8a094e608cf9657622b627d6\`, expected replay SHA \`a91fed6fae63f51557ab88fb9ae892247cc32deccd26c631d765ff27aff03261\`, SPL 1,785 @ slot 456895319, Token-2022 1,448 @ slot 456895320, archived 2026-10-14T15:54:15.873036Z. External reviewer 6.1 Sol reported independent original byte+manifest SHA verification and 32-entry aggregation (9 nonzero / 23 zero, 32 open accounts; one reviewer source access, NOT two).
- Frozen old target roster: \`crypto-300-profit-mission/meme/evidence/frank-v2-thirty-two-mint-finalized-2026-10-11.json\` immutable actual Git Blob SHA \`c6f43e4a63ea9daa1c9b820b8faed8ccefcdb2d1\`. 2026-10-11 10 positive / 22 zero **does not establish sale**. 33rd independent Mint must NOT join baseline.
- F02-R1 API is manual standalone read-only \`127.0.0.1\` \`GET /api/research/positions\`, no production \`mission_control/server.py\` change. **Important** initial A05 bundle was verified but \`research_sidecar_imported=null\`; API cannot return source-backed archival rows until the source is explicitly imported into a NEW isolated research-only Sidecar. That import writes *new research SQLite*, **never** production SQLite.

## Stage 1: Mac read-only preflight — permitted independently; NO import/no listener

Copy the following into macOS zsh. It clones and selects **only** the immutable audited branch SHA under a separate user workspace. It replays existing original bytes offline, prints the frozen 32-only summary, and invokes F02 PLAN_ONLY, with no new network RPC, sidecar creation, service start, trade or email. Git clone/fetch itself accesses GitHub but does not access the Solana RPC.

\`\`\`zsh
(
set -e
repo="$HOME/.local/share/frank-f02-r1-review"
bundle="$HOME/.local/share/frank-owner-full-rpc-evidence/owner-f537013b8a094e608cf9657622b627d6"
sidecar="$HOME/.local/share/frank-f02-research/owner-456895319-456895320.sqlite"
if [ ! -d "$repo/.git" ]; then
  git clone --filter=blob:none --branch fix/frank-f02-later-partial-lower-slot-20261014 --single-branch https://github.com/lxxlx2/ChatGPT_mission_record.git "$repo"
else
  git -C "$repo" fetch origin fix/frank-f02-later-partial-lower-slot-20261014
fi
git -C "$repo" checkout --detach f4007f64dc92c87854e752562ea9e24bbfd78c23
test "$(git -C "$repo" rev-parse HEAD)" = "f4007f64dc92c87854e752562ea9e24bbfd78c23"
test -d "$bundle"
test -f "$bundle/manifest.json"
cd "$repo/crypto-300-profit-mission/local-agent"
python3 -m scripts.frank_capture_owner_full_receipts --person-id frank --replay-bundle "$bundle"
python3 -m scripts.frank_reconcile_frozen32_offline --person-id frank --bundle "$bundle"
python3 -m scripts.frank_f02_readonly_positions_api --person-id frank --bundle "$bundle" --sidecar "$sidecar"
)
\`\`\`

Expected **source-independent** safe boundaries: source replay \`FULL_DUAL_PROGRAM_SOURCE_REPLAY_VERIFIED\` with exact expected capture SHA and 3,233 whole-wallet open accounts; R2 result \`FROZEN32_OFFLINE_ACCOUNT_RECONCILIATION_COMPLETED\` with 32 targets, 9 nonzero /23 zero /0 absent from historical archived observation; F02 default \`PLAN_ONLY\` returns \`sidecar_opened=false\`, \`network_invoked=false\`, \`writes_production_sqlite=false\`. If the Mac file moved, **do not guess a new source or fetch again automatically**; use actual archived bundle path and review permissions. If any SHA, roster/blob, wallet or result deviates, STOP and do not authorize import.

## Stage 2: separately authorized creation of NEW isolated research Sidecar — NOT EXECUTED

**Require explicit user authorization first.** This is the only step that writes to a new research-only SQLite file. Do NOT use the default \`~/Library/Application Support/FrankMeme/research-wallet-evidence.sqlite\`, any \`forward.sqlite\`, \`mission-control.sqlite\`, production loop or production browser SQLite. Do not upload original 3,233 account data to Git. The chosen new path is confined to \`$HOME/.local/share/frank-f02-research/owner-456895319-456895320.sqlite\`, and the command refuses any existing file rather than overwriting unknown research.

After explicit approval, in the *same exact pinned checkout*:

\`\`\`zsh
(
set -e
repo="$HOME/.local/share/frank-f02-r1-review"
bundle="$HOME/.local/share/frank-owner-full-rpc-evidence/owner-f537013b8a094e608cf9657622b627d6"
sidecar="$HOME/.local/share/frank-f02-research/owner-456895319-456895320.sqlite"
test "$(git -C "$repo" rev-parse HEAD)" = "f4007f64dc92c87854e752562ea9e24bbfd78c23"
test -d "$bundle"
test ! -e "$sidecar"
test ! -L "$sidecar"
mkdir -p "$HOME/.local/share/frank-f02-research"
chmod 700 "$HOME/.local/share/frank-f02-research"
cd "$repo/crypto-300-profit-mission/local-agent"
python3 -m scripts.frank_capture_owner_full_receipts --person-id frank --replay-bundle "$bundle" --sidecar "$sidecar" --import-sidecar
python3 -m scripts.frank_f02_readonly_positions_api --person-id frank --bundle "$bundle" --sidecar "$sidecar" --max-age-seconds 300 --probe-once
)
\`\`\`

Expected import \`research_sidecar_imported=true\` *only for newly created isolated file*. Probe \`kind=F02_RESEARCH_ARCHIVED_OWNER_POSITIONS\`, 32 entries and matching source/selected capture SHA. **Because this is a dated original source and the CLI hard limit is 300 seconds by default, expect \`readiness=STALE_ARCHIVED_SOURCE\` and all 32 public API observed quantities \`null\` when the archive is older than 5 minutes.** That is the desired honest fail-closed behavior, not failure of archival R2's 9/23 frozen observation. Never extend TTL to mislabel old evidence as a live position.

Inspect *only limited non-private summary* of the archive; do not publicly publish private full bundle, research DB or complete wallet account lists. If SQLite import fails, do not wipe, regenerate, delete or overwrite an existing research file without separate investigation and permission.

## Stage 3: real fresh-source acceptance / API / Dashboard — future gated steps

A fresh F02 observation needs a **new user-initiated manual full-wire collection**, separately authenticated complete replay and explicit corresponding isolated research Sidecar import; this does not mean turning on automated collection. Start a **manually authorized** local listener only after F02-R1 read-only probe success:

\`python3 -m scripts.frank_f02_readonly_positions_api --person-id frank --bundle "<exact newly captured bundle>" --sidecar "<new explicitly isolated research sidecar>" --max-age-seconds 300 --serve --port 18765\`

Run real localhost HTTP calls with matching selected vs attempted SHA and age; assert zero/null/positive states, no profit inference, and older success masked on later failed attempts; then shut down the manual listener. Does not touch currently running production Dashboard. Browser UI F02-R2 then Mac acceptance F02-R3 follow. Any prod deploy/merge requires separate authorization and later integration+full-system independent reviews.

## Known P3 after approved P2/P3 fix

The external reviewer additionally tested exactly equal UTC capture stamps: selected chain source can remain full and \`latest_attempt_source_status=PARTIAL_SOURCE\` but \`readiness=FRESH_VERIFIED_ARCHIVED_OBSERVATION\`. **Independent extra tests 6 passed / 2 failed**; reviewer assessed this as P3 nonblocking because true capture attempt ordering cannot be established on an exact timestamp tie and default system records microseconds. Do not claim the extra tests passed or invent chronology. Track as future **F02 data-contract consistency guardrail**, prioritize only if real Mac source or forthcoming dashboard demonstrates this ambiguity. Do not build an unbounded new P3-fix PR now.

## Acceptance artifacts to put back in Mission

- Exact commit SHA and untouched privacy-limited original capture SHA.
- Original bundle offline readback status/hash, frozen32 aggregate, isolated Sidecar import boolean/ID and file path masked to \`~/.local/share/...\`, separate actual probe readiness and capture age. Redact private sources or whole wallet raw accounts.
- A05-R2 archived observation count **9 nonzero/23 zero** is as of 2026-10-14 22:54 Bangkok only. F02 API *after TTL* may legitimately return **32 SOURCE_UNAVAILABLE**; do not describe these as zeros or sales.
- Mac proof still requires local test results. Until user separately authorizes import, \`F02-R1_CODE_EXTERNAL_APPROVE / F02_MAC_REAL_PROBE_PENDING / NO_MERGE / NO_DEPLOY\`.

NO_PRODUCTION_SQLITE_WRITE / NO_TRADES / NO_GMAIL / NO_AUTO_RPC / NO_AUTOMATION / NO_MERGE / NO_DEPLOY.


## 2026-10-15 Mac user read-only preflight actual stdout — PASSED

This section updates the earlier prospective Stage 1 instructions: **the user has now run them** and pasted the following source-supported limited evidence (run clock time not provided):

- Detached checkout HEAD `f4007f64dc92c87854e752562ea9e24bbfd78c23`, approved PR #63.
- Offline dual-program original-wire replay `FULL_DUAL_PROGRAM_SOURCE_REPLAY_VERIFIED`; `capture_sha256=a91fed6fae63f51557ab88fb9ae892247cc32deccd26c631d765ff27aff03261`, non-atomic slots 456895319/456895320, 3,233 observed Token Accounts/Mints, `research_sidecar_imported=null`, `writes_production_sqlite=false`. Replay-stage `target_32_mints_verified=false` is not an error; target roster gate is R2.
- Frozen R2 `FROZEN32_OFFLINE_ACCOUNT_RECONCILIATION_COMPLETED`, `roster_git_blob=c6f43e4a63ea9daa1c9b820b8faed8ccefcdb2d1`, 32 target Mint, 32 target Token Accounts, **9 nonzero, 23 zero, 0 missing**, no multi-account target, historical 10 nonzero/22 zero, `network_invoked=false`, `pnl_verified=false`, `report_path=null`, `history_complete=false`.
- **Stage 1 = PASS. Stage 2 = NOT_AUTHORIZED / NOT_RUN. Stage 3 = PENDING.** No new Solana RPC, research SQLite Sidecar, manual research HTTP listener, real F02 API probe, production write, email or trade in this evidence.
- After **explicit separate user authorization**, run Stage 2 only with the reviewed `f4007f64dc92c87854e752562ea9e24bbfd78c23` and **new outside-repo** research Sidecar `~/.local/share/frank-f02-research/owner-456895319-456895320.sqlite`. Because archived `observed_at_utc=2026-10-14T15:54:15.873036+00:00` is already old, a normal 300-second F02 `--probe-once` should **fail closed as `STALE_ARCHIVED_SOURCE`**, 32 source-unavailable/null quantities, despite R2's correct archived 9/23 historical observation. Do not increase max-age to pretend history is current. No merge or prod changes.


## 2026-10-15 explicit user approval received — Stage 2 scoped only; execution evidence pending

- User explicitly replied **“批准”** to the precise request: permit creating a **NEW** research-only isolated Sidecar SQLite at `~/.local/share/frank-f02-research/owner-456895319-456895320.sqlite`, import only the existing owner-f537013b... archived full-wire bundle after exact SHA verification and then run an F02-R1 manual read-only `--probe-once`. This authorizes only this one isolated research evidence write and local read-only probe. No other database/file operation or automatic future capture is authorized.
- Approved immutable script/source pin `f4007f64dc92c87854e752562ea9e24bbfd78c23`, archived capture `a91fed6fae63f51557ab88fb9ae892247cc32deccd26c631d765ff27aff03261`, target roster blob `c6f43e4a63ea9daa1c9b820b8faed8ccefcdb2d1`. Preserve `NO_MERGE / NO_DEPLOY / NO_NEW_RPC / NO_TRADES / NO_GMAIL / NO_PRODUCTION_SQLITE_WRITE / NO_NEW_AUTOMATION`.
- **Authorization received is not proof of execution**: this agent has GitHub access but no remote execution access to the user's private Mac bundle. User must run the pinned local zsh stage-2 invocation and provide limited stdout. Do not mark `SIDECAR_IMPORTED` or `MAC_F02_REAL_PROBE_PASS` until actual machine receipts arrive.
- Expected behavior at present: the 2026-10-14 22:54 BKK original capture is older than the API default `--max-age-seconds 300`; the successful F02 read-only probe should show `readiness=STALE_ARCHIVED_SOURCE`, 32 `SOURCE_UNAVAILABLE`, no nonnull observed quantity. R2 archival result 9 positive/23 zero remains valid only as a time-scoped archived observation. No TTL override to simulate current balances.
