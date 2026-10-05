# PRICE GT V3 ENVELOPE

Status: DESIGN_DRAFT_BLOCKED. This document is not a V3 freeze contract. No certified hidden interval exists; no optimizer or evaluator may run.

Proposed independent GT material admission: FAST abs1h>=4%; MEDIUM abs4h>=7%; REVERSAL each of drawup and drawdown15m>=5% independently; causal prior24h BREAKOUT>=1.5% for3 consecutive samples; VOL>=4x prior24h median plus abs5m>=2.5%. No family priority removes a side.

Envelope starts at first fully observed material minute and survives direction changes. Close only after30 consecutive fully observed minutes inactive across every family and direction. Gaps reset the inactivity counter and never count as inactivity. At partition end preserve right_censored. Warmup-origin envelopes are excluded from onset denominators and separately counted.

Required fields: envelope_id, asset, start_time, first_material_time, last_material_time, end_time, material_family_set, up_family_set, down_family_set, had_direction_conflict, direction_flip_count, peak_up_magnitude, peak_down_magnitude, max_absolute_move, price_range, input_hash, right_censored. Define flips only between consecutive non-conflicting singleton evidence sets; conflicts are counted separately.

Directional segments are independent per direction. Merge interruptions shorter than5 fully observed inactive minutes; close at5. Gap resets inactivity, not false closure. Segments remain linked to their containing envelope.
