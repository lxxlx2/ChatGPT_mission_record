# PRICE V3 EVALUATION PLAN

Status: DESIGN_DRAFT_BLOCKED. This document is not a V3 freeze contract. No certified hidden interval exists; no optimizer or evaluator may run.

Precondition: certified untouched150-day historical interval, including causal warmup, before2026-06-01 05:21 UTC conservative exposed boundary. No range is currently certified. Partition lengths proposed60d CALIBRATION,45d VALIDATION,45d FINAL_HOLDOUT. Exact UTC boundaries and paths must be frozen before new raw acquisition. No exposed interval may be substituted.

Envelope primary hit is candidate ENVELOPE_ACTIVATED or SIGNAL_ADDED in onset[-15m,0]; secondary including+2m is reported independently. Directional segment coverage is same-direction active candidate evidence observed from segment onset through min(onset+2m,last_material_time), irrespective of whether it generates a fresh notification; active state persistence is evidence, not an invented event. Retain per-segment coverage and miss IDs. Envelope hit never implies directional coverage.

Proposed gates: aggregate envelope early/on-time>=90%,including+2m>=95%; per-asset same gates when>=10 envelopes; aggregate directional>=90%,per-asset directional>=90% when>=10 segments. No-label metrics are N/A and aggregate missing labels fail. Daily load perasset median<=5,p95<=15,max<=30;combinedp95<=40;single candidate envelope p95 SIGNAL_ADDED count<=6. Include zero complete UTC days. Validation and holdout use identical gates.

Rank passing calibration configs by min qualifying asset envelope recall, aggregate envelope recall, min qualifying asset directional coverage, aggregate directional coverage, lowercombinedp95,lower total events,higher thresholds in declared order. No passing config means stop. Winner and complete leaderboard commit+push precede validation access. Validation one-shot;failure stops. Holdout access requires committed validation PASS and one-shot receipt. No reselection or definition edits. Failure requires V4 and new exposure qualification.

Capability guards must reject optimizer validation/holdout/exposed access, validation holdout access, GT candidate-output access and candidate GT access. Record acquisition and evaluator openings separately, before reads, with role/range/opened_at/purpose/code version and append result hashes later. Exposed/HYPE diagnostics only after holdout PASS. Forward collection is not started by this draft: live remains prohibited.
