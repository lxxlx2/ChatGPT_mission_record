# BSC F0 24-read runner — report/journal path P1 targeted repair

**Status:** `P1_REPAIR_IMPLEMENTED_OFFLINE / INDEPENDENT_REVIEW_PENDING / NO_RUN`.
**Review comparison:** PR #135 `fed9d88fcdbaeb8acaafafbc066ed50af0cf8b6d`; its independent review returned REQUEST_CHANGES for one audit-integrity P1. This is a separate stacked branch, preserving the rejected SHA and its full 209/209 zero-skip reviewer result without retroactively treating the old code as approved.

## The proven defect

PR #135 `bounded_report_path()` allowed a report named either `report.json` or `journal.json`. With `--report <storage_root>/journal.json` the same file first stored a durable `attempts` array (24 rows) and was later atomically replaced by a final summary that did not include those rows. Both full success and unexpected-error report paths were affected. The reviewer independently reproduced using a fake sender, not a live RPC call.

## Minimal correction, before nonce or send

- `bounded_report_path(..., expected_name='report.json')` only accepts **report.json** for the caller-supplied final report.
- The private journal path is obtained with `expected_name='journal.json'` and only accepts **journal.json**.
- `main()` explicitly checks the two normalized resolved output paths are distinct before `consume_nonce` and before any sender invocation. Both must be inside the permitted storage root, no symlinks, and neither may already exist.
- No changes to call sequencing, the 24-call cap, presend fsynced `ATTEMPTED_OUTCOME_UNKNOWN` journal records, failure mapping, execution approval scope, time window, selected wallets or Router list. No new live permission.

## Executed regression and evidence scope

Four **new** tests in `tests/test_f0_l1_probe_report_collision.py` invoke the real CLI live branch with fully mocked permit validation, source binding, nonce and network sender; the tests do NOT create any real reviewed live permit or send RPC:
1. Using `--report journal.json` is rejected before nonce consumption and with zero fake sends; neither output file is created.
2. The report and journal role-specific filenames cannot be interchanged.
3. After 24 injected, identity-matched fake RPC responses, `report.json` exists AND `journal.json` still has all 24 ordered `attempts`, each already persisted as `ATTEMPTED_OUTCOME_UNKNOWN` upon entry into the fake sender.
4. On an injected exception after the first persisted attempted call, `report.json` contains the `BLOCKED_SOURCE` summary and `journal.json` still contains the first full attempt row (not only a count), with no leaked fake secret.

**Local isolated test directory:** `Ran 213 tests ... OK (skipped=2)`: 211 PASS / 2 SKIP. The only skips are the inherited PR #116 real manifest tests because that raw file was not copied into the isolation directory. **Do not treat these as 213 PASS**. The complete Git checkout must be independently tested for `213/213 PASS, zero SKIP` before this repair is approved.

Exact locally executed code Git blobs:
- `f0_l1_code_probe.py`: `046f50179a4163739d4dc1ed47fac243b196381d`
- `tests/test_f0_l1_probe_report_collision.py`: `da56ee7e5c7043c4a9ebeba8040fb0e4e7673f44`

The independent reviewer must verify the true fixed SHA and Git diff, test no-sends collision pre-nonce, correct report/journal separation in real main, 24-row success and exceptional early stop, all prior 209 tests, no real RPC, and file hashes. The extra 4 tests are synthetic execution traces, not actual network or authorization evidence. Local full verbose stdout SHA256 `2f64f9bbde4bcf0abb5ade56589374b5de4c13c046c03afde10744dfea66a237` is an identifier for the local artifact, **not** a claim that a full log was uploaded to Git.

**No live authorization:** prior 4-call smoke permit was already spent. The proposed 24-read wallet/Router qualification remains unapproved and not executed. Even a reviewer APPROVE here authorizes offline code only. A separately reviewed concrete permit and new written user consent are required for real network use. No WS, trading, signing, notifications, merge or deployment.
