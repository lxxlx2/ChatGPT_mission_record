# Frank PR #34 final independent review remediation — round 6, 2026-10-12

## Source and authority

The user supplied an external independent AI review **in text**, not the actual proposed patch files. The reviewer assessed PR #34 HEAD `dafb126e33338523630bb48d4fe838ddd9c7fb95` (tree `664ad39f42c7deed39c2b333d4cef1bf9172b592`) and reported **MERGE_BLOCKED** for:

- B1: no CI run directly associated by GitHub check-runs with the reviewed commit, although a prior workflow on a separate review branch did checkout and assert the exact SHA/tree internally.
- B2: unkeyed Google OAuth credential values (synthetic `1//...`, `GOCSPX-...`, `ya29....`) can pass evidence export `safe()`; UI claims historical notification was "未发送" based solely on SQLite no-attempt rows.

The original external review reported `1221 passed`, and a **locally proposed, NOT_PUSHED** fix yielded `1223 passed`. The proposed patch bytes were **not attached** to this conversation; this implementation is an independently reconstructed minimal equivalent, not a claim of exact application of the other AI's patch.

## Changes actually pushed to PR #34

- `evidence_sync.py`: extend the existing sensitive-inline detector to match unkeyed, token-shaped Google OAuth refresh/access/client secret strings. Leave whitelist routing, existing records and output format unchanged.
- `static/app.js`: replace "未发送" with "数据库无发送尝试记录"; tooltip discloses that Gmail Sent was not independently verified, and preserves no-auto-resend audit semantics.
- `tests/test_meme_evidence_sync.py`: targeted r6 test for synthetic unkeyed credentials and benign links/strings.
- `tests/research/test_delivery_review_breakdown.py`: targeted r6 UI language regression.
- `evidence_sync.py`: delete one pre-existing unused import (`tempfile`) detected by the new static scan; no behavioral impact.
- `.github/workflows/frank-pr34-exact-head-review-tests.yml`: new read-only CI on the PR #34 integration branch to test the actual commit SHA associated with the workflow, not just another branch's `actions/checkout(ref=...)`.

Original chain evidence JSON files, production Mac files, SQLite, Gmail, LaunchAgents and trading policy were not modified in this remediation.

## Exact remote CI evidence

- **New PR #34 HEAD:** `b637361154863f492b31a636de8e77381bc8156b`
- **Git Tree:** `5bf53fa5d97cf133da7544539cbe429663598504`
- **[GitHub Actions 38189353248](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38189353248)**: completed **SUCCESS** with the job head equal to `b637361154863f492b31a636de8e77381bc8156b`. The job itself confirmed `git rev-parse HEAD == GITHUB_SHA` and wrote both exact SHA and tree to logs.
- Both B2-specific regression nodes: **2 passed**, zero skipped.
- Combined focused tests (nine test modules): **131 passed**, zero skipped (prior count of 129 plus two new cases).
- Complete `local-agent/tests` suite with `FRANK_EXPECT_REAL_GIT_REPLAY=1`: **1223 passed**, zero skipped.
- Python compile, selected pyflakes and JavaScript `node --check`: completed successfully.
- An intermediate run `38189301367` stopped on a pre-existing unused `tempfile` import in `evidence_sync.py`. Import removed with no policy change and the **later exact SHA CI passed**. Do not mislabel the intermediate CI as final.

The earlier CI run `38162884440` is a valid record that a workflow from a separate review branch checked out `dafb126e...` and validated its exact tree before testing. The reviewer's narrow B1 objection was that this did not create a GitHub-native check directly tied to the `dafb126e` commit. The new exact-HEAD job removes that ambiguity for the new head.

## Mac and main integration limits

- Previous PR #31 Mac acceptance ZIP SHA256 `6544344b3a4fa733c1f17335f4a5339d8e75478874f1cc8f5d27a0c0ea266e1e`, independently re-read from the user re-upload in this turn: **28 PASS, one SKIPPED browser gate, zero FAIL**, original machine result `PARTIAL`; separate screenshots show J7 0/2 and BPxx 63/3. This is **not** live combined PR #34 Gmail/Frank deployment acceptance.
- At one GitHub comparison, `main` was `981fecc5a0d248c049dd51a728bac8624a3cff3d`, **58 commits ahead of the pinned combination baseline**, with 44 changed files. None matched local-agent, Frank-specific workflows, or the relevant mission control/Frank evidence paths. This is time-scoped; `main` may move further.
- The existing three-PR integration review candidate was actually Git-merged in two orders and passed **1221** tests at its old SHA. New PR34 B2 files were verified by direct 1223-pass branch CI, but a fresh merge-tree check at the **then-current main + new HEAD** has not been executed by this report.
- CA export L3 async Future result loss remains open before enabling CA auto export; N4 short URL/hostname credential variants and M5 real provider ALT behavior are not established as closed. Refresh token backups retain secrets with mode 0600 and need an operational retention policy.

## Current gate

- **B1: RESOLVED for exact new HEAD** with CI `38189353248`.
- **B2: IMPLEMENTED / TARGETED AND FULL CI PASS**. This is a new code implementation of the requested fix, so an external reviewer may still verify the exact new SHA before changing review status to MERGE_APPROVED.
- **PR #34 remains DRAFT / UNMERGED**. The originally supplied independent review was MERGE_BLOCKED for an older SHA and cannot be retroactively called MERGE_APPROVED.
- **No production deployment or historical Gmail resend authorized or performed.**
