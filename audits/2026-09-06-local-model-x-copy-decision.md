# LOCAL_MODEL_X_COPY_DECISION

Date: 2026-09-06

Status: CURRENT

## Decision

Local Qwen is not approved for X/Twitter copy generation on the current 48 GB workstation under the Owner's representative office workload.

The X revenue workflow keeps deterministic candidate generation until a local text model passes a dedicated workflow-specific `X_COPY` qualification.

## Evidence

### Qwen3.6-35B-A3B-4bit

Two representative production memory preflights were attempted while normal work applications remained open.

Second measured state:

- expected memory profile: 28 GiB;
- current policy reclaimable threshold: 23.8 GiB;
- available memory: 21.51 GiB;
- reclaimable memory: 22.45 GiB;
- compressed: 1.58 GiB;
- swap used: 1.4 GiB;
- pressure: NORMAL;
- admission result: `INSUFFICIENT_RECLAIMABLE_MEMORY`;
- model started: false.

The earlier attempt also failed representative admission with about 21.67 GiB available/reclaimable range.

Result: `X_COPY = RESOURCE_BLOCKED / DO_NOT_USE_FOR_X_COPY`.

No X-writing quality verdict exists because the model never started.

### Qwen3.8-27B-8bit

The model has a higher expected memory profile, and previous representative cold-load evidence hit the relative swap-growth limit.

Result: `X_COPY = RESOURCE_BLOCKED / DO_NOT_USE_FOR_X_COPY`.

## Production consequence

Current production path remains:

`real sources -> deterministic trigger -> deterministic analysis/candidate -> quality checks -> unified Telegram Owner approval -> manual copy/publish`

External X publishing remains disabled.

The existing `@Jersonliu_bot` in `lxxlx2/local-ai-platform` remains the single Telegram approval consumer. The X workflow must not reintroduce its own Telegram polling client.

## Future promotion gate

A local text model may enter X candidate generation only after representative `X_COPY` qualification proves safe admission/coexistence, factual preservation across 10 real saved market artifacts, <=280-character compliance, no unsupported claims, acceptable latency, cleanup safety, and at least 7/10 outputs materially better than the deterministic baseline.

Human Telegram approval remains mandatory after any future model promotion.

## Cross-repository tracking

Direct-work local-model validation is tracked in `lxxlx2/local-ai-platform` Issue #44 and `docs/MODEL_WORK_CAPABILITY_VALIDATION_V1.md`.
