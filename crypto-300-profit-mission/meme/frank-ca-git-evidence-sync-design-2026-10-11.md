# Frank 信号与手动 CA 查询：本地证据自动同步 Git 设计及实现状态

Updated: 2026-10-11 Asia/Bangkok
Owner: 300-3000 Mission Frank/Meme lane
Implementation PR: https://github.com/lxxlx2/ChatGPT_mission_record/pull/31
Evidence-only branch: `evidence/frank-ca-local`
Status: `RESEARCH_CODE_IMPLEMENTED / CI_PASS_ON_TESTED_HEAD / USER_MAC_NOT_TESTED / AUTO_EXPORT_DISABLED / NO_PRODUCTION_DEPLOYMENT`
Background: the user needs the latest **actual** Frank scanning/transaction and CA-query evidence available in Git to debug independently without re-collecting identical Mac files. No new polling task, no fresh watch automation, no trading, no change to frozen Frank BUY/WAIT or Gmail delivery.

## 1. Data lifecycle and bounded upload cadence

```text
Existing Frank Writer health+forward.sqlite (read-only)     Existing CA query
                  |                                               |
       Existing Mission Control loop                    report JSON atomically saved
                  |                                               |
           poll_count advanced                            job result DONE
                  |                                               |
          sanitize + local spool  <--------------- sanitize + local spool
                  |                                               |
                  +-------- independent Git uploader worker ------+
                                       |
                       branch evidence/frank-ca-local only
                                       |
                          Git Contents PUT + GET readback
                                       |
                          exact content verified => dequeue
                          failure => retain local durable spool
```

**Every observed finished Frank writer poll** receives a stable local event keyed by its writer `poll_count` and successful health timestamp. The existing Mission Control loop already runs; no new LaunchAgent or scheduler. Normal near-real-time operation captures each newly observed poll; if Mission Control is not running while Writer continues, some intermediate polls may be missed. The uploader must clearly label the data as `LOCAL_WRITER_HEALTH_READ_ONLY` and never assert complete per-poll chain history in that circumstance. A separate production-wide capture completeness guarantee would require independent review of an immutable Writer completion hook, which is **not authorized by this change**.

Each 15-minute UTC bucket contains the individual records for every captured Frank poll. Completed buckets are uploaded to Git, while the open bucket waits until it closes. A manual `sync --force` uploads the current bucket immediately. **Frank scans are committed in batches, not one commit every 30 seconds**. This prevents Git history spam and has a normal worst-case delay around one bucket while preserving individual scan records. Material scans include 40 recent locally classified trading rows and up to 60 relevant signal candidates, using explicit whitelisted fields; quiet scans keep small health/checkpoint records and periodic samples. Such samples **are not an entire wallet transaction ledger**. The exact local raw archive and forward.sqlite remain the more complete source until separately indexed.

**Each successful manual CA job** triggers local evidence capture immediately after its already-existing JSON/Markdown/latest report files have been durably saved. A separate in-process background worker attempts to publish that job immediately. CA output and user-facing response do not wait for or depend on GitHub. Both code hooks are opt-in and disabled by default.

CA evidence is a structured JSON manifest plus, for oversized reports, independently hashed JSON/base64 chunks. All allowed normalized report fields (holders, relationship edges, funding, relevant trades, coverage and error labels) are reconstructable from Git without revisiting the user's Mac as long as the sanitized source is <= 8 MB. The manifest contains `sanitized_evidence_sha256`, `full_local_report_sha256`, coverage tags, and chunk hashes. Unrepresentable, oversized, credential-bearing or unverified raw sources are **never marked as fully uploaded**. The existing local full report remains unchanged.

## 2. File and schema contract

```text
evidence/frank-ca-local
  crypto-300-profit-mission/meme/local-evidence/
    README.md
    frank/YYYY-MM-DD/HHMM.json
    ca/<exact-solana-mint>/<job-id>.json
    ca/<exact-solana-mint>/<job-id>/part-0000.json  (when applicable)
```

Frank event fields: `schema_version`, `kind=frank`, `poll_count`, `captured_at_utc`, `bucket_utc`, `health` (whitelist), `coverage` (source/local-index status, optional), `recent_recognized_trades_sample`, `signal_eligible_candidates_sample`. The name `sample` is intentional; metrics are never mislabeled chain completeness.

