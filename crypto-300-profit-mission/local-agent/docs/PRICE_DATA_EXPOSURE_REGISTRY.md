# PRICE DATA EXPOSURE REGISTRY

Status: V3_BLOCKED_NO_VERIFIABLE_HIDDEN_INTERVAL. Repository history inventory inspected301 distinct Mission paths,31 relevant price/history/exposure paths. No complete prior exposure ledger exists; no hidden range is certified.

V1 evaluation: 2026-08-31 05:57 UTC to 2026-09-30 05:57 UTC. V2 calibration: 2026-06-02 05:57 UTC to 2026-08-01 05:57 UTC. V2 validation and forensic: 2026-08-01 05:57 UTC to 2026-08-31 05:57 UTC. All of 2026-06-02 to 2026-09-30 is exposed.

Actual cache warmup expands the conservative exclusion start to 2026-06-01T05:21:00+00:00. A new interval must not overlap causal warmup, not just nominal evaluation dates.

Machine source inventory: config/price_data_exposure_registry.json. Existing report/contract bytes and non-AUDIT manifest metadata were hashed. Raw prices and AUDIT manifests were not opened. Filename inventory under /Users/jerson/Documents/ChatGPT found the existing Phase3 and Phase3B market caches and no additional older project cache. This establishes scoped absence only; no global claim about external/deleted evaluations is made. No new hidden range is certified yet.

Each future opening must append role, half-open raw/evaluation ranges, opened_at, purpose, code version and result hash. An opening is recorded before evaluation with pending result, then completed by a separate append, never rewriting the opening. Acquisition itself counts as exposure to the acquisition process; evaluator access remains separately recorded and capability restricted.
