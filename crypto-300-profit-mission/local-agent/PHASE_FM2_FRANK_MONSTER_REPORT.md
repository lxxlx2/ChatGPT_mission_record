# PHASE_FM2_FRANK_MONSTER_REPORT

PHASE_FM2 = PARTIAL

Authorized bounded work is complete and stopped for review. Frank manual validation and real capture passed; no real ACTIVE forward transaction occurred. Monster D1 discovery and frozen replay completed, but noise and sample gates did not pass.

1. **Timestamp discrepancy:** Canonical oldest snapshot time 2025-09-04T00:06:20Z; handoff 02:46:20 was a transcription error; raw unchanged.

2. **Primary50 reviewed:** 50/50 original identities, no resampling; extra 5 complete the original ACTIVE13.

3. **Classification agreement:** 48/50 = 96%; two manual transfer-outs remain UNKNOWN.

4. **Token delta agreement:** 50/50 = 100%.

5. **Signer / fee payer agreement:** 50/50 = 100%.

6. **Authority agreement:** 50/50 = 100%.

7. **ACTIVE13 false positives:** 0; all original 13 retained ACTIVE.

8. **Final parser:** frank-v7; immutable processing-v8 output.

9. **v4 changes:** 32 UNKNOWN→ACTIVE, 4→FAILED, 6→PASSIVE; integer amounts, authority binding, recognized program/log context and transient WSOL repair.

10. **Final 500 classes:** ACTIVE45 / PASSIVE374 / UNKNOWN76 / FAILED4 / TRANSFER_OUT1; 500 parsed, errors0.

11. **Final 500 candidates:** 57 vs old12; semantic signature/mint pairs +46/-1; IDs changed with allowed reason names. HFT suppression applies.

12. **Forward duration:** 125.04 minutes continuous final parser, 2026-09-30 23:05:57Z to 2026-10-01 01:10:59Z; 30s polling.

13. **Real new signatures:** 4 distinct observations overall: 2 migrated with original real detection timestamps, 2 newly detected within final continuous window. Total PASSIVE1 / UNKNOWN3.

14. **Forward candidates:** 0 ACTIVE, 0 candidates; active-candidate transport leg NOT_OBSERVED.

15. **Detection p50 / p95:** N/A: 4 real samples < minimum20; outage sample kept separate.

16. **Gaps:** Recovery gap0, duplicate candidate0; SQLite integrity ok.

17. **Restart / recovery:** Successful real SIGTERM; real SIGKILL; collector stopped 320.06 seconds; one actual PASSIVE signature recovered. Additional SIGKILL preserved two real raw-cache files. Initial STOP serialization failure preserved and repaired.

18. **History progress:** 4724/18203 durably normalized with current parser; 89 active mints, 67 observed round trips, 12 re-entries; available referenced accounts only, no lifetime-entry / wallet-wide exit / PnL claim.

19. **Private transport:** Final historical v8: 57 items in 40+17, 4 private commits, restart/hash/dedupe PASS, identical replay0 writes. Earlier superseded v7 test made4 additional private commits. Real forward transport writes0.

20. **Frank status:** MANUAL_GATE PASS; FORWARD_CAPTURE PASS; ACTIVE_FORWARD_E2E NOT_OBSERVED; overall bounded Frank work PARTIAL.

21. **GT freeze:** 3a4167ee9f9953de31c96f817dce318523d98a71 pushed before discovery; 48-grid and GT V1 unchanged.

22. **Period:** 2025-01-01 through nominal 2026-09-30; closed UTC archives available only through Sep29. TRAIN2025 / VALIDATION2026H1 / AUDIT2026Q3; right-censored anchors250139, split-boundary events40.

23. **Symbols with data:** 1518 of1724 USDT union, Spot611/Futures907. 206 without bars:197 ended pre-window,7 current archive unavailable,2 no official target-period1h.

24. **Not-current coverage:** 279 non-TRADING instruments with bars (Spot115/Futures164);34 absent from current inventory. These are distinct definitions.

25. **Events total:** 1542 non-overlapping frozen GT events; 61690 verified1h archive receipts.

26. **Exact 2X:** 1485; cumulative>=2X1542.

27. **Exact 3X:** 41; cumulative>=3X57.

28. **Exact 5X:** 12; cumulative>=5X16.