CA job fields: `schema_version`, `kind=ca`, `mint`, `job_id`, `generated_at_utc`, `local_job_status=DONE`, chain completeness flag (never inferred from job completion), `data` selected from report and optional `data_chunks`/hashes. The uploader first verifies every part; the manifest goes live last.

**No raw SQLite, cookie, API token, seed phrase, private key, local absolute path, Gmail body, authentication header, RPC credential URL, signal private config or wallet authorization is ever exported.** Git branch access follows the existing repository permissions. Most on-chain addresses/swap data are public, but the repository's visibility must still be considered before enabling uploads.

## 3. Independent uploader, permissions and backpressure

- Implementation: `local-agent/mission_agent/mission_control/evidence_sync.py`; CLI `local-agent/scripts/meme_evidence_sync.py`.
- Opt-in flag: `MISSION_EVIDENCE_EXPORT_ENABLED=1` read by the **already deployed loop and Dashboard server** only *after a separately authorized future deployment*. Current Mac continues unchanged until that step.
- Local spool: `<control_root>/git-evidence-spool/pending/{frank,ca,ca-parts}`, created as mode 0700, event files 0600; atomic creation, content-hash, dedupe, exclusive flock during sync.
- Transport: `gh api` authenticated using existing GitHub CLI credentials. GitHub JSON PUT payload goes only on stdin; private access token is never passed on command line or written into the snapshot. File update checks the remote blob's existing SHA (GitHub CAS), uploads only to fixed remote evidence path and fixed branch.
- A record is `GIT_CONFIRMED` only on **GET readback of identical bytes**; only then are its pending local files removed. A truncated GET, API 404 on branch, CAS race, 429, expired credential or offline network retains pending evidence with `SYNC_PARTIAL`; a not-yet-closed bucket reports `SYNC_PENDING_WINDOW`. User can manually retry without rerunning chain scanning.
- No `git checkout`, commit or push in the working Mission repository. No `main` modification from the uploader, no Git dependency on the signal/notification critical path, and no retry emails or fallback automations.
- Git retention: current design is append-only on the dedicated evidence branch. Review storage volume after actual Mac pilot; never automatically delete immutable research without separate policy review.

## 4. Acceptance evidence and remaining gates

Implemented on **Draft PR #31**:
- Standalone read-only source capture CLI, explicit `capture-frank`, `capture-ca`, `sync` commands.
- Optional in-place CA completion hook, and Mission Control loop reader for Frank snapshots. Frank production writer file unchanged.
- Secure local spool + Git CLI transport + readback equality + retry/pending semantics.
- CA chunked sanitized evidence and reconstructed hash contract.
- `frank_evidence_bootstrap.py` for one-shot Mac validation without touching installed services, exports a safe ZIP + selection-friendly path; optionally syncs after authenticating gh.
- Isolated Git Actions workflow runs new tests plus existing Dashboard/Control service regressions.

**Actually verified in remote GitHub CI**: Python syntax compilation and the new uploader/unit/fake-Git test suite; original Dashboard/Mission Control/Delivery regression subset. Last verified completed run URL and counts should be filled from the actual last CI readback in the corresponding PR; do not claim a future run passed before it does.

**Not verified/NOT DONE**: actual Mac `gh auth`, first real Mac report upload, full readback from user Mac, production config or process restart, queue behavior under Mac TCC and offline network, independent external AI review, a full month of 15-minute retention, missing-poll recovery during Mission Control downtime. No auto enablement or production deployment is claimed.

## 5. Safe Mac bootstrap without touching running worktree

Fetch PR branch into a **separate detached worktree**; never switch the installed source repository's active branch. Run `scripts/frank_evidence_bootstrap.py` on the existing read-only production DB and old CA report directory, with `--sync` to attempt Git upload using existing `gh` credentials.

The script creates a dated ZIP of sanitized pending evidence and D0 local ledger audit plus a status JSON. If `gh` is not installed/authenticated, Git fails, or a partial chunk fails, the ZIP can be shared manually without exposing the production DB or tokens and the pending queue persists for retry. Use macOS `open -R "$PACKET"` in the same command to select the exact file for upload.

### Release gate

Only after real Mac bootstrap with fresh Git **readback** and independent AI review should this feature be considered for merging and installing. Rollout must confirm previously approved Frank policy and writer source fingerprints unchanged; any source alert or Gmail regression is NO_GO. `PRODUCTION_TRADING=NO_GO`.
