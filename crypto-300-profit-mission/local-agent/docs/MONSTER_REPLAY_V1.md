# Frozen Monster V1 replay

The ground-truth definition remains `MONSTER_GROUND_TRUTH_V1.md`, frozen and remotely verified at `3a4167ee9f9953de31c96f817dce318523d98a71` before discovery. The offline evaluator uses NumPy; the baseline agent does not require it.

For an isolated Python 3.12 tool environment:

```sh
uv venv --python 3.12 /absolute/private/evidence/monster-tools-venv
uv pip install --python /absolute/private/evidence/monster-tools-venv/bin/python -r requirements-monster-replay.txt
/absolute/private/evidence/monster-tools-venv/bin/python scripts/monster_d1_frozen.py --root /absolute/private/evidence
```

The actual FM2 run uses its private CPython 3.13.15 environment and NumPy 2.2.6. The exact runtime path and versions are recorded in the private discovery receipt. Agent regression still runs separately under Python 3.14 and 3.12.

Stage A combines the complete historical official directory inventories with fresh official exchangeInfo. USDT dated contracts and SETTLED aliases remain separate instruments with metadata ambiguity retained. Its first directory-only probe attempt was stopped and corrected: the second probe verifies 24 real ZIP/checksum/candle samples before corrected bulk expansion. The first attempt log and listings remain separate evidence; cached verified ZIPs are reused.

The private dataset manifest records ZIP SHA256, official checksum, parsed-bar counts, missing archives, conflicts, and final coverage. Current incomplete UTC days are excluded, and future coverage and split boundaries are censored. Exactly 48 configurations use TRAIN selection only. No recovery observation is credited as an uninterrupted trigger: recovery activation records are retained separately, including their count, rather than hidden in noise or recall.

Future path labels and candidate outcome audits are offline artifacts only. Candidate activation records contain no future labels. Published V1 discovery/evaluation outputs use exclusive-create semantics and reject differing reruns. A new attempt must use a separate output version or evidence root; it must preserve the input freeze and private canonical archives. D2/D3 are conditional on an acceptable D1 result, and no production runtime, launch agent, automation, or investment alert is enabled by these scripts.
