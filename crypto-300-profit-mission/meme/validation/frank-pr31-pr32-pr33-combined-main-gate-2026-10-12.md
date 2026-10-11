# Frank PR #31/#32/#33: exact pinned main merge integration and CI report (2026-10-12 Bangkok)

## Current decision

**Combined code integration: TEST PASS. Formal main merge: NOT AUTHORIZED YET.**

This report is for an independently isolated and locally merged review candidate. It does not authorize a Mac deployment, Gmail send, trading action, or merging `main`.

## Exact source refs

- Main at start of verified test: `26da9bbb56235db055c1e581ec1535f3bdc51635`
- PR #31 Frank V2: `c50e7e2259e85ce89e14641a4e1e98ca3e4a4bc7`
- PR #32 Gmail OAuth recovery: `85f1a792dd7d0fbf354c09ac83872887ed301c10`
- PR #33 Dashboard delivery review: `48f53a71f692f5dc62f67198f4794e79c45402d2`
- **Persisted integration review branch:** `review/frank-pr31-pr32-pr33-integration-20261012`
- **Persisted integration HEAD:** `dafb126e33338523630bb48d4fe838ddd9c7fb95`
- **Persisted Git tree:** `664ad39f42c7deed39c2b333d4cef1bf9172b592`

The integration candidate contains the actual merged source, not a plan or cherry-picked subset. The candidate branch was pushed by a separate GitHub Actions job **after** both isolated matrix gate jobs had completed successfully.

## Real Git merge and conflict resolution

Two orderings were tested in distinct clean temporary Git worktrees:

1. Pinned main → PR #31 → PR #32 → PR #33
2. Pinned main → PR #32 → PR #33 → PR #31

Both completed with no unresolved conflicts. The only original textual Git conflict was an `add/add` for
`.github/workflows/frank-pr32-pr33-review-tests.yml` between PR #32 and PR #33. PR #33's broader version was selected and its exact Git blob verified as `ed885cbad2a3bbb5abee00321fa9e9a4f823ceeb`. No automated Git conflict resolution was allowed for any other path.

The merged application files `mission_control/server.py`, `static/app.js` were auto-merged without textual conflict. Semantic correctness of the combined tree is supported by actual tests, not by the absence of conflicts alone.

An early CI attempt failed because the Runner lacked a local temporary Git author identity. This was corrected using ephemeral author data in the isolated job. A subsequent run proved the real workflow add/add conflict. Neither failure is represented as a production regression.

## GitHub Actions evidence

### Matrix/merge gate

[Run 38162368483](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38162368483): both orderings **SUCCESS**, with each executing:

- Combined focused regressions: **129 passed**, 0 skipped.
- Complete `crypto-300-profit-mission/local-agent/tests` suite: **1,221 passed**, 0 skipped, with `FRANK_EXPECT_REAL_GIT_REPLAY=1`.
- Python compile/static pyflakes and `node --check static/app.js`: completed successfully.

[Run 38162689243](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38162689243): same two-order matrix **SUCCESS** with 129/1221 pass counts, plus independently published the persisted candidate Git branch.

### Exact persisted Git candidate gate

[Run 38162884440](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38162884440): **SUCCESS** against exact persisted commit `dafb126e33338523630bb48d4fe838ddd9c7fb95`; asserts exact tree SHA `664ad39f42c7deed39c2b333d4cef1bf9172b592`; then:

- Focused regression: **129 passed**, zero skipped.
- Full local-agent regression including actual Git replay: **1,221 passed**, zero skipped.
- Backend syntax, selected pyflakes and JavaScript `node --check`: completed successfully.

### main moved after the pinned CI snapshot

`main` advanced after the original combination CI start. At the follow-up check, the latest SHA was `1a37dcd71a6a99e737ffac035f6df25aeffec8d5` (+5 commits). The compare against `26da9bbb` showed five BSC Meme research JSON files under `crypto-300-profit-mission/research/`, with no local-agent code changes; the exact list and SHA were obtained from GitHub compare. This finding is **time-scoped**: recheck immediately before final main merge, because the repository is concurrently updated by other work.

## Mac/runtime limits

- The PR #31 isolated Mac acceptance `frank-pr31-mac-readonly-20261012-005659.zip` recorded 28 automated PASS, one SKIPPED `BROWSER_RENDER`, no FAIL. User-provided J7/BPxx screenshots separately support rendered 0/2 and 63/3 ATA-window text. Raw ZIP remains PARTIAL; see `review/frank-pr31-mac-isolated-readonly-acceptance-20261012` acceptance report.
- New PR #32/#33 code is tested in combined CI. Actual end-to-end Gmail provider sending under the latest combined tree has **not** been tested and must not be inferred from a separate earlier test email.
- Latest PR #33 deployment script is not authorized to modify the existing live Mac Dashboard; prior manual dashboard patch installation and local receipts are separate evidence.
- PR #31 evidence export remains opt-in and disabled. CA export `Future` exception observation (L3), short-secret export allowlist design (N4), and live ALT-provider behavior (M5) remain open or limited as documented; do not enable exporting as a by-product of merging.

## Release gate (not automatic)

1. Request final external human/independent AI **review of the exact persisted integrated Git tree** (not only each historical PR head), particularly combined server/app UI, historical notification review and credential-sanitization invariants.
2. Recheck `main` and all three PR refs for exact SHA drift. Any executable-code drift requires a new test. Research-only additions may be reviewed for non-overlap but still require exact source tracking.
3. Do not merge to main while the three source PRs are Draft and the release authorization is open. Prefer one coherent integration decision to three uncontrolled or overlapping merges.
4. Never treat merge approval as approval for production auto-trading, Gmail resends, Mission Loop restart, or enabling evidence exports.

No production database write, mission-loop restart, real Gmail send, automated trading, or push to main occurred in these gates.
