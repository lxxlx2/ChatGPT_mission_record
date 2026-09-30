# PRICE V3 DIRECTIONAL SIGNALS

Status: DESIGN_DRAFT_BLOCKED. This document is not a V3 freeze contract. No certified hidden interval exists; no optimizer or evaluator may run.

R1-R9 each retain UP and DOWN states independently. R5 tests drawup and drawdown separately; simultaneous reversal evidence remains visible. R1_DOWN cannot erase R5_UP. Candidate has its own envelope with30 fully observed all-rule inactive minutes for closure; it never uses GT labels.

Notify only ENVELOPE_ACTIVATED and SIGNAL_ADDED for inactive-to-active directional rule transitions. SIGNAL_REMOVED and ENVELOPE_CLOSED are state-only. No MATERIAL_ESCALATION or aggregate direction-flip notification in this first draft. Repeated active minutes do not notify. State is the current observed signal set; reset/merge semantics must be implemented and tested before freezing.

Raw schema: event_id, asset, envelope_id, event_type, observed_at, new_signals, active_up_signals, active_down_signals, new_up_signals, new_down_signals, feature_snapshot, market_envelope_state, source, freshness, rule_version, payload_sha256. No unique direction or dominant_direction.

Identity: price:<asset>:PRICE_RULE_V3:<envelope_id>:<event_type>:<observed_at>:<signal_set_hash>. Canonical serialized payload including digest must be<=2048 bytes for normal, conflict and synthetic18-signal worst case. Compact evidence must retain timeframe meaning. Batch and incremental outputs must match identities, states, IDs and payload hashes, not just counts.
