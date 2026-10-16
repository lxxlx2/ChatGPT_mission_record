# Frank Safari: PR #77/#78 independent review remediation, 2026-10-16

Original external reviewer verdicts (unchanged and NOT approved):
- F01 PR #77 SHA `2459cfdc90987a40809bf67f54a1197e23fa3e85`: REQUEST_CHANGES. P2 opposite quote/metrics source priority; P3 formal watchlist exposes raw Slot.
- C02 PR #78 SHA `292b9bbdfab08fc49cd494ba256c931fc1789ca5`: REQUEST_CHANGES. P2 uninitialized/unverified mint is falsely green safe; P3 public identity audit exposes Slot/SHA.

## Actual remediation

- F01 Draft child [PR #79](https://github.com/lxxlx2/ChatGPT_mission_record/pull/79), exact child SHA `95fc00a7ab90b2fa28e34e97ec79b23db7addfa2` based on rejected #77. Eligibility now fails closed if `decision_quote` and `metrics` disagree or are invalid; emitted `validated_follow_quote` is the display source. Formal watchlist removes raw Slot. Frozen Frank decisions, historical metrics, outbox and strategy unchanged. The first child CI [#38838717781](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38838717781) caught an actual historical NO_BUY display regression (1 failed, 1468 passed); fixed without skipping. Final [CI #38838905688](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38838905688) SUCCESS: 42 targeted, 1469 full Python tests + actual renderer Node.
- C02 Draft child [PR #80](https://github.com/lxxlx2/ChatGPT_mission_record/pull/80), exact child SHA `f7aa430ffda98051821ac4a35ccf6d5d9b0bc95d` based on rejected #78. Green permission risk requires verified initialized finalized mint, known program, explicit authority fields and permission/extension evidence. User-facing source detail uses field allowlists; raw Slot/SHA remain in backend provenance. Shared formal watchlist also hides Slot. [CI #38839073435](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38839073435) SUCCESS: 7 targeted, 1452 full Python tests + actual renderer Node.

## Gates

- Exact fixed child versions require a DIFFERENT AI to independently re-review each diff and reproduce the original P2 and P3 counterexamples. Old PR #77/#78 REQUEST_CHANGES is never retroactively upgraded.
- Both branches change `static/app.js`; no claim of a combined green tree is made. After external approval, only a fresh disposable combined checkout can resolve any overlap and run combined Python + Node + authorized new Mac Safari QA.
- Prior Mac integration SHA `9479e33070189231d6be2ed1633a420296dfd1a0` and 60-test result are evidence of the PREVIOUS sources, not these fixes.
- No merge/deploy, real RPC, production SQLite, personal Sidecar reads, Gmail, trading, automation or file cleanup authorized. F02 is internal-only QA; final user-facing F01/C02 pages must never show raw source Slot or SHA.
