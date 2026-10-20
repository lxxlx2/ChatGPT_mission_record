# F0 L1 — PR #141 + PR #143 two-approved-siblings integration review

**State:** `COMBINED_SHA_PENDING_INDEPENDENT_REVIEW / OFFLINE_ONLY / NO_RUN`. Combines two independently APPROVE (OFFLINE ONLY) siblings from the unchanged PR136 baseline. It is not yet a reviewed combined release, is not a live full-block collector, and has no RPC/WS sender or active permit.

## Independently reviewed parent work

| PR | Exact independently APPROVED SHA | Full-checkout unittest independently observed | Responsibility |
| --- | --- | --- | --- |
| #136 | `cd30f8b69301b53380473a33ebb428351d4c1bce` | 213 PASS, 0 SKIP | Durable one-shot 24-read code qualification runner / permit gate (permissions now spent) |
| #141 | `d71459915b3ea78e1e1660aa97ed0e5472ce7454` | 218 PASS, 0 SKIP | Future-report `checked_block` field from independently checked chain ID + positive height |
| #143 | `8d372eeba9e178bae4d4a7578d0657b8351528c3` | 219 PASS, 0 SKIP | Frozen PR116 watch sender + documentary Router destination candidate matching in a common saved full-block stream |

Each sibling was compared against PR136. Both reviewers explicitly disclaimed any combined-version audit, real BSC RPC, E2/E3, quote or production rights.

## Actual integration mechanism

New integration branch forked from the exact approved #143 commit and imported the following 4 #141 files through GitHub's file API preserving identical **Git blob SHA1**:

| Source #141 file path inside `f0/` | Source and combined blob |
| --- | --- |
| `f0_l1_code_probe.py` | `0dab793e75a0f0c1f0d83f7d0fde05d799f0845c` |
| `fixture_l1_code_probe_24_report.json` | `44b957892855f977b04a8d5dc8fa72d564c66506` |
| `tests/test_f0_l1_report_checked_block.py` | `36e93f9580e6e1df53982e74bcaf4e184d9eb7a0` |
| `F0_L1_CHECKED_BLOCK_FUTURE_REPORT_FIX.md` | `08337745784a6450662754f3caaa1b6385781d84` |

`HANDOFF.md` was **reconciled**, preserving each sibling's true reviewed SHA, approvals and accurate state. No cherry-picked README or code edits are claimed beyond these four byte-identical files.

#143's `f0_l1_window.py`, frozen registry, `test_f0_l1_documented_router.py`, synthetic fixture, and documentary Router source remain unchanged from #143. #140 stays a separate **historical operator-reported real 24-read** archive, not retroactively independently verified.

## Single next review gate

In a CLEAN FULL Git checkout, require:

```zsh
python3 -m unittest discover -s crypto-300-profit-mission/bsc-forward-follow-model/f0/tests -p 'test_*.py' -v
```

**Expected discovery count 224 (213 baseline + 5 #141 + 6 #143), with 224 PASS, ZERO SKIP. This is an EXPECTATION, not an observed result.** Independently compare the four imported blobs to their PR141 originals and #143's frozen Router + PR116 manifest blobs; verify updated HANDOFF agrees; specifically exercise the fake CLI `checked_block` tests and saved real-cohort Router tests in one process environment. Require no network calls.

Then perform a targeted *integration-only* code read: `f0_l1_code_probe.py` still changes no RPC planning, permits, persistent journal or nonce beyond #141's checked-block projection, and `f0_l1_window.py` still uses same saved full-block set for both candidates with `control_eligible=false`, `actual_rpc_calls=0`, no E2/E3/quotes. If any mismatch, `REQUEST_CHANGES` with actual evidence.

## L1 next real-world milestone — not part of this PR

The old approved one-height code qualification observed by the user on block `128636823` covers 19 no-code and one code-present PRIMARY, two code-present Router addresses, but it does **not** prove an EOA signer or Router swap. The next meaningful step is **bounded prospective L1 full-block collection**, with UTC + monotonic FIRST-RECEIVED, request-before-send persistent audit, gaps and denominator, watch sender + documentary Router candidates from the SAME responses. A 120-second window at documented `~0.45s/block` needs roughly 267 full-block fetches (plus head/receipt/audit), which is a planning estimate, NOT any new user permit or proven provider capacity.

**Both prior 4-call and 24-read one-shot permissions have been exhausted**. The integrated offline code is NOT any grant for RPC/WS, monitoring, signing, trading, quote, alert, merge or deployment. A future live HTTP/WS experiment requires separately reviewed concrete execution code and user-specified request/time/rate/free-cost/storage boundaries, plus explicit fresh user approval and an independently reviewed permit.
