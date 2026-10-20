# BSC F0 — future checked_block report projection correction (OFFLINE ONLY)

**Status:** `P2_REPORT_FIELD_FIX_CODED_NOT_INDEPENDENTLY_APPROVED / NO_RUN / NO_NEW_RPC`.

## Historical result boundary

[Draft PR #140](https://github.com/lxxlx2/ChatGPT_mission_record/pull/140) contains **operator-reported** completion of one **already consumed** user-authorized 24-request code-at-height qualification on BSC: 1 chainId, 1 blockNumber, 20 frozen PR116 PRIMARY getCode, 2 source-documented Router getCode, 24 `RPC_RESPONSE` states, zero claimed retries/failures. On recorded block `128636823` (`0x7aad797`) 19 PRIMARY returned no runtime code and one returned code (`0x7b3d8e939ee08b52d06ab5e6f85791a6007e8d61`); both Router candidates returned runtime code but remain **control_eligible=false**. The operator reports `report.json` top-level `checked_block=null` even though recorded `eth_blockNumber` and all 20 archived wallet checked heights agree. The original local `report.json` and `journal.json` are on the user's Mac, not checked or recomputed by this branch. Their original bytes **MUST NOT** be modified, reinterpreted as fresh RPC or claimed independently verified.

## Root cause and targeted patch

Approved offline code PR #136 `cd30f8b69301b53380473a33ebb428351d4c1bce` delegates source parsing to `audit_offline()`, which returns a `requested_height` from the internal snapshot; the one-shot runner never provided a final explicit `checked_block`. Its snapshot initializes height to the private parser placeholder `1` before any successful height call, to permit a fail-closed report if the chain or block number is unavailable. An absent checked-block field is not permission to substitute that placeholder as a validated chain observation.

The new `f0_l1_code_probe.probe()` sets `confirmed_height=None` before source requests, assigns it **only after** a valid `eth_chainId=56` and successful `eth_blockNumber > 0` pass, and adds `checked_block=confirmed_height` to the final report. Thus:
- complete 24-read synthetic fixture -> `checked_block=100`;
- chain ID error -> `checked_block=null`;
- unavailable/invalid head -> `checked_block=null`;
- early stop during later `eth_getCode` -> **keep actual confirmed height** in the failed report.

The change is a deterministic **report presentation** fix only. It DOES NOT change any sender, external endpoint, call cap, attempt journal, nonce, permit, latency, real cohort/Router selection, network behavior, quote, E1/E2/E3 or control eligibility. **NO network** used for this repair. Separate documentation/PR #140 result remains archival and is not rewritten.

## Required independent review

Five new tests in `tests/test_f0_l1_report_checked_block.py` assert the 4 cases above and exact replay equality to `fixture_l1_code_probe_24_report.json` with new `checked_block=100`; all use fake saved `eth_chainId`, `eth_blockNumber` and `eth_getCode` responses only.

The previously reviewed PR #136 full checkout ran **213/213 PASS, zero skip**. This branch adds 5 tests, so a fresh full checkout must prove **218/218 PASS, zero SKIP**. **This local ChatGPT environment has not executed the complete test suite**, because it cannot access the private repository via its local container; no such result is claimed. Compare the fixed Git tree to immutable PR #136, verify exact fixture and code effects, and use separate reviewer `APPROVE (OFFLINE ONLY)` or `REQUEST_CHANGES`. No approval of this branch can authorize new RPC reads.

Review command from a complete Git checkout:

```zsh
python3 -m unittest discover -s crypto-300-profit-mission/bsc-forward-follow-model/f0/tests -p 'test_*.py' -v
```

## Next mainline milestone

The user's **4-call smoke and subsequent 24-call qualification permissions have both been consumed**. Do not retry the 24-read qualification. The future meaningful work is a separately permitted **short contiguous-block L1 + ordinary Router unbiased control capture**, then independently measured first-seen delays and actual +60/+300/+900s quotes. Both watchlist and controls require real prospective samples; the present 24-read code-at-height result alone does not establish EOA signer behavior, swap causality, E2/E3 or profit.