29. **Exact 10X:** 2; cumulative>=10X4.

30. **Exact 20X+:** 2; cumulative>=20X2.

31. **D1 TRAIN recall:** No accepted winner. Reporting diagnostic V1-47 selected only by TRAIN minimum p95 then median: >=5X8/12=66.67%; >=10X1/3=33.33%.

32. **VALIDATION 5X recall:** Diagnostic3/4=75%, below85%; no accepted-model claim.

33. **VALIDATION 10X recall:** Diagnostic1/1=100%; N1 < required10: INSUFFICIENT_DATA.

34. **Before 2X rate:** VALIDATION>=10X0/1=0%, below70%; >=5X2/4=50%.

35. **Lead to2X /5X /peak:** VALIDATION>=5X medians14h/59h/96.5h; >=10X0h/0h/0h, same-hour spike. All diagnostic.

36. **Candidate symbols/day:** TRAIN median60, VALIDATION78, AUDIT91; threshold<=30.

37. **p95 symbols/day:** TRAIN82, VALIDATION96, AUDIT115; threshold<=60; every frozen TRAIN config fails noise.

38. **Largest misses:** TRAIN MMT futures14.951X, MMT spot10.324X, AVNT8.261X; VALIDATION BTW7.744X. English objective case notes supplied.

39. **Noise:** Diagnostic non2X rates24h99.22%,72h97.89%,168h95.98%; causal rankings retained, no future reranking. Recovery-context activations16.

40. **D2 availability:** NOT_STARTED: D1 acceptance gate failed; no derivatives history availability claim.

41. **D3 duration:** NOT_STARTED, gate blocked.

42. **D3 candidates:** N/A, no shadow run.

43. **Monster transport:** No D3 candidates, no Monster transport writes. StageB26 windows:171 valid/185 official5m archives,14 HTTP404; original GT unchanged.

44. **Monster status:** MONSTER_D1_INSUFFICIENT_DATA + NEEDS_CALIBRATION; winner=null. D2/D3 blocked.

45. **pytest:** Python3.14:357 passed; Python3.12:357 passed; compileall / both pip check / diff check PASS.

46. **CPU / RSS / disk:** Sampled peak CPU291% (parallel processes/multicore), individual RSS4520096KiB (~4.31GiB); sampled private evidence disk2284175360bytes (~2.13GiB). Bounded jobs completed.

47. **Gmail:** 0 actions.

48. **Automation:** 0 scheduler / LaunchAgent creation; bounded manual processes only.

49. **Production writes:** 0; historical writes restricted to private test namespace.

50. **Branch:** codex/crypto-monitor-design-20260930; no rebase, main untouched.

51. **SHA:** Implementation 890cda7; reviewed merge/source SHA 81376040f4f2543629ba9bc5da9e1474b1f920fd; GT freeze3a4167 remains ancestor. Final report commit in handoff.

52. **Next gate:** Independent review of this fixed candidate. Decide calibration / sample extension separately; no automatic threshold tuning, D2/D3 or production approval.

## Evidence and methodological limitations

Private raw transactions, identities, manual explorer captures, RPC observations and receipts remain outside Git in the local FM2 evidence directory. Reported aggregates are derived from those artifacts. Same500 originals and all intermediate processing outputs are retained.

The initial archive attempt used directory probes before actual candle probes; that attempt is not retrospectively accepted. It was preserved and followed by a corrected 24-ZIP stratified probe, 6/6 successful in each combined stratum, before the corrected expansion. One interrupted attempt left a zero-byte MUUB cache file: original invalid bytes were preserved, and a new checksum-verified 24-bar archive was fetched into a separate repair cache. V2 coverage and replay consume that explicit repair. No official data corruption is claimed.

Stage B is a targeted verification supplement and does not convert wick maxima into executable returns. Validation 10X recall is descriptive only at N=1. No configuration met TRAIN noise constraints; V1-47 diagnostics must not be treated as a deployed winner.

Supporting implementation and operation bounds: [Frank](docs/FRANK_FORWARD_V1.md), [Monster](docs/MONSTER_REPLAY_V1.md), [English case notes](docs/MONSTER_CASE_NOTES_V1.md).

CORE PRICE V3 = PAUSED
NFT = NOT STARTED
$300 AUTOMATION = DISABLED
PRODUCTION = NO_GO
